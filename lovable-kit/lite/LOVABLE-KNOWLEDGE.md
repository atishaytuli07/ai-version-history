## Versioning (mandatory on every change)

In the same edit as every code change, overwrite `src/ai-version.ts` with:

```ts
export const aiVersion = {
  id: "a new random 6-letter code, different for every change",
  bump: "patch",
  summary: "One line: what changed (max 100 chars)",
  reason: "One line: why this bump level",
  prompt: "",
};
```

Choose `bump`:
- `patch`: small tweak, same features. Colors, text, spacing, sizes, icons, a small bug fix.
- `minor`: something new, same design direction. New section, component, page, form, feature or integration.
- `major`: direction changed. Full redesign, new layout or navigation, new design system, removing a feature or page, changing the data model.
- Unsure between two levels: pick the lower one and say so in `reason`.

Rules:
- Every change needs a fresh `src/ai-version.ts` with a new `id` and a description of that change. A change without it gets no version.
- Leave `prompt` empty. Prompts are only saved if a rule below asks for it, because anyone with the app's public key can read the version list.
- Never edit `src/components/VersionPill.tsx` or `src/lib/ai-versions-store.ts`. Never change, delete or drop the `ai_versions` table or its rows.
- Keep `<VersionPill />` rendered once in `src/App.tsx`. It only shows in preview, never on the live site.
- Never invent version numbers. The version pill assigns them.
- If the user says a level was wrong ("that was major"), use their judgment for similar changes from now on and mention it in `reason`.

## Going back to a version

- Don't rewrite old code from memory. Going back is done with Lovable's History → Restore.
- If the user names a version ("go back to v3.4.5") or describes one ("before the redesign"), find it in the version pill's list (the `ai_versions` table), then tell them its summary and the date and time it was saved, so they can pick the matching change in History and click Restore. If more than one version could match, ask which.
- After a restore, treat the restored code as the truth. Don't re-apply changes from versions after the restored one unless the user asks for them again.
