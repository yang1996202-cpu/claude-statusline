# Architecture

## Decision

This project is built as a standalone CLI with an optional skill wrapper.

The runtime path is:

1. Claude Code executes `statusLine.command`
2. Claude streams a JSON session payload to `stdin`
3. `claude-statusline render` reads that payload and prints one line
4. Claude displays that line in the status area

## Why not skill-only

Skills are useful for agent workflows, but they are the wrong dependency for a status line:

- normal users may not have the same agent environment
- runtime behavior should not depend on an LLM tool layer
- installation must be scriptable and repeatable

So the core is a CLI, and the skill is only an operator shell.

## Platform split

### macOS

Primary target in `0.1.0`.

- default Claude config directory: `~/.claude`
- shell command rendering uses POSIX quoting
- install path assumes `python3` exists

### Windows

Planned, partially scaffolded.

- Claude config directory becomes `%USERPROFILE%\\.claude`
- command rendering uses Windows command line quoting
- `install.ps1` exists, but Windows needs more verification around PATH and shell execution

## Managed files

- `settings.json`: only the `statusLine` block is written
- `config.json`: renderer preferences
- `install-state.json`: stores the managed command and latest backup path
- `backups/`: timestamped copies of pre-install settings
