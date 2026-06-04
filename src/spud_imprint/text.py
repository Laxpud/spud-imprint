from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from .metadata import prepare_metadata_text


@dataclass
class TextStylePreset:
    """文字样式配置：包含字号、颜色、字体和排版方式。"""

    font_size_mm: float = 5
    font_size_relative: float | None = None
    text_color: tuple[int, ...] = (50, 50, 50)
    font_name: str = "arial.ttf"
    background_color: tuple[int, ...] = (220, 220, 220, 128)
    alignment: str = "left"
    line_spacing: float = 1.5
    show_field_names: bool = True

    def get_font_size_px(self, canvas):
        """把相对字号或毫米字号转换成实际绘制用的像素字号。"""
        if self.font_size_relative is not None:
            return int(min(canvas.height_px, canvas.width_px) * self.font_size_relative)
        return canvas.mm_to_px(self.font_size_mm)


def calculate_text_positions(
    canvas,
    text_lines,
    text_style,
    font,
    position_preset="center middle",
    margin_percent=0.05,
):
    """根据预设位置计算每一行文字左上角坐标。"""
    canvas_width_px = canvas.width_px
    canvas_height_px = canvas.height_px

    # 预设位置由“水平 垂直”两部分组成，例如 center bottom。
    parts = position_preset.lower().split()
    horizontal = parts[0] if len(parts) > 0 else "center"
    vertical = parts[1] if len(parts) > 1 else "middle"

    margin_x = int(canvas_width_px * margin_percent)
    margin_y = int(canvas_height_px * margin_percent)

    line_height = int(text_style.get_font_size_px(canvas) * text_style.line_spacing)
    text_block_height = len(text_lines) * line_height

    with Image.new("RGB", (10, 10)) as tmp_img:
        draw = ImageDraw.Draw(tmp_img)
        line_widths = []
        for line in text_lines:
            # 不同 Pillow 版本支持的测量 API 不完全一样，这里按可用性逐级回退。
            if hasattr(font, "getbbox"):
                bbox = font.getbbox(line)
                width = bbox[2] - bbox[0]
            elif hasattr(font, "getsize"):
                width = font.getsize(line)[0]
            else:
                try:
                    width = int(draw.textlength(line, font=font))
                except AttributeError:
                    width = len(line) * getattr(font, "size", 10)
            line_widths.append(width)

    max_width = max(line_widths) if line_widths else 0

    if vertical == "top":
        start_y = margin_y
    elif vertical == "bottom":
        start_y = canvas_height_px - margin_y - text_block_height
    else:
        start_y = (canvas_height_px - text_block_height) // 2

    positions = []
    for i, _line in enumerate(text_lines):
        # 先确定整块文字的起始 x，再按每行对齐方式微调。
        if horizontal == "left":
            base_x = margin_x
        elif horizontal == "right":
            base_x = canvas_width_px - margin_x - max_width
        else:
            base_x = (canvas_width_px - max_width) // 2

        if text_style.alignment == "right":
            x = base_x - line_widths[i]
        elif text_style.alignment == "center":
            x = base_x - (line_widths[i] // 2)
        else:
            x = base_x

        y = start_y + i * line_height
        positions.append((x, y))

    return positions


def add_text_to_canvas(
    canvas_image,
    canvas,
    metadata,
    fields_to_draw,
    text_style=None,
    position_mm=(20, 20),
    position_preset=None,
    margin_percent=0.05,
):
    """把选中的元数据字段绘制到画布上。"""
    if text_style is None:
        text_style = TextStylePreset()

    display_text = prepare_metadata_text(metadata, fields_to_draw, text_style)
    draw = ImageDraw.Draw(canvas_image)
    font_size_px = text_style.get_font_size_px(canvas)

    try:
        font = ImageFont.truetype(text_style.font_name, font_size_px)
    except OSError:
        font = ImageFont.load_default()

    if position_preset:
        # 使用预设位置时，坐标由画布大小和文字块大小共同决定。
        positions = calculate_text_positions(
            canvas,
            display_text,
            text_style,
            font,
            position_preset,
            margin_percent,
        )
    else:
        # 没有预设时，保留旧接口：直接用毫米坐标指定第一行位置。
        x_pos = canvas.mm_to_px(position_mm[0])
        y_pos = canvas.mm_to_px(position_mm[1])
        line_height = int(font_size_px * text_style.line_spacing)
        positions = [(x_pos, y_pos + i * line_height) for i in range(len(display_text))]

    for i, text in enumerate(display_text):
        pos = positions[i]
        # 四个方向各画一次浅色文字，形成简单描边，提升照片上的可读性。
        shadow_positions = [
            (pos[0] + 1, pos[1] + 1),
            (pos[0] + 1, pos[1] - 1),
            (pos[0] - 1, pos[1] + 1),
            (pos[0] - 1, pos[1] - 1),
        ]
        for shadow_pos in shadow_positions:
            draw.text(shadow_pos, text, fill=text_style.background_color, font=font)

        draw.text(pos, text, fill=text_style.text_color, font=font)

    return canvas_image
