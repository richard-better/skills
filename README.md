# Agent Skills

A personal collection of reusable agent skills, installable with [`skills`](https://github.com/vercel-labs/skills).

The skills are built and tested in [T3 Code](https://github.com/pingdotgg/t3code). Its
`delegate_task` runs subagents on models from different providers, and its thread tools let one
conversation manage others. Some skills need those tools; the rest work in any agent and run
best in T3 Code.

## Skills

### Run many agents at once

| Skill | What it does | Say |
|-------|--------------|-----|
| [outer-loop-t3](./skills/outer-loop-t3/) | Makes one T3 Code thread the conversation that launches, unblocks and supervises your other threads | "outer loop" |
| [council-debate](./skills/council-debate/) | Adds debate rounds to tstack's `council`: after the council answers, members read and rebut each other's answers | "council, debate this" |

### Climb toward a number

| Skill | What it does | Say |
|-------|--------------|-----|
| [hill-climb](./skills/hill-climb/) | Pushes a measured number (size, speed, score, pass rate) toward a target in rounds of competing candidates, keeping only changes that beat the noise floor, with a ledger of everything tried | "hill climb this to X" |
| [ui-climb](./skills/ui-climb/) | Runs a hill-climb on a screen's design, scored by a blind council of models from different labs on screenshots against reference apps, with owner checkpoints on before-and-after pages | "UI climb" |

### Utilities

| Skill | What it does | Say |
|-------|--------------|-----|
| [ios-app-cleanup](./skills/ios-app-cleanup/) | Bulk-uninstalls apps from a paired iPhone with `xcrun devicectl`, picking them from a generated checklist page with App Store icons | `/ios-app-cleanup` (manual only) |

## What each skill needs

| Skill | T3 Code | Model providers | Other skills | System |
|-------|---------|-----------------|--------------|--------|
| outer-loop-t3 | 🔒 Required | One | - | Any |
| council-debate | 🔒 Required | 🌐 Three | [`council`](https://github.com/t3dotgg/tstack/tree/main/skills/council) from t3dotgg/tstack | Any |
| hill-climb | ⭐ Recommended | One | - | Any |
| ui-climb | ⭐ Recommended | 🌐 Two or more | `hill-climb` | Playwright for web, simulator tooling for native |
| ios-app-cleanup | Not used | One | - | macOS with Xcode, `python3`, `curl`, and an iPhone paired with Developer Mode on |

- 🔒 **Required**: the skill calls T3 Code's tools (`delegate_task`, `t3_thread_launch`, `t3_thread_read`, `t3_thread_send`, `schedule_task`) and does not run without them.
- ⭐ **Recommended**: the skill uses T3 Code's tools when they are there and falls back to other harnesses. `hill-climb` builds candidates with Claude Code's `Agent`, another harness's subagents, or one at a time. `ui-climb` can score with lab CLIs (`codex exec`, `claude -p`, `gemini -p`) or API scripts.
- 🌐 **Providers**: models from different labs share fewer defaults, so the skill needs access to models from that many providers. `council` reports a missing provider instead of substituting another model.

## Install

```bash
# Pick skills interactively
npx skills add richard-better/agent-skills

# Or install one directly
npx skills add richard-better/agent-skills --skill council-debate
```

Add `-g` to install globally instead of into the current project, and `-a <agent>` to target a specific agent (e.g. `claude-code`, `codex`).

Install a skill's dependencies too: `ui-climb` with `hill-climb`, and `council-debate` with `council`:

```bash
npx skills add richard-better/agent-skills --skill hill-climb
npx skills add richard-better/agent-skills --skill ui-climb
npx skills add t3dotgg/tstack --skill council
```
