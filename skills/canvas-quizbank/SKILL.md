---
name: canvas-quizbank
license: Apache-2.0
description: Create Canvas quiz item banks (QTI .zip) from class material such as slides, notes, PDF or Word, with verified questions using math, code and figures. Also builds YAML banks and syncs Canvas reviews.
---

# Canvas quiz bank from class material

You turn class material into a bank of quiz items that an instructor
imports into Canvas, reviews there, and trims. The bank is written to be
trimmed: draft more items than needed, all marked `draft`.

## Outputs

The instructor gets **exactly two downloads** (step 9):

| download | what it is |
|---|---|
| `<bank>.qti.zip` | **import this into Canvas** (New Quizzes item bank or Classic) |
| `<bank>-source-and-review.zip` | everything else, in a folder `<bank>/`: the YAML (source of truth for later edits and syncs), the answer-keyed review sheet, the checks files, the figures, a README |

Your work folder holds the same files loose: `<bank>.yaml`,
`<bank>.review.md`, `<bank>.checks.R` / `.py`, `figures/`. In a chat,
offer only the two downloads, not loose files. Never upload, publish or
share a bank anywhere unless the instructor asks for that specific step.

## Setup

- `SKILL_DIR` is the folder that contains this file. Run the scripts as
  `python3 SKILL_DIR/scripts/<script>.py`. They need Python 3.9+ and nothing
  else; a copy of PyYAML is bundled for sandboxes without it.
- Work folder (`<work>`): if the instructor names a folder, use it.
  Otherwise use `quizbank/<bank-name>/` under the working directory, in a
  coding agent and in a chat sandbox alike. The two downloads are written
  to `<out>`: the chat's download folder (step 9), or `<work>` in a coding
  agent. Never write into `SKILL_DIR`.
- Never modify the skill's scripts or copy them into the deliverables. If
  the request needs something they do not build (a short-answer, essay or
  matching question, for example), say so before drafting and offer the
  closest supported type.
- Read `references/authoring-guide.md` and `references/schema.md` before
  writing any item. Skim `examples/advanced-r-function-factories/function-factories.yaml`
  for the house style and `examples/rejected-patterns.md` for what reviewers
  reject.

## Pick the entry point

| the instructor... | do |
|---|---|
| gives material and wants questions | **A. New bank**, all steps below |
| gives a YAML bank (or a `-source-and-review.zip`) and wants a Canvas file | steps 7-9 only |
| wants items added, replaced or fixed in an existing bank | **C. Revise** |
| has reviewed the bank in Canvas | **D. Sync** |

When the instructor brings back a `<bank>-source-and-review.zip`, unzip it
into `<work>` and work on the YAML inside; it builds as is.

## A. New bank

**1. Profile.** Look for a course profile (`quizbank_profile.yaml` near the
material, or pasted in the chat; format in `references/profile.md`). It
overrides the defaults; the instructor's request overrides both.

**2. Extract.** Run

```
python3 SKILL_DIR/scripts/extract_material.py <inputs...> -o <work>/extracted [--pages-png]
```

Read `extracted/outline.md` in full. It numbers every slide, page or cell
and lists speaker notes and images in place. PDF pages marked
`[N picture(s) not in the text: view the page]` hold diagrams, or code and
formulas shown as images: view those pages directly, as you would a PDF
whose text is thin or missing (scanned). Options: `--pages-png` (with
`--dpi`) renders PDF pages to crop figures from; `--pdf-images` saves the
pictures embedded in a PDF. Older `.ppt` and `.doc` files must be
converted to `.pptx`/`.docx` or PDF first.

**3. Intake.** Ask, in **one** message, only what neither the request nor
the profile answers (at most four questions, each with your suggested
default):

- How many items should be kept? (default 50, so draft about 65)
- Which code languages may items use? (default: those in the material)
- Who is the audience? (level and background)
- Which sections should be included or skipped? (default: all)

If the instructor asks for other question types, confirm which. If they say
"just build it" or similar, skip the intake and the plan and use the
defaults.

**4. Coverage plan.** Show the one-screen plan from
`references/authoring-guide.md` §6: sections with their source ranges,
objectives, item counts, difficulty mix, figures, and what is not covered.
Wait for an OK or edits.

**5. Draft** section by section into `<work>/<bank>.yaml` (schema in
`references/schema.md`), following the ten rules (summary below). Every item
needs `status: draft`, a `source` naming its slide, page or section, and
ids of the form prefix + 3 digits (`w05-001`). Without a profile, name the
bank after the material's topic in kebab-case (`functionals`) and take a
short id prefix from it (`fun-`). For banks over about 30 items, run the
validator (step 7) after each section to catch YAML mistakes early.

**6. Verify** (`references/authoring-guide.md` §7, which has the
`check()` helper and the file layout). Run every snippet as printed and
recompute every number. Keep that code in `<work>/<bank>.checks.R` and/or
`.py`, one isolated section per item id. Set
`verified: run`, or `verified: no` with a `verify_note`. Never check R code
by translating it to Python. Draw figures into `<work>/figures/` with
required alt text (§8).

**7. Validate.**

```
python3 SKILL_DIR/scripts/validate_bank.py <work>/<bank>.yaml --require-source --report
```

Fix every error, and read the warnings and the report: difficulty mix,
types, key positions, "key clearly the longest option", objectives. Then
run the self-review checklist (`authoring-guide.md` §9) over the whole bank.

**8. Package.** Write your hand-over notes (coverage table, substitutions,
judgment calls) to `<work>/notes.md`, then run

```
python3 SKILL_DIR/scripts/package_bank.py <work>/<bank>.yaml --out <out> --notes <work>/notes.md
```

It validates the bank, builds `<out>/<bank>.qti.zip`, checks the package
against the YAML, writes `<work>/<bank>.review.md`, and zips everything else
(YAML, review sheet, checks, the figures the items use, a README with your
notes) into `<out>/<bank>-source-and-review.zip`. Nothing is written if a
check fails. Add `--mode objectbank` for a Classic Quizzes question bank
(see `references/canvas.md`).

**9. Hand over the two downloads.** Make both files downloadable the way
the host expects:

| where you run | `<out>` | how the instructor gets the files |
|---|---|---|
| Claude.ai | `/mnt/user-data/outputs/` | files there appear as downloads; if a tool for presenting files exists (e.g. `present_files`), call it with both paths |
| ChatGPT | `/mnt/data/` | link each file in your reply: `[<bank>.qti.zip](sandbox:/mnt/data/<bank>.qti.zip)` |
| Gemini | the code's working directory | return both files as downloadable files from the code run, so they show as download chips |
| Claude Code, Codex, Antigravity CLI, other coding agents | `<work>` | give both paths; the loose files are in `<work>` too |

If the host cannot offer a file, say so plainly and name the file and its
path; never claim a download that is not there. Then reply in this shape:

```
Download these two files:
1. <bank>.qti.zip: import into Canvas (Item Banks → + Bank → open it →
   ⋮ → Import Content). N items: <types>.
2. <bank>-source-and-review.zip: the review sheet with answers marked, the
   YAML source, checks and figures. Keep it for edits and for syncing after
   your review.
```

After that, add a short summary:

- items per section, difficulty and type
- which items are `verified: no`, and why
- any requested feature you substituted
- the next step: delete unfitting items in Canvas, then bring back the
  source-and-review zip (or its YAML) with a Canvas export or the list of
  kept titles, to sync the YAML

If the bank uses images or non-multiple-choice types and the instructor has
not imported the skill's packages before, suggest a smoke test first: build
`SKILL_DIR/examples/smoke-test/smoke-test.yaml` with `build_qti.py -o
<out>/smoke-test.qti.zip`, offer it as a third download, and point to
`examples/smoke-test/README.md` for what to check. If
there was no profile and the request stated lasting preferences (languages,
audience, size), offer to save them as `quizbank_profile.yaml`; write it
only if the instructor agrees.

## C. Revise or extend a bank

- Read the bank, its checks file and its profile first. Keep every
  existing id. New items continue after the highest existing number,
  counting `removed` items; never reuse an id.
- Edit with exact-string edits, never multi-line regex replacements.
- Re-verify changed items, update their checks sections, then run steps 7
  to 9 (validate, package, hand over the two downloads).
- Fix only what was asked. Do not restyle approved (`reviewed`) items to
  newer rules unless asked.

## D. Sync after review in Canvas

```
python3 SKILL_DIR/scripts/sync_from_canvas.py <bank>.yaml --export <canvas-export>.zip
python3 SKILL_DIR/scripts/sync_from_canvas.py <bank>.yaml --kept-ids kept.txt   # ids or titles, one per line
```

Show the dry run (kept → `reviewed`, missing → `removed`, items edited or
added in Canvas). Then rerun with `--write`. The script edits only `status:`
lines, keeps a `.bak`, and restores the file if anything else changed.
Offer to copy Canvas edits into the YAML. Then package again (step 8, with
`--reviewed-only` if a package of only the kept items is wanted) and hand
over the two downloads (step 9), so the instructor keeps the updated YAML.

## The ten rules (details and examples in the authoring guide)

1. Test the core idea (how it works, how cost grows, numerical behavior),
   never API trivia.
2. Answerable by someone who never saw these slides: no lecture-only names
   or notation; define every symbol.
3. Numbers are fine, but arithmetic takes at most 1-2 mental steps.
4. Mix styles: symbolic Θ(), small concrete examples, code output,
   realistic sizes.
5. One clear question per stem; state any library behavior it depends on.
6. Options parallel and similar in length, key not the longest, no
   "because" clauses, values over prose.
7. Complete code that runs as printed; every number recomputed.
8. No cross-item hints; each example used about once; even coverage; no
   references to homework, terms or internal files.
9. Overdraft about 1.3×; difficulty about ⅓ easy, ½ medium, the rest hard;
   all `draft`; keys spread.
10. Explanations say why the key is right and what mistake leads to each
    tempting distractor.

## Troubleshooting

- **YAML error with a line number:** usually TeX in double quotes or an
  unquoted `: `. Use `|` blocks and single quotes (`references/schema.md`,
  "YAML pitfalls").
- **Canvas says "Unsupported content package":** rebuild with these scripts
  and run `validate_bank.py --qti`. Never post-process the XML.
- **Images broken in Canvas:** rebuild with `--image-mode inline`.
- **A language cannot be run here** (often R in a chat sandbox): mark the
  item `verified: no` with that reason and list it in the hand-over; the
  instructor can run the checks file locally.
- **A package is missing and cannot be installed:** rewrite the item with
  base functions if the idea does not depend on the package; otherwise
  mark it `verified: no` with the reason.
