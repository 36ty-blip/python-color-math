"""Tests for the Color Math Model Context Protocol (MCP) server."""

from __future__ import annotations

import tempfile
import unittest
try:
    import mcp
except ImportError:
    raise unittest.SkipTest("mcp not installed")

from color_math.mcp_server import create_mcp_server


class TestMCPServer(unittest.TestCase):
    def setUp(self) -> None:
        self.server = create_mcp_server()

    def test_registered_tools_exist(self) -> None:
        # Check that all 6 tools are registered on the MCPServer
        expected_tools = {
            "colorize_math_expression",
            "colorize_text",
            "uncolor_text",
            "process_file",
            "scan_vault",
            "list_themes_and_config",
        }
        # In mcp 2.x, tools can be inspected via list_tools or server._tool_manager
        tool_names = set()
        if hasattr(self.server, "list_tools"):
            # If list_tools is a coroutine or callable
            try:
                import asyncio
                res = asyncio.run(self.server.list_tools())
                tool_names = {t.name for t in res}
            except Exception:
                pass

        if not tool_names and hasattr(self.server, "_tool_manager"):
            tool_names = set(self.server._tool_manager._tools.keys())  # type: ignore

        if tool_names:
            self.assertTrue(expected_tools.issubset(tool_names))

    def test_colorize_math_expression_tool(self) -> None:
        import asyncio
        res = asyncio.run(self.server.call_tool(
            "colorize_math_expression",
            {"expression": r"\frac{d}{dx}f(x) = f'(x)"}
        ))
        # The result in mcp 2.x is a CallToolResult
        self.assertIsNotNone(res)
        text_content = str(res)
        self.assertIn("textcolor", text_content)

    def test_colorize_math_expression_with_theme(self) -> None:
        import asyncio
        res = asyncio.run(self.server.call_tool(
            "colorize_math_expression",
            {"expression": r"\frac{d}{dx}f(x)", "theme": "nord"}
        ))
        text_content = str(res)
        self.assertIn("textcolor", text_content)

    def test_colorize_and_uncolor_text_roundtrip(self) -> None:
        import asyncio
        original_md = "# Title\n\nHere is math: $$\\frac{df}{dx} = 5$$\nDone."
        color_res = asyncio.run(self.server.call_tool(
            "colorize_text",
            {"text": original_md, "format_name": "markdown"}
        ))
        color_text = str(color_res)
        self.assertIn("textcolor", color_text)

        uncolor_res = asyncio.run(self.server.call_tool(
            "uncolor_text",
            {"text": r"$$\textcolor{#bb9af7}{\frac{df}{dx}} = 5$$", "format_name": "markdown"}
        ))
        uncolor_text = str(uncolor_res)
        self.assertNotIn("textcolor", uncolor_text)

    def test_process_file_dry_run(self) -> None:
        import asyncio
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "note.md"
            test_file.write_text("# Note\n$$\\frac{df}{dx}$$\n", encoding="utf-8")

            res = asyncio.run(self.server.call_tool(
                "process_file",
                {"file_path": str(test_file), "in_place": False}
            ))
            res_str = str(res)
            self.assertIn("Dry run complete", res_str)
            # File on disk should remain unchanged
            self.assertEqual(test_file.read_text(encoding="utf-8"), "# Note\n$$\\frac{df}{dx}$$\n")

            # Now test in_place = True
            res_in_place = asyncio.run(self.server.call_tool(
                "process_file",
                {"file_path": str(test_file), "in_place": True}
            ))
            self.assertIn("File successfully updated", str(res_in_place))
            self.assertIn("textcolor", test_file.read_text(encoding="utf-8"))

    def test_list_themes_and_config(self) -> None:
        import asyncio
        res = asyncio.run(self.server.call_tool(
            "list_themes_and_config",
            {"theme": "tokyo-night"}
        ))
        res_str = str(res)
        self.assertIn("tokyo-night", res_str)
        self.assertIn("nord", res_str)
        self.assertIn("catppuccin", res_str)


if __name__ == "__main__":
    unittest.main()
