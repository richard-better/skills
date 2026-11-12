# Council

Ask models from three labs the same question and get their answers side by side, with a
synthesis of where they agree, where they disagree, and what to do next. Models from different
labs share fewer defaults, so their agreement means more than one model's confidence.

Adapted from [`council`](https://github.com/t3dotgg/tstack/tree/main/skills/council) in Theo's
tstack. That version is built around code review; here the core works for any question, and the
code review rules (fixes before the audit, scores out of 10, the fix loop, the PR table) live in
[`references/code-review.md`](references/code-review.md), loaded only for a code or PR review.

## How it works

1. The agent picks the latest flagship from each of three providers, or the members you name.
   A missing provider is reported, never swapped for another model.
2. Each member gets the same neutral brief, in parallel and read-only, without the agent's own
   view.
3. The agent checks answers as they arrive, then summarizes findings, disagreements, who raised
   what, and its recommendation.

[`council-debate`](../council-debate/) adds rebuttal rounds on top.

## Use it

Say "council". It runs best in T3 Code, whose `delegate_task` puts each member on its model;
elsewhere it uses subagents or the labs' CLIs. See [what each skill needs](../../README.md#skills).
