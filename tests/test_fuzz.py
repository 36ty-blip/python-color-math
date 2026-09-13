"""Property-based generative fuzz testing for color-math invariants."""

from __future__ import annotations

import random
import unittest

from color_math.config import ColorMathOptions
from color_math.converters.block import convert_text
from color_math.undo import uncolor_text
try:
    from .latex_validator import validate_latex_output
except ImportError:
    from tests.latex_validator import validate_latex_output


class MathExpressionGenerator:
    """Deterministic generative pseudo-random math expression builder."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def leaf(self) -> str:
        choices = [
            # Standard variables
            "x", "y", "z", "t", "u", "v",
            # Greek letters
            r"\alpha", r"\beta", r"\gamma", r"\theta", r"\lambda", r"\omega",
            # Constants
            "e", "i", r"\pi", "0", "1", "2", "5", "42",
            # Dimensionless / Units
            "Re", "Ma",
        ]
        return self.rng.choice(choices)

    def simple_operand(self, depth: int) -> str:
        if depth <= 0 or self.rng.random() < 0.4:
            return self.leaf()
        return self.expression(depth - 1)

    def function_call(self, depth: int) -> str:
        funcs = [
            r"\sin", r"\cos", r"\tan", r"\ln", r"\exp",
            r"\sinh", r"\cosh", r"\arcsin",
            "f", "g", "h",
            r"\operatorname{rank}", r"\operatorname{tr}",
        ]
        fn = self.rng.choice(funcs)
        arg = self.simple_operand(depth - 1)
        if self.rng.random() < 0.5:
            return f"{fn}({arg})"
        return f"{fn}{{{arg}}}"

    def fraction(self, depth: int) -> str:
        num = self.simple_operand(depth - 1)
        den = self.simple_operand(depth - 1)
        return rf"\frac{{{num}}}{{{den}}}"

    def radical(self, depth: int) -> str:
        inner = self.simple_operand(depth - 1)
        if self.rng.random() < 0.3:
            deg = self.rng.choice(["3", "n", "k"])
            return rf"\sqrt[{deg}]{{{inner}}}"
        return rf"\sqrt{{{inner}}}"

    def script(self, depth: int) -> str:
        base = self.leaf()
        sub = self.rng.choice(["i", "j", "n", "k", "0", "1"])
        sup = self.rng.choice(["2", "3", "n", "-1"])
        mode = self.rng.choice(["sub", "sup", "both"])
        if mode == "sub":
            return f"{base}_{{{sub}}}"
        elif mode == "sup":
            return f"{base}^{{{sup}}}"
        else:
            return f"{base}_{{{sub}}}^{{{sup}}}"

    def operator_block(self, depth: int) -> str:
        inner = self.simple_operand(depth - 1)
        op_type = self.rng.choice(["sum", "int", "lim", "prod"])
        if op_type == "sum":
            return rf"\sum_{{i=1}}^{{n}} {inner}"
        elif op_type == "int":
            var = self.rng.choice(["x", "t", "y"])
            return rf"\int_0^1 {inner}\,d{var}"
        elif op_type == "lim":
            return rf"\lim_{{x \to 0}} {inner}"
        else:
            return rf"\prod_{{k=1}}^{{m}} {inner}"

    def matrix(self, depth: int) -> str:
        env = self.rng.choice(["bmatrix", "pmatrix", "matrix"])
        a = self.leaf()
        b = self.leaf()
        c = self.leaf()
        d = self.leaf()
        return (
            rf"\begin{{{env}}}" "\n"
            rf"  {a} & {b} \\" "\n"
            rf"  {c} & {d}" "\n"
            rf"\end{{{env}}}"
        )

    def aligned_block(self, depth: int) -> str:
        left1 = self.leaf()
        right1 = self.simple_operand(depth - 1)
        left2 = self.leaf()
        right2 = self.simple_operand(depth - 1)
        return (
            r"\begin{aligned}" "\n"
            rf"  {left1} &= {right1} \\" "\n"
            rf"  {left2} &= {right2}" "\n"
            r"\end{aligned}"
        )

    def bracketed(self, depth: int) -> str:
        inner = self.simple_operand(depth - 1)
        pair = self.rng.choice([
            (r"\left(", r"\right)"),
            (r"\left[", r"\right]"),
            (r"\left\{", r"\right\}"),
            ("(", ")"),
            ("[", "]"),
        ])
        return f"{pair[0]}{inner}{pair[1]}"

    def expression(self, depth: int = 3) -> str:
        if depth <= 0:
            return self.leaf()

        constructs = [
            self.fraction,
            self.radical,
            self.function_call,
            self.script,
            self.operator_block,
            self.bracketed,
        ]
        if depth >= 2:
            constructs.extend([self.matrix, self.aligned_block])

        gen = self.rng.choice(constructs)
        expr1 = gen(depth)

        if self.rng.random() < 0.5:
            op = self.rng.choice(["+", "-", "=", r"\cdot", r"\le", r"\ge"])
            expr2 = self.simple_operand(depth - 1)
            return f"{expr1} {op} {expr2}"

        return expr1


class FuzzTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        # Fixed seed ensures deterministic reproducibility
        self.rng = random.Random(2026)
        self.generator = MathExpressionGenerator(self.rng)

    def assert_invariants(self, expr: str, options: ColorMathOptions | None = None) -> None:
        raw_doc = f"$$\n{expr}\n$$\n"
        converted = convert_text(raw_doc, options=options)

        # 1. Structural correctness of generated LaTeX
        validate_latex_output(converted)

        # 2. Strict Lossless Undo Invariant: uncolor(convert(doc)) == doc
        uncolored = uncolor_text(converted)
        self.assertEqual(
            uncolored,
            raw_doc,
            f"Undo round-trip failed for expression:\n{expr}\n\nGot:\n{uncolored}",
        )

        # 3. Strict Idempotency Invariant: convert(convert(doc)) == convert(doc)
        re_converted = convert_text(converted, options=options)
        self.assertEqual(
            re_converted,
            converted,
            f"Idempotency failed for expression:\n{expr}\n\nFirst convert:\n{converted}\n\nSecond convert:\n{re_converted}",
        )

    def test_random_expressions_default_options(self) -> None:
        """Fuzz test 150 structurally varied expressions with default options."""
        for i in range(150):
            expr = self.generator.expression(depth=self.rng.randint(1, 4))
            with self.subTest(iteration=i, expr=expr[:40]):
                self.assert_invariants(expr, options=None)

    def test_random_expressions_all_enabled_options(self) -> None:
        """Fuzz test 150 structurally varied expressions with all features enabled."""
        opts = ColorMathOptions.all_enabled()
        for i in range(150):
            expr = self.generator.expression(depth=self.rng.randint(1, 4))
            with self.subTest(iteration=i, expr=expr[:40]):
                self.assert_invariants(expr, options=opts)

    def test_random_expressions_with_interleaved_comments(self) -> None:
        """Fuzz test expressions containing random comments at token boundaries."""
        opts = ColorMathOptions.all_enabled()
        for i in range(50):
            base = self.generator.expression(depth=2)
            # Inject comment into expression
            lines = base.splitlines()
            if lines:
                inject_idx = self.rng.randint(0, len(lines) - 1)
                lines[inject_idx] = lines[inject_idx] + f" % fuzz comment {i}"
                commented_expr = "\n".join(lines)
            else:
                commented_expr = base + f" % fuzz comment {i}\n"

            with self.subTest(iteration=i, expr=commented_expr[:40]):
                self.assert_invariants(commented_expr, options=opts)


if __name__ == "__main__":
    unittest.main()
