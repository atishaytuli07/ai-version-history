# Choosing the level

The level tells the user, at a glance, how far a version is from the one before. Ask: if the user saw these two versions side by side, would they call the difference a tweak, an addition, or a different thing?

| Level | Shown as | The test |
|---|---|---|
| `patch` | Small tweak | Same features and structure; something was adjusted |
| `minor` | New feature | Everything from before is still there, and something was added |
| `major` | Big change | It looks, works, or reads differently overall, or something was taken away |

## Web pages, apps, designs

| Change | Level |
|---|---|
| Change text, color, font size, spacing, an icon, an image | patch |
| Fix a bug, a broken link, a layout glitch | patch |
| Make it work on mobile when it was almost there | patch |
| Rename a button or a page title | patch |
| Add a section, page, form, modal, component, or chart | minor |
| Add a feature (search, login, dark mode toggle, export) | minor |
| Connect a new service (payments, email, database table) | minor |
| Redesign, new layout, new navigation, new visual style or design system | major |
| Remove a page, section, or feature | major |
| Change what the product is or who it's for (new name, new pitch) | major |
| Change the data model in a way that affects existing data | major |

## Documents and writing

| Change | Level |
|---|---|
| Fix typos, rephrase sentences, tighten wording | patch |
| Add a section, an example, a table, a chart | minor |
| Restructure, change the tone or audience, rewrite most of it, cut sections | major |

## Code without visible changes

| Change | Level |
|---|---|
| Refactor, rename, clean up, add comments or tests | patch |
| Update a dependency without changing behavior | patch |
| New capability, endpoint, command, or option | minor |
| Breaking change: removed or renamed something people rely on | major |

## Mixed requests

One request = one version. Use the highest level among its changes. "Fix the typo and add a FAQ" is minor.

## When unsure

Pick the lower level and say why in `--reason`, for example: "Between patch and minor: the new badge is tiny, so treated as a tweak." If the user says a level was wrong, apply their judgment to similar changes from then on and mention it in `--reason`. Never edit past versions to fix a level; history stays as it was.
