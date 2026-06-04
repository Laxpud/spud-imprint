from pathlib import Path


FORMAT_EXTENSIONS = {
    "JPEG": ".jpeg",
    "JPG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def export_image(image, output_path, canvas, format="JPEG", quality=90):
    """按指定格式保存图片，并为 JPEG 写入原图 DPI。"""
    output_path = Path(output_path)
    format = format.upper()
    expected_suffix = FORMAT_EXTENSIONS.get(format, f".{format.lower()}")

    # 输出后缀跟格式保持一致，避免用户传 output/foo 但实际保存成难识别的文件。
    if output_path.suffix.lower() != expected_suffix:
        output_path = output_path.with_suffix(expected_suffix)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_args = {"format": format, "quality": quality}

    if format in {"JPEG", "JPG"}:
        # JPEG 不支持 alpha 通道；如果前面产生了 RGBA，需要先转回普通 RGB。
        save_args["dpi"] = (canvas.original_dpi, canvas.original_dpi)
        if image.mode == "RGBA":
            image = image.convert("RGB")

    image.save(output_path, **save_args)
    return output_path.resolve()
