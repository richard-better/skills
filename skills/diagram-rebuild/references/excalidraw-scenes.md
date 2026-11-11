# Writing Excalidraw scenes

A scene is `{"type": "excalidraw", "version": 2, "elements": [...], "appState": {}, "files": {}}`. Every element needs a unique `id` and `seed`, plus `angle`, `strokeColor`, `backgroundColor`, `fillStyle`, `strokeWidth`, `strokeStyle`, `roughness`, `opacity`, `groupIds`, `frameId`, `roundness`, `version`, `versionNonce`, `isDeleted`, `boundElements`, `updated`, `link`, and `locked`. Generate them from one helper so no field is forgotten.

## Look

- Fonts: `fontFamily: 5` (Excalifont) for prose labels and `fontFamily: 3` (monospace) for identifiers, API names, and code.
- Fills: Excalidraw pastels such as `#ffec99`, `#ffc9c9`, `#d0bfff`, `#b2f2bb`, `#a5d8ff`, `#e9ecef`, with a darker stroke in the same hue. Dashed grey rectangles mark system boundaries; red text marks annotations.
- `roughness: 1` for boxes, glyphs, and short strokes. Use `roughness: 0` for long connectors, lane boundaries, and large rectangles: at roughness 1 Excalidraw draws long lines as two near-parallel strokes that read as doubled lines. Filled boxes can show the same doubled edge with a sliver between fill and stroke; use `fillStyle: "solid"` and roughness 0 for any box where it appears.

## Text

- Text inside a shape is bound: the text has `containerId`, and the container lists `{"type": "text", "id": ...}` in `boundElements`. A container holds one bound text.
- A text element has one font size and one color. Mixed styling ("Product Screens" plus a red "(100+)", a title above bullets) is split into separate text elements grouped with the shape.
- Rotated text (for example a vertical strip label) is a free text with `angle`, centered on the shape rather than bound to it.
- Set `width` and `height` from the content: about 0.55 x fontSize per character for Excalifont (it runs slightly long, so check the render) and 1.25 x fontSize per line.
- Arrow labels sit as separate texts beside the line, not bound onto the arrow, so the stroke never runs through the text.

## Arrows

- Connect shapes with `startBinding` and `endBinding` (`{"elementId": ..., "focus": 0, "gap": 4}`) and list the arrow in both shapes' `boundElements`.
- `points` are relative to the arrow's `x` and `y`. Orthogonal routes are multi-point arrows.
- Rounded elbows: Excalidraw's curved-arrow `roundness` bows the whole route into a wide curve. Keep straight runs straight and add short arc segments at the corners instead.
- Merging lines end where they meet the main line, without their own arrowhead, so only one arrowhead enters the target.
