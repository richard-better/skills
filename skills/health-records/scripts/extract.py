#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf==1.26.5"]
# ///
"""Pull the text layer out of health PDFs, page by page, and render the pages that need eyes.

Usage: uv run extract.py <pdf-or-folder>... --out <work-dir> [--records <records-dir>]
                         [--images needed|all|none] [--dpi 200] [--min-chars 40]

For each PDF, writes <work-dir>/<stem>-<sha8>/ with:

- page-NNN.txt  the page's text layer in reading order (empty for a scan)
- page-NNN.png  the page rendered as an image, for pages whose verdict is not `text`
                (every page with --images all)
- meta.json     sha256, page count, PDF metadata, and per page: chars, image coverage, verdict

A page's verdict:

- text        the text layer holds the page; read the .txt
- scan        no usable text layer; read the .png
- text+image  a text layer plus a large image (a stamp, an embedded scan, a chart); read both

With --records, PDFs whose sha256 already appears in <records-dir>/documents/*.md frontmatter
are skipped, so a rerun over the same folder only extracts new files. Encrypted PDFs are
reported and skipped. Prints one line per PDF and exits non-zero if any PDF failed to open.
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

# Expand ligatures (the "fl" in "fl" units must not come out as one glyph), keep everything else.
TEXT_FLAGS = pymupdf.TEXTFLAGS_TEXT & ~pymupdf.TEXT_PRESERVE_LIGATURES
SHA_LINE = re.compile(r"""^sha256:\s*["']?([0-9a-f]{64})["']?\s*$""", re.MULTILINE)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def known_hashes(records: Path) -> set[str]:
    docs = records / "documents"
    if not docs.is_dir():
        return set()
    found = set()
    for md in docs.glob("*.md"):
        head = md.read_text(encoding="utf-8", errors="replace")[:4000]
        found.update(SHA_LINE.findall(head))
    return found


def usable_chars(text: str) -> int:
    """Count characters a reader could use: letters, digits, punctuation. A broken font map
    yields U+FFFD, private-use glyphs or control codes instead."""
    good = 0
    for ch in text:
        if ch.isspace():
            continue
        cat = unicodedata.category(ch)
        if ch == "�" or cat in ("Co", "Cc", "Cn"):
            continue
        good += 1
    return good


def image_coverage(page: "pymupdf.Page") -> float:
    area = abs(page.rect)
    if not area:
        return 0.0
    covered = 0.0
    for info in page.get_image_info():
        r = pymupdf.Rect(info["bbox"]) & page.rect
        covered += abs(r)
    return min(covered / area, 1.0)


def verdict(chars: int, coverage: float, min_chars: int) -> str:
    if chars < min_chars:
        return "scan"
    if coverage >= 0.25:
        return "text+image"
    return "text"


def extract(pdf: Path, out_root: Path, images: str, dpi: int, min_chars: int, digest: str) -> dict:
    doc = pymupdf.open(pdf)
    if doc.needs_pass:
        return {"file": str(pdf), "sha256": digest, "error": "encrypted: ask the owner for the password"}
    out = out_root / f"{pdf.stem}-{digest[:8]}"
    out.mkdir(parents=True, exist_ok=True)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text", sort=True, flags=TEXT_FLAGS)
        chars = usable_chars(text)
        cov = image_coverage(page)
        v = verdict(chars, cov, min_chars)
        (out / f"page-{i:03d}.txt").write_text(text, encoding="utf-8")
        entry = {"page": i, "chars": chars, "image_coverage": round(cov, 2), "verdict": v, "text": f"page-{i:03d}.txt"}
        if images == "all" or (images == "needed" and v != "text"):
            name = f"page-{i:03d}.png"
            page.get_pixmap(dpi=dpi).save(out / name)
            entry["image"] = name
        pages.append(entry)
    meta = {
        "file": str(pdf),
        "sha256": digest,
        "page_count": doc.page_count,
        "metadata": {k: v for k, v in (doc.metadata or {}).items() if v},
        "pages": pages,
        "dir": str(out),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return meta


def collect(inputs: list[str]) -> list[Path]:
    pdfs: list[Path] = []
    for raw in inputs:
        p = Path(raw).expanduser()
        if p.is_dir():
            pdfs.extend(sorted(q for q in p.rglob("*") if q.is_file() and q.suffix.lower() == ".pdf"))
        elif p.is_file():
            pdfs.append(p)
        else:
            print(f"missing: {p}", file=sys.stderr)
    return pdfs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inputs", nargs="+", help="PDF files or folders (searched recursively)")
    ap.add_argument("--out", required=True, type=Path, help="work directory for page text and images")
    ap.add_argument("--records", type=Path, help="records folder: skip PDFs already extracted there")
    ap.add_argument("--images", choices=["needed", "all", "none"], default="needed")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--min-chars", type=int, default=40, help="below this a page counts as a scan")
    args = ap.parse_args()

    known = known_hashes(args.records) if args.records else set()
    seen: dict[str, Path] = {}
    failed = 0
    for pdf in collect(args.inputs):
        digest = sha256(pdf)
        if digest in known:
            print(f"skip   {pdf}  (already in records)")
            continue
        if digest in seen:
            print(f"skip   {pdf}  (same file as {seen[digest]})")
            continue
        seen[digest] = pdf
        try:
            meta = extract(pdf, args.out, args.images, args.dpi, args.min_chars, digest)
        except Exception as e:  # a corrupt PDF must not stop the batch
            print(f"FAIL   {pdf}  {type(e).__name__}: {e}")
            failed += 1
            continue
        if "error" in meta:
            print(f"FAIL   {pdf}  {meta['error']}")
            failed += 1
            continue
        counts: dict[str, int] = {}
        for p in meta["pages"]:
            counts[p["verdict"]] = counts.get(p["verdict"], 0) + 1
        summary = ", ".join(f"{n} {v}" for v, n in sorted(counts.items()))
        print(f"ok     {pdf}  {meta['page_count']} pages ({summary})  -> {meta['dir']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
