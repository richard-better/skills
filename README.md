# Agent Skills

A personal collection of reusable agent skills, installable with [`skills`](https://github.com/vercel-labs/skills).

## Skills

| Skill | Description |
|-------|-------------|
| [the-gang-t3](./skills/the-gang-t3/) | Ask a panel of models from different labs the same question in parallel through [T3 Code](https://github.com/pingdotgg/t3code)'s `delegate_task`, then synthesize and cross-pollinate their answers |
| [ios-app-cleanup](./skills/ios-app-cleanup/) | Bulk-uninstall apps from a paired iPhone with `xcrun devicectl`, picking them from a generated checklist page with App Store icons |
| [outer-loop-t3](./skills/outer-loop-t3/) | Say "outer loop" and a [T3 Code](https://github.com/pingdotgg/t3code) thread becomes the one conversation that launches, unblocks and supervises your other threads |
| [hill-climb](./skills/hill-climb/) | Push a measured number (size, speed, score, pass rate) toward a target in rounds of competing candidates, keeping only changes that beat the noise floor, with a ledger of everything tried |
| [ui-climb](./skills/ui-climb/) | Hill-climb a screen's design, scored by a blind council of models from different labs on screenshots against reference apps, with owner checkpoints on before-and-after pages |

## Install

```bash
# Pick skills interactively
npx skills add richard-better/agent-skills

# Or install one directly
npx skills add richard-better/agent-skills --skill the-gang-t3
```

Add `-g` to install globally instead of into the current project, and `-a <agent>` to target a specific agent (e.g. `claude-code`, `codex`).

## Requirements

- **the-gang-t3** runs inside T3 Code, which provides the `orchestrator_capabilities` and `delegate_task` tools. The panel models must be configured as providers in T3 Code; seats whose model is unavailable are left empty.
- **outer-loop-t3** runs inside T3 Code, which provides the thread tools (`t3_thread_launch`, `t3_thread_read`, `t3_thread_send`) and `schedule_task`.
- **ios-app-cleanup** needs macOS with Xcode, `python3`, `curl`, and an iPhone paired with the Mac with Developer Mode enabled.
- **ui-climb** builds on **hill-climb**: install both.
