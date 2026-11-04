---
name: versioning-ai-work
description: Gives every change to AI-built work its own version number (v1.2.3), keeps every version until the user deletes it, and lets the user compare versions or go back without losing work. Use whenever you create or edit files for a user over several turns (designs, web pages, apps, documents, code), even if they never mention versions, and whenever the user asks to save a version, see history, compare, undo, restore, roll back, or go back to an earlier or "the previous" version.
---

# Versioning AI work

People iterating with AI lose good versions: a regeneration overwrites them, an undo goes too far, or the conversation drifts. This skill makes every change a numbered version that stays until the user deletes it, so they can see, compare, and return to any earlier state.

## The three rules

1. **Every change gets a version.** One user request that changes files is one version, saved at the end of that turn, before you reply. Saving per request, not per file edit, keeps the history readable.
2. **Going back never deletes a version.** Only the script writes to `.ai-versions/`. Never edit, move, or delete anything there, even if asked to clean up. Point the user to `backup` instead.
3. **Going back is a new version.** Restore with the script; never rebuild old work from memory. A restore is saved as a new version, so it can be undone too.

The script picks every version number. Never guess one; report the number it prints.

## Pick the mode once per project

- **You can run commands and edit files** (Claude Code, Cursor, Codex, Windsurf, Copilot, Gemini CLI, Replit Agent, claude.ai with code execution): use files mode below.
- **The project has `.github/workflows/ai-versions.yml`**: it uses the GitHub version layer. Don't run `init`. Instead, with every change, overwrite `.ai-versions/pending.json`, and to go back, write `.ai-versions/restore.json`. Both are described in [assets/rules/github-layer-rules.md](assets/rules/github-layer-rules.md).
- **You can't run commands** (a plain chat): follow [references/chat-mode.md](references/chat-mode.md).
- **The user builds in Lovable, Bolt or v0 (Bolt and v0 are in beta: not tested live yet), or Figma Make** and asks how to version it there: read [references/app-builders.md](references/app-builders.md).

## Files mode

The script is `scripts/aiv.py` inside this skill's folder (the folder that holds this SKILL.md). Call it by its full path and point it at the project with `--root`:

```bash
python3 "<this skill's folder>/scripts/aiv.py" --root "<project folder>" <command>
# Windows: py instead of python3
```

After `init`, every project also has its own copy, so from the project folder `python3 .ai-versions/aiv.py <command>` works the same. Below, `aiv` means either form. If Python isn't installed, tell the user it's needed (python.org) and use chat mode until it is.

### Start

Before your first edit in a project without `.ai-versions/`, run `init`. It saves the current files as v1.0.0, so the user can always return to how things were before you touched them.

If the folder holds more than the project (a sandbox, a home folder, a Downloads folder), scope it: `init --only poster.html assets/`. `init` refuses folders over 5,000 files because that usually means the wrong folder.

### After every change

```bash
aiv save --bump minor --summary "Added a pricing section with 3 plans" \
  --reason "New section; layout and style unchanged" --prompt "add pricing with 3 plans"
```

| `--bump` | Shown to the user as | When |
|---|---|---|
| `patch` | Small tweak | Same features, small adjustment: text, color, spacing, size, a small fix |
| `minor` | New feature | Something new, same direction: a section, page, component, feature |
| `major` | Big change | The direction changed: redesign, new layout, new style system, removing a feature |

One request with several changes takes the highest level. Unsure between two levels: take the lower one and say so in `--reason`. Edge cases (documents, refactors, content updates) are in [references/bump-levels.md](references/bump-levels.md).

Write `--summary` for the user, not for a developer: "Made the hero image larger", not "Update Hero.tsx". Put the user's request, shortened to one line, in `--prompt`.

Then end your reply with one line, for example: `Saved v1.3.0 (New feature): Added a pricing section with 3 plans.`

If `save` says the files match an older version exactly, it records the save as going back to that version. Tell the user that's what happened.

### When the user asks

| The user says | Run | Then |
|---|---|---|
| "show versions", "history" | `list` | Show a short table. For a visual timeline, run `view` and share the HTML file it writes. |
| "what changed in v1.3.0" | `diff v1.3.0^ v1.3.0` | Explain in plain words. `vX^` means the version before vX. |
| "compare v1.2 and v2.0" | `diff v1.2.0 v2.0.0 --stat`, then without `--stat` for detail | Say what changed, what got better, what got worse. If you can render the work (HTML, images), show both side by side. |
| "go back to v1.2.0", "undo that" | `restore v1.2.0`, or `restore prev` for undo | Then do the step below. |
| "bring back only the old header", "old design but keep the new text" | `restore v1.2.0 --path <files>` | Only those files change; it's saved as a Small tweak. |
| "try another direction from v1.2.0" | `restore v1.2.0` | Then make the new change and save it as usual. |
| "what's the current version", "anything unsaved" | `status` | |
| "give me v1.2.0 as files" | `export v1.2.0 --out v1.2.0.zip` | |
| "continue this in another chat or tool" | `backup --out history.zip` | In the new place: `import history.zip`. |

When the user names a version vaguely ("the blue one", "before the redesign"), run `list` and match the summaries. If two versions fit, ask which one.

### After going back

A full restore puts every project file back the way it was, including files the user may not think of as part of the work, like notes or data. Tell the user which files changed (the script lists them). If it saved unsaved work first, say which version holds it and offer to bring specific files back with `restore <that version> --path <file>`. When the request clearly targets only part of the project ("the old colors"), use `--path` from the start.

Run `handoff <version you restored>` and treat its output as the current truth before making the next change. It lists only the decisions that led to that version and names the dropped ones, so instructions from abandoned directions don't creep back in. If the conversation is long, offer to continue in a new chat and give the user the handoff text to paste there.

### Safety net for forgotten saves

In Claude Code or Cursor, offer this once per project: `install-hooks claude-code` or `install-hooks cursor`. It adds a hook that saves any change you forgot to save as a Small tweak when you finish. Install it only after the user says yes, because it writes to their tool settings.

## Talking about versions

Use the user's words: Small tweak, New feature, Big change, Went back. Mention version numbers, not commits, files in `.ai-versions/`, or hashes. Tool-specific notes (claude.ai, Replit, Windows) are in [references/tools.md](references/tools.md).

When a user goes back, remind them once that only files come back: database rows and other live data stay as they are.

## All commands

| Command | What it does |
|---|---|
| `init [--only PATH...]` | Start the history and save v1.0.0 |
| `save --bump B --summary S [--reason R] [--prompt P]` | Save the current files as a new version |
| `status` | Current version and unsaved changes |
| `list [--all] [--json]` | Versions, newest first |
| `show V` | One version's details and changed files |
| `diff [A] [B] [--stat] [--path P...]` | No args: unsaved changes. One: A to latest. Two: A to B |
| `restore V [--path P...] [--note N]` | Go back (all files, or only some); saves unsaved work first, then saves the restore as a new version |
| `handoff [V]` | Clean context for continuing from V |
| `view [--out FILE]` | HTML timeline of all versions |
| `export V --out DIR_or_ZIP` | The files of one version |
| `backup --out FILE.zip` / `import FILE.zip` | Move the whole history |
| `install-hooks claude-code\|cursor` | Auto-save what the AI forgets |
| `setup-github [--with-pill]` | Add the GitHub layer to an app-builder repo |
| `doctor` | Check the history for missing pieces |

Versions can be written as `v1.2.0`, `1.2.0`, `latest`, `prev`, or `v1.2.0^`.
