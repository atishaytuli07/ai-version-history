# App builders: Lovable, Bolt, v0, Replit, Figma Make

Most app builders can't run this skill's script, but several sync every change to GitHub. There, a GitHub Action versions each change instead: the builder's AI describes the change in `.ai-versions/pending.json`, and the Action turns every push into a permanent version tag, even when the AI forgets to describe it.

## Contents
- Which approach per builder
- Adding the GitHub layer
- Where the rules go in each builder
- Working in a repo that already has the GitHub layer

## Which approach per builder

| Builder | Approach | Why | Status |
|---|---|---|---|
| Lovable | GitHub layer | Two-way sync with the default branch | Tested live on apps made before May 13, 2026; newer (TanStack Start) apps not yet |
| Bolt | GitHub layer | Commits working changes to the connected branch and pulls GitHub changes regularly | Beta: tell the user it hasn't been tested live yet |
| v0 | GitHub layer on the v0 branch | v0 usually commits to its own branch (like `v0/main-abc123`), not to main | Beta: tell the user it hasn't been tested live yet |
| Replit | Files mode | Replit Agent runs shell commands; put `assets/rules/files-mode-rules.md` in `replit.md` at the project root | Uses files mode |
| Figma Make | Built-in history | No files or GitHub to work with; name versions with the same scheme ("v1.3.0 New feature: ...") using Make's "Name this version" | Manual |

## Adding the GitHub layer

The user connects the builder to GitHub first, in the builder's own settings. Then either:

- **You have the repo checked out** (for example in Claude Code or Cursor): run `python3 scripts/aiv.py setup-github`, add `--with-pill` for a version badge in the app's preview, then commit and push. The pill needs React (Lovable, Bolt and v0 apps are); render `<VersionPill />` once in the root layout or App component.
- **The user does it by hand on github.com**: walk them through creating each file from `assets/github-layer/` with **Add file → Create new file**. In this skill the folders are stored without their leading dot: `github/` goes to `.github/` and `ai-versions/` goes to `.ai-versions/` in the repo. Add `.github/workflows/ai-versions.yml` last, since it switches versioning on.

Then, on GitHub:

1. **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.** Without this, versions can't be saved and runs fail with a 403 error.
2. Optional but recommended: **Settings → Rules → Rulesets → New tag ruleset**, target pattern `v*`, turn on Restrict updates, Restrict deletions and Block force pushes. Leave Restrict creations off. Then versions can't be deleted or changed. Rulesets on private repos need a paid GitHub plan; without one, versions stay until someone deletes them, so suggest regular backups.
3. **v0 only:** **Settings → Secrets and variables → Actions → Variables → New repository variable**, name `AI_VERSIONS_BRANCH`, value the branch v0 commits to (shown in v0's Git panel). Without it, versions are only made when changes reach the default branch.

The first push after setup creates `v1.0.0`. Versions appear on the repo's Releases page and, with the pill, in the app preview.

Going back, in order of ease:
1. **Ask in the builder's chat:** "go back to v3.4.5". The builder's AI writes `.ai-versions/restore.json`; the Action brings back that exact version as a new commit (about 1 to 2 minutes) and removes the request. If the number doesn't exist, the pill shows a notice instead.
2. **The builder's own history/restore button.** It's detected and saved as "Went back" (tested in Lovable; beta in Bolt and v0). If it restores a version from before setup or before a kit update, it can also roll back the kit's own files, so prefer asking in chat.
3. **On GitHub:** Actions → AI Restore → Run workflow, type the version number.

After going back, later versions show "Built on v3.4.5" in the pill, so it's clear which line they continue.

Always tell the user: going back restores code, not data. Database rows and stored files stay as they are.

Privacy: the pill's list is served from `public/ai-versions.json`, which anyone can open on the live site. Prompts are left out by default. To show them, add the repository variable `AI_VERSIONS_PILL_NOTES` = `yes`. Prompts are also in the version tags and release pages, which anyone can read on a public repo.

## Where the rules go in each builder

Give the user `assets/rules/github-layer-rules.md` to paste:

| Builder | Where |
|---|---|
| Lovable | Project settings → Instructions |
| Bolt | Project settings → Knowledge (applies to that project) |
| v0 | **+** in the prompt bar → Instructions → New Instruction, then keep it checked. v0 instructions are saved to the account, so they apply to every project while checked. |

Lovable also has a GitHub-free option that stores versions in the project's Lovable Cloud database. It's part of the separate ai-versions Lovable kit, not this skill.

## Working in a repo that already has the GitHub layer

If `.github/workflows/ai-versions.yml` exists, the project is versioned on GitHub. Don't run `init`: two version histories would disagree. Follow `assets/rules/github-layer-rules.md`: overwrite `.ai-versions/pending.json` with every change (the version number appears about a minute after the push), and to go back, write only `.ai-versions/restore.json`.
