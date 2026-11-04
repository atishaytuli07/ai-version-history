# Notes per tool

## Claude Code, Cursor, Codex, Windsurf, Copilot, Gemini CLI

Files mode works as described in SKILL.md. Offer the auto-save hook once in Claude Code (`install-hooks claude-code`, which writes `.claude/settings.local.json`, a personal settings file that isn't committed) or Cursor (`install-hooks cursor`, which writes `.cursor/hooks.json`, a file teams often commit; a teammate without the history sees the hook do nothing). The hooks call `python3` (`py` on Windows), not a path from this machine. This kit installs hooks only for Claude Code and Cursor; elsewhere, saving after each request is the safety net.

AI tool folders (`.claude/`, `.cursor/`, `.agents/`, `.gemini/`, `.devin/`, `.windsurf/`) and installed skills are never versioned, so going back can't remove the skill or the hook, and a backup can't plant files there.

## claude.ai (with code execution)

Files live in this conversation's sandbox and disappear when the conversation ends. When the work matters:
- After meaningful versions, offer `backup --out <name>-history.zip` and share the file, so the user keeps every version.
- In a new conversation, the user uploads that zip; run `import <file>` in an empty folder. It restores the history and writes the current version's files.
- Share the work itself as usual (artifact or file); the history is in addition to that.

If the working folder also holds unrelated files (uploads, scratch files), use `init --only <the files you're building>`.

## Replit Agent

Put `assets/rules/files-mode-rules.md` into `replit.md` at the project root, because Agent reads that file when it handles requests. The project needs Python 3. If `python3` isn't found, the user can add Python from the Dependencies or Nix settings, or use the GitHub layer instead.

## Windows

Use `py` instead of `python3`. Everything else is the same.

## Tools that read rules but not skills

Many tools read a project rules file. Paste `assets/rules/files-mode-rules.md` into it after running `init` once, so `.ai-versions/aiv.py` exists:

| Tool | Rules file |
|---|---|
| Codex, and most agents that read it | `AGENTS.md` |
| Cursor | `.cursor/rules/ai-versions.mdc`, starting with a front-matter block containing `alwaysApply: true` so the rule is always used (or `AGENTS.md`) |
| Windsurf | `.windsurf/rules/ai-versions.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Gemini CLI | `GEMINI.md` |
| Replit | `replit.md` |

For plain chats (ChatGPT, Gemini, Claude Projects without code), paste `assets/rules/chat-mode-rules.md` into custom instructions or project instructions.
