"""Unit tests for YAML frontmatter and quantum note detection."""

import unittest
from color_math.parsers.frontmatter import detect_note_field, parse_frontmatter_text


class TestFrontmatterDetection(unittest.TestCase):
    def test_explicit_color_math_block(self):
        note = """---
title: Quantum Mechanics Notes
color-math:
  field: quantum
---
$$i\\hbar\\frac{\\partial}{\\partial t}\\psi = \\hat{H}\\psi$$
"""
        detection = detect_note_field(note)
        self.assertTrue(detection.is_quantum)
        self.assertEqual(detection.field, "quantum")
        self.assertTrue(detection.overrides.get("color_quantum_operators"))

    def test_inline_color_math_block(self):
        note = """---
color-math: { field: quantum }
---
"""
        detection = detect_note_field(note)
        self.assertTrue(detection.is_quantum)

    def test_standard_yaml_keys(self):
        keys = ["field", "subject", "topic", "discipline", "category"]
        for key in keys:
            note = f"""---
{key}: Quantum Mechanics
---
"""
            detection = detect_note_field(note)
            self.assertTrue(detection.is_quantum, f"Failed for key {key}")

    def test_tags_in_frontmatter(self):
        note = """---
tags:
  - physics
  - math
---
"""
        detection = detect_note_field(note)
        self.assertTrue(detection.is_quantum)

    def test_tags_flow_sequence(self):
        note = """---
tags: [notes, qm, lecture]
---
"""
        detection = detect_note_field(note)
        self.assertTrue(detection.is_quantum)

    def test_in_body_tags(self):
        note = """Regular note without YAML.
Studying #quantum-mechanics today.
$$i\\hbar\\frac{\\partial}{\\partial t}\\psi = E\\psi$$
"""
        detection = detect_note_field(note)
        self.assertTrue(detection.is_quantum)

    def test_unrelated_note_not_quantum(self):
        note = """---
subject: Calculus
topic: Integration
tags:
  - math
---
$$\\int x dx$$
"""
        detection = detect_note_field(note)
        self.assertFalse(detection.is_quantum)


if __name__ == "__main__":
    unittest.main()
