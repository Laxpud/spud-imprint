from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .config import ImprintConfig
from .export import FORMAT_EXTENSIONS


SUPPORTED_LAYOUT_MODES = {"original", "fit", "fill", "stretch"}
SUPPORTED_BLUR_FIT_MODES = {"cover", "contain"}
SUPPORTED_TEXT_ALIGNMENTS = {"left", "center", "right"}
SUPPORTED_POSITION_HORIZONTAL = {"left", "center", "right"}
SUPPORTED_POSITION_VERTICAL = {"top", "middle", "bottom"}


class ConfigValidationError(ValueError):
    """配置校验失败时抛出的异常，保留所有字段错误方便一次性展示。"""

    def __init__(self, errors: Iterable[str]):
        self.errors = list(errors)
        message = "Invalid configuration"
        if self.errors:
            message += ":\n" + "\n".join(f"- {error}" for error in self.errors)
        super().__init__(message)


def _is_number(value):
    """判断值是否是普通数字；bool 虽然继承 int，但不适合当配置数值。"""
    return isinstance(value, int | float) and not isinstance(value, bool)


def _validate_choice(errors, field_path, value, supported):
    """校验枚举字段，并在报错里给出支持值。"""
    normalized = str(value).lower() if value is not None else ""
    if normalized not in supported:
        choices = ", ".join(sorted(supported))
        errors.append(f"{field_path}: must be one of {choices}")


def _validate_color(errors, field_path, value, expected_length):
    """校验颜色数组的长度和通道范围。"""
    if not isinstance(value, tuple | list):
        errors.append(f"{field_path}: must be a color list with {expected_length} values")
        return

    if len(value) != expected_length:
        errors.append(f"{field_path}: must contain {expected_length} values")
        return

    for channel in value:
        if not isinstance(channel, int) or isinstance(channel, bool):
            errors.append(f"{field_path}: color values must be integers from 0 to 255")
            return
        if channel < 0 or channel > 255:
            errors.append(f"{field_path}: color values must be between 0 and 255")
            return


def _resolve_existing_file(path_text, project_root):
    """按 CLI 的相对路径语义查找文件，找不到时返回 None。"""
    if not path_text:
        return None

    path = Path(path_text)
    if path.is_absolute():
        return path if path.is_file() else None

    candidates = []
    if project_root is not None:
        candidates.append(Path(project_root) / path)
    candidates.append(Path.cwd() / path)
    candidates.append(path)

    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate.absolute()
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.is_file():
            return candidate
    return None


def _validate_input_dir(errors, config, project_root, input_dir):
    """校验最终会用于批处理的输入目录。"""
    input_value = input_dir or config.batch.input_dir
    input_path = Path(input_value)
    if not input_path.is_absolute() and project_root is not None:
        input_path = Path(project_root) / input_path

    if not input_path.exists():
        errors.append(f"batch.input_dir: input directory does not exist: {input_path}")
    elif not input_path.is_dir():
        errors.append(f"batch.input_dir: input path is not a directory: {input_path}")


def _validate_position_preset(errors, value):
    """校验文本位置预设是否由合法的水平和垂直位置组成。"""
    if value is None:
        return

    parts = str(value).lower().split()
    if len(parts) != 2:
        errors.append(
            "text.position_preset: must contain horizontal and vertical positions"
        )
        return

    horizontal, vertical = parts
    if horizontal not in SUPPORTED_POSITION_HORIZONTAL:
        choices = ", ".join(sorted(SUPPORTED_POSITION_HORIZONTAL))
        errors.append(f"text.position_preset: horizontal position must be one of {choices}")
    if vertical not in SUPPORTED_POSITION_VERTICAL:
        choices = ", ".join(sorted(SUPPORTED_POSITION_VERTICAL))
        errors.append(f"text.position_preset: vertical position must be one of {choices}")


def validate_config(
    config: ImprintConfig,
    project_root: str | Path | None = None,
    input_dir: str | Path | None = None,
):
    """在处理图片前校验配置，并在发现问题时一次性抛出清晰错误。"""
    root = Path(project_root) if project_root is not None else None
    errors: list[str] = []

    if not isinstance(config.batch.quality, int) or isinstance(
        config.batch.quality, bool
    ):
        errors.append("batch.quality: must be an integer from 1 to 100")
    elif config.batch.quality < 1 or config.batch.quality > 100:
        errors.append("batch.quality: must be between 1 and 100")

    supported_formats = set(FORMAT_EXTENSIONS)
    batch_format = str(config.batch.format).upper()
    if batch_format not in supported_formats:
        choices = ", ".join(sorted(supported_formats))
        errors.append(f"batch.format: must be one of {choices}")

    _validate_choice(
        errors,
        "canvas.layout_mode",
        config.canvas.layout_mode,
        SUPPORTED_LAYOUT_MODES,
    )

    if config.canvas.margin_relative is not None:
        if not _is_number(config.canvas.margin_relative):
            errors.append("canvas.margin_relative: must be a number >= 0 and < 0.5")
        elif config.canvas.margin_relative < 0 or config.canvas.margin_relative >= 0.5:
            errors.append("canvas.margin_relative: must be >= 0 and < 0.5")

    _validate_choice(
        errors,
        "canvas.blur_fit_mode",
        config.canvas.blur_fit_mode,
        SUPPORTED_BLUR_FIT_MODES,
    )
    _validate_color(errors, "canvas.background_color", config.canvas.background_color, 3)
    _validate_color(errors, "photo.shadow_color", config.photo.shadow_color, 4)
    _validate_color(errors, "text.color", config.text.color, 3)
    _validate_color(errors, "text.shadow_color", config.text.shadow_color, 4)

    _validate_choice(
        errors,
        "text.alignment",
        config.text.alignment,
        SUPPORTED_TEXT_ALIGNMENTS,
    )
    _validate_position_preset(errors, config.text.position_preset)

    if _resolve_existing_file(config.text.font_name, root) is None:
        errors.append(f"text.font_name: font file does not exist: {config.text.font_name}")

    _validate_input_dir(errors, config, root, input_dir)

    if errors:
        raise ConfigValidationError(errors)

    return config
