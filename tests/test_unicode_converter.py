import unittest
from color_math.converters.unicode_converter import (
    convert_latex_to_unicode,
    convert_unicode_to_latex,
    convert_document_math,
    UnicodeConversionOptions,
)


class TestUnicodeConverter(unittest.TestCase):
    def test_greek_bidirectional(self):
        # Default plane1
        self.assertEqual(convert_latex_to_unicode(r"\psi"), "𝜓")
        self.assertEqual(convert_unicode_to_latex("𝜓"), r"\psi")
        self.assertEqual(convert_unicode_to_latex("𝝍"), r"\psi")  # alias

        # Standard greek style
        opts_std = UnicodeConversionOptions(greek_style="standard")
        self.assertEqual(convert_latex_to_unicode(r"\psi", opts_std), "ψ")
        self.assertEqual(convert_unicode_to_latex("ψ"), r"\psi")

        # Uppercase
        self.assertEqual(convert_latex_to_unicode(r"\Psi"), "Ψ")
        self.assertEqual(convert_unicode_to_latex("Ψ"), r"\Psi")

    def test_differentials_and_constants(self):
        self.assertEqual(convert_latex_to_unicode(r"i\hbar \frac{\partial}{\partial t}\Psi"), r"iℏ \frac{∂}{∂t}Ψ")
        self.assertEqual(convert_unicode_to_latex(r"iℏ \frac{∂}{∂t}Ψ"), r"i\hbar \frac{\partial}{\partial t}\Psi")

    def test_indefinite_integral(self):
        # Indefinite integral converts to ∫
        self.assertEqual(convert_latex_to_unicode(r"\int f(x) dx"), "∫ f(x) dx")
        self.assertEqual(convert_unicode_to_latex("∫ f(x) dx"), r"\int f(x) dx")

    def test_definite_integral_option(self):
        # Default: preserve \int_a^b
        self.assertEqual(convert_latex_to_unicode(r"\int_0^1 x dx"), r"\int_0^1 x dx")
        self.assertEqual(convert_latex_to_unicode(r"\int_{a}^{b} f(x) dx"), r"\int_{a}^{b} f(x) dx")

        # Option enabled: convert to ∫_a^b
        opts_def = UnicodeConversionOptions(convert_definite_integrals=True)
        self.assertEqual(convert_latex_to_unicode(r"\int_0^1 x dx", opts_def), "∫_0^1 x dx")
        self.assertEqual(convert_latex_to_unicode(r"\int_{a}^{b} f(x) dx", opts_def), "∫_{a}^{b} f(x) dx")

        # Reverse always converts ∫_0^1 to \int_0^1
        self.assertEqual(convert_unicode_to_latex("∫_0^1 x dx"), r"\int_0^1 x dx")

    def test_delimiter_protection(self):
        # \left\langle must NOT be converted to \left⟨
        expr = r"\left\langle \frac{a}{b} \right\rangle"
        self.assertEqual(convert_latex_to_unicode(expr), expr)

        # \Bigl\lceil must NOT be converted to \Bigl⌈
        expr_ceil = r"\Bigl\lceil x \Bigr\rceil"
        self.assertEqual(convert_latex_to_unicode(expr_ceil), expr_ceil)

    def test_delimiter_auto_repair(self):
        # Broken syntax in math like \left⟨ \frac{a}{b} \right⟩ must be repaired to \left\langle ... \right\rangle
        broken = r"\left⟨ \frac{a}{b} \right⟩"
        expected = r"\left\langle \frac{a}{b} \right\rangle"
        self.assertEqual(convert_unicode_to_latex(broken), expected)

    def test_document_math_boundary(self):
        doc = (
            "# Physics Note\n\n"
            "The wave function is $\\psi(x, t)$ with probability density.\n\n"
            "```python\n"
            "psi = 42\n"
            "```\n\n"
            "$$\n"
            "i\\hbar \\frac{\\partial}{\\partial t} \\Psi = \\hat{H}\\Psi\n"
            "$$\n"
        )
        to_uni = convert_document_math(doc, "to-unicode")
        # Code block and heading preserved
        self.assertIn("psi = 42", to_uni)
        self.assertIn("# Physics Note", to_uni)
        # Math blocks converted
        self.assertIn("$𝜓(x, t)$", to_uni)
        self.assertIn("iℏ \\frac{∂}{∂t} Ψ = \\hat{H}Ψ", to_uni)

        to_tex = convert_document_math(to_uni, "to-latex")
        self.assertIn(r"$\psi(x, t)$", to_tex)
        self.assertIn(r"i\hbar \frac{\partial}{\partial t} \Psi = \hat{H}\Psi", to_tex)

    def test_prose_conversion_defaults(self):
        doc = (
            "Here \\psi is outside math, while $\\psi$ is inside math.\n"
            "Also inline code `\\psi` and code block:\n"
            "```\n"
            "\\psi in code\n"
            "```\n"
        )
        # to-unicode by default leaves prose \psi untouched, converts in math
        to_uni = convert_document_math(doc, "to-unicode")
        self.assertIn(r"Here \psi is outside math", to_uni)
        self.assertIn("$𝜓$ is inside math", to_uni)
        self.assertIn("`\\psi`", to_uni)
        self.assertIn("\\psi in code", to_uni)

        # to-unicode with convert_prose_to_unicode=True converts \psi to 𝜓 in prose
        opts_prose_uni = UnicodeConversionOptions(convert_prose_to_unicode=True)
        to_uni_prose = convert_document_math(doc, "to-unicode", opts_prose_uni)
        self.assertIn("Here 𝜓 is outside math", to_uni_prose)
        self.assertIn("$𝜓$ is inside math", to_uni_prose)

        # to-latex with convert_prose_to_latex=True DOES convert 𝜓 to \psi in prose
        opts_prose = UnicodeConversionOptions(convert_prose_to_latex=True)
        to_tex_prose = convert_document_math(to_uni_prose, "to-latex", opts_prose)
        self.assertIn(r"Here \psi is outside math", to_tex_prose)
        self.assertIn(r"$\psi$ is inside math", to_tex_prose)


if __name__ == "__main__":
    unittest.main()
