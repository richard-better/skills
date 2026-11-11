#!/usr/bin/env python3
"""Score a UI climb round from its council reviews.

Usage: score.py <round-dir> [--prev <round-dir>]

Reads every `review-<repeat>-<Reviewer>.md` in the round directory, parses each fenced
```scores block (format in references/brief.md), maps neutral labels back to subjects with
`labels.json` ({"A": "product", "B": "<reference>", ...}), and prints one Markdown table per
row group:

- general: the median of the general rubric rows, the climb's target score
- case:<name>: each owner's case, reported apart
- veto:<name>: the veto row, reported apart

A reviewer's repeats are reduced to their median first, so each model counts once; the Median
column is the median across reviewers. With --prev, each median also shows its change against
that round. Writes `scores.json` into the round directory for the ledger.
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
    """Return {reviewer: {subject: {group: score}}}, repeats reduced to their median."""
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
    return {
        reviewer: {
            subject: {g: statistics.median(v) for g, v in groups.items()}
            for subject, groups in subjects.items()
        }
        for reviewer, subjects in repeats.items()
    }


def summarize(scores):
    """Return {group: {subject: {"reviewers": {...}, "median": x}}}."""
    table = {}
    for reviewer, subjects in scores.items():
        for subject, groups in subjects.items():
            for group, score in groups.items():
                cell = table.setdefault(group, {}).setdefault(subject, {"reviewers": {}})
                cell["reviewers"][reviewer] = score
    for subjects in table.values():
        for cell in subjects.values():
            cell["median"] = statistics.median(cell["reviewers"].values())
    return table


def fmt(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def print_tables(table, reviewers, prev):
    order = ["general"] + sorted(g for g in table if g != "general")
    for group in order:
        if group not in table:
            continue
        print(f"\n### {group}\n")
        print("| Subject | " + " | ".join(reviewers) + " | Median |")
        print("| --- | " + " | ".join("---" for _ in reviewers) + " | --- |")
        subjects = sorted(table[group], key=lambda s: (s != "product", s))
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
    args = parser.parse_args()

    labels_path = args.round_dir / "labels.json"
    if not labels_path.exists():
        sys.exit(f"{labels_path}: missing; write the label key when generating the brief")
    labels = json.loads(labels_path.read_text())

    scores = reviewer_scores(args.round_dir, labels)
    table = summarize(scores)

    prev = None
    if args.prev:
        prev_path = args.prev / "scores.json"
        if not prev_path.exists():
            sys.exit(f"{prev_path}: missing; score that round first")
        prev = json.loads(prev_path.read_text())

    reviewers = sorted(scores)
    if prev:
        reviewers = sorted(set(reviewers) | {
            r for g in prev.values() for c in g.values() for r in c["reviewers"]
        })
    print_tables(table, reviewers, prev)
    (args.round_dir / "scores.json").write_text(json.dumps(table, indent=2) + "\n")


if __name__ == "__main__":
    main()
