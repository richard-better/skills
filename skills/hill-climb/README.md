# Hill climb

Pushes one measured number (bundle size, response time, eval pass rate) toward a target. Each
round builds competing candidates in parallel and keeps one only when it beats the best by more
than the noise floor.

![The best score moves in steps](../../assets/hill-climb/score-steps.png)

## How it works

A climb needs two things before the first change: a command that prints the number, and a
concrete target. The best score then moves in rungs. Changes inside the noise floor are reverted,
plateaus trigger a contest round with bigger approaches, and a holdout catches overfitting.

![One round of a climb](../../assets/hill-climb/round.png)

Every candidate gets a row in the ledger with its verdict, kept or reverted, so no idea is tried
twice.

## Related work

This skill and [`ui-climb`](../ui-climb/) build on [rebase-energy/hillclimb](https://github.com/rebase-energy/hillclimb)
and borrow from other public hill-climbing skills. They differ in running competing candidates in
parallel rounds with the owner in the loop; the others suit a single agent left to climb alone.

- [Bil0000/Hill-Climb](https://github.com/Bil0000/Hill-Climb): a script that locks the check and keeps or undoes each step, with paired timing, a holdout and multi-provider judges. Source of counting the work, finding the floor, the cheat list, repairs and milestone checks.
- [pstack's hillclimb playbook](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/hillclimb.md): one hypothesis per attempt and a decision log. Source of the stop rule with a minimum number of rounds.
- [autolab-ai/hills](https://github.com/autolab-ai/hills): a frozen evaluator that signs its reports. Source of what the number stands for and the final split scored once.

## Use it

Say "hill climb this to X". It runs in any agent and best in T3 Code, which builds candidates in
parallel; see [what each skill needs](../../README.md#skills).
