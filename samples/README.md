# Ready-made Canvas packages

QTI packages built from the skills' examples, to import into Canvas
directly. They live here rather than inside the skills because a skill zip
may not contain other zips (Claude.ai rejects it).

## canvas-quizbank

| file | built from | use |
|---|---|---|
| `smoke-test.qti.zip` | `examples/smoke-test/smoke-test.yaml` | first import into a sandbox course; New Quizzes item bank or a Classic quiz |
| `smoke-test.objectbank.qti.zip` | same, `--mode objectbank` | a Classic Quizzes question bank |
| `smoke-test.inline-images.qti.zip` | same, `--image-mode inline` | fallback if bundled images do not show |
| `function-factories.qti.zip` | `examples/advanced-r-function-factories/function-factories.yaml` | the example bank |

What to check after importing:
`skills/canvas-quizbank/examples/smoke-test/README.md`.

To rebuild after changing an example (from the repository root):

```bash
S=skills/canvas-quizbank; E=$S/examples; O=samples/canvas-quizbank
python3 $S/scripts/build_qti.py $E/smoke-test/smoke-test.yaml -o $O/smoke-test.qti.zip
python3 $S/scripts/build_qti.py $E/smoke-test/smoke-test.yaml -o $O/smoke-test.objectbank.qti.zip --mode objectbank
python3 $S/scripts/build_qti.py $E/smoke-test/smoke-test.yaml -o $O/smoke-test.inline-images.qti.zip --image-mode inline
python3 $S/scripts/build_qti.py $E/advanced-r-function-factories/function-factories.yaml -o $O/function-factories.qti.zip
```

The tests check that each package still matches its YAML.
