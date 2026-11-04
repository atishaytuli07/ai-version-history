# GitHub layer: Bolt, v0 and other builders that sync to GitHub

This is the same versioning as the Lovable Pro kit. It is for builders that sync your project to GitHub.

> **Beta: Bolt and v0 are not tested live yet.** If you try them, the checklist in `docs/LIVE-TEST.md` shows what to check.

> **Warning: going back brings back your code, not your data.** Database rows and stored files stay as they are. If a change added or changed database tables, going back can break the app. Ask the builder to fix it afterwards.

---

## Step 1: Connect the builder to GitHub

A repository (repo) is your project's folder on GitHub.

Bolt:

1. Click the GitHub icon in Bolt.
2. Connect a repository.

v0:

1. Connect a repository from the branch menu next to **Publish**, at the top of the chat.
2. Follow the steps on the screen.

A branch is a separate line of changes inside a repo. v0 makes a new branch for each chat, the first time it changes code. When you click **Publish**, v0 merges that chat's changes into your main branch. With v0, versions are made on your main branch, each time you publish.

**You should see:** your project's code in a repository on GitHub.

---

## Step 2: Let GitHub save versions

A workflow is a small program that GitHub runs for you. This setting lets the versioning workflows save versions.

1. On GitHub, open your repo.
2. Click **Settings → Actions → General**.
3. Under **Workflow permissions**, choose **Read and write permissions**.
4. Click **Save**.

For v0, don't add an `AI_VERSIONS_BRANCH` variable. Every chat has its own branch, so one branch name would stop working at the next chat.

---

## Step 3: Add the 6 files

The files are in the copy-paste folder. To open one on your computer, right-click it and choose **Open with → Notepad** (Windows) or **TextEdit** (Mac).

Add the files in the order of the table. File 6 switches versioning on, so it goes last. For each file:

1. On GitHub, click **Add file → Create new file**.
2. Type the path from the table.
3. Paste the file's contents.
4. Click **Commit changes** (commit means save on GitHub).
5. Click **Commit changes** again in the box that opens.

| # | File in copy-paste | Path on GitHub |
|---|---|---|
| 1 | `1-pending.json` | `.ai-versions/pending.json` |
| 2 | `2-ai-version.mjs` | `.github/scripts/ai-version.mjs` |
| 3 | `3-ai-restore.mjs` | `.github/scripts/ai-restore.mjs` |
| 4 | `4-ai-restore.yml` | `.github/workflows/ai-restore.yml` |
| 5 | `5-VersionPill.tsx` | Bolt (Vite/React): `src/components/VersionPill.tsx`. v0 (Next.js): `components/VersionPill.tsx` |
| 6 | `6-ai-versions.yml` | `.github/workflows/ai-versions.yml` |

The **Actions** tab on GitHub shows each time a workflow runs.

**You should see:** after file 6, the **Actions** tab shows "AI Versions" with a green check. `v1.0.0` appears under **Releases**.

---

## Step 4: Give the builder the rules

Copy everything in `RULES.md`. Then paste it into the builder.

Bolt:

1. Open **Project settings → Knowledge**.
2. Paste the rules.

v0:

1. Click **+** in the prompt bar.
2. Click **Instructions → New Instruction**.
3. For the title, type `ai-versions`.
4. Paste the rules.
5. Keep the instruction checked.

> **Warning:** v0 saves instructions to your account. While this one is checked, it applies to **every** v0 project. Uncheck it in projects without versioning.

---

## Step 5: Add the version button

Send this message to the builder.

Bolt:

```text
In src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change src/components/VersionPill.tsx.
```

v0:

```text
In app/layout.tsx, add import VersionPill from "@/components/VersionPill"; and render <VersionPill /> once inside <body>, after {children}. Don't change components/VersionPill.tsx.
```

**You should see:** a small version button in the bottom-left of the preview. If it doesn't show, add `?versions=on` to the end of the preview address.

---

## Step 6: Try it

1. Ask for a small change, for example "make the heading blue".
2. Wait 1 to 2 minutes.
3. Open the version button. It should show a Small tweak.
4. To go back, ask in chat: "go back to v1.0.1".

---

## If something isn't right

| What you see | What to do |
|---|---|
| No "AI Versions" run in Actions | Check file 6's path. For v0, versions are made when you click **Publish**, so check that the change was published. |
| Red cross with "403" | Do Step 2. Then open the run and click **Re-run jobs**. |
| No version button | Send Step 5's message again, or add `?versions=on` to the preview address. |
| Button says "The version list isn't here yet" | Wait for a green check in Actions, then reopen the button. If the message stays, the builder may not be pulling (copying in) changes from GitHub. Please report it. |
| Going back doesn't change the code | The builder may not be pulling changes from GitHub. Use the builder's own history instead, and please report it. |

## Show your prompts in the button

By default, the version button does not show your prompts. This is because your live site serves the version list.

To show them, add a repository variable: on GitHub, click **Settings → Secrets and variables → Actions → Variables → New repository variable**. For the name, type `AI_VERSIONS_PILL_NOTES`. For the value, type `yes`.

Your prompts are always in the version tags (labels on each version) and release pages on GitHub.
