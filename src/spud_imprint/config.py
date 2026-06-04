from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - used on Python 3.10
    import tomli as tomllib


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}


@dataclass
class BatchConfig:
    """批处理配置：说明图片从哪里读、输出到哪里、用什么格式保存。"""

    input_dir: str = "input"
    output_dir: str = "output"
    filename_suffix: str = "_uniform_watermark"
    format: str = "JPEG"
    quality: int = 100


@dataclass
class CanvasConfig:
    """画布配置：控制成品比例、背景、外边距和模糊背景。"""

    frame_mode: str | None = None
    layout_mode: str = "fit"
    aspect_ratio: float | None = 16 / 9
    background_color: tuple[int, int, int] = (240, 240, 240)
    margin_mm: float | None = None
    margin_relative: float | None = 0.05
    blurred_background: bool = True
    blur_radius: int = 100
    blur_extra_scale: float = 1.5
    blur_fit_mode: str = "cover"


@dataclass
class PhotoConfig:
    """照片配置：控制照片相框边距、圆角和阴影效果。"""

    margin_unit: str | None = None
    margin_policy: str = "minimum_edge"
    margin_mm: float | None = None
    margin_relative: float | None = None
    corner_radius_mm: float | None = None
    corner_radius_relative: float | None = 0.02
    shadow_enabled: bool = True
    shadow_offset_mm: tuple[float, float] | None = (2, 2)
    shadow_offset_relative: tuple[float, float] | None = (0.005, 0.005)
    shadow_blur_radius: int = 10
    shadow_blur_relative: float | None = 0.01
    shadow_color: tuple[int, int, int, int] = (0, 0, 0, 64)


@dataclass
class TextConfig:
    """文字配置：控制要绘制的元数据字段、字体、颜色和位置。"""

    fields: list[str] = field(default_factory=lambda: ["DateTimeOriginal"])
    font_size_mm: float = 5
    font_size_relative: float | None = 0.05
    font_name: str = "assets/fonts/NotoSerifSC-VF.ttf"
    color: tuple[int, int, int] = (255, 255, 255)
    shadow_color: tuple[int, int, int, int] = (220, 220, 220, 128)
    alignment: str = "left"
    line_spacing: float = 1.5
    show_field_names: bool = False
    position_preset: str | None = "center bottom"
    margin_percent: float = 0.05


@dataclass
class ImprintConfig:
    """完整配置对象：把批处理、画布、照片和文字四组配置放在一起。"""

    batch: BatchConfig = field(default_factory=BatchConfig)
    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    photo: PhotoConfig = field(default_factory=PhotoConfig)
    text: TextConfig = field(default_factory=TextConfig)


def _tuple(value: Any):
    """把 TOML 读出来的列表转换成 tuple，方便后续当作颜色或坐标使用。"""
    if value is None or isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return value


def _parse_aspect_ratio(value: Any):
    """把 16:9、16/9、1.777 这几种比例写法统一转换成浮点数。"""
    if value is None:
        return None
    if isinstance(value, int | float):
        ratio = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if text.lower() in {"", "none", "auto"}:
            return None
        separator = ":" if ":" in text else "/"
        if separator in text:
            # 字符串比例只切一次，允许右侧继续保留用户输入用于报错提示。
            left, right = text.split(separator, 1)
            try:
                ratio = float(left.strip()) / float(right.strip())
            except ValueError as exc:
                raise ValueError(f"Invalid aspect_ratio: {value}") from exc
        else:
            try:
                ratio = float(text)
            except ValueError as exc:
                raise ValueError(f"Invalid aspect_ratio: {value}") from exc
    else:
        raise TypeError(f"aspect_ratio must be a number or ratio string: {value!r}")

    if ratio <= 0:
        raise ValueError(f"aspect_ratio must be greater than 0: {value}")
    return ratio


def _merge_dataclass(instance, values: dict[str, Any]):
    """把配置文件里的字段覆盖到默认配置对象上，未知字段会被忽略。"""
    for key, value in values.items():
        if not hasattr(instance, key):
            continue
        # TOML 没有 tuple 类型，所以颜色、坐标和列表需要在这里整理成程序习惯的形状。
        if key == "aspect_ratio":
            value = _parse_aspect_ratio(value)
        elif key.endswith("color"):
            value = _tuple(value)
        elif isinstance(value, list) and key not in {"fields"}:
            value = tuple(value)
        setattr(instance, key, value)
    return instance


def load_config(path: str | Path | None = None) -> ImprintConfig:
    """读取 TOML 配置；没有传路径时返回内置默认配置。"""
    config = ImprintConfig()

    if path is None:
        return config

    path = Path(path)
    with path.open("rb") as file:
        raw = tomllib.load(file)

    # 每个 TOML 表对应一个 dataclass，小表缺失时就继续使用默认值。
    _merge_dataclass(config.batch, raw.get("batch", {}))
    _merge_dataclass(config.canvas, raw.get("canvas", {}))
    _merge_dataclass(config.photo, raw.get("photo", {}))
    _merge_dataclass(config.text, raw.get("text", {}))
    return config
