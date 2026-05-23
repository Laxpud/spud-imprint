from PIL import Image, ImageDraw, ImageFont, ImageFilter

class VirtualCanvas:
    """
    虚拟画布类，用于统一水印的物理尺寸（单位：毫米）
    现在保持照片原始分辨率不变，只缩放画布尺寸
    """
    def __init__(self, original_image, layout_mode="fit", bg_color=(255, 255, 255), 
                 canvas_aspect_ratio=None, margin_mm=None, margin_relative=None,
                 corner_radius_mm=None, corner_radius_relative=None,
                 shadow_enabled=False, shadow_offset_mm=(2, 2), shadow_offset_relative=None,
                 shadow_blur_radius=10, shadow_blur_relative=None, shadow_color=(0, 0, 0, 128)):
        """
        初始化虚拟画布（单位：毫米）
        
        新增参数:
            corner_radius_mm: 圆角半径（毫米），None表示无圆角
            corner_radius_relative: 圆角半径相对值（基于画布最小边长的比例，0-1之间）
            shadow_enabled: 是否启用阴影效果
            shadow_offset_mm: 阴影偏移量（毫米），例如(2, 2)表示右下偏移
            shadow_offset_relative: 阴影偏移相对值（基于画布尺寸的比例，0-1之间）
            shadow_blur_radius: 阴影模糊半径（像素）
            shadow_blur_relative: 阴影模糊半径相对值（基于画布最小边长的比例，0-1之间）
            shadow_color: 阴影颜色（RGBA元组）
        """
        self.original_image = original_image
        self.img_width, self.img_height = original_image.size
        self.layout_mode = layout_mode
        self.bg_color = bg_color
        self.canvas_aspect_ratio = canvas_aspect_ratio
        self.margin_mm = margin_mm
        self.margin_relative = margin_relative
        
        # 新增圆角和阴影参数
        self.corner_radius_mm = corner_radius_mm
        self.corner_radius_relative = corner_radius_relative
        self.shadow_enabled = shadow_enabled
        self.shadow_offset_mm = shadow_offset_mm
        self.shadow_offset_relative = shadow_offset_relative
        self.shadow_blur_radius = shadow_blur_radius
        self.shadow_blur_relative = shadow_blur_relative
        self.shadow_color = shadow_color
        
        # 获取原始图像DPI（如果存在）
        try:
            self.original_dpi = original_image.info['dpi'][0]
        except (KeyError, TypeError):
            self.original_dpi = 300  # 默认值
        
        # 根据布局模式计算画布尺寸（内容区域尺寸，不包括margin）
        self._calculate_canvas_size()
        
        # 应用margin调整最终画布尺寸和偏移
        self._apply_margin()
        
        # 计算相对值参数的实际像素值
        self._calculate_relative_values()
    
    def _calculate_canvas_size(self):
        """根据布局模式计算画布尺寸"""
        if self.layout_mode == "original":
            # 原始大小：画布尺寸等于照片尺寸
            self.width_px = self.img_width
            self.height_px = self.img_height
            
            # 如果指定了长宽比，调整画布尺寸
            if self.canvas_aspect_ratio is not None:
                img_ratio = self.img_width / self.img_height
                if img_ratio > self.canvas_aspect_ratio:
                    # 照片比目标比例宽，增加高度
                    self.height_px = int(self.width_px / self.canvas_aspect_ratio)
                else:
                    # 照片比目标比例高，增加宽度
                    self.width_px = int(self.height_px * self.canvas_aspect_ratio)
            
        elif self.layout_mode == "fit":
            # 适应模式：保持照片宽高比，在包含边距的空间内
            if self.canvas_aspect_ratio is not None:
                # 使用指定的画布长宽比
                img_ratio = self.img_width / self.img_height
                if img_ratio > self.canvas_aspect_ratio:
                    # 照片宽，所以画布宽度为照片宽度，高度根据比例计算
                    self.width_px = self.img_width
                    self.height_px = int(self.width_px / self.canvas_aspect_ratio)
                else:
                    # 照片高，所以画布高度为照片高度，宽度根据比例计算
                    self.height_px = self.img_height
                    self.width_px = int(self.height_px * self.canvas_aspect_ratio)
            else:
                # 使用照片原始比例
                self.width_px = self.img_width
                self.height_px = self.img_height
            
        elif self.layout_mode == "fill":
            # 填充模式：照片被扩展的背景包围，照片保持原始尺寸
            if self.canvas_aspect_ratio is not None:
                target_ratio = self.canvas_aspect_ratio
            else:
                target_ratio = self.img_width / self.img_height
                
            img_ratio = self.img_width / self.img_height
            
            if img_ratio > target_ratio:
                # 宽图片：画布宽度为照片宽度，高度根据目标比例计算
                self.width_px = self.img_width
                self.height_px = int(self.width_px / target_ratio)
            else:
                # 高图片：画布高度为照片高度，宽度根据目标比例计算
                self.height_px = self.img_height
                self.width_px = int(self.height_px * target_ratio)
            
        elif self.layout_mode == "stretch":
            # 拉伸模式：画布与照片宽高比相同，但扩展到包括边距
            if self.canvas_aspect_ratio is not None:
                target_ratio = self.canvas_aspect_ratio
            else:
                target_ratio = self.img_width / self.img_height
                
            # 设置画布尺寸为目标比例，照片居中
            if target_ratio > self.img_width / self.img_height:
                # 目标比例更宽，以高度为基准
                self.height_px = self.img_height
                self.width_px = int(self.height_px * target_ratio)
            else:
                # 目标比例更高，以宽度为基准
                self.width_px = self.img_width
                self.height_px = int(self.width_px / target_ratio)

        # 计算照片在内容区域中的偏移（居中）
        self.image_x_offset = (self.width_px - self.img_width) // 2
        self.image_y_offset = (self.height_px - self.img_height) // 2
    
    def _apply_margin(self):
        """
        应用margin设置，调整最终画布尺寸和内容区域偏移
        """
        # 如果没有设置margin，则最终画布就是内容区域，偏移为0
        if self.margin_relative is None and self.margin_mm is None:
            self.final_width_px = self.width_px
            self.final_height_px = self.height_px
            self.content_x_offset = 0
            self.content_y_offset = 0
        else:
            if self.margin_relative is not None:
                r = self.margin_relative
                # 计算最终画布尺寸：内容区域占 (1 - 2*r) 的比例
                # 例如，margin_relative=0.05，则内容区域占90%，最终画布尺寸 = 内容尺寸 / 0.9
                self.final_width_px = int(self.width_px / (1 - 2*r))
                self.final_height_px = int(self.height_px / (1 - 2*r))
                # 内容区域在最终画布上的偏移
                self.content_x_offset = int(r * self.final_width_px)
                self.content_y_offset = int(r * self.final_height_px)
            else:
                # 使用margin_mm
                margin_px = self.mm_to_px(self.margin_mm)
                self.final_width_px = self.width_px + 2 * margin_px
                self.final_height_px = self.height_px + 2 * margin_px
                self.content_x_offset = margin_px
                self.content_y_offset = margin_px

        # 更新画布尺寸为最终尺寸（包括margin）
        self.width_px = self.final_width_px
        self.height_px = self.final_height_px

        # 调整照片偏移：照片在内容区域中的偏移加上内容区域的偏移
        self.image_x_offset += self.content_x_offset
        self.image_y_offset += self.content_y_offset    
    
    def _calculate_relative_values(self):
        """计算相对值参数的实际像素值"""
        # 计算画布最小边长（用于相对值参考）
        self.min_canvas_dimension = min(self.width_px, self.height_px)
        
        # 计算圆角半径（优先使用相对值）
        if self.corner_radius_relative is not None:
            self.corner_radius_px = int(self.min_canvas_dimension * self.corner_radius_relative)
        elif self.corner_radius_mm is not None:
            self.corner_radius_px = self.mm_to_px(self.corner_radius_mm)
        else:
            self.corner_radius_px = 0
        
        # 计算阴影偏移（优先使用相对值）
        if self.shadow_offset_relative is not None:
            self.shadow_offset_x_px = int(self.width_px * self.shadow_offset_relative[0])
            self.shadow_offset_y_px = int(self.height_px * self.shadow_offset_relative[1])
        elif self.shadow_offset_mm is not None:
            self.shadow_offset_x_px = self.mm_to_px(self.shadow_offset_mm[0])
            self.shadow_offset_y_px = self.mm_to_px(self.shadow_offset_mm[1])
        else:
            self.shadow_offset_x_px = 0
            self.shadow_offset_y_px = 0
        
        # 计算阴影模糊半径（优先使用相对值）
        if self.shadow_blur_relative is not None:
            self.shadow_blur_px = int(self.min_canvas_dimension * self.shadow_blur_relative)
        else:
            self.shadow_blur_px = self.shadow_blur_radius 

    def _apply_round_corners(self, image):
        """应用圆角效果到图像，返回带透明度的图像"""
        if self.corner_radius_px == 0:
            return image
        
        # 确保图像是RGBA模式以支持透明度
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 创建蒙版图像
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        
        # 绘制圆角矩形作为蒙版
        draw.rounded_rectangle([(0, 0), image.size], radius=self.corner_radius_px, fill=255)
        
        # 应用蒙版到图像
        image.putalpha(mask)
        return image
    
    def _create_shadow_image(self):
        """创建阴影图像，基于圆角照片"""
        from PIL import ImageFilter

        img_width, img_height = self.original_image.size

        # 计算阴影图像大小（原图大小加上模糊扩展）
        expansion = self.shadow_blur_px * 2
        shadow_width = img_width + expansion * 2
        shadow_height = img_height + expansion * 2

        # 创建透明背景的阴影图像
        shadow_image = Image.new('RGBA', (shadow_width, shadow_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow_image)
        
        # 绘制圆角矩形作为阴影形状
        draw.rounded_rectangle([(expansion, expansion), (expansion + img_width, expansion + img_height)], 
                              radius=self.corner_radius_px, fill=self.shadow_color)

        # 应用高斯模糊效果
        shadow_image = shadow_image.filter(ImageFilter.GaussianBlur(radius=self.shadow_blur_px))
        return shadow_image
    
    def mm_to_px(self, mm):
        """将毫米转换为像素（使用原始图像DPI）"""
        return int(mm * self.original_dpi / 25.4)
    
    def px_to_mm(self, px):
        """将像素转换为毫米（使用原始图像DPI）"""
        return px * 25.4 / self.original_dpi
    
    def create_canvas(self):
        """创建并返回一个空白画布图像（最终尺寸，包括margin）"""
        return Image.new('RGB', (self.width_px, self.height_px), self.bg_color)
    
    def add_blurred_background(self, canvas_image, blur_radius=20, scale_factor=None, 
                              extra_scale=1.2, opacity=100, fit_mode="cover"):
        """
        将基于原始照片的高斯模糊背景添加到现有画布上
        
        参数:
            canvas_image: 现有的画布Image对象
            blur_radius: 高斯模糊半径，值越大越模糊（默认20）
            scale_factor: 手动指定的缩放系数，如果为None则自动计算（默认None）
            extra_scale: 自动计算时的额外缩放倍率，确保背景比画布大（默认1.2）
            opacity: 背景透明度，0-100，100为完全不透明（默认100）
            fit_mode: 填充模式，"cover"（覆盖）或"contain"（包含），默认"cover"
            
        返回:
            Image: 添加了模糊背景的画布图像
        """
        # 如果没有指定缩放因子，则自动计算
        if scale_factor is None:
            # 计算画布和原始图像的宽高比
            canvas_ratio = self.width_px / self.height_px
            image_ratio = self.img_width / self.img_height
            
            if fit_mode == "cover":
                # 覆盖模式：确保背景覆盖整个画布
                if image_ratio > canvas_ratio:
                    # 图像比画布宽，以高度为基准缩放
                    scale_factor = (self.height_px / self.img_height) * extra_scale
                else:
                    # 图像比画布高，以宽度为基准缩放
                    scale_factor = (self.width_px / self.img_width) * extra_scale
            else:
                # 包含模式：确保整个图像在画布内可见
                if image_ratio > canvas_ratio:
                    # 图像比画布宽，以宽度为基准缩放
                    scale_factor = (self.width_px / self.img_width) * extra_scale
                else:
                    # 图像比画布高，以高度为基准缩放
                    scale_factor = (self.height_px / self.img_height) * extra_scale
        
        # 计算放大后的尺寸
        scaled_width = int(self.img_width * scale_factor)
        scaled_height = int(self.img_height * scale_factor)
        
        # 放大原始图像
        scaled_image = self.original_image.resize(
            (scaled_width, scaled_height), 
            Image.LANCZOS
        )
        
        # 应用高斯模糊
        blurred_image = scaled_image.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # 如果需要调整透明度
        if opacity < 100:
            # 确保图像是RGBA模式
            if blurred_image.mode != 'RGBA':
                blurred_image = blurred_image.convert('RGBA')
            
            # 创建透明度图层
            alpha = blurred_image.split()[3]
            alpha = alpha.point(lambda p: p * opacity / 100)
            blurred_image.putalpha(alpha)
        
        # 计算居中位置
        x_offset = (self.width_px - scaled_width) // 2
        y_offset = (self.height_px - scaled_height) // 2
        
        # 将模糊图像粘贴到画布上
        if blurred_image.mode == 'RGBA':
            canvas_image.paste(blurred_image, (x_offset, y_offset), blurred_image)
        else:
            canvas_image.paste(blurred_image, (x_offset, y_offset))
        
        return canvas_image
    
    def add_photo_to_canvas(self, canvas_image):
        """将原始照片添加到画布中心（考虑margin偏移），并应用圆角和阴影效果"""
        # 如果启用阴影，先添加阴影
        if self.shadow_enabled:
            shadow_image = self._create_shadow_image()
            expansion = self.shadow_blur_px * 2
            shadow_pos_x = self.image_x_offset + self.shadow_offset_x_px - expansion
            shadow_pos_y = self.image_y_offset + self.shadow_offset_y_px - expansion
            canvas_image.paste(shadow_image, (shadow_pos_x, shadow_pos_y), shadow_image)

        # 应用圆角效果（如果需要）
        photo_to_paste = self._apply_round_corners(self.original_image) if self.corner_radius_px > 0 else self.original_image
        
        # 将照片粘贴到画布上
        if photo_to_paste.mode == 'RGBA':
            canvas_image.paste(photo_to_paste, (self.image_x_offset, self.image_y_offset), photo_to_paste)
        else:
            canvas_image.paste(photo_to_paste, (self.image_x_offset, self.image_y_offset))
        
        return canvas_image