# Install

The skill is the folder `skills/canvas-quizbank/` in the repository. Chat
apps take it as a zip; coding agents read the folder from their skills
folder. [Install a skill](../install.md) has the full steps for every app
and agent, with updating, removing and troubleshooting; this page is the
short version for this skill.

## What it needs

| where | needs |
|---|---|
| Claude.ai | **Settings → Capabilities → Code execution and file creation** turned on |
| ChatGPT | nothing extra; the skill runs in ChatGPT's code sandbox |
| Gemini | **Gemini Spark** (Google AI Pro or Ultra), which runs the skill's code |
| coding agents | Python 3.9 or newer on your computer; optionally R, and Poppler for PDFs ([details](index.md#requirements)) |

## Chat apps

| app | zip | where to upload |
|---|---|---|
| Claude.ai | [`zip/claude/canvas-quizbank.zip`](https://github.com/hyunminkang/skills/raw/main/zip/claude/canvas-quizbank.zip) | **Customize → Skills → + → Create skill → Upload a skill** ([steps](../install.md#chat-apps)) |
| ChatGPT | [`zip/claude/canvas-quizbank.zip`](https://github.com/hyunminkang/skills/raw/main/zip/claude/canvas-quizbank.zip) | [chatgpt.com/skills](https://chatgpt.com/skills) → **Add** (top right) → **Upload from your computer** ([steps](../install.md#chat-apps)) |
| Gemini | [`zip/gemini/canvas-quizbank.zip`](https://github.com/hyunminkang/skills/raw/main/zip/gemini/canvas-quizbank.zip) | **Settings** (bottom left) → **Skills** → **Upload** icon → drag and drop the zip → **Create**; then use it in Spark ([steps](../install.md#chat-apps)) |

The Gemini zip differs from the other in two ways that Gemini requires:
`SKILL.md` sits at the root of the zip, and files of types Gemini does not
accept get `.txt` appended (the R checks files become `.R.txt`).

## Coding agents

| agent | all projects | one project |
|---|---|---|
| Codex, GitHub Copilot, Cursor and most others | `~/.agents/skills/canvas-quizbank/` | `.agents/skills/canvas-quizbank/` |
| Claude Code | `~/.claude/skills/canvas-quizbank/` | `.claude/skills/canvas-quizbank/` |
| Antigravity CLI | `~/.gemini/config/skills/canvas-quizbank/` | `.agents/skills/canvas-quizbank/` |

To install for all projects in all three (macOS or Linux):

```bash
git clone https://github.com/hyunminkang/skills.git ~/hyunminkang-skills
mkdir -p ~/.agents/skills ~/.claude/skills ~/.gemini/config/skills
ln -s ~/hyunminkang-skills/skills/canvas-quizbank ~/.agents/skills/canvas-quizbank
ln -s ~/hyunminkang-skills/skills/canvas-quizbank ~/.claude/skills/canvas-quizbank
cp -R ~/hyunminkang-skills/skills/canvas-quizbank ~/.gemini/config/skills/
```

Or, with Node.js, for Claude Code, Codex and the other `.agents` agents:

```bash
npx skills add hyunminkang/skills --skill canvas-quizbank -g
```

Then start a new session. For one project, Windows, unzipping without
git, and the folder each agent reads, see
[Install a skill → Coding agents](../install.md#coding-agents).

## Check the install

Ask the agent: *"Build `examples/smoke-test/smoke-test.yaml` from the
canvas-quizbank skill into a QTI zip."* It should run `build_qti.py` and
report 6 items and 1 image. To call the skill by name, type
`/canvas-quizbank` (Claude Code, Claude.ai and most agents),
`$canvas-quizbank` (Codex), or pick it after typing **@** (ChatGPT) or
**/** (Gemini).
