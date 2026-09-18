"""Unit tests for Quantum Mechanics operators in python-color-math."""

import unittest
from color_math.converters.block import convert_math_block
from color_math.config import DEFAULT_COLORS, ColorMathOptions


class TestQuantumOperators(unittest.TestCase):
    def setUp(self):
        self.quantum_palette = dict(DEFAULT_COLORS)
        self.quantum_palette["energy_operator"] = "#2ac3de"
        self.quantum_options = ColorMathOptions(
            color_quantum_operators=True,
            field="quantum",
        )

    def test_colors_energy_operator_standard(self):
        raw = "$$i\\hbar\\frac{\\partial}{\\partial t}\\psi$$"
        converted = convert_math_block(raw, palette=self.quantum_palette, options=self.quantum_options)
        self.assertIn(r"\textcolor{#2ac3de}{i\hbar\frac{\partial}{\partial t}}", converted)

    def test_colors_energy_operator_dfrac_spacing(self):
        raw = "$$i \\hbar \\dfrac{\\partial}{\\partial t}$$"
        converted = convert_math_block(raw, palette=self.quantum_palette, options=self.quantum_options)
        self.assertIn(r"\textcolor{#2ac3de}{i \hbar \dfrac{\partial}{\partial t}}", converted)

    def test_colors_energy_operator_partial_subscript(self):
        raw = "$$i\\hbar\\partial_t\\psi = \\hat{H}\\psi$$"
        converted = convert_math_block(raw, palette=self.quantum_palette, options=self.quantum_options)
        self.assertTrue(
            r"\textcolor{#2ac3de}{i\hbar\partial_t}" in converted
            or r"\textcolor{#2ac3de}{i\hbar\partial_{t}}" in converted
        )

    def test_colors_unicode_energy_operator(self):
        raw = "$$iℏ\\frac{∂}{∂t}𝜓$$"
        converted = convert_math_block(raw, palette=self.quantum_palette, options=self.quantum_options)
        self.assertIn(r"\textcolor{#2ac3de}{iℏ\frac{∂}{∂t}}", converted)

    def test_colors_momentum_operator_3d_and_1d(self):
        raw3d = "$$\\hat{\\mathbf{p}} = -i\\hbar\\nabla$$"
        converted3d = convert_math_block(raw3d, palette=self.quantum_palette, options=self.quantum_options)
        self.assertIn(r"\textcolor{#2ac3de}{-i\hbar\nabla}", converted3d)

        raw1d = "$$\\hat{p}_x = -i\\hbar\\frac{\\partial}{\\partial x}$$"
        converted1d = convert_math_block(raw1d, palette=self.quantum_palette, options=self.quantum_options)
        self.assertIn(r"\textcolor{#2ac3de}{-i\hbar\frac{\partial}{\partial x}}", converted1d)

    def test_colors_kinetic_energy_operator(self):
        raw = "$$\\hat{T} = -\\frac{\\hbar^2}{2m}\\nabla^2$$"
        converted = convert_math_block(raw, palette=self.quantum_palette, options=self.quantum_options)
        self.assertTrue(
            r"\textcolor{#2ac3de}{-\frac{\hbar^2}{2m}\nabla^2}" in converted
            or r"\textcolor{#2ac3de}{-\frac{\hbar^{2}}{2m}\nabla^{2}}" in converted
        )

    def test_colors_ladder_operator(self):
        raw = "$$\\hat{a}^\\dagger\\hat{a}$$"
        converted = convert_math_block(raw, palette=self.quantum_palette, options=self.quantum_options)
        self.assertTrue(
            r"\textcolor{#2ac3de}{\hat{a}^\dagger}" in converted
            or r"\textcolor{#2ac3de}{\hat{a}^{\dagger}}" in converted
        )

    def test_disabled_quantum_does_not_color_operator(self):
        raw = "$$i\\hbar\\frac{\\partial}{\\partial t}\\psi$$"
        converted = convert_math_block(raw, palette=DEFAULT_COLORS, options=ColorMathOptions(color_quantum_operators=False))
        self.assertNotIn(r"\textcolor{#2ac3de}{i\hbar\frac{\partial}{\partial t}}", converted)


if __name__ == "__main__":
    unittest.main()
