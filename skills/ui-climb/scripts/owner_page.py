#!/usr/bin/env python3
"""Build an owner page (proposals or check) from a JSON spec.

Usage: owner_page.py <spec.json> [-o page.html] [--embed]

The page is plain HTML first: every fix is a card with close-ups of the spots it touches, and
on wide screens the full shot sits beside the list with a numbered gutter. A small script adds
the controls: which shot to show, how to compare before and after (before, after, a slider,
an onion skin with a fader, or a difference blend that lights up changed pixels), highlights
on or off, clicking a highlight or number to select its fix, and answer buttons that build the
reply line. Without the script the page shows the slider at 50%, and answers in chat work.

Spec (paths absolute, boxes in image pixels as [x0, y0, x1, y1]):

{
  "kind": "proposals" | "check",
  "lead": "Check of round 6's build: answer Keep, Drop or Tweak per number.",
  "scores": {"columns": ["Grok", "Opus", "Sol", "Median"],
             "rows": [["General: build", 7.5, 7.5, 8, 7.5], ...],
             "note": "Noise floor 0.5. Guards pass.",
             "summary": "Headline for the Scores page: what moved, against the noise floor.",
             "targets": {"General": 8.5}},
  "shots": [{"id": "home", "label": "Homepage, desktop (dark)", "short": "Desktop",
             "src": "/abs/after.png", "before": "/abs/before.png",
             "names": ["Before", "After"]}],
  "items": [{"n": 1, "rec": "keep", "title": "Footer icons as one set",
             "body": "What changes, with values.", "note": "My call, when it differs.",
             "who": "Sol 2/3 · Opus 3/3", "shot": "home",
             "boxes": [[1100, 1792, 1196, 1886]], "before_boxes": [[1076, 1792, 1172, 1886]],
             "crops": [[x0, y0, x1, y1]]},
            {"n": 11, "shot": "cards", "title": "Card surface", "body": "...",
             "choices": [["brand", "Brand cards"], ["dark", "Dark cards"]], "rec": "dark",
             "boxes": [[...]]}],
  "missing": "States the shots did not show."
}

`rec` is yes / no / tweak on a proposals page and keep / drop / tweak on a check page. An item
with `choices` is a contest: its answers are the choices, its shot's `names` label the two
builds, and the reply reads "11 dark". `before_boxes` pairs with `boxes` by index; leave it out
when nothing moved, and give `[]` when the element is new. Each spot gets its own close-up at a
readable zoom; spots near each other share one, and `crops` overrides them. Shots must be the
clean captures, with nothing drawn on them; a shot's before and after share one crop.
"""

import argparse
import base64
import html
import json
import struct
import sys
from pathlib import Path

ANSWERS = {
    "proposals": [("yes", "Do it"), ("tweak", "Tweak"), ("no", "Not now")],
    "check": [("keep", "Keep"), ("tweak", "Tweak"), ("drop", "Drop")],
}
# Close-up window, in shot pixels (shots are captured at 2x, so 720 px is 360 CSS px).
PAD, MIN_W, MAX_W, MIN_H, MAX_H, MAX_CROPS = 48, 480, 720, 150, 340, 3

# Before and After read best as words; the modes and toggles are icons with a tooltip.
TOOLS = {
    "before": ("Before", "Show the before shot", None),
    "after": ("After", "Show the after shot", None),
    "slider": ("Slider", "Slider: drag across an image to wipe between before and after",
               "M3 5h18v14H3ZM12 3v18M8 10l-2 2 2 2M16 10l2 2-2 2"),
    "onion": ("Onion skin", "Onion skin: lay after over before and fade between them", "M4 4h11v11H4ZM9 9h11v11H9Z"),
    "diff": ("Difference", "Difference: only changed pixels light up",
             "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM12 3v18M12 8h4M12 12h5M12 16h4"),
    "hl": ("Highlights", "Highlights: outline the spots each fix touches", "M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M9 12h6"),
}


def image_size(path):
    data = Path(path).read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            marker, length = data[i + 1], struct.unpack(">H", data[i + 2 : i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return w, h
            i += 2 + length
    sys.exit(f"{path}: only PNG and JPEG shots are supported")


def src_for(path, embed):
    if not embed:
        return path
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def window(u, w, h):
    """A close-up around a union box: readable zoom, clamped to the image."""
    bw, bh = u[2] - u[0] + 2 * PAD, u[3] - u[1] + 2 * PAD
    cw = min(max(bw, MIN_W), MAX_W, w)
    ch = min(max(bh, MIN_H), h)
    x0 = u[0] - PAD if bw > cw else (u[0] + u[2]) / 2 - cw / 2
    y0 = (u[1] + u[3]) / 2 - ch / 2
    x0 = min(max(0, x0), w - cw)
    y0 = min(max(0, y0), h - ch)
    return [round(x0), round(y0), round(x0 + cw), round(y0 + ch)]


def spots(it):
    """Pair each after box with its before box; each spot is the union of the pair."""
    before = it.get("before_boxes")
    out = []
    for i, b in enumerate(it["boxes"]):
        pair = [b] + ([before[i]] if before and i < len(before) else [])
        out.append(union(pair))
    if before and len(before) > len(it["boxes"]):
        out += before[len(it["boxes"]) :]
    return out


def crops_for(it, w, h):
    if it.get("crops"):
        return it["crops"], 0
    clusters = []
    for s in sorted(spots(it), key=lambda b: (b[1], b[0])):
        for c in clusters:
            u = union(c + [s])
            if u[2] - u[0] + 2 * PAD <= MAX_W and u[3] - u[1] + 2 * PAD <= MAX_H:
                c.append(s)
                break
        else:
            clusters.append([s])
    wins = [window(union(c), w, h) for c in clusters]
    return wins[:MAX_CROPS], max(0, len(wins) - MAX_CROPS)


def pct(v):
    return f"{v:.4f}%"


def geo(crop, w, h):
    x0, y0, x1, y1 = crop
    cw, ch = x1 - x0, y1 - y0
    return f"width:{pct(w / cw * 100)};height:{pct(h / ch * 100)};left:{pct(-x0 / cw * 100)};top:{pct(-y0 / ch * 100)}"


def boxes_html(boxes, n, w, h):
    return "".join(
        f'<span class="hs" data-n="{n}" style="left:{pct(b[0] / w * 100)};top:{pct(b[1] / h * 100)};'
        f'width:{pct((b[2] - b[0]) / w * 100)};height:{pct((b[3] - b[1]) / h * 100)}"></span>'
        for b in boxes
    )


def compare(shot, crop, items, badge=None):
    """One comparable image: after (and before) clipped to `crop`, with highlight layers."""
    w, h = shot["w"], shot["h"]
    g = geo(crop, w, h)
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    after_hl = "".join(boxes_html(it["boxes"], it["n"], w, h) for it in items)
    before_hl = "".join(boxes_html(it.get("before_boxes", it["boxes"]), it["n"], w, h) for it in items)
    names = shot.get("names") or ["Before", "After"]
    if shot.get("before_img"):
        imgs = (
            f'<div class="imgs"><div class="pic b"><img src="{shot["before_img"]}" alt="{html.escape(names[0])}" style="{g}"></div>'
            f'<div class="pic a"><img src="{shot["img"]}" alt="{html.escape(names[1])}" style="{g}"></div></div>'
            f'<div class="layer b" style="{g}">{before_hl}</div><div class="layer a" style="{g}">{after_hl}</div>'
            f'<span class="name nb">{html.escape(names[0])}</span><span class="name na">{html.escape(names[1])}</span>'
            '<span class="handle"></span>'
        )
        cls = "cmp two"
    else:
        imgs = (
            f'<div class="imgs"><div class="pic a"><img src="{shot["img"]}" alt="" style="{g}"></div></div>'
            f'<div class="layer a" style="{g}">{after_hl}</div>'
        )
        cls = "cmp"
    b = f'<span class="cbadge">{badge}</span>' if badge is not None else ""
    return f'<div class="{cls}" style="aspect-ratio:{cw}/{ch}">{imgs}{b}</div>'


def tool(key):
    label, hint, path = TOOLS[key]
    if not path:
        return f'<button data-tool="{key}" title="{hint}" aria-pressed="false">{label}</button>'
    return (
        f'<button class="ico" data-tool="{key}" title="{hint}" aria-label="{label}" aria-pressed="false">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true"><path d="{path}"/></svg></button>'
    )


def score_cards(sc):
    """One card per rubric group ("General: build" groups under "General"), each subject a row
    with its median large and every reviewer as a dot on a shared scale."""
    e = html.escape
    cols = sc["columns"]
    mi = next((i for i, c in enumerate(cols) if c.lower() == "median"), None)
    reviewers = [(i, c) for i, c in enumerate(cols) if i != mi]
    groups = {}
    for row in sc["rows"]:
        label, vals = str(row[0]), row[1:]
        group, _, subject = label.rpartition(": ")
        groups.setdefault(group or label, []).append((subject if group else "", vals))
    nums = [float(v) for r in sc["rows"] for v in r[1:] if str(v).replace(".", "", 1).isdigit()]
    targets = sc.get("targets", {})
    nums += [float(t) for t in targets.values()]
    lo = max(0, int(min(nums)) - 1) if nums else 0
    hi = min(10, int(max(nums)) + 1) if nums else 10
    span = max(hi - lo, 1)

    def x(v):
        return f"{(float(v) - lo) / span * 100:.2f}%"

    grid = "".join(f'<span class="tick" style="left:{x(t)}"></span>' for t in range(lo, hi + 1))
    cards = []
    for group, subjects in groups.items():
        kind, _, name = group.partition(": ") if group.split(": ")[0] in ("case", "veto") else ("", "", group)
        badge = f'<span class="kind">{e(kind)}</span>' if kind else ""
        target = targets.get(group)
        target_line = f'<span class="target" style="left:{x(target)}"></span>' if target is not None else ""
        axis = "".join(
            f'<span class="{"lo" if t == lo else "hi" if t == hi else ""}" style="left:{x(t)}">{t}</span>' for t in range(lo, hi + 1)
        )
        if target is not None:
            axis += f'<span class="tlabel" style="left:{x(target)}">target {target}</span>'
        rows = []
        for si, (subject, vals) in enumerate(subjects):
            med = vals[mi] if mi is not None else None
            # Reviewers who gave the same score (or the median) stack above and below it.
            seen = {str(med): 1} if med is not None else {}
            dots = []
            for i, c in reviewers:
                k = seen.get(str(vals[i]), 0)
                seen[str(vals[i])] = k + 1
                dy = 0 if k == 0 else (-1) ** k * 13 * ((k + 1) // 2)
                dots.append(
                    f'<span class="dot" style="left:{x(vals[i])};margin-top:{dy}px" title="{e(c)} {e(str(vals[i]))}"></span>'
                )
            dots = "".join(dots)
            med_dot = f'<span class="med" style="left:{x(med)}"></span>' if med is not None else ""
            who = " · ".join(f"{e(c)} {e(str(vals[i]))}" for i, c in reviewers)
            rows.append(
                f'<div class="srow s{si % 6 + 1}"><div class="subj">{e(subject or name)}</div>'
                f'<div class="track">{grid}{target_line}{dots}{med_dot}</div>'
                f'<div class="medv">{e(str(med)) if med is not None else ""}</div><div class="who">{who}</div></div>'
            )
        cards.append(f'<div class="scard"><h4>{badge}{e(name)}</h4><div class="axis">{axis}</div>{"".join(rows)}</div>')
    return f'<div class="scards">{"".join(cards)}</div>'


def build(spec, embed):
    kind = spec["kind"]
    answers = ANSWERS[kind]
    labels = dict(answers)
    e = html.escape
    shots = {}
    for s in spec["shots"]:
        w, h = image_size(s["src"])
        shot = {**s, "w": w, "h": h, "img": src_for(s["src"], embed)}
        if s.get("before"):
            if image_size(s["before"]) != (w, h):
                sys.exit(f"{s['id']}: before and after shots must share a crop")
            shot["before_img"] = src_for(s["before"], embed)
        shots[s["id"]] = shot
    items = sorted(spec["items"], key=lambda it: it["n"])
    for it in items:
        if it["shot"] not in shots:
            sys.exit(f"item {it['n']}: unknown shot {it['shot']!r}")
        allowed = [c[0] for c in it["choices"]] if it.get("choices") else list(labels)
        if it["rec"] not in allowed:
            sys.exit(f"item {it['n']}: rec must be one of {', '.join(allowed)}")
    any_before = any(s.get("before_img") for s in shots.values())

    sc = spec.get("scores")
    scores_page = ""
    if sc:
        note = f'<p class="scorenote">{sc["note"]}</p>' if sc.get("note") else ""
        summary = f'<p class="summary">{sc["summary"]}</p>' if sc.get("summary") else ""
        scores_page = (
            f'<section class="page" data-page="scores"><h3 class="pagehead">Scores</h3>{summary}'
            f'{score_cards(sc)}{note}</section>'
        )

    # Toolbar at the top, sticky: the page switcher on the left, the review tools on the right.
    left, groups = [], []
    if sc:
        left.append(
            '<div class="toolGroup" role="group" aria-labelledby="lPage"><span class="toolLabel" id="lPage">Page</span>'
            '<div class="segment"><button data-goto="fixes" aria-pressed="true">Fixes</button>'
            '<button data-goto="scores" aria-pressed="false">Scores</button></div></div>'
        )
    if any_before:
        groups.append(
            '<div class="toolGroup review" role="group" aria-labelledby="lCmp"><span class="toolLabel" id="lCmp">Compare</span>'
            f'<div class="segment">{tool("before")}{tool("after")}<span class="div"></span>{tool("slider")}{tool("onion")}{tool("diff")}</div></div>'
            '<div class="toolGroup review mix" role="group" aria-labelledby="lMix"><span class="toolLabel" id="lMix">Mix</span>'
            '<div class="tools range"><input type="range" min="0" max="100" value="50" aria-label="After opacity"></div></div>'
        )
    groups.append(
        '<div class="toolGroup review" role="group" aria-labelledby="lHl"><span class="toolLabel" id="lHl">Show</span>'
        f'<div class="segment">{tool("hl")}</div></div>'
    )
    parts = [
        f'<div class="toolbar"><div class="side">{"".join(left)}</div><div class="side right">{"".join(groups)}</div></div>',
        f'<p class="lead">{spec["lead"]}</p>',
    ]

    # Viewer: the full shots, with a numbered gutter, behind a shot segment.
    seg = "".join(
        f'<button data-shot="{e(s["id"])}" aria-pressed="false">{e(s.get("short") or s["label"])}</button>'
        for s in shots.values()
    )
    views = []
    for s in shots.values():
        on = [it for it in items if it["shot"] == s["id"]]
        gutter = "".join(
            f'<a class="gbadge" href="#fix-{it["n"]}" data-n="{it["n"]}" data-y="{(spots(it) or [[0, 0, 0, 0]])[0][1] / s["h"] * 100:.4f}" '
            f'style="top:{(spots(it) or [[0, 0, 0, 0]])[0][1] / s["h"] * 100:.4f}%">{it["n"]}</a>'
            for it in on
        )
        views.append(
            f'<section class="view" data-shot="{e(s["id"])}"><h3>{e(s["label"])}</h3>'
            f'<div class="shotrow"><div class="gutter">{gutter}</div>{compare(s, [0, 0, s["w"], s["h"]], on)}</div></section>'
        )
    viewer = (
        f'<aside class="viewer"><div class="shottabs" role="tablist" aria-label="Shot">{seg}</div>'
        f'{"".join(views)}<p class="muted hint">Click a number or highlight to find its fix.</p></aside>'
    )

    # Cards: contests first, then grouped by recommendation.
    def card(it):
        s = shots[it["shot"]]
        wins, more = crops_for(it, s["w"], s["h"])
        closeups = "".join(compare(s, c, [it], it["n"]) for c in wins)
        more_note = f'<p class="muted">+{more} more spots, highlighted on the full shot.</p>' if more else ""
        opts = it.get("choices") or answers
        buttons = "".join(f'<button data-v="{v}" class="{v}">{e(lab)}</button>' for v, lab in opts)
        return (
            f'<article class="fix" id="fix-{it["n"]}" data-n="{it["n"]}" data-shot="{e(it["shot"])}">'
            f'<div class="head"><span class="num">{it["n"]}</span><b>{it["title"]}</b></div>'
            f'<div class="closeups">{closeups}</div>{more_note}<p>{it["body"]}</p>'
            + (f'<p class="note"><b>My call:</b> {it["note"]}</p>' if it.get("note") else "")
            + (f'<p class="who">{it["who"]}</p>' if it.get("who") else "")
            + f'<div class="dec">{buttons}</div></article>'
        )

    sections = []
    contests = [it for it in items if it.get("choices")]
    if contests:
        sections.append(f'<h3 class="group"><span class="chip contest">Contest</span>{len(contests)}</h3>' + "".join(map(card, contests)))
    for value, label in answers:
        group = [it for it in items if not it.get("choices") and it["rec"] == value]
        if group:
            sections.append(f'<h3 class="group"><span class="chip {value}">{label}</span>{len(group)}</h3>' + "".join(map(card, group)))

    missing = f'<h3>What the shots did not show</h3><p class="muted">{spec["missing"]}</p>' if spec.get("missing") else ""
    parts.append(
        '<section class="page" data-page="fixes">'
        f'<div class="layout">{viewer}<main class="list">{"".join(sections)}</main></div>'
        f'<div class="reply"><code></code><button class="copy">Select reply</button></div>{missing}</section>'
    )
    parts.append(scores_page)

    recs = {str(it["n"]): it["rec"] for it in items}
    order = [v for v, _ in answers]
    return (
        '<!doctype html><html data-cmp="slider" class="hl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<style>{CSS}</style></head><body>{''.join(parts)}"
        f"<script>const RECS={json.dumps(recs)},ORDER={json.dumps(order)},"
        f"CHOICE={json.dumps([it['n'] for it in contests])};{JS}</script></body></html>"
    )


CSS = """
:root{color-scheme:light dark;--fg:var(--foreground,CanvasText);--mut:var(--muted-foreground,GrayText);
 --line:var(--border,color-mix(in srgb,CanvasText 16%,Canvas));--surf:var(--card,color-mix(in srgb,CanvasText 4%,Canvas));
 --sel:var(--secondary,color-mix(in srgb,CanvasText 10%,Canvas));--ok:var(--success,#1f9d63);--warn:var(--warning,#d98a00);
 --bg:var(--background,Canvas);--r:var(--radius,10px);--mark:#ff4d6d;--pos:50%;--mix:.5}
*{box-sizing:border-box}
body{margin:0;font:14px/1.45 var(--font-sans,system-ui,sans-serif);color:var(--fg)}
button{font:inherit;color:inherit;cursor:pointer;border:0;background:transparent;border-radius:8px;transition:background-color 120ms ease,color 120ms ease}
button:focus-visible,a:focus-visible{outline:2px solid var(--ring,#7c9077);outline-offset:2px}
button:active{transform:scale(.98)}
@media(hover:hover) and (pointer:fine){button:hover{background:var(--sel)}}
.lead{font-size:15px;margin:0 0 12px}
.muted,.who{color:var(--mut);font-size:12px}
h3{font-size:13px;font-weight:600;margin:16px 0 8px}
.summary{font-size:17px;line-height:1.5;margin:8px 0 20px;max-width:60ch}
.scards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:16px}
.scard{--rule:color-mix(in srgb,var(--fg) 14%,transparent);border:1px solid var(--rule);border-radius:var(--r);background:var(--surf);padding:18px 20px 14px}
.scard h4{margin:0 0 14px;font-size:15px;display:flex;align-items:center;gap:8px}
.kind{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);border:1px solid var(--line);border-radius:99px;padding:1px 7px}
.srow{display:grid;grid-template-columns:minmax(0,1fr) 44px;grid-template-areas:"subj medv" "track track" "who who";gap:2px 12px;padding:10px 0;border-top:1px solid var(--rule)}
.srow:first-of-type{border-top:0}
.subj{grid-area:subj;font-size:13px}
.medv{grid-area:medv;font-size:22px;font-weight:600;text-align:right;line-height:1;font-variant-numeric:tabular-nums}
.who{grid-area:who;font-size:11px;color:var(--mut);font-variant-numeric:tabular-nums}
.track{grid-area:track;display:block;position:relative;height:40px;margin:4px 0 2px}
.track:before{content:'';position:absolute;left:0;right:0;top:50%;height:1px;background:var(--rule)}
.tick{position:absolute;top:0;height:100%;width:1px;background:color-mix(in srgb,var(--fg) 8%,transparent)}
.target{position:absolute;top:-2px;height:calc(100% + 4px);width:0;border-left:1.5px dashed color-mix(in srgb,var(--fg) 55%,transparent)}
.axis{position:relative;height:16px;margin:0 0 4px;font-size:10px;color:var(--mut);font-variant-numeric:tabular-nums}
.axis span{position:absolute;transform:translateX(-50%)}
.axis .lo{transform:none}.axis .hi{transform:translateX(-100%)}
.axis .tlabel{top:-14px;white-space:nowrap;color:var(--fg)}
.dot,.med{position:absolute;top:50%;border-radius:50%;transform:translate(-50%,-50%)}
.dot{width:8px;height:8px;border:1.5px solid var(--c);background:var(--surf);opacity:.8}
.med{width:14px;height:14px;background:var(--c);box-shadow:0 0 0 3px var(--surf)}
.s1{--c:var(--chart-1,#4f8cff)}.s2{--c:var(--chart-2,#3ecf8e)}.s3{--c:var(--chart-3,#a1a1aa)}
.s4{--c:var(--chart-4,#f5a524)}.s5{--c:var(--chart-5,#c084fc)}.s6{--c:var(--chart-6,#ff6b6b)}
.scorenote{margin:18px 0 0;font-size:13px;line-height:1.6;color:var(--mut);max-width:70ch}
/* toolbar */
.toolbar{display:none;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:12px 24px;margin:0 0 12px;padding:0 0 10px;position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
.toolbar .side{display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap}
.toolbar .right{margin-left:auto}
@media (max-width:720px){.toolbar{gap:8px}.toolbar .toolLabel{display:none}.toolbar .right{gap:8px}}
.toolbar .segment{margin-bottom:0}
.segment button.ico{width:34px;padding:7px;display:grid;place-items:center}
.segment svg{width:19px;height:19px;display:block}
.js .page{display:none}.js[data-page="fixes"] .page[data-page="fixes"],.js[data-page="scores"] .page[data-page="scores"]{display:block}
.js[data-page="scores"] .toolGroup.review{display:none}
.pagehead{margin-top:6px}.js .pagehead{display:none}
.js .toolbar{display:flex}
.toolLabel{display:block;font-size:10px;line-height:1.4;color:var(--mut);margin:0 0 5px 3px}
.tools{display:flex;align-items:center;gap:2px;padding:3px;border:1px solid var(--line);border-radius:10px}
.tools button{width:34px;height:34px;padding:7px;display:grid;place-items:center}
.tools svg{width:19px;height:19px;display:block}
.tools button[aria-pressed="true"]{background:var(--sel)}
.segment .div{align-self:center;height:18px;width:1px;background:var(--line);margin:0 3px}
.tools.range{height:42px;padding:3px 10px}.tools.range input{width:110px;accent-color:var(--mark)}
.mix{display:none}[data-cmp="onion"] .mix{display:block}
.segment{display:inline-flex;flex-wrap:wrap;padding:3px;border-radius:10px;background:var(--surf);border:1px solid var(--line);gap:2px;margin-bottom:8px}
.segment button{font-size:12px;min-height:32px;padding:6px 11px;color:var(--mut);white-space:nowrap}
.segment button[aria-pressed="true"]{background:var(--sel);color:var(--fg);box-shadow:0 1px 3px #00000012}
.shottabs{display:none;gap:4px;overflow-x:auto;scrollbar-width:none;border-bottom:1px solid var(--line);margin-bottom:10px}
.shottabs::-webkit-scrollbar{display:none}
.js .shottabs{display:flex}
.shottabs button{flex:none;font-size:13px;padding:8px 10px;border-radius:6px 6px 0 0;color:var(--mut);white-space:nowrap;
 border-bottom:2px solid transparent;margin-bottom:-1px}
.shottabs button[aria-pressed="true"]{color:var(--fg);border-bottom-color:var(--fg)}
/* comparable images */
.cmp{position:relative;overflow:hidden;border-radius:calc(var(--r) - 2px);border:1px solid var(--line);background:#181a19;touch-action:pan-y;user-select:none}
.cmp .imgs{position:absolute;inset:0;isolation:isolate}
.cmp .pic{position:absolute;inset:0;overflow:hidden}
.cmp img,.cmp .layer{position:absolute;display:block;max-width:none;pointer-events:none}
.cmp.two{cursor:ew-resize}
[data-cmp="before"] .two .pic.a,[data-cmp="after"] .two .pic.b{opacity:0}
[data-cmp="slider"] .two .pic.a{clip-path:inset(0 0 0 var(--pos))}
[data-cmp="onion"] .two .pic.a{opacity:var(--mix)}
[data-cmp="diff"] .two .pic.a{mix-blend-mode:difference}
[data-cmp="diff"] .two .imgs{filter:brightness(3) saturate(0)}
.layer.b,[data-cmp="before"] .two .layer.a{display:none}[data-cmp="before"] .two .layer.b{display:block}
.handle{display:none;position:absolute;top:0;bottom:0;left:var(--pos);width:2px;margin-left:-1px;background:#fff;box-shadow:0 0 0 1px #0006;pointer-events:none}
.handle:after{content:'';position:absolute;top:50%;left:-7px;width:16px;height:16px;margin-top:-8px;border-radius:50%;background:#fff;box-shadow:0 0 0 1px #0006}
[data-cmp="slider"] .two .handle{display:block}
.name{position:absolute;top:6px;font-size:10px;font-weight:600;padding:1px 6px;border-radius:99px;background:#000a;color:#fff;pointer-events:none;display:none}
.nb{left:6px}.na{right:6px}
.two .name{display:block}
[data-cmp="before"] .na,[data-cmp="after"] .nb{display:none}
[data-cmp="before"] .nb{left:auto;right:6px}
[data-cmp="diff"] .name{display:none}
.hs{position:absolute;border-radius:4px;outline:1.5px solid color-mix(in srgb,var(--mark) 55%,transparent);outline-offset:3px;transition:outline-color .12s,box-shadow .12s}
html:not(.hl) .hs{display:none}
.hs.on{outline:2px solid var(--mark);box-shadow:0 0 0 7px color-mix(in srgb,var(--mark) 22%,transparent)}
.dim .hs:not(.on){outline-color:color-mix(in srgb,var(--mark) 18%,transparent)}
.cbadge{position:absolute;left:6px;bottom:6px}
.cbadge,.gbadge,.num{width:20px;height:20px;border-radius:50%;background:var(--mark);color:#fff;font:700 11px/20px var(--font-sans,system-ui);text-align:center;text-decoration:none;flex:none}
/* viewer */
.shotrow{display:grid;grid-template-columns:24px minmax(0,1fr);gap:2px}
.gutter{position:relative}
.gbadge{position:absolute;left:0;margin-top:-2px;transition:transform .12s,box-shadow .12s}
.gbadge.on{box-shadow:0 0 0 3px color-mix(in srgb,var(--mark) 35%,transparent)}
.view h3{margin:4px 0 6px;color:var(--mut)}
/* cards */
.group{display:flex;gap:8px;align-items:center}
.chip{display:inline-block;font-size:11px;font-weight:600;padding:1px 8px;border-radius:99px}
.chip.yes,.chip.keep{background:color-mix(in srgb,var(--ok) 18%,transparent);color:var(--ok)}
.chip.tweak{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.chip.no,.chip.drop{background:var(--sel);color:var(--mut)}
.chip.contest{background:color-mix(in srgb,var(--mark) 18%,transparent);color:var(--mark)}
.fix{padding:12px 0;border-top:1px solid var(--line);scroll-margin:calc(var(--tb,0px) + 12px)}
.fix .head{display:flex;gap:8px;align-items:center;margin-bottom:8px}
.closeups{display:flex;flex-direction:column;gap:6px;margin-bottom:8px}
.fix p{margin:0 0 3px}.note{font-size:13px;color:var(--mut)}.note b{color:var(--fg);font-weight:600}
.dec,.reply,.hint{display:none}
.js .dec{display:inline-flex;gap:2px;margin-top:8px;padding:3px;border-radius:10px;background:var(--surf);border:1px solid var(--line)}
.dec button{font-size:12px;min-height:30px;padding:5px 11px;color:var(--mut)}
.dec button.on{color:var(--bg)}
.dec button.on.yes,.dec button.on.keep{background:var(--ok)}
.dec button.on.tweak{background:var(--warn)}
.dec button.on.no,.dec button.on.drop{background:var(--mut)}
.dec button.on:not(.yes):not(.keep):not(.tweak):not(.no):not(.drop){background:var(--fg)}
.js .reply{display:flex;gap:8px;align-items:center;margin-top:14px;padding:10px 12px;border:1px solid var(--line);border-radius:var(--r);background:var(--surf)}
.reply code{flex:1;user-select:all;font:12.5px var(--font-mono,ui-monospace,monospace)}
.reply button{font-size:12px;padding:6px 11px;border:1px solid var(--line);background:var(--sel)}
@media (min-width:721px){
 .js .layout{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:20px;align-items:start}
 .js .viewer{position:sticky;top:calc(var(--tb,0px) + 8px)}
 .js .hint{display:block}
 .js .view{display:none}.js .view.on{display:block}.js .view h3{display:none}
 .js .fix{padding:10px;border:1px solid transparent;border-radius:var(--r);cursor:pointer}
 .js .fix:not(.on) .closeups,.js .fix:not(.on)>.muted{display:none}
 .js .fix.on{background:color-mix(in srgb,var(--sel) 60%,transparent);border-color:color-mix(in srgb,var(--mark) 60%,transparent)}
}
@media (max-width:720px){.viewer{display:none}}
@media(prefers-reduced-motion:reduce){button,.hs,.gbadge{transition:none}button:active{transform:none}}
"""

JS = r"""
(() => {
const root = document.documentElement; root.classList.add('js');
const $ = (s, r=document) => r.querySelector(s), $$ = (s, r=document) => [...r.querySelectorAll(s)];
const ans = {...RECS}; let shot = $('.view')?.dataset.shot, sel = null, dragged = false;
function setCmp(m) { root.dataset.cmp = m; $$('[data-tool]').forEach(b => b.dataset.tool !== 'hl' && b.setAttribute('aria-pressed', String(b.dataset.tool === m))); }
function setPage(pg) {
  root.dataset.page = pg;
  $$('.segment button[data-goto]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.goto === pg)));
  if (pg === 'fixes') requestAnimationFrame(layoutGutter);
}
function setHl(on) { root.classList.toggle('hl', on); $('[data-tool="hl"]').setAttribute('aria-pressed', String(on)); }
function layoutGutter() {
  for (const g of $$('.view.on .gutter, .viewer:not(:has(.view.on)) .gutter')) {
    const h = g.offsetHeight; let bottom = -Infinity;
    for (const b of $$('.gbadge', g).sort((a, c) => a.dataset.y - c.dataset.y)) {
      const top = Math.max(b.dataset.y / 100 * h, bottom + 2); b.style.top = top + 'px'; bottom = top + 20;
    }
  }
}
function show() {
  $$('.shottabs button').forEach(b => {
    const on = b.dataset.shot === shot; b.setAttribute('aria-pressed', String(on));
    if (on) b.scrollIntoView({block: 'nearest', inline: 'nearest'});
  });
  $$('.view').forEach(v => v.classList.toggle('on', v.dataset.shot === shot));
  layoutGutter(); sync();
}
function sync(preview) {
  const lit = preview ?? sel;
  $$('.viewer .cmp').forEach(c => c.classList.toggle('dim', lit != null));
  $$('.viewer .hs, .gbadge').forEach(h => h.classList.toggle('on', +h.dataset.n === lit));
  $$('.fix').forEach(f => {
    f.classList.toggle('on', +f.dataset.n === sel);
    $$('.dec button', f).forEach(b => b.classList.toggle('on', ans[f.dataset.n] === b.dataset.v));
  });
  $('.reply code').textContent = reply();
}
function ranges(ns) {
  const out = [];
  for (const n of ns) { const l = out.at(-1); if (l && n === l[1] + 1) l[1] = n; else out.push([n, n]); }
  return out.map(([a, b]) => a === b ? `${a}` : `${a}-${b}`).join(', ');
}
function reply() {
  const ns = Object.keys(ans).map(Number).sort((a, b) => a - b);
  if (ns.every(n => ans[n] === RECS[n])) return 'go with recs';
  const plain = ns.filter(n => !CHOICE.includes(n));
  const parts = ORDER.map(v => [v, plain.filter(n => ans[n] === v)]).filter(([, g]) => g.length).map(([v, g]) => `${ranges(g)} ${v}`);
  return parts.concat(CHOICE.map(n => `${n} ${ans[n]}`)).join(', ');
}
function select(n, from) {
  sel = sel === n && from !== 'list' ? null : n;
  const f = $(`#fix-${n}`);
  if (sel != null && f.dataset.shot !== shot) { shot = f.dataset.shot; show(); } else sync();
  if (sel != null && from !== 'list') f.scrollIntoView({block: 'nearest', behavior: 'smooth'});
}
// Slider: drag anywhere on a two-image compare.
let active = null;
document.addEventListener('pointerdown', e => {
  const c = e.target.closest('.cmp.two'); if (!c || root.dataset.cmp !== 'slider') return;
  active = c; dragged = false; c.setPointerCapture(e.pointerId); move(e);
});
document.addEventListener('pointermove', e => { if (active) { dragged = true; move(e); } });
document.addEventListener('pointerup', () => { active = null; });
function move(e) { const r = active.getBoundingClientRect(); active.style.setProperty('--pos', Math.min(100, Math.max(0, (e.clientX - r.left) / r.width * 100)) + '%'); }
document.addEventListener('click', e => {
  const t = e.target;
  if (dragged) { dragged = false; return; }
  const go = t.closest('[data-goto]');
  if (go) { setPage(go.dataset.goto); scrollTo({top: 0}); return; }
  const tool = t.closest('[data-tool]');
  if (tool) { tool.dataset.tool === 'hl' ? setHl(!root.classList.contains('hl')) : setCmp(tool.dataset.tool); return; }
  const dec = t.closest('.dec button');
  if (dec) { ans[dec.closest('.fix').dataset.n] = dec.dataset.v; return sync(); }
  const sb = t.closest('.shottabs button');
  if (sb) { shot = sb.dataset.shot; sel = null; return show(); }
  const g = t.closest('.gbadge');
  if (g) { e.preventDefault(); return select(+g.dataset.n, 'shot'); }
  const twoView = t.closest('.viewer .cmp');
  if (twoView) {
    const r = twoView.getBoundingClientRect(), x = e.clientX, y = e.clientY;
    const hit = $$('.layer:not([style*="display: none"]) .hs', twoView).find(h => { const b = h.getBoundingClientRect(); return x >= b.left - 6 && x <= b.right + 6 && y >= b.top - 6 && y <= b.bottom + 6; });
    if (hit) return select(+hit.dataset.n, 'shot');
    return;
  }
  const flip = t.closest('.fix .cmp.two');
  if (flip && (root.dataset.cmp === 'before' || root.dataset.cmp === 'after')) { setCmp(root.dataset.cmp === 'before' ? 'after' : 'before'); return; }
  const fix = t.closest('.fix');
  if (fix && innerWidth > 720) return select(+fix.dataset.n, 'list');
  // Clipboard writes fail in many embedded viewers, so select the line for the owner to copy.
  if (t.closest('.reply .copy')) {
    const r = document.createRange(); r.selectNodeContents($('.reply code'));
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
    t.textContent = navigator.platform.startsWith('Mac') ? 'Now press ⌘C' : 'Now press Ctrl+C';
    setTimeout(() => { t.textContent = 'Select reply'; }, 2500);
  }
});
$('.mix input')?.addEventListener('input', e => root.style.setProperty('--mix', e.target.value / 100));
$('.list').addEventListener('mouseover', e => { const f = e.target.closest('.fix'); if (f && f.dataset.shot === shot) sync(+f.dataset.n); });
$('.list').addEventListener('mouseleave', () => sync());
const tb = $('.toolbar');
new ResizeObserver(() => root.style.setProperty('--tb', tb.offsetHeight + 'px')).observe(tb);
addEventListener('resize', layoutGutter);
Promise.all($$('img').map(i => i.decode().catch(() => {}))).then(layoutGutter);
setCmp(root.dataset.cmp); setHl(true); setPage('fixes');
if (innerWidth > 720) { const f = $('.fix'); sel = +f.dataset.n; shot = f.dataset.shot; }
show();
})();
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", help="output path (default: the spec path with .html)")
    ap.add_argument("--embed", action="store_true", help="inline the shots as data URIs, for viewers that cannot read local paths")
    args = ap.parse_args()
    spec = json.loads(Path(args.spec).read_text())
    out = Path(args.out or Path(args.spec).with_suffix(".html"))
    out.write_text(build(spec, args.embed))
    print(out)


if __name__ == "__main__":
    main()
