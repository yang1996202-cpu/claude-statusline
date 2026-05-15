# staline

`staline` is the branded status line CLI for Claude Code.

It is built around one fact verified against Claude Code `2.1.140`: `statusLine`
is now an object with `type=command`, and Claude sends the current session payload
to that command on `stdin`. `staline` packages that runtime into a reusable,
installable workflow instead of one-off shell snippets.

## Why this repo exists

- Branded four-segment status line for Claude Code.
- macOS-first: install and verify a custom status line with one command.
- Open-source friendly: runtime logic lives in a standalone CLI, not a local skill.
- Safer config management: only the `statusLine` block is managed, and backups are kept.
- Windows-ready shape: command quoting and path handling are abstracted, even though
  macOS is the primary supported platform in `0.1.0`.

## Current default output

The default renderer prints:

```text
project | kimi-for-coding | ctx 100% | 二哥的认知进化论
```

It comes from four segments:

1. current directory relative to the Claude project root, with the root displayed as the project name
2. current model display name
3. remaining context percentage, labeled as `ctx`
4. rightmost signature text, defaulting to `二哥的认知进化论`

## Install

### macOS from a cloned repo

```bash
./scripts/install.sh
```

This script will:

1. install the package with `pipx` when available, otherwise `python3 -m pip --user`
2. run `staline install`
3. run `staline doctor`

### Manual install

```bash
python3 -m pip install --user .
staline install
staline doctor
```

`claude-statusline` remains available as a compatibility alias for existing installs and scripts.

### Windows bootstrap

`./scripts/install.ps1` is included as a starting point. The command abstraction is
already in the CLI, but Windows support in `0.1.0` is still marked experimental.

## Commands

```bash
staline render
staline install
staline doctor
staline signature "二哥的认知进化论"
staline signature ""
staline uninstall
```

## Config files

- Claude settings: `~/.claude/settings.json`
- Tool config: `~/.claude/statusline/config.json`
- Backups: `~/.claude/statusline/backups/`
- Install state: `~/.claude/statusline/install-state.json`

## Local preview

```bash
staline render --input examples/sample-session.json
```

## Skill wrapper

The repo also includes [skills/staline/SKILL.md](skills/staline/SKILL.md).
That skill is the operator-facing shell for `staline`. The runtime itself stays
in the CLI so regular users do not need an agent environment.

## Why CLI instead of skill-only

This was an intentional product decision.

`statusLine.command` is a hot-path runtime hook. It needs something local, deterministic,
fast, and scriptable. A skill is useful for guided operations such as install, doctor,
preview, and uninstall, but it is the wrong dependency for a status line renderer.

Why:

1. Claude executes `statusLine.command` automatically. It expects an executable command,
   not an agent workflow.
2. The renderer should run without requiring a chat session, tool call, marketplace,
   or skill environment.
3. Human install and AI-assisted install should land on the same runtime path.
4. A CLI can be tested, versioned, packaged, and distributed in standard ways.

So the current split is deliberate:

- CLI: runtime + install primitives, exposed as `staline`
- skill: product wrapper + guided operator shell

## Data flow

The detailed diagrams live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), but the
high-level model is simple: install writes `statusLine.command`, and runtime reads
Claude's session JSON from `stdin` and turns it into one text line.

## High-value future segments

Model is useful, but it is not the only thing worth showing. The highest-value future
segments are:

1. `ctx`: remaining context window percentage
2. `permission`: current permission mode such as `bypass`, `plan`, or `default`
3. `workspace`: current project or relative working directory
4. `git`: branch name and possibly dirty state
5. `mcp`: failing MCP server count
6. `cost`: running session cost from Claude's session payload

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Roadmap

- `0.1.x`: macOS-first CLI, safe install and uninstall, Python packaging
- `0.2.x`: configurable segments and richer doctor output
- `0.3.x`: Homebrew tap and Windows CI verification
- `1.0`: stable config schema and release automation
