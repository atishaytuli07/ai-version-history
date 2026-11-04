# Live test: Bolt and v0

This takes about 45 minutes per builder. Use a **new throwaway project**, not a real one.

Fill in the results table at the end. Keep the screenshots. They decide whether Bolt and v0 can lose the "beta" label.

## What we're checking

The versioning works in simulation (our automated tests). These tests check the four things only a real builder can show.

Words used below:

- A commit is one saved change on GitHub.
- The robot is the GitHub workflow that saves versions. A workflow is a small program GitHub runs for you.

The four questions:

1. Does the builder pull (copy in) our robot's commits from GitHub? These commits carry the version list, and a restore.
2. Does the builder's AI follow the rules? It should write `pending.json` with each change. When asked to go back, it should write only `restore.json`.
3. Does the version button show up in the builder's preview?
4. The builder and the robot may change things at the same moment. When that happens, does the builder overwrite the robot's work?

---

## Bolt

### Set up (about 20 minutes)

1. In Bolt, create a project: "A one-page site for a bakery called Crumb & Co, React + Vite."
2. Click the GitHub icon in Bolt.
3. Connect it to a **new** repository. A repository (repo) is a project's folder on GitHub.

**You should see:** a repo on GitHub with the code, on branch `main`. A branch is a separate line of changes inside a repo.

4. On GitHub: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**
5. Add the 6 files from the repo's `github-layer/copy-paste` folder. Follow Step 3 of `github-layer/README.md`, file 6 last. For file 5, use the path listed in `github-layer/README.md`.

**You should see:** the Actions tab (where GitHub shows each workflow run) shows "AI Versions" with a green check. `v1.0.0` is under Releases.

6. Wait 1 minute.
7. **Check:** do the new files appear in Bolt's file tree? Bolt pulls changes from GitHub regularly.
8. In Bolt, open **Project settings → Knowledge**.
9. Paste the text from `github-layer/RULES.md`.
10. Send Bolt this message:

```text
In src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change src/components/VersionPill.tsx.
```

**Check:** the version button appears in the bottom-left of Bolt's preview. If it doesn't, add `?versions=on` to the preview address and note that.

### Tests (about 25 minutes, mostly waiting)

After each test, wait 1 to 2 minutes. Then check GitHub **Releases** and the version button.

#### B1. Small tweak

- Do this: send Bolt "Make the heading blue". Then open `.ai-versions/pending.json` in the repo on GitHub.
- You should see: a new version, and the file describes the blue heading.
- Pass if: the new version is labeled Small tweak, and the file describes the blue heading.
- Fail if: there is no new version, it has another label, or the file doesn't describe the blue heading.

#### B2. New feature

- Do this: send Bolt "Add a menu section with 4 items and prices".
- You should see: a new version.
- Pass if: it is labeled New feature.
- Fail if: there is no new version, or it has another label.

#### B3. Edit by hand

- Do this: change one line yourself in Bolt's code editor.
- You should see: a new version, even though the AI wrote nothing.
- Pass if: it is labeled Small tweak.
- Fail if: there is no new version, or it has another label.

#### B4. Go back by chat

- Do this: send Bolt "Go back to v1.0.1". Use a version number from the button.
- You should see: Bolt's code goes back to that version.
- Pass if: Bolt's code goes back within about 2 minutes, the button shows Went back, and `restore.json` is gone.
- Fail if: the code doesn't go back, it goes back and then returns to the newer code, the button doesn't show Went back, or the file is still there.

> **Watch for in B4:** Bolt says it keeps its own changes when both sides change at once. If Bolt's code doesn't go back, or goes back and then returns to the newer code, note exactly what you saw. That's the biggest risk for Bolt.

#### B5. Unknown version

- Do this: send Bolt "Go back to v9.9.9".
- You should see: a notice in the version button.
- Pass if: there is no new version, and the notice says v9.9.9 doesn't exist.
- Fail if: a new version appears, or there is no notice.

#### B6. Built on label

- Do this: make one more change right after B4.
- You should see: a new version.
- Pass if: it's numbered after the restore and shows "Built on v1.0.1".
- Fail if: it isn't numbered after the restore, or "Built on v1.0.1" is missing.

#### B7. Bolt's own restore

- Do this: use Bolt's own version history to restore an older version.
- You should see: a new commit on GitHub.
- Pass if: GitHub gets a new commit, and it's versioned as Went back.
- Fail if: there is no new commit, or it isn't versioned as Went back.

#### B8. No commit loop

- Do this: look at GitHub's commit list.
- You should see: the list stops growing after your last change.
- Pass if: there are no new commits for 5 minutes after your last change.
- Fail if: new commits keep appearing. That is a loop.

---

## v0

v0 makes a new branch for each chat and merges it into `main` when you click **Publish**. So with v0, versions are made on `main`, once per publish. The version files live on `main`.

### Set up (about 20 minutes)

1. In v0, create a project: "A one-page site for a bakery called Crumb & Co."
2. Open the branch menu next to **Publish**, at the top of the chat.
3. Connect a **new** GitHub repository.
4. On GitHub: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**
5. Don't add an `AI_VERSIONS_BRANCH` variable.
6. On GitHub, stay on `main`. Add the 6 files from `github-layer/copy-paste` there, file 6 last, following Step 3 of `github-layer/README.md`. **Put file 5 at** `components/VersionPill.tsx`. v0 projects keep components at the root.

**You should see:** the Actions tab shows "AI Versions" with a green check. `v1.0.0` is under Releases.

7. **Check:** start a new chat in v0 from `main`. Do the new files appear? If v0 never picks them up, stop here and note it. Everything below depends on it.
8. In v0, click **+** in the prompt bar, then **Instructions → New Instruction**.
9. For the title, type `ai-versions`.
10. Paste the text from `github-layer/RULES.md`.
11. Make sure the instruction is checked.
12. Send v0 this message, then click **Publish**:

```text
In app/layout.tsx, add import VersionPill from "@/components/VersionPill"; and render <VersionPill /> once inside <body>, after {children}. Don't change components/VersionPill.tsx.
```

**Check:** the version button appears in v0's preview. If not, add `?versions=on` to the preview address and note that.

### Tests (about 25 minutes, mostly waiting)

After each change, click **Publish**. Then wait 1 to 2 minutes and check GitHub **Releases** and the version button.

#### V1. Small tweak

- Do this: send v0 "Make the heading blue".
- You should see: a new version.
- Pass if: it is labeled Small tweak.
- Fail if: there is no new version, or it has another label.

#### V2. New feature

- Do this: send v0 "Add a menu section with 4 items and prices".
- You should see: a new version.
- Pass if: it is labeled New feature.
- Fail if: there is no new version, or it has another label.

#### V3. Go back by chat

- Do this: send v0 "Go back to v1.0.1", then click **Publish**.
- You should see: the code on `main` goes back to that version.
- Pass if: the code goes back within about 2 minutes of publishing, and the button shows Went back.
- Fail if: the code doesn't go back, or the button doesn't show Went back.

#### V4. Unknown version

- Do this: send v0 "Go back to v9.9.9".
- You should see: a notice in the version button.
- Pass if: there is no new version, and the button shows a notice.
- Fail if: a new version appears, or there is no notice.

#### V5. Built on label

- Do this: make one more change after V3.
- You should see: a new version.
- Pass if: it's numbered after the restore and shows "Built on v1.0.1".
- Fail if: it isn't numbered after the restore, or "Built on v1.0.1" is missing.

#### V6. One version per publish

- Do this: in one chat, send v0 two small changes, then click **Publish** once.
- You should see: v0 merges the chat into `main`. Then look at the Actions tab and Releases.
- Pass if: there is no red cross in Actions, and the publish made new versions for the changes.
- Fail if: Actions shows a red cross, or no version appears for the publish.

#### V7. No commit loop

- Do this: look at the commit list on `main`.
- You should see: the list stops growing after your last change.
- Pass if: there are no new commits for 5 minutes after your last change.
- Fail if: new commits keep appearing. That is a loop.

> **Watch for:** v0 may not pull commits made on GitHub. If so, V3 can't work in v0, because the restore never reaches it. The version button won't update either. v0 can still be versioned, but going back would have to be done in v0 itself. Note it; we'd change the docs for v0.

---

## Results

Write **Pass**, **Fail** or **N/A** (not applicable) in each cell. Add a screenshot for every Fail.

| Test | Bolt | v0 | Notes / screenshot |
|---|---|---|---|
| Builder pulls robot commits (Bolt set-up step 7, v0 set-up step 7) | | | |
| Version button shows in preview | | | |
| Small tweak (B1, V1) | | | |
| New feature (B2, V2) | | | |
| Edit by hand gets a version (B3) | | N/A | |
| Go back by chat (B4, V3) | | | |
| Unknown version notice (B5, V4) | | | |
| Built on label (B6, V5) | | | |
| Builder's own restore detected (B7) | | N/A | |
| One version per publish (V6) | N/A | | |
| No commit loop (B8, V7) | | | |

**Bolt or v0 can drop the "beta" label when** all three of these pass:

- the builder pulls robot commits
- go back by chat works
- nothing loops

Everything else can be a documented limitation (a known problem we write down in the docs).
