# Climb files

One folder per climb, committed with the work.

```text
.climbs/<date>-<slug>/
├── climb.md        target, scorer, guards, holdout, budget, autonomy
├── ledger.md       one row per scored candidate, the parent is the only writer
├── decisions.md    owner decisions, newest last, never reopened by later rounds
├── learnings.md    distilled claims, written at close
└── rounds/<n>/     evidence: scorer output, captures, the checkpoint page
```

## `climb.md`

```markdown
# <Slug> climb

- Goal: <what improves, for whom>. Out of scope: <...>
- Stands for: <what the number stands in for, in the owner's words>
- Target: <metric> <higher|lower> is better, reach <value> <unit>; floor <value>
- Stop rule: <target> and at least <n> rounds
- Scorer: `<command>`, run on <local|staging|production>, <n> replicates, median
- Guards: <metric> must stay <= <value>; ...
- Protected: <scorer, fixtures, holdout paths candidates leave untouched>
- Holdout: <inputs, or "none: why">; final split: <inputs scored once at close, or "none">
- Budget: <rounds>, <wall clock>, <paid spend>; paid models approved: <names>
- Autonomy: <mode>
- Branch: <climb branch>, rungs tagged `<slug>-climb-r<n>`
```

## `ledger.md`

Illustrative rows from a CPU-time climb with a CI-time guard:

```markdown
| Round | Candidate | Base | Hypothesis | Replicates | Median | Guards | Verdict | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | baseline | abc123 | - | 22.1, 22.9, 22.5 ms | 22.5 ms | ok | noise ±0.4 | $0 |
| 1 | prebuild | abc123 | Prebuilt HTML removes render CPU | 2.1, 2.3, 2.0 ms | 2.1 ms | CI +40 s | guard broken | $0.40 |
| 1 | edge-cache | abc123 | Cached responses skip the Worker | 9.8, 10.4, 9.9 ms | 9.9 ms | ok | kept, r1 | $0.35 |
```

## `learnings.md`

```markdown
- <subject> <helps | hurts | no effect | requires> <object>, on <scope>. Evidence: r1 c1, r3 c2.
```

A claim states something that transfers. "Lazy-loading above-the-fold images hurts LCP on
image-led landing pages" beats "c4 scored 81".
