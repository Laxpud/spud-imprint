from pathlib import Path


FORMAT_EXTENSIONS = {
    "JPEG": ".jpeg",
    "JPG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def export_image(image, output_path, canvas, format="JPEG", quality=90):
    output_path = Path(output_path)
    format = format.upper()
    expected_suffix = FORMAT_EXTENSIONS.get(format, f".{format.lower()}")

    if output_path.suffix.lower() != expected_suffix:
        output_path = output_path.with_suffix(expected_suffix)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_args = {"format": format, "quality": quality}

    if format in {"JPEG", "JPG"}:
        save_args["dpi"] = (canvas.original_dpi, canvas.original_dpi)
        if image.mode == "RGBA":
            image = image.convert("RGB")

    image.save(output_path, **save_args)
    return output_path.resolve()
