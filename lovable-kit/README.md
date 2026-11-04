# Version history for Lovable

Every change you make in Lovable gets a version number, like v2.4.1.

A small button in your preview lists your versions: what changed and when. You can go back to any version. Going back is saved as a new version, so you can undo it too.

![The version button, opened](pill-preview.png)

## What the numbers mean

Take v2.4.1:

- The first number (2) goes up for a big change, like a redesign.
- The second number (4) goes up for a new feature, like a new page or section.
- The last number (1) goes up for a small fix, like new text or a color.

When you go back to an older version, the middle number goes up. Your newer versions are all still there.

## Choose a setup

**Lite** needs no GitHub. It takes about 10 minutes, all inside Lovable.

- Good for trying it out on personal or small projects.
- To go back, you use Lovable's History. The version button tells you which change to pick.
- If Lovable forgets to describe a change, that change gets no version. Your code is still in Lovable's History.
- Your version list is stored in your app's database. Anyone with your app's public key can read it and add to it, so don't use Lite for anything private.

**Pro** uses GitHub. It takes about 15 minutes.

- Every change gets a version, even if Lovable forgets to describe it.
- To go back, type in Lovable's chat: "go back to v3.4.5".
- On GitHub you can lock versions so they can't be deleted. For a private repo this needs a paid GitHub plan.

Pick one per project. If you already use GitHub, pick Pro.

It has been tested live in Lovable apps made before May 13, 2026. Apps made since then use a newer setup (TanStack Start). The steps cover both, but the newer setup hasn't been tested live yet.

## Before you start

- Going back never deletes a version. Your history stays until you delete it. Keep a backup of anything important.
- Going back brings back your code, not your data. Rows in your database and uploaded files stay as they are, just like with Lovable's own History.
- If a change added or changed database tables, going back can break the app, because the tables don't go back. Ask Lovable to fix it.

## Get the kit

1. Open [the repository](https://github.com/atishaytuli07/ai-version-history), click **Code**, then **Download ZIP**.
2. Unzip it (double-click the file).
3. Open the `lovable-kit` folder and double-click `START-HERE.html`. It opens in your browser, with every step on one page and a **Copy** button for every message and file.

## Next step

- Lite: the **Lite setup** section in START-HERE, or `lite/SETUP.md`
- Pro: the **Pro setup** section in START-HERE, or `pro/SETUP.md`
- After setup, for everyday use: **Everyday use** in START-HERE, or `HOW-TO-USE.md`
