# GUI 技术原型

本文档记录第 10 项 Tauri 技术原型。当前目标不是完整图片预览编辑器，而是验证桌面界面能否复用已经稳定的 Python CLI。

## 当前范围

第一版原型位于 `gui/`，技术栈为 Tauri 2 + React + TypeScript + Vite。界面只包含：

- 输入目录选择。
- 输出目录选择。
- TOML 配置文件选择。
- 调用批处理 CLI。
- 显示命令、退出码、标准输出和标准错误。

交互预览、文字拖拽、画布编辑和配置导出留给后续第 11 项。

## 运行方式

先准备 Python 开发环境：

```powershell
uv venv
uv pip install -e .
```

再安装 GUI 依赖：

```powershell
cd gui
npm install
```

启动 Tauri 开发模式：

```powershell
npm run tauri dev
```

也可以只检查前端构建：

```powershell
npm run build
```

如果只打开 Vite 页面 `http://127.0.0.1:1420`，界面只能用于布局预览。浏览器无法提供 Tauri 的原生文件和目录选择器，也不能调用 Rust 后端命令；选择按钮会在日志面板提示改用 `npm run tauri dev`。

Rust 后端校验：

```powershell
cd gui\src-tauri
cargo check
```

## CLI 解析规则

Rust 后端会按以下顺序寻找可调用的 CLI：

1. 环境变量 `SPUD_IMPRINT_CLI` 指向的可执行文件。
2. `dist/spud-imprint-windows-x64/spud-imprint.exe`。
3. 仓库内 `.venv/Scripts/python.exe`，通过 `python -m spud_imprint` 调用。
4. PATH 中的 `python`，同样通过 `python -m spud_imprint` 调用。

开发模式下会把仓库 `src/` 加到 `PYTHONPATH`，便于在尚未重新安装 editable 包时调试本地代码。

## 设计边界

- GUI 不包含图像渲染核心逻辑。
- 批处理行为、错误信息和导出结果继续以 Python CLI 为准。
- 当前原型要求输出目录已经存在。
- 当前原型不会提交生成结果、真实照片或 GUI 构建产物。
