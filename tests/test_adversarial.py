"""Adversarial, torture, and stress testing for color-math."""

from __future__ import annotations

import time
import unittest

from color_math.config import ColorMathOptions
from color_math.converters.block import convert_text
from color_math.undo import uncolor_text
try:
    from .latex_validator import validate_latex_output
except ImportError:
    from tests.latex_validator import validate_latex_output


class AdversarialTests(unittest.TestCase):
    maxDiff = None

    def assert_resilient(
        self,
        source: str,
        options: ColorMathOptions | None = None,
        check_syntax: bool = True,
    ) -> str:
        """Verify no unhandled crash, strict undo recovery, and idempotency."""
        converted = convert_text(source, options=options)
        self.assertIsInstance(converted, str)

        # Idempotence: converting again produces identical result
        re_converted = convert_text(converted, options=options)
        self.assertEqual(
            re_converted,
            converted,
            f"Idempotency failed on:\n{source}\n\nConverted:\n{converted}\n\nRe-converted:\n{re_converted}",
        )

        # Lossless Undo: uncolor restores original text
        uncolored = uncolor_text(converted)
        self.assertEqual(
            uncolored,
            source,
            f"Lossless undo failed on:\n{source}\n\nGot:\n{uncolored}",
        )

        if check_syntax:
            validate_latex_output(converted)

        return converted

    def test_unclosed_braces_and_delimiters(self) -> None:
        """Pathological unclosed braces and delimiters must not crash or corrupt source."""
        cases = [
            r"$$\frac{a}{b$$",
            r"$$\sqrt{x$$",
            r"$$x^{2$$",
            r"$$x_{i$$",
            r"$$\left( x + y$$",
            r"$$\left[ \frac{a}{b} \right$$",
            r"$$\begin{bmatrix} a & b \\ c & d$$",
            r"$$\begin{aligned} a &= b \\ c &= d$$",
            r"$$x + {{{{y}}}} + {{{{z$$",
        ]
        opts = ColorMathOptions.all_enabled()
        for case in cases:
            with self.subTest(case=case):
                # We skip KaTeX balance check since input itself has unbalanced braces,
                # but assert resilient conversion, idempotency, and undo restoration.
                self.assert_resilient(case, options=None, check_syntax=False)
                self.assert_resilient(case, options=opts, check_syntax=False)

    def test_empty_and_degenerate_equations(self) -> None:
        """Empty or minimal equations must not cause index or key errors."""
        cases = [
            "$$$$",
            "$$\n$$",
            "$$\n\n\n$$",
            r"$$\frac{}{}$$",
            r"$$\sqrt{}$$",
            r"$$^{}$$",
            r"$$_{}$$",
            r"$$\begin{bmatrix}\end{bmatrix}$$",
            r"$$\begin{aligned}\end{aligned}$$",
            r"$$\quad$$",
            r"$$\,$$",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assert_resilient(case, options=None)
                self.assert_resilient(case, options=ColorMathOptions.all_enabled())

    def test_pathological_comments(self) -> None:
        """Hostile comment placements must not detach syntax or corrupt output."""
        cases = [
            # Comment inside fraction numerator
            "$$\\frac{a % note\n}{b}$$",
            # Comment inside fraction denominator
            "$$\\frac{a}{b % note\n}$$",
            # Comment right before closing $$
            "$$x + y % trailing note\n$$",
            # Comment without trailing newline at EOF
            "$$x + y % eof note",
            # Comment containing LaTeX math delimiter $$
            "$$x + % $$ inside comment\ny$$",
            # Comment containing unbalanced open brace
            "$$x + % { unclosed brace\ny$$",
            # Comment containing unbalanced close brace
            "$$x + % } unmatched brace\ny$$",
            # Comment on each line of an aligned block
            (
                "$$\\begin{aligned}\n"
                "  a &= b \\\\ % line 1\n"
                "  c &= d \\\\ % line 2\n"
                "\\end{aligned}$$"
            ),
            # Comment inside matrix rows
            (
                "$$\\begin{bmatrix}\n"
                "  1 & 2 \\\\ % row 1\n"
                "  3 & 4    % row 2\n"
                "\\end{bmatrix}$$"
            ),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assert_resilient(case, options=None)
                self.assert_resilient(case, options=ColorMathOptions.all_enabled())

    def test_extreme_nesting_depth(self) -> None:
        """25-level nested constructs must not trigger RecursionError or slow down."""
        # 25-level nested fraction
        frac = "x"
        for _ in range(25):
            frac = rf"\frac{{1}}{{{frac}}}"
        self.assert_resilient(f"$${frac}$$", options=None)
        self.assert_resilient(f"$${frac}$$", options=ColorMathOptions.all_enabled())

        # 25-level nested square roots
        rad = "x"
        for _ in range(25):
            rad = rf"\sqrt{{{rad}}}"
        self.assert_resilient(f"$${rad}$$", options=None)
        self.assert_resilient(f"$${rad}$$", options=ColorMathOptions.all_enabled())

        # 25-level nested function composition
        nested_fn = "x"
        for fn in ["f", "g", "h", r"\sin", r"\cos"] * 5:
            nested_fn = f"{fn}({nested_fn})"
        self.assert_resilient(f"$${nested_fn}$$", options=None)
        self.assert_resilient(f"$${nested_fn}$$", options=ColorMathOptions.all_enabled())

    def test_escaped_character_shields(self) -> None:
        """Escaped characters (\\%, \\_, \\$, \\&, \\#) must remain shielded from parsers."""
        cases = [
            r"$$\text{50\% of } x = 0.5x$$",
            r"$$\mathbf{var\_name} = 10$$",
            r"$$\text{Price: \$100} + f(x)$$",
            r"$$\text{A \& B} \implies C$$",
            r"$$\text{\#1 priority} = x$$",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assert_resilient(case, options=None)
                self.assert_resilient(case, options=ColorMathOptions.all_enabled())

    def test_macro_prefix_and_name_collisions(self) -> None:
        """Macros that share prefixes with functions must not be shredded or misidentified."""
        cases = [
            # \sinh vs \sin
            r"$$\sinh(x) + \sin(x)$$",
            # \cosh vs \cos
            r"$$\cosh(x) + \cos(x)$$",
            # \partial vs custom commands
            r"$$\partial_\mu F^{\mu\nu} = J^\nu$$",
            # Custom operators starting with standard operator stems
            r"$$\operatorname{single}(x) + \operatorname{rank}(A)$$",
            r"$$\operatorname*{arg\,min}_{x} f(x)$$",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assert_resilient(case, options=None)
                self.assert_resilient(case, options=ColorMathOptions.all_enabled())

    def test_massive_document_scale_and_linear_performance(self) -> None:
        """5000-line Markdown document with hundreds of equations must process in < 3s."""
        doc_lines = ["# Massive Document Benchmark\n"]
        for i in range(250):
            doc_lines.append(f"## Section {i}\n")
            doc_lines.append(f"Here is inline $f_{i}(x) = x^{i} + \\sin(x)$ for step {i}.\n")
            doc_lines.append(
                "$$\n"
                f"\\int_0^{i+1} \\frac{{d}}{{dx}} \\left[ \\ln(1 + x^{i+1}) \\right] dx = \\lim_{{t \\to {i}}} g(t)\n"
                "$$\n"
            )
        doc = "\n".join(doc_lines)

        start = time.perf_counter()
        converted = convert_text(doc)
        elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 3.5, f"Scaling failed: took {elapsed:.2f}s for 5000 lines")
        self.assertEqual(uncolor_text(converted), doc)
        self.assertEqual(convert_text(converted), converted)


if __name__ == "__main__":
    unittest.main()
