"""Extreme Adversarial Robustness Test Suite for Python Color Math.

Tests edge cases, 'cursed' TeX syntax, TeX primitive token expansion,
cell-boundary preservation, and unconventional valid LaTeX constructs.
"""

import re
import unittest
from color_math.converters.block import convert_math_block, convert_text
from color_math.undo import uncolor_fragment, uncolor_text
from color_math.config import DEFAULT_COLORS, ColorMathOptions


def check_brace_balance(tex: str) -> bool:
    """Ensure all curly braces are balanced and not escaped."""
    depth = 0
    i = 0
    while i < len(tex):
        if tex[i] == "\\" and i + 1 < len(tex):
            i += 2  # skip escaped characters like \{ or \}
            continue
        if tex[i] == "%":
            # skip LaTeX comment
            nl = tex.find("\n", i)
            if nl == -1:
                break
            i = nl + 1
            continue
        if tex[i] == "{":
            depth += 1
        elif tex[i] == "}":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def check_no_cell_crossing_textcolor(tex: str) -> bool:
    """Verify that no \\textcolor{...}{...} wrapper crosses an '&' or '\\\\' table cell boundary."""
    # Find all \textcolor{...}{...} blocks
    pattern = re.compile(r"\\textcolor\{[^{}]+\}\{")
    pos = 0
    while True:
        m = pattern.search(tex, pos)
        if not m:
            break
        start_body = m.end()
        # Find matching close brace
        depth = 1
        j = start_body
        while j < len(tex) and depth > 0:
            if tex[j] == "\\" and j + 1 < len(tex):
                j += 2
                continue
            if tex[j] == "{":
                depth += 1
            elif tex[j] == "}":
                depth -= 1
            j += 1
        body = tex[start_body : j - 1]
        # In LaTeX, \textcolor cannot wrap across alignment '&' or row separator '\\'
        if "&" in body or "\\\\" in body:
            return False
        pos = start_body
    return True


class TestExtremeAdversarial(unittest.TestCase):
    def setUp(self):
        self.palette = dict(DEFAULT_COLORS)
        self.palette["energy_operator"] = "#2ac3de"
        self.options = ColorMathOptions.all_enabled()
        self.options.color_quantum_operators = True
        self.options.field = "quantum"

    def _verify_equation_integrity(self, raw_eq: str):
        """Runs the complete suite of invariants against an equation."""
        colored = convert_math_block(raw_eq, palette=self.palette, options=self.options)

        # 1. Brace balancing check
        self.assertTrue(
            check_brace_balance(colored),
            f"Brace mismatch in colored output:\nOriginal: {raw_eq}\nColored: {colored}",
        )

        # 2. Alignment boundary check (Misplaced & / Missing \cr)
        self.assertTrue(
            check_no_cell_crossing_textcolor(colored),
            f"\\textcolor crossed '&' or '\\\\' alignment cell:\n{colored}",
        )

        # 3. Idempotency (coloring already-colored LaTeX must not change or double-wrap)
        recolored = convert_math_block(colored, palette=self.palette, options=self.options)
        self.assertEqual(
            colored,
            recolored,
            f"Coloring is not idempotent:\nFirst pass: {colored}\nSecond pass: {recolored}",
        )

        # 4. Clean lossless undo
        uncolored = uncolor_fragment(colored)
        self.assertNotIn(
            r"\textcolor",
            uncolored,
            f"Residual \\textcolor tags remain after uncolor:\n{uncolored}",
        )
        self.assertTrue(
            check_brace_balance(uncolored),
            f"Brace mismatch in uncolored output:\n{uncolored}",
        )

    # -------------------------------------------------------------------------
    # Category 1: Zero-Brace Macro Eating (TeX Single-Token Expansion)
    # -------------------------------------------------------------------------
    def test_braceless_fractions_and_operators(self):
        cases = [
            r"$$\frac\partial\partial t \psi = E\psi$$",
            r"$$\frac12 x + \frac\hbar2m = 0$$",
            r"$$\sqrt2 x + \sqrt\pi y$$",
            r"$$\partial_t\psi+\nabla\cdot\mathbf{j}=0$$",
            r"$$\frac\partial{\partial t}\psi$$",
            r"$$\frac{\partial}\partial x$$",
            r"$$x^2_3 + y_i^2$$",
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 2: Illegal Cell-Crossing Boundaries (& and \\)
    # -------------------------------------------------------------------------
    def test_aligned_environments_with_tabs_and_newlines(self):
        cases = [
            r"""$$\begin{aligned}
    i\hbar \frac{\partial \psi}{\partial t} &= \hat{H}\psi \\
    \hat{\mathbf{p}} &= -i\hbar \nabla
\end{aligned}$$""",
            r"""$$\begin{cases}
    \frac{df}{dx} = 1 & \text{if } x > 0 \\
    \frac{df}{dx} = 0 & \text{otherwise}
\end{cases}$$""",
            r"""$$\begin{matrix}
    a & b & c \\
    d & e & f
\end{matrix}$$""",
            r"""$$\begin{split}
    A &= B + C \\
      &= D
\end{split}$$""",
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 3: Delimiter Anarchy
    # -------------------------------------------------------------------------
    def test_asymmetric_and_escaped_delimiters(self):
        cases = [
            r"$$\left[ 0, 1 \right)$$",  # half-open interval
            r"$$\left. \frac{\partial f}{\partial x} \right|_{x=0} = 42$$",  # evaluation bar with \left.
            r"$$\{ x \in \mathbb{R} \mid x > 0 \}$$",  # escaped set braces
            r"$$\langle \psi | \hat{H} | \phi \rangle$$",  # Dirac 3-pipe bra-ket
            r"$$\left( \frac{a}{b} \right\}$$",  # mismatched parenthesis and curly bracket
            r"$$| \psi \rangle \langle \phi |$$",  # projector
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 4: Math-in-Text-in-Math
    # -------------------------------------------------------------------------
    def test_math_inside_text_inside_math(self):
        cases = [
            r"$$\int_0^1 f(x)\,dx \quad \text{where $f(x) = \frac{1}{x}$ for all $x > 0$}$$",
            r"$$x = 1 \quad \text{since $\frac{df}{dx} = 0$}$$",
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 5: Infix TeX Primitive \over
    # -------------------------------------------------------------------------
    def test_infix_over_primitive(self):
        cases = [
            r"$${i\hbar {\partial \psi \over \partial t} = \hat{H}\psi}$$",
            r"$${a + b \over c + d} = 1$$",
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 6: Tensor Index Staggering & Empty Groups
    # -------------------------------------------------------------------------
    def test_tensor_indices_and_empty_groups(self):
        cases = [
            r"$$T^{\mu}{}_{\nu\rho} + R^\lambda{}_{\mu\nu\sigma} = 0$$",
            r"$$g_{\mu\nu;\rho} = 0$$",
            r"$$x_{} + y^{} = z$$",  # empty sub/superscript groups
            r"$$A^{\mu}_{\phantom{\mu}\nu} B^{\nu}$$",  # phantom spacing
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 7: Prime Clustering & Negative Micro-Spacing
    # -------------------------------------------------------------------------
    def test_primes_and_micro_spacing(self):
        cases = [
            r"$$f'''(x) + f''(x) + y' = 0$$",
            r"$$f'(g(x))' \cdot g'(x)$$",
            r"$$\iint \! f(x,y) \, dx\,dy$$",
            r"$$\frac{d^n\!f}{dx^n}$$",
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Category 8: Identifier Collisions
    # -------------------------------------------------------------------------
    def test_identifier_collisions(self):
        cases = [
            r"$$d = v \cdot t$$",  # variable 'd' is not a differential!
            r"$$x \text{ in } A$$",  # 'in' inside text is not \in
            r"$$\mathbf{d}x = \mathbf{d}y$$",  # bold d is vector, not differential
            r"$$\operatorname{Re} z \neq \mathrm{Re}$$",  # Real part vs Reynolds number
            r"$$\sin x + \cos y$$",  # unparenthesized trig functions
            r"$$\fractal = 1$$",  # starts with 'frac'
        ]
        for eq in cases:
            self._verify_equation_integrity(eq)

    # -------------------------------------------------------------------------
    # Document-Level Stress Test (Prose & Multi-block)
    # -------------------------------------------------------------------------
    def test_full_document_stress(self):
        doc = """---
field: quantum
tags: [physics, qm]
---
# Quantum & Field Theory Notes

Here is an equation with inline math $\\frac\\partial\\partial t \\psi$ and text.

```python
# Code block should remain completely untouched
def compute():
    return "frac{1}{2}"
```

Now a complex multi-line aligned system:
$$\\begin{aligned}
    i\\hbar \\frac{\\partial \\psi}{\\partial t} &= \\hat{H}\\psi \\\\
    \\hat{\\mathbf{p}} &= -i\\hbar \\nabla
\\end{aligned}$$

Half-open interval $\\left[ 0, 1 \\right)$ and set $\\{ x \\in \\mathbb{R} \\mid x > 0 \\}$.

End of note.
"""
        converted = convert_text(doc, palette=self.palette, options=self.options)

        # Ensure frontmatter and code block are pristine
        self.assertIn("```python\n# Code block should remain completely untouched", converted)
        self.assertIn("field: quantum", converted)

        # Check alignment boundaries
        self.assertTrue(check_no_cell_crossing_textcolor(converted))
        self.assertTrue(check_brace_balance(converted))

        # Check idempotency
        reconverted = convert_text(converted, palette=self.palette, options=self.options)
        self.assertEqual(converted, reconverted)

        # Check undo
        uncolored = uncolor_text(converted)
        self.assertNotIn(r"\textcolor", uncolored)
        self.assertIn(r"i\hbar \frac{\partial \psi}{\partial t}", uncolored)


if __name__ == "__main__":
    unittest.main()
