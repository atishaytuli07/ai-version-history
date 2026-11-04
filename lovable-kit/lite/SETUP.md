# Lite setup (no GitHub)

About 10 minutes, all inside Lovable. You'll send Lovable three messages and paste one block of text.

Your versions are saved in your project's database. Going back to old code in Lovable doesn't touch the database, so the version list survives a restore.

**Is Lite right for this project?** The app reads and adds versions with its public key, and that key is in every copy of your published app. So anyone can read your version list (version numbers, summaries and dates) and add versions to it. The database blocks the worst cases: a new version must be the next number, texts are short, at most 20 a minute, and nobody can change or delete versions from the app. Prompts aren't saved. For anything private, use Pro.

**Before you start, have ready:**

- Your Lovable project
- The kit, unzipped (see **Get the kit** on the first page)

*Menu names checked on 28 Oct 2026. If a button has moved, look for the same words nearby.*

---

## Step 1: Turn on the database

1. In Lovable, open your project's **Database** view.
2. If you see an **Enable** button, click it. If you already have a database, skip this step.

---

## Step 2: Create the versions table

Send this message in Lovable's chat, and paste the contents of `1-ai-versions-table.sql` right under it:

```text
Create a database table for version history using exactly this SQL. Keep the trigger and the row level security policies exactly as written.
```

<!-- file: copy-paste/1-ai-versions-table.sql -->

Lovable may warn that anyone can read or add rows to `ai_versions`. That's true, and it's what's described at the top of this page. The SQL limits what can be added; it can't make the list private.

*If Lovable won't run it:* open **Manage → SQL editor**, paste the same SQL, and click **Run**.

**You should see:** an `ai_versions` table in the Database view.

---

## Step 3: Add two small files

Send this message, and paste the contents of `2-ai-versions-store.ts` and `3-ai-version.ts` under it, each with its file name on the line above:

```text
Create these two files with exactly this content: src/lib/ai-versions-store.ts and src/ai-version.ts. In ai-versions-store.ts, if this project's database client isn't exported as supabase from @/integrations/supabase/client, change only that import line to use this project's client. Don't change anything else.
```

<!-- file: copy-paste/2-ai-versions-store.ts -->
<!-- file: copy-paste/3-ai-version.ts -->

*Copying from the files yourself? Right-click and choose **Open with → Notepad** (Windows) or **TextEdit** (Mac).*

---

## Step 4: Add the version button

Send this message, and paste the contents of `4-VersionPill.tsx` under it:

```text
Create src/components/VersionPill.tsx with exactly this content. Then in src/App.tsx, add import VersionPill from "./components/VersionPill"; and render <VersionPill /> once, just before the closing tag of the outermost element that App returns. Don't change the content of VersionPill.tsx.
```

<!-- file: copy-paste/4-VersionPill.tsx -->

**You should see:** when the preview reloads, a small button in the bottom-left corner. Click it: it shows **v1.0.0, Start**.

---

## Step 5: Teach Lovable the rules

1. Open **Project Settings → Knowledge**.
2. Paste everything from `LOVABLE-KNOWLEDGE.md` and save.

<!-- file: LOVABLE-KNOWLEDGE.md -->

Do this last. If Lovable has the rules earlier, it may change the files from Steps 3 and 4.

---

## Step 6: Try it

Send these one at a time. After each, click the version button. New versions show up as soon as the preview reloads.

| Send this | The button should show |
|---|---|
| Make the heading blue | Small tweak |
| Add a pricing section with three plans | New feature |
| Redesign the whole site in a dark, minimal style | Big change |
| *In History, click Restore on the pricing section change* | Went back |

> **Going back restores code, not data.** Database rows and uploaded files stay as they are. If a change added or changed database tables, going back can break the app, because the tables aren't rolled back. Ask Lovable to fix it afterwards.

The exact numbers can differ. What matters is that every change shows up with a sensible label.

---

## Done

For everyday use, see `HOW-TO-USE.md`. One thing to keep in mind:

- **Don't go back to a version from before setup** (older than **Start**). That removes the version button and its files. If it happens, do Steps 3 and 4 again; your versions are still in the database.

---

## If something isn't right

| What you see | What to do |
|---|---|
| No version button in the preview | Send Step 4's message again, or add `?versions=on` to the end of the preview link |
| "Can't reach the versions table" | Check Step 2: is `ai_versions` in the Database view? |
| Lovable reports a type error about `ai_versions` | Send: "Regenerate the database types and fix the type error in src/lib/ai-versions-store.ts" |
| A change is missing from the list | Lovable's AI forgot to describe it. Send: "Update src/ai-version.ts for the change you just made." |
| Every change says "Small tweak" | Check that Step 5's text is saved in Knowledge |
| "too many new versions in one minute" | Someone (or a loop) added many versions quickly. Wait a minute. To remove unwanted rows, use **Manage → SQL editor**. |

---

## Good to know

- **Versions are saved when the preview loads.** That happens right after every change. If you change something with the preview closed, the version appears the next time you open it. Your published site only reads the list; it never adds versions.
- **Going back never deletes a version.** The list stays until you delete it. Deleting the project, or its database, deletes the list too.
