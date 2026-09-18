"""Unit tests for Harmonic Tuple Disambiguation & Perceptual Contrast."""

import unittest
from color_math.config import (
    VARIABLE_HASH_PALETTE,
    CANONICAL_VARIABLE_SLOTS,
    hash_string_to_color,
    hash_string_to_slot,
)
from color_math.converters.block import convert_text
from color_math.config import ColorMathOptions


class TestHarmonicTupleDisambiguation(unittest.TestCase):
    def test_spatial_coordinates_distinct(self):
        """Verify (x, y, z) are assigned mutually distinct, contrasting colors."""
        col_x = hash_string_to_color("x")
        col_y = hash_string_to_color("y")
        col_z = hash_string_to_color("z")
        self.assertNotEqual(col_x, col_y)
        self.assertNotEqual(col_y, col_z)
        self.assertNotEqual(col_x, col_z)

    def test_coefficients_distinct(self):
        """Verify (a, b, c, d) are mutually distinct."""
        col_a = hash_string_to_color("a")
        col_b = hash_string_to_color("b")
        col_c = hash_string_to_color("c")
        col_d = hash_string_to_color("d")
        colors = {col_a, col_b, col_c, col_d}
        self.assertEqual(len(colors), 4)

    def test_parameters_distinct(self):
        """Verify (u, v, w) are mutually distinct."""
        col_u = hash_string_to_color("u")
        col_v = hash_string_to_color("v")
        col_w = hash_string_to_color("w")
        colors = {col_u, col_v, col_w}
        self.assertEqual(len(colors), 3)

    def test_indices_distinct(self):
        """Verify (i, j, k, l) are mutually distinct."""
        col_i = hash_string_to_color("i")
        col_j = hash_string_to_color("j")
        col_k = hash_string_to_color("k")
        col_l = hash_string_to_color("l")
        colors = {col_i, col_j, col_k, col_l}
        self.assertEqual(len(colors), 4)

    def test_linear_combination_cross_contrast(self):
        """Verify in ax + by + cz, all six variables receive distinct colors."""
        vars_to_test = ["a", "x", "b", "y", "c", "z"]
        colors = [hash_string_to_color(v) for v in vars_to_test]
        # In term 1: a != x
        self.assertNotEqual(colors[0], colors[1])
        # In term 2: b != y
        self.assertNotEqual(colors[2], colors[3])
        # In term 3: c != z
        self.assertNotEqual(colors[4], colors[5])
        # All 6 must be unique!
        self.assertEqual(len(set(colors)), 6)

    def test_rendered_linear_combination_equation(self):
        """Verify full math expression rendering of ax + by + cz = d."""
        eq = "$$ax + by + cz = d$$"
        opts = ColorMathOptions.all_enabled()
        res = convert_text(eq, options=opts)
        self.assertIn(r"\textcolor{#bb9af7}{a}", res)
        self.assertIn(r"\textcolor{#7aa2f7}{x}", res)
        self.assertIn(r"\textcolor{#f7768e}{b}", res)
        self.assertIn(r"\textcolor{#e0af68}{y}", res)
        self.assertIn(r"\textcolor{#2ac3de}{c}", res)
        self.assertIn(r"\textcolor{#9ece6a}{z}", res)

    def test_dispersive_hash_unknown_variables(self):
        """Verify arbitrary variables receive deterministic slots."""
        s1 = hash_string_to_slot("var1")
        s2 = hash_string_to_slot("var1")
        self.assertEqual(s1, s2)
        self.assertTrue(0 <= s1 < 8)


if __name__ == "__main__":
    unittest.main()
