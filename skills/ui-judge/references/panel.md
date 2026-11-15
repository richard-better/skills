# Panel

A fixed panel of models scoring screenshots against the [rubric](rubric.md). Panel scores are
noisy and biased in ways a program is not, so the panel has its own rules.

## The panel

- **Draw reviewers from at least two labs.** Models from one lab share their defaults, so a
  one-lab panel mostly agrees with itself.
- **Name the reviewers** in `judge-context.md`, or in `climb.md` for a climb, and keep the set
  fixed for as long as scores are compared. Each model has a stable bias (one scored 7 to 8
  while two others scored 8.3 to 8.6 on the same builds), so swapping a reviewer moves the mean
  by itself. Paid reviewers need the owner's approval by name.
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
- **Gate expensive reviewers** in unattended rounds: run the cheapest until its score moves, then
  the full panel. The full panel runs at every owner checkpoint. Late disagreement from the full
  panel is a finding, not a nuisance.
- A straggler that has not answered after ten minutes is scored without, and the round notes
  say so.

## Frozen references

Scored live every round, reference scores drift with the product's even though their shots never
change: in one climb, a reviewer's score for an unchanged reference tracked the product's at a
0.94 correlation. So references are scored once and frozen, and a control catches the scale
moving.

1. **Baseline**: each reviewer scores the product and every reference three times, in fresh
   sessions (`review-1`, `review-2`, `review-3`). `score.py` keeps each reviewer's median as its
   frozen score and the spread across its repeats; the median of those spreads is the noise
   floor.
2. **Later rounds**: reviewers see the reference shots as the bar for craft, but neither score
   them nor see the frozen numbers. Compare with `score.py <round> --frozen <baseline-round>`,
   which sets each reviewer beside its own frozen scores, since frozen scores do not transfer
   between models.
3. **Control**: at every owner checkpoint and at the last round, the unchanged baseline shots of the
   product join the round as `control`, blind like the rest. When the control's median has
   moved past the noise floor, the scale moved: report the gain net of the control's move, and
   say so instead of claiming a win.
4. **New reviewer**: scores its own baseline before its rounds count.

The dispatch that worked:

> You are design reviewer "Sol". Read and follow `<round>/BRIEF.md` exactly. Open every
> screenshot listed there and every reference image (read the README.md in each reference
> folder) as images. Work read-only: the only file you write is `<round>/review-1-Sol.md`. When
> done, reply with the path and a 5-line summary of your top fixes.

## Known reviewer behaviour

- Models share defaults (a serif, a dawn gradient), so agreement among them is weaker evidence
  than it looks.
- They flag capture and fixture artifacts as product bugs. Check each MUST against the shot
  before building it, and pass known artifacts to the brief as a note.
- They invent new patterns unless shown the product's own screens.
- They reopen settled values and reward copy the owner removed, unless `judge-context.md` says
  so.
- They answer product questions too (merge these screens?). The owner decides those.
