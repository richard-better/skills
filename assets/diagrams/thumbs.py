"""Make each skill's 16:10 thumbnail for the README grid.

Usage: python3 assets/diagrams/thumbs.py (needs Pillow)
Writes assets/<skill>/thumb.png. Diagrams are padded so the whole figure shows; screenshots
are cropped from the top, where the page's header and first rows are.
"""

from PIL import Image

from climb import ROOT

FIGURES = {
    "outer-loop-t3": ("loops.png", "pad"),
    "council": ("council.png", "pad"),
    "council-debate": ("debate.png", "pad"),
    "hill-climb": ("score-steps.png", "pad"),
    "ui-climb": ("round.png", "pad"),
    "health-records": ("pipeline.png", "pad"),
    "health-differential": ("panel.png", "pad"),
    "diagram-rebuild": ("loop.png", "pad"),
    "ios-app-cleanup": ("checklist.png", "top"),
}
W, H, PAD = 1600, 1000, 40

for skill, (name, fit) in FIGURES.items():
    im = Image.open(ROOT / skill / name).convert("RGB")
    if fit == "top":
        thumb = im.crop((0, 0, im.width, round(im.width * H / W))).resize((W, H), Image.LANCZOS)
    else:
        scale = min((W - 2 * PAD) / im.width, (H - 2 * PAD) / im.height)
        small = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        thumb = Image.new("RGB", (W, H), im.getpixel((5, 5)))
        thumb.paste(small, ((W - small.width) // 2, (H - small.height) // 2))
    path = ROOT / skill / "thumb.png"
    thumb.save(path, optimize=True)
    print(f"wrote {path.relative_to(ROOT.parent)}")
