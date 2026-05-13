$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install --force $RepoRoot
} else {
    py -m pip install --user $RepoRoot
}

claude-statusline install
claude-statusline doctor
