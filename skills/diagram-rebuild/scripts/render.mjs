// Render a diagram source to PNG.
// Usage: node render.mjs <input.html|input.excalidraw> <output.png> [scale=2]
//   .html        screenshots the first <svg> (diagram-design output)
//   .excalidraw  exports through Excalidraw's own exportToSvg, then screenshots it
// Requires the toolchain from setup.sh (DIAGRAM_REBUILD_HOME, default ~/.cache/diagram-rebuild).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";

const [input, output, scaleArg] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: node render.mjs <input.html|input.excalidraw> <output.png> [scale=2]");
  process.exit(2);
}

const home = process.env.DIAGRAM_REBUILD_HOME ?? path.join(os.homedir(), ".cache", "diagram-rebuild");
const bundle = path.join(home, "dist", "excalidraw.js");
if (!fs.existsSync(bundle)) {
  console.error(`toolchain missing in ${home}; run: bash ${path.join(path.dirname(new URL(import.meta.url).pathname), "setup.sh")}`);
  process.exit(1);
}
const { chromium } = createRequire(path.join(home, "package.json"))("playwright");

// Module scripts cannot load from file://, so the Excalidraw page is served from a fake origin.
const ORIGIN = "http://render.local";
const HOST_PAGE = `<!doctype html><html><head><meta charset="utf-8">
<script type="module" src="/excalidraw.js"></script></head>
<body style="margin:0;background:#fff"><div id="out"></div></body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: Number(scaleArg ?? 2), viewport: { width: 1600, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));

try {
  if (input.endsWith(".excalidraw")) {
    const scene = JSON.parse(fs.readFileSync(input, "utf8"));
    await page.route(`${ORIGIN}/**`, (route) => {
      const { pathname } = new URL(route.request().url());
      if (pathname === "/") return route.fulfill({ body: HOST_PAGE, contentType: "text/html" });
      if (pathname === "/excalidraw.js") return route.fulfill({ path: bundle, contentType: "text/javascript" });
      return route.fulfill({ status: 404 });
    });
    await page.goto(`${ORIGIN}/`);
    await page.waitForFunction(() => window.excalidrawReady === true, null, { timeout: 30000 });
    await page.evaluate(async (scene) => {
      const svg = await window.exportToSvg({
        elements: scene.elements,
        // Excalidraw defaults exportScale to devicePixelRatio, which would apply the scale argument twice.
        appState: { exportBackground: true, viewBackgroundColor: "#ffffff", ...(scene.appState ?? {}), exportWithDarkMode: false, exportScale: 1 },
        files: scene.files ?? {},
        exportPadding: 24,
      });
      document.getElementById("out").appendChild(svg);
      await document.fonts.ready;
    }, scene);
    // Excalidraw embeds its fonts asynchronously after the SVG is attached.
    await page.waitForTimeout(1500);
  } else {
    await page.goto(`file://${path.resolve(input)}`, { waitUntil: "networkidle", timeout: 20000 }).catch(() => {});
    await page.evaluate(() => document.fonts.ready);
  }

  const svg = page.locator("svg").first();
  const box = await svg.boundingBox();
  if (box) {
    await page.setViewportSize({
      width: Math.ceil(Math.max(1600, box.x + box.width + 40)),
      height: Math.ceil(Math.max(1000, box.y + box.height + 40)),
    });
  }
  await svg.screenshot({ path: output });
  console.log(`wrote ${output}`);
  if (errors.length) console.error(`page errors:\n${errors.join("\n")}`);
} finally {
  await browser.close();
}
