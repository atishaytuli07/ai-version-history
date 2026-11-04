# Chat mode (no commands, no files)

Use this when you can't run the script: a plain chat without code execution. The conversation itself is the history, so the rules are the same but you keep the record by hand.

## After every change

Reply with the complete new version of the work (the full page, document, or code, not just the changed part), then end with a version card on its own line:

```
v1.3.0 (New feature): Added a pricing section with 3 plans. Before: v1.2.1.
```

- Start at `v1.0.0` for the first full version you produce.
- Pick the level as in [bump-levels.md](bump-levels.md): patch adds to the last number, minor to the middle one (last becomes 0), major to the first (others become 0).
- Continue from the highest number already in the conversation. Never reuse or skip numbers.
- Going back to a version is a new version: `v2.1.0 (Went back): Back to v1.3.0. Before: v2.0.0.`

## When the user asks

| The user says | Do |
|---|---|
| "show versions" | List every version card from the conversation, newest first |
| "compare v1.3.0 and v2.0.0" | Find both full versions in the conversation and explain what changed, what got better, what got worse |
| "go back to v1.3.0" | Copy the full content of v1.3.0 exactly as it was, character for character, and give it a new "Went back" card |
| "continue in a new chat" | Give a handoff block: the version card, a short list of the decisions that led to it, the dropped directions to avoid, and the full content |

If the old version is no longer in what you can see of the conversation, say so plainly and ask the user to paste it. Don't rebuild it from memory: a rebuilt version isn't the same version.

## Be honest about the limits

Chat history isn't a safe store: it can be edited, regenerated, or lost. When the work matters, suggest saving each version's content to a file named with its version number (for example `pricing-page-v1.3.0.html`), or switching to a tool that can run commands, where the script keeps every version safely.

For tools that support custom instructions but not skills (for example ChatGPT or Gemini custom instructions, or a Project's instructions), the user can paste `assets/rules/chat-mode-rules.md`.
