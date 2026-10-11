# canvas-quizbank

Turns class material into a quiz item bank that an instructor imports into
Canvas, reviews there, and trims.

**Input:** lecture slides, notes, PDF, PowerPoint, Word, Jupyter notebooks,
Markdown (including Marp decks), LaTeX or HTML.

**Output:** two downloads.

| download | what it is |
|---|---|
| `<bank>.qti.zip` | the file to import into Canvas (New Quizzes item bank or Classic) |
| `<bank>-source-and-review.zip` | everything else, in one folder (below) |

The second zip holds:

| file | what it is |
|---|---|
| `<bank>.yaml` | the source of truth; every later build and sync starts here |
| `<bank>.review.md` | answer-keyed review sheet; unverified items listed first |
| `<bank>.checks.R` / `.py` | the code that verified each item |
| `figures/` | PNG figures used by items, if any |
| `README.md` | summary, unverified items, the agent's notes, import and sync steps |

Keep that zip: give it back to the agent (with a Canvas export) to sync
after your review, or to revise the bank later.

**See it in action:** [a worked example](example-hwe.md) (one genetics
lecture, run on Claude.ai, ChatGPT and Gemini) and
[importing into Canvas](import.md), step by step with screenshots.

## What it does

- **Reads the material** and numbers every slide, page or cell, so each
  item records where it comes from.
- **Asks only what it needs** (number of items, code languages, audience,
  sections), then shows a one-screen coverage plan before drafting. Saying
  "just build it" skips both.
- **Drafts more items than you need**, all marked `draft`, so you can trim.
  Items are multiple choice by default; multiple-answer, numerical and
  true/false items are drafted on request.
- **Writes math and code as Canvas expects:**
  - LaTeX becomes Canvas equation images, the form Canvas's own equation
    editor produces.
  - Code blocks, ruled tables and figures with required alt text are kept.
- **Verifies items by running them:** every snippet runs as printed, every
  number is recomputed, and the code is kept beside the bank.
- **Learns from your review:** after you delete items in Canvas, it reads a
  Canvas export (or a list of kept ids) and marks the YAML: kept items
  `reviewed`, deleted ones `removed`.

The authoring rules come from several rounds of instructor review of real
banks; see the [authoring guide](authoring-guide.md). A
[course profile](profiles.md) adds a course's own conventions.

## Status in Canvas

| feature | status |
|---|---|
| multiple choice with math and code | in use in a live course |
| multiple answers, numerical, true/false | confirmed by importing the smoke-test bank (2026-10-10) |
| bundled images | confirmed with the smoke-test bank (2026-10-10) |
| ruled tables | styled after the first import; re-check pending |
| Classic `objectbank` mode | built to Canvas's documented shape; not yet confirmed |

Before your first real bank, import the
[smoke-test bank](examples.md#smoke-test) into a sandbox course.

## Requirements

Python 3.9 or newer; nothing else is required (PyYAML is bundled). Optional:

- R or Python, to verify items that show code in that language
- Poppler (`pdftotext`, `pdftoppm`, `pdfimages`), for PDF text, page images
  and picture detection
