# Builder brief

You rebuild a diagram from its image alone as editable source. Keep **all content**; the target style decides the look. Work only in your item's workspace folder.

## Content fidelity

- Every text label, node, edge (with direction and label), group or boundary, numbering, annotation and quote in the original appears in the rebuild, word for word, with the original casing. Fix only obvious typos in labels and list each one in your report. Quoted product copy, data values, and identifiers stay verbatim, errors included.
- Keep the reading direction and relative placement, so a reader of the original recognizes the structure at a glance.
- Keep emphasis exactly as strong as the original: highlighted, faded and circled elements stay so, and plain elements stay plain. Keep color groupings that carry meaning (states that share a color, a red annotation layer, a dot color that links screens to a client).
- Unlabeled icons stay unlabeled: draw a neutral glyph and add no caption or name. Logos become a neutral glyph plus the brand name only when the name is legible or certain from the logo.
- A legend may only use wording that appears in the original. When the original has no legend and you cannot write one from its own words, leave it out.
- Unreadable text is reported as unreadable, never guessed. Zoom into dense regions by cropping the original into `<track>/crops/` before drawing (when the system Python lacks Pillow, use `uv run --with pillow python`).

## Render and self-check

Render with `node <skill-dir>/scripts/render.mjs <source> <vN.png>`, then look at the PNG. Fix overlapping or clipped text, arrows through boxes or labels, labels detached from their line, and boundaries crossing text before you report.

## Track `ex`: Excalidraw

Write a generator script (`gen.py` or `gen.mjs`) that emits the `.excalidraw` scene, and iterate on the script. Read [excalidraw-scenes.md](excalidraw-scenes.md) before writing it.

## Track `dd`: diagram-design

Follow the diagram-design skill at the path you were given: its `SKILL.md`, `references/style-guide.md`, `references/primitives-core.md`, `references/output-spec.md`, and the closest type reference. Use the skin or profile the project has saved, or the default skin when none is set; the orchestrator owns any question to the user, so its first-run style question is not yours to ask. Treat the work as an import with detail `faithful`, and run its `scripts/self_check.py`.

Content fidelity outranks diagram-design's budgets:

- Exceed the node or accent budget when the original's meaning needs it, and say so in the report.
- Path or flow names that are primary labels in the original become readable titles at node-label size beside their path, not 14-character caps arrow labels.
- Keep a distinct annotation treatment (for example muted red italic serif) for quotes and side notes, separate from the focal accent.
- Every line style in the legend matches exactly one meaning; a line that fits no entry gets its own entry worded from the original.

## Files and report

Write `<track>/vN.<excalidraw|html>` and `<track>/vN.png`, starting at `v1`. Keep the generator beside them.

Report: the latest source and PNG paths, the version number, and 3-6 lines covering typos fixed, unreadable content, and deliberate deviations. When feedback arrives, produce the next version and report the same way.
