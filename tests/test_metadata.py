import unittest
import tempfile
from pathlib import Path

from PIL import Image

from spud_imprint.metadata import (
    empty_metadata,
    format_special_field,
    get_categorized_metadata,
    prepare_metadata_text,
)
from spud_imprint.text import TextStylePreset


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class MetadataTests(unittest.TestCase):
    def test_reads_small_exif_fixture(self):
        metadata = get_categorized_metadata(FIXTURE_DIR / "sample_exif.jpg")

        self.assertEqual(metadata["device_info"]["Make"], "Spud Imprint")
        self.assertEqual(metadata["device_info"]["Model"], "Fixture Camera")
        self.assertEqual(
            metadata["time_info"]["DateTimeOriginal"],
            "2026:06:05 20:30:00",
        )

    def test_handles_image_without_exif(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "no-exif.jpg"
            Image.new("RGB", (32, 24), (30, 60, 90)).save(image_path)

            metadata = get_categorized_metadata(image_path)

        self.assertEqual(metadata, empty_metadata())

    def test_formats_date_time_original_as_date(self):
        formatted = format_special_field("DateTimeOriginal", "2025:09:06 13:38:00")

        self.assertEqual(formatted, "2025-09-06")

    def test_prepares_selected_metadata_without_field_names(self):
        metadata = {
            "time_info": {"DateTimeOriginal": "2025:09:06 13:38:00"},
            "capture_settings": {},
        }
        style = TextStylePreset(show_field_names=False)

        lines = prepare_metadata_text(metadata, ["DateTimeOriginal"], style)

        self.assertEqual(lines, ["2025-09-06"])

    def test_prepares_missing_metadata_with_field_name(self):
        style = TextStylePreset(show_field_names=True)

        lines = prepare_metadata_text({"time_info": {}}, ["FNumber"], style)

        self.assertEqual(lines, ["FNumber: Not Found"])


if __name__ == "__main__":
    unittest.main()
