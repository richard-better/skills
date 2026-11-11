---
name: ui-climb
description: Hill-climb a screen's design, scored by a council of models on screenshots against reference apps, with owner checkpoints. Use for "UI climb", making a UI match or beat a reference app or site, or rating a UI from screenshots in rounds.
---

# UI climb

A UI climb is a [hill-climb](../hill-climb/SKILL.md) on something no program can score: how a
screen looks. Read `hill-climb` first. Its frame, ledger, rungs, step and contest rounds, stop
rule and close all apply. One thing changes: the objective scorer becomes a **scoring council**,
a fixed panel of models scoring screenshots against a rubric and reference apps, set up as in
[references/council.md](references/council.md). Council scores are opinions, so this skill adds
what keeps them honest, plus what screens need.

Whatever part of the screen a program can measure stays a program: contrast ratios, clipped
text, tap counts for a flow, one spacing grid, one radius scale, Lighthouse accessibility. Make
those guards in `climb.md`. A measured guard settles what the council argues about.

## Repository tooling

When the repository has climb tooling, use it and follow its README for commands. Without
tooling, capture web with Playwright and native apps with the harness's simulator tooling (in T3
Code, `device_open`, then its `agent-device` command), and score with
[scripts/score.py](scripts/score.py).

## 1. Setup

On top of `hill-climb` step 1, where `climb.md` names the council's models in place of a
scorer command, and the climb folder gains `judge-context.md` (what the council may see):

1. **Scope one screen**, or two at most, and **state its purpose** in `judge-context.md` ("an
   audit log: nobody comes here to find work"). Without it reviewers optimise the wrong thing.
2. **Work in a dedicated worktree** with its own named simulator on iOS ("<app>-climb").
3. **Build fixtures of real screens**: the real views fed with sample data in the real format,
   modelled on the owner's actual data. Weak sample content reads as weak design. Pin the clock.
   When comparing against one product, make the content like for like and tell reviewers to
   judge presentation, not wording. A state reached by interaction (an open menu, a scrolled
   thread) comes from an input recorded once (a click path, a gesture replay) and replayed on the
   product and the references, so their frames match.
4. **Crop each capture to the subject**, at most 1280 px wide: every reviewer pays for every
   pixel in every round. Capture every state the screen has (empty, loading, long content,
   error), in each appearance the climb covers.
5. **Collect references from the owner**, one app or site per folder with a README describing
   each shot, in the same appearance as the climb. References are a bar for craft, never a look
   to copy. Climbs toward a feeling with no references have made products worse. Add **house
   shots**: the product's own neighbouring screens, so fixes match its existing components.
   When the goal is to match a reference exactly (a site the owner points at), say so in
   `judge-context.md` and score per state against it.
6. **Write the rubric with the owner** before round 1, from
   [references/rubric.md](references/rubric.md): the general rows, the owner's cases, and a veto
   row when the climb is about a feeling.
7. **Baseline** the product and every reference with the full council, three fresh sessions per
   reviewer, and freeze the scores as in
   [references/council.md](references/council.md#frozen-references). Their spread is the noise
   floor.

Done when `judge-context.md` states the screen's purpose, the owner has approved the rubric and
the references, and the ledger holds frozen baseline scores for the product and every reference.

## 2. A round

1. Capture every shot. Wait for content, never for a fixed time.
2. Generate the blind brief from [references/brief.md](references/brief.md), run the council,
   and score with `scripts/score.py`.
3. Fix pure UI bugs the council flags (clipping, overlap, misalignment) after checking each
   against the shot. A blank or broken shot is a capture problem until proven otherwise.
4. Show the owner the proposals page (step 3) and build only what is accepted, unless the
   autonomy mode says otherwise.
5. After every build, recapture, score and show the check page without being asked.

In a contest round between opposing looks ("one column" against "two panes"), capture every
variant with the same fixtures and show them side by side on one page with the council's scores,
so the owner chooses between built options.

## 3. Owner pages

The owner decides from one page per checkpoint. The format in
[references/owner-page.md](references/owner-page.md) converged over many rounds; follow it.
Each page opens with one line saying which kind it is:

- **Proposals**: fixes to decide before building. Answers: Do it, Not now, Tweak.
- **Check**: changes already built. Answers: Keep, Drop, Tweak.

After a build the owner dislikes overall, a change-by-change Keep or Drop list recovers the good
parts. Use it instead of reverting the whole round.

## 4. Plateau and bold rounds

Council scores plateau around 8, and a plateau is read against the references, not the absolute
score. At a plateau, ask the council what a 10 would take, small tweaks or a redo, and run the
answers as a contest round from a tagged rung, with what must survive named in the brief. Once a
climb ends, ask what transfers to the sister platform (web and iOS), and check before porting:
much of it does not.

## Owner taste

The owner's recurring taste may already be written down: in a file their agent instructions
point to, or in the repository beside its climb tooling. Read it at setup; when there is none,
collect it as in [references/owner-taste.md](references/owner-taste.md). Copy what applies into
the climb's `judge-context.md`. Repository preferences win over personal ones.
