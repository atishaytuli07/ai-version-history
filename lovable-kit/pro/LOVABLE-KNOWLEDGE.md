## Versioning (do this with every change)

In the same edit as every code change, overwrite `.ai-versions/pending.json` with:

```json
{
  "bump": "patch",
  "summary": "One line: what changed (max 100 chars)",
  "reason": "One line: why this bump level",
  "prompt": "The user's request, shortened to one line"
}
```

Choose `bump`:
- `patch`: small tweak, same features. Colors, text, spacing, sizes, icons, a small bug fix.
- `minor`: something new, same design direction. New section, component, page, form, feature or integration.
- `major`: direction changed. Full redesign, new layout or navigation, new design system, removing a feature or page, changing the data model.
- Unsure between two levels: pick the lower one and say so in `reason`.

## Going back to a version

When the user asks to go back to a version ("go back to v3.4.5", "undo the redesign"):
- Don't change any code, and don't touch `pending.json`. Write only `.ai-versions/restore.json`:
  `{ "version": "v3.4.5", "note": "why, in one line" }`
- If they describe a version instead of giving a number, find it in `public/ai-versions.json` (each version has a summary and the prompt). If more than one could match, ask which.
- Tell the user: GitHub brings that exact version back in about 1 to 2 minutes, and the preview updates when it syncs. It's saved as a new version, so nothing is lost and they can go back again.
- Once the code has gone back, treat it as the truth. Don't re-apply changes from versions after the restored one unless the user asks for them again.

## Rules

- Never edit or delete `.github/`, `public/ai-versions.json`, `src/components/VersionPill.tsx`, or anything else in `.ai-versions/`, except `pending.json` and `restore.json` as described above.
- Keep `<VersionPill />` rendered once in the root layout (`src/routes/__root.tsx`, or `src/App.tsx` in older apps). It only shows in the preview, never on the live site.
- Never invent version numbers. GitHub assigns them about a minute after each change.
- If the user says a level was wrong ("that was major"), use their judgment for similar changes from now on and mention it in `reason`.
- Commits named "Update version list" or "Restore vX (asked in chat)" are automatic. Never treat them as user changes.
