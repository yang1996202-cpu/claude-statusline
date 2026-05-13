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

user_base="$(python3 -c 'import site; print(site.USER_BASE)')"

if ! command -v claude-statusline >/dev/null 2>&1; then
  export PATH="$HOME/.local/bin:$user_base/bin:$PATH"
fi

if command -v claude-statusline >/dev/null 2>&1; then
  cli=(claude-statusline)
else
  cli=(python3 -m claude_statusline)
fi

"${cli[@]}" install
"${cli[@]}" doctor
