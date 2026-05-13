import json
import tempfile
import unittest
from pathlib import Path

from claude_statusline.cli import DEFAULT_CONFIG, get_claude_dir, load_tool_config, render_statusline


class RenderStatuslineTests(unittest.TestCase):
    def test_project_root_renders_dot(self) -> None:
        payload = {
            "workspace": {
                "current_dir": "/tmp/demo",
                "project_dir": "/tmp/demo",
            },
            "model": {"display_name": "claude-sonnet-4-6"},
            "context_window": {"remaining_percentage": 88},
        }
        self.assertEqual(render_statusline(payload, DEFAULT_CONFIG), ". | claude-sonnet-4-6 | 88%")

    def test_nested_dir_renders_relative_path(self) -> None:
        payload = {
            "workspace": {
                "current_dir": "/tmp/demo/app/api",
                "project_dir": "/tmp/demo",
            },
            "model": {"display_name": "kimi-for-coding"},
            "context_window": {"used_percentage": 12},
        }
        self.assertEqual(render_statusline(payload, DEFAULT_CONFIG), "app/api | kimi-for-coding | 88%")

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


if __name__ == "__main__":
    unittest.main()