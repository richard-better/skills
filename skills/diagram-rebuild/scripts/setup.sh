#!/usr/bin/env bash
# Install the pinned render toolchain into a cache directory (idempotent).
# Usage: bash setup.sh
set -euo pipefail

home="${DIAGRAM_REBUILD_HOME:-$HOME/.cache/diagram-rebuild}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
stamp="$home/.setup-v2"

if [[ -f "$stamp" && -f "$home/dist/excalidraw.js" ]]; then
  echo "toolchain ready: $home"
  exit 0
fi

mkdir -p "$home"
cd "$home"
[[ -f package.json ]] || echo '{"name":"diagram-rebuild-toolchain","private":true}' >package.json

# npm reads ~/.npmrc, so a configured registry mirror applies here too.
npm install --no-audit --no-fund --silent \
  playwright@1.64.1 @excalidraw/excalidraw@0.18.1 react@18.3.1 react-dom@18.3.1 esbuild@0.25.10 >&2
npx --no-install playwright install chromium >&2

cp "$here/excalidraw-entry.js" "$home/excalidraw-entry.js"
npx --no-install esbuild excalidraw-entry.js --bundle --format=esm --minify \
  --define:process.env.NODE_ENV='"production"' --outfile=dist/excalidraw.js --log-level=warning >&2

touch "$stamp"
echo "toolchain installed: $home"
