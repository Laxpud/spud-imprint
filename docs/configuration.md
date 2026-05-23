# 配置说明

Spud Imprint 使用 TOML 配置文件控制批处理、画布、照片效果和文字样式。示例文件位于：

```text
examples/config.example.toml
```

## 基本结构

配置文件分为四个部分：

```toml
[batch]

[canvas]

[photo]

[text]
```

- `[batch]` 控制输入输出和导出格式。
- `[canvas]` 控制画布尺寸、比例、背景和边距。
- `[photo]` 控制主体照片的圆角和阴影。
- `[text]` 控制元数据文字内容、字体、颜色和位置。

## batch

```toml
[batch]
input_dir = "input"
output_dir = "output"
filename_suffix = "_uniform_watermark"
format = "JPEG"
quality = 100
```

### input_dir

默认输入目录。命令行传入 `--input` 时，会覆盖这个值。

### output_dir

默认输出目录。命令行传入 `--output` 时，会覆盖这个值。

### filename_suffix

输出文件名后缀。默认 `_uniform_watermark`。

例如 `photo.jpg` 会导出为 `photo_uniform_watermark.jpeg`。

### format

导出格式。当前常用值：

```text
JPEG
PNG
WEBP
```

### quality

导出质量，主要影响 JPEG 和 WEBP。范围通常是 `1` 到 `100`，数值越高质量越好，文件也更大。

## canvas

```toml
[canvas]
layout_mode = "fit"
aspect_ratio = 1.7777777778
background_color = [240, 240, 240]
margin_relative = 0.05
blurred_background = true
blur_radius = 100
blur_extra_scale = 1.5
blur_fit_mode = "cover"
```

### layout_mode

画布布局模式。当前支持：

```text
original
fit
fill
stretch
```

- `original`：画布从原图尺寸出发，可根据目标比例扩展。
- `fit`：保持主体照片原始尺寸，根据目标比例扩展画布。
- `fill`：用目标比例生成画布，照片保持原始尺寸居中。
- `stretch`：根据目标比例扩展画布，但不拉伸照片本身。

当前示例使用 `fit`。

### aspect_ratio

画布宽高比。`1.7777777778` 约等于 `16:9`。

常见值：

```text
1.7777777778  # 16:9
1.3333333333  # 4:3
1.0           # 1:1
```

### background_color

画布背景色，使用 RGB 数组：

```toml
background_color = [240, 240, 240]
```

### margin_relative

相对边距。`0.05` 表示边距大约占最终画布尺寸的 5%。

注意：这个值必须大于等于 `0` 且小于 `0.5`。

### margin_mm

毫米单位边距。当前示例没有启用。如果同时设置 `margin_relative` 和 `margin_mm`，代码会优先使用 `margin_relative`。

### blurred_background

是否启用基于原图的模糊背景。

### blur_radius

模糊半径。数值越大，背景越模糊。

### blur_extra_scale

背景图额外放大比例，用于确保模糊背景覆盖整个画布。

### blur_fit_mode

模糊背景填充方式：

```text
cover
contain
```

- `cover`：背景覆盖整个画布，可能裁切。
- `contain`：背景尽量完整显示，可能留边。

## photo

```toml
[photo]
corner_radius_relative = 0.02
shadow_enabled = true
shadow_offset_relative = [0.005, 0.005]
shadow_blur_relative = 0.01
shadow_color = [0, 0, 0, 64]
```

### corner_radius_relative

照片圆角半径，相对于画布短边计算。`0.02` 表示画布短边的 2%。

### corner_radius_mm

毫米单位圆角半径。当前示例没有启用。如果同时设置相对值和毫米值，代码会优先使用相对值。

### shadow_enabled

是否启用照片阴影。

### shadow_offset_relative

阴影偏移，相对于画布宽高计算：

```toml
shadow_offset_relative = [0.005, 0.005]
```

第一个值是横向偏移，第二个值是纵向偏移。

### shadow_offset_mm

毫米单位阴影偏移。当前示例没有启用。如果同时设置相对值和毫米值，代码会优先使用相对值。

### shadow_blur_relative

阴影模糊半径，相对于画布短边计算。

### shadow_blur_radius

像素单位阴影模糊半径。当前示例没有启用。如果同时设置相对值和像素值，代码会优先使用相对值。

### shadow_color

阴影颜色，使用 RGBA 数组：

```toml
shadow_color = [0, 0, 0, 64]
```

最后一个值是透明度，`0` 完全透明，`255` 完全不透明。

## text

```toml
[text]
fields = ["DateTimeOriginal"]
font_size_relative = 0.05
font_name = "assets/fonts/NotoSerifSC-VF.ttf"
color = [255, 255, 255]
shadow_color = [220, 220, 220, 128]
alignment = "left"
line_spacing = 1.5
show_field_names = false
position_preset = "center bottom"
margin_percent = 0.05
```

### fields

要显示的 EXIF 字段列表。示例只显示拍摄日期：

```toml
fields = ["DateTimeOriginal"]
```

常见字段包括：

```text
DateTimeOriginal
Make
Model
LensModel
ExposureTime
FNumber
ISOSpeedRatings
FocalLength
```

### font_size_relative

字体大小，相对于画布短边计算。`0.05` 表示画布短边的 5%。

### font_size_mm

毫米单位字体大小。当前示例没有启用。如果同时设置相对值和毫米值，代码会优先使用相对值。

### font_name

字体路径。示例使用仓库内置字体：

```toml
font_name = "assets/fonts/NotoSerifSC-VF.ttf"
```

建议从仓库根目录运行命令，这样相对路径可以正确解析。

### color

主文字颜色，使用 RGB 数组：

```toml
color = [255, 255, 255]
```

### shadow_color

文字描边或阴影颜色，使用 RGBA 数组：

```toml
shadow_color = [220, 220, 220, 128]
```

### alignment

多行文本内部对齐方式：

```text
left
center
right
```

### line_spacing

行距倍数。`1.5` 表示 1.5 倍字体大小。

### show_field_names

是否显示字段名。

如果为 `true`，输出类似：

```text
DateTimeOriginal: 2025-09-06
```

如果为 `false`，输出类似：

```text
2025-09-06
```

### position_preset

文本位置预设，由水平位置和垂直位置组成：

```text
left top
left middle
left bottom
center top
center middle
center bottom
right top
right middle
right bottom
```

示例使用：

```toml
position_preset = "center bottom"
```

### margin_percent

文本距离画布边缘的百分比边距，仅在使用 `position_preset` 时生效。

## 推荐本地配置

不要直接修改 `examples/config.example.toml`。建议复制到：

```text
local/config.toml
```

然后使用：

```powershell
python -m spud_imprint batch `
  --input .\local\real-tests\input `
  --output .\local\real-tests\output `
  --config .\local\config.toml
```

`local/` 已被 Git 忽略，适合保存个人配置和真实照片测试文件。

