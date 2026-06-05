import tempfile
import unittest
from pathlib import Path

from spud_imprint.config import load_config, resolve_template_path


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

    def test_parses_ratio_string_as_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            config_path.write_text(
                """
[canvas]
aspect_ratio = "21:9"
""".strip(),
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertAlmostEqual(config.canvas.aspect_ratio, 21 / 9)

    def test_loads_named_template_from_project_templates_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_dir = root / "templates"
            template_dir.mkdir()
            (template_dir / "minimal.toml").write_text(
                """
[canvas]
blurred_background = false

[text]
color = [10, 20, 30]
""".strip(),
                encoding="utf-8",
            )

            config = load_config(template="minimal", project_root=root)

        self.assertFalse(config.canvas.blurred_background)
        self.assertEqual(config.text.color, (10, 20, 30))

    def test_config_file_overrides_template_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_dir = root / "templates"
            template_dir.mkdir()
            template_path = template_dir / "classic.toml"
            config_path = root / "config.toml"
            template_path.write_text(
                """
[batch]
quality = 80

[text]
alignment = "center"
""".strip(),
                encoding="utf-8",
            )
            config_path.write_text(
                """
[batch]
quality = 95
""".strip(),
                encoding="utf-8",
            )

            config = load_config(
                config_path,
                template="classic",
                project_root=root,
            )

        self.assertEqual(config.batch.quality, 95)
        self.assertEqual(config.text.alignment, "center")

    def test_resolves_template_path_without_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_dir = root / "templates"
            template_dir.mkdir()
            template_path = template_dir / "poster.toml"
            template_path.write_text(
                '[canvas]\naspect_ratio = "16:9"\n',
                encoding="utf-8",
            )

            resolved = resolve_template_path("poster", project_root=root)

        self.assertEqual(resolved, template_path)


if __name__ == "__main__":
    unittest.main()
