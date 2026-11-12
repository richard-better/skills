---
name: health-differential
description: A panel of models takes a second look at a health records folder to find what the records have not already flagged. Use when asked for a differential or second look, after new results land, or when symptoms persist without a diagnosis.
---

# Health differential

A panel of models reads one person's health records and looks for what they have not
**already flagged**. It follows Microsoft's MAI-DxO, where the gain came from structure, not the
model: separate roles that propose diagnoses, attack the leading view, and audit the data, each
in fresh context. Frame everything as preparation for clinicians.

The records folder is built by `health-records`. Run that skill first when `index.md` is missing
or new PDFs have arrived. `records.py` is in its `scripts/` folder; run it with `uv run`.

## 1. Track record

If `<records>/panels/` holds an earlier report, read the latest. Its items are its New and
Re-ranked items, plus any its own Track record left `still open`. Score each `confirmed`,
`killed` or `still open` from evidence dated after that report: documents in `index.md`, rows in
`markers.csv`, and `context.md`. Items still open join this run's Already flagged list.

## 2. Case brief

Read `index.md`, `context.md`, every document, and `records.py table <records>`. Write
`<scratch>/health-differential/brief.md` with:

- **Demographics, medications and supplements**, with start and stop dates
- **Problem list**: every active and recently closed problem, one line each
- **Lab table**: the full output of `records.py table`
- **Already flagged**: every diagnosis, hypothesis, planned test and conclusion in the
  documents, `context.md` and open panel items, one line each with its source

Done when every document in `index.md` has contributed to the brief, or is named as having none.

## 3. Panel

Run `council` three times at once, one per role, so each member holds one role in fresh context:
nine answers from three labs. Each member's task:

```
You are the <ROLE> on a diagnostic panel. <ROLE BRIEF>

Read <scratch>/health-differential/brief.md, then the records it summarises in <records>:
index.md, context.md, documents/ and markers.csv. The brief is lossy; check the sources.

Write each finding as: claim / evidence (value, date, document) / confidence / discriminating
test. Mark each NEW or ALREADY-FLAGGED against the brief's Already flagged list.
```

- **Hypothesis**: probability-ranked diagnoses, per problem and **unifying** (one cause behind
  several problems). Update explicitly on every finding. Top 3 per cluster, with percentages.
- **Challenger**: assume each working diagnosis in Already flagged is wrong. Find contradicting
  evidence, anchoring, premature closure, treatment trials that failed without the diagnosis
  being revisited, and links across specialties nobody connected.
- **Data auditor**: trend every lab value, including drift inside the range. Find abnormal
  values never commented on, tests ordered but never resulted, dropped follow-ups, medication
  timing that lines up with symptom onset, and records that conflict.

Done when all nine members have answered or failed.

## 4. Synthesis

You are the test chooser and the steward of cost.

1. Merge duplicates. Rank higher what two or three labs raised independently, then what two or
   more roles raised; a single member's finding needs stronger evidence to make New.
2. **Novelty check**: grep the records folder for each finding's key terms. A finding already
   flagged moves to Re-ranked or is dropped.
3. **Verify** every cited value against its document, and drop findings that rest on a misread.
   Compare values across units with care; `records.py check` names those analytes.
4. For each surviving hypothesis, pick the 1 to 3 steps that best discriminate between the
   leading candidates. Prefer history questions and add-ons to planned blood draws over new
   visits, and new visits over imaging.

Done when every New item cites a value you checked against its document, and grep found no
earlier mention of it.

## 5. Report

Write `<records>/panels/YYYY-MM-DD-health-differential.md`, with `-2`, `-3` for another run that
day. Name the council's models at the top, then these sections in order:

- **Track record**, only when an earlier report exists: each item `confirmed`, `killed` or
  `still open`, with the result and date that settled it, then a tally of hits, misses and open
  items per model and per role.
- **New**: claim, evidence with dates and documents, who raised it (role and model), what would
  confirm or kill it, and the cheapest discriminating step. Probabilities are model estimates;
  the track record calibrates them.
- **Re-ranked**: existing hypotheses whose likelihood the panel moved, and why.
- **Next steps**: at most 5, ranked by information per cost and effort. Mark which can ride an
  already planned blood draw or visit.
- **Questions for the doctor**: short, ready to copy.
- **Checked, not worth chasing**: considered and dropped, with the reason.

Then run `records.py index <records>` so the index lists the report. Propose edits to
`context.md` and the documents to the owner rather than making them. When the records folder is a
git repository, commit the report and the index.
