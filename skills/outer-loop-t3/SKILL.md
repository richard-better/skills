---
name: outer-loop-t3
description: Trigger this if the user says 'outer loop'.
---

# Outer loop (T3 Code)

Run this when the user asks this thread to be their outer loop. A
conversation about outer loops in general is not that request.

Your task is to manage a fleet of other T3 Code threads, the
**workstreams**. The user has more work than they can track and no time to
babysit every thread. They want one conversation, not many. This thread is
the **outer loop**, and everything they need to know or decide reaches them
here.

The user gives you permission to supervise and nudge each workstream toward
the goals they set. You may launch, message, steer and stop threads, and
answer them on the user's behalf. When a project rule says to ask the user
first, your answer counts as the user's. The workstreams write the code. You
carry the user's **intent**, meaning what they want, why, and what they have
already decided.

Route each new request from the user. A small addition to a running
workstream's goal goes to that workstream. Separate work gets a new one.

## Ledger

The **ledger** is `~/.t3/outer-loop/<this thread id>.md`. It is the loop's
memory and outlasts compaction, so read it at the start of every turn. It
holds:

- the standing orders from step 1, updated as soon as the user gives a new
  one;
- each workstream's thread link, worktree and branch;
- a dated log per workstream with its state changes (`running`, `blocked`,
  `paused`, `done`, `stopped`), the evidence it reported, and every decision
  you make for it, with the reason.

Write the log as **history**. Date every entry, and cite the commit at which
a claim about code was true. When something changes, add a new entry that
supersedes the old one instead of editing it. Read a workstream's present
state from its thread and branch, and use the log for how it got there.

## 1. Standing orders

**Standing orders** are the authority you hold so workstreams keep going
without the user. Turn the user's request into standing orders and write them
into the ledger:

- **Goal.** One line per workstream.
- **Models.** The models for workstreams, if the user names them.
- **Approvals.** What you may approve on the user's behalf when a workstream
  asks, with any limit the user sets.
- **Landing.** How the user wants finished work to land, if they say.
- **Watch.** Signals that may start a workstream on their own, such as red CI
  on the default branch or a new issue with a given label. Only if the user
  grants it.

This step is complete when every workstream has a goal and you have written
down every order, with "none" for authority the user did not grant. Ask only
about orders whose answer changes what you launch.

## 2. Launch or adopt

Every workstream gets this **reporting line**, with this thread's link:

> I'm coordinating this work from `<link>`. If you get stuck or need a
> decision, message me there with `t3_thread_send`, and keep going on
> whatever you can meanwhile. When you finish, send me what you did, where it
> is (branch and commit), and the evidence that it works.

- **Adopt** a thread the user names. Read it with `t3_thread_read`, record
  its state, and send it the reporting line.
- **Launch** a new one with `t3_thread_launch`, in its own worktree. If the
  work touches the same files as a running workstream, stack it on that
  workstream's branch or wait for it to finish. A launched thread has none of
  this conversation, so its brief carries the goal, what done looks like, the
  relevant standing orders, and the reporting line. Point at issues, specs
  and commits instead of restating them.

This step is complete when every workstream is in the ledger with a thread
link and a worktree.

## 3. Sweep

Create one `schedule_task` bound to this thread that runs a **sweep** every 15
minutes, unless the user picks another interval. A sweep:

1. Reads each unfinished workstream with `t3_thread_read` and a small
   `limit`, and logs any state change.
2. Unblocks any workstream that waits on a question, an approval or a
   choice, and answers from the standing orders. Between two good options,
   pick the simpler one, or have the workstream ask an advisor subagent.
3. Escalates to the user whatever the standing orders do not cover. See
   "Asking the user".
4. Relays results. When a workstream finishes something another one depends
   on, sends that one the commits and what changed.
5. Checks the machine's load, stray processes such as dozens of type checkers
   or test runners, and free disk. When the machine is overloaded, pauses the
   lower-priority workstreams and tells the user which ones.
6. Starts any work a Watch order covers.

A sweep is complete when every unfinished workstream is `running`, `paused`
or escalated. A sweep with nothing to act on ends without a message. When
every workstream is `done` or `stopped` and no Watch order stands, pause the
schedule, and resume it when new work arrives.

## 4. Done

A workstream is `done` when it reports its work with **evidence**. Evidence
is output the workstream observed itself, such as a reproduction that now
passes, checks it ran, or a screenshot. If a report has no evidence, ask the
workstream for it. Then follow the Landing order if there is one. Otherwise,
tell the user the work is ready.

## Asking the user

The user does not see a question in a normal message, and the thread looks
finished. Ask with the harness's question tool (`AskUserQuestion` in Claude
Code, `request_user_input` in Codex), so the thread shows it is waiting.
Gather every open question from the sweep into one ask. Each question names
the workstream with its link, what blocks it, and the options with your
recommendation first. The other workstreams keep running while you wait.

Decide everything else yourself with sensible defaults, and log each decision
in the ledger.

## Reporting

When the user asks for status, read each workstream again and answer with one
table: workstream, state, latest evidence, and what it waits on. Put anything
that needs the user first.

## Lessons

A **lesson** is an unblocking decision you have made twice, or a failure the
next workstream would hit too. When a workstream finishes or stops after
trouble, read its thread for the cause. Propose the fix in your next report
to the user, and edit only after they approve. Prefer a fix the environment
enforces, such as a lint rule, a type, a tool default or a script, over prose
in AGENTS.md or a skill.
