#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

if command -v pipx >/dev/null 2>&1; then
  pipx install --force "$repo_root"
else
  python3 -m pip install --user "$repo_root"
fi

if ! command -v claude-statusline >/dev/null 2>&1; then
  export PATH="$HOME/.local/bin:$HOME/Library/Python/3.9/bin:$HOME/Library/Python/3.10/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.12/bin:$HOME/Library/Python/3.13/bin:$PATH"
fi

claude-statusline install
claude-statusline doctor
