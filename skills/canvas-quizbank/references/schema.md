# Bank schema

A bank is one YAML file: a title, a description, and a list of questions.
`scripts/validate_bank.py` enforces everything below.

```yaml
title: "Example Bank: Function Factories in R"   # Canvas shows it as the bank/quiz name
description: |                                    # for people; not exported
  Where the items come from, how they were checked, how to build.
questions:
  - id: ff-004                    # unique, never reused; letters, digits, . _ -
    topic: function-factories     # optional free tag
    objective: state              # learning objective tag; the report counts these
    difficulty: medium            # easy | medium | hard
    status: draft                 # draft | reviewed | removed (default draft)
    source: "Advanced R (2e) §10.2.4"   # where in the material; shown in feedback
    verified: run                 # run | no
    verify_note: "..."            # required when verified: no
    title: "Two counters"         # short name; Canvas title becomes "ff-004 · Two counters"
    type: multiple_choice         # see "Types" (default multiple_choice)
    points: 1                     # default 1
    shuffle_answers: true         # default true (choice types only)
    question: |                   # Markdown + $TeX$; see "Markdown"
      ...
    choices: [...]                # choice types only
    answer: 3                     # form depends on type
    explanation: |                # Markdown; Canvas general feedback
      ...
```

Required: `id`, `objective`, `difficulty`, `question`, `answer`,
`explanation`; `choices` for the choice types. `source` is required for new
drafts (`--require-source`). The validator warns without it, so older banks
still build.

## Types

| type | `choices` | `answer` | Canvas type |
|---|---|---|---|
| `multiple_choice` | 3+ distinct | zero-based index: `2` | multiple choice |
| `multiple_answers` | 3+ distinct | list of indexes: `[0, 2]` | multiple answers (Canvas's own scoring; partial credit is a quiz setting) |
| `numerical` | none | `{value: 4, tolerance: 0.01}` or `{min: 0.97, max: 0.98}` | numerical |
| `true_false` | none | `true` or `false` | true/false |

`tolerance` is absolute: `{value: 2.082, tolerance: 0.001}` accepts 2.081
through 2.083.

## Status

- `draft`: written by the agent and not yet reviewed (every new item)
- `reviewed`: kept by the instructor (set by hand or by `sync_from_canvas.py`)
- `removed`: deleted in review. The item stays in the file so its id is
  never reused, but it is never built, and the validator skips its content
  checks.

`build_qti.py --reviewed-only` packages only `reviewed` items.

## Markdown

`question`, `choices` and `explanation` are Markdown, rendered by
`scripts/mdrender.py` (standard library only):

- **Paragraphs** are separated by a blank line. **Emphasis** uses `*em*`,
  `**strong**`, `~~strike~~`, `^sup^` and `~sub~`.
- **Code:** `inline code`, and fenced blocks with an optional language:
  ```` ```r ````, ```` ```python ````, ```` ```{r} ````, or `~~~`.
- **Math:** `$inline$` and `$$display$$` TeX in standard amsmath (`\frac`,
  `\sum`, `\overline`, `\begin{pmatrix}`, ...).
  A `$` opens math only before a non-space, and closes only after a
  non-space when no digit follows, so `$5 and $20` stays text. Write a
  literal dollar as `\$`.
- **Tables** are pipe tables with an optional alignment row (`:--`, `:-:`,
  `--:`). Cells may hold code and math; a `|` inside `$...$` or backticks
  does not split a cell. They render with a ruled grid, padded cells and a
  shaded header row (inline styles, since Canvas adds none).
- **Lists** use `-`, `*` or `1.`; nested items are indented two or more
  spaces.
- **Images:** `![alt text](figures/name.png)`, with the path relative to the
  YAML file; PNG, JPEG or GIF. Alt text is required.
- **Other blocks:** links, `> blockquotes`, headings and `---` rules.
- **Typography:** outside code and math, quotes become curly, `--` becomes
  an en dash, `---` an em dash and `...` an ellipsis.

What is not supported:

- **Raw HTML.** Only `<br>`, `<sup>`, `<sub>`, `<kbd>`, `<u>`, `<mark>` and
  `<small>` pass through. Anything else is shown as text.
- **Footnotes, definition lists and attributes on blocks.**

**Blank line before a block.** A list, table, blockquote or heading needs a
blank line before it. Without one, a wrapped line that happens to start with
"3." stays text. The validator warns when a line that looks like a list item
follows a text line. A fenced code block may follow text directly.

**Math rendering in Canvas.** Each formula becomes a Canvas equation image
(`/equation_images/<TeX>`), the same form Canvas's own equation editor
produces, rendered by the Canvas server that imports it. Never MathML: New
Quizzes shows MathML as "Unexpected text node". Keep TeX standard: no
`\newcommand`, no packages beyond amsmath.

## YAML pitfalls

- Use block scalars (`|`) for any multi-line text and for anything that
  contains code.
- Quote a one-line string that contains `: `, starts with a backtick, `*`,
  `&`, `!`, `%`, `@`, `[`, `{`, or is `yes`/`no`/`true`/`false`.
- Prefer **single quotes** for choices: backslashes stay literal
  (`'$\lambda = 1$'`). Inside single quotes, write a quote as `''`
  (`'`Error: object ''x'' not found`'`).
- Never put TeX in **double quotes**: YAML treats `\l`, `\T`, ... as escape
  sequences, so the file fails to load or the TeX is corrupted.
- Edit banks with exact-string edits, never multi-line regex replacements,
  which can silently move lines between items. Re-run the validator after
  every edit.
