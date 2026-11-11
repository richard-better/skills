---
name: hill-climb
description: Hill-climb a number a program measures (size, speed, score, pass rate) toward a target, keeping only changes that beat the noise floor. Use for "hill climb", "get this to X", making something measurably faster or smaller, or building competing approaches to measure them all. Screen design climbs use ui-climb.
---

# Hill climb

A **climb** pushes one number toward a concrete target in **rounds**. Each round builds
**candidates** on the current best, an objective **scorer** measures each, and the climb keeps a
candidate only when it beats the best by more than the **noise floor**. Everything tried, kept or
reverted goes in the **ledger**, so no idea is tried twice and the losses save budget later.

The method follows [rebase-energy/hillclimb](https://github.com/rebase-energy/hillclimb): the
scorer defines what better means, candidates are immutable, a score is the median of repeated
**replicates** so variance is measured and never climbed, and a **holdout** catches overfitting.
Here the climber is you: you frame, score and decide, and subagents build the candidates.

## What makes a climb

Two things, both before the first change:

- **An objective scorer**: a command that prints the number. A program cannot be talked into a
  higher score.
- **A concrete target**: "Lighthouse 100", "CPU under 10 ms", "pass 12 of 12 cases".

| Target | Scorer |
| --- | --- |
| Bundle or output size | Bytes, gzipped, of the build output |
| Server CPU time | CPU ms per request from the platform's metrics (Cloudflare Workers) |
| Response time | p50 and p95 over N requests to a fixed set of URLs |
| Page quality | Lighthouse category scores, several runs, median |
| App launch | Launch timing from the device, cold, several runs |
| CI time | Wall clock of the pipeline on an unchanged commit, several runs |
| Agent quality | Eval pass rate on fixed cases, with repeats per case |
| Cost | Recorded spend per eval run |

A climb usually has one target and some **guards**: numbers that must not get worse. "Cut CI
time and output size, but keep CPU under 10 ms per request" makes CPU time a guard and the other
two targets.

When no program can produce the number, look for a measurable proxy first (a contrast ratio, tap
count, an eval case). For screen design, use `ui-climb`, which adds a scoring council. Otherwise
it is not a climb: say so and do the work as ordinary changes.

## 1. Frame the climb

Create the climb folder in the repository's plans folder, or `.climbs/<date>-<slug>/` when it
has none, with the files in [references/climb-files.md](references/climb-files.md).
Write `climb.md` with the owner:

- **Target**: the number, its direction, and the value to reach. What is out of scope.
- **Scorer**: the exact command, where it runs (local, staging, production), and the replicate
  count.
- **Guards**: each with its threshold. A candidate that breaks a guard is reverted however much it
  moves the target.
- **Protected paths**: the scorer, its fixtures and inputs, and the holdout. Candidates leave
  them untouched, so a score can only rise because the product got better.
- **Holdout**: inputs the candidates never see, scored only when a candidate is kept (unseen eval
  cases, pages left out of the benchmark). When the domain has none, say why.
- **Budget**: rounds, wall clock and paid spend. Paid model runs need the owner's approval.
- **Autonomy**: one mode from the table in step 3.

Done when every field is filled and the owner has approved the target and budget.

**Light climb**: when the owner wants a quick climb (an hour or so, a cheap local scorer), keep
only `ledger.md`, with target, scorer, guards and protected paths as its header, and build
candidates one at a time in place, committing each one kept. The baseline, the noise floor, one
change per candidate and the protected paths still hold.

## 2. Baseline and noise floor

Before changing anything:

1. **Check the scorer.** Feed it one known-good and one known-bad input, and confirm it ranks
   them correctly. Grader and measurement bugs are the most common reason a climb stalls or
   climbs the wrong hill. Fixing the scorer means re-baselining.
2. **Score the baseline at least three times**, more when the spread is wide next to the gains
   you expect. The **noise floor** is the spread (highest minus lowest) of those replicates;
   record each guard's spread the same way. Measure where the number really comes from (cold against warm, network against CPU) so a candidate cannot win
   on caching alone.
3. **Write the baseline row** of `ledger.md`: commit, replicate scores, median, noise floor,
   guard scores, cost.

Done when the ledger holds a baseline whose noise floor comes from at least three repeats.

## 3. Rounds

A round is one of two kinds.

**Step round**: two to four candidates, each one **attributable** change with a one-line
hypothesis, drawn from what the last scores show (the slowest request, the largest chunk, the
failing case). Read the ledger first and leave out anything already tried from this base.

**Contest round**: when the owner, a council or a review brings **competing ideas** ("prebuild
everything" against "cache at the edge"), build them all instead of debating which to try.
Group ideas that work together into **variants**, each a coherent set built as one candidate,
and keep ideas that exclude each other in separate variants. When two ideas are independent and
cheap, build each alone and both together. The table of results settles the argument. After a
variant wins, **ablate** it: remove each of its parts in turn and re-score, so the ledger
records which parts carried the gain and which were passengers.

Every round then:

1. **Build in parallel**, each candidate in its own worktree and branch, dispatched as below.
   The task names the base commit, the change or variant, the hypothesis, the scorer
   command and the protected paths. The child commits and reports the commit id; the parent scores every candidate, so
   all scores come from one place.

   | Harness | One candidate |
   | --- | --- |
   | T3 Code | `delegate_task` with `isolation: "worktree"` |
   | Claude Code | `Agent` with `isolation: "worktree"` |
   | Other subagents | A subagent told to work only in a checkout you made with `git worktree add` |
   | No subagents | Build candidates one after another yourself, each in its own `git worktree add` checkout |

2. **Check the diffs.** A candidate whose diff touches a protected path gets the verdict
   `touched scorer` and is never scored.
3. **Score each candidate alongside the current best**, with the same scorer, place and
   replicate count as the baseline, interleaving the runs (best, A, B, best, A, B, ...).
   Machines, caches and networks drift, so compare against the best as scored this round, never
   against a number stored from an earlier one.
4. **Decide.** The leader is the candidate whose median beats the best by more than the noise
   floor with every guard holding. A guard breaks when it misses its threshold by more than its
   own spread. The best of several noisy candidates is flattered by luck, so **confirm** the
   leader with a fresh set of replicates against the best before keeping it, then run the
   holdout. Record every other candidate with a verdict: `worse`, `no effect`, `guard broken`
   or `not confirmed`. When the runner-up also beat the floor and touches different things,
   combine it with the kept candidate as the next round's first candidate.
5. **Save the rung.** Merge the kept candidate onto the climb branch and tag it
   (`<slug>-climb-r<n>`). Every rung is a working fallback.
6. **Record the round** in the ledger: candidates, hypotheses, replicates, verdicts, cost. The
   parent is the only writer of the ledger.
7. **Checkpoint** as the autonomy mode says.

| Mode | Owner's words | Use when |
| --- | --- | --- |
| Checkpoint each round | "show me after each round" | First rounds, new direction |
| Unattended with a limit | "run five rounds on your own" | The target and guards are clear |
| Until the target | "get it to 100" | The scorer is cheap and trusted; the budget still stops it |

At a checkpoint, show the round as a table (candidates, hypotheses, replicates, median against
the best, guards, verdict) plus a recommendation, and ask numbered questions the owner can answer
in one line. Record every owner decision in `decisions.md` at once.

A round is done when every candidate has a ledger row with a verdict, and a kept candidate is
tagged as a rung.

## 4. Stop

- **Target reached**: confirm with one extra round of replicates, then close.
- **Plateau**: two rounds with nothing kept. Run one contest round of bigger, structurally
  different approaches from the latest rung ("what is the meta for this?"). Keep what beats the
  rung, otherwise close at the rung.
- **Budget**: stop when the next round would exceed any budget line.

## 5. Close

1. Land the best rung on the main branch the way the repository lands work.
2. Write the closing report into the climb folder: the score series per round, the change that
   moved the number most, the gap to the target, and the total cost.
3. Distill three to eight **claims** into `learnings.md`, each citing ledger rows as evidence,
   including `no effect` and `worse` results. Promote any claim that applies beyond this climb
   to the repository's docs or AGENTS.md.
4. Tell other agents climbing in the same repository about tooling they depend on (in T3 Code,
   with `t3_thread_send`).

Done when the main branch has the best rung, the report and `learnings.md` are committed, and
the evidence the report cites is committed or linked from it.

## Rules

- The owner decides what ships. A higher score that the owner rejects is recorded in
  `decisions.md` and stays rejected.
- A change to the scorer, its inputs, where it runs or the replicate count starts a new
  baseline. Scores from before and after are not compared.
- Keep the climb folder in git. Evidence that only exists in a scratch folder gets deleted.
