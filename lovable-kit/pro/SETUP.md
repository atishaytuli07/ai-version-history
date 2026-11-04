# Pro setup (with GitHub)

About 15 minutes. You'll change one GitHub setting, add 6 files to GitHub, and send Lovable one message.

**Before you start, have ready:**

- Your Lovable project
- A GitHub account
- The kit, unzipped (see **Get the kit** on the first page)

*Menu names checked on 28 Oct 2026. If a button has moved, look for the same words nearby.*

---

## Step 1: Connect Lovable to GitHub

*Skip this if your project is already connected.*

1. In Lovable, open your project.
2. Open **Settings → Connectors → GitHub** (or click the GitHub button in the editor) and follow the steps.

**You should see:** a new repository (repo) on GitHub with your project's code. A repo is your project's folder on GitHub.

---

## Step 2: Let GitHub save versions

1. On GitHub, open your repo.
2. Click **Settings → Actions → General**.
3. Scroll to **Workflow permissions**, choose **Read and write permissions**, and click **Save**.

**Why:** a small GitHub robot (called an Action) numbers your versions. It needs this permission to save them.

---

## Step 3: Add the 6 files

For each file below:

1. On your repo's main page, click **Add file → Create new file**.
2. In the name box, type the **name on GitHub** exactly. Typing `/` creates a folder.
3. Copy the file's contents and paste them into the big box. In START-HERE.html, click **Show** under the table, then **Copy**. If you open the files yourself, right-click them and choose **Open with → Notepad** (Windows) or **TextEdit** (Mac).
4. Click **Commit changes**, then **Commit changes** again.

Add them **in this order**. File 6 switches everything on, so it goes last.

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

**You should see:** after file 6, open the **Actions** tab. Within a minute, "AI Versions" gets a green check.

> **Red cross instead?** Do Step 2 again, then open the failed run and click **Re-run jobs**.

---

## Step 4: Lock your versions (recommended)

Without this, a version can be deleted by anyone with access to the repo. With it, nobody can delete or change a version, including you.

1. On GitHub: **Settings → Rules → Rulesets → New ruleset → New tag ruleset**.
2. Name: `protect versions`. Enforcement status: **Active**.
3. Under **Target tags**, click **Add target → Include by pattern**, type `v*`.
4. Turn on **Restrict updates**, **Restrict deletions** and **Block force pushes**.
5. Leave **Restrict creations** off. With it on, new versions can't be saved.
6. Click **Create**.

*Rulesets on private repos need a paid GitHub plan. On the free plan, skip this step and back up regularly: your versions stay until someone deletes them.*

---

## Step 5: Teach Lovable the rules

1. In Lovable, open **Project Settings → Knowledge**.
2. Paste everything from `LOVABLE-KNOWLEDGE.md` and save.

<!-- file: LOVABLE-KNOWLEDGE.md -->

---

## Step 6: Add the version button

Send this message in Lovable's chat:

```text
In src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change src/components/VersionPill.tsx.
```

**You should see:** about a minute later, a small button like `v1.0.1` in the bottom-left corner of the preview. Click it to see your versions.

---

## Step 7: Try it

Send these to Lovable one at a time. After each, wait about a minute and click the version button.

| Send this | The button should show |
|---|---|
| Make the heading blue | Small tweak |
| Add a pricing section with three plans | New feature |
| Redesign the whole site in a dark, minimal style | Big change |
| Go back to the version with the pricing section | Went back (takes 1 to 2 minutes) |
| *Change one line yourself in the code editor* | Small tweak |

> **Going back restores code, not data.** Database rows and uploaded files stay as they are. If a change added or changed database tables, going back can break the app, because the tables aren't rolled back. Ask Lovable to fix it afterwards.

The exact numbers can differ. What matters is that every change shows up with a sensible label.

---

## Done

For everyday use, see `HOW-TO-USE.md`. Two things to keep in mind:

- **Go back by asking in chat**, not with Lovable's History button. Chat keeps the versioning files up to date. Lovable's History brings back old copies of them too, which can stop versioning.
- **Going back to a version from before setup** makes the version button disappear, because that version didn't have it yet. Send Step 6's message again to bring it back.

---

## If something isn't right

| What you see | What to do |
|---|---|
| No "AI Versions" run in the Actions tab | Check file 6's name: `.github/workflows/ai-versions.yml` |
| Red cross with "403" | Do Step 2, then **Re-run jobs** |
| Red cross mentioning "Restrict creations" | Turn that off in Step 4's ruleset, then **Re-run jobs** |
| No version button in the preview | Send Step 6's message again, or add `?versions=on` to the end of the preview link |
| The button says "The version list isn't here yet" | Wait a minute for the green check in Actions, then open the button again |
| Every change says "Small tweak" | Check that Step 5's text is saved in Knowledge |
| Versioning stopped after using Lovable's History | Add the 6 files again (Step 3) |

---

## Privacy

- **Your prompts aren't shown in the version button by default**, because your live site serves the version list at `your-site.com/ai-versions.json` for anyone to read.
- **To show them:** on GitHub, **Settings → Secrets and variables → Actions → Variables → New repository variable**. Name `AI_VERSIONS_PILL_NOTES`, value `yes`.
- **Prompts are always saved in the version tags and release pages on GitHub.** On a public repo, anyone can read those.
- **Extra entries in Lovable's History.** After each change you'll see an "Update version list" entry. That's the robot updating the version button; it doesn't create a version.
