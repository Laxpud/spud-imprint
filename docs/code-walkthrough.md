# 代码导览教程

这份文档面向想学习 Spud Imprint 代码库的读者。它不替代 [使用指南](usage.md) 和 [配置说明](configuration.md)：使用指南告诉你命令怎么跑，配置说明告诉你参数怎么填；本导览关注的是这些命令和参数进入代码后，怎样一步一步变成一张导出的图片。

如果你不熟悉 Python 或 Pillow，也可以先把它当成“读代码地图”。不用一次读懂所有细节，先知道每个模块负责什么，再顺着一次完整流程回头看具体函数，会轻松很多。

## 这个项目在做什么

Spud Imprint 的核心任务可以拆成四件事：

1. 读取一张或多张照片。
2. 根据配置创建成品画布，并把照片放到合适位置。
3. 读取照片 EXIF 元数据，把日期、相机、镜头、曝光等字段画到图上。
4. 按配置选择格式和质量，把结果保存到输出目录。

代码按这个过程分层：

- `src/spud_imprint/cli.py`：命令行入口，负责解析 `batch`、`preview`、`validate-config` 等子命令。
- `src/spud_imprint/config.py`：配置模型、默认值、TOML 文件和模板加载。
- `src/spud_imprint/validation.py`：在真正处理图片前检查配置是否合法。
- `src/spud_imprint/pipeline.py`：把“读图、建画布、读元数据、画文字、导出”串成完整流程。
- `src/spud_imprint/canvas.py`：计算画布尺寸、照片位置、边距、圆角、阴影和模糊背景。
- `src/spud_imprint/metadata.py`：读取 EXIF，并把字段分到设备、拍摄参数、时间等类别。
- `src/spud_imprint/text.py`：把元数据字段排版成文字，并画到画布上。
- `src/spud_imprint/export.py`：根据导出格式保存图片，并处理文件后缀、JPEG DPI 等细节。

一个简单的记忆方式是：`cli.py` 接住用户命令，`config.py` 准备规则，`validation.py` 先把明显错误挡住，`pipeline.py` 指挥核心处理，其他模块各自完成一个专业步骤。

## 推荐阅读顺序

第一次读这个项目，不建议从最长的 `canvas.py` 开始。更顺的路线是：

1. 先看 `cli.py`，了解用户能发起哪些动作。
2. 再看 `config.py`，理解默认配置和用户配置如何合并。
3. 接着看 `pipeline.py`，因为它是核心流程的“目录页”。
4. 然后按兴趣进入 `canvas.py`、`metadata.py`、`text.py`、`export.py`。
5. 最后看 `tests/`，用测试反向确认每个模块的预期行为。

如果只想先抓主线，可以重点读 `pipeline.py` 里的三个函数：

- `process_batch()`：批量处理一个目录。
- `process_preview()`：只处理一张预览图。
- `render_image()`：真正把单张照片渲染成成品图。

## 从一次 batch 命令开始

假设用户运行：

```powershell
python -m spud_imprint batch `
  --input .\local\real-tests\input `
  --output .\local\real-tests\output `
  --config .\examples\config.example.toml
```

这条命令首先进入 `cli.py`。`build_parser()` 用 `argparse` 声明所有命令和参数；`main()` 解析参数后，根据 `args.command` 分发到 `run_batch()`。

`run_batch()` 做几件事：

1. 调用 `_load_config()` 读取配置。
2. 调用 `validate_config()` 检查配置、字体路径和输入目录。
3. 如果带了 `--dry-run`，只扫描图片并打印计划输出，不写文件。
4. 正常批处理时调用 `process_batch()`。
5. 把每张图片的处理结果打印成 `OK` 或 `ERR`，最后输出汇总。

这里有一个重要边界：CLI 只负责“命令行用户体验”，例如参数、退出码、终端输出和 dry-run 展示。真正的图像处理不放在 CLI 里，而是交给 `pipeline.py` 和下游模块。这样未来 GUI 也能复用同一套核心流程。

## 配置如何生效

配置入口在 `config.py`。完整配置对象是 `ImprintConfig`，里面分成四组：

- `BatchConfig`：输入输出、文件名后缀、导出格式和质量。
- `CanvasConfig`：画布比例、背景、外边距和模糊背景。
- `PhotoConfig`：照片边距、圆角和阴影。
- `TextConfig`：要显示的字段、字体、颜色、对齐和位置。

`load_config()` 的加载顺序是：

```text
内置默认值 -> 模板 -> 用户配置文件
```

也就是说，代码先创建一份默认 `ImprintConfig()`。如果命令行传了 `--template`，模板覆盖默认值；如果又传了 `--config`，用户配置再覆盖模板。这个顺序让模板适合保存常用外观，而个人配置可以继续覆盖局部字段。

真正覆盖字段的是 `_apply_raw_config()` 和 `_merge_dataclass()`。TOML 读出来的颜色和坐标通常是列表，例如 `[255, 255, 255]`；代码会把它们整理成 tuple，方便 Pillow 后续当作颜色使用。`aspect_ratio` 也会被 `_parse_aspect_ratio()` 转成数字，所以 `"16:9"`、`"16/9"`、`1.777` 都能进入同一套计算逻辑。

命令行参数还有一层覆盖关系。比如 `batch.input_dir` 可以写在配置里，但用户运行命令时传入 `--input`，`run_batch()` 和 `process_batch()` 会优先使用命令行传入的路径。

## 批处理和预览的共同核心

`pipeline.py` 是理解项目的关键。它把单张处理、批量处理和预览处理拆开，但最核心的渲染逻辑共享在 `render_image()`。

批量处理路径大致是：

```text
process_batch()
  -> iter_image_files()
  -> process_image()
  -> render_image()
  -> export_image()
```

预览处理路径大致是：

```text
process_preview()
  -> render_image()
  -> export_image()
```

这意味着 `batch` 和 `preview` 看到的画布、文字、背景和导出逻辑是一致的。未来 GUI 如果只想预览一张图，也可以复用同一个核心思想：给它一张输入图、一个输出路径和一份配置。

`process_batch()` 还有一个适合学习的设计：单张图片失败不会中断整批任务。每张图片都会生成一个 `ProcessResult`，里面记录源文件、输出路径、是否成功和错误信息。CLI 最后只是把这些结果打印出来。

## render_image 做了什么

`render_image()` 可以看成“单张图片加工流水线”。它的步骤是：

1. 用 Pillow 打开图片，并调用 `img.load()` 把像素读进内存。
2. 根据配置创建 `VirtualCanvas`，让它计算最终画布尺寸和照片偏移。
3. 调用 `canvas.create_canvas()` 创建纯色背景画布。
4. 如果启用模糊背景，调用 `canvas.add_blurred_background()` 先铺一层放大模糊的原图。
5. 调用 `canvas.add_photo_to_canvas()` 把阴影和清晰照片贴到画布上。
6. 调用 `get_categorized_metadata()` 读取并分类 EXIF。
7. 根据 `TextConfig` 创建 `TextStylePreset`。
8. 调用 `add_text_to_canvas()` 把指定元数据字段画到图上。
9. 返回渲染好的图片和 `canvas` 对象。

为什么返回值里还要带 `canvas`？因为导出 JPEG 时需要用到原图 DPI。`VirtualCanvas` 在初始化时会从原图读取 DPI，读不到就默认使用 `300`。`export_image()` 保存 JPEG 时会把这个 DPI 写回去。

## 画布几何入门

`canvas.py` 里最难的是几何计算。先不要急着记住所有分支，只要抓住几个核心概念。

第一，画布和照片不是一回事。照片是原始输入图，画布是最终成品图。代码会尽量保持照片本身不被缩放，而是通过扩展画布、添加背景、调整偏移来得到统一比例的成品。

第二，`frame_mode` 是新相框逻辑。常用值有：

- `photo_aspect`：画框比例跟随照片比例。
- `fixed_aspect`：画框使用固定比例，例如 `16:9`。

如果没有设置 `frame_mode`，代码还保留旧版 `layout_mode`，包括 `original`、`fit`、`fill`、`stretch`。配置文档会说明这些模式怎么填；读源码时只要知道：它们最终都会算出画布宽高和照片偏移。

第三，相对边距的含义是“占最终画布的比例”。例如 `margin_relative = 0.05` 不是简单给当前照片加 5% 像素，而是要反推出一个最终画布，让边距约等于最终画布的 5%。所以代码里会出现 `1 / (1 - 2 * margin_relative)` 这样的反推计算。

第四，毫米单位要通过 DPI 换成像素。`mm_to_px()` 的公式是：

```text
像素 = 毫米 * DPI / 25.4
```

这也是为什么 `VirtualCanvas` 会保存 `original_dpi`。如果照片没有 DPI 信息，代码使用 300 作为默认值，让毫米配置仍然能工作。

第五，圆角和阴影都是在贴照片前准备好的。圆角通过一张透明 mask 实现；阴影先画在一张更大的透明图上，再用高斯模糊扩散，最后贴到照片下方。

## EXIF 和文字绘制

`metadata.py` 负责把照片里的 EXIF 读出来。Pillow 返回的 EXIF tag 通常是数字，代码用 `PIL.ExifTags.TAGS` 把数字翻译成 `DateTimeOriginal`、`FNumber`、`FocalLength` 这类字段名，再根据 `CATEGORY_MAP` 分到不同类别。

如果图片没有 EXIF，`empty_metadata()` 会返回固定结构。这样后续代码不用到处判断 `None`，只要在各个类别里找字段就可以。

`prepare_metadata_text()` 会按配置里的 `text.fields` 顺序生成文字行。字段存在时，某些字段会被 `format_special_field()` 转成更适合显示的格式。例如拍摄日期会从 `2025:09:06 12:34:56` 变成 `2025-09-06`；焦距会加上 `mm`；光圈会显示成 `f/` 格式。字段不存在时，如果 `show_field_names` 为 `false`，就显示 `Not Found`。

`text.py` 负责真正绘制文字。`TextStylePreset.get_font_size_px()` 会优先使用相对字号；如果没有相对字号，再用毫米字号换算像素。字体加载失败时，代码会回退到 Pillow 默认字体，避免整个处理流程因为字体问题直接崩掉。不过在 CLI 正常入口中，`validation.py` 会提前检查字体文件是否存在。

文字位置由 `position_preset` 控制，例如 `center bottom`。`calculate_text_positions()` 会先计算文字块宽高，再根据水平位置、垂直位置和 `margin_percent` 算出每一行的坐标。真正绘制时，代码会先在四个轻微偏移位置画一层浅色文字，再画主文字，这相当于一个简单描边，能提高照片上的可读性。

## 导出发生在最后

`export.py` 的 `export_image()` 做三件事：

1. 根据配置格式决定文件后缀，例如 `JPEG` 对应 `.jpeg`。
2. 确保输出目录存在。
3. 调用 Pillow 的 `image.save()` 保存图片。

如果导出 JPEG，代码会额外处理两个细节：

- JPEG 不支持 alpha 通道，所以如果图片是 `RGBA`，会先转成 `RGB`。
- 保存时写入原图 DPI，让输出图保留合理的打印尺寸信息。

这也是为什么 `export_image()` 需要接收 `canvas` 参数：它不只需要图片本身，还需要 `canvas.original_dpi`。

## validate-config 为什么单独存在

`validation.py` 的作用是在处理图片前尽早发现问题。它会检查：

- `batch.quality` 是否在 `1..100`。
- 导出格式是否支持。
- 布局模式、模糊背景模式、文字对齐和文字位置是否合法。
- 颜色数组长度和通道范围是否正确。
- 字体文件是否存在。
- 批处理输入目录是否存在。

错误会收集到一个列表里，再由 `ConfigValidationError` 一次性展示。这样用户不用修一个错误、跑一次命令、再发现下一个错误。

注意 `validate-config` 子命令默认不要求输入目录存在，除非用户显式传入 `--input`。这是为了让用户可以只检查样式配置，而不必先准备照片目录。

## 测试怎样帮助读代码

`tests/` 是另一个很适合学习的入口。它们不是只给机器看的，也能帮人确认“代码应该怎么工作”。

- `test_cli.py`：验证 CLI 参数、退出码、dry-run、verbose 和错误输出。
- `test_config.py`：验证默认配置、模板加载、配置覆盖和比例解析。
- `test_validation.py`：验证各种错误配置会被提前拦住。
- `test_pipeline.py`：验证批处理、预览、空目录和输出格式。
- `test_canvas.py`：验证画布尺寸、边距和几何计算。
- `test_text.py`：验证文字定位和绘制相关逻辑。
- `test_metadata.py`：验证 EXIF 读取、缺失 EXIF 和字段格式化。

如果你读某个函数觉得抽象，可以先搜索测试文件里有没有直接调用它。测试通常会给出更小、更具体的例子。

## 一条适合学习者的实践路线

建议按这个顺序动手：

1. 先运行帮助命令：

   ```powershell
   python -m spud_imprint --help
   ```

2. 再用 `validate-config` 检查示例配置：

   ```powershell
   python -m spud_imprint validate-config --config .\examples\config.example.toml
   ```

3. 放一张自己的照片到 `local/real-tests/input/`，运行一次 `preview` 或 `batch`。
4. 打开 `pipeline.py`，对照终端命令追踪 `run_batch()` 到 `process_batch()` 再到 `render_image()`。
5. 改一个容易观察的配置，比如 `text.position_preset` 或 `canvas.blurred_background`，再运行一次预览。
6. 去 `tests/` 找对应测试，看项目如何用小图片和临时目录验证行为。

读代码时不必一开始就记住所有配置项。先抓住主线：配置决定规则，pipeline 串起步骤，canvas 算位置，metadata 准备内容，text 画文字，export 保存结果。等这条线顺了，细节自然会慢慢接上。
