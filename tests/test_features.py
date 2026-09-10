"""Comprehensive unit tests for new semantic and disambiguation features."""
from __future__ import annotations
import unittest

from color_math.config import DEFAULT_COLORS, ColorMathOptions, hash_string_to_color
from color_math.converters.block import convert_text
from color_math.converters.generic import color_latex_body
from color_math.converters.matrix import convert_matrix_block
from color_math.parsers.alignment import find_alignment_spans, collect_alignment_spans
from color_math.parsers.braket import find_braket_spans, collect_braket_delimiter_spans
from color_math.parsers.constants import (
    collect_single_constant_spans,
    is_euler_constant,
    is_imaginary_unit,
)
from color_math.parsers.delimiters import find_delimiter_pairs, collect_delimiter_spans
from color_math.parsers.differentials import find_differential_spans
from color_math.parsers.dimensionless import find_dimensionless_spans
from color_math.parsers.math_parser import find_semantic_spans
from color_math.parsers.taxonomy import collect_taxonomy_spans
from color_math.parsers.units import find_unit_spans
from color_math.parsers.variable_hash import collect_variable_spans
from color_math.utils.latex_helpers import normalize_latex_braces


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

    def test_normalize_latex_braces(self) -> None:
        self.assertEqual(normalize_latex_braces(r"\frac23"), r"\frac{2}{3}")
        self.assertEqual(normalize_latex_braces(r"\sqrt V"), r"\sqrt{V}")
        self.assertEqual(normalize_latex_braces(r"x^2 + y_n"), r"x^{2} + y_{n}")
        self.assertEqual(normalize_latex_braces(r"\frac{a}{b}"), r"\frac{a}{b}")

    def test_bare_math_functions(self) -> None:
        # 1. math_parser finds semantic spans for bare functions
        spans, err = find_semantic_spans(r"sin x + cos(y)")
        self.assertIsNone(err)
        fn_names = [s.value for s in spans if s.kind == "function"]
        self.assertIn("sin", fn_names)
        self.assertIn("cos", fn_names)

        # 2. taxonomy colors bare functions
        tax_spans = collect_taxonomy_spans(r"sin \theta + \cos \theta")
        colored_names = [s.start for s in tax_spans if s.color == DEFAULT_COLORS["main"]]
        self.assertTrue(len(colored_names) >= 2)

        # 3. variable_hash skips bare functions without shredding into letters
        var_spans = collect_variable_spans(r"sin(x)")
        # only 'x' should be hashed as a variable
        self.assertEqual(len(var_spans), 1)

    def test_single_character_constants(self) -> None:
        # Euler constant e
        self.assertTrue(is_euler_constant("e^x", 0))
        self.assertTrue(is_euler_constant("e^{-t}", 0))
        self.assertFalse(is_euler_constant("error", 0))

        # Imaginary unit i, j
        self.assertTrue(is_imaginary_unit("2i", 1))
        self.assertTrue(is_imaginary_unit(r"e^{i\pi}", 3))
        self.assertTrue(is_imaginary_unit("x + iy", 4))
        self.assertTrue(is_imaginary_unit("3j", 1))

        # Shield macro names containing 'e' or 'i': \pi, \phi, \sin, \exp
        self.assertFalse(is_imaginary_unit(r"\pi", 2))
        self.assertFalse(is_euler_constant(r"\exp", 1))

        # Collect spans
        const_spans = collect_single_constant_spans(r"e^{i\pi}")
        self.assertTrue(any(s.start == 0 for s in const_spans))  # e
        self.assertTrue(any(s.start == 3 for s in const_spans))  # i

    def test_alignment_delimiters(self) -> None:
        body = r"a & b \\ c & d"
        spans = find_alignment_spans(body)
        self.assertEqual(len(spans), 3)  # 2 '&' and 1 '\\'

        colored_spans = collect_alignment_spans(body)
        self.assertEqual(len(colored_spans), 3)

        # Ensure color_latex_body NEVER wraps & or \\ in \textcolor
        colored_latex = color_latex_body(body)
        self.assertNotIn(r"\textcolor{#f7768e}{&}", colored_latex)
        self.assertNotIn(r"\textcolor{#f7768e}{\\}", colored_latex)

    def test_arrow_guard_in_matrix(self) -> None:
        # Atomic transition with subscript arrows should NOT be parsed as matrix block
        transition = r"^{4}F_{3/2} \rightarrow {}^{4}I_{11/2}"
        result = convert_matrix_block(f"$${transition}$$")
        self.assertIsNone(result)

    def test_environment_name_skipping(self) -> None:
        # \begin{bmatrix} ... \end{bmatrix} should not shred bmatrix into variables
        spans = collect_variable_spans(r"\begin{bmatrix} a & b \\ c & d \end{bmatrix}")
        # Only a, b, c, d should be variables (4 variables)
        self.assertEqual(len(spans), 4)

    def test_multi_letter_functions(self) -> None:
        opts = ColorMathOptions(variable_data_flow=True, enable_taxonomy=True)
        result = color_latex_body("rank(A) + nullity(A) = n", options=opts)
        self.assertIn("rank", result)
        self.assertIn("nullity", result)
        color_a = hash_string_to_color("A")
        color_n = hash_string_to_color("n")
        self.assertIn(f"\\textcolor{{{color_a}}}{{A}}", result)
        self.assertIn(f"\\textcolor{{{color_n}}}{{n}}", result)

    def test_multi_variable_products(self) -> None:
        opts = ColorMathOptions(variable_data_flow=True)
        result = color_latex_body("ax(y + z)", options=opts)
        color_a = hash_string_to_color("a")
        color_x = hash_string_to_color("x")
        color_y = hash_string_to_color("y")
        color_z = hash_string_to_color("z")
        self.assertIn(f"\\textcolor{{{color_a}}}{{a}}", result)
        self.assertIn(f"\\textcolor{{{color_x}}}{{x}}", result)
        self.assertIn(f"\\textcolor{{{color_y}}}{{y}}", result)
        self.assertIn(f"\\textcolor{{{color_z}}}{{z}}", result)

    def test_operatorname_handling(self) -> None:
        opts = ColorMathOptions(variable_data_flow=True, enable_taxonomy=True)
        result = color_latex_body(r"\operatorname{rank}(A)", options=opts)
        color_a = hash_string_to_color("A")
        self.assertIn(f"\\textcolor{{{color_a}}}{{A}}", result)

    def test_three_letter_functions(self) -> None:
        opts = ColorMathOptions(variable_data_flow=True, enable_taxonomy=True)
        result = color_latex_body("adj(A) + var(X)", options=opts)
        self.assertIn("adj", result)
        self.assertIn("var", result)
        color_a = hash_string_to_color("a")
        self.assertNotIn(f"\\textcolor{{{color_a}}}{{a}}d", result)
        color_cap_a = hash_string_to_color("A")
        color_cap_x = hash_string_to_color("X")
        self.assertIn(f"\\textcolor{{{color_cap_a}}}{{A}}", result)
        self.assertIn(f"\\textcolor{{{color_cap_x}}}{{X}}", result)

    def test_permanent_bake_parity(self) -> None:
        matrix_block = """$$
A=
\\begin{bmatrix}
sin(x) & adj(A) & 3\\\\
4 & 5 & 6\\\\
7 & 8 & 9
\\end{bmatrix}
$$"""
        opts = ColorMathOptions(variable_data_flow=True, enable_taxonomy=True)
        baked = convert_text(matrix_block, options=opts)
        self.assertIn(r"\textcolor{#7dcfff}{A}", baked)
        self.assertIn(r"\textcolor{#7aa2f7}{sin}", baked)
        self.assertIn(r"\textcolor{#7aa2f7}{adj}", baked)
        self.assertIn(r"\begin{bmatrix}", baked)
        self.assertNotIn(r"\textcolor{#bb9af7}{\begin{bmatrix}", baked)

    def test_extended_functions_switch(self) -> None:
        expr = "ch(x) + sp(v)"
        # 1. Switch OFF: 2-letter contradictory functions treated as variable multiplication
        opts_off = ColorMathOptions(
            variable_data_flow=True,
            enable_taxonomy=True,
            extended_functions=False,
        )
        res_off = color_latex_body(expr, options=opts_off)
        color_c = hash_string_to_color("c")
        color_h = hash_string_to_color("h")
        color_s = hash_string_to_color("s")
        color_p = hash_string_to_color("p")
        self.assertIn(f"\\textcolor{{{color_c}}}{{c}}", res_off)
        self.assertIn(f"\\textcolor{{{color_h}}}{{h}}", res_off)
        self.assertIn(f"\\textcolor{{{color_s}}}{{s}}", res_off)
        self.assertIn(f"\\textcolor{{{color_p}}}{{p}}", res_off)

        # Core functions like sin(x) remain functions even when switch is off
        sin_res = color_latex_body("sin(x)", options=opts_off)
        self.assertNotIn(f"\\textcolor{{{color_s}}}{{s}}", sin_res)
        self.assertIn("sin", sin_res)

        # 2. Switch ON (default): ch and sp are unified functions
        opts_on = ColorMathOptions(
            variable_data_flow=True,
            enable_taxonomy=True,
            extended_functions=True,
        )
        res_on = color_latex_body(expr, options=opts_on)
        self.assertNotIn(f"\\textcolor{{{color_c}}}{{c}}", res_on)
        self.assertNotIn(f"\\textcolor{{{color_s}}}{{s}}", res_on)

    def test_full_bare_functions_and_new_extended(self) -> None:
        from color_math.config import FULL_BARE_FUNCTIONS, EXTENDED_BARE_FUNCTIONS, STANDARD_BARE_FUNCTIONS
        new_funcs = ["jac", "hes", "wr", "vol", "rms", "fft", "dft", "ord", "val", "num", "den", "sn", "cn", "dn", "avg", "len"]
        for f in new_funcs:
            self.assertIn(f, EXTENDED_BARE_FUNCTIONS)
            self.assertIn(f, FULL_BARE_FUNCTIONS)
        self.assertEqual(FULL_BARE_FUNCTIONS, STANDARD_BARE_FUNCTIONS | EXTENDED_BARE_FUNCTIONS)

        # Verify parsing with extended functions switch
        expr = "jac(f) + wr(y)"
        opts_on = ColorMathOptions(variable_data_flow=True, enable_taxonomy=True, extended_functions=True)
        res_on = color_latex_body(expr, options=opts_on)
        self.assertIn("jac", res_on)
        self.assertIn("wr", res_on)
        color_w = hash_string_to_color("w")
        self.assertNotIn(f"\\textcolor{{{color_w}}}{{w}}", res_on)


if __name__ == "__main__":
    unittest.main()

