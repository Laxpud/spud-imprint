from PIL import Image
from PIL.ExifTags import TAGS


CATEGORY_MAP = {
    "Make": "device_info",
    "Model": "device_info",
    "BodySerialNumber": "device_info",
    "LensModel": "device_info",
    "LensSerialNumber": "device_info",
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
    "DateTimeOriginal": "time_info",
    "DateTimeDigitized": "time_info",
    "SubsecTimeOriginal": "time_info",
    "OffsetTimeOriginal": "time_info",
    "OffsetTimeDigitized": "time_info",
    "OffsetTime": "time_info",
    "Software": "post_processing",
    "DateTime": "post_processing",
    "Artist": "copyright_info",
    "Copyright": "copyright_info",
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
    "FocalPlaneXResolution": "sensor_data",
    "FocalPlaneYResolution": "sensor_data",
    "FocalPlaneResolutionUnit": "sensor_data",
    "SensingMethod": "sensor_data",
}


def empty_metadata():
    return {
        "device_info": {},
        "capture_settings": {},
        "time_info": {},
        "post_processing": {},
        "copyright_info": {},
        "technical_params": {},
        "sensor_data": {},
        "other": {},
    }


def format_special_field(field, value):
    if field == "ExposureTime":
        if value < 1:
            return f"1/{int(1 / value)}s"
        return f"{value}s"
    if field in ["FocalLength", "FocalLengthIn35mmFilm"]:
        return f"{value}mm"
    if field == "FNumber":
        return f"f/{value}"
    if field == "DateTimeOriginal":
        try:
            date_part = value.split(" ")[0]
            return date_part.replace(":", "-")
        except AttributeError:
            return value
    return value


def get_categorized_metadata(image_path):
    categorized = empty_metadata()

    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif() or {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                category = CATEGORY_MAP.get(tag_name, "other")
                categorized[category][tag_name] = value
    except (OSError, AttributeError, KeyError):
        return categorized

    return categorized


def prepare_metadata_text(metadata, fields_to_draw, text_style):
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
