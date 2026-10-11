# Agent skills

Agent skills for teaching, by Hyun Min Kang. Each skill is a folder with a
`SKILL.md` in the open Agent Skills format. The same folder works in
Claude.ai, ChatGPT, Gemini, Claude Code, Codex, Antigravity CLI and other
agents that read Agent Skills.

**Documentation:** <https://hyunminkang.github.io/skills/> (source in
[`docs/`](docs/))

## Skills

| skill | what it does | download |
|---|---|---|
| [canvas-quizbank](skills/canvas-quizbank/) | Turns class material (slides, notes, PDF, PowerPoint, Word, notebooks, Markdown, LaTeX) into a Canvas quiz item bank. Hands back two downloads: a QTI `.zip` for Canvas (math, code, tables and figures), and one zip with the YAML source, an answer-keyed review sheet, the checks and figures. Drafts multiple choice by default, and multiple-answer, numerical and true/false items on request. Verifies items by running their code, and syncs the YAML after you review the bank in Canvas. | [Claude.ai, ChatGPT](zip/claude/canvas-quizbank.zip) · [Gemini](zip/gemini/canvas-quizbank.zip) |

## See it in action

[`examples/hwe/`](examples/hwe/) runs canvas-quizbank on one public
genetics lecture (Hardy-Weinberg equilibrium) in Claude.ai, ChatGPT and
Gemini, with the prompt and each platform's downloads. After import, the
items look like this in Canvas:

![An imported item in Canvas New Quizzes with rendered math: the two-sided exact HWE p-value for a single copy of the minor allele.](docs/canvas-quizbank/images/canvas-import-3-imported-items.png)

Step-by-step import instructions with screenshots:
[Importing into Canvas](https://hyunminkang.github.io/skills/canvas-quizbank/import/).

## Install a skill

Chat apps take a zip; coding agents read the skill folder from their
skills folder.

| where | how |
|---|---|
| Claude.ai | turn on **Settings → Capabilities → Code execution and file creation**; then **Customize → Skills → + → Create skill → Upload a skill** with the zip from [`zip/claude/`](zip/claude/) |
| ChatGPT | [chatgpt.com/skills](https://chatgpt.com/skills) → **Add** (top right) → **Upload from your computer** with the zip from [`zip/claude/`](zip/claude/) |
| Gemini | **Settings** (bottom left) → **Skills** → **Upload** icon → drag and drop the zip from [`zip/gemini/`](zip/gemini/) → **Create**; use the skill in **Gemini Spark** |
| Claude Code | put `skills/<name>/` in `~/.claude/skills/` (all projects) or `.claude/skills/` (one project) |
| Codex, GitHub Copilot, Cursor, OpenCode and most other agents | put `skills/<name>/` in `~/.agents/skills/` (all projects) or `.agents/skills/` (one project) |
| Antigravity CLI | put `skills/<name>/` in `~/.gemini/config/skills/` (all projects) or `.agents/skills/` (one project) |

For example, to install canvas-quizbank for Claude Code and the
`.agents` agents from a clone:

```bash
git clone https://github.com/hyunminkang/skills.git ~/hyunminkang-skills
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s ~/hyunminkang-skills/skills/canvas-quizbank ~/.agents/skills/canvas-quizbank
ln -s ~/hyunminkang-skills/skills/canvas-quizbank ~/.claude/skills/canvas-quizbank
```

The [install guide](https://hyunminkang.github.io/skills/install/) has
step-by-step instructions for each app and agent, Windows commands,
`npx skills`, updating, removing and troubleshooting.

## Repository layout

```
skills/<name>/       the skills: SKILL.md plus scripts, references, examples
zip/claude/<name>.zip   upload for Claude.ai, ChatGPT (skill folder inside the zip)
zip/gemini/<name>.zip   upload for Gemini (SKILL.md at the zip root)
samples/<name>/      ready-made outputs to try (e.g. Canvas packages); never inside a skill
examples/<example>/  end-to-end runs: input, prompt, and what each platform handed back
docs/                documentation site (MkDocs Material), built with mkdocs.yml
tests/               standard-library tests: python3 -m unittest discover -s tests
tools/build_zips.py  checks every skill, runs the tests, rebuilds zip/
```

After editing a skill, run `python3 tools/build_zips.py` and commit the
updated zips with it. To preview the docs:

```
pip install -r requirements-docs.txt
mkdocs serve
```

## License

Apache License 2.0; see [LICENSE](LICENSE). Third-party components and
attributions are listed in [NOTICE](NOTICE).
