#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Keep a health records folder's markers.csv and index.md.

Usage: uv run records.py <command> <records-dir> [options]

  merge <records> <rows.csv>   Validate staged marker rows and merge them into markers.csv.
                               A source's rows replace all earlier rows from that source.
                               Writes nothing and exits 1 if any row is invalid.
  index <records>              Regenerate index.md from document frontmatter, markers.csv,
                               context.md and panels/.
  table <records> [--name S]   Print every analyte's full history, oldest first, as Markdown.
  check <records>              Report problems; exits 1 on errors, 0 on warnings only.

Staged rows (rows.csv) need columns original_name, value, date, source, and may carry name,
loinc, unit, ref_range, flag. `source` is the document's path inside the records folder, such as
documents/2025-03-14_lab_example-lab.md. Rows without `name` are named from the bundled
references/analytes.csv and the folder's own aliases.csv. A row whose `name` is new for its
original name adds that pair to aliases.csv, so later runs name it the same way.
"""

import argparse
import csv
import io
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import yaml

SKILL = Path(__file__).resolve().parent.parent
ANALYTES = SKILL / "references" / "analytes.csv"
COLUMNS = ["name", "loinc", "date", "value", "unit", "ref_range", "flag", "original_name", "source"]
FLAGS = {"", "H", "L", "HH", "LL", "A"}
DOC_TYPES = {"lab", "imaging", "discharge", "visit", "pathology", "procedure", "prescription",
             "vaccination", "other"}
DOC_FIELDS = ["date", "type", "provider", "title", "language", "source", "sha256", "extraction",
              "summary"]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NUMBER = re.compile(r"^(<=|>=|<|>|≤|≥)?\s*(-?\d+(?:\.\d+)?)$")
COMMA_DECIMAL = re.compile(r"\d,\d")
RANGE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*[-–]\s*(-?\d+(?:\.\d+)?)$")
BOUND = re.compile(r"^(<=|>=|<|>|≤|≥)\s*(-?\d+(?:\.\d+)?)$")


# ---------------------------------------------------------------- normalizing


def name_key(s: str) -> str:
    """Match key for analyte names: no accents, case or stray punctuation."""
    s = unicodedata.normalize("NFKD", s.strip())
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold()
    s = re.sub(r"[\s_]+", " ", s)
    return s.strip(" :*")


# Spellings of one unit with the same numeric scale, after unit_key's other rewrites.
SAME_UNIT = {
    "G/L": "10^9/L", "10^3/uL": "10^9/L", "10^3/mm3": "10^9/L", "K/uL": "10^9/L",
    "T/L": "10^12/L", "10^6/uL": "10^12/L", "M/uL": "10^12/L",
    "ng/mL": "ug/L", "pg/mL": "ng/L", "uIU/mL": "mIU/L", "uU/mL": "mIU/L", "IU/L": "U/L",
}
SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def unit_key(u: str) -> str:
    """Match key for units. Case matters (G/L is 10^9/L, g/L is grams), except for the litre."""
    u = u.strip().replace(" ", "").replace("μ", "u").replace("µ", "u").replace(",", ".")
    u = u.replace("perc", "min").replace("óra", "h").replace("mcg", "ug")
    u = re.sub(r"^[x×*]", "", u.translate(SUPERSCRIPT)).replace("10*", "10^").replace("E9/", "10^9/")
    u = re.sub(r"^10(\d+)/", r"10^\1/", u)  # 10⁹/L arrives as 109/L
    u = re.sub(r"(?<![A-Za-z])([munpfdk]?)[lL](?![A-Za-z])", lambda m: m.group(1).lower() + "L", u)
    return SAME_UNIT.get(u, u)


def parse_value(v: str):
    m = NUMBER.match(v.strip())
    if not m:
        return None, None
    return (m.group(1) or ""), float(m.group(2))


def parse_range(r: str):
    r = r.strip()
    if m := RANGE.match(r):
        return float(m.group(1)), float(m.group(2))
    if m := BOUND.match(r):
        op, x = m.group(1), float(m.group(2))
        return (None, x) if op in ("<", "<=", "≤") else (x, None)
    return None


def computed_flag(value: str, ref: str) -> str | None:
    """H or L from a numeric value and range, "" when inside, None when it cannot tell."""
    op, x = parse_value(value)
    rng = parse_range(ref) if ref else None
    if x is None or rng is None or op:
        return None
    lo, hi = rng
    if lo is not None and x < lo:
        return "L"
    if hi is not None and x > hi:
        return "H"
    return ""


# ---------------------------------------------------------------- loading


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in columns})
    path.write_text(buf.getvalue(), encoding="utf-8")


class Names:
    """Original name -> canonical name, and canonical name + unit -> LOINC."""

    def __init__(self, records: Path):
        self.alias: dict[str, str] = {}
        self.loinc: dict[tuple[str, str], str] = {}
        self.local_path = records / "aliases.csv"
        for row in read_csv(ANALYTES):
            name = row["name"]
            for u in row["units"].split("|"):
                self.loinc[(name, unit_key(u))] = row["loinc"]
            self.alias.setdefault(name_key(name), name)
            for a in filter(None, row["aliases"].split("|")):
                self.alias[name_key(a)] = name
        self.local = read_csv(self.local_path)
        for row in self.local:
            self.alias[name_key(row["original_name"])] = row["name"]
        self.added: list[dict] = []

    def resolve(self, original: str) -> str | None:
        return self.alias.get(name_key(original))

    def learn(self, original: str, name: str) -> None:
        self.alias[name_key(original)] = name
        self.added.append({"original_name": original, "name": name})

    def loinc_for(self, name: str, unit: str) -> str:
        return self.loinc.get((name, unit_key(unit)), "")

    def save(self) -> None:
        if self.added:
            write_csv(self.local_path, self.local + self.added, ["original_name", "name"])


def frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    try:
        # BaseLoader keeps every value a string: a date stays 2025-03-14, a hash never becomes a number.
        data = yaml.load(text[4:end], Loader=yaml.BaseLoader)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def documents(records: Path) -> list[tuple[Path, dict | None]]:
    docs = records / "documents"
    return [(p, frontmatter(p)) for p in sorted(docs.glob("*.md"))] if docs.is_dir() else []


# ---------------------------------------------------------------- merge


def validate(row: dict, n: int, records: Path, names: Names) -> tuple[dict | None, list[str], list[str]]:
    errors, notes = [], []
    where = f"row {n} ({row.get('original_name') or '?'})"
    for col in ("original_name", "value", "date", "source"):
        if not row.get(col):
            errors.append(f"{where}: missing {col}")
    if errors:
        return None, errors, notes
    if not ISO_DATE.match(row["date"]):
        errors.append(f"{where}: date {row['date']!r} is not YYYY-MM-DD")
    if not (records / row["source"]).is_file():
        errors.append(f"{where}: source {row['source']} does not exist in the records folder")
    for col in ("value", "ref_range"):
        if COMMA_DECIMAL.search(row.get(col, "")):
            errors.append(f"{where}: {col} {row[col]!r} has a decimal comma; write it with a dot")
    flag = row.get("flag", "").upper()
    if flag not in FLAGS:
        errors.append(f"{where}: flag {row['flag']!r} is not one of H, L, HH, LL, A or empty")

    name = row.get("name", "")
    known = names.resolve(row["original_name"])
    if not name:
        if not known:
            errors.append(f"{where}: unknown analyte; give it a canonical `name` (see analytes.csv)")
        name = known or ""
    elif not known:
        names.learn(row["original_name"], name)
        notes.append(f"alias added: {row['original_name']!r} -> {name}")
    if errors:
        return None, errors, notes

    unit = row.get("unit", "")
    loinc = row.get("loinc") or names.loinc_for(name, unit)
    calc = computed_flag(row["value"], row.get("ref_range", ""))
    if not flag and calc:
        flag = calc
        notes.append(f"{where}: flag {calc} computed from the range")
    elif calc is not None and flag in ("H", "L", "") and flag != calc:
        notes.append(f"{where}: report flag {flag or 'none'} but value/range say {calc or 'none'}; kept the report's")
    out = dict(row, name=name, loinc=loinc, unit=unit, flag=flag)
    return out, errors, notes


def merge(records: Path, staged: Path) -> int:
    names = Names(records)
    new, errors, notes = [], [], []
    for n, row in enumerate(read_csv(staged), start=2):
        out, e, m = validate(row, n, records, names)
        errors += e
        notes += m
        if out:
            new.append(out)
    if errors:
        print("Nothing written. Fix these rows and merge again:")
        print("\n".join(f"  {e}" for e in errors))
        return 1

    path = records / "markers.csv"
    old = read_csv(path)
    sources = {r["source"] for r in new}
    kept = [r for r in old if r["source"] not in sources]
    replaced = len(old) - len(kept)

    def same(r):
        return (r["name"], r["date"], r["value"], unit_key(r["unit"]))

    seen = {same(r): r["source"] for r in kept}
    added, dropped = [], []
    for r in new:
        k = same(r)
        if k in seen and seen[k] != r["source"]:
            dropped.append(f"{r['name']} {r['date']} {r['value']} from {r['source']} (already from {seen[k]})")
            continue
        if k in seen:
            continue  # the same row twice in one source
        seen[k] = r["source"]
        added.append(r)

    rows = sorted(kept + added, key=lambda r: (r["name"].casefold(), r["date"], r["source"], r["original_name"]))
    write_csv(path, rows, COLUMNS)
    names.save()

    by_day = defaultdict(set)
    for r in rows:
        by_day[(r["name"], r["date"])].add((r["value"], unit_key(r["unit"])))
    conflicts = [f"{n} on {d}: {sorted(v for v, _ in vals)}" for (n, d), vals in by_day.items() if len(vals) > 1]

    print(f"markers.csv: {len(rows)} rows ({len(added)} from {len(sources)} source(s), {replaced} earlier rows replaced)")
    for title, items in (("Duplicates dropped", dropped), ("Notes", notes),
                         ("Same analyte, same day, different values (check the sources)", conflicts)):
        if items:
            print(f"{title}:")
            print("\n".join(f"  {i}" for i in items))
    return 0


# ---------------------------------------------------------------- reading


def history(records: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in read_csv(records / "markers.csv"):
        out[r["name"]].append(r)
    for rows in out.values():
        rows.sort(key=lambda r: (r["date"], r["source"]))
    return dict(sorted(out.items(), key=lambda kv: kv[0].casefold()))


def cell(r: dict, with_date=True) -> str:
    s = r["value"] + (f" {r['flag']}" if r["flag"] else "")
    return f"{s} ({r['date']})" if with_date else s


def esc(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def table(records: Path, name: str | None) -> int:
    hist = history(records)
    if name:
        hist = {k: v for k, v in hist.items() if name_key(name) in name_key(k)}
    print("| Analyte | LOINC | Unit | Reference | Results, oldest first |")
    print("|---|---|---|---|---|")
    for analyte, rows in hist.items():
        units = sorted({r["unit"] for r in rows})
        loincs = sorted({r["loinc"] for r in rows if r["loinc"]})
        refs = sorted({r["ref_range"] for r in rows if r["ref_range"]})
        if len(units) > 1:
            values = "; ".join(f"{cell(r)} {r['unit']}" for r in rows)
        else:
            values = "; ".join(cell(r) for r in rows)
        print(f"| {esc(analyte)} | {', '.join(loincs)} | {esc(', '.join(units))} | {esc('; '.join(refs))} | {esc(values)} |")
    return 0


def problems(records: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    docs = documents(records)
    marker_rows = read_csv(records / "markers.csv")
    counts = defaultdict(int)
    for r in marker_rows:
        counts[r["source"]] += 1
    shas = defaultdict(list)
    for path, fm in docs:
        rel = path.relative_to(records).as_posix()
        if fm is None:
            errors.append(f"{rel}: no YAML frontmatter")
            continue
        missing = [f for f in DOC_FIELDS if not fm.get(f)]
        if missing:
            errors.append(f"{rel}: frontmatter missing {', '.join(missing)}")
        if fm.get("type") and fm["type"] not in DOC_TYPES:
            errors.append(f"{rel}: type {fm['type']!r} is not one of {', '.join(sorted(DOC_TYPES))}")
        if fm.get("date") and not ISO_DATE.match(str(fm["date"])):
            errors.append(f"{rel}: date {fm['date']!r} is not YYYY-MM-DD")
        if fm.get("source") and not (path.parent / fm["source"]).is_file():
            errors.append(f"{rel}: source PDF {fm['source']} not found next to it")
        if fm.get("sha256"):
            shas[fm["sha256"]].append(rel)
        if fm.get("type") == "lab" and not counts.get(rel):
            warnings.append(f"{rel}: lab document with no rows in markers.csv")
    for sha, rels in shas.items():
        if len(rels) > 1:
            errors.append(f"same PDF extracted twice: {', '.join(rels)}")
    names = {p.relative_to(records).as_posix() for p, _ in docs}
    for src in sorted(counts):
        if src not in names:
            errors.append(f"markers.csv: {counts[src]} rows cite {src}, which does not exist")
    for analyte, rows in history(records).items():
        units = {unit_key(r["unit"]) for r in rows}
        if len(units) > 1:
            warnings.append(f"{analyte}: results in {len(units)} units ({', '.join(sorted({r['unit'] for r in rows}))}); compare with care")
        if not any(r["loinc"] for r in rows):
            warnings.append(f"{analyte}: no LOINC")
    return errors, warnings


def check(records: Path) -> int:
    errors, warnings = problems(records)
    for e in errors:
        print(f"error: {e}")
    for w in warnings:
        print(f"warning: {w}")
    if not errors and not warnings:
        print("ok")
    return 1 if errors else 0


def index(records: Path) -> int:
    docs = [(p, fm) for p, fm in documents(records) if fm]
    docs.sort(key=lambda d: (str(d[1].get("date", "")), d[0].name))
    hist = history(records)
    per_doc = defaultdict(lambda: [0, 0])
    for rows in hist.values():
        for r in rows:
            per_doc[r["source"]][0] += 1
            per_doc[r["source"]][1] += bool(r["flag"])
    errors, warnings = problems(records)

    out = ["# Health records index", "",
           "Generated by `records.py index` from each document's frontmatter, `markers.csv`, "
           "`context.md` and `panels/`. Edit those, then regenerate; edits here are lost.", ""]
    ctx = records / "context.md"
    out.append("Owner's context: [context.md](context.md)" if ctx.is_file()
               else "Owner's context: none yet. Write `context.md` with age, sex, conditions, medications with dates, and open questions.")
    out.append("")

    dates = [str(fm["date"]) for _, fm in docs if fm.get("date")]
    span = f", {min(dates)} to {max(dates)}" if dates else ""
    out += [f"## Documents ({len(docs)}{span})", "",
            "| Date | Type | Provider | Document | Summary | Markers |", "|---|---|---|---|---|---|"]
    for path, fm in docs:
        rel = path.relative_to(records).as_posix()
        n, flagged = per_doc.get(rel, (0, 0))
        markers = f"{n} ({flagged} flagged)" if n else ""
        out.append(f"| {fm.get('date', '')} | {fm.get('type', '')} | {esc(fm.get('provider', ''))} | "
                   f"[{esc(fm.get('title') or path.stem)}]({rel}) | {esc(fm.get('summary', ''))} | {markers} |")
    out.append("")

    total = sum(len(v) for v in hist.values())
    out += [f"## Markers ({len(hist)} analytes, {total} results)", "",
            "Latest result per analyte. Every result: `records.py table <records>`, or `markers.csv`.", "",
            "| Analyte | Latest | Unit | Reference | Date | Earlier, newest first | Results | Ever flagged |",
            "|---|---|---|---|---|---|---|---|"]
    for analyte, rows in hist.items():
        last = rows[-1]
        earlier = "; ".join(cell(r) for r in reversed(rows[-4:-1]))
        if len(rows) > 4:
            earlier += "; ..."
        ever = sum(bool(r["flag"]) for r in rows)
        out.append(f"| {esc(analyte)} | {esc(cell(last, False))} | {esc(last['unit'])} | {esc(last['ref_range'])} | "
                   f"{last['date']} | {esc(earlier)} | {len(rows)} | {ever or ''} |")
    out.append("")

    panels = sorted((records / "panels").glob("*.md")) if (records / "panels").is_dir() else []
    out += ["## Panels", ""]
    out += [f"- [{p.stem}](panels/{p.name})" for p in reversed(panels)] or ["None yet."]
    out.append("")

    if errors or warnings:
        out += ["## Needs attention", ""]
        out += [f"- Error: {esc(e)}" for e in errors] + [f"- {esc(w)}" for w in warnings]
        out.append("")

    (records / "index.md").write_text("\n".join(out), encoding="utf-8")
    print(f"index.md: {len(docs)} documents, {len(hist)} analytes, {total} results, "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("records", type=Path)
    m.add_argument("rows", type=Path)
    for name in ("index", "check"):
        sub.add_parser(name).add_argument("records", type=Path)
    t = sub.add_parser("table")
    t.add_argument("records", type=Path)
    t.add_argument("--name")
    args = ap.parse_args()
    if not args.records.is_dir():
        print(f"not a folder: {args.records}", file=sys.stderr)
        return 2
    if args.cmd == "merge":
        return merge(args.records, args.rows)
    if args.cmd == "index":
        return index(args.records)
    if args.cmd == "table":
        return table(args.records, args.name)
    return check(args.records)


if __name__ == "__main__":
    sys.exit(main())
