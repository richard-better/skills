# Taste file

The owner's recurring UI taste, in a file the owner keeps and edits, read by every judging.
Without it, reviewers reward the defaults models share, and the owner rejects the same kind of
fix round after round. The skill ships no taste of its own: each owner writes theirs, and a
repository can carry one for its product.

## Format

```markdown
# <Owner or product>'s UI taste

- **<Value>.** <What it means on screen, concretely>.
```

One bold claim per value, plus a line of what it looks like on screen, phrased as a settled
value reviewers judge within. Values that have worked, for the shape:

- **Compact marks over words.** A tint or a small mark instead of a spelled-out status line.
- **Each surface has one job.** Pending decisions live in one place; a log is a log.
- **Match the product's own components.** A new sheet looks like the other sheets.
- **Nothing moves under the pointer.** Controls keep their position while the user acts on them.

Keep screen-specific decisions in `judge-context.md`; a value belongs here when it held on more
than one screen.

## Collect it

When the owner has no taste file:

1. Ask for two or three screens they love and one they dislike, and what about each.
2. Ask which recurring fixes they reject (more labels, gradients, extra accent colour, centred
   empty states, ...).
3. Mine the `decisions.md` of earlier climbs: every Drop and every rejected higher score says
   something about taste.

Write the file where the owner chooses, and offer to add a line to their agent instructions
naming its path, so every later judging finds it.
