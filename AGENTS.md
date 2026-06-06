# AI 代理指令

本文件定义本仓库专用的 AI 编码代理工作规则。它主要承担入口索引、模块路由和行为边界的作用；架构背景、配置说明和用户手册等长文档应维护在 `docs/` 中。

## 文档入口

- 架构背景和技术决策：`docs/architecture.md`。
- 配置格式和模板说明：`docs/configuration.md`。
- 开发、测试和发布流程：`docs/development.md`。
- 用户命令和使用示例：`docs/usage.md`。
- 当前计划、进度和未完成事项：`TODO.md`。

## 模块路由

- `src/spud_imprint/cli.py`：CLI 参数、子命令、退出码和终端输出。
- `src/spud_imprint/pipeline.py`：批处理、预览和单图处理流程编排。
- `src/spud_imprint/config.py`：配置模型、默认值和 TOML 模板加载。
- `src/spud_imprint/validation.py`：配置和输入路径校验。
- `src/spud_imprint/canvas.py`：画布、照片布局、边距、圆角、阴影和背景。
- `src/spud_imprint/metadata.py`：图片元数据读取与字段归类。
- `src/spud_imprint/text.py`：文字样式、字段排版和绘制。
- `src/spud_imprint/export.py`：导出格式、质量和文件保存。
- `tests/`：单元测试和小型 fixture；新增行为应优先补充对应测试。

## 行为边界

- 修改前先按任务类型阅读相关入口文档和模块；不要在 `AGENTS.md` 中复制长篇架构说明。
- 优先保持 CLI 用户可见行为稳定，包括子命令、退出码、终端输出和 dry-run 语义。
- 图像处理核心应放在 `pipeline.py` 及其下游核心模块中，不要把核心渲染逻辑塞进 CLI。
- 新增配置项时，同步考虑配置模型、默认值、模板、配置文档、中英文 README 和测试。
- 未来 GUI 应复用稳定的 Python 核心和配置模型，不应引入另一套独立渲染逻辑。

## 项目方向

- 目前继续把图像处理核心保留在 Python 中。
- 在启动桌面 GUI 之前，优先保持 CLI 行为稳定。
- 未来 GUI 方向：Tauri + React/TypeScript，交互式预览由 Konva.js 或类似 Canvas 库处理。
- 除非包体积或分发限制成为明确优先事项，不要把渲染核心改写为 Rust。

## 语言规则

- 代码标识符、模块名、CLI 命令、终端输出、日志消息、异常消息和配置键使用英文。
- AI 代理新增或编辑 Python 注释和 docstring 时，这些注释和 docstring 使用中文。
- 中文注释和 docstring 规则只约束 AI 代理；不要把它表述为人类贡献者必须遵守的硬性要求。
- 默认面向用户的文档保持中文。修改 `README.md` 时，同步维护 `README.en.md`。

## Python 风格

- 遵循 PEP 8 格式规范和 PEP 257 docstring 规范。
- 适度多写中文注释和 docstring，让编程经验较少的读者也能快速理解每个有意义代码块在做什么以及为什么这样做。
- 在重要步骤、分支、循环、数据转换、图像几何计算、坐标计算、格式转换、配置处理和边界情况处理前，优先添加简短的块级注释。
- 避免逐行写只复述赋值或函数调用的噪声注释；注释应说明目的、数据流、假设或这样选择的原因。
- 公共类、公共函数和复杂的私有方法应有简洁的中文 docstring，说明其职责、关键输入、输出以及重要副作用。

## 测试规则

- 提交前运行默认测试命令：

```powershell
python -m unittest discover -s tests
```

- 快速测试优先使用程序生成的图片和临时目录。
- 默认不要提交真实照片资产。
- 本地真实照片手动测试输入放在 `local/real-tests/input/`。
- 本地真实照片手动测试输出放在 `local/real-tests/output/`。
- 如果需要 fixture 图片，把小型、脱敏、可自由分发的文件放在 `tests/fixtures/`。

## TODO 维护规则

- `TODO.md` 使用复选框记录进度：未完成写 `[ ]`，已完成写 `[x]`。
- 完成或部分完成 `TODO.md` 中的事项时，在同一轮改动中同步更新对应主项和子项状态。
- 只有在代码、文档和必要测试都已经落地后，才把主项标记为 `[x]`。
- 部分完成的事项保持主项为 `[ ]`，并在条目下写明“当前状态”和剩余缺口。
- 新增 TODO 时保持中文描述，写清目标、当前状态、建议实现或验收标准。
- 不要把已经完成的事项直接删除；优先保留完成记录，除非是在专门整理历史 TODO。

## Git 与资产

- 不要创建 `v0.5.py` 这类带版本号的脚本文件；使用 Git commit 和 tag 管理版本。
- AI 代理完成一轮文件改动后，默认检查状态、运行适用测试，并自动提交本轮相关改动；用户明确要求暂不提交、只修改不提交或需要先人工检查时除外。
- 自动提交前只暂存本轮相关文件；如果工作区已有无关改动，不要把它们混入提交。
- 提交信息使用 Conventional Commits：

```text
type(scope): concise summary
```

- 使用清晰的 type，例如 `feat`、`fix`、`docs`、`test`、`refactor`、`style`、`build`、`ci` 或 `chore`。
- scope 能说明影响范围时添加简短 scope，例如 `config`、`cli`、`canvas`、`pipeline`、`docs` 或 `tests`。
- summary 使用英文祈使句，并保持具体。优先使用 `docs(agents): require conventional commit messages`，不要使用 `update files` 或 `misc changes` 这类笼统信息。
- 除非改动非常小，否则在提交正文中使用 bullet 子条目概括主要改动，例如实现细节、影响的行为、运行过的测试或迁移说明。
- 提交正文的每个 bullet 必须独立换行；使用命令行提交时，优先为每个 bullet 使用单独的 `-m` 参数，或使用提交消息文件，禁止把多个 bullet 写进同一个 `-m` 字符串。
- 提交后默认用 `git log -1 --format=full` 检查最近一次提交消息，确认 subject、空行和每个 body bullet 的换行格式正确。
- 原始遗留脚本保留在 `legacy/` 下。
- 不要提交生成输出、工作照片、缓存或虚拟环境。
- 保持 `local/` 被忽略；它专门用于本地真实照片测试。
- 保持仓库根目录聚焦于项目元数据和源码目录。

## 依赖管理

- 本地 Python 环境设置优先使用 `uv`：

```powershell
uv venv
uv pip install -e .
```

- `uv` 是开发工具偏好，不是终端用户运行时依赖。
