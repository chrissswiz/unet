# Unet-PyTorch: U-Net for Biomedical Image Segmentation in PyTorch

![GitHub last commit](https://img.shields.io/github/last-commit/bubbliiiing/unet-pytorch)
![GitHub license](https://img.shields.io/github/license/bubbliiiing/unet-pytorch)
![GitHub stars](https://img.shields.io/github/stars/bubbliiiing/unet-pytorch)
![GitHub forks](https://img.shields.io/github/forks/bubbliiiing/unet-pytorch)

[English](README_EN.md)

## 目录
1. [仓库更新](#仓库更新)
2. [相关仓库](#相关仓库)
3. [性能情况](#性能情况)
4. [所需环境](#所需环境)
5. [文件下载](#文件下载)
6. [训练步骤](#训练步骤)
7. [预测步骤](#预测步骤)
8. [评估步骤](#评估步骤)
9. [参考资料](#参考资料)

## 仓库更新
**`2022年3月`**：进行了大幅度更新，支持 step 和 cos 学习率下降法，支持选择 Adam 和 SGD 优化器，支持学习率根据 batch_size 自适应调整。详情请参阅 [原仓库](https://github.com/bubbliiiing/unet-pytorch/tree/bilibili)。

**`2020年8月`**：创建仓库，支持多个 backbone，支持数据 mIOU 评估，标注数据处理，以及大量注释。

## 相关仓库
| 模型 | 仓库链接 |
| :----- | :----- |
Unet | [https://github.com/bubbliiiing/unet-pytorch](https://github.com/bubbliiiing/unet-pytorch)  
PSPnet | [https://github.com/bubbliiiing/pspnet-pytorch](https://github.com/bubbliiiing/pspnet-pytorch)
deeplabv3+ | [https://github.com/bubbliiiing/deeplabv3-plus-pytorch](https://github.com/bubbliiiing/deeplabv3-plus-pytorch)

## 性能情况 test test
**U-Net 并不适合 VOC 这类数据集，它更适合特征较少、需要浅层特征的医药数据集等。**

| 训练数据集 | 权值文件名称 | 测试数据集 | 输入图片大小 | mIOU | 
| :-----: | :-----: | :------: | :------: | :------: | 
| VOC12+SBD | [unet_vgg_voc.pth](https://github.com/bubbliiiing/unet-pytorch/releases/download/v1.0/unet_vgg_voc.pth) | VOC-Val12 | 512x512 | 58.78 | 
| VOC12+SBD | [unet_resnet_voc.pth](https://github.com/bubbliiiing/unet-pytorch/releases/download/v1.0/unet_resnet_voc.pth) | VOC-Val12 | 512x512 | 67.53 | 

## 所需环境
- torch==1.2.0
- torchvision==0.4.0   

## 文件下载
训练所需的权值文件可以从百度网盘下载。

- [百度网盘链接](https://pan.baidu.com/s/1A22fC5cPRb74gqrpq7O9-A)
- 提取码: 6n2c

VOC 拓展数据集的百度网盘如下：

- [百度网盘链接](https://pan.baidu.com/s/1vkk3lMheUm6IjTXznlg7Ng)
- 提取码: 44mk

## 训练步骤
### 一、训练 VOC 数据集
1. 将提供的 VOC 数据集放入 VOCdevkit 中（无需运行 voc_annotation.py）.
2. 运行 train.py 进行训练，默认参数已经对应 VOC 数据集所需的参数了.

### 二、训练自己的数据集
1. 使用 VOC 格式进行训练.
2. 在训练前，将标签文件放入 VOCdevkit 文件夹下的 VOC2007 文件夹下的 SegmentationClass 文件夹中.
3. 在训练前，将图片文件放入 VOCdevkit 文件夹下的 VOC2007 文件夹下的 JPEGImages 文件夹中.
4. 在训练前，利用 voc_annotation.py 文件生成相应的 txt 文件.
5. 修改 train.py 中的 num_classes 为分类个数+1.
6. 运行 train.py 即可开始训练.

### 三、训练医药数据集
1. 下载 VGG 的预训练权重到 model_data 文件夹下.
2. 按照默认参数运行 train_medical.py 即可开始训练.

## 预测步骤
### 一、使用预训练权重
#### a、VOC 预训练权重
1. 下载并解压库后，如果想要使用 VOC 训练好的权重进行预测，请从百度网盘或 release 下载权值文件，放入 model_data 文件夹，然后运行即可预测.

```python
img/street.jpg
在 predict.py 中可以进行设置，以进行 FPS 测试和视频检测.
b、医药预训练权重
下载并解压库后，如果想要使用医药数据集训练好的权重进行预测，请从百度网盘或 release 下载权值文件，放入 model_data 文件夹，并修改 unet.py 中的 model_path 和 num_classes.
python
Copy code
# 默认参数
_defaults = {
    "model_path": 'model_data/unet_vgg_medical.pth',
    "num_classes": 2,
    "backbone": "vgg",
    "input_shape": [512, 512],
    "blend": True,
    "cuda": True,
}
运行即可开始预测.
python
Copy code
img/cell.png
二、使用自己训练的权重
按照训练步骤进行训练.
在 unet.py 文件中，根据训练好的文件修改 model_path、backbone 和 num_classes，以使其与训练好的权重文件相对应.
python
Copy code
# 默认参数
_defaults = {
    "model_path": 'model_data/unet_vgg_voc.pth',
    "num_classes": 21,
    "backbone": "vgg",
    "input_shape": [512, 512],
    "blend": True,
    "cuda": True,
}
运行 predict.py，然后输入：
python
Copy code
img/street.jpg
在 predict.py 中可以进行设置，以进行 FPS 测试和视频检测.
评估步骤
在 get_miou.py 中设置 num_classes 为预测的类别数加 1.
在 get_miou.py 中设置 name_classes 为需要区分的类别.
运行 get_miou.py 即可获得 mIOU 值.
参考资料
https://github.com/ggyyzm/pytorch_segmentation
https://github.com/bonlime/keras-deeplab-v3-plus
