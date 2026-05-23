import unittest

from PIL import ImageFont

from laxpud_imprint.canvas import VirtualCanvas
from laxpud_imprint.text import TextStylePreset, calculate_text_positions


class TextPlacementTests(unittest.TestCase):
    def test_center_bottom_position_is_inside_canvas(self):
        image = __import__("PIL.Image").Image.new("RGB", (120, 80), (255, 255, 255))
        canvas = VirtualCanvas(
            image,
            canvas_aspect_ratio=16 / 9,
            margin_relative=0.05,
        )
        style = TextStylePreset(font_size_relative=0.05, alignment="left")
        font = ImageFont.load_default()

        positions = calculate_text_positions(
            canvas,
            ["2025-09-06"],
            style,
            font,
            position_preset="center bottom",
            margin_percent=0.05,
        )

        self.assertEqual(len(positions), 1)
        x, y = positions[0]
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertLess(x, canvas.width_px)
        self.assertLess(y, canvas.height_px)


if __name__ == "__main__":
    unittest.main()
