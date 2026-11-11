---
name: council-debate
description: Run the council skill, then have its members debate each other's answers. Use when the user asks the council to debate, argue it out, or cross-pollinate.
---

# Council Debate

An add-on to the `council` skill: after the council answers, every member reads
the others' answers and rebuts them. Follow `council` for choosing members,
dispatch, read-only work, and unavailable members; this skill adds the brief
file and the debate rounds.

## Round 1: the council answers

1. Write the brief once, to `council-brief.md` in your scratch directory. It
   carries the user's request and every piece of context a member needs, so
   it stands on its own. Leave your own view out of it, so members answer
   independently.
2. Run `council`, with each member's task pointing at the brief file. For a
   decision or open question, skip council's pre-audit fixes, scores, and fix
   loop; for a code review, keep them.
3. When every member has reported or failed, show the user each answer in
   full under its model name, then synthesize: agreements, disagreements,
   your recommendation. Report each failed member with its error and continue
   with the rest; a failed member sits out the debate.

## Debate rounds

Start the first debate round as soon as round 1 is shown. For each round:

1. Write `council-debate-r<N>.md`: the original brief, each member's latest
   answer labeled by model name, any pushback the user gave, then the
   rebuttal prompt below.
2. Dispatch one fresh `delegate_task` per member, same model and effort,
   pointing at that file. The file carries everything the member saw before,
   and a fresh task wakes this thread on completion.
3. Show each rebuttal in full under its model name, then synthesize:
   - **Concessions:** what each member admitted it missed.
   - **Resolved:** debates one position won, and why.
   - **Unresolved:** where they still disagree. These are the user's real
     decision points.
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

Run one debate round by default. Offer another only while an unresolved
tension remains, and fold in the user's pushback when they give it. After
three debate rounds, stop and give the final recommendation with the open
disagreements.
