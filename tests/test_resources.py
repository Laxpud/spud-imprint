import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spud_imprint.config import ImprintConfig, resolve_template_path
from spud_imprint.pipeline import resolve_font_path
from spud_imprint.resources import resolve_existing_resource
from spud_imprint.validation import validate_config


class ResourceResolutionTests(unittest.TestCase):
    def test_resolves_resource_from_runtime_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resource = root / "assets" / "fonts" / "font.ttf"
            resource.parent.mkdir(parents=True)
            resource.write_bytes(b"fake font")

            with patch(
                "spud_imprint.resources.runtime_resource_roots",
                return_value=[root],
            ):
                resolved = resolve_existing_resource("assets/fonts/font.ttf")

        self.assertEqual(resolved, resource)

    def test_resolves_named_template_from_runtime_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "templates" / "minimal.toml"
            template.parent.mkdir(parents=True)
            template.write_text("[text]\nalignment = \"center\"\n", encoding="utf-8")

            with patch(
                "spud_imprint.config.runtime_resource_roots",
                return_value=[root],
            ):
                resolved = resolve_template_path("minimal")

        self.assertEqual(resolved, template)

    def test_font_validation_accepts_runtime_resource_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            font = root / "assets" / "fonts" / "font.ttf"
            input_dir = root / "input"
            font.parent.mkdir(parents=True)
            input_dir.mkdir()
            font.write_bytes(b"fake font")

            config = ImprintConfig()
            config.batch.input_dir = str(input_dir)
            config.text.font_name = "assets/fonts/font.ttf"

            with patch(
                "spud_imprint.resources.runtime_resource_roots",
                return_value=[root],
            ):
                validated = validate_config(config, project_root=root / "work")

        self.assertIs(validated, config)

    def test_pipeline_font_resolution_uses_runtime_resource_font(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            font = root / "assets" / "fonts" / "font.ttf"
            font.parent.mkdir(parents=True)
            font.write_bytes(b"fake font")

            with patch(
                "spud_imprint.resources.runtime_resource_roots",
                return_value=[root],
            ):
                resolved = resolve_font_path("assets/fonts/font.ttf")

        self.assertEqual(resolved, str(font))


if __name__ == "__main__":
    unittest.main()
