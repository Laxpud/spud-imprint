from PIL import Image
from PIL.ExifTags import TAGS

# 辅助函数：格式化特殊元数据字段
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

# 获取分类元数据函数
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

# 准备元数据文本函数
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