#!/usr/bin/env python3
"""Write <workspace>/gallery.html: each original beside the latest render of every track.

Usage: python3 gallery.py <workspace>
Expects <workspace>/<id>/original.png and <workspace>/<id>/<track>/vN.png.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

TRACK_NAMES = {"ex": "Excalidraw", "dd": "diagram-design"}


def latest_render(track_dir: Path) -> Path | None:
    versions = [(int(m.group(1)), p) for p in track_dir.glob("v*.png") if (m := re.fullmatch(r"v(\d+)\.png", p.name))]
    return max(versions)[1] if versions else None


def main() -> None:
    workspace = Path(sys.argv[1]).resolve()
    sections = []
    for item in sorted(p for p in workspace.iterdir() if (p / "original.png").is_file()):
        cells = [("Original", item / "original.png")]
        for track_dir in sorted(p for p in item.iterdir() if p.is_dir() and p.name in TRACK_NAMES):
            if render := latest_render(track_dir):
                cells.append((f"{TRACK_NAMES[track_dir.name]} ({render.stem})", render))
        figures = "".join(
            f'<figure><figcaption>{html.escape(label)}</figcaption>'
            f'<a href="{path.relative_to(workspace)}" target="_blank"><img src="{path.relative_to(workspace)}" alt="{html.escape(label)}"></a></figure>'
            for label, path in cells
        )
        sections.append(f'<section><h2>{html.escape(item.name)}</h2><div class="row" style="--n:{len(cells)}">{figures}</div></section>')

    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Diagram rebuilds</title><style>
body{{font:14px/1.4 -apple-system,system-ui,sans-serif;margin:24px;background:#fafafa;color:#222}}
h2{{font-size:15px;margin:28px 0 8px}}
.row{{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:12px}}
figure{{margin:0;background:#fff;border:1px solid #ddd;border-radius:6px;padding:8px}}
figcaption{{font-weight:600;margin-bottom:6px}} img{{width:100%;height:auto;display:block}}
</style></head><body><h1>Diagram rebuilds</h1>{"".join(sections)}</body></html>"""
    out = workspace / "gallery.html"
    out.write_text(page)
    print(out)


if __name__ == "__main__":
    main()
