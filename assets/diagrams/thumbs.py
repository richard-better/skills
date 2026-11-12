"""Pad each skill's main figure to a 16:10 thumbnail for the README grid.

Usage: python3 assets/diagrams/thumbs.py (needs Pillow)
Writes assets/<skill>/thumb.png from the PNGs listed in FIGURES.
"""

from PIL import Image

from climb import ROOT

FIGURES = {
    "outer-loop-t3": "loops.png",
    "council-debate": "debate.png",
    "hill-climb": "score-steps.png",
    "ui-climb": "round.png",
}
W, H, PAD = 1600, 1000, 40

for skill, name in FIGURES.items():
    im = Image.open(ROOT / skill / name).convert("RGB")
    scale = min((W - 2 * PAD) / im.width, (H - 2 * PAD) / im.height)
    fit = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    thumb = Image.new("RGB", (W, H), im.getpixel((5, 5)))
    thumb.paste(fit, ((W - fit.width) // 2, (H - fit.height) // 2))
    path = ROOT / skill / "thumb.png"
    thumb.save(path, optimize=True)
    print(f"wrote {path.relative_to(ROOT.parent)}")
