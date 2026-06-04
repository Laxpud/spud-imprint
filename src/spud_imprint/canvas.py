from PIL import Image, ImageDraw, ImageFilter


class VirtualCanvas:
    """虚拟画布：负责计算成品尺寸，并尽量保持原照片像素不被缩放。"""

    def __init__(
        self,
        original_image,
        frame_mode=None,
        layout_mode="fit",
        bg_color=(255, 255, 255),
        canvas_aspect_ratio=None,
        margin_mm=None,
        margin_relative=None,
        photo_margin_mm=None,
        photo_margin_relative=None,
        photo_margin_unit=None,
        margin_policy="minimum_edge",
        corner_radius_mm=None,
        corner_radius_relative=None,
        shadow_enabled=False,
        shadow_offset_mm=(2, 2),
        shadow_offset_relative=None,
        shadow_blur_radius=10,
        shadow_blur_relative=None,
        shadow_color=(0, 0, 0, 128),
    ):
        """保存画布参数，并立刻算出后续绘制会用到的尺寸和偏移。"""
        self.original_image = original_image
        self.img_width, self.img_height = original_image.size
        self.frame_mode = frame_mode
        self.layout_mode = layout_mode
        self.bg_color = tuple(bg_color)
        self.canvas_aspect_ratio = canvas_aspect_ratio
        self.margin_mm = margin_mm
        self.margin_relative = margin_relative
        self.photo_margin_mm = photo_margin_mm
        self.photo_margin_relative = photo_margin_relative
        self.photo_margin_unit = photo_margin_unit
        self.margin_policy = margin_policy
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

        # frame_mode 是新的“相框”逻辑：先直接算最终画布，再把照片居中放进去。
        if self.frame_mode:
            self._calculate_frame_layout()
        else:
            # 旧版布局先算内容区域，再额外套一圈全局边距。
            self._calculate_canvas_size()
            self._apply_margin()
        self._calculate_relative_values()

    def _calculate_frame_layout(self):
        """根据相框模式计算最终画布，并把照片放在画布中央。"""
        frame_mode = self.frame_mode.lower()
        if frame_mode == "photo_aspect":
            self._calculate_photo_aspect_frame()
        elif frame_mode == "fixed_aspect":
            self._calculate_fixed_aspect_frame()
        else:
            raise ValueError(f"Unsupported frame mode: {self.frame_mode}")

        self.image_x_offset = (self.width_px - self.img_width) // 2
        self.image_y_offset = (self.height_px - self.img_height) // 2

    def _resolve_margin_unit(self):
        """决定照片边距使用毫米还是相对比例。"""
        if self.photo_margin_unit is not None:
            return self.photo_margin_unit.lower()
        if self.photo_margin_mm is not None or self.margin_mm is not None:
            return "mm"
        return "relative"

    def _resolve_margin_mm(self):
        """读取照片边距的毫米值，并兼容旧配置里的 margin_mm。"""
        if self.photo_margin_mm is not None:
            return self.photo_margin_mm
        return self.margin_mm

    def _resolve_margin_relative(self):
        """读取照片边距的比例值，并兼容旧配置里的 margin_relative。"""
        if self.photo_margin_relative is not None:
            return self.photo_margin_relative
        if self.margin_relative is not None:
            return self.margin_relative
        return 0

    def _calculate_relative_photo_aspect_frame(self, margin_relative):
        """按照片原始比例扩出一圈相对边距。"""
        if margin_relative < 0 or margin_relative >= 0.5:
            raise ValueError("margin_relative must be >= 0 and < 0.5")

        # 边距占最终画布比例，所以需要反推画布比照片大多少。
        scale = 1 / (1 - 2 * margin_relative)
        self.width_px = int(round(self.img_width * scale))
        self.height_px = int(round(self.img_height * scale))

    def _calculate_mm_photo_aspect_frame(self, margin_mm):
        """按照片原始比例扩出一圈毫米边距。"""
        if margin_mm < 0:
            raise ValueError("margin_mm must be >= 0")

        margin_px = self.mm_to_px(margin_mm)
        policy = (self.margin_policy or "preserve_frame_ratio").lower()
        if policy == "equal_edges":
            # equal_edges 表示四边实际像素边距完全相同，成品比例会随照片变化。
            self.width_px = self.img_width + 2 * margin_px
            self.height_px = self.img_height + 2 * margin_px
            return

        # 默认保留照片比例：让短边拥有指定毫米边距，长边按比例一起放大。
        if self.img_width >= self.img_height:
            scale = (self.img_height + 2 * margin_px) / self.img_height
        else:
            scale = (self.img_width + 2 * margin_px) / self.img_width

        self.width_px = int(round(self.img_width * scale))
        self.height_px = int(round(self.img_height * scale))

    def _calculate_photo_aspect_frame(self):
        """选择相对边距或毫米边距来计算照片同比例相框。"""
        unit = self._resolve_margin_unit()
        if unit == "relative":
            self._calculate_relative_photo_aspect_frame(
                self._resolve_margin_relative()
            )
        elif unit == "mm":
            margin_mm = self._resolve_margin_mm()
            if margin_mm is None:
                raise ValueError("margin_mm is required when margin_unit is mm")
            self._calculate_mm_photo_aspect_frame(margin_mm)
        else:
            raise ValueError(f"Unsupported margin unit: {self.photo_margin_unit}")

    def _calculate_relative_fixed_aspect_frame(self, margin_relative):
        """在固定画布比例下，用相对边距反推足够大的画布。"""
        if self.canvas_aspect_ratio is None:
            raise ValueError("aspect_ratio is required when frame_mode is fixed_aspect")
        if margin_relative < 0 or margin_relative >= 0.5:
            raise ValueError("margin_relative must be >= 0 and < 0.5")

        # 横版画布优先用高度反推，竖版画布优先用宽度反推，避免照片越界。
        if self.canvas_aspect_ratio >= 1:
            height_for_photo_height = self.img_height / (1 - 2 * margin_relative)
            height_for_photo_width = self.img_width / (
                self.canvas_aspect_ratio - 2 * margin_relative
            )
            self.height_px = int(
                round(max(height_for_photo_height, height_for_photo_width))
            )
            self.width_px = int(round(self.height_px * self.canvas_aspect_ratio))
        else:
            width_for_photo_width = self.img_width / (1 - 2 * margin_relative)
            width_for_photo_height = self.img_height / (
                (1 / self.canvas_aspect_ratio) - 2 * margin_relative
            )
            self.width_px = int(round(max(width_for_photo_width, width_for_photo_height)))
            self.height_px = int(round(self.width_px / self.canvas_aspect_ratio))

    def _calculate_mm_fixed_aspect_frame(self, margin_mm):
        """在固定画布比例下，用毫米边距反推足够大的画布。"""
        if self.canvas_aspect_ratio is None:
            raise ValueError("aspect_ratio is required when frame_mode is fixed_aspect")
        if margin_mm < 0:
            raise ValueError("margin_mm must be >= 0")

        margin_px = self.mm_to_px(margin_mm)
        min_width = self.img_width + 2 * margin_px
        min_height = self.img_height + 2 * margin_px

        # 先得到能包住照片和边距的最小矩形，再沿固定比例补齐另一边。
        if min_width / min_height > self.canvas_aspect_ratio:
            self.width_px = min_width
            self.height_px = int(round(self.width_px / self.canvas_aspect_ratio))
        else:
            self.height_px = min_height
            self.width_px = int(round(self.height_px * self.canvas_aspect_ratio))

    def _calculate_fixed_aspect_frame(self):
        """选择相对边距或毫米边距来计算固定比例相框。"""
        unit = self._resolve_margin_unit()
        if unit == "relative":
            self._calculate_relative_fixed_aspect_frame(
                self._resolve_margin_relative()
            )
        elif unit == "mm":
            margin_mm = self._resolve_margin_mm()
            if margin_mm is None:
                raise ValueError("margin_mm is required when margin_unit is mm")
            self._calculate_mm_fixed_aspect_frame(margin_mm)
        else:
            raise ValueError(f"Unsupported margin unit: {self.photo_margin_unit}")

    def _calculate_canvas_size(self):
        """根据旧版 layout_mode 算内容区域尺寸。"""
        if self.layout_mode == "original":
            # original 从照片原尺寸开始；如果指定比例，只扩展不足的一边。
            self.width_px = self.img_width
            self.height_px = self.img_height

            if self.canvas_aspect_ratio is not None:
                img_ratio = self.img_width / self.img_height
                if img_ratio > self.canvas_aspect_ratio:
                    self.height_px = int(self.width_px / self.canvas_aspect_ratio)
                else:
                    self.width_px = int(self.height_px * self.canvas_aspect_ratio)

        elif self.layout_mode == "fit":
            # fit 保证整张照片完整放入目标比例画布，不裁切照片。
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
            # fill 让画布按目标比例铺满照片范围，适合后续做背景延展。
            target_ratio = self.canvas_aspect_ratio or self.img_width / self.img_height
            img_ratio = self.img_width / self.img_height

            if img_ratio > target_ratio:
                self.width_px = self.img_width
                self.height_px = int(self.width_px / target_ratio)
            else:
                self.height_px = self.img_height
                self.width_px = int(self.height_px * target_ratio)

        elif self.layout_mode == "stretch":
            # stretch 只改变画布比例，不改变照片本身，照片仍居中贴上去。
            target_ratio = self.canvas_aspect_ratio or self.img_width / self.img_height

            if target_ratio > self.img_width / self.img_height:
                self.height_px = self.img_height
                self.width_px = int(self.height_px * target_ratio)
            else:
                self.width_px = self.img_width
                self.height_px = int(self.width_px / target_ratio)
        else:
            raise ValueError(f"Unsupported layout mode: {self.layout_mode}")

        # 后续贴图只需要知道照片左上角相对画布的偏移。
        self.image_x_offset = (self.width_px - self.img_width) // 2
        self.image_y_offset = (self.height_px - self.img_height) // 2

    def _apply_margin(self):
        """给旧版布局套全局边距，并同步移动照片偏移。"""
        if self.margin_relative is None and self.margin_mm is None:
            self.final_width_px = self.width_px
            self.final_height_px = self.height_px
            self.content_x_offset = 0
            self.content_y_offset = 0
        elif self.margin_relative is not None:
            # 相对边距同样是“占最终画布的比例”，所以要从内容尺寸反推最终尺寸。
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

        # 画布变大后，照片和内容区域都要整体向右下移动边距距离。
        self.width_px = self.final_width_px
        self.height_px = self.final_height_px
        self.image_x_offset += self.content_x_offset
        self.image_y_offset += self.content_y_offset

    def _calculate_relative_values(self):
        """把相对圆角、阴影偏移和阴影模糊转换成像素值。"""
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
        """给照片叠加透明圆角遮罩。"""
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
        """创建一张比照片更大的透明阴影图，给模糊留出扩散空间。"""
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
        """按原图 DPI 把毫米换算成像素。"""
        return int(mm * self.original_dpi / 25.4)

    def px_to_mm(self, px):
        """按原图 DPI 把像素换算成毫米。"""
        return px * 25.4 / self.original_dpi

    def create_canvas(self):
        """创建一张纯色背景画布。"""
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
        """把原图放大并模糊后铺在背景上，用来填充照片外侧区域。"""
        if scale_factor is None:
            canvas_ratio = self.width_px / self.height_px
            image_ratio = self.img_width / self.img_height

            # cover 会保证背景盖满画布；contain 风格则优先保证背景不超出某一边。
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
            # 降低 alpha 可以让纯色画布和模糊背景混合，背景不会太抢眼。
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
        """把阴影和照片按已计算好的偏移贴到画布上。"""
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
