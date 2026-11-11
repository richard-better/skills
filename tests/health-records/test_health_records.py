"""Tests for the health-records skill's scripts, run the way an agent runs them: `uv run <script>`.

Run: uv run --with pytest --with pymupdf==1.26.5 pytest tests/health-records
All data is synthetic.
"""

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from make_pdfs import make_all

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "health-records" / "scripts"
LAB = "documents/2025-03-14_lab_example-lab.md"
LETTER = "documents/2025-05-02_discharge_riverside.md"


def run(script: str, *args, check=True) -> subprocess.CompletedProcess:
    p = subprocess.run(["uv", "run", "-q", str(SCRIPTS / script), *map(str, args)],
                       capture_output=True, text=True)
    if check and p.returncode != 0:
        raise AssertionError(f"{script} {args} exited {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def doc(records: Path, rel: str, **fm) -> None:
    fields = dict(date="2025-03-14", type="lab", provider="Example Lab", title="Labs", language="hu",
                  source=Path(rel).with_suffix(".pdf").name, sha256=hashlib.sha256(rel.encode()).hexdigest(), extraction="text",
                  summary="Synthetic.")
    fields.update(fm)
    path = records / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    head = "\n".join(f"{k}: {v}" for k, v in fields.items())
    path.write_text(f"---\n{head}\n---\n\n# Body\n", encoding="utf-8")
    path.with_suffix(".pdf").write_bytes(b"%PDF-1.7\n")


def stage(path: Path, rows: list[dict]) -> Path:
    cols = ["original_name", "name", "value", "unit", "ref_range", "flag", "date", "source"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({"date": "2025-03-14", "source": LAB, **r})
    return path


def markers(records: Path) -> list[dict]:
    with (records / "markers.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- extract.py


@pytest.fixture(scope="module")
def extracted(tmp_path_factory):
    root = tmp_path_factory.mktemp("extract")
    files = make_all(root / "inbox")
    p = run("extract.py", root / "inbox", "--out", root / "work", check=False)
    metas = {Path(m["file"]).name: m for m in
             (json.loads(f.read_text()) for f in (root / "work").glob("*/meta.json"))}
    return root, files, p, metas


def test_text_pdf_keeps_hungarian_and_expands_ligatures(extracted):
    root, files, _, metas = extracted
    meta = metas[files["lab"].name]
    assert [p["verdict"] for p in meta["pages"]] == ["text", "text"]
    work = Path(meta["dir"])
    p1 = (work / "page-001.txt").read_text()
    p2 = (work / "page-002.txt").read_text()
    assert "Glükóz" in p1 and "6,4" in p1 and "Összkoleszterin" in p1
    assert "fl" in p2 and "ﬂ" not in p2
    assert not list(work.glob("*.png"))


def test_scan_gets_a_page_image(extracted):
    _, files, _, metas = extracted
    page = metas[files["scan"].name]["pages"][0]
    assert page["verdict"] == "scan" and page["chars"] == 0
    assert (Path(metas[files["scan"].name]["dir"]) / page["image"]).stat().st_size > 10_000


def test_text_with_large_image_gets_both(extracted):
    _, files, _, metas = extracted
    page = metas[files["mixed"].name]["pages"][0]
    assert page["verdict"] == "text+image" and "image" in page


def test_bad_pdfs_fail_without_stopping_the_batch(extracted):
    _, files, p, metas = extracted
    assert p.returncode == 1
    assert "encrypted" in p.stdout and files["corrupt"].name in p.stdout
    assert "same file as" in p.stdout
    assert set(metas) == {files["lab"].name, files["scan"].name, files["mixed"].name}


def test_records_flag_skips_known_pdfs(extracted, tmp_path):
    root, files, _, metas = extracted
    records = tmp_path / "records"
    doc(records, LAB, sha256=f'"{metas[files["lab"].name]["sha256"]}"')
    p = run("extract.py", files["lab"], files["scan"], "--out", tmp_path / "work", "--records", records)
    assert "already in records" in p.stdout
    assert [d.name.split("-")[0] for d in (tmp_path / "work").iterdir()] == ["scan0001"]


# ---------------------------------------------------------------- records.py merge


@pytest.fixture
def records(tmp_path):
    r = tmp_path / "records"
    doc(r, LAB)
    doc(r, LETTER, date="2025-05-02", type="discharge", language="en")
    return r


def test_merge_names_codes_and_flags(records, tmp_path):
    rows = stage(tmp_path / "rows.csv", [
        {"original_name": "Glükóz", "value": "6.4", "unit": "mmol/l", "ref_range": "3.9-6.0", "flag": "H"},
        {"original_name": "Fehérvérsejt", "value": "5.9", "unit": "G/l", "ref_range": "4.4-12.4"},
        {"original_name": "MCV", "value": "78.1", "unit": "fl", "ref_range": "80.0-95.0"},
        {"original_name": "Glucose", "value": "110", "unit": "mg/dL", "ref_range": "70-99", "date": "2024-01-02"},
    ])
    run("records.py", "merge", records, rows)
    got = {(m["name"], m["date"]): m for m in markers(records)}
    assert got[("Glucose", "2025-03-14")]["loinc"] == "14749-6"
    assert got[("Glucose", "2024-01-02")]["loinc"] == "2345-7"
    assert got[("Glucose", "2024-01-02")]["flag"] == "H"
    assert got[("WBC", "2025-03-14")]["loinc"] == "6690-2"
    assert got[("MCV", "2025-03-14")]["flag"] == "L"
    assert [m["name"] for m in markers(records)] == ["Glucose", "Glucose", "MCV", "WBC"]


def test_merge_is_idempotent_and_replaces_by_source(records, tmp_path):
    first = stage(tmp_path / "a.csv", [
        {"original_name": "Ferritin", "value": "18", "unit": "ug/l", "ref_range": "20-250"},
        {"original_name": "Gluocse", "name": "Glucose", "value": "6.4", "unit": "mmol/l"},
    ])
    run("records.py", "merge", records, first)
    before = (records / "markers.csv").read_text()
    run("records.py", "merge", records, first)
    assert (records / "markers.csv").read_text() == before

    fixed = stage(tmp_path / "b.csv", [
        {"original_name": "Ferritin", "value": "16", "unit": "ug/l", "ref_range": "20-250"},
    ])
    run("records.py", "merge", records, fixed)
    assert [(m["name"], m["value"]) for m in markers(records)] == [("Ferritin", "16")]


def test_merge_rejects_bad_rows_and_writes_nothing(records, tmp_path):
    rows = stage(tmp_path / "rows.csv", [
        {"original_name": "Ferritin", "value": "18", "unit": "ug/l"},
        {"original_name": "Glükóz", "value": "6,4", "unit": "mmol/l"},
        {"original_name": "Mystery marker", "value": "3"},
        {"original_name": "CRP", "value": "2", "date": "14.03.2025"},
        {"original_name": "CRP", "value": "2", "source": "documents/missing.md"},
        {"original_name": "CRP", "value": "2", "flag": "+"},
    ])
    p = run("records.py", "merge", records, rows, check=False)
    assert p.returncode == 1
    for needle in ("decimal comma", "unknown analyte", "YYYY-MM-DD", "does not exist", "flag '+'"):
        assert needle in p.stdout
    assert not (records / "markers.csv").exists()


def test_merge_learns_aliases(records, tmp_path):
    run("records.py", "merge", records, stage(tmp_path / "a.csv", [
        {"original_name": "Lp(a) frakció", "name": "Lipoprotein(a)", "value": "41", "unit": "mg/dl"},
    ]))
    assert "Lp(a) frakció,Lipoprotein(a)" in (records / "aliases.csv").read_text()
    run("records.py", "merge", records, stage(tmp_path / "b.csv", [
        {"original_name": "LP(A) FRAKCIO", "value": "38", "unit": "mg/dl", "source": LETTER, "date": "2025-05-02"},
    ]))
    assert [m["name"] for m in markers(records)] == ["Lipoprotein(a)", "Lipoprotein(a)"]
    assert markers(records)[0]["loinc"] == "10835-7"


def test_merge_drops_cross_source_duplicates_and_reports_conflicts(records, tmp_path):
    run("records.py", "merge", records, stage(tmp_path / "a.csv", [
        {"original_name": "CRP", "value": "86", "unit": "mg/L", "date": "2025-05-02"},
        {"original_name": "WBC", "value": "13.2", "unit": "G/l", "date": "2025-05-02"},
    ]))
    p = run("records.py", "merge", records, stage(tmp_path / "b.csv", [
        {"original_name": "CRP", "value": "86", "unit": "mg/l", "date": "2025-05-02", "source": LETTER},
        {"original_name": "WBC", "value": "13.8", "unit": "x10^9/L", "date": "2025-05-02", "source": LETTER},
    ]))
    assert "Duplicates dropped" in p.stdout and "different values" in p.stdout
    assert [(m["name"], m["source"]) for m in markers(records)] == [
        ("CRP", LAB), ("WBC", LAB), ("WBC", LETTER)]


def test_report_flag_disagreeing_with_range_is_kept_and_noted(records, tmp_path):
    p = run("records.py", "merge", records, stage(tmp_path / "a.csv", [
        {"original_name": "Hemoglobin", "value": "150", "unit": "g/l", "ref_range": "140-175", "flag": "L"},
    ]))
    assert "kept the report's" in p.stdout
    assert markers(records)[0]["flag"] == "L"


# ---------------------------------------------------------------- index, table, check


def test_index_table_and_check(records, tmp_path):
    (records / "context.md").write_text("# Context\n")
    (records / "panels").mkdir()
    (records / "panels" / "2025-06-01-differential-panel.md").write_text("# Panel\n")
    run("records.py", "merge", records, stage(tmp_path / "a.csv", [
        {"original_name": "Ferritin", "value": v, "unit": "ug/l", "ref_range": "20-250", "date": d}
        for v, d in [("40", "2023-01-01"), ("31", "2024-01-01"), ("18", "2025-03-14")]
    ]))
    run("records.py", "index", records)
    index = (records / "index.md").read_text()
    assert "[context.md](context.md)" in index
    assert "| Ferritin | 18 L | ug/l | 20-250 | 2025-03-14 | 31 (2024-01-01); 40 (2023-01-01) | 3 | 1 |" in index
    assert "(panels/2025-06-01-differential-panel.md)" in index
    assert f"]({LETTER})" in index

    table = run("records.py", "table", records, "--name", "ferr").stdout
    assert "40 (2023-01-01); 31 (2024-01-01); 18 L (2025-03-14)" in table

    p = run("records.py", "check", records)
    assert "documents/2025-05-02_discharge_riverside.md" not in p.stdout  # not a lab document


def test_check_catches_broken_folders(records):
    doc(records, "documents/2025-07-01_lab_other.md", type="bloodwork", sha256=hashlib.sha256(LAB.encode()).hexdigest())
    (records / "documents" / "2025-07-01_lab_other.pdf").unlink()
    p = run("records.py", "check", records, check=False)
    assert p.returncode == 1
    assert "type 'bloodwork'" in p.stdout
    assert "source PDF" in p.stdout
    assert "same PDF extracted twice" in p.stdout
    assert "lab document with no rows" in p.stdout
