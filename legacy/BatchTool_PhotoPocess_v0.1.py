from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import os

class TextStylePreset:
    """
    文本样式配置类，封装所有文本格式设置
    """
    def __init__(self, font_size=20, text_color=(255, 255, 255), 
                 font_name="arial.ttf", background_color=(0, 0, 0),
                 alignment="left", line_spacing=1.5, show_field_names=True):
        """
        初始化文本样式配置
        
        参数:
            font_size: 字体大小（默认20）
            text_color: 文字颜色 (RGB元组，默认白色)
            font_name: 字体文件路径或名称（默认"arial.ttf"）
            background_color: 文字阴影/背景颜色 (RGB元组，默认黑色)
            alignment: 文本对齐方式 ("left", "center", "right")
            line_spacing: 行间距倍数（默认1.5倍行高）
            show_field_names: 是否显示元数据字段名称 (True/False)
        """
        self.font_size = font_size
        self.text_color = text_color
        self.font_name = font_name
        self.background_color = background_color
        self.alignment = alignment
        self.line_spacing = line_spacing
        self.show_field_names = show_field_names

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

def get_text_dimensions(draw, text, font):
    """
    获取文本的宽度和高度（兼容不同版本的Pillow）
    
    参数:
        draw: ImageDraw 对象
        text: 文本内容
        font: 字体对象
        
    返回:
        tuple: (宽度, 高度)
    """
    # Pillow 9.5.0及以后使用getbbox()
    if hasattr(font, 'getbbox'):
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    
    # 旧版本Pillow使用getsize()
    elif hasattr(font, 'getsize'):
        return font.getsize(text)
    
    # 如果都没有，尝试使用图像测量
    else:
        try:
            # 尝试使用textlength方法（Pillow 8.0.0以后）
            width = int(draw.textlength(text, font=font))
            height = font.size
            return width, height
        except AttributeError:
            # 最后的方法：估计文本大小
            return len(text) * font.size, font.size

def calculate_text_positions(image_size, text_lines, preset, 
                           margin_percent, text_style, font):
    """
    计算文本块的位置（多行文本作为一个整体定位）
    
    参数:
        image_size: 图片尺寸 (width, height)
        text_lines: 文本行列表
        preset: 位置预设字符串
        margin_percent: 边距百分比
        text_style: 文本样式配置
        font: 字体对象（用于计算文本尺寸）
        
    返回:
        list: 每行文本的坐标位置 [(x, y), ...]
    """
    width, height = image_size
    parts = preset.lower().split()
    horizontal = parts[0] if len(parts) > 0 else "center"
    vertical = parts[1] if len(parts) > 1 else "middle"
    
    # 计算整体边距
    margin_x = int(width * margin_percent)
    margin_y = int(height * margin_percent)
    
    # 计算文本块高度（基于行高）
    line_height = int(text_style.font_size * text_style.line_spacing)
    text_block_height = len(text_lines) * line_height
    
    # 计算垂直位置
    if vertical == "top":
        start_y = margin_y
    elif vertical == "bottom":
        start_y = height - margin_y - text_block_height
    else:  # middle
        start_y = (height - text_block_height) // 2
    
    # 创建绘图对象用于测量文本尺寸
    with Image.new("RGB", (10, 10)) as tmp_img:
        draw = ImageDraw.Draw(tmp_img)        
        # 计算每行的宽度
        line_widths = [get_text_dimensions(draw, line, font)[0] for line in text_lines]
    
    # 确定最宽行的宽度
    max_width = max(line_widths) if line_widths else 0
    
    # 生成位置列表
    positions = []
    for i, line in enumerate(text_lines):
        # 根据预设的水平位置确定基准x坐标
        if horizontal == "left":
            base_x = margin_x
        elif horizontal == "right":
            base_x = width - margin_x - max_width
        else:  # center
            base_x = (width - max_width) // 2
        
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

def add_metadata_to_image(image, metadata, fields_to_draw, 
                         position_preset="center middle",
                         margin_percent=0.05,
                         text_style=None):
    """
    在图片上添加元数据文本
    
    参数:
        image: PIL Image对象
        metadata: 分类元数据字典
        fields_to_draw: 要显示的字段列表
        position_preset: 位置预设 (水平位置”left“/”center“/”right“ 垂直位置”top“/”middle“/”bottom“)
        margin_percent: 边距百分比 (0-1)
        text_style: 文本样式配置对象（如为None则使用默认配置）
        
    返回:
        Image: 添加了文本的Image对象
    """
    # 如果没有提供文本样式，使用默认配置
    if text_style is None:
        text_style = TextStylePreset()
    
    # 准备要显示的文本内容
    display_text = prepare_metadata_text(metadata, fields_to_draw, text_style)
    
    # 创建绘图对象
    draw = ImageDraw.Draw(image)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype(text_style.font_name, text_style.font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # 计算文本位置（现在需要传递font对象用于测量）
    positions = calculate_text_positions(
        image.size, 
        display_text, 
        position_preset,
        margin_percent,
        text_style,
        font
    )
    
    # 绘制文本（带阴影效果）
    for text, pos in zip(display_text, positions):
        # 添加阴影效果增强可读性
        shadow_positions = [(pos[0]+dx, pos[1]+dy) for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]]
        for shadow_pos in shadow_positions:
            draw.text(shadow_pos, text, fill=text_style.background_color, font=font)
        
        # 绘制主文本
        draw.text(pos, text, fill=text_style.text_color, font=font)
    
    return image
# 辅助函数：格式化特殊元数据字段
def format_special_field(field, value):
    """对特殊字段进行格式化处理"""
    if field == "ExposureTime":
        # 曝光时间格式化：如果小于1秒显示为分数
        if value < 1:
            return f"1/{int(1/value)}s"
        return f"{value}s"
    elif field in ["FocalLength", "FocalLengthIn35mmFilm"]:
        # 焦距格式化：添加单位
        return f"{value}mm"
    elif field == "FNumber":
        # 光圈值格式化：显示为标准的f/数值
        return f"f/{value}"
    elif field == "DateTimeOriginal":
        # 日期格式化：只保留年月日部分
        try:
            # 原始格式通常是 "YYYY:MM:DD HH:MM:SS"
            date_part = value.split(" ")[0]  # 获取日期部分
            # 将冒号替换为连字符
            return date_part.replace(":", "-")
        except:
            # 如果解析失败，返回原始值
            return value
    return value
# 导出修改后的照片
def export_image(image, output_path, format="JPEG", quality=90):
    """
    导出修改后的图像
    
    参数:
        image: PIL Image对象
        output_path: 输出文件路径
        format: 图像格式 ('JPEG', 'PNG'等)
        quality: JPEG质量(1-100)
        
    返回:
        str: 输出文件的完整路径
    """
    # 自动添加扩展名
    if not output_path.lower().endswith(f".{format.lower()}"):
        output_path = f"{os.path.splitext(output_path)[0]}.{format.lower()}"
    
    # 准备保存参数
    save_args = {"format": format}
    
    # 添加特定格式的选项
    if format == "JPEG":
        save_args["quality"] = quality
    
    # 保存图像
    image.save(output_path, **save_args)
    
    print(f"图片已导出至: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

# 主流程示例
if __name__ == '__main__':
    # 1. 读取图像和元数据
    image_path = r"P1074931.jpg"
    img = Image.open(image_path)
    metadata = get_categorized_metadata(image_path)
    
    # 2. 选择要在图片上显示的元数据
    fields_to_draw = [
        #"Model", 
        #"LensModel", 
        #"ExposureTime", 
        #"FNumber", 
        #"ISOSpeedRatings", 
        "DateTimeOriginal"
    ]
    
    # 3. 创建自定义文本样式
    custom_style = TextStylePreset(
        font_size=100,
        font_name="NotoSerifSC-VF.ttf",  # 自定义字体文件
        text_color=(255, 255, 255),  # 白色文本
        background_color=(50, 50, 50),  # 深灰色阴影
        alignment="left",  # 左对齐
        line_spacing=1.8,   # 行距1.8倍
        show_field_names=False  # 不显示字段名称
    )
    
    # 4. 添加元数据到图片
    img_with_metadata = add_metadata_to_image(
        img, 
        metadata, 
        fields_to_draw, 
        position_preset="center bottom",  # 左下角位置
        margin_percent=0.05,
        text_style=custom_style
    )
    
    # 5. 导出图像
    output_filename = f"{os.path.splitext(image_path)[0]}_watermarked.jpg"
    export_image(
        img_with_metadata, 
        output_filename,
        quality=100
    )
    
    print("导出完成")