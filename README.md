# Agent Skills

A personal collection of reusable agent skills, installable with [`skills`](https://github.com/vercel-labs/skills).

The skills are built and tested in [T3 Code](https://github.com/pingdotgg/t3code). Its
`delegate_task` runs subagents on models from different providers, and its thread tools let one
conversation manage others. Some skills need those tools; the rest work in any agent and run
best in T3 Code.

## Skills

### For work

<table>
<tr>
<td width="50%" valign="top">
<a href="./skills/outer-loop-t3/"><img src="./assets/outer-loop-t3/thumb.png" alt="outer-loop-t3 diagram"></a>
<br><a href="./skills/outer-loop-t3/"><strong><code>outer-loop-t3</code></strong></a><br>
One thread that launches, unblocks and supervises your other threads<br>Say <em>"outer loop"</em>
</td>
<td width="50%" valign="top">
<a href="./skills/council-debate/"><img src="./assets/council-debate/thumb.png" alt="council-debate diagram"></a>
<br><a href="./skills/council-debate/"><strong><code>council-debate</code></strong></a><br>
Debate rounds for <a href="https://github.com/t3dotgg/tstack/tree/main/skills/council"><code>council</code></a>: models from three labs answer, then rebut each other<br>Say <em>"council, debate this"</em>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="./skills/hill-climb/"><img src="./assets/hill-climb/thumb.png" alt="hill-climb diagram"></a>
<br><a href="./skills/hill-climb/"><strong><code>hill-climb</code></strong></a><br>
Push a measured number toward a target, keeping only real wins<br>Say <em>"hill climb this to X"</em>
</td>
<td width="50%" valign="top">
<a href="./skills/ui-climb/"><img src="./assets/ui-climb/thumb.png" alt="ui-climb diagram"></a>
<br><a href="./skills/ui-climb/"><strong><code>ui-climb</code></strong></a><br>
Climb a screen's design, scored by a blind council of models<br>Say <em>"UI climb"</em>
</td>
</tr>
</table>

### For health

<table>
<tr>
<td width="50%" valign="top">
<a href="./skills/health-records/"><img src="./assets/health-records/thumb.png" alt="health-records diagram"></a>
<br><a href="./skills/health-records/"><strong><code>health-records</code></strong></a><br>
Turn health PDFs, in any language, into faithful documents and a <code>markers.csv</code> of lab results for trends<br>Say <em>"add these lab results"</em>
</td>
<td width="50%" valign="top">
<a href="./skills/differential-panel/"><img src="./assets/differential-panel/thumb.png" alt="differential-panel diagram"></a>
<br><a href="./skills/differential-panel/"><strong><code>differential-panel</code></strong></a><br>
Three roles on models from two labs look for what your records have not flagged<br>Say <em>"run the panel"</em>
</td>
</tr>
</table>

### Utilities

<table>
<tr>
<td width="50%" valign="top">
<a href="./skills/ios-app-cleanup/"><img src="./assets/ios-app-cleanup/thumb.png" alt="ios-app-cleanup checklist page"></a>
</td>
<td width="50%" valign="top">
<a href="./skills/ios-app-cleanup/"><strong><code>ios-app-cleanup</code></strong></a><br>
Bulk-uninstall apps from a paired iPhone, picked from a checklist page with App Store icons<br>Run <code>/ios-app-cleanup</code> (manual only)
</td>
</tr>
</table>

<details>
<summary><strong>What each skill needs</strong></summary>

| Skill | T3 Code | Model providers | Other skills | System |
|-------|---------|-----------------|--------------|--------|
| outer-loop-t3 | 🔒 Required | One | - | Any |
| council-debate | 🔒 Required | 🌐 Three | [`council`](https://github.com/t3dotgg/tstack/tree/main/skills/council) from t3dotgg/tstack | Any |
| hill-climb | ⭐ Recommended | One | - | Any |
| ui-climb | ⭐ Recommended | 🌐 Two or more | `hill-climb` | Playwright for web, simulator tooling for native |
| health-records | Not used | One that reads PDFs, or at least images | - | [`uv`](https://docs.astral.sh/uv/) |
| differential-panel | ⭐ Recommended | 🌐 Two | `health-records` | [`uv`](https://docs.astral.sh/uv/) |
| ios-app-cleanup | Not used | One | - | macOS with Xcode, `python3`, `curl`, and an iPhone paired with Developer Mode on |

- 🔒 **Required**: the skill calls T3 Code's tools (`delegate_task`, `t3_thread_launch`, `t3_thread_read`, `t3_thread_send`, `schedule_task`) and does not run without them.
- ⭐ **Recommended**: the skill uses T3 Code's tools when they are there and falls back to other harnesses. `hill-climb` builds candidates with Claude Code's `Agent`, another harness's subagents, or one at a time. `differential-panel` can run its seats with the labs' CLIs. `ui-climb` can score with lab CLIs (`codex exec`, `claude -p`, `gemini -p`) or API scripts.
- 🌐 **Providers**: models from different labs share fewer defaults, so the skill needs access to models from that many providers. `council` reports a missing provider instead of substituting another model.

</details>

## Install

```bash
# Pick skills interactively
npx skills add richard-better/agent-skills

# Or install one directly
npx skills add richard-better/agent-skills --skill council-debate
```

Add `-g` to install globally instead of into the current project, and `-a <agent>` to target a specific agent (e.g. `claude-code`, `codex`).

Install a skill's dependencies too: `ui-climb` with `hill-climb`, `differential-panel` with
`health-records`, and `council-debate` with `council`:

```bash
npx skills add richard-better/agent-skills --skill hill-climb
npx skills add richard-better/agent-skills --skill ui-climb
npx skills add richard-better/agent-skills --skill health-records
npx skills add richard-better/agent-skills --skill differential-panel
npx skills add t3dotgg/tstack --skill council
```
