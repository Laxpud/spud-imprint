from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import os

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

# 其余代码保持不变...
class TextStylePreset:
    """
    文本样式配置类，支持物理尺寸（毫米）和相对尺寸（基于画布大小）
    """
    def __init__(self, font_size_mm=5, font_size_relative=None, text_color=(50, 50, 50), 
                 font_name="arial.ttf", background_color=(220, 220, 220, 128),
                 alignment="left", line_spacing=1.5, show_field_names=True):
        """
        初始化文本样式配置
        
        参数:
            font_size_mm: 字体物理高度（毫米）（默认5mm）
            font_size_relative: 字体相对大小（基于画布高度的比例，0-1之间）
            text_color: 文字颜色 (RGB元组，默认深灰色)
            font_name: 字体文件路径或名称（默认"arial.ttf"）
            background_color: 文字阴影/背景颜色 (RGBA元组，默认半透明白色)
            alignment: 文本对齐方式 ("left", "center", "right")
            line_spacing: 行间距倍数（默认1.5倍行高）
            show_field_names: 是否显示元数据字段名称 (True/False)
        """
        self.font_size_mm = font_size_mm
        self.font_size_relative = font_size_relative
        self.text_color = text_color
        self.font_name = font_name
        self.background_color = background_color
        self.alignment = alignment
        self.line_spacing = line_spacing
        self.show_field_names = show_field_names
    
    def get_font_size_px(self, canvas):
        """根据画布获取字体大小的像素值"""
        if self.font_size_relative is not None:
            # 使用相对大小（基于画布短边）
            return int(min(canvas.height_px, canvas.width_px) * self.font_size_relative)
        else:
            # 使用绝对大小（毫米）
            return canvas.mm_to_px(self.font_size_mm)

def add_photo_to_canvas(original_image, canvas):
    """
    将照片添加到画布上
    
    参数:
        original_image: 原始PIL Image对象
        canvas: VirtualCanvas对象
        
    返回:
        Image: 带照片的画布Image对象
    """
    canvas_image = canvas.create_canvas()
    
    # 缩放图像（如果需要）
    if canvas.layout_mode != "original":
        resized_image = original_image.resize(
            (canvas.image_width_px, canvas.image_height_px), 
            Image.LANCZOS
        )
    else:
        resized_image = original_image
    
    # 将图像粘贴到画布上
    canvas_image.paste(resized_image, (canvas.image_x_offset, canvas.image_y_offset))
    
    return canvas_image

# 辅助函数：格式化特殊元数据字段（保持不变）
def format_special_field(field, value):
    """对特殊字段进行格式化处理"""
    if field == "ExposureTime":
        if value < 1:
            return f"1/{int(1/value)}s"
        return f"{value}s"
    elif field in ["FocalLength", "FocalLengthIn35mmFilm"]:
        return f"{value}mm"
    elif field == "FNumber":
        return f"f/{value}"
    elif field == "DateTimeOriginal":
        try:
            date_part = value.split(" ")[0]
            return date_part.replace(":", "-")
        except:
            return value
    return value

# 准备元数据文本函数（保持不变）
def prepare_metadata_text(metadata, fields_to_draw, text_style):
    """
    准备要显示的元数据文本内容
    """
    display_lines = []
    
    for field in fields_to_draw:
        value = None
        for category in metadata.values():
            if field in category:
                value = format_special_field(field, category[field])
                break
        
        if value is None:
            text = f"{field}: Not Found" if text_style.show_field_names else "Not Found"
        else:
            text = f"{field}: {value}" if text_style.show_field_names else str(value)
        
        display_lines.append(text)
    
    return display_lines

# 获取分类元数据函数（保持不变）
def get_categorized_metadata(image_path):
    """
    读取图像元数据并进行智能分类
    
    参数:
        image_path: 图像文件路径 (str)
    
    返回:
        dict: 包含8个分类类别的字典
    """
    # 1. 定义元数据分类映射
    CATEGORY_MAP = {
        # 设备信息类
        "Make": "device_info",
        "Model": "device_info",
        "BodySerialNumber": "device_info",
        "LensModel": "device_info",
        "LensSerialNumber": "device_info",
        
        # 拍摄参数类
        "ExposureTime": "capture_settings",
        "FNumber": "capture_settings",
        "ISOSpeedRatings": "capture_settings",
        "FocalLength": "capture_settings",
        "FocalLengthIn35mmFilm": "capture_settings",
        "ApertureValue": "capture_settings",
        "ShutterSpeedValue": "capture_settings",
        "MaxApertureValue": "capture_settings",
        "ExposureBiasValue": "capture_settings",
        "SceneCaptureType": "capture_settings",
        
        # 时间信息类
        "DateTimeOriginal": "time_info",
        "DateTimeDigitized": "time_info",
        "SubsecTimeOriginal": "time_info",
        "OffsetTimeOriginal": "time_info",
        "OffsetTimeDigitized": "time_info",
        "OffsetTime": "time_info",
        
        # 后期处理类
        "Software": "post_processing",
        "DateTime": "post_processing",  # 文件修改时间
        
        # 版权信息类
        "Artist": "copyright_info",
        "Copyright": "copyright_info",
        
        # 技术参数类
        "WhiteBalance": "technical_params",
        "MeteringMode": "technical_params",
        "ExposureProgram": "technical_params",
        "Flash": "technical_params",
        "ColorSpace": "technical_params",
        "DigitalZoomRatio": "technical_params",
        "Contrast": "technical_params",
        "Saturation": "technical_params",
        "Sharpness": "technical_params",
        "GainControl": "technical_params",
        
        # 传感器数据类
        "FocalPlaneXResolution": "sensor_data",
        "FocalPlaneYResolution": "sensor_data",
        "FocalPlaneResolutionUnit": "sensor_data",
        "SensingMethod": "sensor_data"
    }
    
    # 2. 初始化分类字典
    categorized = {
        "device_info": {},
        "capture_settings": {},
        "time_info": {},
        "post_processing": {},
        "copyright_info": {},
        "technical_params": {},
        "sensor_data": {},
        "other": {}
    }
    
    try:
        # 3. 打开图像并提取原始EXIF数据
        with Image.open(image_path) as img:
            exif_data = img._getexif() or {}
            
            # 4. 处理并分类每个元数据项
            for tag_id, value in exif_data.items():
                # 获取可读标签名
                tag_name = TAGS.get(tag_id, tag_id)
                
                # 确定分类（默认为"other"）
                category = CATEGORY_MAP.get(tag_name, "other")
                
                # 添加到对应分类
                categorized[category][tag_name] = value
                
        return categorized
        
    except (IOError, AttributeError, KeyError) as e:
        print(f"处理图像时出错: {e}")
        return categorized  # 返回空分类结构

def prepare_metadata_text(metadata, fields_to_draw, text_style):
    """
    准备要显示的元数据文本内容
    
    参数:
        metadata: 分类元数据字典
        fields_to_draw: 要显示的字段列表
        text_style: 文本样式配置对象
        
    返回:
        list: 格式化后的文本行列表
    """
    display_lines = []
    
    for field in fields_to_draw:
        # 在所有分类中搜索该字段
        value = None
        for category in metadata.values():
            if field in category:
                value = format_special_field(field, category[field])
                break
        
        # 根据是否显示字段名来格式化文本
        if value is None:
            text = f"{field}: Not Found" if text_style.show_field_names else "Not Found"
        else:
            text = f"{field}: {value}" if text_style.show_field_names else str(value)
        
        display_lines.append(text)
    
    return display_lines

def calculate_text_positions(canvas, text_lines, text_style, font, 
                           position_preset="center middle", margin_percent=0.05):
    """
    计算文本块的位置（多行文本作为一个整体定位），使用预设位置和百分比边距
    
    参数:
        canvas: VirtualCanvas对象
        text_lines: 文本行列表
        text_style: 文本样式配置
        font: 字体对象
        position_preset: 位置预设 (水平位置"left"/"center"/"right" 垂直位置"top"/"middle"/"bottom")
        margin_percent: 边距百分比 (0-1)
        
    返回:
        list: 每行文本的坐标位置 [(x, y), ...]
    """
    # 获取画布尺寸（像素）
    canvas_width_px = canvas.width_px
    canvas_height_px = canvas.height_px
    
    # 解析位置预设
    parts = position_preset.lower().split()
    horizontal = parts[0] if len(parts) > 0 else "center"
    vertical = parts[1] if len(parts) > 1 else "middle"
    
    # 计算整体边距（像素）
    margin_x = int(canvas_width_px * margin_percent)
    margin_y = int(canvas_height_px * margin_percent)
    
    # 计算文本块高度（基于行高）
    line_height = int(text_style.get_font_size_px(canvas) * text_style.line_spacing)
    text_block_height = len(text_lines) * line_height
    
    # 创建绘图对象用于测量文本尺寸
    with Image.new("RGB", (10, 10)) as tmp_img:
        draw = ImageDraw.Draw(tmp_img)        
        # 计算每行的宽度
        line_widths = []
        for line in text_lines:
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox(line)
                width = bbox[2] - bbox[0]
            elif hasattr(font, 'getsize'):
                width = font.getsize(line)[0]
            else:
                try:
                    width = int(draw.textlength(line, font=font))
                except AttributeError:
                    width = len(line) * font.size
            line_widths.append(width)
    
    # 确定最宽行的宽度
    max_width = max(line_widths) if line_widths else 0
    
    # 计算垂直位置
    if vertical == "top":
        start_y = margin_y
    elif vertical == "bottom":
        start_y = canvas_height_px - margin_y - text_block_height
    else:  # middle
        start_y = (canvas_height_px - text_block_height) // 2
    
    # 生成位置列表
    positions = []
    for i, line in enumerate(text_lines):
        # 根据预设的水平位置确定基准x坐标
        if horizontal == "left":
            base_x = margin_x
        elif horizontal == "right":
            base_x = canvas_width_px - margin_x - max_width
        else:  # center
            base_x = (canvas_width_px - max_width) // 2
        
        # 根据对齐方式计算具体的x坐标
        if text_style.alignment == "right":
            x = base_x - line_widths[i]
        elif text_style.alignment == "center":
            x = base_x - (line_widths[i] // 2)
        else:  # left
            x = base_x
        
        y = start_y + i * line_height
        positions.append((x, y))
    
    return positions

def add_text_to_canvas(canvas_image, canvas, metadata, fields_to_draw, 
                      text_style=None, position_mm=(20, 20), 
                      position_preset=None, margin_percent=0.05):
    """
    添加文本到画布上（使用物理尺寸定位和 sizing）
    
    参数:
        canvas_image: 已包含照片的画布Image对象
        canvas: VirtualCanvas对象
        metadata: 分类元数据字典
        fields_to_draw: 要显示的字段列表
        text_style: 文本样式配置对象
        position_mm: 文本位置（毫米）(x, y) - 绝对定位
        position_preset: 位置预设 (水平位置"left"/"center"/"right" 垂直位置"top"/"middle"/"bottom")
        margin_percent: 边距百分比 (0-1) - 仅当使用position_preset时有效
        
    返回:
        Image: 带文本的画布Image对象
    """
    if text_style is None:
        text_style = TextStylePreset()
    
    # 准备要显示的文本内容
    display_text = prepare_metadata_text(metadata, fields_to_draw, text_style)
    
    # 创建绘图对象
    draw = ImageDraw.Draw(canvas_image)
    
    # 获取字体大小（像素）
    font_size_px = text_style.get_font_size_px(canvas)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype(text_style.font_name, font_size_px)
    except IOError:
        font = ImageFont.load_default()
        font.size = font_size_px
    
    # 计算文本位置
    if position_preset:
        # 使用预设位置
        positions = calculate_text_positions(
            canvas, 
            display_text, 
            text_style,
            font,
            position_preset,
            margin_percent
        )
    else:
        # 使用绝对位置（毫米）
        # 将毫米位置转换为像素位置
        x_pos = canvas.mm_to_px(position_mm[0])
        y_pos = canvas.mm_to_px(position_mm[1])
        
        # 计算文本行高度（像素）
        line_height = int(font_size_px * text_style.line_spacing)
        
        # 生成位置列表
        positions = []
        for i in range(len(display_text)):
            current_y = y_pos + i * line_height
            positions.append((x_pos, current_y))
    
    # 绘制每一行文本
    for i, text in enumerate(display_text):
        pos = positions[i]
        
        # 添加阴影效果
        shadow_positions = [
            (pos[0]+1, pos[1]+1), (pos[0]+1, pos[1]-1), 
            (pos[0]-1, pos[1]+1), (pos[0]-1, pos[1]-1)
        ]
        for shadow_pos in shadow_positions:
            draw.text(shadow_pos, text, fill=text_style.background_color, font=font)
        
        # 绘制主文本
        draw.text(pos, text, fill=text_style.text_color, font=font)
    
    return canvas_image

# 导出函数（更新为使用画布的原始DPI）
def export_image(image, output_path, canvas, format="JPEG", quality=90):
    """
    导出修改后的图像，保持原始分辨率信息
    
    参数:
        image: PIL Image对象
        output_path: 输出文件路径
        canvas: VirtualCanvas对象（用于获取DPI信息）
        format: 图像格式 ('JPEG', 'PNG'等)
        quality: JPEG质量(1-100)
    """
    if not output_path.lower().endswith(f".{format.lower()}"):
        output_path = f"{os.path.splitext(output_path)[0]}.{format.lower()}"
    
    save_args = {"format": format, "quality": quality}
    
    # 添加DPI信息
    if format == "JPEG":
        save_args["dpi"] = (canvas.original_dpi, canvas.original_dpi)
    
    image.save(output_path, **save_args)
    print(f"图片已导出至: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

# 主流程示例
if __name__ == '__main__':
    # 1. 读取原始图像
    image_path = r"P1128225.jpg"
    img = Image.open(image_path)
    
    # 2. 创建虚拟画布
    canvas = VirtualCanvas(
        original_image=img,
        layout_mode="fit",      # 适应模式
        bg_color=(240, 240, 240),  # 浅灰色背景
        canvas_aspect_ratio=16/9,  # 16:9的长宽比
        margin_relative=0.05,  # 边距为画布高度的5%
        corner_radius_relative=0.02,    # 圆角半径为画布最小边长的2%
        shadow_enabled=True,   # 启用阴影效果
        shadow_offset_relative=(0.005, 0.005),  # 阴影偏移为画布尺寸的0.5%
        shadow_blur_relative=0.01, # 阴影模糊半径为画布最小边长的1%
        shadow_color=(0, 0, 0, 64)  # 半透明黑色阴影        
    )
    
    # 3. 创建画布并添加照片
    canvas_image = canvas.create_canvas()
    canvas_image = canvas.add_photo_to_canvas(canvas_image)
    
    # 4. 获取元数据
    metadata = get_categorized_metadata(image_path)
    
    # 5. 选择要显示的元数据字段
    fields_to_draw = ["DateTimeOriginal"]
    
    # 6. 创建文本样式
    custom_style = TextStylePreset(
        font_size_relative=0.05,  # 字体高度为画布高度的5%
        text_color=(255, 255, 255),  # 白色文本
        font_name="NotoSerifSC-VF.ttf",  # 思源黑体
        background_color=(220, 220, 220, 128),  # 半透明白色阴影
        alignment="left",
        show_field_names=False
    )
    
    # 7. 添加文本到画布 - 使用预设位置
    result_image = add_text_to_canvas(
        canvas_image,
        canvas,
        metadata,
        fields_to_draw,
        text_style=custom_style,
        position_preset="center middle",  # 使用预设位置
        margin_percent=0.05  # 5%边距
    )
    
    # 8. 导出图像（保持原始DPI）
    output_filename = f"{os.path.splitext(image_path)[0]}_uniform_watermark.jpg"
    export_image(result_image, output_filename, canvas, format="JPEG", quality=100)
    
    print("处理完成！已保持原始照片分辨率。")