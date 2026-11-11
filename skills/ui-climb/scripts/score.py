#!/usr/bin/env python3
"""Score a UI climb round from its council reviews.

Usage: score.py <round-dir> [--prev <round-dir>] [--frozen <baseline-round-dir>]

Reads every `review-<repeat>-<Reviewer>.md` in the round directory, parses each fenced
```scores block (format in references/brief.md), maps neutral labels back to subjects with
`labels.json` ({"A": "product", "B": "<reference>", ...}), and prints one Markdown table per
row group:

- general: the median of the general rubric rows, the climb's target score
- case:<name>: each owner's case, reported apart
- veto:<name>: the veto row, reported apart

A reviewer's repeats are reduced to their median first, so each model counts once; the Median
column is the median across reviewers, and scores.json keeps each reviewer's spread across its
repeats. With --prev, each median also shows its change against that round. With --frozen, the
baseline round's subjects are added as "<subject> (frozen)" rows, so each reviewer's score sits
beside its own frozen reference and round-1 product scores. Writes `scores.json` into the round
directory for the ledger.
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

REVIEW_NAME = re.compile(r"^review-(\d+)-(.+)\.md$")
SCORES_BLOCK = re.compile(r"```scores\s*\n(.*?)```", re.DOTALL)


def parse_review(text, path):
    """Return {label: {row: score}} from every scores block in one review."""
    subjects = {}
    blocks = SCORES_BLOCK.findall(text)
    if not blocks:
        sys.exit(f"{path}: no ```scores block found")
    for block in blocks:
        label, rows = None, {}
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.rpartition(":")
            if not sep:
                sys.exit(f"{path}: cannot parse line {line!r}")
            key, value = key.strip(), value.strip()
            if key.lower() == "subject":
                label = value
                continue
            try:
                score = float(value)
            except ValueError:
                sys.exit(f"{path}: score for {key!r} is not a number: {value!r}")
            if not 1 <= score <= 10:
                sys.exit(f"{path}: score for {key!r} is outside 1 to 10: {score}")
            rows[key] = score
        if label is None:
            sys.exit(f"{path}: a scores block has no 'subject:' line")
        subjects[label] = rows
    return subjects


def group_of(row):
    lowered = row.lower()
    if lowered.startswith("case:") or lowered.startswith("veto:"):
        return row
    return "general"


def reviewer_scores(round_dir, labels):
    """Return {reviewer: {subject: {group: [score per repeat]}}}."""
    repeats = {}
    for path in sorted(round_dir.iterdir()):
        match = REVIEW_NAME.match(path.name)
        if not match:
            continue
        reviewer = match.group(2)
        for label, rows in parse_review(path.read_text(), path).items():
            if label not in labels:
                sys.exit(f"{path}: unknown subject label {label!r}")
            groups = {}
            for row, score in rows.items():
                groups.setdefault(group_of(row), []).append(score)
            per_group = {
                g: statistics.median(v) if g == "general" else v[0] for g, v in groups.items()
            }
            subject = labels[label]
            for group, score in per_group.items():
                repeats.setdefault(reviewer, {}).setdefault(subject, {}).setdefault(
                    group, []
                ).append(score)
    if not repeats:
        sys.exit(f"{round_dir}: no review-<repeat>-<Reviewer>.md files")
    return repeats


def summarize(repeats):
    """Return {group: {subject: {"reviewers": {...}, "spread": {...}, "median": x}}}."""
    table = {}
    for reviewer, subjects in repeats.items():
        for subject, groups in subjects.items():
            for group, scores in groups.items():
                cell = table.setdefault(group, {}).setdefault(
                    subject, {"reviewers": {}, "spread": {}}
                )
                cell["reviewers"][reviewer] = statistics.median(scores)
                cell["spread"][reviewer] = max(scores) - min(scores)
    for subjects in table.values():
        for cell in subjects.values():
            cell["median"] = statistics.median(cell["reviewers"].values())
    return table


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def add_frozen(table, frozen):
    """Add the baseline round's subjects as "(frozen)" rows beside this round's."""
    for group, subjects in frozen.items():
        for subject, cell in subjects.items():
            table.setdefault(group, {})[f"{subject} (frozen)"] = cell


def print_tables(table, reviewers, prev):
    order = ["general"] + sorted(g for g in table if g != "general")
    for group in order:
        if group not in table:
            continue
        print(f"\n### {group}\n")
        print("| Subject | " + " | ".join(reviewers) + " | Median |")
        print("| --- | " + " | ".join("---" for _ in reviewers) + " | --- |")
        subjects = sorted(table[group], key=lambda s: (s != "product", s != "control", s))
        for subject in subjects:
            cell = table[group][subject]
            cols = [
                fmt(cell["reviewers"][r]) if r in cell["reviewers"] else "not run"
                for r in reviewers
            ]
            median = fmt(cell["median"])
            before = prev.get(group, {}).get(subject, {}).get("median") if prev else None
            if before is not None:
                median += f" ({cell['median'] - before:+.2f})"
            print(f"| {subject} | " + " | ".join(cols) + f" | {median} |")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("round_dir", type=Path)
    parser.add_argument("--prev", type=Path, help="earlier round directory to compare against")
    parser.add_argument("--frozen", type=Path, help="baseline round directory with frozen scores")
    args = parser.parse_args()

    labels_path = args.round_dir / "labels.json"
    if not labels_path.exists():
        sys.exit(f"{labels_path}: missing; write the label key when generating the brief")
    labels = json.loads(labels_path.read_text())

    repeats = reviewer_scores(args.round_dir, labels)
    table = summarize(repeats)
    (args.round_dir / "scores.json").write_text(json.dumps(table, indent=2) + "\n")

    prev = load_scores(args.prev) if args.prev else None
    if args.frozen:
        add_frozen(table, load_scores(args.frozen))

    reviewers = sorted(repeats)
    if prev:
        reviewers = sorted(set(reviewers) | {
            r for g in prev.values() for c in g.values() for r in c["reviewers"]
        })
    print_tables(table, reviewers, prev)


def load_scores(round_dir):
    path = round_dir / "scores.json"
    if not path.exists():
        sys.exit(f"{path}: missing; score that round first")
    return json.loads(path.read_text())


if __name__ == "__main__":
    main()
