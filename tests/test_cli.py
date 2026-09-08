"""Comprehensive test suite for the color_math command-line interface."""

from __future__ import annotations

import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from color_math.config import DEFAULT_COLORS, THEMES, ColorMathOptions
from color_math.main import build_parser, main
from color_math.tutorial import run_tutorial


class CLITests(unittest.TestCase):
    def test_parser_version_and_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["note.md", "-w", "--theme", "nord", "--units"])
        self.assertEqual(args.inputs, ["note.md"])
        self.assertTrue(args.in_place)
        self.assertEqual(args.theme, "nord")
        self.assertTrue(args.units)

    def test_direct_expression_conversion(self) -> None:
        expr = r"$$\frac{d}{dx}f(x)$$"
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = main([expr])
        self.assertEqual(ret, 0)
        output = stdout.getvalue()
        self.assertIn(r"\textcolor{#7aa2f7}{f}", output)

    def test_direct_expression_with_theme(self) -> None:
        expr = r"$$\frac{d}{dx}f(x)$$"
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = main([expr, "--theme", "catppuccin"])
        self.assertEqual(ret, 0)
        output = stdout.getvalue()
        self.assertIn(f"\\textcolor{{{THEMES['catppuccin']['main']}}}{{f}}", output)

    def test_direct_expression_with_color_override(self) -> None:
        expr = r"$$\frac{d}{dx}f(x)$$"
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = main([expr, "--color", "main=#123456"])
        self.assertEqual(ret, 0)
        output = stdout.getvalue()
        self.assertIn(r"\textcolor{#123456}{f}", output)

    def test_auto_detect_single_file_preview(self) -> None:
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("$$\\frac{d}{dx}f(x)$$\n", encoding="utf-8")

            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                ret = main([str(file_path)])
            self.assertEqual(ret, 0)
            self.assertIn(r"\textcolor{#7aa2f7}{f}", stdout.getvalue())
            # File on disk should remain unchanged without -w or -i
            self.assertEqual(file_path.read_text(encoding="utf-8"), "$$\\frac{d}{dx}f(x)$$\n")

    def test_write_mode_with_dash_w(self) -> None:
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("$$\\frac{d}{dx}f(x)$$\n", encoding="utf-8")

            ret = main([str(file_path), "-w"])
            self.assertEqual(ret, 0)
            content = file_path.read_text(encoding="utf-8")
            self.assertIn(r"\textcolor{#7aa2f7}{f}", content)

    def test_undo_restores_plain_latex(self) -> None:
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            original = "$$\\frac{d}{dx}f(x)$$\n"
            file_path.write_text(original, encoding="utf-8")

            # First color it
            main([str(file_path), "-w"])
            self.assertIn(r"\textcolor", file_path.read_text(encoding="utf-8"))

            # Now undo it
            ret = main([str(file_path), "--undo", "-w"])
            self.assertEqual(ret, 0)
            self.assertEqual(file_path.read_text(encoding="utf-8"), original)

    def test_check_mode_linter(self) -> None:
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("$$\\frac{d}{dx}f(x)$$\n", encoding="utf-8")

            # Should return 1 when changes are needed
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                ret_dirty = main([str(file_path), "--check"])
            self.assertEqual(ret_dirty, 1)

            # Color the file
            main([str(file_path), "-w"])

            # Should return 0 when clean
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                ret_clean = main([str(file_path), "--check"])
            self.assertEqual(ret_clean, 0)

    def test_diff_mode(self) -> None:
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("$$\\frac{d}{dx}f(x)$$\n", encoding="utf-8")

            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                ret = main([str(file_path), "--diff"])
            self.assertEqual(ret, 0)
            diff_text = stdout.getvalue()
            self.assertIn("---", diff_text)
            self.assertIn("+++", diff_text)
            self.assertIn(r"\textcolor{#7aa2f7}{f}", diff_text)

    def test_output_destination(self) -> None:
        with TemporaryDirectory() as tmpdir:
            in_file = Path(tmpdir) / "in.md"
            out_file = Path(tmpdir) / "out.md"
            in_file.write_text("$$\\frac{d}{dx}f(x)$$\n", encoding="utf-8")

            ret = main([str(in_file), "-o", str(out_file)])
            self.assertEqual(ret, 0)
            self.assertTrue(out_file.exists())
            self.assertIn(r"\textcolor{#7aa2f7}{f}", out_file.read_text(encoding="utf-8"))

    def test_recursive_directory_processing(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sub = root / "subfolder"
            sub.mkdir()

            f1 = root / "f1.md"
            f2 = sub / "f2.md"
            f1.write_text("$$x=1$$\n", encoding="utf-8")
            f2.write_text("$$y=2$$\n", encoding="utf-8")

            with patch("sys.stdout", io.StringIO()):
                ret = main([str(root), "-r", "-w"])
            self.assertEqual(ret, 0)
            self.assertIn(r"\textcolor", f1.read_text(encoding="utf-8"))
            self.assertIn(r"\textcolor", f2.read_text(encoding="utf-8"))

    def test_show_colors(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = main(["--show-colors"])
        self.assertEqual(ret, 0)
        output = stdout.getvalue()
        self.assertIn("Python Color Math Palette", output)
        self.assertIn("main", output)
        self.assertIn(DEFAULT_COLORS["main"], output)

    def test_init_config_and_reset_colors(self) -> None:
        with TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / ".colormath.json"

            # Init config
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                ret_init = main(["--init-config", str(cfg_path)])
            self.assertEqual(ret_init, 0)
            self.assertTrue(cfg_path.exists())

            # Load and verify content
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            self.assertEqual(data["theme"], "default")
            self.assertEqual(data["colors"]["main"], DEFAULT_COLORS["main"])

            # Test reset-colors
            with patch("sys.stdout", stdout):
                ret_reset = main(["--reset-colors"])
            self.assertEqual(ret_reset, 0)

    def test_tutorial_non_interactive(self) -> None:
        # Piped/non-interactive test of tutorial
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = run_tutorial(input_fn=lambda _: "q")
        self.assertEqual(ret, 0)
        output = stdout.getvalue()
        self.assertIn("Welcome to Python Color Math", output)
        self.assertIn("Chapter 1", output)

    def test_grouped_help_output(self) -> None:
        parser = build_parser()
        help_text = parser.format_help()
        self.assertIn("File & Batch Targeting:", help_text)
        self.assertIn("Verification & Diagnostic Modes:", help_text)
        self.assertIn("Palettes & Theming:", help_text)
        self.assertIn("Engine Features & Presets:", help_text)
        self.assertIn("Interactive, Help & Diagnostics:", help_text)
        self.assertIn("examples:", help_text)
        self.assertIn("color-math note.md -w", help_text)

    def test_stdin_tty_zero_hang(self) -> None:
        # When run with no args and stdin is a TTY, print usage and exit 0 without hanging
        stderr = io.StringIO()
        stdin_mock = io.StringIO()
        stdin_mock.isatty = lambda: True  # type: ignore[assignment]
        with patch("sys.stdin", stdin_mock), patch("sys.stderr", stderr):
            ret = main([])
        self.assertEqual(ret, 0)
        self.assertIn("usage: color-math", stderr.getvalue())
        self.assertIn("To process LaTeX from standard input", stderr.getvalue())

    def test_stdin_explicit_dash(self) -> None:
        stdin_mock = io.StringIO("$$x = 1$$\n")
        stdout = io.StringIO()
        with patch("sys.stdin", stdin_mock), patch("sys.stdout", stdout):
            ret = main(["-"])
        self.assertEqual(ret, 0)
        self.assertIn(r"\textcolor", stdout.getvalue())

    def test_no_color_and_force_color_env(self) -> None:
        from color_math.main import should_color

        with patch.dict("os.environ", {"NO_COLOR": "1"}, clear=False):
            self.assertFalse(should_color())

        with patch.dict("os.environ", {"FORCE_COLOR": "1", "NO_COLOR": ""}, clear=False):
            self.assertTrue(should_color())

    def test_show_colors_json(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = main(["--show-colors", "--json"])
        self.assertEqual(ret, 0)
        data = json.loads(stdout.getvalue())
        self.assertIn("palette", data)
        self.assertIn("descriptions", data)
        self.assertEqual(data["palette"]["main"], DEFAULT_COLORS["main"])

    def test_show_colors_terminal_swatches(self) -> None:
        from color_math.main import print_color_table
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            print_color_table(DEFAULT_COLORS, colorize=True)
        out = stdout.getvalue()
        self.assertIn("Swatch", out)
        self.assertIn("\033[38;2;", out)
        self.assertIn("███", out)

    def test_colored_diff(self) -> None:
        from color_math.main import generate_diff
        diff = generate_diff("$$x$$\n", "$$y$$\n", "test.md", colorize=True)
        self.assertIn("\033[31m-", diff)  # Red for removal
        self.assertIn("\033[32m+", diff)  # Green for addition
        self.assertIn("\033[36m@@", diff)  # Cyan for hunk

    def test_check_json_mode(self) -> None:
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("$$\\frac{d}{dx}f(x)$$\n", encoding="utf-8")

            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                ret_dirty = main([str(file_path), "--check", "--json"])
            self.assertEqual(ret_dirty, 1)
            data_dirty = json.loads(stdout.getvalue())
            self.assertFalse(data_dirty["clean"])
            self.assertEqual(data_dirty["modified_files"], 1)

            # Color the file
            main([str(file_path), "-w"])

            stdout_clean = io.StringIO()
            with patch("sys.stdout", stdout_clean):
                ret_clean = main([str(file_path), "--check", "--json"])
            self.assertEqual(ret_clean, 0)
            data_clean = json.loads(stdout_clean.getvalue())
            self.assertTrue(data_clean["clean"])
            self.assertEqual(data_clean["modified_files"], 0)

    def test_global_xdg_config_lookup(self) -> None:
        from color_math.config import load_config
        with TemporaryDirectory() as tmpdir:
            global_cfg_dir = Path(tmpdir) / "color-math"
            global_cfg_dir.mkdir()
            cfg_file = global_cfg_dir / "config.json"
            cfg_file.write_text(json.dumps({"theme": "catppuccin"}), encoding="utf-8")

            with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(tmpdir), "APPDATA": str(tmpdir)}):
                palette, _ = load_config(path=None)
                self.assertEqual(palette["main"], THEMES["catppuccin"]["main"])

    def test_keyboard_interrupt_handling(self) -> None:
        with patch("color_math.main._main_impl", side_effect=KeyboardInterrupt):
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                ret = main(["note.md"])
            self.assertEqual(ret, 130)
            self.assertIn("Interrupted.", stderr.getvalue())

    def test_generate_completion_shells(self) -> None:
        for shell, signature in [
            ("bash", "complete -F _color_math_completion color-math"),
            ("zsh", "#compdef color-math"),
            ("fish", "Fish completion for color-math"),
            ("powershell", "Register-ArgumentCompleter -Native -CommandName color-math"),
        ]:
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                ret = main(["--generate-completion", shell])
            self.assertEqual(ret, 0, f"Completion failed for {shell}")
            out = stdout.getvalue()
            self.assertIn(signature, out)
            self.assertIn("theme", out)
            self.assertIn("diff", out)

    def test_generate_completion_invalid_shell(self) -> None:
        from color_math.completions import generate_completion
        with self.assertRaises(ValueError):
            generate_completion("unsupported_shell")

    def test_interactive_progress_output(self) -> None:
        with TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "f1.md"
            f2 = Path(tmpdir) / "f2.md"
            f1.write_text("$$x+1$$\n", encoding="utf-8")
            f2.write_text("$$y+2$$\n", encoding="utf-8")

            stderr = io.StringIO()
            stderr.isatty = lambda: True  # type: ignore[assignment]
            with patch("sys.stderr", stderr):
                ret = main([str(f1), str(f2), "-w"])
            self.assertEqual(ret, 0)
            val = stderr.getvalue()
            self.assertIn("[1/2]", val)
            self.assertIn("[2/2]", val)


if __name__ == "__main__":
    unittest.main()

