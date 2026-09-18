import unittest
from color_math.parsers.differentials import find_differential_spans
from color_math.adapters import transform_document
from color_math.config import ColorMathOptions


class TestUnicodeMath(unittest.TestCase):
    def test_unicode_partial_derivative_fractions(self):
        spans = find_differential_spans(r"i\hbar \frac{∂}{∂t} \Psi=\hat{H}\Psi")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].text, r"\frac{∂}{∂t}")
        self.assertEqual(spans[0].kind, "derivative_fraction")

    def test_unicode_partial_derivative_with_variable(self):
        spans = find_differential_spans(r"\frac{∂y}{∂t} = 0")
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].text, r"\frac{∂y}{∂t}")
        self.assertEqual(spans[0].kind, "derivative_fraction")

    def test_schrodinger_unicode_coloring(self):
        opts = ColorMathOptions(color_differentials=True, enable_taxonomy=True)
        raw = r"$$ i\hbar \frac{∂}{∂t} \Psi=\hat{H}\Psi$$"
        colored = transform_document(raw + "\n", "markdown", options=opts)
        self.assertIn(r"\textcolor{#bb9af7}{\frac{∂}{∂t}}", colored)
        self.assertIn(r"\textcolor{#e0af68}{\hbar}", colored)

    def test_schrodinger_all_unicode_coloring(self):
        opts = ColorMathOptions(color_differentials=True, enable_taxonomy=True)
        raw = r"$$ iℏ \frac{∂}{∂t} \Psi=\hat{H}\Psi$$"
        colored = transform_document(raw + "\n", "markdown", options=opts)
        self.assertIn(r"\textcolor{#bb9af7}{\frac{∂}{∂t}}", colored)
        self.assertIn(r"\textcolor{#e0af68}{ℏ}", colored)


if __name__ == "__main__":
    unittest.main()
