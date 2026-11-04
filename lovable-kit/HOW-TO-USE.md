# Using ai-versions every day

Work in Lovable as usual. Versions are made for you.

---

## See your versions

Click the version button in the bottom-left corner of your preview.

- The newest version is at the top, marked **Now**.
- Each version shows what changed and when (and your prompt, if you turned prompts on).
- Click a version to see the full date and time.

The dot on the left shows how big the change was:

| Dot | Label | Example |
|---|---|---|
| Large | Big change | Redesign, new layout, removed a feature |
| Medium | New feature | New section, page or form |
| Small | Small tweak | Color, text, small fix |
| Ring | Went back | You returned to an older version |

Visitors to your live site never see the button. To see it there yourself, add `?versions=on` to the end of the address. To hide it, add `?versions=off`.

---

## Go back to an older version

**Pro:** ask in Lovable's chat, for example:

```text
Go back to v3.4.5
```

You can also describe it: "go back to before the redesign". About 1 to 2 minutes later the preview shows that version.

**Lite:** ask Lovable which version you mean. It tells you the date and time, then open **History** and click **Restore** on that change.

Going back never deletes a version. It's saved as a new version, so you can undo it.

> **Going back restores code, not data.** Database rows and uploaded files stay as they are. If a change added or changed database tables, going back can break the app, because the tables aren't rolled back. Ask Lovable to fix it afterwards.

---

## What happens after you go back

Say you're on **v7.0.0** and go back to **v3.4.5**:

```text
v7.0.0   Big change    your latest work
v7.1.0   Went back     the code of v3.4.5
v7.1.1   Small tweak   your next change          "Built on v3.4.5"
v7.2.0   New feature   the change after that     "Built on v3.4.5"
```

- **Numbers keep going up.** The newest version always has the highest number.
- **"Built on v3.4.5"** under a version tells you it continues from v3.4.5, not from v7.0.0.
- **v4 to v7 are still there.** To return to v7.0.0 later, just ask: "go back to v7.0.0". That's saved as a new version too.

---

## Compare two versions (Pro)

Usually the summaries in the version button are enough. To see every changed line, open your repo on GitHub, click **Releases**, open a version, and click its **Compare** link.

---

## The label is wrong?

Tell Lovable, for example: "That last change was a big change." It applies that to similar changes from now on. Old versions stay as they are; that's on purpose.

---

## Three things to remember

1. **Avoid going back to a version from before setup** (older than **Start**, at the bottom of the list). In Pro, the version button disappears until you add it again (Pro setup, Step 6). In Lite, you need to redo Lite setup Steps 3 and 4.
2. **Going back restores code, not data.** Database rows and uploaded files stay as they are.
3. **Don't edit the versioning files**, and don't let Lovable change them: `VersionPill.tsx`, and the `.github` and `.ai-versions` folders (Pro) or `ai-versions-store.ts` and the `ai_versions` table (Lite).
