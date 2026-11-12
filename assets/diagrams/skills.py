"""Generate the council-debate, outer-loop-t3 and diagram-rebuild figures as Excalidraw scenes.

Usage: python3 assets/diagrams/skills.py
Writes assets/council-debate/debate.excalidraw, assets/outer-loop-t3/loops.excalidraw and
assets/diagram-rebuild/loop.excalidraw.
"""

import math

from climb import (BLUE, BLUE_FILL, GREY, INK, MONO, ORANGE, ORANGE_FILL, PURPLE, RED,
                   RED_FILL, ROOT, Scene)

GREEN, GREEN_FILL = "#2f9e44", "#d3f9d8"
SKY, SKY_FILL = "#1971c2", "#d0ebff"


def R(b):  # right middle
    return (b["x"] + b["width"], b["y"] + b["height"] / 2)


def L(b):
    return (b["x"], b["y"] + b["height"] / 2)


def T(b):
    return (b["x"] + b["width"] / 2, b["y"])


def B(b):
    return (b["x"] + b["width"] / 2, b["y"] + b["height"])


def badge(s, x, y, n, color=RED):
    d = s.dot(x, y, 15, color, color)
    s.text(x, y - 12, str(n), 18, "#ffffff", align="center")
    return d


def council_debate():
    s = Scene(41)
    s.text(0, 0, "Debate turns three independent answers into what is settled and what is yours to decide",
           24, INK)
    members = [("Claude Opus", ORANGE, ORANGE_FILL), ("GPT Sol", GREEN, GREEN_FILL),
               ("Gemini Pro", SKY, SKY_FILL)]
    ys = [130, 260, 390]
    cy = 305

    brief = s.box(0, cy - 55, 190, 110, "council-brief.md\n", font=MONO, size=17)
    s.text(95, cy + 8, "your view stays out", 15, GREY, align="center")

    s.text(380, 75, "Round 1: council, one model per provider", 17, GREY, align="center")
    r1 = []
    for (name, st, fi), y in zip(members, ys):
        r1.append(s.box(290, y, 180, 90, f"{name}\nanswers alone", stroke=st, fill=fi, size=18))
    for b, y in zip(r1, ys):
        s.line([R(brief), (240, cy), (240, y + 45), L(b)], GREY, start=brief if b is r1[1] else None, end=b)

    syn1 = s.box(560, cy - 60, 190, 120, "Show every answer\nin full, then\nsynthesize", size=17)
    for b, y in zip(r1, ys):
        s.line([R(b), (515, y + 45), (515, cy), L(syn1)], GREY, arrow=b is r1[1],
               end=syn1 if b is r1[1] else None)

    deb = s.box(830, cy - 60, 230, 120, "council-debate-r1.md\n\n", font=MONO, size=16)
    s.text(945, cy - 6, "brief + every answer,\nlabelled by model", 15, GREY, align="center")
    s.line([R(syn1), L(deb)], GREY, start=syn1, end=deb)
    s.text(945, cy + 120, "\"I disagree with Sol on X\"", 16, RED, align="center")
    s.text(945, cy + 145, "your pushback, if any", 14, GREY, align="center")
    s.line([(945, cy + 116), B(deb)], RED, dashed=True, end=deb)

    s.text(1235, 75, "Debate round: new delegate_task,\nsame model, reads the file", 17, GREY, align="center")
    r2 = []
    for (name, st, fi), y in zip(members, ys):
        r2.append(s.box(1150, y, 180, 90, f"{name}\nrebuts the others", stroke=st, fill=fi, size=18))
    for b, y in zip(r2, ys):
        s.line([R(deb), (1105, cy), (1105, y + 45), L(b)], GREY, start=deb if b is r2[1] else None, end=b)

    fin = s.box(1430, cy - 140, 250, 280, "", stroke=BLUE, fill="#ffffff")
    s.text(1555, cy - 125, "Synthesis", 20, INK, align="center")
    rows = [("Concessions", "what each one missed", "#e9ecef", GREY),
            ("Resolved", "which position won, why", "#e9ecef", GREY),
            ("Unresolved", "your real decisions", BLUE_FILL, BLUE),
            ("New", "points no answer had", "#e9ecef", GREY)]
    for i, (h, sub, fi, st) in enumerate(rows):
        y = cy - 85 + i * 56
        col = "#ffffff" if fi == BLUE_FILL else INK
        s.box(1445, y, 220, 48, "", stroke=st, fill=fi, rough=0)
        s.text(1555, y + 3, h, 17, col, align="center")
        s.text(1555, y + 24, sub, 14, "#ffffff" if fi == BLUE_FILL else GREY, align="center")
    for b, y in zip(r2, ys):
        s.line([R(b), (1380, y + 45), (1380, cy), L(fin)], GREY, arrow=b is r2[1],
               end=fin if b is r2[1] else None)

    s.line([T(fin), (1555, 40), (945, 40), (945, cy - 64)], BLUE, start=fin, end=deb)
    s.text(1250, 46, "another round while a disagreement remains, three at most", 16, BLUE, align="center")
    s.save(ROOT / "council-debate" / "debate.excalidraw")



def pt(cx, cy, rx, ry, deg):
    a = math.radians(deg)
    return cx + rx * math.cos(a), cy + ry * math.sin(a)


def ring(s, cx, cy, rx, ry, a0, a1, color, dashed=False, width=2, heads=(), head_len=5):
    n = max(2, int(abs(a1 - a0) / 3))
    pts = [pt(cx, cy, rx, ry, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    e = s.line(pts, color, arrow=False, dashed=dashed, kind="line", width=width)
    e["roundness"] = {"type": 2}
    for h in heads:
        s.line([pt(cx, cy, rx, ry, h - head_len), pt(cx, cy, rx, ry, h + head_len)], color, width=3)


def outer_loop():
    s = Scene(83)
    s.text(0, 0, "One outer loop keeps several inner loops moving", 24, INK)
    CX, CY, RX, RY = 820, 560, 600, 400

    # outer ring: solid through the six steps, dashed while waiting for the next sweep
    angles = [-35, 15, 65, 115, 165, 215]
    for i in range(5):
        ring(s, CX, CY, RX, RY, angles[i], angles[i + 1], PURPLE, width=3,
             heads=[(angles[i] + angles[i + 1]) / 2], head_len=3)
    ring(s, CX, CY, RX, RY, 215, 325, PURPLE, dashed=True, width=3, heads=[270], head_len=3)
    s.text(CX, CY - RY - 74, "wait for the next sweep", 18, PURPLE, align="center")
    s.text(CX, CY - RY - 50, "schedule_task, every 15 minutes", 15, INK, MONO, "center")

    steps = [("Read", "t3_thread_read each"), ("Unblock", "from standing orders"),
             ("Escalate", "the rest to you"), ("Relay", "results between loops"),
             ("Check the machine", "pause low priority"), ("Watch", "start covered work")]
    W, H = 220, 70
    stops = []
    for i, ((h, sub), ang) in enumerate(zip(steps, angles)):
        x, y = pt(CX, CY, RX, RY, ang)
        b = s.box(x - W / 2, y - H / 2, W, H, "", stroke=PURPLE, fill="#ffffff")
        s.text(x, y - 28, h, 19, INK, align="center")
        s.text(x, y + 2, sub, 14, GREY, align="center")
        badge(s, x - W / 2, y - H / 2, i + 1, PURPLE)
        stops.append(b)

    # outer loop's own state, top inside the ring
    s.text(CX, CY - RY + 70, "Outer loop thread", 22, PURPLE, align="center")
    s.text(CX, CY - RY + 100, "standing orders: Goal, Models, Approvals, Landing, Watch", 15, GREY, align="center")
    s.text(CX, CY - RY + 122, "~/.t3/outer-loop/<id>.md  ledger, read every turn", 14, INK, MONO, "center")

    # inner loops
    inner = [("A", "running", GREEN, GREEN_FILL, CX - 250, CY + 10),
             ("B", "blocked", RED, RED_FILL, CX + 250, CY + 10),
             ("C", "done", BLUE, "#d0ebff", CX, CY + 200)]
    r = 95
    for name, st, sc, sf, x, y in inner:
        s._base("ellipse", x - r, y - r * 0.8, 2 * r, 1.6 * r, strokeColor="transparent",
                backgroundColor=sf, opacity=60, roughness=0)
        if st == "blocked":
            ring(s, x, y, r, r * 0.8, -60, 250, sc, width=2, heads=[95], head_len=12)
            s.text(x, y - r * 0.8 - 24, "waiting on a decision", 14, RED, align="center")
        elif st == "done":
            ring(s, x, y, r, r * 0.8, 0, 360, sc, width=2, heads=[95, 275], head_len=12)
        else:
            ring(s, x, y, r, r * 0.8, 0, 360, sc, width=2, heads=[5, 125, 245], head_len=12)
        s.text(x, y - 34, f"Workstream {name}", 18, INK, align="center")
        s.text(x, y - 8, "build, check, fix", 14, GREY, align="center")
        s.box(x - 45, y + 20, 90, 30, st, stroke=sc, fill="#ffffff", font=MONO, size=14, rough=0)

    # spokes: where the outer loop touches the inner loops
    rd, ub, esc, rl = stops[0], stops[1], stops[2], stops[3]
    ax, ay = inner[0][4], inner[0][5]
    bx, by = inner[1][4], inner[1][5]
    cx_, cy_ = inner[2][4], inner[2][5]
    s.line([(bx + 30, by - r * 0.8 - 30), (rd["x"] + 40, rd["y"] + H + 4)], GREY, dashed=True)
    s.line([(ub["x"] - 4, ub["y"] + H / 2), (bx + r + 6, by)], PURPLE)
    s.text(ub["x"] - 120, ub["y"] + H / 2 + 6, "answers", 14, PURPLE)
    s.line([(cx_ - r - 6, cy_), (rl["x"] + W - 30, rl["y"] - 4)], GREY, dashed=True)
    s.text(cx_ - r - 150, cy_ + 34, "branch, commit,\nevidence", 14, GREY, align="center")
    s.text(rd["x"] + 70, rd["y"] + H + 40, "state,\nquestions", 14, GREY)
    s.text(ax - r, ay + r * 0.8 + 16, "each inner loop is its own T3 thread,\nlaunched with t3_thread_launch", 14, GREY)

    you = s.box(esc["x"] + W + 120, esc["y"] + 120, 170, 80, "You", size=22)
    ex, ey = esc["x"] + W / 2, esc["y"] + H
    s.line([(ex, ey + 4), (ex, you["y"] + 40), (you["x"] - 4, you["y"] + 40)], PURPLE, end=you)
    s.text(ex + 14, ey + 26, "AskUserQuestion, batched", 14, INK, MONO)

    s.text(0, CY + RY + 150, "solid: the outer loop acts     dashed: waiting, or an inner loop reporting back", 15, GREY)
    s.save(ROOT / "outer-loop-t3" / "loops.excalidraw")


def stage(s, x, y, w, h, title, sub, stroke=GREY, fill="#ffffff", font=None):
    b = s.box(x, y, w, h, "", stroke=stroke, fill=fill)
    s.text(x + w / 2, y + 22, title, 20, INK, font or 5, "center")
    s.text(x + w / 2, y + 58, sub, 15, GREY, align="center")
    return b


def diagram_rebuild():
    s = Scene(57)
    s.text(0, 0, "A fresh reviewer checks every round until the rebuild matches the original", 24, INK)
    y, h = 250, 110
    orig = stage(s, 0, y, 190, h, "original.png", "an image only", font=MONO)
    build = stage(s, 280, y, 230, h, "Builder", "draws editable source\nfrom the image", ORANGE, ORANGE_FILL)
    s.text(395, y + h + 14, "one per track: ex (Excalidraw),\ndd (diagram-design)", 14, GREY, align="center")
    render = stage(s, 600, y, 200, h, "render.mjs", "source to vN.png", font=MONO)
    review = stage(s, 890, y, 240, h, "Fresh reviewer", "sees only the brief\nand both images", SKY, SKY_FILL)
    gallery = stage(s, 1250, y, 230, h, "gallery.html", "original beside\nevery track", GREEN, GREEN_FILL,
                    font=MONO)

    s.line([R(orig), L(build)], GREY, start=orig, end=build)
    s.line([R(build), L(render)], GREY, start=build, end=render)
    s.line([R(render), L(review)], GREY, start=render, end=review)
    s.line([R(review), L(gallery)], GREEN, start=review, end=gallery)
    s.text(1190, y + 22, "PASS", 17, GREEN, MONO, "center")

    s.line([T(review), (1010, 160), (395, 160), T(build)], RED, start=review, end=build)
    s.text(702, 126, "ITERATE: located fixes go back to the builder", 17, RED, align="center")
    s.text(702, 168, "a new reviewer each round, four rounds at most", 15, GREY, align="center")

    s.line([B(orig), (95, 470), (1010, 470), B(review)], GREY, dashed=True, start=orig, end=review)
    s.text(552, 478, "the original, for comparison", 15, GREY, align="center")
    s.save(ROOT / "diagram-rebuild" / "loop.excalidraw")


if __name__ == "__main__":
    council_debate()
    outer_loop()
    diagram_rebuild()
