# Spud Imprint

Spud Imprint 是一个批量照片题字和水印工具。

[English README](README.en.md)

这个项目正在从早期的 Pillow 脚本重构为一个可复用的 Python 代码库。当前优先目标是先稳定核心图像处理能力和 CLI；未来会在同一套核心逻辑之上扩展现代跨平台 GUI。

## 当前状态

- 使用 Python 和 Pillow 实现核心图像处理。
- 已提供批处理 CLI 作为第一阶段稳定入口。
- 未来计划使用 Tauri + React/TypeScript 实现现代跨平台 GUI。
- 未来预览编辑器会使用 Konva.js 或类似 Canvas 工具支持直接拖拽操作。

## 开发环境

推荐使用 `uv` 管理本项目的 Python 虚拟环境和依赖：

```powershell
uv venv
uv pip install -e .
```

如果暂时不用 `uv`，也可以使用标准库 `venv`：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

## 运行批处理

```powershell
python -m spud_imprint batch `
  --input .\input `
  --output .\output `
  --config .\examples\config.example.toml
```

命令会扫描输入目录中的常见图片格式，根据配置渲染水印和题字，并把导出结果写入输出目录。

如果只想检查配置文件，可以运行：

```powershell
python -m spud_imprint validate-config --config .\examples\config.example.toml
```

配置合法时会输出 `Config OK`。如果要在批处理前预览会处理哪些图片，可以给 `batch` 添加 `--dry-run`；需要更多路径信息时添加 `--verbose`。

如果只想渲染一张预览图，可以使用 `preview`：

```powershell
python -m spud_imprint preview `
  --input .\local\real-tests\input\P1074931.jpg `
  --output .\local\preview.jpeg `
  --config .\examples\config.example.toml
```

常用样式可以通过 `--template` 选择，例如 `classic`、`minimal` 或 `poster-16x9`：

```powershell
python -m spud_imprint preview `
  --input .\local\real-tests\input\P1074931.jpg `
  --output .\local\preview.jpeg `
  --template minimal
```

查看当前版本使用：

```powershell
python -m spud_imprint --version
```

本地原始照片和生成结果不会进入 Git。建议把真实照片测试素材放在：

```text
local/real-tests/input/
```

对应导出结果放在：

```text
local/real-tests/output/
```

`local/` 是本地专用目录，已被 Git 忽略。

## 运行测试

```powershell
python -m unittest discover -s tests
```

当前测试使用程序生成的小图片和临时目录，不依赖真实照片素材。真实照片通常体积大、可能包含隐私或版权信息，不应该默认进入仓库。

如果要用自己的真实照片做本地手动测试，可以运行：

```powershell
python -m spud_imprint batch `
  --input .\local\real-tests\input `
  --output .\local\real-tests\output `
  --config .\examples\config.example.toml
```

## 打包验证

当前 Windows CLI 便携包使用 PyInstaller one-dir 方式验证：

```powershell
.\scripts\build-windows.ps1
```

脚本会运行默认测试、构建 `dist/spud-imprint-windows-x64/`，并在源码目录外执行打包冒烟测试。详细说明见 [docs/packaging.md](docs/packaging.md)。

## GUI 技术原型

桌面 GUI 原型位于 `gui/`，使用 Tauri 2 + React + TypeScript。当前原型只负责选择输入目录、输出目录和配置文件，随后调用现有 Python CLI 并显示处理日志；完整交互预览留到后续阶段。

```powershell
cd gui
npm install
npm run tauri dev
```

详细说明见 [docs/gui-prototype.md](docs/gui-prototype.md)。

## 开发规范

本仓库的具体约定见 [docs/development.md](docs/development.md)。

更多文档：

- [后续工作 TODO](TODO.md)
- [使用指南](docs/usage.md)
- [配置说明](docs/configuration.md)
- [CLI 打包验证](docs/packaging.md)
- [GUI 技术原型](docs/gui-prototype.md)
- [代码导览教程](docs/code-walkthrough.md)
- [架构说明](docs/architecture.md)

核心约定：

- 默认 README 使用中文，同时维护英文版 `README.en.md`。
- AI 助手新增或修改 Python 注释和 docstring 时使用中文；这不是对人类贡献者的强制要求。
- 代码标识符、CLI 命令、日志、终端输出、配置键名继续使用英文。
- 测试素材只提交小型、脱敏、可复现的 fixture；真实照片素材不直接进入 Git。

## 路线图

1. 保留旧脚本到 `legacy/` 作为参考。
2. 稳定 `src/spud_imprint` 中的核心处理模块。
3. 完善配置驱动的 CLI。
4. 扩展测试覆盖元数据、布局、导出和端到端批处理。
5. 通过轻量桌面 GUI 原型验证 CLI 复用路径。
