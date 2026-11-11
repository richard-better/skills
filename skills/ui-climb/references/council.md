# Scoring council

The scorer of a UI climb: a fixed panel of models scoring screenshots against the
[rubric](rubric.md). Council scores are noisy and biased in ways a program is not, so the
panel has its own rules.

## The panel

- **Draw reviewers from at least two labs.** Models from one lab share their defaults, so a
  one-lab panel mostly agrees with itself.
- **Name the reviewers in `climb.md`** and keep the set fixed for the whole climb. Each model has
  a stable bias (one scored 7 to 8 while two others scored 8.3 to 8.6 on the same builds), so
  swapping a reviewer moves the mean by itself. Paid reviewers need the owner's approval by name.
- **Run each reviewer** as its own read-only run on its model, with a task that names
  `BRIEF.md` and the one file it writes:

  | Harness | One reviewer |
  | --- | --- |
  | T3 Code | `delegate_task` with `role: "review"` and the model in `target`; check `orchestrator_capabilities` once per thread for model names |
  | A lab's CLI | Its non-interactive mode, read-only: `codex exec`, `claude -p`, `gemini -p` |
  | API | A script that sends the brief and images to the model and writes its reply to the review file |

- **Repeat noisy reviewers** two times per round and take their median. Each model still counts
  once toward agreement.
- **Report one series per reviewer**, plus the median across them. Write "not run" for a reviewer
  that was skipped. Never average across a panel that changed.
- **Score the references** with the same panel every round.
- **Gate expensive reviewers** in unattended rounds: run the cheapest until its score moves, then
  the full panel. The full panel runs at every owner checkpoint. Late disagreement from the full
  panel is a finding, not a nuisance.
- A straggler that has not answered after ten minutes is scored without, and the round notes
  say so.

The dispatch that worked:

> You are design reviewer "Sol". Read and follow `<round>/BRIEF.md` exactly. Open every
> screenshot listed there and every reference image (read the README.md in each reference
> folder) as images. Work read-only: the only file you write is `<round>/review-1-Sol.md`. When
> done, reply with the path and a 5-line summary of your top fixes.

## The brief

Generate one `BRIEF.md` per round from the rubric, the shots and `judge-context.md`. Reviewers
read only the brief.

- **Blind**: the brief holds no target, stop rule, past score or round number. A stated target
  anchors scores to it. Keep those in `climb.md` and `ledger.md`.
- **`judge-context.md`** holds the screen's purpose and the owner decisions reviewers must
  respect, phrased as "judge within these, never ask to undo them". Reviewers reopen settled
  values and reward copy the owner removed unless told.
- **Output contract**: a score per rubric row in a fixed block the scoring script parses, then
  fixes ranked MUST or SHOULD, each with a location on screen. Score by script, never by hand.

## Which fixes to build

| Situation | Rule |
| --- | --- |
| Owner checkpoint | The owner picks per item. Show what each model said, not a filtered conclusion |
| Unattended | Build fixes at least two different models named independently |
| Two models contradict, or a value swings back and forth | Build both as a contest round, or cross-review: each reviewer reads the others and answers agree, concede (with what convinced it) or hold (with evidence) |
| A value argued twice | Settle it in `decisions.md` |

## Known reviewer behaviour

- Models share defaults (a serif, a dawn gradient), so agreement among them is weaker evidence
  than it looks.
- They flag capture and fixture artifacts as product bugs. Check each MUST against the shot
  before building it, and pass known artifacts to the brief as a note.
- They invent new patterns unless shown the product's own screens.
- They answer product questions too (merge these screens?). The owner decides those.

## Calibration

When the owner's ranking and the council's disagree, have the owner rank three or four builds,
then tune the rubric until the council reproduces that order.
