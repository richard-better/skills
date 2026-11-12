---
name: council
description: Ask one strong model from each of three labs the same question, then synthesize their answers. Use when the user says 'council'.
---

# Council

Bring in three delegates for the user's request: one strong model from each of three
different providers, at high reasoning effort. If the user's instructions name council members,
use those. Otherwise pick the latest flagship model from each provider, for example Claude Opus,
GPT Sol, and Gemini Pro.

In T3 Code, use `orchestrator_capabilities` to resolve the models, then `delegate_task` to start
one delegate per model in parallel. Elsewhere, use the harness's subagent tools or each lab's
CLI in its non-interactive mode. If you cannot reach three providers, or a named member is
unavailable, report it instead of substituting.

Give each delegate the request and all the context it needs, stated neutrally. Write it to a
brief file when it is long. Your own view stays in this thread, so every answer is independent.
Members work read-only unless the user asks otherwise.

Keep working while they run: check each answer against the sources as it arrives. If the user
marks a member as non-blocking, go on without it and treat a late answer as feedback.

Once every member has answered or failed, summarize the useful findings, the disagreements, who
raised what, and your recommended next steps. List each failed member with its error.

For a code or PR review, also follow [references/code-review.md](references/code-review.md).
