# 使用指南

本文档说明如何在本地安装、运行和验证 Spud Imprint。

## 安装开发环境

推荐使用 `uv`：

```powershell
uv venv
uv pip install -e .
```

也可以使用 Python 自带的 `venv`：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

安装完成后，可以通过模块方式运行：

```powershell
python -m spud_imprint --help
```

如果当前 Python 环境的 Scripts 目录在 `PATH` 中，也可以直接运行：

```powershell
spud-imprint --help
```

## 准备输入和输出目录

普通本地使用建议把照片放在：

```text
local/real-tests/input/
```

输出结果会写入：

```text
local/real-tests/output/
```

`local/` 是本地专用目录，已经被 Git 忽略。这里适合放真实照片、手动测试结果和临时实验文件。

## 运行批处理

使用示例配置处理本地真实照片：

```powershell
python -m spud_imprint batch `
  --input .\local\real-tests\input `
  --output .\local\real-tests\output `
  --config .\examples\config.example.toml
```

命令会做这些事：

1. 扫描输入目录中的图片文件。
2. 读取照片和 EXIF 元数据。
3. 创建统一比例的画布。
4. 添加模糊背景、照片圆角、阴影和文本。
5. 把结果导出到输出目录。

当前支持的输入扩展名：

```text
.jpg
.jpeg
.png
.bmp
.tiff
.tif
```

## 输出文件名

默认配置会给输出文件添加 `_uniform_watermark` 后缀。例如：

```text
P1074931.jpg
```

会导出为：

```text
P1074931_uniform_watermark.jpeg
```

后缀和导出格式可以在配置文件的 `[batch]` 部分修改。

## 配置文件

默认示例配置在：

```text
examples/config.example.toml
```

复制一份到本地目录后再修改更合适，例如：

```text
local/config.toml
```

然后运行：

```powershell
python -m spud_imprint batch `
  --input .\local\real-tests\input `
  --output .\local\real-tests\output `
  --config .\local\config.toml
```

配置项说明见 [configuration.md](configuration.md)。

## 运行测试

默认测试命令：

```powershell
python -m unittest discover -s tests
```

这些测试使用程序生成的小图片和临时目录，不依赖真实照片。

## 常见问题

### 找不到字体怎么办

示例配置使用：

```text
assets/fonts/NotoSerifSC-VF.ttf
```

请从仓库根目录运行命令，或者在配置文件中写入可访问的字体路径。

### 为什么真实照片不进 Git

真实照片通常较大，EXIF 中也可能包含设备、时间、位置等隐私信息。本项目约定真实照片只放在被 Git 忽略的 `local/` 目录中。

### 什么时候使用 tests/fixtures

只有小型、脱敏、可自由分发，并且必须参与自动测试的素材，才应该放入 `tests/fixtures/`。

