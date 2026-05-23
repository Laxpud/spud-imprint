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