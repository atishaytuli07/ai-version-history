# Pro setup (with GitHub)

This takes about 15 minutes. You will change one GitHub setting, add 6 files to GitHub, and send Lovable one message.

Before you start, have these ready:

- Your Lovable project
- A GitHub account (GitHub is a website that stores code)
- The kit, unzipped (see "Get the kit" on the first page)

*Menu names in Lovable and GitHub can change. If a button has moved, look for the same words nearby.*

---

## Step 1: Connect Lovable to GitHub

*Skip this step if your project is already connected to GitHub.*

1. In Lovable, open your project.
2. Open **Settings → Connectors → GitHub**. Or click the GitHub button in the editor.
3. Follow the steps on the screen.

**You should see:** a new repository (repo) on GitHub with your project's code. A repo is your project's folder on GitHub.

---

## Step 2: Let GitHub save versions

1. On GitHub, open your repo.
2. Click **Settings → Actions → General**.
3. Scroll down to **Workflow permissions**.
4. Choose **Read and write permissions**.
5. Click **Save**.

Why this is needed: a small GitHub robot (called an Action) numbers your versions. It needs this permission to save them.

---

## Step 3: Add the 6 files

Add the files in the order of the table below. File 6 switches everything on, so it goes last.

For each file:

1. On your repo's main page, click **Add file → Create new file**.
2. In the name box, type the file's **name on GitHub** exactly. Typing `/` creates a folder.
3. Copy the file's contents (see how below).
4. Paste them into the big box.
5. Click **Commit changes** (commit means save on GitHub).
6. Click **Commit changes** again.

How to copy a file: in START-HERE.html, click **Show** under the table, then **Copy**. If you open the files yourself, right-click the file and choose **Open with → Notepad** (Windows) or **TextEdit** (Mac).

| # | File in copy-paste | Name on GitHub |
|---|---|---|
| 1 | `1-pending.json` | `.ai-versions/pending.json` |
| 2 | `2-ai-version.mjs` | `.github/scripts/ai-version.mjs` |
| 3 | `3-ai-restore.mjs` | `.github/scripts/ai-restore.mjs` |
| 4 | `4-ai-restore.yml` | `.github/workflows/ai-restore.yml` |
| 5 | `5-VersionPill.tsx` | `src/components/VersionPill.tsx` |
| 6 | `6-ai-versions.yml` | `.github/workflows/ai-versions.yml` |

<!-- file: copy-paste/1-pending.json -->
<!-- file: copy-paste/2-ai-version.mjs -->
<!-- file: copy-paste/3-ai-restore.mjs -->
<!-- file: copy-paste/4-ai-restore.yml -->
<!-- file: copy-paste/5-VersionPill.tsx -->
<!-- file: copy-paste/6-ai-versions.yml -->

**You should see:** after you add file 6, open the **Actions** tab in your repo. Within a minute, "AI Versions" gets a green check.

> **Red cross instead?** Do Step 2 again. Then open the failed run and click **Re-run jobs**.

---

## Step 4: Lock your versions (recommended)

Without this step, anyone with access to the repo can delete a version. With it, nobody can delete or change a version, not even you.

*Rulesets (GitHub's protection rules) on private repos need a paid GitHub plan. On the free plan, skip this step and back up regularly. Your versions stay until someone deletes them.*

1. On GitHub, open **Settings → Rules → Rulesets → New ruleset → New tag ruleset**.
2. For the name, type `protect versions`.
3. Set **Enforcement status** to **Active**.
4. Under **Target tags**, click **Add target → Include by pattern**.
5. Type `v*`.
6. Turn on **Restrict updates**, **Restrict deletions** and **Block force pushes**.
7. Leave **Restrict creations** off. If it is on, new versions can't be saved.
8. Click **Create**.

---

## Step 5: Teach Lovable the rules

1. In Lovable, open **Project Settings → Knowledge**.
2. Paste everything from `LOVABLE-KNOWLEDGE.md`.
3. Save.

<!-- file: LOVABLE-KNOWLEDGE.md -->

---

## Step 6: Add the version button

Send this message in Lovable's chat:

```text
In src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change src/components/VersionPill.tsx.
```

**You should see:** after about a minute, a small button like `v1.0.1` in the bottom-left corner of the preview. Click it to see your versions.

---

## Step 7: Try it

Send these messages to Lovable one at a time. After each one, wait about a minute. Then click the version button.

| Send this | The button should show |
|---|---|
| Make the heading blue | Small tweak |
| Add a pricing section with three plans | New feature |
| Redesign the whole site in a dark, minimal style | Big change |
| Go back to the version with the pricing section | Went back (takes 1 to 2 minutes) |
| *Change one line yourself in the code editor* | Small tweak |

> **Going back restores code, not data.** Database rows and uploaded files stay as they are. If a change added or changed database tables, going back can break the app, because the tables don't go back. If that happens, ask Lovable to fix it.

Your version numbers may be different. What matters is that every change shows up with a label that fits it.

---

## Done

For everyday use, see `HOW-TO-USE.md`. Two things to keep in mind:

- **Go back by asking in chat**, not with Lovable's History button. Chat keeps the versioning files up to date. Lovable's History also brings back old copies of those files, and that can stop versioning.
- **Going back to a version from before setup** makes the version button disappear, because that version didn't have the button yet. To bring it back, send Step 6's message again.

---

## If something isn't right

| What you see | What to do |
|---|---|
| No "AI Versions" run in the Actions tab | Check file 6's name. It must be `.github/workflows/ai-versions.yml` |
| A red cross with "403" | Do Step 2 again. Then open the failed run and click **Re-run jobs**. |
| A red cross that mentions "Restrict creations" | Turn **Restrict creations** off in Step 4's ruleset. Then click **Re-run jobs**. |
| No version button in the preview | Send Step 6's message again. Or add `?versions=on` to the end of the preview link. |
| The button says "The version list isn't here yet" | Wait a minute for the green check in Actions. Then open the button again. |
| Every change says "Small tweak" | Check that Step 5's text is saved in Knowledge. |
| Versioning stopped after you used Lovable's History | Add the 6 files again (Step 3). |

---

## Privacy

By default, the version button doesn't show your prompts. This is because your live site shows the version list at `your-site.com/ai-versions.json`, and anyone can read it.

To show your prompts in the button:

1. On GitHub, open **Settings → Secrets and variables → Actions → Variables → New repository variable**.
2. For the name, type `AI_VERSIONS_PILL_NOTES`.
3. For the value, type `yes`.

**Prompts are always saved in the version tags and release pages on GitHub.** On a public repo, anyone can read those. (Tags and releases are how GitHub stores each version.)

Extra entries in Lovable's History: after each change, you will see an "Update version list" entry. That's the robot updating the version button. It doesn't create a version.
