# Agent skills

Agent skills for teaching, by Hyun Min Kang.

- **Format:** each skill is a folder with a `SKILL.md` in the open Agent
  Skills format, plus the scripts, references and examples it uses.
- **Hosts:** the same folder works in Claude.ai, ChatGPT, Gemini, Claude
  Code, Codex, Antigravity CLI and other agents that read Agent Skills.
- **Downloads:** upload-ready zips are in the repository's
  [`zip/`](https://github.com/hyunminkang/skills/tree/main/zip) folder.

## Skills

| skill | what it does |
|---|---|
| [canvas-quizbank](canvas-quizbank/index.md) | Turns class material into a Canvas quiz item bank: a QTI `.zip` with math, code, tables and figures, plus a YAML source and an answer-keyed review sheet. Items are verified by running their code. See the [worked example](canvas-quizbank/example-hwe.md) and [how to import](canvas-quizbank/import.md). |

## Install

| where | what to do |
|---|---|
| Claude.ai | upload `zip/claude/<skill>.zip` at **Customize → Skills** (code execution on) |
| ChatGPT | upload `zip/claude/<skill>.zip` at [chatgpt.com/skills](https://chatgpt.com/skills) → **Add** |
| Gemini | upload `zip/gemini/<skill>.zip` at **Settings → Skills**, then use it in Gemini Spark |
| Claude Code | put the folder `skills/<skill>/` in `~/.claude/skills/` |
| Codex, GitHub Copilot, Cursor and most other agents | put the folder `skills/<skill>/` in `~/.agents/skills/` |
| Antigravity CLI | put the folder `skills/<skill>/` in `~/.gemini/config/skills/` |

[Install a skill](install.md) has step-by-step instructions for each app
and agent.

## License

Apache License 2.0. Third-party components and attributions are listed in
the repository's
[NOTICE](https://github.com/hyunminkang/skills/blob/main/NOTICE) file.
