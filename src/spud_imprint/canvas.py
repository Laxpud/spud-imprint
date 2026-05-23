from PIL import Image, ImageDraw, ImageFilter


class VirtualCanvas:
    """Canvas that keeps the source photo at original pixel size."""

    def __init__(
        self,
        original_image,
        layout_mode="fit",
        bg_color=(255, 255, 255),
        canvas_aspect_ratio=None,
        margin_mm=None,
        margin_relative=None,
        corner_radius_mm=None,
        corner_radius_relative=None,
        shadow_enabled=False,
        shadow_offset_mm=(2, 2),
        shadow_offset_relative=None,
        shadow_blur_radius=10,
        shadow_blur_relative=None,
        shadow_color=(0, 0, 0, 128),
    ):
        self.original_image = original_image
        self.img_width, self.img_height = original_image.size
        self.layout_mode = layout_mode
        self.bg_color = tuple(bg_color)
        self.canvas_aspect_ratio = canvas_aspect_ratio
        self.margin_mm = margin_mm
        self.margin_relative = margin_relative
        self.corner_radius_mm = corner_radius_mm
        self.corner_radius_relative = corner_radius_relative
        self.shadow_enabled = shadow_enabled
        self.shadow_offset_mm = shadow_offset_mm
        self.shadow_offset_relative = shadow_offset_relative
        self.shadow_blur_radius = shadow_blur_radius
        self.shadow_blur_relative = shadow_blur_relative
        self.shadow_color = tuple(shadow_color)

        try:
            self.original_dpi = original_image.info["dpi"][0]
        except (KeyError, TypeError, IndexError):
            self.original_dpi = 300

        self._calculate_canvas_size()
        self._apply_margin()
        self._calculate_relative_values()

    def _calculate_canvas_size(self):
        if self.layout_mode == "original":
            self.width_px = self.img_width
            self.height_px = self.img_height

            if self.canvas_aspect_ratio is not None:
                img_ratio = self.img_width / self.img_height
                if img_ratio > self.canvas_aspect_ratio:
                    self.height_px = int(self.width_px / self.canvas_aspect_ratio)
                else:
                    self.width_px = int(self.height_px * self.canvas_aspect_ratio)

        elif self.layout_mode == "fit":
            if self.canvas_aspect_ratio is not None:
                img_ratio = self.img_width / self.img_height
                if img_ratio > self.canvas_aspect_ratio:
                    self.width_px = self.img_width
                    self.height_px = int(self.width_px / self.canvas_aspect_ratio)
                else:
                    self.height_px = self.img_height
                    self.width_px = int(self.height_px * self.canvas_aspect_ratio)
            else:
                self.width_px = self.img_width
                self.height_px = self.img_height

        elif self.layout_mode == "fill":
            target_ratio = self.canvas_aspect_ratio or self.img_width / self.img_height
            img_ratio = self.img_width / self.img_height

            if img_ratio > target_ratio:
                self.width_px = self.img_width
                self.height_px = int(self.width_px / target_ratio)
            else:
                self.height_px = self.img_height
                self.width_px = int(self.height_px * target_ratio)

        elif self.layout_mode == "stretch":
            target_ratio = self.canvas_aspect_ratio or self.img_width / self.img_height

            if target_ratio > self.img_width / self.img_height:
                self.height_px = self.img_height
                self.width_px = int(self.height_px * target_ratio)
            else:
                self.width_px = self.img_width
                self.height_px = int(self.width_px / target_ratio)
        else:
            raise ValueError(f"Unsupported layout mode: {self.layout_mode}")

        self.image_x_offset = (self.width_px - self.img_width) // 2
        self.image_y_offset = (self.height_px - self.img_height) // 2

    def _apply_margin(self):
        if self.margin_relative is None and self.margin_mm is None:
            self.final_width_px = self.width_px
            self.final_height_px = self.height_px
            self.content_x_offset = 0
            self.content_y_offset = 0
        elif self.margin_relative is not None:
            r = self.margin_relative
            if r < 0 or r >= 0.5:
                raise ValueError("margin_relative must be >= 0 and < 0.5")
            self.final_width_px = int(self.width_px / (1 - 2 * r))
            self.final_height_px = int(self.height_px / (1 - 2 * r))
            self.content_x_offset = int(r * self.final_width_px)
            self.content_y_offset = int(r * self.final_height_px)
        else:
            margin_px = self.mm_to_px(self.margin_mm)
            self.final_width_px = self.width_px + 2 * margin_px
            self.final_height_px = self.height_px + 2 * margin_px
            self.content_x_offset = margin_px
            self.content_y_offset = margin_px

        self.width_px = self.final_width_px
        self.height_px = self.final_height_px
        self.image_x_offset += self.content_x_offset
        self.image_y_offset += self.content_y_offset

    def _calculate_relative_values(self):
        self.min_canvas_dimension = min(self.width_px, self.height_px)

        if self.corner_radius_relative is not None:
            self.corner_radius_px = int(
                self.min_canvas_dimension * self.corner_radius_relative
            )
        elif self.corner_radius_mm is not None:
            self.corner_radius_px = self.mm_to_px(self.corner_radius_mm)
        else:
            self.corner_radius_px = 0

        if self.shadow_offset_relative is not None:
            self.shadow_offset_x_px = int(
                self.width_px * self.shadow_offset_relative[0]
            )
            self.shadow_offset_y_px = int(
                self.height_px * self.shadow_offset_relative[1]
            )
        elif self.shadow_offset_mm is not None:
            self.shadow_offset_x_px = self.mm_to_px(self.shadow_offset_mm[0])
            self.shadow_offset_y_px = self.mm_to_px(self.shadow_offset_mm[1])
        else:
            self.shadow_offset_x_px = 0
            self.shadow_offset_y_px = 0

        if self.shadow_blur_relative is not None:
            self.shadow_blur_px = int(
                self.min_canvas_dimension * self.shadow_blur_relative
            )
        else:
            self.shadow_blur_px = self.shadow_blur_radius

    def _apply_round_corners(self, image):
        if self.corner_radius_px == 0:
            return image

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), image.size], radius=self.corner_radius_px, fill=255)
        image.putalpha(mask)
        return image

    def _create_shadow_image(self):
        img_width, img_height = self.original_image.size
        expansion = self.shadow_blur_px * 2
        shadow_width = img_width + expansion * 2
        shadow_height = img_height + expansion * 2

        shadow_image = Image.new("RGBA", (shadow_width, shadow_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow_image)
        draw.rounded_rectangle(
            [(expansion, expansion), (expansion + img_width, expansion + img_height)],
            radius=self.corner_radius_px,
            fill=self.shadow_color,
        )
        return shadow_image.filter(ImageFilter.GaussianBlur(radius=self.shadow_blur_px))

    def mm_to_px(self, mm):
        return int(mm * self.original_dpi / 25.4)

    def px_to_mm(self, px):
        return px * 25.4 / self.original_dpi

    def create_canvas(self):
        return Image.new("RGB", (self.width_px, self.height_px), self.bg_color)

    def add_blurred_background(
        self,
        canvas_image,
        blur_radius=20,
        scale_factor=None,
        extra_scale=1.2,
        opacity=100,
        fit_mode="cover",
    ):
        if scale_factor is None:
            canvas_ratio = self.width_px / self.height_px
            image_ratio = self.img_width / self.img_height

            if fit_mode == "cover":
                if image_ratio > canvas_ratio:
                    scale_factor = (self.height_px / self.img_height) * extra_scale
                else:
                    scale_factor = (self.width_px / self.img_width) * extra_scale
            elif image_ratio > canvas_ratio:
                scale_factor = (self.width_px / self.img_width) * extra_scale
            else:
                scale_factor = (self.height_px / self.img_height) * extra_scale

        scaled_width = int(self.img_width * scale_factor)
        scaled_height = int(self.img_height * scale_factor)
        scaled_image = self.original_image.resize((scaled_width, scaled_height), Image.LANCZOS)
        blurred_image = scaled_image.filter(ImageFilter.GaussianBlur(blur_radius))

        if opacity < 100:
            if blurred_image.mode != "RGBA":
                blurred_image = blurred_image.convert("RGBA")
            alpha = blurred_image.split()[3]
            alpha = alpha.point(lambda p: p * opacity / 100)
            blurred_image.putalpha(alpha)

        x_offset = (self.width_px - scaled_width) // 2
        y_offset = (self.height_px - scaled_height) // 2

        if blurred_image.mode == "RGBA":
            canvas_image.paste(blurred_image, (x_offset, y_offset), blurred_image)
        else:
            canvas_image.paste(blurred_image, (x_offset, y_offset))

        return canvas_image

    def add_photo_to_canvas(self, canvas_image):
        if self.shadow_enabled:
            shadow_image = self._create_shadow_image()
            expansion = self.shadow_blur_px * 2
            shadow_pos_x = self.image_x_offset + self.shadow_offset_x_px - expansion
            shadow_pos_y = self.image_y_offset + self.shadow_offset_y_px - expansion
            canvas_image.paste(shadow_image, (shadow_pos_x, shadow_pos_y), shadow_image)

        if self.corner_radius_px > 0:
            photo_to_paste = self._apply_round_corners(self.original_image)
        else:
            photo_to_paste = self.original_image

        if photo_to_paste.mode == "RGBA":
            canvas_image.paste(
                photo_to_paste,
                (self.image_x_offset, self.image_y_offset),
                photo_to_paste,
            )
        else:
            canvas_image.paste(photo_to_paste, (self.image_x_offset, self.image_y_offset))

        return canvas_image
