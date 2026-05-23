import unittest

from spud_imprint.metadata import format_special_field, prepare_metadata_text
from spud_imprint.text import TextStylePreset


class MetadataTests(unittest.TestCase):
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
