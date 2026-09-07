"""Comprehensive unit tests for new semantic and disambiguation features."""
from __future__ import annotations
import unittest

from color_math.config import DEFAULT_COLORS, ColorMathOptions
from color_math.converters.block import convert_text
from color_math.converters.generic import color_latex_body
from color_math.parsers.units import find_unit_spans
from color_math.parsers.differentials import find_differential_spans
from color_math.parsers.braket import find_braket_spans, collect_braket_delimiter_spans
from color_math.parsers.dimensionless import find_dimensionless_spans
from color_math.parsers.delimiters import find_delimiter_pairs, collect_delimiter_spans
from color_math.parsers.taxonomy import collect_taxonomy_spans
from color_math.parsers.variable_hash import collect_variable_spans


class FeatureTests(unittest.TestCase):
    def test_units_disambiguation(self) -> None:
        # 1. Micro units
        spans = find_unit_spans(r"1.064\, \mu m")
        self.assertEqual(len(spans), 1)
        self.assertIn(r"\mu m", spans[0].text)

        # 2. Velocity unit
        spans_vel = find_unit_spans(r"10 m/s")
        self.assertEqual(len(spans_vel), 1)
        self.assertEqual(spans_vel[0].text, "m/s")

        # 3. Temperature degree unit
        spans_deg = find_unit_spans(r"100 ^\circ C")
        self.assertEqual(len(spans_deg), 1)
        self.assertIn(r"^\circ C", spans_deg[0].text)

        # 4. Shielding: algebraic variables are NOT units
        self.assertEqual(len(find_unit_spans(r"F = ma")), 0)
        self.assertEqual(len(find_unit_spans(r"E = mc^2")), 0)

        # 5. Full generic conversion with color_units enabled
        opts = ColorMathOptions(color_units=True)
        colored = color_latex_body(r"v = 25 m/s", options=opts)
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['unit']}}}{{m/s}}", colored)

    def test_differentials_disambiguation(self) -> None:
        # 1. Infinitesimals
        spans = find_differential_spans(r"\int x^2 \, dx")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].text, "dx")

        # 2. Greek differential
        spans_greek = find_differential_spans(r"\int \sin(\theta) \, d\theta")
        self.assertEqual(len(spans_greek), 1)
        self.assertEqual(spans_greek[0].text, r"d\theta")

        # 3. Derivative fractions
        spans_frac = find_differential_spans(r"\frac{df}{dx} = 2x")
        self.assertEqual(len(spans_frac), 1)
        self.assertEqual(spans_frac[0].kind, "derivative_fraction")

        # 4. Shielding: standalone distance d or variable d is NOT a differential
        self.assertEqual(len(find_differential_spans("W = F d")), 0)
        self.assertEqual(len(find_differential_spans("d = vt")), 0)
        self.assertEqual(len(find_differential_spans(r"d\iff e")), 0)

        # 5. Full generic conversion with color_differentials enabled
        opts = ColorMathOptions(color_differentials=True)
        colored = color_latex_body(r"\int x \, dx", options=opts)
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['derivative']}}}{{dx}}", colored)

    def test_braket_disambiguation(self) -> None:
        # 1. Expectation value / bracket
        spans = find_braket_spans(r"\langle \phi | \hat{H} | \psi \rangle")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].kind, "bracket")

        # 2. Ket and Bra
        spans_ket = find_braket_spans(r"|\psi\rangle")
        self.assertEqual(len(spans_ket), 1)
        self.assertEqual(spans_ket[0].kind, "ket")

        spans_bra = find_braket_spans(r"\langle\phi|")
        self.assertEqual(len(spans_bra), 1)
        self.assertEqual(spans_bra[0].kind, "bra")

        # 3. Shielding: absolute value / inequality is NOT a bra-ket
        self.assertEqual(len(find_braket_spans("|x| < 5")), 0)

        # 4. Color delimiters
        opts = ColorMathOptions(color_braket=True)
        colored = color_latex_body(r"\langle \phi | \psi \rangle", options=opts)
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['orange']}}}{{\\langle}}", colored)
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['orange']}}}{{\\rangle}}", colored)

    def test_dimensionless_disambiguation(self) -> None:
        # 1. Standard numbers
        spans = find_dimensionless_spans(r"Re = \frac{\rho v L}{\mu}")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].text, "Re")

        # 2. Strict contiguity: R e is NOT Reynolds
        self.assertEqual(len(find_dimensionless_spans("R e = 5")), 0)
        self.assertEqual(len(find_dimensionless_spans(r"R \, e = 5")), 0)

        # 3. Preserves LaTeX real part operator \Re
        self.assertEqual(len(find_dimensionless_spans(r"\Re(z)")), 0)

        # 4. Color dimensionless
        opts = ColorMathOptions(color_dimensionless=True)
        colored = color_latex_body("Ma = 2.5", options=opts)
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['main']}}}{{Ma}}", colored)

    def test_rainbow_delimiters(self) -> None:
        # Nested parentheses
        body = "((a + b) * (c + d))"
        pairs = find_delimiter_pairs(body)
        self.assertEqual(len(pairs), 3)

        # Outer pair depth 0, inner pairs depth 1
        outer = [p for p in pairs if p.open_item.start == 0][0]
        self.assertEqual(outer.depth, 0)

        # Delimiter spans
        spans = collect_delimiter_spans(body)
        self.assertEqual(len(spans), 6)  # 3 pairs * 2 delimiters

    def test_taxonomy_semantic_roles(self) -> None:
        # Constants, functions, parameters, bound indices
        body = r"\sum_{i=1}^n \sin(\alpha \pi)"
        spans = collect_taxonomy_spans(body)
        self.assertTrue(len(spans) >= 3)

        # Index 'i' colored as chain
        chain_spans = [s for s in spans if s.color == DEFAULT_COLORS["chain"]]
        self.assertTrue(len(chain_spans) >= 1)

        # Constant \pi colored as orange
        const_spans = [s for s in spans if s.color == DEFAULT_COLORS["orange"]]
        self.assertTrue(len(const_spans) >= 1)

    def test_variable_data_flow(self) -> None:
        body = "x + y + x"
        spans = collect_variable_spans(body)
        self.assertEqual(len(spans), 3)
        # Identical variable x gets identical color
        self.assertEqual(spans[0].color, spans[2].color)

        # Function f(x) does NOT color f as a variable
        func_spans = collect_variable_spans("f(x)")
        self.assertEqual(len(func_spans), 1)  # only x

    def test_boxed_equation(self) -> None:
        body = r"\boxed{E=mc^2}"
        colored = color_latex_body(body)
        self.assertIn(r"\boxed", colored)
        # Content inside boxed is colored
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['relation']}}}{{=}}", colored)

    def test_extended_and_all_enabled_options(self) -> None:
        text = r"$$Re = 2000 \quad \text{at} \quad 10 m/s$$"
        converted_default = convert_text(text)
        self.assertNotIn(f"\\textcolor{{{DEFAULT_COLORS['unit']}}}{{m/s}}", converted_default)

        converted_ext = convert_text(text, options=ColorMathOptions.extended())
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['unit']}}}{{m/s}}", converted_ext)
        self.assertIn(f"\\textcolor{{{DEFAULT_COLORS['main']}}}{{Re}}", converted_ext)


if __name__ == "__main__":
    unittest.main()
