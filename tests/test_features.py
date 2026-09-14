"""Comprehensive unit tests for new semantic and disambiguation features."""
from __future__ import annotations
import unittest

from color_math.adapters import AdapterError, has_potential_math, transform_document
from color_math.config import DEFAULT_COLORS, ColorMathOptions, hash_string_to_color
from color_math.converters.block import convert_text
from color_math.undo import uncolor_text
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

    def test_array_environment_head_protection(self) -> None:
        expr = r"\begin{array}{cc|c} 1 & 2 & 3 \\ 4 & 5 & 6 \end{array}"
        opts = ColorMathOptions(variable_data_flow=True, enable_taxonomy=True)
        res = color_latex_body(expr, options=opts)
        # Verify {cc|c} is intact and not shredded into colored variables
        self.assertIn(r"\begin{array}{cc|c}", res)
        self.assertNotIn(r"\textcolor", res[:res.find("}") + 10])

    def test_angle_bracket_delimiters(self) -> None:
        from color_math.parsers.delimiters import find_delimiter_pairs
        # Bare \langle and \rangle
        pairs = find_delimiter_pairs(r"\langle x, y \rangle")
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].depth, 0)
        self.assertEqual(pairs[0].open_item.delim_type, "angle")
        self.assertEqual(pairs[0].close_item.delim_type, "angle")

        # \left\langle and \right\rangle
        pairs_lr = find_delimiter_pairs(r"\left\langle x, y \right\rangle")
        self.assertEqual(len(pairs_lr), 1)
        self.assertTrue(pairs_lr[0].open_item.is_left_right)
        self.assertTrue(pairs_lr[0].close_item.is_left_right)

        # User formulas with inner product and norms without cross-matching
        opts = ColorMathOptions(
            rainbow_delimiters=True,
            color_braket=True,
            variable_data_flow=True,
        )
        expr1 = r"|x| =\sqrt{\langle x,x\rangle},"
        res1 = color_latex_body(expr1, options=opts)
        self.assertIn(r"\textcolor{#e0af68}{\langle}", res1)
        self.assertIn(r"\textcolor{#e0af68}{\rangle}", res1)
        self.assertIn(r"|", res1)

        expr2 = r"\cos\theta=\frac{\langle x,y\rangle}{|x||y|},"
        res2 = color_latex_body(expr2, options=opts)
        self.assertIn(r"\textcolor{#e0af68}{\langle}", res2)
        self.assertIn(r"\textcolor{#e0af68}{\rangle}", res2)

    def test_math_inline_whitespace_rules(self) -> None:
        # 1. Valid inline math is colored
        valid = "Let $a=b$ be true."
        res_valid = convert_text(valid)
        self.assertIn(r"\textcolor", res_valid)
        self.assertIn("$", res_valid)

        # 2. Leading whitespace after opening $ is NOT math
        leading_space = "Not math: $ a=b$ here."
        self.assertEqual(convert_text(leading_space), leading_space)

        # 3. Trailing whitespace before closing $ is NOT math
        trailing_space = "Not math: $a=b $ here."
        self.assertEqual(convert_text(trailing_space), trailing_space)

        # 4. Newline across inline $ is NOT math
        newline_inline = "Not math: $a=b\n$ here."
        self.assertEqual(convert_text(newline_inline), newline_inline)

        # 5. Escaped dollar \$ is NOT math
        escaped_dollar = r"Costs \$a=b\$ here."
        self.assertEqual(convert_text(escaped_dollar), escaped_dollar)

    def test_currency_protection(self) -> None:
        # Currency ranges should not be mistakenly paired as math
        currency1 = "Cost is $20 and profit is $30."
        self.assertEqual(convert_text(currency1), currency1)

        currency2 = "Spent $100 on groceries."
        self.assertEqual(convert_text(currency2), currency2)

        # Mixed currency and real math
        mixed = "Spent $50, but equation is $E=mc^2$."
        res_mixed = convert_text(mixed)
        self.assertIn("Spent $50", res_mixed)
        self.assertIn(r"\textcolor", res_mixed)

    def test_code_protection(self) -> None:
        # Inline code with math symbols is protected
        inline_code = "Use `$a=b$` in terminal and $c=d$ in math."
        res = convert_text(inline_code)
        self.assertIn("`$a=b$`", res)
        self.assertIn(r"\textcolor", res)

        # Fenced code block is protected
        fenced = "```python\nx = '$a=b$'\n```\n$$x=y$$"
        res_fenced = convert_text(fenced)
        self.assertIn("x = '$a=b$'", res_fenced)
        self.assertIn(r"\textcolor", res_fenced)

    def test_fast_path_bypass(self) -> None:
        # Plain text without any math symbols returns immediately
        plain = "This is a plain document without any math markers whatsoever."
        self.assertFalse(has_potential_math(plain, "markdown"))
        self.assertFalse(has_potential_math(plain, "tex"))
        self.assertFalse(has_potential_math(plain, "anki"))
        self.assertEqual(transform_document(plain, "markdown"), plain)

        # Document with $ returns True
        has_dollar = "Contains $x=1$ math."
        self.assertTrue(has_potential_math(has_dollar, "markdown"))

        # Anki bracket without dollar returns True
        has_bracket = r"Contains \[x=1\] math."
        self.assertTrue(has_potential_math(has_bracket, "anki"))
        self.assertTrue(has_potential_math(has_bracket, "markdown"))

    def test_anki_and_tex_combinations(self) -> None:
        # Anki with \[ ... \]
        anki_source = r"Front \[ \frac{d}{dx} x^2 = 2x \] Back"
        anki_res = transform_document(anki_source, "anki")
        self.assertIn(r"\textcolor", anki_res)
        self.assertIn(r"\[", anki_res)

        # TeX with \begin{equation}
        tex_source = "\\begin{equation}\n\\frac{d}{dx} x^2 = 2x\n\\end{equation}"
    def test_empty_and_degenerate_inputs_hard(self) -> None:
        # 1. Completely empty string across all adapters
        for fmt in ("markdown", "tex", "anki"):
            self.assertEqual(transform_document("", fmt), "")
        self.assertEqual(convert_text(""), "")
        with self.assertRaises(AdapterError):
            transform_document("", "jupyter")

        # 2. Whitespace-only strings
        ws_cases = [
            " ",
            "    ",
            "\t",
            "\n",
            "\r\n",
            "  \t \r\n \n \t  ",
        ]
        for ws in ws_cases:
            for fmt in ("markdown", "tex", "anki"):
                self.assertEqual(transform_document(ws, fmt), ws)
            self.assertEqual(convert_text(ws), ws)

        # 3. Pure prose and symbols without math
        plain_prose = (
            "Text with numbers 0-9, symbols !@#%^&*()_+-=[]{}|;':\",./<>? and no math.\n"
            "Second line with tab\tand accents: é, à, ü, ö, ñ, ç.\n"
        )
        for fmt in ("markdown", "tex", "anki"):
            self.assertEqual(transform_document(plain_prose, fmt), plain_prose)

        # 4. Pure comments
        tex_comment = "% This is a LaTeX comment with no math\n% Another line\n"
        self.assertEqual(transform_document(tex_comment, "tex"), tex_comment)

        # 5. Degenerate dollar strings
        degenerate_dollars = [
            "$",
            "$$",
            "$$$",
            "$$$$",
            "$ $",
            "$    $",
            "$$ $$",
            "$$   $$",
            "$$ \n\n $$",
            "Hello $ world",
            "Hello $$ world",
        ]
        for item in degenerate_dollars:
            self.assertEqual(convert_text(item), item, f"Failed on {item!r}")

        # 6. Degenerate LaTeX/Anki environments
        degenerate_envs = [
            r"\[\]",
            r"\(\)",
            r"\[   \]",
            r"\(   \)",
            r"\begin{equation}\end{equation}",
            r"\begin{align}\end{align}",
            r"\[",
            r"\(",
            r"\begin{equation}",
            r"\end{equation}",
        ]
        for item in degenerate_envs:
            res_md = transform_document(item, "markdown")
            self.assertNotIn(r"\textcolor", res_md, f"Unexpected color in {item!r}")

        # 7. Empty and degenerate code blocks
        degenerate_fences = [
            "```\n```",
            "````\n````",
            "~~~\n~~~",
        ]
        for fence in degenerate_fences:
            self.assertEqual(transform_document(fence, "markdown"), fence)

    def test_kitchen_sink_combined_hard(self) -> None:
        combined_doc = (
            "# Advanced Mathematics & Notes\r\n"
            "\r\n"
            "> [!theorem] Hamiltonian Formulation\r\n"
            "> In quantum mechanics, the Hamiltonian is given by:\r\n"
            "> $H = \\frac{p^2}{2m} + V(x)$\r\n"
            "> and the eigenvalue equation satisfies $H|\\psi\\rangle = E|\\psi\\rangle$.\r\n"
            ">\r\n"
            "> We budgeted \\$50 for the experiment, but spent $20 and $30 on materials.\r\n"
            "> Expected cost was $100 to $200 per sensor.\r\n"
            "> Notice that $ invalid leading$ and $invalid trailing $ are not math.\r\n"
            "> Nor is multiline dollar:\r\n"
            "> $a = b\r\n"
            "> $\r\n"
            "> Code elements must remain completely untouched:\r\n"
            "> `$protected_inline = True$` and ``$double_backtick_protected$``.\r\n"
            ">\r\n"
            "> ```python\r\n"
            "> # Code block with math syntax inside\r\n"
            "> def simulate():\r\n"
            ">     cost = '$50'\r\n"
            ">     equation = '$$E = mc^2$$'\r\n"
            ">     return f'{cost}: {equation}'\r\n"
            "> ```\r\n"
            "\r\n"
            "## Section with Mixed Delimiters and Environments\r\n"
            "\r\n"
            "Here is standard display math:\r\n"
            "$$\r\n"
            "\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}\r\n"
            "$$\r\n"
            "\r\n"
            "Punctuation wrapped math: ($x=1$), [$y=2$], and {$z=3$}.\r\n"
            "Limits and fractions: $\\lim_{\\Delta x \\to 0} \\frac{\\Delta y}{\\Delta x} = \\frac{dy}{dx}$.\r\n"
            "\r\n"
            "Anki bracket display:\r\n"
            "\\[ \\mathbf{F} = m \\mathbf{a} \\]\r\n"
            "and Anki paren inline:\r\n"
            "\\( \\Delta x \\cdot \\Delta p \\ge \\frac{\\hbar}{2} \\)\r\n"
            "\r\n"
            "TeX multiline align block:\r\n"
            "\\begin{align}\r\n"
            "\\nabla \\times \\mathbf{E} &= -\\frac{\\partial \\mathbf{B}}{\\partial t} \\\\\r\n"
            "\\nabla \\cdot \\mathbf{D} &= \\rho\r\n"
            "\\end{align}\r\n"
            "\r\n"
            "Matrix inside display block:\r\n"
            "$$\r\n"
            "\\begin{pmatrix}\r\n"
            "a & b \\\\\r\n"
            "c & d\r\n"
            "\\end{pmatrix}\r\n"
            "$$\r\n"
            "\r\n"
            "~~~latex\r\n"
            "\\begin{equation}\r\n"
            "\\text{Verbatim tilde protected: } \\int x dx\r\n"
            "\\end{equation}\r\n"
            "~~~\r\n"
            "\r\n"
            "Multilingual & emoji support:\r\n"
            "🚀 Quantum computing: $\\sum_{k=1}^N |k\\rangle\\langle k| = \\mathbf{I}$ 🎉\r\n"
            "日本語テキスト: $f(x) = x^2$ の計算。\r\n"
            "Über Schrödinger: $\\hat{H}\\psi = E\\psi$.\r\n"
            "\r\n"
            "Final paragraph with no math whatsoever.\r\n"
        )

        converted = transform_document(combined_doc, "markdown")

        # 1. Check that legitimate math was colored
        self.assertIn(r"\textcolor", converted)
        self.assertIn(r"\frac{\textcolor", converted)
        self.assertIn(r"\sqrt{", converted)
        self.assertIn(r"\lim_{", converted)
        self.assertIn(r"\begin{pmatrix}", converted)

        # 2. Check that protected regions are 100% byte-for-byte preserved
        self.assertIn(r"\$50 for the experiment", converted)
        self.assertIn("$20 and $30", converted)
        self.assertIn("$100 to $200", converted)
        self.assertIn("$ invalid leading$", converted)
        self.assertIn("$invalid trailing $", converted)
        self.assertIn("`$protected_inline = True$`", converted)
        self.assertIn("``$double_backtick_protected$``", converted)
        self.assertIn("cost = '$50'", converted)
        self.assertIn("equation = '$$E = mc^2$$'", converted)
        self.assertIn("\\text{Verbatim tilde protected: } \\int x dx", converted)

        # 3. Check CRLF preservation
        self.assertIn("\r\n", converted)
        self.assertEqual(converted.count("\r\n"), combined_doc.count("\r\n"))
        self.assertNotIn("\n", converted.replace("\r\n", ""))

        # 4. Check Unicode and Emoji preservation
        self.assertIn("🚀", converted)
        self.assertIn("🎉", converted)
        self.assertIn("日本語テキスト", converted)
        self.assertIn("Über", converted)

        # 5. Check Idempotency (transforming again produces identical output)
        converted_second_pass = transform_document(converted, "markdown")
        self.assertEqual(converted_second_pass, converted)

        # 6. Check Lossless Undo
        uncolored = uncolor_text(converted)
        self.assertEqual(uncolored, combined_doc)

        # 7. Also verify TeX adapter on a TeX kitchen sink
        tex_doc = (
            "\\documentclass{article}\r\n"
            "\\begin{document}\r\n"
            "\\begin{align}\r\n"
            "\\nabla \\times \\mathbf{E} &= -\\frac{\\partial \\mathbf{B}}{\\partial t} \\\\\r\n"
            "\\nabla \\cdot \\mathbf{D} &= \\rho\r\n"
            "\\end{align}\r\n"
            "\\[ \\mathbf{F} = m \\mathbf{a} \\]\r\n"
            "\\( \\Delta x \\cdot \\Delta p \\ge \\frac{\\hbar}{2} \\)\r\n"
            "$E = mc^2$\r\n"
            "\\begin{verbatim}\r\n"
            "Protected: $x = 1$ and \\begin{equation} y = 2 \\end{equation}\r\n"
            "\\end{verbatim}\r\n"
            "\\end{document}\r\n"
        )
        converted_tex = transform_document(tex_doc, "tex")
        self.assertIn(r"\textcolor", converted_tex)
        self.assertIn(r"Protected: $x = 1$", converted_tex)
        self.assertIn(r"\begin{equation} y = 2 \end{equation}", converted_tex)
        self.assertEqual(transform_document(converted_tex, "tex"), converted_tex)
        self.assertEqual(transform_document(converted_tex, "tex", undo=True), tex_doc)

        # 8. Also verify Anki adapter on an Anki kitchen sink
        anki_doc = (
            "Card 1 Front\t"
            "\\[ \\int_0^1 x^2 dx = \\frac{1}{3} \\] and \\( e^{i\\pi} + 1 = 0 \\)\t"
            "Card 1 Back\n"
            "Card 2 Front\t"
            "[$] \\sum_{n=1}^\\infty \\frac{1}{n^2} = \\frac{\\pi^2}{6} [/$]\t"
            "Card 2 Back\n"
        )
        converted_anki = transform_document(anki_doc, "anki")
        self.assertIn(r"\textcolor", converted_anki)
        self.assertIn("Card 1 Front\t", converted_anki)
        self.assertIn("Card 2 Back", converted_anki)
        self.assertEqual(transform_document(converted_anki, "anki"), converted_anki)
        self.assertEqual(transform_document(converted_anki, "anki", undo=True), anki_doc)


if __name__ == "__main__":
    unittest.main()



