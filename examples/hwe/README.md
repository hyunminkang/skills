# Example: Hardy-Weinberg equilibrium, on three chat platforms

The same lecture and the same request, run with the canvas-quizbank skill on
Claude.ai, ChatGPT and Gemini. Each platform handed back the two downloads
the skill produces, and every bank passes the skill's validator and package
check.

## Input

- `input/666.02.pdf`: *Lecture 02, Hardy Weinberg Equilibrium*, from
  BIOSTAT 666 "Models in Human Genetics" by Gonçalo Abecasis (36 slides),
  publicly posted at <https://csg.sph.umich.edu/abecasis/class/666.02.pdf>
  ([course notes](https://csg.sph.umich.edu/abecasis/class/index.html)).
- `input/prompt.txt`: the request, given with the PDF:

  > /canvas-quizbank draft ~25 Canvas quiz questions from my lecture slides
  > for me to review. Include at least one true/false questions, one
  > multiple-answer questions, one short answer (numeric answers) questions
  > while making most questions as MCQ. Include at least one image, multiple
  > mathematical equations, and multiple code blocks (mixture of R and
  > python) in the quiz problems.

## Output

Each folder under `output/` holds what the platform offered for download.

| platform | items | types | verified by running code | code blocks | figures |
|---|---|---|---|---|---|
| Claude.ai (Opus 5.5), [`output/claude-opus-5-5/`](output/claude-opus-5-5/) | 26 | 23 multiple choice, 1 multiple answers, 1 numerical, 1 true/false | 24 (2 conceptual) | 2 R, 3 Python | 2 |
| ChatGPT, [`output/chatgpt-sol-6-1/`](output/chatgpt-sol-6-1/) | 25 | 20 multiple choice, 2 multiple answers, 2 numerical, 1 true/false | 14 (8 conceptual, 3 R not available) | 3 R, 5 Python | 2 |
| Gemini (Spark, Flash 3.8), [`output/gemini-spark-flash-3-8/`](output/gemini-spark-flash-3-8/) | 25 | 20 multiple choice, 2 multiple answers, 2 numerical, 1 true/false | 22 (3 R not available) | 2 R, 3 Python | 2 |

In every folder:

- `<bank>.qti.zip`: the file to import into Canvas.
- `<bank>-source-and-review.zip`: one folder holding:
  - the YAML (source of truth)
  - the answer-keyed review sheet
  - the R and Python checks files
  - the figures
  - a README with the summary, the unverified items and the platform's
    notes

Claude.ai also offered `smoke-test.qti.zip`, the skill's six-item test bank,
because this was the first bank with images and several question types.

Notes:

- **Unverified items.** "R not available" means the platform's sandbox had
  no R. Those items are marked `verified: no`, and their R checks file is
  included so the instructor can run it locally.
- **ChatGPT's extra file.** Its bundle also holds an HTML review page.

## Importing into Canvas

See [Importing into Canvas](https://hyunminkang.github.io/skills/canvas-quizbank/import/)
for the steps with screenshots. This is the Claude.ai bank after import:

![The imported bank in Canvas New Quizzes, showing item hwe-026 with rendered math: the two-sided exact HWE p-value for a single copy of the minor allele, with options 1/(2N), 1/N, 0.5 and 1.](../../docs/canvas-quizbank/images/canvas-import-3-imported-items.png)

## Try it yourself

From the repository root, check any output against the skill's rules:

```bash
mkdir -p /tmp/hwe && unzip -o examples/hwe/output/claude-opus-5-5/hardy-weinberg-source-and-review.zip -d /tmp/hwe
python3 skills/canvas-quizbank/scripts/validate_bank.py /tmp/hwe/hardy-weinberg/hardy-weinberg.yaml \
  --report --qti examples/hwe/output/claude-opus-5-5/hardy-weinberg.qti.zip
```
