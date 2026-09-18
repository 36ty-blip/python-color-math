import unittest
try:
    import pytest
    pytest.importorskip("IPython")
except ImportError:
    pass

from IPython.core.interactiveshell import InteractiveShell
from IPython.display import Math

from color_math.ipython import (
    ColorMath,
    colormath,
    load_ipython_extension,
    unload_ipython_extension,
)
from color_math.jupyter import notebook_pre_save_hook


class TestIPythonIntegration(unittest.TestCase):
    def setUp(self):
        self.shell = InteractiveShell.instance()

    def test_colormath_helper(self):
        # Fragment test (no dollar signs)
        frag = colormath(r"\int_0^1 x^2 dx = \frac{1}{3}", is_fragment=True)
        self.assertIn(r"\textcolor{#e0af68}{\int", frag)
        self.assertIn(r"\textcolor{white}{=}", frag)

        # Full markdown test
        md = colormath("Let $f(x) = x^2$.")
        self.assertIn(r"\textcolor{#7aa2f7}{f}", md)

    def test_colormath_display_object(self):
        obj = ColorMath(r"\frac{df}{dx} = f'(x)")
        self.assertIsInstance(obj, Math)
        self.assertIn(r"\textcolor{#7aa2f7}{f'}", obj.data)

    def test_load_and_unload_extension(self):
        load_ipython_extension(self.shell)
        self.assertTrue(self.shell.find_magic("color_math") is not None)
        self.assertTrue(self.shell.find_magic("colormath") is not None)
        self.assertTrue(self.shell.find_magic("color_math_auto") is not None)

        # Execute line magic
        result = self.shell.run_line_magic("color_math", r"\int x^2 dx")
        self.assertIsInstance(result, Math)
        self.assertIn(r"\textcolor{#e0af68}{\int", result.data)

        # Execute cell magic
        cell_body = "The equation is:\n$$ \\psi + \\omega $$"
        self.shell.run_cell_magic("color_math", "", cell_body)

        # Test auto hook
        self.shell.run_line_magic("color_math_auto", "on")
        # Creating a standard IPython Math object should now produce colored latex in _repr_latex_
        standard_math = Math(r"\int x^2 dx")
        repr_latex = standard_math._repr_latex_()
        self.assertIn(r"\textcolor{#e0af68}{\int", repr_latex)

        self.shell.run_line_magic("color_math_auto", "off")
        unload_ipython_extension(self.shell)

    def test_jupyter_pre_save_hook(self):
        model = {
            "type": "notebook",
            "content": {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "source": "Calculate $$\\int_0^1 x dx = \\frac{1}{2}$$.",
                    },
                    {
                        "cell_type": "code",
                        "source": "x = 1\nprint(x)",
                    },
                ]
            },
        }

        notebook_pre_save_hook(model)

        # Markdown cell was transformed
        md_cell = model["content"]["cells"][0]
        self.assertIn(r"\textcolor{#e0af68}{\int", md_cell["source"])

        # Code cell was untouched
        code_cell = model["content"]["cells"][1]
        self.assertEqual(code_cell["source"], "x = 1\nprint(x)")


if __name__ == "__main__":
    unittest.main()
