---
name: diagram-rebuild
description: Rebuild diagrams that exist only as images into editable Excalidraw or diagram-design source, verified by independent visual review. Use when the user wants to recreate, redraw, or make editable a diagram from a screenshot, PNG, or exported image.
---

# Diagram rebuild

A rebuild keeps every piece of the original's content and lets the target style decide the look. Quality comes from a loop: a **builder** draws, a **reviewer** with fresh eyes compares the render against the original, and the builder fixes what the reviewer found.

## Requirements

- `node` and `npm`, for the render toolchain [scripts/setup.sh](scripts/setup.sh) installs: Playwright with Chromium, `@excalidraw/excalidraw`, React, and esbuild.
- `python3` for the gallery. Builders and reviewers crop with Pillow; `uv run --with pillow python` supplies it when the system Python lacks it.
- The `dd` track runs the [`diagram-design`](https://github.com/cathrynlavery/diagram-design) skill from cathrynlavery/diagram-design. That skill stays the source for the `dd` style, skins, and self-check. When it is not installed, run `ex` alone and tell the user.

## Subagents

Builders and reviewers run as subagents:

| Harness | Start one | Send a builder its fixes |
|---|---|---|
| T3 Code | `delegate_task` | `t3_thread_send` to the builder's thread |
| Claude Code | `Agent` | `SendMessage` to the builder |
| Other | The harness's subagent tool | Its follow-up message, if it has one |
| No subagents | Build yourself | - |

A builder that cannot take a follow-up is replaced by a new one pointed at the same item folder; the generator and renders there carry its work.

A reviewer is always a **fresh context** that has never seen the builder's notes or earlier reviews. Without a subagent tool, run each review as a one-shot agent CLI (`claude -p`, `codex exec`, `gemini -p`) given the brief and both image paths. When no fresh context is available at all, stop and tell the user rather than reviewing your own builds.

## Steps

1. **Set up the workspace.** Create a scratch folder outside any repository unless the user names a location; the originals may be private. Copy each source image to `<workspace>/<id>/original.png`, skipping byte-identical duplicates. Images that share one layout with small changes form a variant group: one builder builds the group from a shared generator, and one reviewer checks it. Run `bash <skill-dir>/scripts/setup.sh`; it installs the pinned render toolchain once into `~/.cache/diagram-rebuild` (override with `DIAGRAM_REBUILD_HOME`). Done when setup prints `toolchain ready` or `toolchain installed`.

2. **Choose the tracks.** Run both tracks by default so the user can compare: `ex` (Excalidraw: editable, hand-drawn, the natural fit for whiteboard-style diagrams) and `dd` (diagram-design: an editorial style, in the project's saved skin or the default one). A format the user names runs that track alone. Tell the user the plan in one line.

3. **Build.** Start one builder per item (or variant group) and track, in parallel up to the harness's concurrent-subagent limit; queue the rest and start them as slots free up. Give each the path to [references/builder-brief.md](references/builder-brief.md), this skill's directory, the item folder, the track, for `dd` the diagram-design skill's directory, and one sentence naming the diagram's kind and subject ("a fan-out of three API clients into an order service"), not a content inventory, so the builder reads the image itself. Done when every builder reports a rendered `vN.png`.

4. **Review.** For each new render, start a fresh reviewer with the path to [references/reviewer-brief.md](references/reviewer-brief.md), the original, and the render. Give it `<item>/<track>/review-vN/` as its crop folder. The reviewer sees only images and the brief. For a pair of related images, one reviewer checks both and confirms they share positions and names.

5. **Loop.** On `ITERATE`, send the fixes to the builder; then review the new version with another fresh reviewer. On `PASS`, look at the render yourself: when a listed fix is a text collision or unreadable text, send one polish round and check the result yourself; optional fixes are skipped. When a fix contradicts an earlier round, or a builder note contradicts the render, settle it against the original yourself. Stop each item at `PASS` or after four rounds. Done when every item has passed or hit the cap with its remaining differences written down.

6. **Deliver.** Run `python3 <skill-dir>/scripts/gallery.py <workspace>` and open the resulting `gallery.html` for the user (`open` on macOS, `xdg-open` on Linux; a headless run reports the path), which shows each original beside the latest render of every track. Report a table of items, tracks, final versions, and scores, then the content the builders could not read, the typos they fixed, and the deliberate deviations.

## Rendering

`node <skill-dir>/scripts/render.mjs <source> <output.png> [scale]` renders `.excalidraw` scenes through Excalidraw's own exporter, with its real fonts, and screenshots the first `<svg>` of a diagram-design `.html` file.

## Where rebuilds go wrong

| Symptom | Fix |
|---|---|
| Captions or names on unlabeled icons; legend entries that interpret unlabeled marks | Unlabeled stays unlabeled; legends use only the original's wording |
| A focal accent added to an element that is plain in the original | Emphasis matches the original exactly |
| Doubled lines in Excalidraw | `roughness: 0` on long connectors and boundaries |
| diagram-design caps labels too small to read; red annotations neutralized | Content outranks the style's budgets; see the `dd` section of the builder brief |
| Reviewers asking for opposite changes in successive rounds | The orchestrator decides against the original; the four-round cap holds |
