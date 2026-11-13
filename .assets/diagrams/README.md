# Diagrams

The skill pages' figures are generated as Excalidraw scenes. Each figure answers one question,
following the visual patterns in the `domi-tech-writing` skill.

| Figure | Question | Pattern |
| --- | --- | --- |
| `hill-climb/score-steps` | Why does the best score move in steps? | Illustrative plot |
| `hill-climb/round` | What does a round keep? | decision-flow |
| `ui-climb/round` | What does ui-climb change? | `hill-climb/round` with the scorer swapped |
| `council/council` | What does a council add over one model? | decision-flow |
| `council-debate/debate` | What does debating add to a council? | decision-flow |
| `outer-loop-t3/loops` | How does one thread keep the others moving? | nested loops |
| `health-records/pipeline` | How does a PDF become a document and marker rows? | decision-flow |
| `health-differential/panel` | How do three councils turn into one report? | decision-flow |
| `diagram-rebuild/loop` | How does an image become source that passes review? | decision-flow |

`climb.py` draws the climb figures, `health.py` the health-records and health-differential
figures, and `skills.py` the rest. `ui-climb/round` reuses every position from
`hill-climb/round`, so keep the two in step by editing `round_flow()` only.

## Regenerate

```bash
python3 .assets/diagrams/climb.py
python3 .assets/diagrams/skills.py
python3 .assets/diagrams/health.py
for f in .assets/*/*.excalidraw; do node skills/diagram-rebuild/scripts/render.mjs "$f" "${f%.excalidraw}.png"; done
```

Run `bash skills/diagram-rebuild/scripts/setup.sh` once first. Open any `.excalidraw` file at
excalidraw.com to edit it by hand, but regenerating overwrites hand edits. Review every render at
about 900 px wide, the width GitHub shows it: no overlapping or clipped text, no arrow through a
label.
