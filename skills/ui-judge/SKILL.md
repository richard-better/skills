---
name: ui-judge
description: Score screenshots of a screen with a blind panel of models from different labs, against a rubric, reference apps and a taste file (a built-in default, or the user's own). Use for "judge this UI", rating or comparing screen designs from screenshots, and as the scorer of a ui-climb.
---

# UI judge

A **panel** of models from different labs scores screenshots of a screen, blind, against a
**rubric**, **reference** shots and a **taste file**, and lists ranked fixes. The panel
scores opinions, so the rules here keep them honest: neutral labels, repeats, a noise floor,
frozen references and a control.

The skill holds what is the same for everyone: the panel rules, the brief, the measured checks
and `score.py`. It also ships a **default taste** ([references/taste.md](references/taste.md),
distilled from Emil Kowalski's design skills) and a **default rubric**
([references/rubric.md](references/rubric.md)), which a user, a project or a single run can
replace.

## Taste and rubric

Take the taste and the rubric each from the first of these that has one:

1. **This run**: a file or values the user gives in the request, or a taste shipped beside the
   default that the request names: [Richard's](references/richard-taste.md).
2. **The project**: a path the repository's `AGENTS.md` or `CLAUDE.md` names, else
   `docs/ui-taste.md` and `docs/ui-rubric.md`.
3. **The user**: a path their agent instructions name.
4. **The default** in this skill.

The one found replaces the default whole. On top of either, each screen adds its own
`judge-context.md` (purpose, settled decisions, capture artifacts) and the owner's cases and
veto row in the rubric. A change of taste or rubric after a baseline starts a new baseline,
since scores from before and after are not comparable. A user who wants their
own taste file writes it as in [references/custom-taste.md](references/custom-taste.md).

## Measure first

Whatever a program can measure stays a program, reported beside the panel's scores and never
argued by it: contrast ratios, clipped or truncated text, overlap, tap counts for a flow, off-grid
spacing, radii outside the scale, Lighthouse accessibility. A measured failure settles what the
panel debates. When the judge serves a `ui-climb`, these become the climb's guards.

## 1. Set up

Put the judging in a folder with `rounds/<n>/` for each scoring round: the climb folder when a
`ui-climb` calls the judge, otherwise `.ui-judge/<date>-<slug>/` in the repository, or a scratch
folder when the shots are private.

1. **Name the panel** as in [references/panel.md](references/panel.md#the-panel): reviewers from
   at least two labs, fixed for as long as scores are compared.
2. **Write `judge-context.md`**: the screen's purpose ("an audit log: nobody comes here to find
   work"), the owner's settled decisions phrased as "judge within these", and known capture
   artifacts.
3. **Resolve the taste and the rubric** as in [Taste and rubric](#taste-and-rubric), and note
   the taste values that bear on this screen.
4. **Add the owner's cases** and a veto row to the rubric when the owner has them.
5. **Collect the shots**: the product's, each cropped to the subject at most 1280 px wide, in
   every state and appearance being judged, and the references the owner chose, one app or site
   per folder with a README describing each shot.

Done when `judge-context.md` states the purpose and names the taste and rubric sources, the
panel is named, and every shot is in place.

## 2. Score a round

1. **Generate the brief** at `rounds/<n>/BRIEF.md` from [references/brief.md](references/brief.md),
   with fresh neutral labels in `labels.json`.
2. **Run every reviewer** as its own read-only run on its model, as in
   [references/panel.md](references/panel.md#the-panel).
3. **Score** with `python3 <skill-dir>/scripts/score.py rounds/<n> [--prev rounds/<n-1>]
   [--frozen rounds/<baseline>]`, never by hand.
4. **Check each MUST fix against its shot.** A capture or fixture artifact goes into
   `judge-context.md` for the next brief, not into the fix list.

Done when `scores.json` is written and every MUST fix is confirmed against its shot or struck as
an artifact.

**Judging the same screen again**: score a baseline first, three fresh sessions per reviewer,
then freeze the reference scores and add a control at checkpoints, as in
[references/panel.md](references/panel.md#frozen-references). The spread of the baseline repeats
is the noise floor; a change inside it is no change.

## 3. Report

- The taste and rubric used: the default, or whose file.
- The measured checks, pass or fail.
- `score.py`'s tables: one series per reviewer and the median, general rows apart from the
  owner's cases and the veto row, with the noise floor when there is a baseline.
- The fixes, each with the models that named it. Show what each model said, not a filtered
  conclusion; the owner decides what to build.

## Calibration

When the owner and the panel rank builds differently, the disagreement is missing taste or an
unclear rubric row. Ask the owner what made the difference, write it into their own taste file
or rubric (starting one from the default when they have none), and rescore three or four builds
the owner has ranked until the panel reproduces the order. The skill and its defaults stay the
same; the owner's files change.
