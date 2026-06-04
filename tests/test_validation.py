import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from spud_imprint.cli import main
from spud_imprint.config import ImprintConfig
from spud_imprint.validation import ConfigValidationError, validate_config


class ConfigValidationTests(unittest.TestCase):
    def _valid_config(self, root):
        config = ImprintConfig()
        input_dir = root / "input"
        font_file = root / "font.ttf"
        input_dir.mkdir()
        font_file.write_bytes(b"fake font")
        config.batch.input_dir = str(input_dir)
        config.text.font_name = str(font_file)
        return config

    def test_accepts_valid_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._valid_config(root)

            validated = validate_config(config, project_root=root)

        self.assertIs(validated, config)

    def test_reports_all_invalid_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ImprintConfig()
            config.batch.input_dir = str(root / "missing-input")
            config.batch.quality = 101
            config.batch.format = "TIFF"
            config.canvas.layout_mode = "crop"
            config.canvas.margin_relative = 0.5
            config.canvas.blur_fit_mode = "tile"
            config.photo.shadow_color = (0, 0, 0)
            config.text.color = (255, 255, 255, 255)
            config.text.alignment = "justify"
            config.text.position_preset = "middle center"
            config.text.font_name = "missing-font.ttf"

            with self.assertRaises(ConfigValidationError) as context:
                validate_config(config, project_root=root)

        message = str(context.exception)
        self.assertIn("batch.quality", message)
        self.assertIn("batch.format", message)
        self.assertIn("canvas.layout_mode", message)
        self.assertIn("canvas.margin_relative", message)
        self.assertIn("canvas.blur_fit_mode", message)
        self.assertIn("photo.shadow_color", message)
        self.assertIn("text.color", message)
        self.assertIn("text.alignment", message)
        self.assertIn("text.position_preset", message)
        self.assertIn("text.font_name", message)
        self.assertIn("batch.input_dir", message)

    def test_uses_cli_input_override_when_validating_input_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._valid_config(root)
            override_input = root / "override-input"
            override_input.mkdir()
            config.batch.input_dir = str(root / "missing-input")

            validate_config(config, project_root=root, input_dir=override_input)

    def test_cli_stops_before_processing_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "output"
            config_path = root / "config.toml"
            input_dir.mkdir()
            config_path.write_text(
                """
[batch]
quality = 0

[text]
font_name = "missing-font.ttf"
""".strip(),
                encoding="utf-8",
            )

            output = StringIO()
            with patch("spud_imprint.cli.process_batch") as process_batch:
                with redirect_stdout(output):
                    exit_code = main(
                        [
                            "batch",
                            "--input",
                            str(input_dir),
                            "--output",
                            str(output_dir),
                            "--config",
                            str(config_path),
                        ]
                    )

        self.assertEqual(exit_code, 2)
        self.assertIn("Invalid configuration", output.getvalue())
        process_batch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
