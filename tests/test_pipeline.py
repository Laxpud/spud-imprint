import tempfile
import unittest
from pathlib import Path

from PIL import Image, features

from spud_imprint.config import ImprintConfig
from spud_imprint.pipeline import process_batch


class PipelineTests(unittest.TestCase):
    def _minimal_config(self):
        config = ImprintConfig()
        config.canvas.blurred_background = False
        config.canvas.margin_relative = 0.02
        config.photo.shadow_enabled = False
        config.photo.corner_radius_relative = None
        config.text.font_name = "arial.ttf"
        config.text.font_size_relative = 0.04
        return config

    def test_process_batch_exports_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()

            source = input_dir / "sample.jpg"
            Image.new("RGB", (120, 80), (120, 130, 140)).save(source)

            config = self._minimal_config()

            results = process_batch(
                config,
                input_dir=input_dir,
                output_dir=output_dir,
                project_root=root,
            )

            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].ok, results[0].error)
            self.assertIsNotNone(results[0].output)
            self.assertTrue(results[0].output.exists())
            self.assertEqual(results[0].output.suffix, ".jpeg")

    def test_process_batch_exports_different_output_formats(self):
        formats = {"JPEG": ".jpeg", "PNG": ".png"}
        if features.check("webp"):
            formats["WEBP"] = ".webp"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            input_dir.mkdir()
            source = input_dir / "sample.jpg"
            Image.new("RGB", (120, 80), (120, 130, 140)).save(source)

            for output_format, expected_suffix in formats.items():
                with self.subTest(output_format=output_format):
                    config = self._minimal_config()
                    config.batch.format = output_format
                    output_dir = root / f"output-{output_format.lower()}"

                    results = process_batch(
                        config,
                        input_dir=input_dir,
                        output_dir=output_dir,
                        project_root=root,
                    )

                    self.assertEqual(len(results), 1)
                    self.assertTrue(results[0].ok, results[0].error)
                    self.assertIsNotNone(results[0].output)
                    self.assertEqual(results[0].output.suffix, expected_suffix)
                    with Image.open(results[0].output) as exported:
                        self.assertEqual(exported.format, output_format)


if __name__ == "__main__":
    unittest.main()
