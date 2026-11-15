# UI judge

Scores screenshots of a screen with a blind panel of models from different labs, against a
rubric, reference apps and a taste file, and lists ranked fixes with the models that named
each one. [`ui-climb`](../ui-climb/) uses it as its scorer.

## How it works

The skill holds what is the same for everyone: the panel rules (neutral labels, repeats, a
noise floor, frozen reference scores, a control), the general rubric rows, the checks a program
can measure, and `score.py`. It ships a default taste, distilled from the parts of
[Emil Kowalski's design skills](https://github.com/emilkowalski/skills) that show in a still
screenshot, and a default rubric. Supply your own taste file or rubric for one run, for a
project (`docs/ui-taste.md`, `docs/ui-rubric.md`), or for yourself, and it replaces the default.

## Use it

Say "judge this UI". It needs models from two or more providers; see
[what each skill needs](../../README.md#skills).
