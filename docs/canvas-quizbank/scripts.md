# Scripts

The agent runs these for you, but they also work by hand. They live in
`skills/canvas-quizbank/scripts/` and need only Python 3.9 or newer; PyYAML
is bundled in `scripts/_vendor/` for environments without it. Every script
prints its options with `--help`.

## package_bank.py

The usual last step: validates the bank, builds the Canvas package, checks
it against the YAML, writes the review sheet, and bundles everything else.

```bash
python3 scripts/package_bank.py bank.yaml --out downloads/ --notes notes.md
```

- **Output:** `downloads/bank.qti.zip` (import into Canvas) and
  `downloads/bank-source-and-review.zip`. The second zip is a folder
  `bank/` with the YAML, the review sheet, the checks files, the figures
  the items use, and a README (summary, unverified items, notes, import and
  sync steps). It unzips into a folder whose YAML rebuilds as is.
- **Options:** `--notes FILE` adds Markdown notes to the README;
  `--mode`, `--image-mode` and `--reviewed-only` work as in
  `build_qti.py`.
- Nothing is written if validation or the package check fails.

## extract_material.py

Turns class material into one numbered outline for drafting.

```bash
python3 scripts/extract_material.py lecture.pptx notes.pdf -o work/extracted
```

- **Output:** `work/extracted/outline.md` and `work/extracted/media/<file>/`.
- **Inputs:**

  | type | what is extracted |
  |---|---|
  | `.pptx` | slide titles, bullets with levels, tables, speaker notes, pictures, hidden-slide flags |
  | `.docx` | headings, paragraphs, lists, tables, pictures; equations as plain text |
  | `.ipynb` | Markdown cells; code cells with their language; text and image outputs |
  | `.md`, `.Rmd`, `.qmd` | as is; Marp decks are split into slides, with `<!-- notes -->` listed |
  | `.html` | text, code, lists and tables; KaTeX and MathJax v2 math recovered as `$TeX$` |
  | `.tex` | as is; Beamer decks split by frame |
  | `.pdf` | per-page text (`pdftotext` or `pypdf`); pages with pictures are flagged |

- **Options:**

  | option | effect |
  |---|---|
  | `-o DIR` | output folder (default `extracted`) |
  | `--pages-png [--dpi N]` | render PDF pages to PNG, to crop figures from |
  | `--pdf-images` | save the pictures embedded in a PDF |

## validate_bank.py

Checks banks against the [schema](schema.md), and optionally the built
package against its bank. Exits 1 on any error.

```bash
python3 scripts/validate_bank.py bank.yaml --require-source --report
python3 scripts/validate_bank.py bank.yaml --qti bank.qti.zip
```

| option | effect |
|---|---|
| `--report` | coverage summary: difficulty, types, status, key positions, objectives |
| `--require-source` | a missing `source` is an error (use for new drafts) |
| `--qti ZIP` | open the package and check its manifest, namespaces, images, and every item's type and answer key against the YAML |
| `--reviewed-only` | with `--qti`, for a package built with `--reviewed-only` |
| `--strict` | treat warnings as errors |
| `--verbose` | list every warning instead of grouping them |

## build_qti.py

Builds the Canvas package and, optionally, the review sheet. The bank is
validated first; any error stops the build.

```bash
python3 scripts/build_qti.py bank.yaml -o bank.qti.zip --review-md bank.review.md
```

| option | effect |
|---|---|
| `-o ZIP` | output file (default: `bank.qti.zip` next to the YAML) |
| `--review-md FILE` | also write the answer-keyed review sheet |
| `--mode assessment` | default; for New Quizzes item banks, or a quiz in Classic |
| `--mode objectbank` | a named question bank in Classic Quizzes |
| `--reviewed-only` | package only `status: reviewed` items |
| `--no-id-in-title` | titles without the id prefix (sync then matches by text) |
| `--image-mode inline` | embed figures as `data:` URIs instead of bundling files |

## sync_from_canvas.py

Records a review done in Canvas: kept items become `reviewed`, the others
`removed`. It runs as a dry run unless `--write` is given.

```bash
python3 scripts/sync_from_canvas.py bank.yaml --export canvas-export.zip
python3 scripts/sync_from_canvas.py bank.yaml --kept-ids kept.txt --write
```

- **`--export`:** any zip Canvas produces (a QTI quiz export, or a Classic
  `.imscc` course export); the option can be repeated.
- **`--kept-ids`:** a text file with one id or one Canvas title per line.
- **Matching:** items are matched by the id at the start of their title,
  and by question text when a title has no id.
- **Reported:** items added in Canvas and items whose text was edited
  there.
- **With `--write`:** only `status:` lines change and a `.bak` copy is kept.
  The file is re-read to confirm that nothing else changed; if anything
  did, the original is restored.

## mdrender.py

The Markdown and math renderer behind `build_qti.py`, using only the
standard library. The supported Markdown is listed in the
[schema](schema.md#markdown). `python3 scripts/mdrender.py < item.md`
prints the HTML Canvas will receive.
