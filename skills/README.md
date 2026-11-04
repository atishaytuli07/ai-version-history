# ai-versions: a version history for your AI-built work

This is a skill: a folder of instructions an AI tool loads when it needs them. With it, every change your AI makes gets a version number, like **v2.4.1**. Versions stay until you delete them, and you can compare or go back to any of them, just by asking.

It works in Claude, Claude Code, Cursor, Codex, GitHub Copilot, Gemini CLI, Windsurf and Replit. Lovable is covered through GitHub (Bolt and v0 too, in beta), and plain chats like ChatGPT through rules you paste in.

![The version timeline](timeline-preview.png)

## What the numbers mean

```text
v 2 . 4 . 1
  |   |   |
  |   |   +--  small tweaks: a color, some text, a small fix
  |   +------  new features: a new section, page or function
  +----------  big changes: a redesign, a new direction
```

When you go back to an older version, the middle number goes up. Your newer versions are all still there.

## What you can say

Talk to your AI normally:

- "Show me the versions."
- "What changed in v1.3.0?"
- "Compare v1.2 and v2.0."
- "Go back to before the redesign." or "Undo that."
- "Use the old colors, but keep the new text."
- "Show me the version timeline." This makes the page in the picture above.

Going back never deletes a version. Unsaved work is saved first, and going back is saved as a new version, so you can always undo it. History stays until you delete it, so back up regularly (ask: "Make a backup of the versions").

---

## Install

First get the files: on GitHub, open the repository and click **Code → Download ZIP**, then unzip it. The skill is the **versioning-ai-work** folder inside `skills/`.

Copy that whole folder, not just one file: it contains the program that saves versions.

| Tool | Put the folder in | Or for all your projects |
|---|---|---|
| Claude (website or app) | Settings → Capabilities → Skills → **Upload skill**, choose `versioning-ai-work.zip`. Needs a paid plan with code execution on. | |
| Claude Code | `.claude/skills/` in your project | `~/.claude/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| GitHub Copilot | `.github/skills/` | `~/.copilot/skills/` |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` |
| Windsurf (now Devin Desktop) | `.devin/skills/` (older versions: `.windsurf/skills/`) | `~/.codeium/windsurf/skills/` |

Several tools also read `.agents/skills/`, so that's a good choice for a project you open in more than one tool. *Folders checked against each tool's docs on 28 Oct 2026; tools move them now and then.*

**You also need Python 3.8 or newer** (tested on 3.8, 3.11 and 3.13). To check, run `python3 --version` (on Windows: `py --version`). If it's missing, get it from python.org. Git isn't needed.

**Check that it works:** open a project and ask your AI, "Set up versioning for this project." It should answer with something like `Set up version history. v1.0.0 saved with 12 files.`

---

## Auto-save (optional)

In Claude Code and Cursor, the AI offers this once per project. It saves any change the AI forgot to save, as a Small tweak, whenever the AI finishes. You can also just ask: "Turn on auto-save for versions."

---

## Other tools

| Where you build | What to do |
|---|---|
| **Lovable** (tested), **Bolt and v0** (beta: not tested live yet) | Connect the project to GitHub. Then, in a tool that has this skill (for example Claude Code with the repo open), ask: "Set up ai-versions for my Lovable repo" (or Bolt, or v0). Steps: `versioning-ai-work/references/app-builders.md`. After that, you can ask the builder's own chat to "go back to v3.4.5". |
| **Replit** | Paste `assets/rules/files-mode-rules.md` into the `replit.md` file at your project's root. |
| **Other agents with a rules file** (`AGENTS.md`, `.cursor/rules`, `GEMINI.md`) | Ask once to set up versioning, then paste `assets/rules/files-mode-rules.md` into the rules file. |
| **Plain chats** (ChatGPT, Gemini, Claude without code) | Paste `assets/rules/chat-mode-rules.md` into custom instructions. Versions live in the conversation, which is less safe, so save important versions as files too. |

---

## Where versions are kept

Everything lives in a hidden **.ai-versions** folder inside your project:

- every version's files, stored once even when they repeat
- a small record per version: number, label, summary, prompt, date
- **HISTORY.md**, a list you can read yourself
- a copy of the program, so the project works on its own

In a git project, this folder is kept out of git automatically, so switching branches can't change your history. To move your history to another computer, chat or tool, ask: "Make a backup of the versions." Then in the new place: "Import this backup."

AI tool settings and the installed skill are never part of a version, so going back can't remove them. If you delete the `.ai-versions` folder (for example with `git clean -x`), the history is gone, so keep backups.

---

## Good to know

- **Going back restores your files, not your data.** Database rows, uploaded files in storage and other live data stay as they are. Back up data separately.

- **The AI picks the label.** It's usually right. If not, tell it; it learns for similar changes. Old versions stay as they are.
- **Without auto-save, a change only gets a version if the AI saves it.** The skill tells it to save after every request.
- **Very large files** (over 25 MB) and **huge folders** (over 5,000 files or 500 MB) are skipped with a message.
- **In Claude on the web,** files only live inside one chat. The AI offers a backup so you keep your history.

## What's inside

```text
versioning-ai-work/
  SKILL.md              the instructions the AI follows
  scripts/aiv.py        the program that saves, compares and restores (Python, nothing else needed)
  references/           examples for picking labels, chat mode, app builders, notes per tool
  assets/github-layer/  the GitHub robot and version button for Lovable (Bolt and v0 in beta)
  assets/rules/         rules to paste into tools that don't load skills
```
