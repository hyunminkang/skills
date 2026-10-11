# Development

## Repository layout

```
skills/<name>/             one folder per skill: SKILL.md + scripts/ references/ examples/
zip/claude/<name>.zip      generated: skill folder inside the zip (Claude.ai, ChatGPT)
zip/gemini/<name>.zip      generated: SKILL.md at the zip root (Gemini)
samples/<name>/            ready-made outputs (e.g. Canvas QTI packages) for people to try
samples/<name>/<example>/  end-to-end runs: input material, prompt, and each platform's downloads
docs/                      this site; reference pages include the skills' own files
tests/                     standard-library unittest suites
tools/build_zips.py        checks, tests and zips every skill
mkdocs.yml                 site configuration
LICENSE, NOTICE            Apache 2.0 and third-party attributions
```

## After changing a skill

```bash
python3 -m unittest discover -s tests     # the tests alone
python3 tools/build_zips.py               # checks + tests, then rewrites zip/
```

`build_zips.py` refuses to write zips when a check or test fails. It checks
that:

- `SKILL.md` has frontmatter with a `name` equal to the folder name
  (lowercase letters, digits and hyphens, at most 64 characters);
- the `description` has 1–200 characters (Claude.ai's upload limit; the
  open Agent Skills spec allows 1,024, but every host must accept the zip);
- no skill folder contains a `.zip` (Claude.ai rejects a skill zip that
  contains another zip, so built packages go to `samples/`);
- every file is a type Gemini accepts, or text that can be renamed with a
  `.txt` suffix in the Gemini zip (Gemini rejects other types, and the
  build stops on an unsupported binary);
- the tests in `tests/` pass.

The zips are deterministic (sorted entries, fixed timestamps), so they
change in git only when the skill does. Commit them with the change.

## Adding a skill

1. Create `skills/<name>/SKILL.md` with `name`, `description` (what it does
   and when to use it, in the user's words, at most 200 characters) and
   `license: Apache-2.0`.
   - Keep `SKILL.md` short; put details in `references/`.
   - Put scripts in `scripts/`, standard library only where possible:
     chat sandboxes cannot install packages.
   - Put worked examples in `examples/`.
2. Add `tests/test_<name>.py`.
3. Add a row to the skills table in `README.md` and `docs/index.md`, and a
   section to `docs/` and `mkdocs.yml`.
4. Run `python3 tools/build_zips.py`.

## Documentation

```bash
pip install -r requirements-docs.txt
mkdocs serve          # preview at http://127.0.0.1:8000
mkdocs build --strict # what a deploy would run
```

Reference pages include the skill files with
`--8<-- "skills/<name>/references/<file>.md"` (pymdownx.snippets). Edit the
skill file, not the page, so the documentation and the agent's instructions
stay identical.

## canvas-quizbank notes

- `scripts/mdrender.py` replaces Pandoc. Before it shipped, it was compared
  with Pandoc on 3,408 text fields from about 570 real items: the visible
  text, math and structure matched everywhere except choices that start
  with "(ii)" or "(a)". Pandoc turns those into one-item numbered lists;
  this renderer keeps the text as written.
- `references/canvas.md` has a "Verified in Canvas" table. Update it when an
  import confirms or breaks a feature.
