# Laxpud Imprint

Laxpud Imprint 是一个批量照片题字和水印工具。

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
python -m laxpud_imprint batch `
  --input .\input `
  --output .\output `
  --config .\examples\config.example.toml
```

命令会扫描输入目录中的常见图片格式，根据配置渲染水印和题字，并把导出结果写入输出目录。

本地原始照片和生成结果不会进入 Git。请把自己的工作照片放在 `input/` 这类被忽略的目录中。

## 运行测试

```powershell
python -m unittest discover -s tests
```

当前测试使用程序生成的小图片和临时目录，不依赖真实照片素材。真实照片通常体积大、可能包含隐私或版权信息，不应该默认进入仓库。

## 开发规范

本仓库的具体约定见 [docs/development.md](docs/development.md)。

核心约定：

- 默认 README 使用中文，同时维护英文版 `README.en.md`。
- AI 助手新增或修改 Python 注释和 docstring 时使用中文；这不是对人类贡献者的强制要求。
- 代码标识符、CLI 命令、日志、终端输出、配置键名继续使用英文。
- 测试素材只提交小型、脱敏、可复现的 fixture；真实照片素材不直接进入 Git。

## 路线图

1. 保留旧脚本到 `legacy/` 作为参考。
2. 稳定 `src/laxpud_imprint` 中的核心处理模块。
3. 完善配置驱动的 CLI。
4. 扩展测试覆盖元数据、布局、导出和端到端批处理。
5. 核心逻辑稳定后，再开始桌面 GUI。
