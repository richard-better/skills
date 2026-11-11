# Owner taste

The owner's recurring UI taste, written once and reused across climbs. Without it, reviewers
reward the defaults models share, and the owner rejects the same kind of fix round after round.

## Collect it

At setup, when no taste file exists:

1. Ask the owner for two or three screens they love and one they dislike, and what about each.
2. Ask which recurring fixes they reject (more labels, gradients, extra accent colour, centred
   empty states, ...).
3. Mine `decisions.md` of earlier climbs: every Drop and every rejected higher score says
   something about taste.

Write each value as one bold claim plus a line of what it means on screen, phrased as a settled
value reviewers judge within. Offer to save the file where the owner's agent instructions can
point at it, so the next climb starts with it.

## Format

```markdown
# <Owner>'s UI taste

- **<Value>.** <What it means on screen, concretely>.
```

Values that have worked, for the shape:

- **Compact marks over words.** A tint or a small mark instead of a spelled-out status line.
- **Each surface has one job.** Pending decisions live in one place; a log is a log.
- **Match the product's own components.** A new sheet looks like the other sheets.
- **Nothing moves under the pointer.** Controls keep their position while the user acts on them.
