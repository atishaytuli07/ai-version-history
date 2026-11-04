# GitHub layer: Bolt, v0 and other GitHub-synced builders

The same versioning as the Lovable Pro kit, for builders that sync your project to GitHub. **Bolt and v0 are in beta: not tested live yet.** If you try them, the checklist in `docs/LIVE-TEST.md` shows what to check.

Going back restores code, not data. Database rows and stored files stay as they are. If a change added or changed database tables, going back can break the app; ask the builder to fix it afterwards.

---

## Step 1: Connect the builder to GitHub

- **Bolt:** click the GitHub icon in Bolt and connect a repository.
- **v0:** open the **Git** panel and connect a repository. Write down the branch name v0 shows (for example `v0/main-abc123`): v0 usually commits there, not to `main`.

**You should see:** your project's code in a repository on GitHub.

---

## Step 2: Let GitHub save versions

On GitHub: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**

**v0 only:** also **Settings → Secrets and variables → Actions → Variables → New repository variable**. Name `AI_VERSIONS_BRANCH`, value the branch name from Step 1.

---

## Step 3: Add the 6 files

On GitHub, click **Add file → Create new file**, type the path, paste the file's contents, and click **Commit changes**. **v0 only:** first switch to v0's branch with the branch menu at the top left; new files go to the branch you're viewing.

Add them in this order. File 6 switches versioning on, so it goes last.

| # | File in copy-paste | Path on GitHub |
|---|---|---|
| 1 | `1-pending.json` | `.ai-versions/pending.json` |
| 2 | `2-ai-version.mjs` | `.github/scripts/ai-version.mjs` |
| 3 | `3-ai-restore.mjs` | `.github/scripts/ai-restore.mjs` |
| 4 | `4-ai-restore.yml` | `.github/workflows/ai-restore.yml` |
| 5 | `5-VersionPill.tsx` | Bolt (Vite/React): `src/components/VersionPill.tsx`. v0 (Next.js): `components/VersionPill.tsx` |
| 6 | `6-ai-versions.yml` | `.github/workflows/ai-versions.yml` |

To open the files on your computer: right-click, **Open with → Notepad** (Windows) or **TextEdit** (Mac).

**You should see:** after file 6, the **Actions** tab shows "AI Versions" with a green check, and `v1.0.0` appears under **Releases**.

---

## Step 4: Give the builder the rules

Paste everything from `RULES.md`:

- **Bolt:** **Project settings → Knowledge**.
- **v0:** **+** in the prompt bar → **Instructions → New Instruction**, title `ai-versions`, and keep it checked. v0 saves instructions to your account, so while it's checked it applies to **every** v0 project. Uncheck it in projects without versioning.

---

## Step 5: Add the version button

Send this to the builder:

**Bolt:**

```text
In src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change src/components/VersionPill.tsx.
```

**v0:**

```text
In app/layout.tsx, add import VersionPill from "@/components/VersionPill"; and render <VersionPill /> once inside <body>, after {children}. Don't change components/VersionPill.tsx.
```

**You should see:** a small version button in the bottom-left of the preview. If it doesn't show, add `?versions=on` to the end of the preview address.

---

## Step 6: Try it

Ask for a small change ("make the heading blue"), wait 1 to 2 minutes, and open the version button: it should show a Small tweak. To go back, ask in chat: "go back to v1.0.1".

---

## If something isn't right

| What you see | What to do |
|---|---|
| No "AI Versions" run in Actions | Check file 6's path. For v0, check that the files are on v0's branch and `AI_VERSIONS_BRANCH` is set |
| Red cross with "403" | Do Step 2, then open the run and click **Re-run jobs** |
| No version button | Send Step 5's message again, or add `?versions=on` to the preview address |
| Button says "The version list isn't here yet" | Wait for a green check in Actions, then reopen the button. If it stays, the builder may not be pulling changes from GitHub; please report it |
| Going back doesn't change the code | The builder may not be pulling changes from GitHub. Use the builder's own history instead, and please report it |

Prompts aren't shown in the version button by default, because your live site serves the list. To show them, add a repository variable `AI_VERSIONS_PILL_NOTES` with value `yes`. Prompts are always in the version tags and release pages on GitHub.
