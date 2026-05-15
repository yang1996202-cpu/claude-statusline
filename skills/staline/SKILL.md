---
name: staline
description: Install `staline`, update the rightmost signature, or remove the managed status line cleanly.
---

# staline skill

This skill wraps the external `staline` CLI.

The skill is intentionally not the runtime. Claude's `statusLine.command` must point to a local
command that can run automatically and cheaply on every refresh. The skill exists only for guided
operations around that CLI.

Claude Code's built-in `/statusline` command is a separate product surface that configures status
lines from the shell prompt. Do not treat it as this project's entry point.

Use it when the user wants to:

- install or refresh the branded four-segment Claude Code status line
- change the rightmost signature text
- clear the signature so the status line falls back to three visible segments
- remove the managed status line cleanly

## Rules

1. Keep the user-facing surface to two actions only: modify signature or uninstall.
2. If the status line is missing or stale, run `staline install` internally instead of asking the user to do it.
3. For signature changes, use `staline signature <text>` and use an empty string to clear it.
4. Do not expose `install`, `render`, or `doctor` unless the user explicitly asks for technical details.
5. Treat Windows as experimental unless the user explicitly wants to test it.

## Hidden implementation commands

```bash
staline install
staline status
staline signature "二哥的认知进化论"
staline signature ""
staline uninstall

claude-statusline install
claude-statusline status
claude-statusline signature "二哥的认知进化论"
claude-statusline signature ""
claude-statusline uninstall
```

## User-facing behavior

- Default install shows four segments, with the rightmost signature set to `二哥的认知进化论`.
- When the user edits the signature, prefill with the current value.
- If the user clears the signature, the rendered line returns to three visible segments.
- The only clean exit is uninstalling the status line.