"""Build a checklist page of an iPhone's removable apps with App Store icons.

Usage: python3 -I scripts/build_app_page.py <devicectl apps.json> <icon cache dir> <out.html> <device label> [--embed]

--embed links icons from Apple's CDN instead of inlining them and uses the host's theme
variables, so the page stays small enough to render inline in T3 Code.
"""

import base64
import html
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

COUNTRIES = ["us", "hu", "gb", "de", "jp", "cn", "kr", "vn", "ua", "dk", "cz", "pl", "es", "nl", "fr", "lt"]
BATCH = 50
EMBED_CSS = """<style>
  :root { --bg: var(--background); --surface: var(--card); --text: var(--foreground); --muted: var(--muted-foreground);
          --line: var(--border); --accent: var(--destructive); --accent-soft: var(--destructive-surface); }
  body { background: none; }
  header { padding: 12px 0; background: var(--background); backdrop-filter: none; -webkit-backdrop-filter: none; }
  header h1 { display: none; }
  .tools { margin-left: 0; }
  main { padding: 0 0 80px; }
</style>
"""


def fetch(url):
    return subprocess.run(["curl", "-fsSL", "--max-time", "30", "--retry", "3", "--retry-all-errors", url], check=True, capture_output=True).stdout


def fetch_json(url):
    return json.loads(fetch(url))


def lookup_artwork(bundle_ids):
    artwork = {}
    remaining = list(bundle_ids)
    for country in COUNTRIES:
        if not remaining:
            break
        for i in range(0, len(remaining), BATCH):
            chunk = remaining[i : i + BATCH]
            query = urllib.parse.urlencode({"bundleId": ",".join(chunk), "country": country, "entity": "software"})
            try:
                data = fetch_json(f"https://itunes.apple.com/lookup?{query}")
            except Exception as err:
                print(f"lookup failed ({country}): {err}", file=sys.stderr)
                continue
            for result in data.get("results", []):
                url = result.get("artworkUrl100") or result.get("artworkUrl60")
                if url and result.get("bundleId") in chunk:
                    artwork[result["bundleId"]] = url.replace("100x100bb.jpg", "128x128bb.png")
        remaining = [b for b in remaining if b not in artwork]
    return artwork


def icon_data_uri(bundle_id, url, cache_dir):
    path = cache_dir / f"{bundle_id}.png"
    if not path.exists():
        try:
            path.write_bytes(fetch(url))
        except Exception as err:
            print(f"icon download failed for {bundle_id}: {err}", file=sys.stderr)
            return None
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def card(app, icon):
    name = html.escape(app["name"])
    bundle = html.escape(app["bundleIdentifier"])
    search = html.escape(f"{app['name']} {app['bundleIdentifier']}".lower())
    if icon:
        visual = f'<img src="{icon}" alt="" loading="lazy">'
    else:
        visual = f'<div class="placeholder">{html.escape(app["name"][:1].upper() or "?")}</div>'
    return (
        f'<label class="app" data-search="{search}">'
        f'<input type="checkbox" data-name="{name}" data-bundle="{bundle}">'
        f"{visual}<span class=\"name\">{name}</span><span class=\"bundle\">{bundle}</span></label>"
    )


def section(title, apps, icons):
    cards = "".join(card(a, icons.get(a["bundleIdentifier"])) for a in apps)
    return f'<section><h2>{html.escape(title)} <span class="count">{len(apps)}</span></h2><div class="grid">{cards}</div></section>'


def main():
    apps_json, cache_dir, out_html, label = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    embed = sys.argv[5:] == ["--embed"]
    cache_dir.mkdir(parents=True, exist_ok=True)
    apps = [a for a in json.loads(Path(apps_json).read_text())["result"]["apps"] if a.get("removable")]
    apps.sort(key=lambda a: a["name"].lstrip("‎").casefold())
    third_party = [a for a in apps if not a["bundleIdentifier"].startswith("com.apple.")]
    apple = [a for a in apps if a["bundleIdentifier"].startswith("com.apple.")]

    artwork = lookup_artwork([a["bundleIdentifier"] for a in apps])
    if embed:
        icons = artwork
    else:
        icons = {b: uri for b, url in artwork.items() if (uri := icon_data_uri(b, url, cache_dir))}
    print(f"{len(apps)} removable apps, {len(icons)} with icons", file=sys.stderr)
    if apps and not icons:
        sys.exit("no icons found; App Store lookups are failing")

    template = (Path(__file__).parent / "app_page_template.html").read_text()
    page = (
        template.replace("{{LABEL}}", html.escape(label))
        .replace("{{TOTAL}}", str(len(apps)))
        .replace("{{SECTIONS}}", section("Apps", third_party, icons) + section("Apple apps", apple, icons))
    )
    if embed:
        page = page.replace("</head>", EMBED_CSS + "</head>")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(page)


if __name__ == "__main__":
    main()
