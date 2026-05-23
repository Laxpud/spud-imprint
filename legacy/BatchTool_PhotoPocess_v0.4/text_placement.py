from PIL import ImageDraw, ImageFont, Image

from text_style import TextStylePreset
from metadata_utils import prepare_metadata_text

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