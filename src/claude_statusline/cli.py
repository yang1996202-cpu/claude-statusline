from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from claude_statusline import __version__


DEFAULT_CONFIG: dict[str, Any] = {
    "separator": " | ",
    "segments": ["cwd", "model", "context_remaining"],
    "cwd": {
        "home_tilde": True,
    },
    "context_remaining": {
        "label": "ctx",
        "unknown_label": "--%",
        "zero_usage_label": "100%",
    },
}


def get_platform_name() -> str:
    return platform.system().lower()


def get_claude_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    if get_platform_name() == "windows":
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".claude"

    return Path.home() / ".claude"


def get_statusline_dir(claude_dir: Path) -> Path:
    return claude_dir / "statusline"


def get_settings_path(claude_dir: Path) -> Path:
    return claude_dir / "settings.json"


def get_config_path(claude_dir: Path) -> Path:
    return get_statusline_dir(claude_dir) / "config.json"


def get_state_path(claude_dir: Path) -> Path:
    return get_statusline_dir(claude_dir) / "install-state.json"


def get_backup_dir(claude_dir: Path) -> Path:
    return get_statusline_dir(claude_dir) / "backups"


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_tool_config(claude_dir: Path) -> dict[str, Any]:
    user_config = read_json_file(get_config_path(claude_dir), default={})
    return deep_merge(DEFAULT_CONFIG, user_config)


def quote_command(parts: list[str]) -> str:
    if get_platform_name() == "windows":
        return subprocess.list2cmdline(parts)
    return shlex.join(parts)


def get_managed_command() -> str:
    executable = shutil.which("claude-statusline")
    if executable:
        return quote_command([executable, "render"])
    return quote_command([sys.executable, "-m", "claude_statusline", "render"])


def format_with_home(path: str, enabled: bool) -> str:
    if not enabled:
        return path

    home = str(Path.home())
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return path.replace(home, "~", 1)
    return path


def format_with_label(value: str, label: str | None) -> str:
    if not label:
        return value
    return f"{label} {value}"


def get_project_root_display(project_dir: str, cwd_config: dict[str, Any]) -> str:
    custom_label = cwd_config.get("project_root_label")
    if isinstance(custom_label, str) and custom_label:
        return custom_label

    project_name = Path(project_dir).name
    if project_name:
        return project_name

    return format_with_home(project_dir, cwd_config.get("home_tilde", True))


def render_cwd(payload: dict[str, Any], config: dict[str, Any]) -> str:
    cwd_config = config.get("cwd", {})
    workspace = payload.get("workspace") or {}
    current_dir = workspace.get("current_dir") or payload.get("cwd") or os.getcwd()
    project_dir = workspace.get("project_dir") or current_dir

    try:
        relative = os.path.relpath(current_dir, project_dir)
    except ValueError:
        relative = current_dir

    if relative == ".":
        return get_project_root_display(project_dir, cwd_config)
    if not relative.startswith(".."):
        return relative
    return format_with_home(current_dir, cwd_config.get("home_tilde", True))


def render_model(payload: dict[str, Any]) -> str:
    model = payload.get("model") or {}
    return (
        model.get("display_name")
        or model.get("id")
        or os.environ.get("ANTHROPIC_MODEL")
        or "unknown-model"
    )


def render_context_remaining(payload: dict[str, Any], config: dict[str, Any]) -> str:
    context_config = config.get("context_remaining", {})
    context_window = payload.get("context_window") or {}
    remaining = context_window.get("remaining_percentage")
    label = context_config.get("label")

    if remaining is None:
        used = context_window.get("used_percentage")
        if isinstance(used, (int, float)):
            remaining = max(0, 100 - used)
        elif context_window.get("current_usage") in (0, None):
            return format_with_label(context_config.get("zero_usage_label", "100%"), label)

    if isinstance(remaining, float):
        if remaining.is_integer():
            remaining = int(remaining)
        else:
            return format_with_label(f"{remaining:.1f}%", label)

    if isinstance(remaining, int):
        return format_with_label(f"{remaining}%", label)

    return format_with_label(context_config.get("unknown_label", "--%"), label)


def render_statusline(payload: dict[str, Any], config: dict[str, Any]) -> str:
    segment_renderers = {
        "cwd": lambda: render_cwd(payload, config),
        "model": lambda: render_model(payload),
        "context_remaining": lambda: render_context_remaining(payload, config),
    }

    rendered: list[str] = []
    for segment_name in config.get("segments", []):
        renderer = segment_renderers.get(segment_name)
        if renderer is None:
            continue
        value = renderer()
        if value:
            rendered.append(value)

    return config.get("separator", " | ").join(rendered)


def load_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        return json.loads(Path(input_path).read_text(encoding="utf-8"))

    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {}


def backup_settings(settings_path: Path, backup_dir: Path) -> Path | None:
    if not settings_path.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"settings.{timestamp}.json"
    shutil.copy2(settings_path, backup_path)
    return backup_path


def install(args: argparse.Namespace) -> int:
    claude_dir = get_claude_dir(args.claude_dir)
    statusline_dir = get_statusline_dir(claude_dir)
    settings_path = get_settings_path(claude_dir)
    config_path = get_config_path(claude_dir)
    state_path = get_state_path(claude_dir)
    backup_dir = get_backup_dir(claude_dir)

    statusline_dir.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        write_json_file(config_path, DEFAULT_CONFIG)

    settings = read_json_file(settings_path, default={})
    backup_path = backup_settings(settings_path, backup_dir)
    command = args.command or get_managed_command()
    settings["statusLine"] = {
        "type": "command",
        "command": command,
    }
    write_json_file(settings_path, settings)
    write_json_file(
        state_path,
        {
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "managed_command": command,
            "backup_path": str(backup_path) if backup_path else None,
            "platform": get_platform_name(),
        },
    )

    print(f"installed statusLine in {settings_path}")
    print(f"managed command: {command}")
    if backup_path:
        print(f"backup: {backup_path}")
    return 0


def uninstall(args: argparse.Namespace) -> int:
    claude_dir = get_claude_dir(args.claude_dir)
    settings_path = get_settings_path(claude_dir)
    state_path = get_state_path(claude_dir)
    settings = read_json_file(settings_path, default={})
    state = read_json_file(state_path, default={})

    status_line = settings.get("statusLine")
    managed_command = state.get("managed_command")

    if not isinstance(status_line, dict):
        print("no managed statusLine found")
        return 0

    if not args.force and status_line.get("command") != managed_command:
        print("refusing to remove statusLine because it no longer matches the recorded managed command")
        print("rerun with --force if you want to remove it anyway")
        return 1

    settings.pop("statusLine", None)
    write_json_file(settings_path, settings)
    if state_path.exists():
        state_path.unlink()
    print(f"removed managed statusLine from {settings_path}")
    return 0


def doctor(args: argparse.Namespace) -> int:
    claude_dir = get_claude_dir(args.claude_dir)
    settings_path = get_settings_path(claude_dir)
    config_path = get_config_path(claude_dir)
    state_path = get_state_path(claude_dir)
    settings = read_json_file(settings_path, default={})
    state = read_json_file(state_path, default={})
    status_line = settings.get("statusLine")
    managed_command = state.get("managed_command")

    messages: list[tuple[str, str]] = []
    messages.append(("ok", f"platform: {get_platform_name()}"))
    if get_platform_name() == "windows":
        messages.append(("warn", "windows support is scaffolded but not yet fully validated"))
    else:
        messages.append(("ok", "macOS or POSIX environment detected"))

    messages.append(("ok", f"claude dir: {claude_dir}"))
    if config_path.exists():
        messages.append(("ok", f"config: {config_path}"))
    else:
        messages.append(("warn", f"config missing: {config_path}"))

    if not settings_path.exists():
        messages.append(("warn", f"settings missing: {settings_path}"))
    elif not isinstance(status_line, dict):
        messages.append(("warn", "statusLine is not configured as an object"))
    elif status_line.get("type") != "command":
        messages.append(("fail", f"statusLine.type must be 'command', got {status_line.get('type')!r}"))
    elif not isinstance(status_line.get("command"), str):
        messages.append(("fail", "statusLine.command is missing or not a string"))
    else:
        messages.append(("ok", f"statusLine command: {status_line['command']}"))
        if managed_command and managed_command == status_line.get("command"):
            messages.append(("ok", "statusLine matches the recorded managed command"))
        elif managed_command:
            messages.append(("warn", "statusLine differs from the recorded managed command"))
        else:
            messages.append(("warn", "install-state.json missing or incomplete"))

    for level, message in messages:
        print(f"[{level}] {message}")

    return 0 if not any(level == "fail" for level, _ in messages) else 1


def render(args: argparse.Namespace) -> int:
    claude_dir = get_claude_dir(args.claude_dir)
    config = load_tool_config(claude_dir)
    payload = load_payload(args.input)
    print(render_statusline(payload, config))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claude-statusline")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a status line from Claude session JSON")
    render_parser.add_argument("--input", help="Read the Claude session payload from a file instead of stdin")
    render_parser.add_argument("--claude-dir", help="Override the Claude config directory")
    render_parser.set_defaults(func=render)

    install_parser = subparsers.add_parser("install", help="Install the managed statusLine into Claude settings")
    install_parser.add_argument("--claude-dir", help="Override the Claude config directory")
    install_parser.add_argument("--command", help="Override the managed command written to statusLine.command")
    install_parser.set_defaults(func=install)

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove the managed statusLine from Claude settings")
    uninstall_parser.add_argument("--claude-dir", help="Override the Claude config directory")
    uninstall_parser.add_argument("--force", action="store_true", help="Remove statusLine even if it no longer matches the recorded command")
    uninstall_parser.set_defaults(func=uninstall)

    doctor_parser = subparsers.add_parser("doctor", help="Inspect the current installation and Claude settings")
    doctor_parser.add_argument("--claude-dir", help="Override the Claude config directory")
    doctor_parser.set_defaults(func=doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
