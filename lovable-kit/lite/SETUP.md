# Lite setup (no GitHub)

This takes about 10 minutes, all inside Lovable. You will send Lovable three messages and paste one block of text.

Your versions are saved in your project's database (the place where your app keeps its data). When you go back to old code in Lovable, the database doesn't change. So your version list stays after a restore.

**Is Lite right for this project?** Read this first.

Your app reads and adds versions with its public key (the key your app uses to reach its database). This key is in every copy of your published app. So anyone can read your version list (version numbers, summaries and dates). Anyone can also add versions to it.

The database blocks the worst cases:

- A new version must have the next number.
- Texts must be short.
- At most 20 new versions can be added in a minute.
- Nobody can change or delete versions from the app.

Prompts aren't saved. For anything private, use Pro.

Before you start, have these ready:

- Your Lovable project
- The kit, unzipped (see "Get the kit" on the first page)

*Menu names in Lovable and GitHub can change. If a button has moved, look for the same words nearby.*

---

## Step 1: Turn on the database

If your project already has a database, skip this step.

1. In Lovable, open your project's **Database** view.
2. If you see an **Enable** button, click it.

---

## Step 2: Create the versions table

Send this message in Lovable's chat. Right under it, in the same message, paste the contents of `1-ai-versions-table.sql`.

```text
Create a database table for version history using exactly this SQL. Keep the trigger and the row level security policies exactly as written.
```

<!-- file: copy-paste/1-ai-versions-table.sql -->

Lovable may warn that anyone can read or add rows (entries) to `ai_versions`. That's true. It is the risk described at the top of this page. The SQL (the database commands in the file) limits what can be added. It can't make the list private.

If Lovable won't run the SQL:

1. Open **Manage → SQL editor**.
2. Paste the same SQL.
3. Click **Run**.

**You should see:** an `ai_versions` table in the Database view.

---

## Step 3: Add two small files

Send this message. Under it, paste the contents of `2-ai-versions-store.ts` and `3-ai-version.ts`. Put each file's name on the line above its contents.

```text
Create these two files with exactly this content: src/lib/ai-versions-store.ts and src/ai-version.ts. In ai-versions-store.ts, if this project's database client isn't exported as supabase from @/integrations/supabase/client, change only that import line to use this project's client. Don't change anything else.
```

<!-- file: copy-paste/2-ai-versions-store.ts -->
<!-- file: copy-paste/3-ai-version.ts -->

Copying from the files yourself? Right-click the file and choose **Open with → Notepad** (Windows) or **TextEdit** (Mac).

---

## Step 4: Add the version button

Send this message. Under it, paste the contents of `4-VersionPill.tsx`.

```text
Create src/components/VersionPill.tsx with exactly this content. Then render <VersionPill /> once in the app's root layout, so it shows on every page, and add the import for it there. In apps with src/routes/__root.tsx, put it in the root route next to <Outlet />. In older apps with src/App.tsx, put it just before the closing tag of the outermost element that App returns. Don't change the content of VersionPill.tsx.
```

<!-- file: copy-paste/4-VersionPill.tsx -->

**You should see:** a small button in the bottom-left corner after the preview reloads. Click it. It shows "v1.0.0, Start".

---

## Step 5: Teach Lovable the rules

1. In Lovable, open **Project settings → Instructions**.
2. Paste everything from `LOVABLE-KNOWLEDGE.md`.
3. Save.

<!-- file: LOVABLE-KNOWLEDGE.md -->

Do this step last. If Lovable gets the rules earlier, it may change the files from Steps 3 and 4.

---

## Step 6: Try it

Send these messages one at a time. After each one, click the version button. New versions show up as soon as the preview reloads.

| Send this | The button should show |
|---|---|
| Make the heading blue | Small tweak |
| Add a pricing section with three plans | New feature |
| Redesign the whole site in a dark, minimal style | Big change |
| *In History, click Revert on the pricing section change* | Went back |

> **Going back restores code, not data.** Database rows and uploaded files stay as they are. If a change added or changed database tables, going back can break the app, because the tables don't go back. If that happens, ask Lovable to fix it.

Your version numbers may be different. What matters is that every change shows up with a label that fits it.

---

## Done

For everyday use, see `HOW-TO-USE.md`. One thing to keep in mind:

- **Don't go back to a version from before setup** (older than "Start"). That removes the version button and its files. If it happens, do Steps 3 and 4 again. Your versions are still in the database.

---

## If something isn't right

| What you see | What to do |
|---|---|
| No version button in the preview | Send Step 4's message again. Or add `?versions=on` to the end of the preview link. |
| A message that says "Can't reach the versions table" | Check Step 2. Open the Database view. Is the `ai_versions` table there? |
| Lovable reports a type error about `ai_versions` | Send: "Regenerate the database types and fix the type error in src/lib/ai-versions-store.ts" |
| A change is missing from the list | Lovable's AI forgot to describe it. Send: "Update src/ai-version.ts for the change you just made." |
| Every change says "Small tweak" | Check that Step 5's text is saved in Instructions. |
| A message that says "too many new versions in one minute" | Someone (or some code running over and over) added many versions quickly. Wait a minute. To remove unwanted rows, use **Manage → SQL editor**. |

---

## Good to know

- Versions are saved when the preview loads. That happens right after every change. If you change something while the preview is closed, the version appears the next time you open the preview.
- Your published site only reads the list. It never adds versions.
- Going back never deletes a version. The list stays until you delete it. If you delete the project or its database, the list is deleted too.
