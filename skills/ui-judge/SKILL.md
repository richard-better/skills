---
name: ui-judge
description: Score screenshots of a screen with a blind panel of models from different labs, against a rubric, reference apps and the owner's taste file. Use for "judge this UI", rating or comparing screen designs from screenshots, and as the scorer of a ui-climb.
---

# UI judge

A **panel** of models from different labs scores screenshots of a screen, blind, against a
**rubric**, **reference** shots and the owner's **taste file**, and lists ranked fixes. The panel
scores opinions, so the rules here keep them honest: neutral labels, repeats, a noise floor,
frozen references and a control.

The skill holds what is the same for every owner: the panel rules, the brief, the general
rubric rows, the measured checks and `score.py`. What one owner or one screen wants lives in
files the skill reads:

| File | Holds | Written by |
| --- | --- | --- |
| Taste file | Recurring taste across screens and projects | The owner, once, edited over time |
| `judge-context.md` | This screen's purpose, settled decisions, known capture artifacts | The owner and the agent, per screen |
| Rubric | General rows, plus the owner's cases and a veto row for this screen | Copied from [references/rubric.md](references/rubric.md), cases added with the owner |

Swap the taste file and the same panel judges for someone else.

## Taste file

Read the owner's taste file at setup, in this order:

1. The repository's: a path its `AGENTS.md` or `CLAUDE.md` names, else `docs/ui-taste.md`.
2. The owner's personal one: a path their agent instructions name.

When both exist, read both; a repository value wins where they conflict. When neither exists,
offer to collect one as in [references/taste.md](references/taste.md), and judge with the
general rows meanwhile.

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
3. **Read the taste file** and note the values that bear on this screen.
4. **Write the rubric** from [references/rubric.md](references/rubric.md): the general rows as
   they are, plus the owner's cases and a veto row when the owner has them.
5. **Collect the shots**: the product's, each cropped to the subject at most 1280 px wide, in
   every state and appearance being judged, and the references the owner chose, one app or site
   per folder with a README describing each shot.

Done when `judge-context.md` states the purpose, the panel is named, the rubric is written and
every shot is in place.

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

- The measured checks, pass or fail.
- `score.py`'s tables: one series per reviewer and the median, general rows apart from the
  owner's cases and the veto row, with the noise floor when there is a baseline.
- The fixes, each with the models that named it. Show what each model said, not a filtered
  conclusion; the owner decides what to build.

## Calibration

When the owner and the panel rank builds differently, the disagreement is missing taste or an
unclear rubric row. Ask the owner what made the difference, write it into the taste file or the
rubric, and rescore three or four builds the owner has ranked until the panel reproduces the
order. The skill stays the same; the files change.
