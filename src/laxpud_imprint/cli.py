from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .pipeline import process_batch


def build_parser():
    parser = argparse.ArgumentParser(
        prog="laxpud-imprint",
        description="Batch photo imprint and watermark tool.",
    )
    subparsers = parser.add_subparsers(dest="command")

    batch = subparsers.add_parser("batch", help="Process a directory of images.")
    batch.add_argument("-i", "--input", dest="input_dir", help="Input image directory.")
    batch.add_argument("-o", "--output", dest="output_dir", help="Output directory.")
    batch.add_argument("-c", "--config", dest="config_path", help="TOML config path.")

    return parser


def run_batch(args):
    config = load_config(args.config_path)
    project_root = Path.cwd()
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
        if result.ok:
            print(f"OK  {result.source} -> {result.output}")
        else:
            failed += 1
            print(f"ERR {result.source}: {result.error}")

    print(f"Done. {len(results) - failed} succeeded, {failed} failed.")
    return 1 if failed else 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "batch":
        return run_batch(args)

    parser.print_help()
    return 0
