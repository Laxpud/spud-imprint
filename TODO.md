# 后续工作 TODO

仓库准备工作已经完成：项目结构、Git 管理、GitHub 远端、GitHub Actions CI、基础测试、README、使用文档、配置文档、架构文档和 AI 指令都已经建立。

当前状态更新于 2026-06-06。下次继续开发时，优先从第 10 项 GUI 技术原型开始。

## [x] 1. 配置校验

目标：在处理图片前检查 `config.toml` 是否合法，并给出清楚的错误信息。

当前状态：已新增独立配置校验模块，并在 `batch` 命令开始处理前统一检查配置；错误会一次性列出字段路径和原因。

需要检查：

- [x] `batch.quality` 是否在 `1..100`。
- [x] `batch.format` 是否为支持的格式，例如 `JPEG`、`PNG`、`WEBP`。
- [x] `canvas.layout_mode` 是否为 `original`、`fit`、`fill`、`stretch`。
- [x] `canvas.margin_relative` 是否大于等于 `0` 且小于 `0.5`。
- [x] `canvas.blur_fit_mode` 是否为 `cover` 或 `contain`。
- [x] `photo.shadow_color` 和 `text.color` 这类颜色值长度是否正确。
- [x] `text.alignment` 是否为 `left`、`center`、`right`。
- [x] `text.position_preset` 是否由合法的水平和垂直位置组成。
- [x] 字体路径不存在时是否给出明确提示。
- [x] 输入目录不存在时是否给出明确提示。

建议实现：

- [x] 新增 `src/spud_imprint/validation.py`。
- [x] 定义 `ConfigValidationError`。
- [x] 提供 `validate_config(config, project_root=None, input_dir=None)`。
- [x] 在 `batch` 命令开始处理前调用校验。
- [x] 给错误配置补单元测试。

## [x] 2. 增加 validate-config 命令

目标：用户可以只检查配置，不处理图片。

当前状态：已新增 `validate-config` 子命令；默认只检查配置字段和字体等文件路径，显式传入 `--input` 时会同步检查输入目录。

建议命令：

```powershell
python -m spud_imprint validate-config --config .\examples\config.example.toml
```

成功输出：

```text
Config OK
```

失败输出清楚的字段路径和原因。

## [x] 3. 改善 CLI

当前状态：已具备基础批处理命令、单图成功/失败输出、空输入提示、完成汇总、版本号输出、详细日志和 dry-run 预览。

建议补充：

- [x] `--version`
- [x] `--verbose`
- [x] `--dry-run`
- [x] 更清晰的错误退出码
- [x] 处理完成后的汇总信息

## [x] 4. 补充代码 docstring 和中文注释

按 `AGENTS.md` 规则，AI 新增或修改 Python 注释和 docstring 时使用中文。

当前状态：已给优先模块补充中文 docstring 和关键块级注释。

优先补这些模块：

- [x] `src/spud_imprint/config.py`
- [x] `src/spud_imprint/pipeline.py`
- [x] `src/spud_imprint/canvas.py`
- [x] `src/spud_imprint/text.py`

重点解释：

- [x] 配置加载流程。
- [x] 画布尺寸计算。
- [x] 相对尺寸和毫米尺寸的优先级。
- [x] 文本定位逻辑。
- [x] 导出格式处理。

## [x] 5. 增加测试覆盖

当前状态：已补齐无 EXIF 图片、不同输出格式和空输入目录等专项测试；测试仍使用临时目录和小型 fixture，避免依赖本地真实照片。

优先补：

- [x] 错误配置测试。
- [x] CLI 参数测试。
- [x] 无 EXIF 图片测试。
- [x] 字体路径不存在测试。
- [x] 不同输出格式测试。
- [x] 输入目录为空的测试。

## [x] 6. 准备小型测试 fixture

当前测试使用程序生成图片。后续如果需要测试真实 EXIF 行为，可以添加小型、脱敏、可自由分发的 fixture。

当前状态：已添加 `tests/fixtures/`，其中包含一张小型合成 JPEG fixture，用于稳定测试 EXIF 读取路径。真实工作照片继续只放在 `local/real-tests/input/` 做本地手动测试，不提交到 Git。

建议路径：

```text
tests/fixtures/
```

注意：真实工作照片继续放在 `local/real-tests/input/`，不要提交到 Git。

## [x] 7. 增加 preview 命令

目标：为未来 GUI 提供预览能力。

当前状态：已新增 `preview` 子命令，复用现有渲染流程处理单张图片，并把结果导出到用户指定路径。

建议命令：

```powershell
python -m spud_imprint preview `
  --input .\local\real-tests\input\P1074931.jpg `
  --output .\local\preview.jpeg `
  --config .\examples\config.example.toml
```

第一版已复用现有渲染流程，只处理单张图。

## [x] 8. 模板系统

目标：允许保存多套常用样式。

当前状态：已新增 `templates/` 目录和模板加载逻辑；`batch`、`preview`、`validate-config` 都支持 `--template`。加载顺序为内置默认值、模板、用户配置文件。

建议目录：

```text
templates/
├─ classic.toml
├─ minimal.toml
└─ poster-16x9.toml
```

已先实现轻量级模板系统，模板只保存常用样式；个人路径和真实照片测试配置继续放在被 Git 忽略的 `local/`。

## [x] 9. CLI 打包验证

目标：先把 Python CLI 打成可执行文件，验证分发路径。

当前状态：已使用 PyInstaller one-dir 打通 Windows x64 便携包验证流程；构建脚本会运行默认单元测试、生成 `dist/spud-imprint-windows-x64/`，并在源码目录外执行打包冒烟测试。

候选工具：

- PyInstaller：已作为第一阶段默认方案。
- Nuitka

已先验证 Windows；Nuitka、macOS/Linux、安装器、签名和 GitHub Release 留到后续发布流程中再评估。

## [ ] 10. GUI 技术原型

等 CLI 和配置模型稳定后，再启动 GUI。

当前状态：尚未开始。

第一版 Tauri 原型只做：

- 选择输入目录。
- 选择输出目录。
- 选择配置文件。
- 调用 CLI。
- 显示处理日志。

不要一开始就做完整交互预览。

## [ ] 11. 交互预览原型

未来使用 React + Konva.js 验证：

- 加载一张预览图。
- 显示画布。
- 拖动文字。
- 修改文字位置。
- 导出配置。

当前状态：尚未开始。

预览和最终导出必须共享同一份配置模型。

## [ ] 12. 准备 GitHub 页面效果展示图

目标：从本地真实照片中挑选少量适合公开展示的样张，生成脱敏、压缩后的 GitHub 页面展示素材。

当前状态：真实照片只保留在 `local/real-tests/input/` 用于本地手动测试，尚未生成公开展示版本。

建议实现：

- [ ] 优先选择视觉隐私风险低的花卉、公共景点远景或城市天际线。
- [ ] 避免直接使用人群和车辆密集街景，必要时先裁切或模糊敏感区域。
- [ ] 生成中等尺寸展示图，不提交原始大图或 RAW 文件。
- [ ] 导出展示图时剥离 EXIF，尤其是 GPS、序列号、作者、版权等字段。
- [ ] 将展示图放在 `docs/showcase/` 或 `assets/showcase/`，并在 README 或 GitHub Pages 中引用。
- [ ] 在文档中说明展示图为作者自摄并授权本项目展示使用。

## [ ] 13. 发布流程

当前状态：尚未开始。

后续需要补：

- 版本号策略。
- changelog。
- GitHub Release。
- 自动构建包。
- GUI 安装包签名和发布策略。
