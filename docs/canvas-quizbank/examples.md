# More examples

The main worked example, a genetics lecture run on three platforms, has its
own page: [Example: Hardy-Weinberg](example-hwe.md). The examples below ship
inside the skill; they are in
[`skills/canvas-quizbank/examples/`](https://github.com/hyunminkang/skills/tree/main/skills/canvas-quizbank/examples).

## Example bank: function factories in R

`advanced-r-function-factories/` holds 18 original items on Chapter 10 of
Hadley Wickham's *Advanced R* (2nd edition). Together they show every
feature of the schema:

- 15 multiple-choice items, and one each of multiple answers, numerical and
  true/false
- inline and display math, R code, a table and a figure
- 6 easy, 8 medium and 4 hard items

| file | what it is |
|---|---|
| `function-factories.yaml` | the bank |
| `function-factories.checks.R` | runs every snippet and recomputes every number (`Rscript function-factories.checks.R`) |
| `function-factories.review.md` | the review sheet |
| `ATTRIBUTION.md` | source and license notes |

The built packages (this bank and the smoke test) are in the repository's
[`samples/canvas-quizbank/`](https://github.com/hyunminkang/skills/tree/main/samples/canvas-quizbank),
ready to import. Skill zips cannot contain zips, so they are kept outside
the skill.

## Smoke test

`smoke-test/` has six neutral items: one of each question type, plus a
figure and a table. Import it once into a sandbox course to confirm that the
package format works on your Canvas; see [Smoke test](smoke-test.md).

## Rejected patterns

[Rejected patterns](rejected-patterns.md) shows what reviewers reject and
how each item was fixed. The agent reads it before drafting.
