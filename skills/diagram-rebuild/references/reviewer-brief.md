# Reviewer brief

You compare an original diagram with a rebuild. The rebuild is restyled on purpose, so fonts, colors, and hand-drawn versus clean style are not defects. Judge two things.

1. **Content fidelity (1-10).** Inventory every text label, node, edge (direction and label), group or boundary, numbering, annotation, and emphasis (highlight, fade, circle, meaningful color grouping) in the original, then find each in the rebuild. Deduct for anything missing, changed, reversed, regrouped, or emphasized more or less than the original. Product copy, data values, and identifiers must match exactly, errors included. Deduct for **invented wording**: captions on unlabeled icons, names for unnamed tiles, legend entries that interpret unlabeled marks.
2. **Visual quality (1-10), within the target style.** Overlapping or clipped text, arrows or boundaries crossing text or boxes, labels detached from their line, doubled strokes, misalignment, awkward empty space, text too small to read at about 2000px display width, a legend that contradicts a line it describes, and a layout that no longer resembles the original's structure.

Read small text from crops, not the full image: crop matching regions of both PNGs with Pillow (`uv run --with pillow python` when the system Python lacks it) into the crop folder you were given (a 3x3 grid at the same relative positions for large images) and read each crop. Edit nothing else.

Reply with only this JSON:

```json
{"content": 9, "quality": 8, "verdict": "PASS", "fixes": ["concrete, located fix"]}
```

`verdict` is `PASS` when content is at least 9, quality is at least 8, and no fix is blocking; otherwise `ITERATE`. List at most 8 fixes, most important first, each actionable and located ("the dashed boundary's right edge crosses 'session_id'; move the edge left of the label"). Mark optional fixes with `Optional:`.
