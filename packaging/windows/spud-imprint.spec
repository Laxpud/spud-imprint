# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_submodules


project_root = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
src_dir = os.path.join(project_root, "src")
entry_script = os.path.join(project_root, "scripts", "spud_imprint_entry.py")

datas = [
    (os.path.join(project_root, "assets"), "assets"),
    (os.path.join(project_root, "templates"), "templates"),
    (os.path.join(project_root, "examples"), "examples"),
]

a = Analysis(
    [entry_script],
    pathex=[src_dir, project_root],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("PIL"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="spud-imprint",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="spud-imprint-windows-x64",
)
