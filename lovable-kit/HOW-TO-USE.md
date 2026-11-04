# Using ai-versions every day

Work in Lovable as usual. Your versions are made for you.

---

## See your versions

Click the version button in the bottom-left corner of your preview.

- The newest version is at the top. It is marked "Now".
- Each version shows what changed and when. If you turned prompts on (Pro setup, Privacy), it also shows your prompt.
- Click a version to see the full date and time.

The dot on the left shows how big the change was:

| Dot | Label | Example |
|---|---|---|
| Large | Big change | Redesign, new layout, removed a feature |
| Medium | New feature | New section, page or form |
| Small | Small tweak | Color, text, small fix |
| Ring | Went back | You returned to an older version |

Visitors to your live site (your published app) never see the button. To see it there yourself, add `?versions=on` to the end of the web address. To hide it again, add `?versions=off`.

---

## Go back to an older version

**Pro:** ask in Lovable's chat. For example:

```text
Go back to v3.4.5
```

You can also describe the version, like "go back to before the redesign". After about 1 to 2 minutes, the preview shows that version.

**Lite:** use Lovable's History.

1. Tell Lovable which version you want. Lovable tells you the date and time of that change.
2. In Lovable, open **History**.
3. Find the change with that date and time, and click **Restore**.

Going back never deletes a version. Going back is saved as a new version, so you can undo it.

> **Going back restores code, not data.** Database rows and uploaded files stay as they are. If a change added or changed database tables, going back can break the app, because the tables don't go back. If that happens, ask Lovable to fix it.

---

## What happens after you go back

Example: you are on v7.0.0 and you go back to v3.4.5. Your list then looks like this:

```text
v7.0.0   Big change    your latest work
v7.1.0   Went back     the code of v3.4.5
v7.1.1   Small tweak   your next change          "Built on v3.4.5"
v7.2.0   New feature   the change after that     "Built on v3.4.5"
```

- Numbers keep going up. The newest version always has the highest number.
- "Built on v3.4.5" under a version means it continues from v3.4.5, not from v7.0.0.
- v4 to v7 are still there. To return to v7.0.0 later, ask Lovable: "go back to v7.0.0". This is also saved as a new version.

---

## Compare two versions (Pro)

Usually the summaries in the version button are enough. To see every line that changed:

1. On GitHub, open your repo (your project's folder on GitHub).
2. Click **Releases**.
3. Open a version.
4. Click its **Compare** link.

---

## The label is wrong?

Tell Lovable. For example: "That last change was a big change." Lovable then uses that label for similar changes from now on. Old versions keep their labels. This is on purpose.

---

## Three things to remember

1. **Avoid going back to a version from before setup.** These versions are older than "Start", at the bottom of the list. In Pro, the version button disappears until you add it again (Pro setup, Step 6). In Lite, you need to do Lite setup Steps 3 and 4 again.
2. **Going back restores code, not data.** Database rows and uploaded files stay as they are.
3. **Don't edit the versioning files**, and don't let Lovable change them. In both setups: `VersionPill.tsx`. In Pro: the `.github` and `.ai-versions` folders. In Lite: `ai-versions-store.ts` and the `ai_versions` table.
