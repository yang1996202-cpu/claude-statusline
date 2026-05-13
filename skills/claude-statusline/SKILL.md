---
name: claude-statusline
description: Install, diagnose, preview, or remove the claude-statusline CLI when users want a reusable Claude Code status line.
---

# claude-statusline skill

This skill wraps the external `claude-statusline` CLI.

The skill is intentionally not the runtime. Claude's `statusLine.command` must point to a local
command that can run automatically and cheaply on every refresh. The skill exists only for guided
operations around that CLI.

Use it when the user wants to:

- install a standard Claude Code status line
- diagnose broken `statusLine` config
- preview rendered output from a sample JSON payload
- remove the managed status line cleanly

## Rules

1. Prefer the CLI over ad-hoc inline shell snippets.
2. Run `claude-statusline doctor` before changing files when troubleshooting.
3. For installation, prefer `claude-statusline install` over editing `settings.json` manually.
4. Treat Windows as experimental unless the user explicitly wants to test it.

## Useful commands

```bash
claude-statusline doctor
claude-statusline render --input examples/sample-session.json
claude-statusline install
claude-statusline uninstall
```
