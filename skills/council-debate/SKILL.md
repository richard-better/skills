---
name: council-debate
description: Debate rounds for the council skill - after the council answers, each member rebuts the others. Use when the user asks the council to debate.
---

# Council Debate

Runs `council`, then adds debate rounds. `council` stays the source for
choosing members, dispatch, read-only work, and unavailable members.

## Round 1

1. Write the brief once, to `council-brief.md` in your scratch directory: the
   user's request plus all the context a member needs, stated neutrally. Your
   own view stays in this thread, so every first answer is independent.
2. Run `council`, each member's task pointing at the brief file. For a
   decision question, skip council's pre-audit fixes, scores, and fix loop.
3. Once every member has answered or failed, show each answer in full under
   its model name, then synthesize: agreements, disagreements, your
   recommendation. List each failed member with its error; it sits out the
   debate.

## Debate rounds

Start the first debate round right after round 1. Each round:

1. Write `council-debate-r<N>.md`: the brief, each member's latest answer
   under its model name, the user's pushback if any, then the rebuttal
   prompt below.
2. Dispatch a new `delegate_task` per member on the same model and effort,
   pointing at that file. The file carries the member's history; a new task
   wakes this thread when it completes.
3. Once every member has rebutted or failed, show each rebuttal in full
   under its model name, then synthesize:
   - **Concessions:** what each member admitted it missed.
   - **Resolved:** debates one position won, and why.
   - **Unresolved:** where they still disagree, the user's real decisions.
   - **New:** insights no round 1 answer had.

Rebuttal prompt:

```
You answered the brief above as one member of a council. Every member's
answer is above, yours included, labeled by model. Judge the arguments, not
the authors.

1. Where are the others right, and what did you miss?
2. Where are they wrong or soft?
3. Where do they contradict each other, and who is right?
4. State your final position, and what changed it.
5. What important point has nobody made clearly?

Be direct and disagree where you disagree. A diplomatic round is a wasted
round.
```

## Stopping

One debate round by default. Offer another while an unresolved tension
remains, folding in the user's pushback. After three debate rounds, give the
final recommendation with the open disagreements.
