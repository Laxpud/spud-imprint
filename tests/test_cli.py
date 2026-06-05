import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from spud_imprint import __version__
from spud_imprint.cli import main


class CliTests(unittest.TestCase):
    def test_version_option_prints_package_version(self):
        output = StringIO()

        with self.assertRaises(SystemExit) as context:
            with redirect_stdout(output):
                main(["--version"])

        self.assertEqual(context.exception.code, 0)
        self.assertIn(f"spud-imprint {__version__}", output.getvalue())

    def test_validate_config_accepts_example_config_without_input_check(self):
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "validate-config",
                    "--config",
                    "examples/config.example.toml",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Config OK", output.getvalue())

    def test_validate_config_reports_invalid_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.toml"
            config_path.write_text(
                """
[batch]
quality = 0
""".strip(),
                encoding="utf-8",
            )

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "validate-config",
                        "--config",
                        str(config_path),
                    ]
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("batch.quality", output.getvalue())

    def test_validate_config_checks_input_when_override_is_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_input = Path(tmp) / "missing"

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "validate-config",
                        "--config",
                        "examples/config.example.toml",
                        "--input",
                        str(missing_input),
                    ]
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("batch.input_dir", output.getvalue())

    def test_batch_dry_run_lists_planned_outputs_without_processing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()
            Image.new("RGB", (40, 30), (120, 130, 140)).save(input_dir / "sample.jpg")

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
                            "examples/config.example.toml",
                            "--dry-run",
                            "--verbose",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        self.assertFalse(output_dir.exists())
        self.assertIn("Config:", output.getvalue())
        self.assertIn("DRY", output.getvalue())
        self.assertIn("sample_uniform_watermark.jpeg", output.getvalue())
        process_batch.assert_not_called()

    def test_batch_reports_empty_input_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()

            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "batch",
                        "--input",
                        str(input_dir),
                        "--output",
                        str(output_dir),
                        "--config",
                        "examples/config.example.toml",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("No supported images found.", output.getvalue())


if __name__ == "__main__":
    unittest.main()
