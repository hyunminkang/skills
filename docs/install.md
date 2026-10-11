# Install a skill

Every skill in this repository is a folder, `skills/<name>/`, with a
`SKILL.md` at its top. How you install it depends on where you use it:

- **Chat apps** (Claude.ai, ChatGPT, Gemini and others): upload a zip on the
  app's Skills page. No terminal needed.
- **Coding agents** (Claude Code, Codex, Antigravity CLI, GitHub Copilot,
  Cursor and others): put the skill folder in the agent's skills folder.

The steps below use `canvas-quizbank`; for another skill, replace the name.
Skill-specific requirements and a check that the install worked are on each
skill's own install page, e.g. [canvas-quizbank](canvas-quizbank/install.md).

!!! note "Menus move"
    These steps were checked against each product's documentation in
    October 2026. Vendors rename menus often; if a label differs, look for
    **Skills** in the app's settings or sidebar.

## Download the zip

Each skill has two zips with the same files, laid out differently because
the apps disagree about the layout:

| zip | layout | use it for |
|---|---|---|
| [`zip/claude/canvas-quizbank.zip`](https://github.com/hyunminkang/skills/raw/main/zip/claude/canvas-quizbank.zip) | the folder `canvas-quizbank/` inside the zip | Claude.ai, ChatGPT, Manus; unzipping into a coding agent's skills folder |
| [`zip/gemini/canvas-quizbank.zip`](https://github.com/hyunminkang/skills/raw/main/zip/gemini/canvas-quizbank.zip) | `SKILL.md` at the root of the zip; some files renamed to `.txt` | Gemini, Perplexity, Microsoft 365 Copilot Cowork |

The links download the file directly. From GitHub's file page, use the
**Download raw file** button (the arrow at the top right of the file view).

!!! warning "Keep the zip zipped"
    Safari unzips downloads by default (**Safari → Settings → General →
    Open "safe" files after downloading**). If you find a folder instead of
    a `.zip` in Downloads, turn that off and download again, rather than
    zipping the folder yourself: macOS adds `__MACOSX/` and `.DS_Store`
    files, which some apps reject.

## Chat apps

=== "Claude.ai"

    Works in the web app and the desktop app on every plan. On Team and
    Enterprise plans, an owner must allow skills and code execution for the
    organization (below).

    1. Turn on code execution: **Settings → Capabilities → Code execution
       and file creation**. Without it, skills are hidden.
    2. Open **Customize → Skills**
       ([claude.ai/customize/skills](https://claude.ai/customize/skills)).
    3. Click **+**, then **Create skill → Upload a skill**, and choose
       `zip/claude/canvas-quizbank.zip`.
    4. The skill appears under **Your skills**. Make sure its toggle is on.

    **Use it:** start a new chat and ask in plain words; Claude loads the
    skill when the request matches its description. To call it by name,
    type **/** in the message box and pick the skill. Claude's thinking
    shows when it reads the skill.

    **Update:** open the skill, click **…** → **Delete**, then upload the
    new zip.

    **Turn off or remove:** use the toggle next to the skill, or **…** →
    **Delete**.

    **Mobile:** skills you uploaded also work in the mobile apps; upload
    them from the web or the desktop app.

    **For a whole organization (Team, Enterprise):**

    - An owner turns on **Code execution and file creation** and **Skills**
      in **Organization settings → Plugins & skills → Policy**.
    - To give a skill to everyone: **Organization settings → Plugins &
      skills → Add → Upload a skill**. It is on for every member, who can
      turn it off but not delete it.
    - A member can also share a skill they uploaded: **…** → **Share**.

=== "ChatGPT"

    Personal skills are available on ChatGPT Business, Enterprise, Edu and
    Healthcare, and on some personal plans. In a workspace, an admin may
    need to turn on skills, and **Enable skill uploading**, first.

    1. Go to [chatgpt.com/skills](https://chatgpt.com/skills). From the
       sidebar, the same page is under **Plugins → Skills**.
    2. Click **Add** at the top right, then **Upload from your computer**.
    3. Drag `zip/claude/canvas-quizbank.zip` into the upload box, or click
       the box to choose the file.
    4. ChatGPT scans the skill. Most skills are ready at once; if it shows
       **Needs review**, open it and confirm.

    **Use it:** start a new chat (skills load when a chat starts). Ask in
    plain words, or type **@** and pick the skill. If a skill doesn't
    appear in a regular chat on a Plus or Pro plan, try it in **Work**.

    **Update or remove:** on the Skills page, open the skill's menu and
    delete it; upload the new zip to update.

    **Desktop and mobile:** skills added in the desktop app and on the web
    don't sync; add the skill in each place you use it.

=== "Gemini"

    Use the skill in **Gemini Spark**, Gemini's agent mode, which runs the
    skill's code. Spark needs:

    - a Google AI Pro or Ultra subscription
    - a personal Google account (not work or school), age 18 or over
    - **Keep Activity** turned on
    - a country where Spark is offered (not the EEA, the UK, Switzerland
      or Nigeria)

    Upload from [gemini.google.com](https://gemini.google.com) or the Mac
    app; the mobile apps can't upload skills.

    1. Click **Settings** at the bottom left of the sidebar, then
       **Skills**.
    2. Click the **Upload** icon at the top of the page.
    3. Drag and drop `zip/gemini/canvas-quizbank.zip` into the window, or
       click to choose it and click **Open**.
    4. Check the name and description Gemini read from the zip, then click
       **Create**.

    **Use it:** click **Switch to Spark** in the sidebar and ask in plain
    words. To call the skill by name, type **/** (or **@**) and pick it.

    **Update:** on the Skills page, open the skill, click **More (⋮) →
    Replace skill**, upload the new zip, and click **Save**.

    **Turn off or remove:** **More (⋮) → Deactivate** stops Gemini from
    using it on its own; **More (⋮) → Delete** removes it.

    **Why a separate zip:** Gemini needs `SKILL.md` at the root of the zip
    and accepts only certain file types (plain text such as `.md`, `.py`,
    `.yaml`, plus PDFs and images). In the Gemini zip, text files of other
    types get `.txt` appended (`checks.R` becomes `checks.R.txt`).

### Other chat apps

These apps also take Agent Skills. The skills in this repository have not
been tested in them, and skills that run code need an app with a code
sandbox.

| app | where | zip | notes |
|---|---|---|---|
| Perplexity (Computer) | **Skills → Create skill → Upload a skill** | `zip/gemini/` | at most 10 MB |
| Microsoft 365 Copilot (Cowork) | **Customize → Skills →** arrow next to **Add → Upload skill** | `zip/gemini/` | work accounts; at most 10 MB and 100 files |
| Manus | **Skills → + Add → Upload a skill**, or **Import from GitHub** | `zip/claude/` | type **/** to call a skill |
| Grok | [grok.com/skills](https://grok.com/skills) → **Import** | either | |
| Mistral Vibe | **Context → Skills → New Skill**; paste `SKILL.md` and attach the other files | none | no zip upload |

## Coding agents

### Where skills go

Nearly every coding agent reads skills from the same two folders, with two
exceptions worth knowing:

| agent | all projects | one project |
|---|---|---|
| Codex, GitHub Copilot, Cursor and [most others](#other-agents) | `~/.agents/skills/<name>/` | `<project>/.agents/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` | `<project>/.claude/skills/<name>/` |
| Antigravity CLI | `~/.gemini/config/skills/<name>/` | `<project>/.agents/skills/<name>/` |

Claude Code uses the same layout with `.claude` in place of `.agents`.
Antigravity reads `.agents` in a project but keeps skills for all projects
under `~/.gemini/config/`.

Committing a project's skill folder to the repository shares the skill
with collaborators and with cloud agents (Claude Code on the web, the
Copilot cloud agent), which see only what is in the repository.

In every case, `SKILL.md` must sit directly inside a folder named after
the skill:

```
~/.agents/skills/
└── canvas-quizbank/
    ├── SKILL.md
    ├── scripts/
    ├── references/
    └── examples/
```

A common mistake is one level too many
(`~/.agents/skills/canvas-quizbank/canvas-quizbank/SKILL.md`); the agent
will not find that.

### Put the skill there

Pick one of three ways. The commands install for all projects. For one
project, run them in the project folder with `.agents/skills` (or
`.claude/skills` for Claude Code) in place of the folder in your home
directory.

=== "Clone and link (recommended)"

    Keep a clone of this repository and link the skill into each agent's
    folder. `git pull` then updates every agent at once.

    macOS or Linux:

    ```bash
    git clone https://github.com/hyunminkang/skills.git ~/hyunminkang-skills

    # Codex, GitHub Copilot, Cursor and most other agents
    mkdir -p ~/.agents/skills
    ln -s ~/hyunminkang-skills/skills/canvas-quizbank ~/.agents/skills/canvas-quizbank

    # Claude Code
    mkdir -p ~/.claude/skills
    ln -s ~/hyunminkang-skills/skills/canvas-quizbank ~/.claude/skills/canvas-quizbank

    # Antigravity CLI: copy, because it may not follow links
    mkdir -p ~/.gemini/config/skills
    cp -R ~/hyunminkang-skills/skills/canvas-quizbank ~/.gemini/config/skills/
    ```

    Windows (PowerShell; a junction needs no administrator rights):

    ```powershell
    git clone https://github.com/hyunminkang/skills.git $HOME\hyunminkang-skills

    New-Item -ItemType Directory -Force $HOME\.agents\skills
    New-Item -ItemType Junction -Path $HOME\.agents\skills\canvas-quizbank `
      -Target $HOME\hyunminkang-skills\skills\canvas-quizbank

    New-Item -ItemType Directory -Force $HOME\.claude\skills
    New-Item -ItemType Junction -Path $HOME\.claude\skills\canvas-quizbank `
      -Target $HOME\hyunminkang-skills\skills\canvas-quizbank

    New-Item -ItemType Directory -Force $HOME\.gemini\config\skills
    Copy-Item -Recurse $HOME\hyunminkang-skills\skills\canvas-quizbank `
      $HOME\.gemini\config\skills\
    ```

    Update later with `git -C ~/hyunminkang-skills pull`, then copy the
    Antigravity folder again.

=== "Download and unzip (no git)"

    The zip in `zip/claude/` holds the folder `canvas-quizbank/`, so
    unzipping it into the skills folder gives the right layout.

    macOS or Linux:

    ```bash
    curl -LO https://github.com/hyunminkang/skills/raw/main/zip/claude/canvas-quizbank.zip

    mkdir -p ~/.agents/skills ~/.claude/skills ~/.gemini/config/skills
    unzip -o canvas-quizbank.zip -d ~/.agents/skills          # most agents
    unzip -o canvas-quizbank.zip -d ~/.claude/skills          # Claude Code
    unzip -o canvas-quizbank.zip -d ~/.gemini/config/skills   # Antigravity CLI
    ```

    Windows (PowerShell):

    ```powershell
    Invoke-WebRequest -OutFile canvas-quizbank.zip `
      https://github.com/hyunminkang/skills/raw/main/zip/claude/canvas-quizbank.zip

    Expand-Archive -Force canvas-quizbank.zip $HOME\.agents\skills          # most agents
    Expand-Archive -Force canvas-quizbank.zip $HOME\.claude\skills          # Claude Code
    Expand-Archive -Force canvas-quizbank.zip $HOME\.gemini\config\skills   # Antigravity CLI
    ```

    To update, delete the `canvas-quizbank` folders and unzip the new zip.

=== "npx skills"

    [`skills`](https://github.com/vercel-labs/skills) is a command-line
    installer, run with Node.js, that knows the skills folder of about 85
    agents.

    ```bash
    # all projects, for Claude Code and Codex
    npx skills add hyunminkang/skills --skill canvas-quizbank -g -a claude-code codex -y

    # this project only; asks which agents
    npx skills add hyunminkang/skills --skill canvas-quizbank
    ```

    - `-g` installs for all projects; without it, into the current project.
    - `-a` names the agents (`claude-code`, `codex`, `cursor`,
      `github-copilot`, `opencode`, …); `-a '*'` means all of them.
    - It keeps one copy in `~/.agents/skills/` (or `.agents/skills/`) and
      links it into the folders of agents that look elsewhere, such as
      `~/.claude/skills/`. Add `--copy` to copy instead of linking.
    - `npx skills list`, `npx skills update` and
      `npx skills remove canvas-quizbank` manage what you installed.
    - For Antigravity CLI, `-a antigravity-cli` uses
      `~/.gemini/antigravity-cli/skills/`, which the CLI may not read; copy
      the skill into `~/.gemini/config/skills/` instead (see the other
      tabs).

Then **start a new session** of the agent. Most agents read skills when a
session starts.

### Each agent

=== "Claude Code"

    | | |
    |---|---|
    | all projects | `~/.claude/skills/canvas-quizbank/` |
    | one project | `<project>/.claude/skills/canvas-quizbank/` |
    | check | type `/skills`, or ask "What skills are available?" |
    | call by name | `/canvas-quizbank` |

    Claude Code does **not** read `.agents/skills`. The same folders serve
    the CLI, the VS Code and JetBrains extensions and the desktop app.

    - Claude Code picks up a new skill while it runs. If `~/.claude/skills`
      did not exist when the session started, type `/reload-skills`.
    - It also looks in `.claude/skills` of parent folders, up to the
      repository root.
    - **Claude Code on the web** and other cloud sessions see only the
      repository's `.claude/skills/`, not your `~/.claude/skills/`. Commit
      the skill to the repository to use it there.
    - To turn a skill off without deleting it, use the `/skills` menu.

=== "Codex"

    | | |
    |---|---|
    | all projects | `~/.agents/skills/canvas-quizbank/` |
    | one project | `<project>/.agents/skills/canvas-quizbank/` (Codex also looks in parent folders up to the repository root) |
    | check | type `/skills` |
    | call by name | `$canvas-quizbank`, or pick it from `/skills` |

    The Codex CLI, the IDE extension and the ChatGPT desktop app share
    these folders.

    - Codex notices new skills on its own; if one doesn't appear, restart
      Codex.
    - Codex's built-in installer works too: type
      `$skill-installer install https://github.com/hyunminkang/skills/tree/main/skills/canvas-quizbank`.
      It puts the skill in `~/.codex/skills/`, an older folder Codex still
      reads.
    - A skill in both `~/.codex/skills/` and `~/.agents/skills/` shows up
      twice; keep one.
    - If the desktop app doesn't list a linked skill, copy the folder
      instead of linking it.
    - To turn a skill off without deleting it, add this to
      `~/.codex/config.toml`, with the full path to its `SKILL.md`, and
      restart Codex:

      ```toml
      [[skills.config]]
      path = "/Users/you/.agents/skills/canvas-quizbank/SKILL.md"
      enabled = false
      ```

=== "Antigravity CLI"

    | | |
    |---|---|
    | all projects | `~/.gemini/config/skills/canvas-quizbank/` |
    | one project | `<project>/.agents/skills/canvas-quizbank/` (`agy` also looks in parent folders up to the repository root) |
    | check | type `/skills` |
    | call by name | `/canvas-quizbank` |

    Antigravity CLI (`agy`) reads `.agents/skills` in a project, but for
    all projects it does **not** read `~/.agents/skills`. Use
    `~/.gemini/config/skills/`, which the CLI, the Antigravity IDE and
    Antigravity 2.0 share. (Antigravity's skills page lists
    `~/.gemini/antigravity-cli/skills/` for the CLI, but users report that
    only `~/.gemini/config/skills/` is found.)

    - **Copy the folder rather than linking it:** reports differ on
      whether Antigravity follows linked skill folders.
    - `/skills reload` picks up a new skill without restarting.
    - Project skills load after you answer **Yes, I trust this folder**.
    - Moving from Gemini CLI: project skills move from `.gemini/skills/` to
      `.agents/skills/`.

=== "GitHub Copilot"

    | | |
    |---|---|
    | all projects | `~/.agents/skills/canvas-quizbank/` (also `~/.copilot/skills/`) |
    | one project | `<project>/.agents/skills/canvas-quizbank/` (also `.github/skills/`, `.claude/skills/`) |
    | check | VS Code: type `/skills` in Chat; Copilot CLI: `/skills list` |
    | call by name | `/canvas-quizbank` |

    The **Copilot cloud agent** on github.com sees only skills committed
    to the repository. In the Copilot CLI, `/skills reload` picks up a new
    skill without restarting.

=== "Cursor"

    | | |
    |---|---|
    | all projects | `~/.agents/skills/canvas-quizbank/` (also `~/.cursor/skills/`) |
    | one project | `<project>/.agents/skills/canvas-quizbank/` (also `.cursor/skills/`) |
    | check | **Customize** panel → **Skills**; `/skills` in the Cursor CLI |
    | call by name | `/canvas-quizbank` |

    Cursor also reads `.claude/skills`, so a skill installed for Claude
    Code appears in Cursor too.

### Other agents

All of these read `~/.agents/skills/` (all projects) and
`<project>/.agents/skills/` (one project), so the steps above work
unchanged. The table shows how to check and call a skill.

| agent | check | call by name | notes |
|---|---|---|---|
| Amp | `amp skills list` | automatic | also reads `.claude/skills` |
| Augment (Auggie CLI) | `/skills` | `/canvas-quizbank` | |
| Cline | **Skills** tab | `/canvas-quizbank` | |
| Crush | **Ctrl+P** palette | automatic | |
| Factory Droid | `/skills` | `/canvas-quizbank` | start a new session after installing |
| Gemini CLI | `/skills list` | automatic | Google moved personal accounts to Antigravity CLI in June 2026; work and API-key accounts can still use it |
| Goose | `goose skills list` | `/skills canvas-quizbank` | |
| Junie CLI | `/skills` | `/canvas-quizbank` | project skills load only in trusted projects |
| Kilo Code | **/** menu → **Skills** | `/canvas-quizbank` | `/reload` after installing |
| Kimi Code CLI | | `/skill:canvas-quizbank` | start a new session after installing |
| Mistral Vibe | | `/canvas-quizbank` | project skills load only in trusted folders |
| OpenCode | ask the agent | automatic | also reads `.claude/skills` |
| OpenHands | | automatic | OpenHands Cloud sees only skills in the repository |
| Qwen Code | `/skills` | `/canvas-quizbank` | |
| Warp | ask the agent | `/canvas-quizbank` | |
| Windsurf (Devin Desktop) | Cascade **⋯** menu → **Skills** | `@canvas-quizbank` | |

These agents need a different folder:

| agent | all projects | one project |
|---|---|---|
| Kiro (IDE and CLI) | `~/.kiro/skills/` | `.kiro/skills/`; or **Agent Steering & Skills → Import** in the IDE |
| Junie in a JetBrains IDE | `~/.junie/skills/` | `.junie/skills/` |
| JetBrains AI Assistant | **Settings → Tools → AI Assistant → Skills** | `.agents/skills/` |
| Letta Code | `~/.letta/skills/` | `.agents/skills/` |

Agents not listed here: if the agent supports Agent Skills, try
`~/.agents/skills/` first; it is the location the
[Agent Skills guidance for clients](https://agentskills.io/client-implementation/adding-skills-support)
recommends.

## Troubleshooting

**The upload is rejected.**

- Check you used the right zip: Claude.ai and ChatGPT take
  `zip/claude/`; Gemini takes `zip/gemini/`.
- Upload the zip as downloaded. Re-zipping on a Mac adds `__MACOSX/` and
  `.DS_Store` files, which Gemini rejects.

**The agent doesn't list the skill.**

- Check the path: `SKILL.md` must be at `<skills folder>/canvas-quizbank/SKILL.md`,
  not one folder deeper.
- Claude Code reads `.claude/skills`, not `.agents/skills`.
- Start a new session; most agents read skills only at the start.
- Project skills: some agents load them only after you trust the folder.

**The skill is listed twice.** Agents that read both `.agents/skills` and
`.claude/skills` (Cursor, Copilot, OpenCode, Amp and others) list a skill
installed in both. Linking both to one clone keeps the copies identical,
so either one works.

**The agent ignores the skill.** Call it by name (`/canvas-quizbank` in
Claude Code and most agents, `$canvas-quizbank` in Codex, **@** in
ChatGPT), and check that its toggle is on in a chat app.

**The skill's scripts fail.** In a chat app, turn on code execution
(Claude.ai) or use an agent mode that runs code (Gemini Spark). In a
coding agent, check that `python3 --version` prints 3.9 or newer.

## Before installing anyone's skill

A skill can tell the agent to run its scripts. Read `SKILL.md` and the
`scripts/` folder of any skill before installing it, as you would any
program. The skills in this repository are Apache-2.0 licensed and their
scripts use only the Python standard library.
