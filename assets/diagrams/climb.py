"""Generate the hill-climb and ui-climb figures as Excalidraw scenes.

Usage: python3 assets/diagrams/climb.py
Writes assets/hill-climb/{score-steps,round}.excalidraw and assets/ui-climb/round.excalidraw.
Render each with diagram-rebuild's render.mjs (see assets/diagrams/README.md).
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INK = "#1e1e1e"
GREY = "#868e96"
GREY_LINE = "#dee2e6"
FADE = "#ced4da"
BLUE, BLUE_FILL = "#1971c2", "#1c7ed6"
BAND = "#a5d8ff"
YELLOW, YELLOW_FILL = "#f08c00", "#fff3bf"
RED, RED_FILL = "#e03131", "#ffc9c9"
ORANGE, ORANGE_FILL = "#e8590c", "#ffe8cc"
PURPLE, PURPLE_FILL = "#7048e8", "#e5dbff"
BG = "#f8f9fa"
HAND, MONO = 5, 3


class Scene:
    def __init__(self, seed):
        self.els = []
        self.rng = random.Random(seed)
        self.n = 0

    def _base(self, kind, x, y, w, h, **kw):
        self.n += 1
        e = {
            "id": f"{kind}-{self.n}", "type": kind, "x": x, "y": y, "width": w, "height": h,
            "angle": 0, "strokeColor": INK, "backgroundColor": "transparent", "fillStyle": "solid",
            "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": None,
            "seed": self.rng.randrange(1, 2**31), "version": 1,
            "versionNonce": self.rng.randrange(1, 2**31), "isDeleted": False,
            "boundElements": [], "updated": 1, "link": None, "locked": False,
        }
        e.update(kw)
        self.els.append(e)
        return e

    def text(self, x, y, s, size=20, color=INK, font=HAND, align="left", container=None, **kw):
        lines = s.split("\n")
        per = 0.6 if font == MONO else 0.55
        w = max(len(l) for l in lines) * size * per
        h = len(lines) * size * 1.25
        if align == "center" and container is None:
            x -= w / 2
        return self._base(
            "text", x, y, w, h, strokeColor=color, text=s, originalText=s, fontSize=size,
            fontFamily=font, textAlign=align, verticalAlign="middle" if container else "top",
            lineHeight=1.25, containerId=container, autoResize=True, **kw)

    def box(self, x, y, w, h, label="", stroke=GREY_LINE, fill="#ffffff", size=20, color=INK,
            font=HAND, kind="rectangle", dashed=False, rough=1, **kw):
        b = self._base(kind, x, y, w, h, strokeColor=stroke, backgroundColor=fill,
                       roundness={"type": 3 if kind == "rectangle" else 2}, roughness=rough,
                       strokeStyle="dashed" if dashed else "solid", **kw)
        if label:
            lines = label.split("\n")
            per = 0.6 if font == MONO else 0.55
            tw = max(len(l) for l in lines) * size * per
            th = len(lines) * size * 1.25
            t = self.text(x + (w - tw) / 2, y + (h - th) / 2, label, size, color, font,
                          "center", container=b["id"], opacity=kw.get("opacity", 100))
            b["boundElements"].append({"type": "text", "id": t["id"]})
        return b

    def line(self, pts, color=GREY, arrow=True, dashed=False, start=None, end=None, width=2,
             kind="arrow", **kw):
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        extra = {}
        if kind == "arrow":
            extra = {
                "startBinding": {"elementId": start["id"], "focus": 0, "gap": 4} if start else None,
                "endBinding": {"elementId": end["id"], "focus": 0, "gap": 4} if end else None,
                "startArrowhead": None, "endArrowhead": "arrow" if arrow else None,
                "elbowed": False,
            }
        e = self._base(kind, x0, y0, max(xs) - min(xs), max(ys) - min(ys), strokeColor=color,
                       strokeWidth=width, roughness=0, points=rel, lastCommittedPoint=None,
                       strokeStyle="dashed" if dashed else "solid", **extra, **kw)
        for b in (start, end):
            if b is not None and kind == "arrow":
                b["boundElements"].append({"type": "arrow", "id": e["id"]})
        return e

    def dot(self, cx, cy, r, stroke, fill):
        return self._base("ellipse", cx - r, cy - r, 2 * r, 2 * r, strokeColor=stroke,
                          backgroundColor=fill, roughness=0)

    def save(self, path, bg=BG):
        path.parent.mkdir(parents=True, exist_ok=True)
        scene = {"type": "excalidraw", "version": 2, "source": "assets/diagrams/climb.py",
                 "elements": self.els, "appState": {"viewBackgroundColor": bg}, "files": {}}
        path.write_text(json.dumps(scene, indent=1) + "\n")
        print(f"wrote {path.relative_to(ROOT.parent)}")


def score_steps():
    """Illustrative climb: the best only moves when a candidate clears the noise floor."""
    s = Scene(11)
    ox, oy, step, unit, lo = 90, 600, 125, 9, 52
    X = lambda r: ox + 60 + r * step
    Y = lambda v: oy - (v - lo) * unit
    noise = 2
    best = 60
    # (round, [(score, verdict)]): verdict k=kept, r=reverted, g=guard broken
    rounds = [
        (1, [(58, "r"), (61, "r"), (66, "k")]),
        (2, [(65, "r"), (70, "k"), (67, "r")]),
        (3, [(71, "r"), (69, "r"), (73, "g")]),
        (4, [(75, "k"), (73, "r")]),
        (5, [(74, "r"), (76, "r")]),
        (6, [(73, "r"), (76, "r"), (72, "r")]),
        (7, [(80, "r"), (84, "r"), (88, "k")]),
    ]
    right = X(7) + 190

    # axes
    s.line([(ox, Y(52)), (ox, Y(99))], INK, arrow=True)
    s.line([(ox, oy), (right + 20, oy)], INK, arrow=True)
    s.text(ox - 10, Y(99) - 34, "score", 18, GREY, align="center")
    s.text(right + 30, oy - 12, "round", 18, GREY)
    s.text(X(0), oy + 12, "base", 16, GREY, MONO, "center")
    for r in range(1, 8):
        s.text(X(r), oy + 12, str(r), 16, GREY, MONO, "center")

    # target
    s.line([(ox, Y(94)), (right, Y(94))], RED, arrow=False, dashed=True, kind="line")
    s.text(right - 4, Y(94) - 30, "target", 18, RED, align="left")

    # best line with its noise band, drawn per segment
    segs = []
    cur, start = best, X(0) - 30
    for r, cands in rounds:
        kept = [v for v, k in cands if k == "k"]
        if kept:
            segs.append((start, X(r), cur))
            cur, start = kept[0], X(r)
    segs.append((start, right, cur))
    for x0, x1, v in segs:
        s._base("rectangle", x0, Y(v + noise), x1 - x0, noise * unit, strokeColor="transparent",
                backgroundColor=BAND, opacity=45, roughness=0)
    pts = []
    for i, (x0, x1, v) in enumerate(segs):
        pts += [(x0, Y(v)), (x1, Y(v))]
    s.line(pts, BLUE, arrow=False, kind="line", width=3)

    # baseline replicates
    for dv in (-1, 0, 1):
        s.dot(X(0) + dv * 10, Y(best + dv), 6, BLUE, "#ffffff")

    for r, cands in rounds:
        for i, (v, k) in enumerate(cands):
            cx = X(r) - 16 + i * 16
            if k == "k":
                s.dot(X(r), Y(v), 9, BLUE, BLUE_FILL)
            elif k == "g":
                s.dot(cx, Y(v), 7, RED, RED_FILL)
            else:
                s.dot(cx, Y(v), 7, GREY, "#e9ecef")
        kept = [v for v, k in cands if k == "k"]
        if kept:
            s.text(X(r) + 14, Y(kept[0]) - 30, f"r{ [x for x, c in rounds if any(k=='k' for _, k in c)].index(r) + 1 }", 16, BLUE, MONO)

    # annotations
    s.text(X(3) + 4, Y(73) - 54, "beat the floor,\nbroke a guard", 16, RED, align="center")
    s.line([(X(5) - 30, Y(80)), (X(6) + 30, Y(80))], GREY, arrow=False, kind="line")
    s.line([(X(5) - 30, Y(80)), (X(5) - 30, Y(78.5))], GREY, arrow=False, kind="line")
    s.line([(X(6) + 30, Y(80)), (X(6) + 30, Y(78.5))], GREY, arrow=False, kind="line")
    s.text((X(5) + X(6)) / 2, Y(80) - 54, "plateau: 2 rounds,\nnothing kept", 16, INK, align="center")
    s.text(X(7) + 16, Y(84) - 10, "contest round:\nbigger approaches", 16, INK)
    s.text(X(0) + 30, Y(best) + 30, "baseline x3\nspread = noise floor", 16, BLUE, align="left")

    # legend
    lx, ly = ox + 10, oy + 56
    items = [(BLUE, BLUE_FILL, "kept, tagged as a rung"), (GREY, "#e9ecef", "reverted: worse or no effect"),
             (RED, RED_FILL, "reverted: guard broken")]
    for i, (st, fi, label) in enumerate(items):
        x = lx + i * 300
        s.dot(x, ly + 12, 7, st, fi)
        s.text(x + 16, ly, label, 16, INK)
    s._base("rectangle", lx + 900 - 7, ly + 4, 22, 16, strokeColor="transparent",
            backgroundColor=BAND, opacity=45, roughness=0)
    s.text(lx + 900 + 22, ly, "best + noise floor", 16, INK)
    s.text(lx, ly + 34, "Illustrative data", 14, GREY)
    s.save(ROOT / "hill-climb" / "score-steps.excalidraw")


def round_flow(ui=False):
    """One round, left to right. ui=True swaps the scorer for the council."""
    s = Scene(23 if not ui else 29)
    n, a, t = s.box, s.line, s.text

    cy = 330
    best = n(0, cy - 45, 170, 90, "Best rung\n", )
    t(85, cy + 5, "climb-r2", 16, GREY, MONO, "center")

    t(330, 128, "built in parallel,\none worktree each", 16, GREY, align="center")
    cands = []
    for i, (name, hyp) in enumerate([("A", "one change"), ("B", "one change"), ("C", "one change")]):
        y = 185 + i * 110
        cands.append(n(245, y, 170, 70, f"Candidate {name}\n{hyp}", size=18))
    for c in cands:
        mid = c["y"] + 35
        a([(174, cy), (205, cy), (205, mid), (241, mid)], GREY, start=best if c is cands[1] else None, end=c)

    if ui:
        scorer = s.box(510, cy - 70, 230, 140, "Scoring council\n2+ labs, blind brief\nscore.py", stroke=PURPLE,
                       fill=PURPLE_FILL, size=19)
        s.box(470, 70, 150, 80, "Screenshots\nevery state", stroke=PURPLE, fill=PURPLE_FILL, size=17)
        s.box(640, 70, 150, 80, "Reference\napps", stroke=PURPLE, fill=PURPLE_FILL, size=17)
        s.line([(545, 154), (545, cy - 74)], PURPLE, end=scorer)
        s.line([(715, 154), (715, cy - 74)], PURPLE, end=scorer)
        s.text(800, 108, "both scored\nevery round", 15, PURPLE)
    else:
        scorer = s.box(510, cy - 70, 230, 140, "Scorer command\nmedian of 3+ runs,\ninterleaved with best",
                       stroke=ORANGE, fill=ORANGE_FILL, size=19)
    for c in cands:
        mid = c["y"] + 35
        a([(419, mid), (470, mid), (470, cy), (506, cy)], GREY, end=scorer if c is cands[1] else None,
          arrow=c is cands[1])

    d = n(820, cy - 115, 230, 230, "beats best\nby more than\nthe noise floor,\nguards hold?",
          stroke=YELLOW, fill=YELLOW_FILL, kind="diamond", size=18)
    a([(744, cy), (816, cy)], GREY, start=scorer, end=d)

    conf = n(1140, cy - 50, 190, 100, "Confirm with\nfresh runs,\nthen holdout", size=18)
    a([(1054, cy), (1136, cy)], BLUE, start=d, end=conf)
    t(1068, cy - 30, "yes", 18, BLUE)

    rung = n(1410, cy - 50, 180, 100, "New rung\n", stroke=BLUE, fill=BLUE_FILL, color="#ffffff", size=20)
    t(1500, cy + 2, "climb-r3", 16, "#ffffff", MONO, "center")
    a([(1334, cy), (1406, cy)], BLUE, start=conf, end=rung)

    rev = n(820, 560, 230, 120, "", stroke=RED, fill=RED_FILL)
    t(935, 576, "Revert", 20, INK, align="center")
    t(935, 616, "worse | no effect\nguard broken", 15, INK, MONO, "center")
    a([(935, cy + 119), (935, 556)], RED, start=d, end=rev)
    t(945, 480, "no", 18, RED)
    a([(1235, cy + 54), (1235, 620), (1054, 620)], RED, start=conf, end=rev)
    t(1080, 585, "not confirmed", 15, RED, MONO)

    led = n(0, 760, 1590, 56, "", stroke=GREY_LINE, fill="#ffffff", dashed=True, rough=0)
    t(20, 772, "ledger.md", 20, INK, MONO)
    t(160, 775, "every candidate gets a row with its verdict, so no idea is tried twice", 18, GREY)
    a([(935, 684), (935, 756)], GREY, dashed=True, start=rev, end=led)
    a([(1500, cy + 54), (1500, 756)], GREY, dashed=True, start=rung, end=led)

    a([(1500, cy - 54), (1500, 40), (85, 40), (85, cy - 49)], BLUE, dashed=False, start=rung, end=best)
    t(800, 10, "next round builds on the new rung", 18, BLUE, align="center")

    if ui:
        s.save(ROOT / "ui-climb" / "round.excalidraw")
    else:
        s.save(ROOT / "hill-climb" / "round.excalidraw")


if __name__ == "__main__":
    score_steps()
    round_flow()
    round_flow(ui=True)
