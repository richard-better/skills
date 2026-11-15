# UI judge

Scores screenshots of a screen with a blind panel of models from different labs, against a
rubric, reference apps and your taste file, and lists ranked fixes with the models that named
each one. [`ui-climb`](../ui-climb/) uses it as its scorer.

## How it works

The skill holds what is the same for everyone: the panel rules (neutral labels, repeats, a
noise floor, frozen reference scores, a control), the general rubric rows, the checks a program
can measure, and `score.py`. Your taste lives in a file you own and edit: a short list of values
such as "compact marks over words". Swap the file and the same panel judges for someone else. A
repository can carry its own taste file for its product, and its values win over yours.

## Use it

Say "judge this UI". It needs models from two or more providers; see
[what each skill needs](../../README.md#skills).
