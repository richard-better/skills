# Council for code review

Before the review, address outstanding PR comments, fix known issues, and run relevant checks.
Give the council the updated implementation; known fixes go in now, not after the reviews
return. If the user wants to discard the implementation and explore new ideas, skip fixes to
code being replaced.

Leave the files alone while a delegate still reviews the same checkout.

Ask each delegate for a score out of 10. Count each full review pass as one round; a fresh review
after fixes starts a new round. A non-blocking delegate's late score is not recorded.

If you agree with their recommendations, make the changes and request a fresh review. Continue
until all delegates are satisfied. Repeated reviews invite scope creep; it is your job to keep
scope limited.

If the work ends in a pull request, put the results in the PR description, before the model and
harness line at the end:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus | 7/10 | 9/10 |
| GPT Sol | 8/10 | 10/10 |
| Gemini Pro | 7/10 | 9/10 |
```

If a delegate gives no score, write `no score`. If the PR is open, edit its description rather
than posting a comment. If there is no PR, put the same results in the final reply only.
