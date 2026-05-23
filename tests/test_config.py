import tempfile
import unittest
from pathlib import Path

from laxpud_imprint.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_nested_toml_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            config_path.write_text(
                """
[batch]
input_dir = "photos"
output_dir = "exports"
quality = 88

[canvas]
background_color = [1, 2, 3]
margin_relative = 0.1

[text]
fields = ["DateTimeOriginal", "FNumber"]
color = [255, 255, 255]
show_field_names = true
""".strip(),
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertEqual(config.batch.input_dir, "photos")
        self.assertEqual(config.batch.output_dir, "exports")
        self.assertEqual(config.batch.quality, 88)
        self.assertEqual(config.canvas.background_color, (1, 2, 3))
        self.assertEqual(config.canvas.margin_relative, 0.1)
        self.assertEqual(config.text.fields, ["DateTimeOriginal", "FNumber"])
        self.assertEqual(config.text.color, (255, 255, 255))
        self.assertTrue(config.text.show_field_names)


if __name__ == "__main__":
    unittest.main()
