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
    input_dir: str = "input"
    output_dir: str = "output"
    filename_suffix: str = "_uniform_watermark"
    format: str = "JPEG"
    quality: int = 100


@dataclass
class CanvasConfig:
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
    batch: BatchConfig = field(default_factory=BatchConfig)
    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    photo: PhotoConfig = field(default_factory=PhotoConfig)
    text: TextConfig = field(default_factory=TextConfig)


def _tuple(value: Any):
    if value is None or isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return value


def _merge_dataclass(instance, values: dict[str, Any]):
    for key, value in values.items():
        if not hasattr(instance, key):
            continue
        if key.endswith("color"):
            value = _tuple(value)
        elif isinstance(value, list) and key not in {"fields"}:
            value = tuple(value)
        setattr(instance, key, value)
    return instance


def load_config(path: str | Path | None = None) -> ImprintConfig:
    config = ImprintConfig()

    if path is None:
        return config

    path = Path(path)
    with path.open("rb") as file:
        raw = tomllib.load(file)

    _merge_dataclass(config.batch, raw.get("batch", {}))
    _merge_dataclass(config.canvas, raw.get("canvas", {}))
    _merge_dataclass(config.photo, raw.get("photo", {}))
    _merge_dataclass(config.text, raw.get("text", {}))
    return config
