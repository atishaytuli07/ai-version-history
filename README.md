# AI Version History for Lovable, Bolt, v0, Claude Code and Cursor

[![Check](https://github.com/atishaytuli07/ai-version-history/actions/workflows/check.yml/badge.svg)](https://github.com/atishaytuli07/ai-version-history/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Undo AI changes without losing anything. Every change your AI makes gets a readable version number like **v3.4.5**, with the date, a one-line summary and (if you want) the prompt that made it. Open the timeline from your app's preview, and go back to any version by asking in chat.

Free and open source. Works in Lovable today, with Bolt and v0 in testing, and as an agent skill for Claude Code, Cursor and other AI coding tools.

![The version button in a Lovable preview, showing v7.1.1, a "Went back" version and a big change, each with its date and prompt](lovable-kit/pill-preview.png)

## Why

AI builders already keep a history, but it's hard to use when something breaks:

- Versions have no readable names, so finding "the one before the redesign" means scrolling and guessing.
- The prompt that made a change usually isn't shown next to it.
- Coding-agent checkpoints are short-term undo. Claude Code, Cursor and Copilot all say in their own docs to keep using Git for real history.

This kit puts a number, a date, a summary and the prompt on every change, in one timeline.

## What you get

- **A readable number for every change.** Small tweak `v3.4.5 → v3.4.6`, new feature `→ v3.5.0`, big change `→ v4.0.0`.
- **A timeline inside your preview.** A small button lists every version. Visitors to your live site don't see it.
- **Go back by asking.** "Go back to v3.4.5" brings that version back as a new version.
- **Going back never deletes a version.** Later versions show "Built on v3.4.5", so you always know where you are.
- **Your prompts, if you want them.** Prompts are off by default, so nothing private ends up on your live site.

## Where it works

| Where you build | Use | Status |
|---|---|---|
| Lovable | [`lovable-kit/`](lovable-kit/): Lite (no GitHub) or Pro (GitHub) | Tested live |
| Bolt | [`github-layer/`](github-layer/) | Beta: not tested live yet |
| v0 | [`github-layer/`](github-layer/) | Beta: not tested live yet |
| Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, Replit, Claude | the skill in [`skills/versioning-ai-work/`](skills/versioning-ai-work/) | Needs Python 3.8+ |
| ChatGPT, Gemini and other chat apps | [paste-in rules](skills/versioning-ai-work/assets/rules/chat-mode-rules.md) | Copy and paste |

## Quick start

### Lovable

1. Click **Code → Download ZIP** at the top of this page and unzip it.
2. Open the `lovable-kit` folder and double-click **START-HERE.html**. It opens in your browser with every step and a **Copy** button for each message and file. (GitHub shows `.html` files as code, so open it from your computer.)
3. Pick **Lite** (about 10 minutes, no GitHub) or **Pro** (about 15 minutes, uses GitHub) and follow the steps.

| | Lite | Pro |
|---|---|---|
| Needs GitHub | No | Yes |
| Where versions are kept | A table in your app's database | Git tags on GitHub |
| How you go back | Lovable's History; the button tells you which change | Ask in chat: "go back to v3.4.5" |
| Every change gets a version | Only when Lovable describes the change | Yes |
| Private | No: anyone with your app's public key can read the list | Yes, in a private repo |
| Best for | Trying it out, personal and prototype projects | Real projects and anything private |

### Bolt or v0 (beta)

Read [`github-layer/README.md`](github-layer/README.md). The checklist used to test it is in [`docs/LIVE-TEST.md`](docs/LIVE-TEST.md).

### Claude Code, Cursor and other AI coding tools

Install the skill:

```bash
npx skills add atishaytuli07/ai-version-history
```

Or copy the [`skills/versioning-ai-work/`](skills/versioning-ai-work/) folder into your tool's skills folder. The path for each tool is in [`skills/README.md`](skills/README.md). Then talk to your AI normally: "Show me the versions", "What changed in v1.3.0?", "Go back to before the redesign".

## How the numbers work

```text
v 2 . 4 . 1
  |   |   |
  |   |   +--  small tweaks: a colour, some text, a small fix
  |   +------  new features: a new section, page or form
  +----------  big changes: a redesign, a new direction
```

When you go back, the numbers keep going up. On v7.0.0, going back to v3.4.5 gives you v7.1.0 with v3.4.5's code, and v4 to v7 are still there to come back to.

## Good to know

- **Going back restores code, not data.** Database rows and uploaded files stay as they are, just like with Lovable's and Bolt's own history. If a change added or changed database tables, going back can break the app until you ask the AI to fix the tables.
- **History stays until you delete it.** In Pro, lock version tags on GitHub to stop them being deleted (rulesets on private repos need a paid GitHub plan), and back up regularly.
- **Don't go back to a version from before you set the kit up.**

## FAQ

**How do I undo a change in Lovable?**
Without the kit: open History from the top bar, pick a version and click Revert. With the kit you also see each version's number, date and prompt, and in Pro you can go back by asking in chat.

**Is it free?**
Yes. It's open source under the MIT license. Pro needs a GitHub account.

**Will my visitors see the version button?**
No. It shows in your preview. Add `?versions=on` to your live site's address to see it there yourself.

**Can I use it for ChatGPT or Gemini chats?**
Yes, with the paste-in rules. The AI numbers each change in the chat so you can ask for any earlier version. Those notes live inside the chat, so save important work outside it too.

**More help:** the full guide, and how to undo changes in each AI tool without the kit, is at [aibestprompts.in/ai-versions](https://aibestprompts.in/ai-versions).

## Testing

Tests run on every push ([`check.yml`](.github/workflows/check.yml)): the skill's script on Python 3.8 to 3.13, the GitHub layer (including restores across workflow changes), the Lite database rules on Postgres, and a check that the copies of the GitHub layer match.

## Contributing and security

Bug reports and ideas are welcome in [Issues](https://github.com/atishaytuli07/ai-version-history/issues). To report a security problem, please don't open a public issue: see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Atishay Tuli
