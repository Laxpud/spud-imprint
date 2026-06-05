from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .config import load_config
from .export import FORMAT_EXTENSIONS
from .pipeline import iter_image_files, process_batch, process_preview
from .validation import ConfigValidationError, validate_config


def build_parser():
    """创建命令行参数解析器，集中声明所有 CLI 子命令。"""
    parser = argparse.ArgumentParser(
        prog="spud-imprint",
        description="Batch photo imprint and watermark tool.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    batch = subparsers.add_parser("batch", help="Process a directory of images.")
    batch.add_argument("-i", "--input", dest="input_dir", help="Input image directory.")
    batch.add_argument("-o", "--output", dest="output_dir", help="Output directory.")
    batch.add_argument("-c", "--config", dest="config_path", help="TOML config path.")
    batch.add_argument(
        "-t",
        "--template",
        dest="template",
        help="Template name or path.",
    )
    batch.add_argument(
        "--dry-run",
        action="store_true",
        help="List images and planned outputs without writing files.",
    )
    batch.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra processing details.",
    )

    validate = subparsers.add_parser(
        "validate-config",
        help="Validate a TOML config without processing images.",
    )
    validate.add_argument("-c", "--config", dest="config_path", help="TOML config path.")
    validate.add_argument(
        "-t",
        "--template",
        dest="template",
        help="Template name or path.",
    )
    validate.add_argument(
        "-i",
        "--input",
        dest="input_dir",
        help="Optional input directory override to validate.",
    )
    validate.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra validation details.",
    )

    preview = subparsers.add_parser("preview", help="Render one preview image.")
    preview.add_argument(
        "-i",
        "--input",
        dest="input_path",
        required=True,
        help="Input image path.",
    )
    preview.add_argument(
        "-o",
        "--output",
        dest="output_path",
        required=True,
        help="Output preview image path.",
    )
    preview.add_argument("-c", "--config", dest="config_path", help="TOML config path.")
    preview.add_argument(
        "-t",
        "--template",
        dest="template",
        help="Template name or path.",
    )
    preview.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra processing details.",
    )

    return parser


def _load_config(path, template=None):
    """读取配置并把解析错误转换成稳定的 CLI 退出码。"""
    try:
        return load_config(path, template=template, project_root=Path.cwd())
    except (OSError, ValueError) as exc:
        print(f"Config load error: {exc}")
        return None


def _resolve_cli_path(path_value, project_root):
    """按当前 CLI 语义解析路径，用于 dry-run 展示和扫描。"""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return project_root / path


def _planned_output_path(image_path, output_dir, config):
    """根据导出格式推算 dry-run 会写出的目标文件名。"""
    output_name = f"{image_path.stem}{config.batch.filename_suffix}"
    suffix = FORMAT_EXTENSIONS.get(
        str(config.batch.format).upper(),
        f".{str(config.batch.format).lower()}",
    )
    return (output_dir / output_name).with_suffix(suffix)


def run_validate_config(args):
    """执行 validate-config 子命令，只校验配置和可选输入目录。"""
    config = _load_config(args.config_path, template=args.template)
    if config is None:
        return 2

    project_root = Path.cwd()
    try:
        validate_config(
            config,
            project_root=project_root,
            input_dir=args.input_dir,
            check_input_dir=args.input_dir is not None,
        )
    except ConfigValidationError as exc:
        print(exc)
        return 2

    if args.verbose:
        print(f"Config: {args.config_path or '<defaults>'}")
        print(f"Template: {args.template or '<none>'}")
        if args.input_dir is not None:
            print(f"Input: {_resolve_cli_path(args.input_dir, project_root)}")
    print("Config OK")
    return 0


def run_dry_batch(args, config, project_root):
    """执行 batch 的 dry-run 路径，只扫描输入并展示计划输出。"""
    input_path = _resolve_cli_path(
        args.input_dir or config.batch.input_dir,
        project_root,
    )
    output_path = _resolve_cli_path(
        args.output_dir or config.batch.output_dir,
        project_root,
    )

    images = list(iter_image_files(input_path))
    if args.verbose:
        print(f"Config: {args.config_path or '<defaults>'}")
        print(f"Template: {args.template or '<none>'}")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")

    if not images:
        print("No supported images found.")
        return 0

    for image_path in images:
        planned_output = _planned_output_path(image_path, output_path, config)
        print(f"DRY {image_path} -> {planned_output}")

    print(f"Done. {len(images)} planned, 0 written.")
    return 0


def run_batch(args):
    """执行 batch 子命令，并把每张图片的处理结果打印到终端。"""
    config = _load_config(args.config_path, template=args.template)
    if config is None:
        return 2

    project_root = Path.cwd()
    try:
        validate_config(config, project_root=project_root, input_dir=args.input_dir)
    except ConfigValidationError as exc:
        print(exc)
        return 2

    if args.dry_run:
        return run_dry_batch(args, config, project_root)

    if args.verbose:
        print(f"Config: {args.config_path or '<defaults>'}")
        print(f"Template: {args.template or '<none>'}")
        input_path = _resolve_cli_path(
            args.input_dir or config.batch.input_dir,
            project_root,
        )
        output_path = _resolve_cli_path(
            args.output_dir or config.batch.output_dir,
            project_root,
        )
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")

    results = process_batch(
        config,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        project_root=project_root,
    )

    if not results:
        print("No supported images found.")
        return 0

    failed = 0
    for result in results:
        # CLI 输出保持简短稳定，方便用户复制日志或未来被脚本读取。
        if result.ok:
            print(f"OK  {result.source} -> {result.output}")
        else:
            failed += 1
            print(f"ERR {result.source}: {result.error}")

    print(f"Done. {len(results) - failed} succeeded, {failed} failed.")
    return 1 if failed else 0


def run_preview(args):
    """执行 preview 子命令，只渲染并导出一张图片。"""
    config = _load_config(args.config_path, template=args.template)
    if config is None:
        return 2

    project_root = Path.cwd()
    try:
        validate_config(config, project_root=project_root, check_input_dir=False)
    except ConfigValidationError as exc:
        print(exc)
        return 2

    input_path = _resolve_cli_path(args.input_path, project_root)
    output_path = _resolve_cli_path(args.output_path, project_root)

    if args.verbose:
        print(f"Config: {args.config_path or '<defaults>'}")
        print(f"Template: {args.template or '<none>'}")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")

    try:
        exported = process_preview(
            input_path,
            output_path,
            config,
            project_root=project_root,
        )
    except Exception as exc:
        print(f"ERR {input_path}: {exc}")
        return 1

    print(f"OK  {input_path} -> {exported}")
    return 0


def main(argv=None):
    """命令行入口：解析参数并分发到具体子命令。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "batch":
        return run_batch(args)
    if args.command == "preview":
        return run_preview(args)
    if args.command == "validate-config":
        return run_validate_config(args)

    parser.print_help()
    return 0
