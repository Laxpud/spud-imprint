# 后续工作 TODO

仓库准备工作已经完成：项目结构、Git 管理、GitHub 远端、GitHub Actions CI、基础测试、README、使用文档、配置文档、架构文档和 AI 指令都已经建立。

下次继续开发时，优先从第 1 项开始。

## 1. 配置校验

目标：在处理图片前检查 `config.toml` 是否合法，并给出清楚的错误信息。

需要检查：

- `batch.quality` 是否在 `1..100`。
- `batch.format` 是否为支持的格式，例如 `JPEG`、`PNG`、`WEBP`。
- `canvas.layout_mode` 是否为 `original`、`fit`、`fill`、`stretch`。
- `canvas.margin_relative` 是否大于等于 `0` 且小于 `0.5`。
- `canvas.blur_fit_mode` 是否为 `cover` 或 `contain`。
- `photo.shadow_color` 和 `text.color` 这类颜色值长度是否正确。
- `text.alignment` 是否为 `left`、`center`、`right`。
- `text.position_preset` 是否由合法的水平和垂直位置组成。
- 字体路径不存在时是否给出明确提示。
- 输入目录不存在时是否给出明确提示。

建议实现：

- 新增 `src/spud_imprint/validation.py`。
- 定义 `ConfigValidationError`。
- 提供 `validate_config(config, project_root=None, input_dir=None)`。
- 在 `batch` 命令开始处理前调用校验。
- 给错误配置补单元测试。

## 2. 增加 validate-config 命令

目标：用户可以只检查配置，不处理图片。

建议命令：

```powershell
python -m spud_imprint validate-config --config .\examples\config.example.toml
```

成功输出：

```text
Config OK
```

失败输出清楚的字段路径和原因。

## 3. 改善 CLI

建议补充：

- `--version`
- `--verbose`
- `--dry-run`
- 更清晰的错误退出码
- 处理完成后的汇总信息

## 4. 补充代码 docstring 和中文注释

按 `AGENTS.md` 规则，AI 新增或修改 Python 注释和 docstring 时使用中文。

优先补这些模块：

- `src/spud_imprint/config.py`
- `src/spud_imprint/pipeline.py`
- `src/spud_imprint/canvas.py`
- `src/spud_imprint/text.py`

重点解释：

- 配置加载流程。
- 画布尺寸计算。
- 相对尺寸和毫米尺寸的优先级。
- 文本定位逻辑。
- 导出格式处理。

## 5. 增加测试覆盖

优先补：

- 错误配置测试。
- CLI 参数测试。
- 无 EXIF 图片测试。
- 字体路径不存在测试。
- 不同输出格式测试。
- 输入目录为空的测试。

## 6. 准备小型测试 fixture

当前测试使用程序生成图片。后续如果需要测试真实 EXIF 行为，可以添加小型、脱敏、可自由分发的 fixture。

建议路径：

```text
tests/fixtures/
```

注意：真实工作照片继续放在 `local/real-tests/input/`，不要提交到 Git。

## 7. 增加 preview 命令

目标：为未来 GUI 提供预览能力。

建议命令：

```powershell
python -m spud_imprint preview `
  --input .\local\real-tests\input\P1074931.jpg `
  --output .\local\preview.jpeg `
  --config .\examples\config.example.toml
```

第一版可以复用现有渲染流程，只处理单张图。

## 8. 模板系统

目标：允许保存多套常用样式。

建议目录：

```text
templates/
├─ classic.toml
├─ minimal.toml
└─ poster-16x9.toml
```

先不急着实现，等配置模型稳定后再做。

## 9. CLI 打包验证

目标：先把 Python CLI 打成可执行文件，验证分发路径。

候选工具：

- PyInstaller
- Nuitka

先验证 Windows，再考虑 macOS/Linux。

## 10. GUI 技术原型

等 CLI 和配置模型稳定后，再启动 GUI。

第一版 Tauri 原型只做：

- 选择输入目录。
- 选择输出目录。
- 选择配置文件。
- 调用 CLI。
- 显示处理日志。

不要一开始就做完整交互预览。

## 11. 交互预览原型

未来使用 React + Konva.js 验证：

- 加载一张预览图。
- 显示画布。
- 拖动文字。
- 修改文字位置。
- 导出配置。

预览和最终导出必须共享同一份配置模型。

## 12. 发布流程

后续需要补：

- 版本号策略。
- changelog。
- GitHub Release。
- 自动构建包。
- GUI 安装包签名和发布策略。

