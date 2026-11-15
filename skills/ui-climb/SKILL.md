---
name: ui-climb
description: Hill-climb a screen's design, scored by ui-judge's blind panel of models against reference apps, with owner checkpoints. Use for "UI climb", or making a UI match or beat a reference app or site in rounds.
---

# UI climb

A UI climb is a [hill-climb](../hill-climb/SKILL.md) on something no program can score: how a
screen looks. Read `hill-climb` first. Its frame, ledger, rungs, step and contest rounds, stop
rule and close all apply. One thing changes: the objective scorer becomes
[`ui-judge`](../ui-judge/SKILL.md), a blind panel of models scoring screenshots against a
rubric, reference apps and the owner's taste file. Read it too. This skill adds what a climb on
screens needs around it.

`ui-judge`'s measured checks (contrast, clipped text, tap counts, one spacing grid, one radius
scale) become guards in `climb.md`.

## Repository tooling

When the repository has climb tooling, use it and follow its README for commands. Without
tooling, capture web with Playwright and native apps with the harness's simulator tooling (in T3
Code, `device_open`, then its `agent-device` command), score with `ui-judge`, and build owner
pages with [scripts/owner_page.py](scripts/owner_page.py).

## 1. Setup

On top of `hill-climb` step 1, where `climb.md` names the panel's models in place of a scorer
command, and the climb folder doubles as the judging folder of `ui-judge` step 1:

1. **Scope one screen**, or two at most, and **state its purpose** in `judge-context.md` ("an
   audit log: nobody comes here to find work"). Without it reviewers optimise the wrong thing.
2. **Work in a dedicated worktree** with its own named simulator on iOS ("<app>-climb"). When
   the design question is not platform specific, climb on web first: a capture takes seconds,
   not a native rebuild.
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
6. **Set up the judge** with the owner before round 1, as in `ui-judge` step 1: the panel, the
   taste file, and the rubric with the owner's cases, plus a veto row when the climb is about a
   feeling.
7. **Baseline** the product and every reference with the full panel and freeze the scores, as
   in `ui-judge`'s baseline. Their spread is the noise floor.

Done when `judge-context.md` states the screen's purpose, the owner has approved the rubric and
the references, and the ledger holds frozen baseline scores for the product and every reference.

## 2. A round

1. Capture every shot. Wait for content, never for a fixed time.
2. Score the round with `ui-judge` step 2.
3. Fix pure UI bugs the panel flags (clipping, overlap, misalignment) after checking each
   against the shot. A blank or broken shot is a capture problem until proven otherwise.
4. Show the owner the proposals page (step 3) and build only what is accepted, unless the
   autonomy mode says otherwise.
5. After every build, recapture, score and show the check page without being asked.

In a contest round between opposing looks ("one column" against "two panes"), capture every
variant with the same fixtures and show them side by side on one page with the panel's scores,
so the owner chooses between built options.

## Which fixes to build

| Situation | Rule |
| --- | --- |
| Owner checkpoint | The owner picks per item. Show what each model said, not a filtered conclusion |
| Unattended | Build fixes at least two different models named independently |
| Two models contradict, or a value swings back and forth | Build both as a contest round, or cross-review: each reviewer reads the others and answers agree, concede (with what convinced it) or hold (with evidence) |
| A value argued twice | Settle it in `decisions.md` |

## 3. Owner pages

The owner decides from one page per checkpoint, built with
[scripts/owner_page.py](scripts/owner_page.py) as in
[references/owner-page.md](references/owner-page.md): each fix sits next to its spot,
highlighted on the shot. Capture the shots clean and record each fix's element boxes while
capturing. Each page opens with one line saying which kind it is:

- **Proposals**: fixes to decide before building. Answers: Do it, Not now, Tweak.
- **Check**: changes already built. Answers: Keep, Drop, Tweak.

After a build the owner dislikes overall, a change-by-change Keep or Drop list recovers the good
parts. Use it instead of reverting the whole round.

## 4. Plateau and bold rounds

Panel scores plateau around 8, and a plateau is read against the references, not the absolute
score. The stop rule reads the owner's cases and the veto row as well as the general median, so
polish cannot hide a regression.

When polish stalls, look for the one-off styles each round added: a **system pass** (one type
scale, one spacing grid, one radius scale) beats another fix list. Then ask the panel what a 10
would take, small tweaks or a redo, and offer the answers to the owner as a list to choose from.
Run what they pick as a contest round from a tagged rung, with what must survive named in the
brief, and ask for improvements to the screen, not a new one: "be bold" without that replaced
designs wholesale. Building every bold proposal at once has not beaten a plateau. Once a climb
ends, ask what transfers to the sister platform (web and iOS), and check before porting:
much of it does not.

## Owner taste

`ui-judge` judges with the owner's taste file, or its default taste when they have none. When a
climb's `decisions.md` shows a value the owner held on more than one screen, offer at close to
add it to their taste file, starting one from the default if needed.
