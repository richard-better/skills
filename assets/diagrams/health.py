"""Generate the health-records and health-differential figures as Excalidraw scenes.

Usage: python3 assets/diagrams/health.py
Writes assets/health-records/pipeline.excalidraw and assets/health-differential/panel.excalidraw.
Render each to PNG as described in assets/diagrams/README.md.
"""

import json
import random
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent

INK = "#1e1e1e"
GREY = "#868e96"
LINE = "#adb5bd"
BOX = "#ced4da"
BG = "#ffffff"
RED = "#e03131"
BLUE, BLUE_FILL = "#1971c2", "#d0ebff"
PURPLE, PURPLE_FILL = "#7048e8", "#e5dbff"
ORANGE, ORANGE_FILL = "#e8590c", "#ffe8cc"
GREEN, GREEN_FILL = "#2f9e44", "#d3f9d8"
HAND, MONO = 5, 3


class Scene:
    def __init__(self, seed: int):
        self.els: list[dict] = []
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
        w = max(len(line) for line in lines) * size * per
        h = len(lines) * size * 1.25
        if align == "center" and container is None:
            x -= w / 2
        return self._base(
            "text", x, y, w, h, strokeColor=color, text=s, originalText=s, fontSize=size,
            fontFamily=font, textAlign=align, verticalAlign="middle" if container else "top",
            lineHeight=1.25, containerId=container, autoResize=True, **kw)

    def box(self, x, y, w, h, label="", stroke=BOX, fill="#ffffff", size=20, color=INK,
            font=HAND, kind="rectangle", dashed=False, rough=1, **kw):
        b = self._base(kind, x, y, w, h, strokeColor=stroke, backgroundColor=fill,
                       roundness={"type": 3 if kind == "rectangle" else 2}, roughness=rough,
                       strokeStyle="dashed" if dashed else "solid", **kw)
        if label:
            lines = label.split("\n")
            per = 0.6 if font == MONO else 0.55
            tw = max(len(line) for line in lines) * size * per
            th = len(lines) * size * 1.25
            t = self.text(x + (w - tw) / 2, y + (h - th) / 2, label, size, color, font,
                          "center", container=b["id"])
            b["boundElements"].append({"type": "text", "id": t["id"]})
        return b

    def card(self, x, y, w, h, title, sub, stroke=BOX, fill="#ffffff", font=HAND, size=19):
        """A box with a title line and a smaller grey second line, as two texts."""
        b = self.box(x, y, w, h, stroke=stroke, fill=fill)
        gap = 6
        lines = sub.count("\n") + 1
        total = size * 1.25 + gap + lines * 15 * 1.25
        top = y + (h - total) / 2
        self.text(x + w / 2, top, title, size, INK, font, "center")
        self.text(x + w / 2, top + size * 1.25 + gap, sub, 15, GREY, HAND, "center")
        return b

    def line(self, pts, color=LINE, arrow=True, dashed=False, start=None, end=None, width=2):
        x0, y0 = pts[0]
        rel = [[px - x0, py - y0] for px, py in pts]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        e = self._base(
            "arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys), strokeColor=color,
            strokeWidth=width, roughness=0, points=rel, lastCommittedPoint=None,
            strokeStyle="dashed" if dashed else "solid",
            startBinding={"elementId": start["id"], "focus": 0, "gap": 4} if start else None,
            endBinding={"elementId": end["id"], "focus": 0, "gap": 4} if end else None,
            startArrowhead=None, endArrowhead="arrow" if arrow else None, elbowed=False)
        for b in (start, end):
            if b is not None:
                b["boundElements"].append({"type": "arrow", "id": e["id"]})
        return e

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        scene = {"type": "excalidraw", "version": 2, "source": "assets/diagrams/health.py",
                 "elements": self.els, "appState": {"viewBackgroundColor": BG}, "files": {}}
        path.write_text(json.dumps(scene, indent=1) + "\n")
        print(f"wrote {path.relative_to(ASSETS.parent)}")


def L(b):
    return (b["x"], b["y"] + b["height"] / 2)


def R(b):
    return (b["x"] + b["width"], b["y"] + b["height"] / 2)


def T(b):
    return (b["x"] + b["width"] / 2, b["y"])


def B(b):
    return (b["x"] + b["width"] / 2, b["y"] + b["height"])


def pipeline():
    s = Scene(7)
    s.text(0, 0, "Every PDF becomes a faithful document and rows in one markers table;\n"
                 "the generated index is where the panel starts", 24, INK)

    pdfs = s.card(0, 250, 180, 130, "PDF folder", "lab reports, letters,\nimaging, scans")
    lst = s.box(230, 280, 170, 70, "extract.py --list", font=MONO, size=16)
    s.line([R(pdfs), L(lst)], start=pdfs, end=lst)
    s.text(315, 360, "new PDFs only,\nby content hash", 15, GREY, align="center")

    agent = s.card(870, 255, 190, 120, "Agent reads PDF", "directly, every page,\nas printed",
                   stroke=PURPLE, fill=PURPLE_FILL)
    s.line([R(lst), L(agent)], PURPLE, start=lst, end=agent, width=3)
    s.text(635, 280, "PDF input", 17, PURPLE, align="center")

    # fallback for models that cannot read PDFs
    ext = s.box(450, 440, 170, 60, "extract.py", font=MONO, size=17, dashed=True)
    pages = s.box(670, 440, 170, 60, ".txt + .png", font=MONO, size=17, dashed=True)
    s.line([(330, 420), (330, 470), L(ext)], dashed=True, start=None, end=ext)
    s.line([R(ext), L(pages)], dashed=True, start=ext, end=pages)
    s.line([R(pages), (965, 470), B(agent)], dashed=True, start=pages, end=agent)
    s.text(545, 512, "fallback: the model cannot\nread PDFs", 15, GREY, align="center")

    rows = s.box(870, 520, 190, 56, "rows.csv", font=MONO, size=17)
    merge = s.box(870, 620, 190, 60, "records.py merge", font=MONO, size=16)
    s.line([(1050, 375), (1050, 520)], start=agent, end=rows)
    s.line([B(rows), T(merge)], start=rows, end=merge)
    s.line([L(merge), (835, 650), (835, 548), L(rows)], RED, dashed=True, start=merge, end=rows)
    s.text(625, 575, "bad rows: nothing\nwritten, fix and rerun", 15, RED)

    fx, fy, fw, fh = 1130, 90, 330, 620
    s.box(fx, fy, fw, fh, stroke=LINE, fill="transparent", dashed=True, rough=0)
    s.text(fx + 12, fy + 10, "records folder", 16, GREY)
    docs = s.card(fx + 30, 140, 270, 75, "documents/*.md", "faithful text + frontmatter", font=MONO, size=17)
    marks = s.card(fx + 30, 290, 270, 75, "markers.csv", "one row per result, LOINC", font=MONO, size=17)
    ctx = s.card(fx + 30, 440, 270, 75, "context.md", "the owner writes it", font=MONO, size=17)
    idx = s.card(fx + 30, 600, 270, 75, "index.md", "generated: records.py index", stroke=BLUE,
                 fill=BLUE_FILL, font=MONO, size=17)
    s.line([R(agent), (1100, 315), (1100, 177), L(docs)], start=agent, end=docs)
    s.line([R(merge), (1110, 650), (1110, 327), L(marks)], start=merge, end=marks)
    for b in (docs, marks, ctx):
        s.line([R(b), (fx + fw - 10, R(b)[1])], arrow=False)
    s.line([(fx + fw - 10, 177), (fx + fw - 10, 570), (T(idx)[0], 570), T(idx)], end=idx)

    panel = s.card(1510, 595, 230, 85, "health-differential", "starts at index.md", stroke=ORANGE,
                   fill=ORANGE_FILL, font=MONO, size=17)
    s.line([R(idx), L(panel)], BLUE, start=idx, end=panel)
    s.text(1625, 690, "writes panels/<date>.md", 15, GREY, align="center")
    s.save(ASSETS / "health-records" / "pipeline.excalidraw")


def panel():
    s = Scene(13)
    s.text(0, 0, "Six seats read the same records from three angles;\n"
                 "a finding ranks high when both models raise it", 24, INK)

    recs = s.card(0, 300, 190, 110, "records folder", "index.md, documents,\nmarkers.csv, context.md")
    brief = s.box(250, 260, 230, 190, stroke=BOX)
    s.text(365, 272, "brief.md", 18, INK, MONO, "center")
    for i, item in enumerate(["demographics, meds", "problem list", "lab table, every value",
                              "Already flagged"]):
        color = BLUE if item == "Already flagged" else GREY
        s.text(365, 312 + i * 32, item, 16, color, align="center")
    s.line([R(recs), L(brief)], start=recs, end=brief)

    roles = ["Hypothesis", "Challenger", "Data auditor"]
    jobs = ["ranks diagnoses, unifying ones too", "assumes each working diagnosis is wrong",
            "trends every value, finds dropped follow-ups"]
    models = [("Model A", ORANGE, ORANGE_FILL), ("Model B", GREEN, GREEN_FILL)]
    cx = [720, 920]
    s.text(cx[0] + 80, 100, "Model A", 18, ORANGE, align="center")
    s.text(cx[1] + 80, 100, "Model B", 18, GREEN, align="center")
    s.text(cx[0] + 180, 128, "from different labs, same task", 15, GREY, align="center")
    bands = []
    for r, (role, job) in enumerate(zip(roles, jobs, strict=True)):
        y = 165 + r * 140
        s.text(cx[0] - 30, y - 6, role, 18, INK, align="right")
        s.els[-1]["x"] -= s.els[-1]["width"]
        bands.append(s.box(cx[0] - 15, y - 12, 390, 94, stroke=BOX, fill="#f8f9fa", rough=0))
        for c, (_, st, fi) in enumerate(models):
            s.box(cx[c], y, 160, 70, "answer.md", stroke=st, fill=fi, font=MONO, size=16)
        s.text(cx[0] + 180, y + 86, job, 15, GREY, align="center")
    # brief fans out to the grid through one trunk
    s.line([R(brief), (530, 355)], arrow=False)
    s.line([(530, 200), (530, 480)], arrow=False)
    for r in range(3):
        s.line([(530, 200 + r * 140), L(bands[r])], end=bands[r])

    syn = s.box(1180, 165, 280, 350, stroke=BLUE, fill="#ffffff")
    s.text(1320, 180, "Synthesis", 20, INK, align="center")
    steps = ["1 rank: both models, then\n   two roles, then one seat",
             "2 novelty check against\n   Already flagged",
             "3 verify each value\n   against its document",
             "4 pick steps that\n   discriminate, cheapest first"]
    for i, st in enumerate(steps):
        s.text(1200, 222 + i * 70, st, 16, INK)
    for r in range(3):
        y = 200 + r * 140
        s.line([R(bands[r]), (1130, y)], arrow=False)
    s.line([(1130, 200), (1130, 480)], arrow=False)
    s.line([(1130, 340), L(syn)], end=syn)

    rep = s.box(1540, 140, 260, 400, stroke=BOX, fill="#ffffff")
    s.text(1670, 152, "panels/<date>.md", 17, INK, MONO, "center")
    sections = [("0 Track record", True), ("1 New", False), ("2 Re-ranked", False),
                ("3 Next steps, 5 at most", False), ("4 Questions for the doctor", False),
                ("5 Not worth chasing", False)]
    for i, (name, loop) in enumerate(sections):
        y = 195 + i * 55
        s.box(1555, y, 230, 44, name, stroke=BLUE if loop else BOX, fill=BLUE_FILL if loop else "#f8f9fa",
              size=15, rough=0)
    s.line([R(syn), L(rep)], start=syn, end=rep)

    # the loop: next run scores this run's items, and open ones join Already flagged
    s.line([B(rep), (1670, 620), (365, 620), B(brief)], BLUE, dashed=True, start=rep, end=brief)
    s.text(1018, 630, "next run: score each item confirmed, killed or still open;\nopen items join Already flagged",
           16, BLUE, align="center")
    s.save(ASSETS / "health-differential" / "panel.excalidraw")


if __name__ == "__main__":
    pipeline()
    panel()
