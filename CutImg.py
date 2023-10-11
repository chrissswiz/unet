from PIL import Image
import os

# 输入文件夹和输出文件夹
input_folder = "VOCdevkit/VOC2007/SegmentationClass"
output_folder = "VOCdevkit2/VOC2007/SegmentationClass"

# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 定义切分参数
rows = 3
cols = 3

# 遍历输入文件夹中的所有图片
for filename in os.listdir(input_folder):
    if filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
        # 打开图像
        image_path = os.path.join(input_folder, filename)
        img = Image.open(image_path)

        # 获取图像的宽度和高度
        width, height = img.size

        # 计算每个切分图像的宽度和高度
        tile_width = width // cols
        tile_height = height // rows

        for i in range(rows):
            for j in range(cols):
                # 计算切分图像的坐标
                left = j * tile_width
                upper = i * tile_height
                right = (j + 1) * tile_width
                lower = (i + 1) * tile_height

                # 切分图像并保存到输出文件夹
                tile = img.crop((left, upper, right, lower))
                output_filename = f"{os.path.splitext(filename)[0]}_tile_{i}_{j}.png"
                output_path = os.path.join(output_folder, output_filename)
                tile.save(output_path)

# 完成后关闭图像
img.close()
