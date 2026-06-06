# CLI 打包验证

本文档记录第 9 项 Windows CLI 打包验证流程。当前目标是先验证 Python CLI 可以作为便携可执行文件分发；正式版本号、安装器、签名、GitHub Release 和跨平台自动构建留到后续发布流程处理。

## 当前策略

第一阶段使用 PyInstaller 的 one-dir 模式，生成 Windows x64 便携目录：

```text
dist/spud-imprint-windows-x64/
  spud-imprint.exe
  assets/
  templates/
  examples/
```

选择 one-dir 的原因是便于排查资源路径、Pillow 动态依赖和后续 Tauri sidecar 调用问题。暂不使用 one-file，避免把启动解包、临时目录和资源查找问题混在一起。

## 构建命令

先准备开发环境：

```powershell
uv venv
uv pip install -e .
```

然后运行 Windows 构建脚本：

```powershell
.\scripts\build-windows.ps1
```

脚本会依次执行：

1. `python -m unittest discover -s tests`
2. 检查 PyInstaller，缺失时用 `uv pip install pyinstaller` 安装到当前环境。
3. 使用 `packaging/windows/spud-imprint.spec` 构建 one-dir 包。
4. 把 `assets/`、`templates/` 和 `examples/` 复制到 exe 同级目录。
5. 运行 `scripts/smoke-packaged-cli.py` 做打包冒烟测试。

## 冒烟测试

冒烟测试会在源码目录外创建临时工作目录，并运行：

```powershell
.\dist\spud-imprint-windows-x64\spud-imprint.exe --version
.\dist\spud-imprint-windows-x64\spud-imprint.exe validate-config --template minimal
.\dist\spud-imprint-windows-x64\spud-imprint.exe preview --input <temp-image> --output <temp-output> --template minimal
.\dist\spud-imprint-windows-x64\spud-imprint.exe batch --input <temp-input-dir> --output <temp-output-dir> --template classic --dry-run
```

`preview` 输出会再用 Pillow 打开校验，确认打包后的字体、模板和图像导出链路可用。

## 资源路径约定

CLI 会按以下优先级查找模板、默认字体等资源：

1. 用户传入的绝对路径。
2. 当前工作目录下的相对路径。
3. exe 同级目录或源码项目根目录。
4. PyInstaller `_MEIPASS` 解包目录。

因此，便携包中的 `assets/`、`templates/` 和 `examples/` 应保留在 `spud-imprint.exe` 同级目录。用户显式传入的配置路径、字体路径和模板路径仍优先遵循当前工作目录语义。

## 已知限制

- 当前只验证 Windows x64 CLI 便携包。
- 不生成安装器，不做签名，不上传 GitHub Release。
- 不提交 `build/`、`dist/` 或其他生成产物。
- Nuitka 暂不作为默认构建工具；后续如果包体积、启动速度或发布流程需要，再单独比较。
