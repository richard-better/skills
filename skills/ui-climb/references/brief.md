# Round brief

Generate `rounds/<n>/BRIEF.md` from this template each round. Reviewers read only the brief and
the images it lists, so it carries everything they need and nothing that anchors them.

## Blind labels

Give every scored subject a neutral label (A, B, C, ...) drawn in a new random order each
round, and write the key to `rounds/<n>/labels.json`:

```json
{ "A": "reference-1", "B": "product", "C": "reference-2" }
```

Which subjects are scored depends on the round, as in [council.md](council.md#frozen-references):

- **Baseline**: the product and every reference. Use `product` for the climb's own screens and
  the reference folder names for the rest.
- **Later rounds**: the product only. References still appear, under "Reference shots", as the
  bar for craft, with no label and no score.
- **Checkpoints and close**: the product plus `control`, the unchanged baseline shots of the
  product, so reviewers cannot tell which build is new.

Copy each scored shot into `rounds/<n>/shots/` as `<label>-<state>-<appearance>.png`, and
describe shots without naming an app or brand. Reviewers learn which label is the product only in the fixes
section, after they have scored.

## Template

````markdown
# Design review

You are reviewing app screens from screenshots. Work read-only: the only file you write is the
review file named in your task.

## The screen

<Purpose from judge-context.md: what the screen is for and who comes to it.>

Judge within these settled values; never ask to undo them:

- <Owner decisions and taste from judge-context.md>

Known capture artifacts, not product bugs: <list, or "none">.

## Subjects

Score each subject on its own shots, in this order. Score only what the shots show.

- **A**: `shots/A-<state>-<appearance>.png`, ... <one line per shot: what state it shows>
- **B**: ...

## Reference shots

<Later rounds only.> The bar for craft, never a look to copy. Do not score them.

- `refs/<n>-<state>-<appearance>.png`, ... <one line per shot, with no app or brand name>

## Rubric

Scale: 1 to 10 in half points. 5 is functional but generic, 7 a good shipping app, 9 best in
class.

<General rows, owner's cases and veto row from the climb's rubric, each with its question.>

## Scores

Write one block per subject, every row filled, exactly in this form:

```scores
subject: A
Typography: 7.5
Hierarchy: 8
Spacing and density: 7
Colour and contrast: 7.5
Iconography: 7
Consistency and polish: 7
Clarity: 8
case: One assistant: 6.5
veto: Grounded: 8
```

Rows prefixed `case:` are the owner's cases and `veto:` the veto row; write them with the same
names as the rubric.

## Fixes

Subject <product label> is the product under review. After the score blocks, list fixes for it,
each ranked MUST or SHOULD, with the shot and the location on screen:

- MUST: <fix>. Where: <shot>, <location>. Why: <what it improves, by rubric row>.
````

## What stays out

The target, the stop rule, past scores, the round number and the names behind the labels. Keep
those in `climb.md`, `ledger.md` and `labels.json`.
