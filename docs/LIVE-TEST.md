# Live test: Bolt and v0

About 45 minutes per builder. Use a **new throwaway project**, not a real one. Fill in the results table at the end and keep the screenshots: they decide whether Bolt and v0 can lose the "beta" label.

**What we're really checking.** The versioning works in simulation. These tests check the four things only a real builder can show:

1. Does the builder pull our robot's commits from GitHub (the version list, and a restore)?
2. Does the builder's AI follow the rules (write `pending.json` with each change, and only `restore.json` when asked to go back)?
3. Does the version button show up in the builder's preview?
4. When the builder and the robot change things at the same moment, does the builder overwrite the robot's work?

---

## Bolt

### Set up (about 10 minutes)

1. In Bolt, create a project: "A one-page site for a bakery called Crumb & Co, React + Vite."
2. Click the GitHub icon in Bolt and connect it to a **new** repository.

**You should see:** a repo on GitHub with the code, on branch `main`.

3. On GitHub: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**
4. Add the 6 files from the repo's `github-layer/copy-paste` folder, the same way as the Lovable Pro setup (Step 3), file 6 last. Use the path for file 5 listed in `github-layer/README.md`.

**You should see:** the Actions tab shows "AI Versions" with a green check, and `v1.0.0` under Releases.

5. Wait 1 minute. **Check:** do the new files appear in Bolt's file tree? (Bolt pulls changes from GitHub regularly.)
6. In Bolt: **Project settings → Knowledge**. Paste the text from `github-layer/RULES.md`.
7. Send Bolt this message:

```text
In src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change src/components/VersionPill.tsx.
```

**Check:** the version button appears in the bottom-left of Bolt's preview. If it doesn't, add `?versions=on` to the preview address and note that.

### Tests (about 15 minutes)

After each, wait 1 to 2 minutes, then check GitHub **Releases** and the version button.

| # | Do this in Bolt | Pass if |
|---|---|---|
| B1 | "Make the heading blue" | A new version labeled Small tweak. Also open `.ai-versions/pending.json` in the repo on GitHub: it describes the blue heading |
| B2 | "Add a menu section with 4 items and prices" | A new version labeled New feature |
| B3 | Change one line yourself in Bolt's code editor | A new version labeled Small tweak, even though the AI wrote nothing |
| B4 | "Go back to v1.0.1" (use a number from the button) | Bolt's code goes back within about 2 minutes; button shows Went back; `restore.json` is gone |
| B5 | "Go back to v9.9.9" | No new version; the button shows a notice that v9.9.9 doesn't exist |
| B6 | Make one more change right after B4 | It's numbered after the restore and shows "Built on v1.0.1" |
| B7 | Use Bolt's own version history to restore an older version | GitHub gets a new commit, and it's versioned as Went back |
| B8 | Look at GitHub's commit list | No loop: no new commits for 5 minutes after your last change |

**Watch for in B4:** Bolt says it keeps its own changes when both sides change at once. If Bolt's code doesn't go back, or goes back and then returns to the newer code, note exactly what you saw. That's the biggest risk for Bolt.

---

## v0

v0 commits to its own branch (named like `v0/main-abc123`), not to `main`. The version files have to live on that branch.

### Set up (about 10 minutes)

1. In v0, create a project: "A one-page site for a bakery called Crumb & Co."
2. Open v0's **Git** panel and connect a **new** GitHub repository. Write down the branch name v0 shows (for example `v0/main-abc123`).
3. On GitHub: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**
4. On GitHub: **Settings → Secrets and variables → Actions → Variables → New repository variable**. Name: `AI_VERSIONS_BRANCH`. Value: the branch name from step 2.
5. On GitHub, switch to **v0's branch** with the branch menu at the top left of the code view. **Add file → Create new file** then saves to the branch you're viewing. Add the 6 files from `github-layer/copy-paste`, file 6 last. **Put file 5 at** `components/VersionPill.tsx` (v0 projects keep components at the root).

**You should see:** the Actions tab shows "AI Versions" with a green check, and `v1.0.0` under Releases.

6. **Check:** do the new files appear in v0 within a minute or two? If v0 never pulls them, stop here and note it: everything below depends on it.
7. In v0: click **+** in the prompt bar → **Instructions → New Instruction**. Title: `ai-versions`. Paste the text from `github-layer/RULES.md`. Make sure the instruction is checked.
8. Send v0 this message:

```text
In app/layout.tsx, add import VersionPill from "@/components/VersionPill"; and render <VersionPill /> once inside <body>, after {children}. Don't change components/VersionPill.tsx.
```

**Check:** the version button appears in v0's preview. If not, add `?versions=on` to the preview address and note that.

### Tests (about 15 minutes)

| # | Do this in v0 | Pass if |
|---|---|---|
| V1 | "Make the heading blue" | A new version labeled Small tweak |
| V2 | "Add a menu section with 4 items and prices" | A new version labeled New feature |
| V3 | "Go back to v1.0.1" | v0's code goes back within about 2 minutes; button shows Went back |
| V4 | "Go back to v9.9.9" | No new version; the button shows a notice |
| V5 | One more change after V3 | Numbered after the restore, "Built on v1.0.1" |
| V6 | On GitHub, click **Pull requests → New pull request**, choose base `main` and compare v0's branch, click **Create pull request**, then **Merge pull request** | No red cross in Actions; no new versions appear for the merge |
| V7 | Look at the commit list on v0's branch | No loop: no new commits for 5 minutes after your last change |

**Watch for:** if v0 doesn't pull commits made on GitHub, V3 can't work in v0 (the restore never reaches it), and the version button won't update. In that case v0 can still be versioned, but going back would have to be done in v0 itself. Note it; we'd change the docs for v0.

---

## Results

Write **Pass**, **Fail** or **N/A** in each cell. Add a screenshot for every Fail.

| Test | Bolt | v0 | Notes / screenshot |
|---|---|---|---|
| Builder pulls robot commits (set-up step 5 or 6) | | | |
| Version button shows in preview | | | |
| Small tweak (B1, V1) | | | |
| New feature (B2, V2) | | | |
| Edit by hand gets a version (B3) | | N/A | |
| Go back by chat (B4, V3) | | | |
| Unknown version notice (B5, V4) | | | |
| Built on label (B6, V5) | | | |
| Builder's own restore detected (B7) | | N/A | |
| Merge to main is quiet (V6) | N/A | | |
| No commit loop (B8, V7) | | | |

**Bolt or v0 can drop the "beta" label when:** the builder pulls robot commits, go-back-by-chat works, and nothing loops. Everything else can be a documented limitation.
