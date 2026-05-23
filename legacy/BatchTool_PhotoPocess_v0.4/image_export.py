import os

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