---
name: differential-panel
description: Run a multi-model physician panel over a health records folder to find what the records have not already flagged. Use for "run the panel", "differential", "second look", "what are we missing", unexplained or multi-system symptoms, after new results land, or when a working diagnosis has stalled (a treatment trial failed, symptoms persist despite clean tests).
---

# Differential panel

A virtual physician panel over one person's health records, modelled on Microsoft's MAI-DxO
("Sequential Diagnosis with Language Models", 2025). The gain in that work came from
**structure, not the model**: separate roles that hypothesise, attack the leading view, and
weigh each test's information against its cost. One model asked "what's wrong?" anchors on
whatever the records already say. The panel exists to find what the records have **not**
already flagged.

Frame everything as preparation for clinicians, never as a diagnosis.

## The records folder

The panel reads a folder in the `health-records` skill's layout. Run that skill first when
`index.md` is missing or PDFs have arrived since it was generated.

| Path | Holds |
| --- | --- |
| `index.md` | The way in: every document with date, type and summary; the latest result of each analyte |
| `context.md` | The owner's own account: age, sex, conditions, medications with dates, questions |
| `documents/*.md` | Faithful transcriptions, frontmatter on top, PDF beside each |
| `markers.csv` | Every lab result, one row each; `records.py table <records>` prints each analyte's history |
| `panels/` | Earlier panel reports, the track record's input |

`records.py` is in the `health-records` skill's `scripts/` folder; run it with `uv run`.

## Output

One file, `<records>/panels/YYYY-MM-DD-differential-panel.md`, with `-2`, `-3` added for a second
run that day. Sections in this order:

0. **Track record**: only when an earlier panel exists. For each of its New and Re-ranked items,
   `confirmed`, `killed` or `still open`, with the result and date that settled it. Close with a
   tally, one line per model and per role: hits, misses, open.
1. **New**: findings not in Already flagged. Each: claim, evidence with dates and documents,
   who raised it (role and model), what would confirm or kill it, and the cheapest
   discriminating step.
2. **Re-ranked**: existing hypotheses whose likelihood the panel moved, and why.
3. **Next steps**: at most 5, ranked by information per cost and effort. Mark which can ride an
   already planned blood draw or visit.
4. **Questions for the doctor**: short, ready to copy.
5. **Checked, not worth chasing**: considered and dropped, with the reason.

## Process

### 0. Track record

If `panels/` holds an earlier report, read the latest. Its items are its New and Re-ranked
items plus the items its own Track record left `still open`, so a hypothesis stays tracked until
a result settles it. For each item, look for evidence dated after that report: documents in
`index.md`, rows in `markers.csv`, and `context.md`. Score each item `confirmed`, `killed` or
`still open` and write the Track record section first. Items still open join this run's Already
flagged list, so they are not reported as new a second time.

### 1. Case brief

Read `index.md`, `context.md`, every document and `records.py table <records>`. Write
`<scratch>/differential-panel/brief.md` with:

- **Demographics, medications and supplements**, with start and stop dates
- **Problem list**: every active and recently closed problem, one line each
- **Lab table**: the output of `records.py table`, every analyte with every value, date and
  reference range, so trends are visible
- **Already flagged**: every diagnosis, hypothesis, planned test and conclusion already in the
  documents, `context.md` and open panel items, one line each with its source

Done when every document in `index.md` has contributed its problems, conclusions and plans to
the brief, or is named as having none.

### 2. Panel: six seats

Three roles, each run on two models from different labs, so six seats with fresh context.
Use the models the owner names; otherwise the strongest reasoning model each of two labs
offers. Name both in the report. When one model is unavailable, run its three seats on the
other and say so; never swap in a third model silently. The seats read the records, so their
content goes to each model's provider.

Create one output directory per seat, then dispatch all six at once, read-only:

| Harness | One seat |
| --- | --- |
| T3 Code | `delegate_task` with `mode: "async"`, `role: "review"`, the model in `target`, and a `clientRequestId` of `differential-<date>-<role>-<model>`; check `orchestrator_capabilities` once for model names. End the turn and wait for the completions |
| A lab's CLI | Its non-interactive, read-only mode: `codex exec --sandbox read-only`, `claude -p` with only read tools allowed |
| Your own subagents | Only for seats on your own model; the other lab's seats still need one of the rows above |

Every seat gets the same task, varying only its role and directory:

```
You are the <ROLE> on a diagnostic panel. Your brief: <ROLE BRIEF>

Read <scratch>/differential-panel/brief.md, then the records it summarises in <records>:
index.md, context.md, documents/ and markers.csv. The brief is lossy; check the sources.
Work read-only: the only file you write is <seat-dir>/answer.md.

Write each finding as: claim / evidence (value, date, document) / confidence / discriminating
test. Mark each NEW or ALREADY-FLAGGED against the brief's Already flagged list.
```

| Role | Role brief |
| --- | --- |
| **Hypothesis** | Probability-ranked possible diagnoses, both per problem and **unifying** (one cause behind several problems). Update explicitly on every finding. Top 3 per cluster, with percentages. |
| **Challenger** | Assume each working diagnosis in Already flagged is wrong. Find contradicting evidence, anchoring, premature closure, treatment trials that failed without the diagnosis being revisited, and links across specialties nobody connected. |
| **Data auditor** | Trend every lab value, including drift inside the range. Find abnormal values never commented on, tests ordered but never resulted, follow-ups that dropped, medication timing that lines up with symptom onset, and records that conflict. |

Done when all six seats have written `answer.md` or failed; list failed seats with their error.

### 3. Synthesis

You are the test chooser, the steward of cost, and the checklist.

1. Read every `answer.md`. Merge duplicates across seats. Rank higher what **both models**
   raised independently, then what two or more roles raised; a finding from one seat needs
   stronger evidence to make New. Record which seats raised each finding.
2. **Novelty check**: grep the records folder for each finding's key terms. A finding already
   in Already flagged moves to Re-ranked or is dropped, never presented as new.
3. **Verify** every cited value against its document. Drop findings that rest on a misread.
4. For each surviving hypothesis, pick the 1 to 3 steps that best **discriminate** between the
   leading candidates. Prefer history questions and add-ons to planned blood draws over new
   visits, and new visits over imaging.
5. Write the report to `panels/`, then run `records.py index <records>` so the index lists it.
   Leave `context.md` and the documents unchanged; propose edits to the owner instead.
6. When the records folder is a git repository, commit the report and the index.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Restating the records' own conclusions as findings | Novelty check against Already flagged |
| Seats working only from the brief | The task sends them to the sources; the brief is lossy |
| Long test wish lists | At most 5 next steps, each tied to the hypothesis it discriminates |
| Ignoring drift inside the range | The data auditor trends every analyte, not only flagged ones |
| Treating one seat's idea as consensus | Report which roles and models raised it |
| Reading probabilities as calculated | They are model estimates; the track record calibrates them |
| Re-reporting last run's open items as new | Step 0 carries them into Already flagged |
| Comparing values across units | `records.py check` names analytes measured in more than one unit |
