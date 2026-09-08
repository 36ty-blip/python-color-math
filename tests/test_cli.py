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

    def test_options_preset_extended(self) -> None:
        expr = r"$$v = 25 m/s$$"
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            ret = main([expr, "--preset", "extended"])
        self.assertEqual(ret, 0)
        output = stdout.getvalue()
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['unit']}}}{{m/s}}", output)


if __name__ == "__main__":
    unittest.main()
