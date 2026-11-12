# Extracting a PDF without reading it directly

Use this when your model cannot read PDFs, or a PDF read comes back empty or truncated.

```bash
uv run <skill>/scripts/extract.py <pdf> --out <scratch>/extract --records <records>
```

Each PDF gets a work folder with `page-NNN.txt` (the text layer), page images where needed, and
`meta.json`. Each page's verdict says how to read it:

- `text`: read the `.txt`. When a table's columns come out scrambled, rerun that PDF with
  `--images all` and read the page image too. Set `extraction: text`.
- `scan`: read the `.png` with your own vision. Set `extraction: vision`.
- `text+image`: read both; the image may carry content the text layer lacks.

Set `extraction: mixed` when a document's pages were read in more than one way.
