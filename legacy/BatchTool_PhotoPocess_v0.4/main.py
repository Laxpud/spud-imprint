import os
from PIL import Image
from virtual_canvas import VirtualCanvas
from text_style import TextStylePreset
from metadata_utils import get_categorized_metadata, prepare_metadata_text
from text_placement import add_text_to_canvas
from image_export import export_image

def main():
    """主函数，执行完整的水印添加流程，现在支持处理多个图像"""
    # 定义输入和输出文件夹路径
    input_dir = "input"  # 输入文件夹，包含所有要处理的图像
    output_dir = "output"  # 输出文件夹，用于保存处理后的图像

    # 确保输出文件夹存在，如果不存在则创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取所有图像文件：列出 input 文件夹中的文件，并过滤出常见图像格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']  # 支持的图像扩展名列表
    image_files = []
    for f in os.listdir(input_dir):
        file_path = os.path.join(input_dir, f)
        if os.path.isfile(file_path) and os.path.splitext(f)[1].lower() in image_extensions:
            image_files.append(f)  # 只添加符合条件的图像文件

    # 固定参数：这些参数对所有图像相同，因此定义在循环外以提高效率
    fields_to_draw = ["DateTimeOriginal"]  # 要显示的元数据字段列表
    custom_style = TextStylePreset(
        font_size_relative=0.05,  # 字体大小相对画布的比例
        text_color=(255, 255, 255),  # 文本颜色（白色）
        font_name="NotoSerifSC-VF.ttf",  # 字体文件名称
        background_color=(220, 220, 220, 128),  # 文本背景颜色（浅灰色，半透明）
        alignment="left",  # 文本对齐方式
        show_field_names=False  # 是否显示字段名称（这里只显示值）
    )

    # 循环处理每个图像文件
    for image_file in image_files:
        # 构建完整的图像路径
        image_path = os.path.join(input_dir, image_file)
        try:
            # 1. 读取原始图像：使用 PIL 的 Image.open 打开图像文件
            img = Image.open(image_path)
            
            # 2. 创建虚拟画布：基于原始图像和固定参数初始化画布
            canvas = VirtualCanvas(
                original_image=img,
                layout_mode="fit",  # 布局模式：适应画布
                bg_color=(240, 240, 240),  # 画布背景颜色（浅灰色）
                canvas_aspect_ratio=16/9,  # 画布宽高比（16:9）
                margin_relative=0.05,  # 边距相对比例
                corner_radius_relative=0.02,  # 圆角相对比例
                shadow_enabled=True,  # 启用阴影
                shadow_offset_relative=(0.005, 0.005),  # 阴影偏移相对比例
                shadow_blur_relative=0.01,  # 阴影模糊相对比例
                shadow_color=(0, 0, 0, 64)  # 阴影颜色（黑色，半透明）
            )
            
            # 3. 创建画布并添加照片：先创建空画布，然后将模糊背景和照片添加到画布上
            canvas_image = canvas.create_canvas()  # 创建基础画布
            canvas_image = canvas.add_blurred_background(
                canvas_image,
                blur_radius=100,
                extra_scale=1.5,
                fit_mode="cover"
            )
            canvas_image = canvas.add_photo_to_canvas(canvas_image)  # 添加照片到画布
            
            # 4. 获取元数据：从图像文件中提取分类的元数据（如拍摄时间）
            metadata = get_categorized_metadata(image_path)
            
            # 5. 和6. 使用固定的 fields_to_draw 和 custom_style（已定义在循环外）
            
            # 7. 添加文本到画布：将元数据文本添加到画布的指定位置
            result_image = add_text_to_canvas(
                canvas_image,
                canvas,
                metadata,
                fields_to_draw,
                text_style=custom_style,
                position_preset="center bottom",  # 文本位置：画布中心
                margin_percent=0.05  # 文本边距百分比
            )
            
            # 8. 导出图像：构建输出文件名和路径，并保存图像
            base_name = os.path.splitext(image_file)[0]  # 获取文件名（不含扩展名）
            output_filename = f"{base_name}_uniform_watermark.jpg"  # 添加后缀
            output_path = os.path.join(output_dir, output_filename)  # 完整输出路径
            export_image(result_image, output_path, canvas, format="JPEG", quality=100)  # 导出为JPEG，质量100%
            
            print(f"处理完成：{image_file} -> {output_filename}")  # 打印处理进度
        except Exception as e:
            # 错误处理：如果处理某个图像时出错，打印错误信息并继续处理其他图像
            print(f"处理图像 {image_file} 时出错：{e}")

    print("所有处理完成！已保持原始照片分辨率。")  # 最终完成消息

if __name__ == '__main__':
    main()