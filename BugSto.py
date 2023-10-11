import os

# 输入文件夹路径
input_folder = "VOCdevkit2/VOC2007/JPEGImages"

# 遍历输入文件夹中的所有文件
for filename in os.listdir(input_folder):
    if filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
        # 构建旧文件路径和新文件路径
        old_file_path = os.path.join(input_folder, filename)
        new_file_path = os.path.join(input_folder, os.path.splitext(filename)[0] + ".jpg")

        # 重命名文件
        os.rename(old_file_path, new_file_path)

print("批量修改后缀名完成。")
