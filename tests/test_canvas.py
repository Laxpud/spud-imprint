import unittest

from PIL import Image

from spud_imprint.canvas import VirtualCanvas


class CanvasLayoutTests(unittest.TestCase):
    def test_photo_aspect_frame_keeps_equal_relative_margins(self):
        image = Image.new("RGB", (200, 100), (255, 255, 255))

        canvas = VirtualCanvas(
            image,
            frame_mode="photo_aspect",
            photo_margin_unit="relative",
            photo_margin_relative=0.1,
        )

        self.assertEqual(canvas.width_px, 250)
        self.assertEqual(canvas.height_px, 125)
        self.assertEqual(canvas.image_x_offset, 25)
        self.assertEqual(canvas.image_y_offset, 12)

    def test_fixed_aspect_frame_keeps_configured_nearest_margin(self):
        image = Image.new("RGB", (200, 100), (255, 255, 255))

        canvas = VirtualCanvas(
            image,
            frame_mode="fixed_aspect",
            canvas_aspect_ratio=16 / 9,
            photo_margin_unit="relative",
            photo_margin_relative=0.1,
        )

        margins = [
            canvas.image_x_offset,
            canvas.width_px - canvas.image_x_offset - image.width,
            canvas.image_y_offset,
            canvas.height_px - canvas.image_y_offset - image.height,
        ]

        self.assertAlmostEqual(canvas.width_px / canvas.height_px, 16 / 9, places=2)
        self.assertLessEqual(abs(min(margins) - canvas.height_px * 0.1), 1)


if __name__ == "__main__":
    unittest.main()
