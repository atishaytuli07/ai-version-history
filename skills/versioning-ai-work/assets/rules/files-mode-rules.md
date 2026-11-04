## Versioning (do this with every change)

This project keeps every version in `.ai-versions/`. Use its script; never edit that folder by hand.

- After finishing each request that changed files, run:
  `python3 .ai-versions/aiv.py save --bump <patch|minor|major> --summary "<what changed, in plain words>" --reason "<why this level>" --prompt "<the request, one line>"`
  (Windows: `py` instead of `python3`.) Then end your reply with the line it prints, such as `Saved v1.3.0 (New feature): ...`.
- `patch` = small tweak (text, color, spacing, small fix). `minor` = something new added (section, page, feature). `major` = direction changed (redesign, new layout, something removed). One request = one version; use the highest level. Unsure: pick the lower one and say so in `--reason`.
- "Show versions": `list`. "What changed in v1.3.0": `diff v1.3.0^ v1.3.0`. "Compare A and B": `diff A B`.
- "Go back to v1.2.0" or "undo": `restore v1.2.0` or `restore prev`. Never rebuild old work from memory. After a restore, run `handoff <that version>` and follow it, so dropped ideas don't come back.
- Never invent version numbers, and never delete or edit anything in `.ai-versions/`.
