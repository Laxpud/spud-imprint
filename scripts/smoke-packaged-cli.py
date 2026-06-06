from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


def run_command(exe_path: Path, args: list[str], cwd: Path) -> str:
    """运行打包后的 CLI，并在失败时展示完整输出便于定位。"""
    completed = subprocess.run(
        [str(exe_path), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        command_text = " ".join([str(exe_path), *args])
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}: {command_text}\n"
            f"{output}"
        )
    return output


def assert_contains(output: str, expected: str):
    """确认命令输出包含预期片段，避免只检查退出码。"""
    if expected not in output:
        raise AssertionError(f"Expected output to contain {expected!r}, got:\n{output}")


def verify_image(path: Path):
    """确认输出图片存在，并且 Pillow 能正常读取。"""
    if not path.is_file():
        raise AssertionError(f"Expected image to exist: {path}")
    with Image.open(path) as image:
        image.verify()


def main() -> int:
    """在源码目录外验证 PyInstaller one-dir 产物能独立运行。"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dist-dir",
        required=True,
        help="Directory containing spud-imprint.exe.",
    )
    args = parser.parse_args()

    dist_dir = Path(args.dist_dir).resolve()
    exe_path = dist_dir / "spud-imprint.exe"
    if not exe_path.is_file():
        raise FileNotFoundError(f"Packaged executable does not exist: {exe_path}")

    with tempfile.TemporaryDirectory(prefix="spud-imprint-smoke-") as tmp:
        work_dir = Path(tmp)
        input_dir = work_dir / "input"
        output_dir = work_dir / "output"
        input_dir.mkdir()

        source = input_dir / "sample.jpg"
        preview_output = work_dir / "preview.jpeg"
        Image.new("RGB", (96, 72), (120, 130, 140)).save(source)

        assert_contains(run_command(exe_path, ["--version"], work_dir), "spud-imprint")
        assert_contains(
            run_command(exe_path, ["validate-config", "--template", "minimal"], work_dir),
            "Config OK",
        )
        assert_contains(
            run_command(
                exe_path,
                [
                    "preview",
                    "--input",
                    str(source),
                    "--output",
                    str(preview_output),
                    "--template",
                    "minimal",
                ],
                work_dir,
            ),
            "OK",
        )
        verify_image(preview_output)

        dry_run_output = run_command(
            exe_path,
            [
                "batch",
                "--input",
                str(input_dir),
                "--output",
                str(output_dir),
                "--template",
                "classic",
                "--dry-run",
            ],
            work_dir,
        )
        assert_contains(dry_run_output, "DRY")
        assert_contains(dry_run_output, "Done. 1 planned, 0 written.")

    print(f"Packaged CLI smoke test passed: {exe_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
