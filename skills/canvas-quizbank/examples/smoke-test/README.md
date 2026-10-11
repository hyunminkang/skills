# Smoke test: one Canvas import

Six items that exercise every question type and display feature. Import them
once into a sandbox course to confirm that the package format works on your
Canvas instance.

## Files

The skill holds only the source (`smoke-test.yaml`, `figures/`, the checks
file and the review sheet). Skill zips cannot contain zips, so the
ready-made packages are in the repository's `samples/canvas-quizbank/`:

- `smoke-test.qti.zip`: default build (`assessment` mode, images bundled)
- `smoke-test.objectbank.qti.zip`: `objectbank` mode, for Classic Quizzes
  question banks
- `smoke-test.inline-images.qti.zip`: images embedded as `data:` URIs, a
  fallback if bundled images do not show

Or ask the agent to build the smoke test, or build it yourself:

```
python3 ../../scripts/build_qti.py smoke-test.yaml -o <out>/smoke-test.qti.zip
python3 ../../scripts/build_qti.py smoke-test.yaml -o <out>/smoke-test.objectbank.qti.zip --mode objectbank
python3 ../../scripts/build_qti.py smoke-test.yaml -o <out>/smoke-test.inline-images.qti.zip --image-mode inline
```

## Import

- **New Quizzes:** open **Item Banks**, choose **+ Bank** to create a
  bank, open it, choose **⋮ → Import Content**, and upload
  `smoke-test.qti.zip`.
- **Classic Quizzes:** go to **Settings → Import Course Content**, choose
  **QTI .zip file**, and upload `smoke-test.objectbank.qti.zip` (for a
  question bank) or `smoke-test.qti.zip` (for a quiz).

## What to check

| item | type | look for |
|---|---|---|
| st-001 | multiple choice | display formula with a fraction and a sum; R and Python code blocks in monospace; choices rendered as math |
| st-002 | multiple answers | checkboxes, not radio buttons; math in each choice; choosing A and B scores full marks |
| st-003 | numerical | an answer box; 2.081, 2.082 and 2.083 score, 2.08 does not |
| st-004 | numerical (range) | any value from 0.97 to 0.98 scores |
| st-005 | true/false | two options, True and False; False scores |
| st-006 | multiple choice | the histogram shows (not a broken image); a two-row table with a ruled grid and a shaded header; math in the table |

On every item:

- The title starts with the id (`st-001 · ...`).
- After answering, the feedback shows the explanation and the source line.

If an image is broken, re-import with `smoke-test.inline-images.qti.zip`, then
build your banks with `--image-mode inline`. Record what worked in
`references/canvas.md` under "Verified in Canvas".
