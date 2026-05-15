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
2. **Detection & installation flow** (run in this order):
   a. Try `staline status` then `claude-statusline status`.
   b. If the CLI is not found, read `~/.claude/settings.json` and inspect the `statusLine` object.
   c. Treat settings as **managed by staline** only when `statusLine.type == "command"` and `statusLine.command` clearly points to one of these renderer forms:
      - `staline render`
      - `claude-statusline render`
      - `python -m claude_statusline render`
   d. If settings already point to staline but the CLI is missing, install only the CLI package (`pip install -e .` in the project root). Do **not** rerun `staline install` unless the user explicitly wants to refresh the managed command.
   e. If settings contain a different `statusLine`, do **not** overwrite it automatically. Tell the user another status line is active and ask whether to replace it with staline.
   f. Only if there is no managed staline status line yet, and the user explicitly wants staline, do a fresh install:
      - First run `pip install -e .` in the project root to make the CLI available.
      - Then run `staline install`.
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