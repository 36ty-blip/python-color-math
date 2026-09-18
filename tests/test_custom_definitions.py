import unittest
from color_math.custom_definitions import sanitize_definition, CUSTOM_FUNCTIONS
from color_math.config import (
    COLOR_COMMANDS,
    FUNCTION_COMMANDS,
    MATH_CONSTANTS,
    RELATIONS,
    ALL_BARE_FUNCTIONS,
)
from color_math.converters.generic import color_latex_body


class TestCustomDefinitions(unittest.TestCase):
    def test_sanitize_definition(self):
        macro, bare = sanitize_definition("sinc()")
        self.assertEqual(macro, r"\sinc")
        self.assertEqual(bare, "sinc")

        macro, bare = sanitize_definition(r"\relu(x)")
        self.assertEqual(macro, r"\relu")
        self.assertEqual(bare, "relu")

    def test_registrations(self):
        self.assertIn(r"\relu", FUNCTION_COMMANDS)
        self.assertIn(r"\sinc", FUNCTION_COMMANDS)
        self.assertIn("sinc", ALL_BARE_FUNCTIONS)
        self.assertIn("relu", ALL_BARE_FUNCTIONS)
        self.assertTrue(r"\kB" in MATH_CONSTANTS or "kB" in MATH_CONSTANTS)
        self.assertIn(r"\coloneqq", RELATIONS)
        self.assertIn(r"\coloneqq", COLOR_COMMANDS)

    def test_color_rendering(self):
        colored_macro = color_latex_body(r"\relu(x)")
        self.assertIn(r"\textcolor{#7aa2f7}{\relu}", colored_macro)

        colored_bare = color_latex_body("relu(x)")
        self.assertIn(r"\textcolor{#7aa2f7}{relu}", colored_bare)

        colored_relation = color_latex_body(r"x \coloneqq 5")
        self.assertIn(r"\textcolor{white}{\coloneqq}", colored_relation)


if __name__ == "__main__":
    unittest.main()
