// Browser entry bundled by setup.sh: exposes Excalidraw's own SVG exporter to render.mjs.
import { exportToSvg } from "@excalidraw/excalidraw";

window.exportToSvg = exportToSvg;
window.excalidrawReady = true;
