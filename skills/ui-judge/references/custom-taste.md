# Custom taste

A taste file the user writes replaces the [default taste](taste.md) whole. It holds values
that hold across screens; a decision about one screen goes in `judge-context.md` instead.

## Format

```markdown
# <Owner or product>'s UI taste

- **<Value>.** <What it means on screen, concretely>.
```

One bold claim per value, plus what it looks like on screen, phrased as a settled value
reviewers judge within. The default taste is a complete example. Values from owners' files
that worked:

- **Compact marks over words.** A tint or a small mark instead of a spelled-out status line.
- **Each surface has one job.** Pending decisions live in one place; a log is a log.
- **Match the product's own components.** A new sheet looks like the other sheets.
- **Nothing moves under the pointer.** Controls keep their position while the user acts on them.

## Collect it

When the user wants their own taste file and has none:

1. Start from a copy of the default and ask which values they reject or would change.
2. Ask for two or three screens they love and one they dislike, and what about each.
3. Ask which recurring fixes they reject (more labels, gradients, extra accent colour, centred
   empty states, ...).
4. Mine the `decisions.md` of earlier climbs: every Drop and every rejected higher score says
   something about taste.

Save it where the user chooses: the project's `docs/ui-taste.md`, or a personal file their agent
instructions name.
