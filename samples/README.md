# Samples

Ready-made outputs to try: QTI packages built from the skills' examples, to
import into Canvas directly, and end-to-end runs of a skill on the chat
platforms. They live here rather than inside the skills because a skill zip
may not contain other zips (Claude.ai rejects it), and because they are for
people to look at, not for the agent to read.

## canvas-quizbank

| file | built from | use |
|---|---|---|
| `smoke-test.qti.zip` | `examples/smoke-test/smoke-test.yaml` | first import into a sandbox course; New Quizzes item bank or a Classic quiz |
| `smoke-test.objectbank.qti.zip` | same, `--mode objectbank` | a Classic Quizzes question bank |
| `smoke-test.inline-images.qti.zip` | same, `--image-mode inline` | fallback if bundled images do not show |
| `function-factories.qti.zip` | `examples/advanced-r-function-factories/function-factories.yaml` | the example bank |

What to check after importing:
`skills/canvas-quizbank/examples/smoke-test/README.md`.

### Worked example: `hwe/`

One public genetics lecture (Hardy-Weinberg equilibrium) and one request,
run with the skill on Claude.ai, ChatGPT and Gemini:

| folder | what it holds |
|---|---|
| `hwe/input/` | the lecture PDF and the prompt |
| `hwe/output/<platform>/` | the two downloads each platform handed back |

See [`canvas-quizbank/hwe/README.md`](canvas-quizbank/hwe/README.md) for
the results and how to check them. The lecture PDF belongs to its author
and is not covered by this repository's license; see `NOTICE`.

To rebuild after changing an example (from the repository root):

```bash
S=skills/canvas-quizbank; E=$S/examples; O=samples/canvas-quizbank
python3 $S/scripts/build_qti.py $E/smoke-test/smoke-test.yaml -o $O/smoke-test.qti.zip
python3 $S/scripts/build_qti.py $E/smoke-test/smoke-test.yaml -o $O/smoke-test.objectbank.qti.zip --mode objectbank
python3 $S/scripts/build_qti.py $E/smoke-test/smoke-test.yaml -o $O/smoke-test.inline-images.qti.zip --image-mode inline
python3 $S/scripts/build_qti.py $E/advanced-r-function-factories/function-factories.yaml -o $O/function-factories.qti.zip
```

The tests check that each package still matches its YAML.
