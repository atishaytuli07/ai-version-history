# ai-versions

A version history for AI-built work. Every change gets a readable number like **v3.4.5**, with its date and a summary. You can go back to any version by asking in chat, and going back is saved as a new version, so you can undo it too.

## What it does

- **Readable version numbers.** Small tweak `v3.4.5 → v3.4.6`, new feature `→ v3.5.0`, big change `→ v4.0.0`.
- **A timeline inside your preview.** A small button lists every version with its date and what changed (and your prompt, if you turn that on).
- **Go back from chat.** "Go back to v3.4.5" brings back that exact version as a new version.
- **Going back never deletes a version.** History stays until you delete it. Versions are git tags you can lock on GitHub (Pro), or rows in your project's database (Lovable Lite). Back up regularly.
- **"Built on" labels.** After going back, later versions show which version they continue from.

Going back restores **code**, not **data**: database rows and stored files stay as they are.

## Where it works

| Where you build | Use | Status |
|---|---|---|
| Lovable | `lovable-kit/` (Lite without GitHub, or Pro with GitHub) | Tested live |
| Bolt | `github-layer/` | Beta: not tested live yet |
| v0 | `github-layer/` | Beta: not tested live yet |
| Claude, Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, Replit | the skill in `skills/versioning-ai-work/` | Needs Python 3.8+ |
| ChatGPT, Gemini and other plain chats | `skills/versioning-ai-work/assets/rules/chat-mode-rules.md` | Paste-in rules |

## Start here

First download everything: click **Code → Download ZIP** at the top of this page and unzip it.

- **Lovable:** in the unzipped folder, open `lovable-kit` and double-click **START-HERE.html**. (GitHub shows .html files as code, so open it from your computer.)
- **Bolt or v0:** read `github-layer/README.md`.
- **AI coding tools:** install the skill:

```bash
npx skills add YOUR-GITHUB-NAME/ai-versions
```

Or copy `skills/versioning-ai-work/` into your tool's skills folder. Paths for each tool are in `skills/README.md`.

## Testing

- Automatic tests run on every push (`.github/workflows/check.yml`): the script on Python 3.8 to 3.13, the GitHub layer, the Lite database rules, and a check that the three copies of the GitHub layer match.
- Bolt and v0 live checklist: `docs/LIVE-TEST.md`.

## License

MIT. See `LICENSE`.
