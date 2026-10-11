# Authoring guide

How to write items an instructor keeps. These defaults come from several
rounds of instructor review of real banks. A course profile
(`references/profile.md`) adds to them and wins when the two conflict.

Contents: 1 what an item certifies · 2 the ten default rules · 3 item
styles and types · 4 stems, options, explanations · 5 difficulty · 6 the
coverage plan · 7 verification and the checks file · 8 figures ·
9 self-review before handing over

## 1. What an item certifies

Ask of every draft: *which idea from the material does a correct answer
show the student understands?* If the honest answer is "a detail of one
library's API" or "that they remember the slides", drop the item.

## 2. The ten default rules

1. **Test the core idea, not trivia.** Good targets are how a method works,
   how its cost grows, what a key step does, and how it behaves numerically.
   Asking about a key step of an implementation is fine. Never test a
   library's calling convention, argument order, one implementation's quirks
   or incidental naming. When the material *is* about a library (a chapter
   on `purrr`, a pandas tutorial), test the ideas its functions embody
   (what a map returns, that a reduction carries an accumulator, that a
   predicate search stops early), not argument names, shortcuts or
   aliases.
2. **Answerable without these slides.** Someone who knows the subject but
   never saw this material must be able to answer it. Do not use the
   material's private names for examples or strategies, its one-off
   notation, its helper-function names or its classroom analogies. Use
   standard terms and define every symbol in the stem. Code shown in full
   may define any function it needs, but give helpers generic names
   (`my_map`, `f`) rather than the material's.
3. **Numbers are fine; arithmetic is not the point.** Concrete numbers and
   small examples are welcome, but any computation takes at most one or
   two simple mental steps (16/4, (2 − 1)/0.5). Never require a
   calculator, a full substitution, or more than about five quick checks.
4. **Mix the styles in every bank.** Combine symbolic items (Θ(n²) in
   n, p, k), small concrete examples (a 2×2 matrix, five counts, a tiny
   graph), short code with "what does this print?" or "which line fails?",
   and realistic sizes where the arithmetic is mental (10,000 × 100). An
   all-symbolic or all-code bank is a defect.
5. **One clear question per stem.** Say exactly what is compared, counted or
   printed ("what does the last line print?", "how many times does `lm()`
   run?"). No two-part stems. When the answer depends on what a library
   call does and that behavior is *not* what the item tests, state it in
   the stem ("`ecdf(x)` returns the empirical CDF as a function"). When the
   behavior is the idea being tested, do not state it; make sure it is a
   core idea (rule 1).
6. **Options of the same shape.** Options are parallel in form and similar
   in length; the key is not the longest option. Put no "because ..."
   clause in options: reasons belong in `explanation`. Prefer values
   (outputs, numbers, Θ-classes) to prose. Avoid "all of the above" and
   "none of the above" unless the idea really needs it.
7. **Complete code that runs as printed.** Show the whole function, not a
   fragment. Run every snippet exactly as printed and recompute every number
   in the stem, options and explanation (section 7).
8. **No hints across items; even coverage.** Code or text in one item must
   not reveal another item's answer. Use each worked example about once.
   Spread items evenly over the material's sections. Do not refer to
   homework, exams, past terms or course-internal files.
9. **Overdraft, then let the instructor trim.** Draft about 1.3× the target
   (e.g. 65 for a 50-item bank), with difficulty around ⅓ easy, ½ medium
   and the rest hard, every item `status: draft`, and keys spread across
   positions.
10. **Explanations teach.** Two to four sentences: why the key is right,
    and what mistake leads to each tempting distractor. Canvas shows the
    explanation as feedback after the attempt.

## 3. Item styles and types

**Styles** (use several in every bank):

| style | example stem |
|---|---|
| predict the output | "What does the last line print?" |
| find the change | "Exactly one of these one-line changes makes it return 4. Which?" |
| find the error | "Exactly one row of the table is wrong. Which one?" |
| cost | "What is the total cost of the factory call and the k calls?" (Θ) |
| apply the idea to a new case | "Which value can `b()` never return?" |
| read a figure | "Which statement about the counts must be true?" |
| property | "Which term can be dropped without moving the maximum?" |

**Types.** Use multiple choice unless the instructor or profile asks for
others, or the request says "mix in other types". When other types are
allowed:

- `numerical`: the answer is one number a student can get in one or two
  mental steps (an estimate, a count, a probability). Give a tolerance or a
  range that accepts reasonable rounding, and say in the stem how many
  decimals to enter.
- `multiple_answers`: "select all that apply" over 4 or 5 statements with 2
  or 3 correct. Every statement is independently checkable.
- `true_false`: only for a clean, important statement. Use sparingly (at
  most about 1 in 20); true/false is the easiest type to guess.

Canvas has more types (matching, fill in the blank); this skill does not
build them.

## 4. Stems, options, explanations

- **Stem.** Put the setup (code, formula, table, figure) first and the
  question last, as its own short paragraph. Name variables generically
  (`x`, `f`, `fit`), not after the lecture's examples. Fix nuisance
  parameters so a Θ is in one variable.
- **Distractors** come from real mistakes: the off-by-one count, forgetting
  to divide by λ, the shared-state assumption, the value before an update,
  n instead of n − 1. Every distractor must be clearly wrong to someone who
  understands; if an expert could argue for it, rewrite it.
- **Options** are 4 for multiple choice (3 is the minimum). Order numeric
  options naturally or at random; the build keeps your order and Canvas
  shuffles when `shuffle_answers: true` (the default).
- **Explanation.** Say why the key is right, then name the mistake behind
  the main distractors. Do not restate the question.
- **Formatting.** Code in fenced blocks with a language (```` ```r ````,
  ```` ```python ````), math in `$...$` and `$$...$$`, tables as pipe
  tables. See `schema.md` for the supported Markdown.

## 5. Difficulty

- **easy:** one idea, applied directly (predict a short output, recognize
  a definition in use).
- **medium:** one idea applied to a case the material did not show, or two
  ideas combined in one short step.
- **hard:** a subtle consequence (lazy evaluation in a loop, what memory a
  closure keeps, a cost that changes with where work happens), still
  answerable in about two minutes.

Hard never means long, tricky wording or heavy arithmetic.

## 6. The coverage plan

Show this to the instructor before drafting, on one screen:

```
Bank: <title>                       Target: 50 kept → draft 65
Source: lecture09.pptx (155 slides), notes09.pdf (12 pages)
Languages: R, Python                Types: multiple choice only

section (source)                  objectives                         items  e/m/h
Seeds and generators (sl. 4-20)   seeds, period, Lehmer generator       8   3/4/1
Inverse transform (sl. 21-35)     continuous, discrete, Box-Muller      9   3/5/1
...
Total                                                                  65  22/32/11

Figures: 3 (a histogram, two density sketches). Not covered: <sections and why>.
```

Wait for an OK or edits. On "just build it", skip the plan and use the
defaults.

## 7. Verification and the checks file

- Run every code snippet as printed, in its own language. Recompute every
  number in stems, options and explanations. Check that each distractor is
  wrong.
- Save the code you ran next to the bank as `<bank>.checks.R` and/or
  `<bank>.checks.py`. It runs top to bottom, stops at the first failed
  check, and has one section per item, headed `# ---- <id>`. The validator
  warns when a `verified: run` item has no section. Wrap each section so
  one item's objects cannot change another's result:

  ```r
  # <bank>.checks.R — run: Rscript <bank>.checks.R
  check <- function(id, ok) {
    if (!isTRUE(ok)) stop("check failed: ", id, call. = FALSE)
    cat("ok", id, "\n")
  }
  cat(R.version.string, "\n")            # record versions of what you use
  # ---- ff-004: two counters
  local({
    ...code exactly as printed in the item...
    check("ff-004", identical(c(a(), a(), b(), a()), c(1, 2, 1, 3)))
  })
  cat("all checks passed\n")
  ```

  ```python
  # <bank>.checks.py — run: python3 <bank>.checks.py
  import sys
  def check(item_id, ok):
      if not ok:
          sys.exit(f"check failed: {item_id}")
      print("ok", item_id)
  print(sys.version)
  # ---- ff-004: two counters
  def _ff_004():
      ...code exactly as printed in the item...
      check("ff-004", result == [1, 2, 1, 3])
  _ff_004()
  print("all checks passed")
  ```

  When an item's answer depends on a fresh session (for example "object
  not found"), run that snippet on its own as well (`Rscript --vanilla
  -e '...'`, `python3 -I -c '...'`).
- Packages: load them in the section that uses them and print their
  versions. If a package the item needs is missing and cannot be installed,
  either rewrite the item with base functions (when the idea does not
  depend on the package) or mark it `verified: no` with the reason.
- Set `verified: run` only if the item's checks ran and passed. Otherwise
  set `verified: no` and a `verify_note` saying why ("R not available in
  this sandbox", "conceptual: nothing to execute"). Never "verify" R code by
  translating it to Python: random streams, integer types and printing
  differ between languages, and those are often what the item tests.
- A conceptual item with nothing to run can still check its numbers (a
  formula evaluated at the stem's values).
- Do not ask for the values of a language's own random generator unless
  the seed and generator are fixed in the stem and the item says which
  language; R and NumPy give different draws for the same seed.

## 8. Figures

- Use a figure only when the picture carries the idea (a curve's shape, a
  histogram's skew, a matrix's sparsity pattern). If a table or printed
  output says the same thing, use that.
- Draw with R (`png(..., width = 640, height = 400, res = 110)`) or
  matplotlib (`figsize=(6.4, 4), dpi=100`). Keep text at least 10 pt and
  labels on the axes. Do not encode meaning by color alone.
- Save as PNG under `figures/` next to the YAML, and keep the drawing code
  in the checks file.
- Alt text (required) describes what a student needs to answer: the axes,
  the shape and any marked values. It may contain the value a sighted
  student reads off the figure; it must not contain the conclusion the item
  asks for.
- To reuse a figure from the material, take it from the extractor's
  `media/` folder (a PPTX picture or a rendered PDF page), cropped to the
  figure.

## 9. Self-review before handing over

Run this over the whole bank, not only the newest items:

- [ ] `validate_bank.py --require-source --report` shows 0 errors; warnings
      are read and either fixed or explained.
- [ ] Every item's `source` points at a real slide, page or section.
- [ ] Key positions are spread out; the report's "key clearly the longest
      option" list is short (it is informational; when the long key is
      unavoidable, e.g. an option describing an error, say so in the
      hand-over).
- [ ] No item uses a name or symbol the stem does not define.
- [ ] No two items test the same example the same way, and no item answers
      another.
- [ ] Every `verified: no` has a reason, and they are listed for the
      instructor.
- [ ] The styles of section 3 are mixed.
