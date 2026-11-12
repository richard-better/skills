#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Keep a health records folder's markers.csv and index.md.

Usage: uv run records.py <command> <records-dir> [options]

  merge <records> <rows.csv> [--clear <source>]...
                               Validate staged marker rows and merge them into markers.csv.
                               A source's rows replace all earlier rows from that source;
                               --clear empties a source that now has no rows. Writes nothing
                               and exits 1 if any row is invalid.
  index <records>              Regenerate index.md from document frontmatter, markers.csv,
                               context.md and panels/.
  table <records> [--name S]   Print every analyte's full history, oldest first, as Markdown.
  check <records>              Report problems; exits 1 on errors, 0 on warnings only.

Staged rows (rows.csv) need columns original_name, value, date, source, and may carry name,
loinc, unit, ref_range, flag. `source` is the document's path inside the records folder, such as
documents/2025-03-14_lab_example-lab.md. Rows without `name` are named from the bundled
references/analytes.csv and the folder's own aliases.csv. A row whose `name` is new for its
original name adds that pair to aliases.csv, so later runs name it the same way; a `name` that
differs from an aliases.csv entry corrects that entry. markers.csv keeps every row each document
holds; `index` and `table` count a result several documents report once.
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
    """(low, low is strict, high, high is strict); a-b is inclusive, <b and >a are strict."""
    r = r.strip()
    if m := RANGE.match(r):
        return float(m.group(1)), False, float(m.group(2)), False
    if m := BOUND.match(r):
        op, x = m.group(1), float(m.group(2))
        strict = op in ("<", ">")
        return (None, False, x, strict) if op in ("<", "<=", "≤") else (x, strict, None, False)
    return None


def computed_flag(value: str, ref: str) -> str | None:
    """H or L from a numeric value and range, "" when inside, None when it cannot tell."""
    op, x = parse_value(value)
    rng = parse_range(ref) if ref else None
    if x is None or rng is None or op:
        return None
    lo, lo_strict, hi, hi_strict = rng
    if lo is not None and (x < lo or (lo_strict and x == lo)):
        return "L"
    if hi is not None and (x > hi or (hi_strict and x == hi)):
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
        self.units: dict[str, set[str]] = defaultdict(set)
        self.local_path = records / "aliases.csv"
        for row in read_csv(ANALYTES):
            name = row["name"]
            for u in row["units"].split("|"):
                self.loinc[(name, unit_key(u))] = row["loinc"]
                self.units[name].add(unit_key(u))
            self.alias.setdefault(name_key(name), name)
            for a in filter(None, row["aliases"].split("|")):
                self.alias[name_key(a)] = name
        self.known = set(self.units)
        self.local = {name_key(r["original_name"]): r for r in read_csv(self.local_path)}
        for key, row in self.local.items():
            self.alias[key] = row["name"]
        self.changed = False

    def resolve(self, original: str, unit: str) -> str | None:
        """The canonical name, moved between `X` and `X %` when the unit says which one it is."""
        name = self.alias.get(name_key(original))
        if not name:
            return None
        percent = unit_key(unit) == "%"
        if percent and f"{name} %" in self.known:
            return f"{name} %"
        if not percent and unit and name.endswith(" %") and name[:-2] in self.known:
            return name[:-2]
        return name

    def is_local(self, original: str) -> bool:
        return name_key(original) in self.local

    def learn(self, original: str, name: str) -> None:
        key = name_key(original)
        self.alias[key] = name
        self.local[key] = {"original_name": original, "name": name}
        self.changed = True

    def loinc_for(self, name: str, unit: str) -> str:
        return self.loinc.get((name, unit_key(unit)), "")

    def unusual_unit(self, name: str, unit: str) -> bool:
        return name in self.units and unit_key(unit) not in self.units[name]

    def save(self) -> None:
        if self.changed:
            rows = sorted(self.local.values(), key=lambda r: name_key(r["original_name"]))
            write_csv(self.local_path, rows, ["original_name", "name"])


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


def canonical_source(records: Path, src: str) -> str | None:
    """documents/<file>.md relative to the records folder, or None when it points elsewhere."""
    root = records.resolve()
    p = (root / src).resolve()
    if p.parent != root / "documents" or p.suffix != ".md" or not p.is_file():
        return None
    return p.relative_to(root).as_posix()


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
    source = canonical_source(records, row["source"])
    if not source:
        errors.append(f"{where}: source {row['source']} is not a document in {records}/documents")
    for col in ("value", "ref_range"):
        if COMMA_DECIMAL.search(row.get(col, "")):
            errors.append(f"{where}: {col} {row[col]!r} has a decimal comma; write it with a dot")
    flag = row.get("flag", "").upper()
    if flag not in FLAGS:
        errors.append(f"{where}: flag {row['flag']!r} is not one of H, L, HH, LL, A or empty")

    unit = row.get("unit", "")
    name = row.get("name", "")
    known = names.resolve(row["original_name"], unit)
    if not name:
        if not known:
            errors.append(f"{where}: unknown analyte; give it a canonical `name` (see analytes.csv)")
        name = known or ""
    elif not known:
        names.learn(row["original_name"], name)
        notes.append(f"alias added: {row['original_name']!r} -> {name}")
    elif known != name and names.is_local(row["original_name"]):
        names.learn(row["original_name"], name)
        notes.append(f"alias changed: {row['original_name']!r} -> {name} (was {known})")
    elif known != name:
        notes.append(f"{where}: named {name} for this row; the analyte table says {known}")
    if errors:
        return None, errors, notes
    if names.unusual_unit(name, unit):
        notes.append(f"{where}: unit {unit!r} is unusual for {name}; check the name")

    loinc = row.get("loinc") or names.loinc_for(name, unit)
    calc = computed_flag(row["value"], row.get("ref_range", ""))
    if not flag and calc:
        flag = calc
        notes.append(f"{where}: flag {calc} computed from the range")
    elif calc is not None and flag in ("H", "L", "") and flag != calc:
        notes.append(f"{where}: report flag {flag or 'none'} but value/range say {calc or 'none'}; kept the report's")
    out = dict(row, name=name, loinc=loinc, unit=unit, flag=flag, source=source)
    return out, errors, notes


def merge(records: Path, staged: Path, clear: list[str]) -> int:
    names = Names(records)
    new, errors, notes = [], [], []
    cleared = set()
    for src in clear:
        c = canonical_source(records, src)
        if c:
            cleared.add(c)
        else:
            errors.append(f"--clear {src}: not a document in {records}/documents")
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
    sources = {r["source"] for r in new} | cleared
    kept = [r for r in old if r["source"] not in sources]
    replaced = len(old) - len(kept)
    rows = sorted(kept + new, key=lambda r: (r["name"].casefold(), r["date"], r["source"], r["original_name"]))
    write_csv(path, rows, COLUMNS)
    names.save()

    by_day = defaultdict(lambda: defaultdict(set))
    for r in rows:
        by_day[(r["name"], r["date"])][(r["value"], unit_key(r["unit"]))].add(r["source"])
    shared, conflicts = [], []
    for (n, d), vals in by_day.items():
        if len(vals) > 1:
            conflicts.append(f"{n} on {d}: {sorted(v for v, _ in vals)}")
        for (v, _), srcs in vals.items():
            if len(srcs) > 1 and srcs & sources:
                shared.append(f"{n} {d} {v}: {', '.join(sorted(srcs))}")

    print(f"markers.csv: {len(rows)} rows ({len(new)} from {len(sources)} source(s), {replaced} earlier rows replaced)")
    for title, items in (("Notes", notes),
                         ("Reported by more than one document (kept in each, counted once in trends)", shared),
                         ("Same analyte, same day, different values (check the sources)", conflicts)):
        if items:
            print(f"{title}:")
            print("\n".join(f"  {i}" for i in items))
    return 0


# ---------------------------------------------------------------- reading


def history(records: Path) -> dict[str, list[dict]]:
    """Each analyte's results, oldest first. A result several documents report (a lab value
    quoted in a discharge letter) counts once, from the first source."""
    out: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for r in sorted(read_csv(records / "markers.csv"), key=lambda r: (r["date"], r["source"])):
        key = (r["name"], r["date"], r["value"], unit_key(r["unit"]), r["source"])
        repeat = (r["name"], r["date"], r["value"], unit_key(r["unit"]))
        if repeat in seen and key not in seen:
            continue
        seen.update({key, repeat})
        out[r["name"]].append(r)
    return dict(sorted(out.items(), key=lambda kv: kv[0].casefold()))


def cell(r: dict, with_date=True, unit=False, ref=False) -> str:
    s = r["value"] + (f" {r['unit']}" if unit and r["unit"] else "") + (f" {r['flag']}" if r["flag"] else "")
    extra = [r["date"]] if with_date else []
    if ref and r["ref_range"]:
        extra.append(f"ref {r['ref_range']}")
    return f"{s} ({', '.join(extra)})" if extra else s


def esc(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def table(records: Path, name: str | None) -> int:
    hist = history(records)
    if name:
        hist = {k: v for k, v in hist.items() if name_key(name) in name_key(k)}
    print("| Analyte | LOINC | Unit | Reference | Results, oldest first |")
    print("|---|---|---|---|---|")
    for analyte, rows in hist.items():
        loincs = sorted({r["loinc"] for r in rows if r["loinc"]})
        many_units = len({unit_key(r["unit"]) for r in rows}) > 1
        refs = {r["ref_range"] for r in rows}
        many_refs = len(refs) > 1
        unit = "per result" if many_units else rows[0]["unit"]
        ref = "per result" if many_refs else rows[0]["ref_range"]
        values = "; ".join(cell(r, unit=many_units, ref=many_refs) for r in rows)
        print(f"| {esc(analyte)} | {', '.join(loincs)} | {esc(unit)} | {esc(ref)} | {esc(values)} |")
    return 0


def problems(records: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    known = Names(records).known
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
    for rels in shas.values():
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
        if analyte not in known and not any(r["loinc"] for r in rows):
            warnings.append(f"{analyte}: no LOINC; look one up (see references/loinc.md)")
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
        earlier = "; ".join(cell(r, unit=unit_key(r["unit"]) != unit_key(last["unit"]))
                            for r in reversed(rows[-4:-1]))
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
    m.add_argument("--clear", action="append", default=[], metavar="SOURCE",
                   help="also drop this document's rows when the staged file has none for it")
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
        return merge(args.records, args.rows, args.clear)
    if args.cmd == "index":
        return index(args.records)
    if args.cmd == "table":
        return table(args.records, args.name)
    return check(args.records)


if __name__ == "__main__":
    sys.exit(main())
