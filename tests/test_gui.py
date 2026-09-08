"""Unit tests for the Tkinter built-in GUI module."""

from __future__ import annotations

import sys
import tkinter as tk
import unittest
from unittest.mock import patch

from color_math.config import DEFAULT_COLORS, THEMES, ColorMathOptions
from color_math.gui import (
    ColorMathApp,
    configure_dpi_scaling,
    enable_high_dpi,
)


class GUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        enable_high_dpi()
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
            cls.has_tk = True
        except Exception:
            cls.has_tk = False

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.has_tk and hasattr(cls, "root"):
            try:
                cls.root.destroy()
            except Exception:
                pass

    def setUp(self) -> None:
        if not self.has_tk:
            self.skipTest("Tkinter display not available in current test environment")

    def test_dpi_scaling_configuration(self) -> None:
        scale = configure_dpi_scaling(self.root)
        self.assertIsInstance(scale, float)
        self.assertGreater(scale, 0.0)

    def test_app_initialization_defaults(self) -> None:
        sub_window = tk.Toplevel(self.root)
        sub_window.withdraw()
        try:
            app = ColorMathApp(
                sub_window,
                initial_path="test_note.md",
                initial_write=True,
            )
            self.assertEqual(app.target_path_var.get(), "test_note.md")
            self.assertEqual(app.mode_var.get(), "write")
            self.assertEqual(app.palette["main"], DEFAULT_COLORS["main"])
            self.assertFalse(app.is_recursive_var.get())
        finally:
            sub_window.destroy()

    def test_color_normalization_and_contrast(self) -> None:
        sub_window = tk.Toplevel(self.root)
        sub_window.withdraw()
        try:
            app = ColorMathApp(sub_window)
            self.assertEqual(app._normalize_bg("white"), "#ffffff")
            self.assertEqual(app._normalize_bg("black"), "#000000")
            self.assertEqual(app._normalize_bg("#7aa2f7"), "#7aa2f7")

            # High luminance color should have black text
            self.assertEqual(app._get_contrast_fg("#ffffff"), "#000000")
            # Low luminance color should have white text
            self.assertEqual(app._get_contrast_fg("#000000"), "#ffffff")
        finally:
            sub_window.destroy()

    def test_reset_colors(self) -> None:
        sub_window = tk.Toplevel(self.root)
        sub_window.withdraw()
        try:
            app = ColorMathApp(sub_window)
            # Mutate a color
            app.palette["main"] = "#123456"
            self.assertNotEqual(app.palette["main"], DEFAULT_COLORS["main"])

            # Reset
            app._on_reset_colors()
            self.assertEqual(app.palette["main"], DEFAULT_COLORS["main"])
            self.assertEqual(app.theme_var.get(), "default")
        finally:
            sub_window.destroy()

    def test_theme_change(self) -> None:
        sub_window = tk.Toplevel(self.root)
        sub_window.withdraw()
        try:
            app = ColorMathApp(sub_window)
            app.theme_var.set("catppuccin")
            app._on_theme_changed()
            self.assertEqual(app.palette["main"], THEMES["catppuccin"]["main"])
        finally:
            sub_window.destroy()

    def test_preset_change(self) -> None:
        sub_window = tk.Toplevel(self.root)
        sub_window.withdraw()
        try:
            app = ColorMathApp(sub_window)
            app.preset_var.set("extended")
            app._on_preset_changed()

            opts = app._collect_current_options()
            self.assertTrue(opts.color_units)
            self.assertTrue(opts.color_differentials)
            self.assertTrue(opts.rainbow_delimiters)
            self.assertTrue(opts.color_braket)
            self.assertTrue(opts.color_dimensionless)
            self.assertTrue(opts.enable_taxonomy)
            self.assertFalse(opts.variable_data_flow)
        finally:
            sub_window.destroy()


if __name__ == "__main__":
    unittest.main()
