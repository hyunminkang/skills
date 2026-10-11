# Canvas: import, review, export

## Which package to build

| goal | build with | import path |
|---|---|---|
| New Quizzes item bank (most courses) | `--mode assessment` (default) | **Item Banks** (course navigation, or Manage Item Banks from a New Quiz) → **+ Bank** → name it → open the bank → **⋮ → Import Content** → upload the zip |
| Classic Quizzes question bank | `--mode objectbank` | **Course Settings → Import Course Content → QTI .zip file** → the items arrive as a question bank named after `title` |
| Classic quiz | `--mode assessment` | the same Settings import path; arrives as an unpublished quiz |

Canvas menus move between releases. If a label differs, look for "Import
Content" on the item bank, or use the course-level QTI import.

To give the bank a clear name in Canvas, set `title:` in the YAML before
building.

## What the instructor sees

- **Title:** each item is titled `<id> · <title>` (e.g. `ff-004 · Two
  counters`), so items can be found, discussed and synced by id.
  `--no-id-in-title` turns this off.
- **Question and choices:** the rendered Markdown. Math appears as Canvas
  equation images and code in monospace blocks.
- **Feedback:** the explanation, plus a final line "Source: ...". Students
  see it after submitting, as the quiz settings allow.
- **Options** are shuffled per student when `shuffle_answers: true`.

## The review loop

1. Import the package and read the items in Canvas; delete the ones that
   do not fit. The review sheet (`<bank>.review.md`, answers marked ✅,
   unverified items listed first) is the same content offline.
2. Export what is left:
   - a New Quizzes quiz that uses the bank: the quiz's menu → **Export**
     (QTI)
   - Classic: **Settings → Export Course Content** (choose the quiz or
     bank), which downloads an `.imscc`
   - if no export is available: copy the remaining item titles (each
     starts with its id) into a text file, one per line
3. Run `sync_from_canvas.py BANK.yaml --export export.zip` (or
   `--kept-ids kept.txt`). Read the dry run, then add `--write`. Kept items
   become `reviewed`, deleted ones `removed`. Items edited in Canvas are
   listed so the edit can be copied into the YAML by hand.
4. Rebuild with `--reviewed-only` when a clean, reviewed-only package is
   needed.

## Package format (what Canvas enforces)

`build_qti.py` writes `imsmanifest.xml`, `assessment.xml` and `images/*`.
These details each cost a failed import; `validate_bank.py --qti` checks
them all:

- **Bare default namespaces.** `<manifest xmlns="...">`, never
  `<ns0:manifest>`. Canvas finds the QTI resource with CSS selectors that do
  not match prefixed elements and reports only "Unsupported content
  package".
- **Equation images, never MathML.** New Quizzes renders MathML as
  "Unexpected text node: '<latex>'".
- **Feedback before scoring.** The `continue="Yes"` feedback condition comes
  before the `continue="No"` scoring condition. Otherwise students who
  answer correctly never see the explanation.
- **Images** go under `images/`, each declared as a `webcontent` resource
  in the manifest, and are referenced as
  `%24IMS-CC-FILEBASE%24/images/<name>`, the layout Canvas's own exports
  use. Canvas copies them into the course files on import.
  `--image-mode inline` embeds `data:` URIs instead, as a fallback.

## Verified in Canvas

| feature | status |
|---|---|
| multiple choice, math, code blocks (`assessment` mode) | in use: built by the predecessor of these scripts and imported into a live course |
| multiple answers, numerical, true/false (`assessment` mode) | confirmed 2026-10-10: `examples/smoke-test` imported and checked |
| bundled images (`assessment` mode) | confirmed 2026-10-10 with the smoke test |
| tables | rendered 2026-10-10 as unruled, cramped text; now emitted with inline borders, padding and a shaded header (`border="1"` as a fallback); re-check after the next import |
| `objectbank` mode | built to Canvas's documented shape; not yet confirmed |

Update this table when an import confirms or breaks a feature (date, what
was checked).
