from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .canvas import VirtualCanvas
from .config import IMAGE_EXTENSIONS, ImprintConfig
from .export import export_image
from .metadata import get_categorized_metadata
from .text import TextStylePreset, add_text_to_canvas


@dataclass
class ProcessResult:
    source: Path
    output: Path | None
    ok: bool
    error: str | None = None


def iter_image_files(input_dir: Path):
    for path in sorted(input_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def resolve_font_path(font_name: str, project_root: Path | None = None):
    font_path = Path(font_name)
    if font_path.is_absolute() and font_path.exists():
        return str(font_path)

    candidates = []
    if project_root is not None:
        candidates.append(project_root / font_path)
    candidates.append(Path.cwd() / font_path)
    candidates.append(font_path)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return font_name


def render_image(image_path: Path, config: ImprintConfig, project_root: Path | None = None):
    with Image.open(image_path) as img:
        img.load()
        canvas = VirtualCanvas(
            original_image=img,
            layout_mode=config.canvas.layout_mode,
            bg_color=config.canvas.background_color,
            canvas_aspect_ratio=config.canvas.aspect_ratio,
            margin_mm=config.canvas.margin_mm,
            margin_relative=config.canvas.margin_relative,
            corner_radius_mm=config.photo.corner_radius_mm,
            corner_radius_relative=config.photo.corner_radius_relative,
            shadow_enabled=config.photo.shadow_enabled,
            shadow_offset_mm=config.photo.shadow_offset_mm,
            shadow_offset_relative=config.photo.shadow_offset_relative,
            shadow_blur_radius=config.photo.shadow_blur_radius,
            shadow_blur_relative=config.photo.shadow_blur_relative,
            shadow_color=config.photo.shadow_color,
        )

        canvas_image = canvas.create_canvas()
        if config.canvas.blurred_background:
            canvas_image = canvas.add_blurred_background(
                canvas_image,
                blur_radius=config.canvas.blur_radius,
                extra_scale=config.canvas.blur_extra_scale,
                fit_mode=config.canvas.blur_fit_mode,
            )
        canvas_image = canvas.add_photo_to_canvas(canvas_image)

        metadata = get_categorized_metadata(image_path)
        text_style = TextStylePreset(
            font_size_mm=config.text.font_size_mm,
            font_size_relative=config.text.font_size_relative,
            text_color=config.text.color,
            font_name=resolve_font_path(config.text.font_name, project_root),
            background_color=config.text.shadow_color,
            alignment=config.text.alignment,
            line_spacing=config.text.line_spacing,
            show_field_names=config.text.show_field_names,
        )

        return add_text_to_canvas(
            canvas_image,
            canvas,
            metadata,
            config.text.fields,
            text_style=text_style,
            position_preset=config.text.position_preset,
            margin_percent=config.text.margin_percent,
        ), canvas


def process_image(
    image_path: Path,
    output_dir: Path,
    config: ImprintConfig,
    project_root: Path | None = None,
):
    rendered, canvas = render_image(image_path, config, project_root=project_root)
    output_name = f"{image_path.stem}{config.batch.filename_suffix}"
    output_path = output_dir / output_name
    exported = export_image(
        rendered,
        output_path,
        canvas,
        format=config.batch.format,
        quality=config.batch.quality,
    )
    return exported


def process_batch(
    config: ImprintConfig,
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    project_root: Path | None = None,
):
    input_path = Path(input_dir or config.batch.input_dir)
    output_path = Path(output_dir or config.batch.output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    results = []

    for image_path in iter_image_files(input_path):
        try:
            exported = process_image(
                image_path,
                output_path,
                config,
                project_root=project_root,
            )
            results.append(ProcessResult(source=image_path, output=exported, ok=True))
        except Exception as exc:
            results.append(
                ProcessResult(source=image_path, output=None, ok=False, error=str(exc))
            )

    return results
