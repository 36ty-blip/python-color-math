import json
import tempfile
import unittest
from pathlib import Path

from color_math.config import (
    DEFAULT_COLORS,
    DEFAULT_UNICODE_CONFIG,
    ColorMathOptions,
    get_bundled_default_config,
    get_bundled_default_config_path,
    load_config,
    save_default_config,
)


class TestConfigTolerance(unittest.TestCase):
    def test_bundled_default_config_exists(self):
        path = get_bundled_default_config_path()
        self.assertTrue(path.exists(), f"Bundled default config {path} should exist")
        data = get_bundled_default_config()
        self.assertIn("theme", data)
        self.assertIn("colors", data)
        self.assertIn("options", data)
        self.assertIn("unicode", data)
        self.assertEqual(data["unicode"]["greek_style"], "plane1")

    def test_corrupt_json_safe_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            corrupt_file = Path(tmp_dir) / ".colormath.json"
            # Write invalid JSON (trailing comma and unquoted value)
            corrupt_file.write_text("{\n  'theme': broken,\n}\n", encoding="utf-8")

            # Should not raise ValueError or JSONDecodeError; safely falls back to defaults
            palette, options, unicode_config = load_config(corrupt_file)
            self.assertEqual(palette["main"], DEFAULT_COLORS["main"])
            self.assertEqual(unicode_config["greek_style"], "plane1")
            self.assertFalse(unicode_config["convert_definite_integrals"])

    def test_partial_user_config_merge(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            user_file = Path(tmp_dir) / ".colormath.json"
            # User only overrides one color and one unicode option
            custom_data = {
                "colors": {"main": "#ff0000"},
                "unicode": {"greek_style": "standard"},
            }
            user_file.write_text(json.dumps(custom_data), encoding="utf-8")

            palette, options, unicode_config = load_config(user_file)
            # Custom values applied
            self.assertEqual(palette["main"], "#ff0000")
            self.assertEqual(unicode_config["greek_style"], "standard")
            # All other defaults intact
            self.assertEqual(palette["orange"], DEFAULT_COLORS["orange"])
            self.assertFalse(unicode_config["convert_definite_integrals"])
            self.assertFalse(unicode_config["convert_prose_to_unicode"])

    def test_save_default_config_creates_reference(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / ".colormath.json"
            save_default_config(target)

            self.assertTrue(target.exists())
            # Also created .colormath.default.json reference alongside it
            default_ref = Path(tmp_dir) / ".colormath.default.json"
            self.assertTrue(default_ref.exists())

            # Data matches factory defaults
            loaded = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(loaded["theme"], "default")
            self.assertIn("unicode", loaded)


if __name__ == "__main__":
    unittest.main()
