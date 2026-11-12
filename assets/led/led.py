"""Draw the README's LED dot-matrix art: one animated icon per skill, the banner, and the
social preview.

Usage: python3 assets/led/led.py [--png]
Writes assets/<skill>/icon.svg and assets/banner.svg. With --png it also draws the social preview
and screenshots it to assets/social-preview.png with headless Chrome (set CHROME to its path if
it is not found).

Every image is a board of dots. An animation is a list of (frame, ticks) pairs; a frame maps
cells to a brightness (dim, on, hot). Frames switch on instantly and fade out over DECAY seconds,
like phosphor, so moving dots leave a short trail. Under prefers-reduced-motion each animation
shows one finished "poster" frame and stays still.
"""

import math
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
RANK = {"dim": 0, "on": 1, "hot": 2}
DECAY = 0.26  # seconds of afterglow after a frame ends
GLOW = "cubic-bezier(0.23,1,0.32,1)"  # strong ease-out: fast drop, long tail
ICON, ICON_S, ICON_R = 25, 24, 7.6  # icons: 25 x 25 board, cell size, dot radius


class F(dict):
    """One frame: cell -> brightness. Adding never dims a cell that is already brighter."""

    def add(self, cells, cl="on"):
        for c in cells:
            c = (int(c[0]), int(c[1]))
            if c not in self or RANK[cl] >= RANK[self[c]]:
                self[c] = cl
        return self

    def copy(self):
        return F(self)


# ---------- rendering ----------

def dots(cells, S, rad):
    return "".join(f'<circle class="{cl}" cx="{c*S+S/2:g}" cy="{r*S+S/2:g}" r="{rad:g}"/>'
                   for (c, r), cl in sorted(cells.items()))


def layer(prefix, frames, step, S, rad):
    """CSS keyframes and one <g> per frame for an animation looping on its own clock."""
    T = sum(h for _, h in frames) * step
    P = lambda sec: sec / T * 100
    t, css, groups = 0, "", ""
    for k, (f, h) in enumerate(frames):
        a, b = t * step, (t + h) * step
        t += h
        e = b + DECAY
        if e > T:  # the afterglow wraps into the start of the next loop
            left = 1 - (T - b) / DECAY
            kf = [f"0%{{opacity:{left:.3f};animation-timing-function:{GLOW}}}", f"{P(e-T):.3f}%{{opacity:0}}"]
        else:
            kf = ["0%{opacity:0}"]
        if a > 0:
            kf += [f"{P(a):.3f}%{{opacity:0}}", f"{P(a)+.001:.3f}%{{opacity:1}}"]
        else:
            kf = [x for x in kf if not x.startswith("0%")] + ["0%{opacity:1}"]
        kf += [f"{P(b):.3f}%{{opacity:1;animation-timing-function:{GLOW}}}"]
        kf += [f"{P(e):.3f}%{{opacity:0}}" if e <= T else f"100%{{opacity:{1-(T-b)/DECAY:.3f}}}"]
        if e < T:
            kf += ["100%{opacity:0}"]
        n = f"{prefix}{k}"
        css += f"@keyframes {n}{{{''.join(kf)}}}.{n}{{opacity:0;animation:{n} {T:.2f}s linear infinite}}"
        groups += f'<g class="{n}">{dots(f, S, rad)}</g>'
    return css, groups


def board(cols, rows, layers=(), static=None, S=ICON_S, rad=ICON_R, rx=30, scale=2, blur=4.5, label=None):
    """An SVG board. layers: [(prefix, frames, step, poster)]; static: cells lit throughout."""
    W, H = cols * S, rows * S
    css, groups, still = "", dots(static, S, rad) if static else "", ""
    for prefix, frames, step, poster in layers:
        c, g = layer(prefix, frames, step, S, rad)
        css += c
        groups += g
        still += f"g[class^={prefix}]{{animation:none!important;opacity:0}}g.{prefix}{poster % len(frames)}{{opacity:1}}"
    base = "".join(f'<circle cx="{c*S+S/2:g}" cy="{r*S+S/2:g}" r="{rad:g}"/>' for c in range(cols) for r in range(rows))
    aria = f' role="img" aria-label="{label}"' if label else ""
    media = f"@media (prefers-reduced-motion:reduce){{{still}}}" if still else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" width="{W*scale:g}" height="{H*scale:g}"{aria}>
<defs><clipPath id="clip"><rect width="{W:g}" height="{H:g}" rx="{rx}"/></clipPath>
<filter id="g" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{blur}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<style>.base{{fill:#2a251f}}.dim{{fill:#7a501a}}.on{{fill:#ffaa33}}.hot{{fill:#fff0c4}}{css}
{media}</style>
<g clip-path="url(#clip)"><rect width="{W:g}" height="{H:g}" fill="#13100d"/><g class="base">{base}</g><g filter="url(#g)">{groups}</g></g></svg>'''


def icon(skill, frames, step, poster=-1):
    path = ROOT / skill / "icon.svg"
    path.write_text(board(ICON, ICON, [("f", frames, step, poster)]))
    print(f"wrote {path.relative_to(ROOT.parent)}")


# ---------- shapes ----------

def rect(c0, r0, c1, r1):
    return [(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1) if c in (c0, c1) or r in (r0, r1)]


def fill(c0, r0, c1, r1):
    return [(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)]


def hl(r, c0, c1):
    return [(c, r) for c in range(c0, c1 + 1)]


def vl(c, r0, r1):
    return [(c, r) for r in range(min(r0, r1), max(r0, r1) + 1)]


def line(a, b):
    """Bresenham line from a to b, inclusive."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    e, out = dx + dy, []
    while True:
        out.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return out
        e2 = 2 * e
        if e2 >= dy:
            e += dy
            x0 += sx
        if e2 <= dx:
            e += dx
            y0 += sy


def box(c, r):
    return rect(c - 1, r - 1, c + 1, r + 1)


def ring(cx, cy, rad):
    """Cells of a circle, ordered by angle."""
    pts = {}
    for t in range(360):
        a = math.radians(t)
        pts.setdefault((round(cx + rad * math.cos(a)), round(cy + rad * math.sin(a))), t)
    return [p for p, _ in sorted(pts.items(), key=lambda kv: kv[1])]


def shift(cells, dc, dr):
    return [(c + dc, r + dr) for c, r in cells]


def sparks(base, paths, n):
    """n frames of one bright dot per path, easing in and out along it."""
    inout = lambda x: x * x * (3 - 2 * x)
    at = lambda path, frac: path[round(frac * (len(path) - 1))]
    return [(base.copy().add([at(p, inout(i / (n - 1))) for p in paths], "hot"), 1) for i in range(n)]


# ---------- motifs shared by icons, banner and social preview ----------

def debate(cols, cy, d):
    """One -> three -> one -> three -> one, hubs on row cy and models d rows above and below."""
    rows = [cy - d, cy, cy + d]
    hubs = [(cols[0], cy), (cols[2], cy), (cols[4], cy)]
    m1, m2 = [(cols[1], r) for r in rows], [(cols[3], r) for r in rows]

    def fan(c, r):  # hub's right edge -> bus -> model on row r
        if r == cy:
            return [(c + 2, cy), (c + 3, cy)]
        return [(c + 2, cy)] + (vl(c + 3, r, cy)[::-1] if r < cy else vl(c + 3, cy, r))

    def merge(c, r):  # model's right edge -> bus -> hub
        if r == cy:
            return [(c + 2, cy), (c + 3, cy)]
        return [(c + 2, r)] + (vl(c + 3, r, cy) if r < cy else vl(c + 3, cy, r)[::-1])

    p1, q1 = [fan(cols[0], r) for r in rows], [merge(cols[1], r) for r in rows]
    p2, q2 = [fan(cols[2], r) for r in rows], [merge(cols[3], r) for r in rows]
    base = F().add(sum(p1 + q1 + p2 + q2, []), "dim").add(sum((box(*n) for n in hubs + m1 + m2), []), "on")
    fr = [(base.copy().add(box(*hubs[0]) + [hubs[0]], "hot"), 2)]
    for pin, mids, pout, hub in [(p1, m1, q1, hubs[1]), (p2, m2, q2, hubs[2])]:
        fr += sparks(base, pin, 6)
        fr += [(base.copy().add(mids, "hot" if k % 2 == 0 else "on"), 1) for k in range(3)]
        fr += sparks(base, pout, 6)
        fr.append((base.copy().add(box(*hub) + [hub], "hot"), 2 if hub == hubs[1] else 9))
    fr.append((base, 4))
    return fr


def climb(ox, oy):
    """Five steps and a flag; a 2x2 square lands, steps and hops to the top."""
    stairs, pos = [], []
    for k in range(5):
        x, y = 1 + 4 * k + ox, 21 - 3 * k + oy
        stairs += hl(y, x, x + 3)
        if k < 4:
            stairs += vl(x + 4, y - 1, y - 3)
        pos += [(x, y - 2)] + ([(x + 2, y - 2)] if k < 4 else [])
    flag = shift([(21, 3), (22, 3), (21, 4), (22, 4), (23, 4), (21, 5), (22, 5)], ox, oy)
    base = F().add(stairs + vl(20 + ox, 3 + oy, 8 + oy) + flag, "on")
    sq = lambda p: fill(p[0], p[1], p[0] + 1, p[1] + 1)
    fr = []
    for i, p in enumerate(pos):
        landing = i == 0 or pos[i][1] != pos[i - 1][1]
        fr.append((base.copy().add(sq(p), "hot"), 3 if landing else 2))
    fr += [(base.copy().add(sq(pos[-1]), "hot").add(flag, "hot" if k % 2 == 0 else "on"), 2) for k in range(4)]
    fr += [(base.copy().add(sq(pos[-1]), "hot"), 6), (base, 4)]
    return fr


def orbit(cx, cy, R, inner):
    """Three threads orbit a ring around three small loops that each run their own dot."""
    outer, loops, fr = ring(cx, cy, R), [ring(x, y, 2) for x, y in inner], []
    for k in range(12):
        f = F().add(outer, "dim")
        for j, lp in enumerate(loops):
            i = (k * len(lp) // 12 + j * len(lp) // 3) % len(lp)
            f.add(lp, "dim").add([lp[i]], "hot").add([lp[i - 1]], "on")
        for j in range(3):
            a = math.radians(k * 30 + j * 120 - 90)
            c, r = round(cx + R * math.cos(a)), round(cy + R * math.sin(a))
            f.add([(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)], "on").add([(c, r)], "hot")
        fr.append((f, 1))
    return fr


# ---------- skill icons ----------

def council():
    src, dst, mids = (3, 12), (21, 12), [(12, 4), (12, 12), (12, 20)]
    pin = [line((5, 12), (10, m[1])) for m in mids]
    pout = [line((14, m[1]), (19, 12)) for m in mids]
    base = F().add(sum(pin + pout, []), "dim").add(box(*src) + box(*dst) + sum((box(*m) for m in mids), []), "on")
    fr = [(base.copy().add(box(*src) + [src], "hot"), 2)]
    fr += sparks(base, pin, 6)
    fr += [(base.copy().add(mids, "hot" if k % 2 == 0 else "on"), 1) for k in range(3)]
    fr += sparks(base, pout, 6)
    fr += [(base.copy().add(box(*dst) + [dst], "hot"), 9), (base, 4)]
    icon("council", fr, 0.16, poster=-2)


def ui_climb():
    chrome = rect(0, 0, 10, 13) + hl(2, 0, 10) + [(2, 1), (4, 1)]
    versions = {
        "v1": rect(2, 4, 4, 11) + hl(5, 6, 8) + hl(7, 6, 8) + hl(9, 6, 7),
        "v2": rect(2, 4, 8, 6) + hl(9, 2, 5) + hl(11, 2, 8),
        "ref": rect(2, 4, 8, 7) + hl(9, 2, 8) + hl(11, 2, 5),
    }
    win = lambda cells: shift(cells, 7, 4)
    bar = lambda n: hl(20, 7, 6 + n) if n else []
    base = F().add(hl(20, 7, 17), "dim")
    fr, prev = [], 0
    for v, score in [("v1", 3), ("v2", 7), ("ref", 11)]:
        top = [p for p in versions[v] if p[1] <= 8]
        bottom = [p for p in versions[v] if p[1] > 8]
        fr.append((base.copy().add(win(chrome), "on").add(bar(prev), "on"), 2))
        fr.append((base.copy().add(win(chrome + top), "on").add(bar(prev), "on"), 1))
        fr.append((base.copy().add(win(chrome + top + bottom), "on").add(bar(prev), "on"), 2))
        full = win(chrome + versions[v])
        fr += [(base.copy().add(full, "on").add(bar(n), "hot"), 1) for n in range(prev + 1, score + 1)]
        fr.append((base.copy().add(full, "on").add(bar(score), "on"), 8 if v != "ref" else 2))
        prev = score
    fr.append((base.copy().add(win(chrome + versions["ref"]), "hot").add(hl(20, 7, 17), "hot"), 14))
    fr.append((base.copy().add(win(chrome), "on"), 4))
    icon("ui-climb", fr, 0.1, poster=-2)


def diagram_rebuild():
    def graph(A, B, C):
        nodes = [A, B, C]
        near = lambda p: any(abs(p[0] - n[0]) <= 1 and abs(p[1] - n[1]) <= 1 for n in nodes)
        edges = [p for a, b in [(A, C), (A, B), (C, B)] for p in line(a, b) if not near(p)]
        return sum((box(*n) for n in nodes), []), edges

    target = ((2, 2), (8, 7), (2, 11))
    tb, te = graph(*target)
    base = F().add(shift(tb + te, 1, 5), "dim").add([(12, r) for r in range(0, 25, 2)], "dim")
    fr = []
    for g in [((3, 3), (8, 10), (2, 9)), ((2, 2), (8, 8), (3, 11)), target]:
        b, e = graph(*g)
        fr += [(base.copy(), 1), (base.copy().add(shift(b, 13, 5), "on"), 1),
               (base.copy().add(shift(b + e, 13, 5), "on"), 4)]
    fr += [(base.copy().add(shift(tb + te, 13, 5), "hot"), 7), (base, 2)]
    icon("diagram-rebuild", fr, 0.2, poster=-2)


def health_records():
    doc = lambda c, r: [p for p in rect(c, r, c + 3, r + 5) if p != (c + 3, r)] + [(c + 2, r + 1)] + hl(r + 3, c + 1, c + 2)
    docs = [(1, 4), (6, 6), (2, 13), (7, 15)]
    table, rows = rect(14, 5, 23, 19), [9, 11, 13, 15]
    row = lambda y: hl(y, 16, 21)
    base = F().add(sum((doc(*d) for d in docs), []), "on").add(table, "on")
    fr, done = [(base, 2)], F()
    for i, d in enumerate(docs):
        f = base.copy().add(doc(*d), "hot")
        f.update(done)
        fr.append((f, 2))
        f = base.copy()
        f.update(done)
        fr.append((f.add(doc(*d), "dim"), 1))
        done.add(doc(*d), "dim")
        for y in rows[:i]:
            done.add(row(y), "on")
        f = base.copy()
        f.update(done)
        fr.append((f.add(row(rows[i]), "hot"), 2))
    f = base.copy()
    f.update(done)
    fr.append((f.add(row(rows[3]), "on").add(table, "hot"), 7))
    empty = F().add(table, "on")
    fr.append((empty, 2))
    fr += [(F(empty).add(sum((doc(*d) for d in docs[:i]), []), "on"), 1) for i in range(1, 4)]
    icon("health-records", fr, 0.2, poster=-5)


def health_differential():
    heart_rows = [".X.X.", "XXXXX", ".XXX.", "..X.."]
    heart = [(2 + c, 10 + r) for r, s in enumerate(heart_rows) for c, ch in enumerate(s) if ch == "X"]
    roles = [4, 12, 20]
    role = lambda r: rect(10, r - 2, 14, r + 2)
    trio = lambda r: [(11, r - 1), (13, r - 1), (12, r + 1)]
    cross = hl(12, 19, 23) + vl(21, 10, 14)
    pin = [[(6, 12), (7, 12), (8, 12), (9, 12)] if r == 12 else
           [(6, 12), (7, 12), (8, 12)] + (vl(8, 12, r)[::-1] if r < 12 else vl(8, 12, r)) + [(9, r)] for r in roles]
    pout = [[(15, 12), (16, 12), (17, 12), (18, 12)] if r == 12 else
            [(15, r)] + (vl(16, r, 12) if r < 12 else vl(16, 12, r)[::-1]) + [(17, 12), (18, 12)] for r in roles]
    base = (F().add(sum(pin + pout, []), "dim").add(heart, "on").add(sum((role(r) for r in roles), []), "on")
            .add(sum((trio(r) for r in roles), []), "dim").add(cross, "on"))
    fr = [(base.copy().add(heart, "hot"), 1), (base, 1), (base.copy().add(heart, "hot"), 2)]
    fr += sparks(base, pin, 5)
    for k in range(6):
        f = base.copy()
        for r in roles:
            f.add([trio(r)[(k + r) % 3]], "hot")
        fr.append((f, 1))
    fr += sparks(base, pout, 5)
    fr += [(base.copy().add(cross, "hot"), 9), (base, 4)]
    icon("health-differential", fr, 0.17, poster=-2)


def ios_app_cleanup():
    slots = [(9 + 3 * c, 4 + 3 * r) for r in range(6) for c in range(3)]
    remove = {1, 3, 5, 6, 8, 10, 13, 15, 16}
    keep = [i for i in range(18) if i not in remove]
    tile = lambda p: fill(p[0], p[1], p[0] + 1, p[1] + 1)
    base = F().add(rect(7, 1, 18, 23), "on")

    def apps(pos):
        f = base.copy()
        for p in pos:
            f.add(tile(p), "on")
        return f

    fr = [(apps(slots), 8)]
    for k in range(4):
        f = apps(slots)
        for i in remove:
            f.add(tile(slots[i]), "hot" if k % 2 == 0 else "dim")
        fr.append((f, 2))
    pos = [slots[i] for i in keep]
    fr.append((apps(pos), 6))
    for j in range(len(keep)):  # survivors slide into place one at a time
        if pos[j] != slots[j]:
            pos[j] = slots[j]
            fr.append((apps(pos), 1))
    fr += [(apps(pos), 16), (base.copy(), 3)]
    fr += [(apps(slots[:3 * r]), 1) for r in range(1, 6)]  # refill row by row
    icon("ios-app-cleanup", fr, 0.08, poster=-7)


SMALL = {  # 3 x 5 letters for labels
    "A": [".X.", "X.X", "XXX", "X.X", "X.X"], "D": ["XX.", "X.X", "X.X", "X.X", "XX."],
    "E": ["XXX", "X..", "XX.", "X..", "XXX"], "I": ["XXX", ".X.", ".X.", ".X.", "XXX"],
    "K": ["X.X", "X.X", "XX.", "X.X", "X.X"], "L": ["X..", "X..", "X..", "X..", "XXX"],
    "M": ["X.X", "XXX", "XXX", "X.X", "X.X"], "N": ["XX.", "X.X", "X.X", "X.X", "X.X"],
    "O": [".X.", "X.X", "X.X", "X.X", ".X."], "P": ["XX.", "X.X", "XX.", "X..", "X.."],
    "R": ["XX.", "X.X", "XX.", "X.X", "X.X"], "S": [".XX", "X..", ".X.", "..X", "XX."],
    "T": ["XXX", ".X.", ".X.", ".X.", ".X."], "Y": ["X.X", "X.X", ".X.", ".X.", ".X."],
    ".": [".", ".", ".", ".", "X"],
}


def label(text, cx, r0):
    """Small text centred on column cx."""
    width = sum(len(SMALL[ch][0]) + 1 for ch in text) - 1
    c, out = cx - width // 2, []
    for ch in text:
        g = SMALL[ch]
        out += [(c + x, r0 + y) for y, row in enumerate(g) for x, v in enumerate(row) if v == "X"]
        c += len(g[0]) + 1
    return out


def skillsfile():
    """Repos -> skills.yaml (pinned) -> installed skills; an upstream update keeps your patch."""
    C, R, rows = 128, 28, [12, 17, 22]
    repo = lambda r: rect(6, r - 1, 16, r + 1) + hl(r, 11, 14)
    commit = lambda r: [(8, r)]
    feed = lambda r: hl(r, 17, 43)
    doc = [p for p in rect(44, 9, 72, 25) if p not in [(72, 9), (71, 9)]] + [(71, 10), (72, 11)]
    lengths = {12: 12, 17: 8, 22: 10}
    entry = lambda r: [(47, r)] + hl(r, 49, 48 + lengths[r])
    lock = lambda r: [(64, r - 1), (63, r), (64, r), (65, r), (63, r + 1), (64, r + 1), (65, r + 1)]
    out = lambda r: hl(r, 73, 101)
    skill = lambda r: rect(102, r - 1, 112, r + 1) + [(105, r), (106, r), (107, r)]
    patch = lambda r: fill(114, r - 1, 115, r)
    labels = label("REPOS", 11, 2) + label("SKILLS.YAML", 58, 2) + label("INSTALLED", 107, 2)
    base = (F().add(labels, "dim").add(sum((repo(r) for r in rows), []), "on").add(doc, "on")
            .add(sum((feed(r) + out(r) for r in rows), []), "dim").add(sum((rect(102, r - 1, 112, r + 1) for r in rows), []), "dim"))
    state = F()

    def frame(*parts, without=()):
        f = base.copy()
        f.update({c: cl for c, cl in state.items() if c not in without})
        for cells, cl in parts:
            f.add(cells, cl)
        return f

    def travel(paths, extra=()):
        return [(frame(*extra, (cells, "hot")), 1) for cells in
                [list(step[0]) for step in sparks(F(), paths, 6)]]

    fr = [(frame(), 4)]
    for r in rows:  # add: each repo's skill becomes a pinned entry
        fr.append((frame((commit(r), "hot")), 2))
        fr += travel([feed(r)])
        fr.append((frame((entry(r), "hot")), 2))
        state.add(entry(r), "on")
        fr.append((frame((lock(r), "hot")), 2))
        state.add(lock(r), "on")
    fr.append((frame(), 3))
    fr += travel([out(r) for r in rows])  # install all at once
    fr.append((frame((sum((skill(r) for r in rows), []), "hot")), 3))
    state.add(sum((skill(r) for r in rows), []), "on")
    fr.append((frame(), 4))
    fr.append((frame((patch(17), "hot")), 3))  # your own edit to one skill
    state.add(patch(17), "on")
    fr.append((frame(), 10))
    for k in range(3):  # upstream moves
        fr.append((frame((commit(17), "hot" if k % 2 == 0 else "on")), 2))
    fr += travel([feed(17)])
    fr.append((frame((lock(17), "hot"), (entry(17), "hot")), 3))  # re-pinned to the new commit
    fr += travel([out(17)])
    fr.append((frame(without=skill(17) + patch(17)), 2))
    fr.append((frame((skill(17), "hot"), without=patch(17)), 3))
    fr.append((frame((patch(17), "hot")), 4))  # the patch survives the update
    fr.append((frame(), 16))
    fr.append((base.copy(), 4))
    path = ROOT / "skillsfile" / "demo.svg"
    path.parent.mkdir(exist_ok=True)
    path.write_text(board(C, R, [("f", fr, 0.1, -2)], S=12, rad=3.9, rx=20, scale=0.6, blur=2.6,
                          label="skillsfile: repos to a pinned skills.yaml to installed skills"))
    print(f"wrote {path.relative_to(ROOT.parent)}")

# ---------- banner and social preview ----------

GLYPH = {
    "A": [".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "G": [".XXX.", "X...X", "X....", "X.XXX", "X...X", "X...X", ".XXX."],
    "E": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    "N": ["X...X", "XX..X", "X.X.X", "X..XX", "X...X", "X...X", "X...X"],
    "T": ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "..X.."],
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "K": ["X...X", "X..X.", "X.X..", "XX...", "X.X..", "X..X.", "X...X"],
    "I": [".XXX.", "..X..", "..X..", "..X..", "..X..", "..X..", ".XXX."],
    "L": ["X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"],
    " ": ["....."] * 7,
}
TITLE = "AGENT SKILLS"
TW = len(TITLE) * 6 - 1


def title(c0, r0):
    return [(c0 + i * 6 + c, r0 + r) for i, ch in enumerate(TITLE)
            for r, row in enumerate(GLYPH[ch]) for c, x in enumerate(row) if x == "X"]


def banner():
    C, R, c0 = 126, 21, 27
    text = F().add(title(c0, 7), "on").add(hl(16, c0, c0 + TW - 1), "dim")
    comet = [(F().add([(c, 16)], "hot").add([(c - 1, 16)], "on"), 1) for c in range(c0, c0 + TW)] + [(F(), 30)]
    layers = [("d", debate([2, 7, 12, 17, 22], 10, 7), 0.15, -2),
              ("h", climb(100, -2), 0.1, -2),
              ("c", comet, 0.035, -1)]
    path = ROOT / "banner.svg"
    path.write_text(board(C, R, layers, static=text, S=12, rad=3.9, rx=20, scale=1, blur=2.6, label="Agent Skills"))
    print(f"wrote {path.relative_to(ROOT.parent)}")


def freeze(frames, i):
    """A still of frame i, with the previous frame's bright cells as afterglow."""
    f = F().add([p for p, cl in frames[i - 1][0].items() if cl == "hot"], "on")
    f.update({p: cl for p, cl in frames[i][0].items() if not (p in f and RANK[f[p]] > RANK[cl])})
    return f


def social_preview():
    """GitHub's social preview: 1280 x 640, square corners, no animation."""
    C, R = 96, 48
    S, c0 = 1280 / C, (C - TW) // 2
    still = (F().add(title(c0, 8), "on").add(hl(17, c0, c0 + TW - 1), "dim")
             .add([(c0 + 44, 17)], "hot").add([(c0 + 43, 17), (c0 + 42, 17)], "on"))
    still.update(freeze(debate([13, 18, 23, 28, 33], 31, 7), 29))  # sparks heading into the last merge
    still.update(freeze(climb(60, 19), 7))
    still.update(freeze(orbit(48, 31, 9, [(48, 27), (52, 33), (44, 33)]), 2))
    screenshot(board(C, R, static=still, S=S, rad=S * 0.32, rx=0, scale=1, blur=2.8), ROOT / "social-preview.png", 1280, 640)


def screenshot(svg, png, w, h):
    chrome = os.environ.get("CHROME") or next(
        (p for p in [shutil.which("google-chrome"), shutil.which("chromium"),
                     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"] if p and os.path.exists(p)), None)
    if not chrome:
        sys.exit("no Chrome found for --png; set CHROME to its path")
    with tempfile.TemporaryDirectory() as tmp:
        (pathlib.Path(tmp) / "image.svg").write_text(svg)
        page = pathlib.Path(tmp) / "page.html"
        page.write_text(f'<!doctype html><style>html,body{{margin:0}}img{{display:block}}</style>'
                        f'<img src="image.svg" width="{w}" height="{h}">')
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                        f"--screenshot={png}", page.as_uri()], check=True, capture_output=True)
    print(f"wrote {png.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    council()
    icon("council-debate", debate([2, 7, 12, 17, 22], 12, 8), 0.15, poster=-2)
    icon("outer-loop-t3", orbit(12, 12, 10, [(12, 8), (16, 14), (8, 14)]), 0.3)
    icon("hill-climb", climb(0, 0), 0.1, poster=-2)
    ui_climb()
    diagram_rebuild()
    health_records()
    health_differential()
    ios_app_cleanup()
    skillsfile()
    banner()
    if "--png" in sys.argv:
        social_preview()
