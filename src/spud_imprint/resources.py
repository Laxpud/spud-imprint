from __future__ import annotations

import sys
from pathlib import Path


def source_project_root() -> Path:
    """返回源码仓库根目录，用于开发环境下查找内置资源。"""
    return Path(__file__).resolve().parents[2]


def runtime_resource_roots(project_root: str | Path | None = None) -> list[Path]:
    """按优先级返回可能存放内置资源的目录。"""
    roots: list[Path] = []

    if project_root is not None:
        roots.append(Path(project_root))

    # CLI 语义优先跟随当前工作目录，方便用户用相对路径组织项目文件。
    roots.append(Path.cwd())

    # 打包后资源通常放在 exe 同级目录，Tauri sidecar 也适合这种布局。
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)

    roots.append(source_project_root())

    # PyInstaller one-file 会把资源展开到 _MEIPASS；one-dir 也可能把数据放在内部目录。
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))

    unique_roots: list[Path] = []
    seen = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root.absolute()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_roots.append(root)

    return unique_roots


def resolve_existing_resource(
    path_value: str | Path | None,
    project_root: str | Path | None = None,
) -> Path | None:
    """解析用户路径或内置资源路径；找不到时返回 None。"""
    if not path_value:
        return None

    path = Path(path_value)
    if path.is_absolute():
        return path if path.exists() else None

    for root in runtime_resource_roots(project_root):
        candidate = root / path
        if candidate.exists():
            return candidate

    if path.exists():
        return path

    return None
