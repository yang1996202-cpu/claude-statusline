import argparse
import json
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from claude_statusline.cli import (
    DEFAULT_CONFIG,
    DEFAULT_SIGNATURE_TEXT,
    LEGACY_CLI_NAME,
    PRIMARY_CLI_NAME,
    get_claude_dir,
    get_managed_command,
    load_tool_config,
    migrate_user_config_for_install,
    render_statusline,
    signature,
    status,
)


class RenderStatuslineTests(unittest.TestCase):
    def test_project_root_renders_project_name(self) -> None:
        payload = {
            "workspace": {
                "current_dir": "/tmp/demo",
                "project_dir": "/tmp/demo",
            },
            "model": {"display_name": "claude-sonnet-4-6"},
            "context_window": {"remaining_percentage": 88},
        }
        self.assertEqual(render_statusline(payload, DEFAULT_CONFIG), f"demo | claude-sonnet-4-6 | ctx 88% | {DEFAULT_SIGNATURE_TEXT}")

    def test_nested_dir_renders_relative_path(self) -> None:
        payload = {
            "workspace": {
                "current_dir": "/tmp/demo/app/api",
                "project_dir": "/tmp/demo",
            },
            "model": {"display_name": "kimi-for-coding"},
            "context_window": {"used_percentage": 12},
        }
        self.assertEqual(render_statusline(payload, DEFAULT_CONFIG), f"app/api | kimi-for-coding | ctx 88% | {DEFAULT_SIGNATURE_TEXT}")

    def test_project_root_label_override(self) -> None:
        payload = {
            "workspace": {
                "current_dir": "/tmp/demo",
                "project_dir": "/tmp/demo",
            },
            "model": {"display_name": "kimi-for-coding"},
            "context_window": {"remaining_percentage": 62},
        }
        config = {
            **DEFAULT_CONFIG,
            "cwd": {
                **DEFAULT_CONFIG["cwd"],
                "project_root_label": "root",
            },
        }
        self.assertEqual(render_statusline(payload, config), f"root | kimi-for-coding | ctx 62% | {DEFAULT_SIGNATURE_TEXT}")

    def test_load_tool_config_merges_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_dir = Path(temp_dir)
            config_path = claude_dir / "statusline" / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({"separator": " :: "}), encoding="utf-8")
            merged = load_tool_config(claude_dir)
            self.assertEqual(merged["separator"], " :: ")
            self.assertEqual(merged["segments"], DEFAULT_CONFIG["segments"])

    def test_get_claude_dir_override(self) -> None:
        self.assertTrue(str(get_claude_dir("~/tmp")).endswith("tmp"))

    def test_empty_signature_hides_fourth_segment(self) -> None:
        payload = {
            "workspace": {
                "current_dir": "/tmp/demo",
                "project_dir": "/tmp/demo",
            },
            "model": {"display_name": "kimi-for-coding"},
            "context_window": {"remaining_percentage": 88},
        }
        config = {
            **DEFAULT_CONFIG,
            "signature": {
                "text": "",
            },
        }
        self.assertEqual(render_statusline(payload, config), "demo | kimi-for-coding | ctx 88%")

    def test_install_migration_backfills_default_signature(self) -> None:
        migrated = migrate_user_config_for_install({"segments": ["cwd", "model", "context_remaining"]})
        self.assertEqual(migrated["signature"]["text"], DEFAULT_SIGNATURE_TEXT)
        self.assertIn("signature", migrated["segments"])

    def test_signature_command_clears_signature_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_dir = Path(temp_dir)
            signature(
                argparse.Namespace(
                    claude_dir=str(claude_dir),
                    text="",
                )
            )
            config = load_tool_config(claude_dir)
            self.assertEqual(config["signature"]["text"], "")

    def test_status_command_reports_not_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_dir = Path(temp_dir)
            stdout_buffer = io.StringIO()
            original_stdout = __import__("sys").stdout
            try:
                __import__("sys").stdout = stdout_buffer
                exit_code = status(
                    argparse.Namespace(
                        claude_dir=str(claude_dir),
                    )
                )
            finally:
                __import__("sys").stdout = original_stdout

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout_buffer.getvalue().strip(), "not_installed")

    def test_get_managed_command_prefers_staline_binary(self) -> None:
        with mock.patch("claude_statusline.cli.shutil.which") as mock_which:
            mock_which.side_effect = lambda name: "/tmp/staline" if name == PRIMARY_CLI_NAME else None
            self.assertEqual(get_managed_command(), "/tmp/staline render")

    def test_get_managed_command_falls_back_to_legacy_binary(self) -> None:
        with mock.patch("claude_statusline.cli.shutil.which") as mock_which:
            mock_which.side_effect = lambda name: "/tmp/claude-statusline" if name == LEGACY_CLI_NAME else None
            self.assertEqual(get_managed_command(), "/tmp/claude-statusline render")


if __name__ == "__main__":
    unittest.main()