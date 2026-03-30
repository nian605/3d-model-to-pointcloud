# 3D模型转点云工具

一个用于将3D模型批量转换为点云数据的Python工具，支持命令行和图形界面两种使用方式。

## 功能特点

- 支持多种3D模型格式：OBJ, STL, PLY, GLB, GLTF, OFF, DAE
- 基于泊松盘采样算法，按指定点间距进行采样
- 批量处理多个模型文件
- 提供友好的GUI界面，实时显示处理进度
- 输出TXT格式点云文件（X Y Z坐标）

## 环境要求

- Python 3.9+
- trimesh
- numpy
- tkinter（GUI界面需要）

## 安装

### 使用 Conda（推荐）

```bash
# 创建虚拟环境
conda create -n pointcloudconvert_env python=3.9 trimesh numpy scikit-learn -c conda-forge

# 激活环境
conda activate pointcloudconvert_env
```

### 使用 pip

```bash
pip install trimesh numpy
```

## 使用方法

### 方式一：图形界面（GUI）

运行图形界面程序：

```bash
python gui_converter.py
```

操作步骤：
1. 点击"选择模型文件"按钮，选择要转换的3D模型
2. 设置目标点间距（默认0.1）
3. 点击"开始转换"按钮
4. 查看实时处理进度和日志
5. 转换完成后，点云文件将保存到 `output` 文件夹

### 方式二：命令行

批量处理文件夹中的所有模型：

```bash
python convert_model_to_pointcloud_by_distance.py -d 1
```

参数说明：
- `-i, --input`：输入文件夹路径（默认：`./input`）
- `-o, --output`：输出文件夹路径（默认：`./output`）
- `-d, --distance`：目标点间距（默认：0.1）

示例：

```bash
# 使用默认输入输出文件夹，点间距为0.5
python convert_model_to_pointcloud_by_distance.py -d 0.5

# 指定输入输出文件夹
python convert_model_to_pointcloud_by_distance.py -i ./models -o ./results -d 0.2
```

## 项目结构

```
convert_model_to_pointcloud_by_distance/
├── convert_model_to_pointcloud_by_distance.py  # 命令行版本
├── gui_converter.py                            # GUI版本
├── PointCloudConverter.spec                    # PyInstaller打包配置
├── input/                                      # 输入文件夹（放置3D模型）
├── output/                                     # 输出文件夹（生成的点云文件）
└── README.md                                   # 说明文档
```

## 输出格式

生成的点云文件为TXT格式，每行包含一个点的X Y Z坐标，以空格分隔：

```
-1.234567 2.345678 0.123456
-1.230000 2.340000 0.120000
...
```

## 打包为可执行文件

首先安装 PyInstaller：

```bash
pip install pyinstaller
```

使用 PyInstaller 将GUI版本打包为独立可执行文件：

```bash
pyinstaller PointCloudConverter.spec
```

生成的可执行文件位于 `dist` 文件夹中。

## 算法说明

本工具使用改进的泊松盘采样算法：

1. 首先从3D模型表面均匀采样大量初始点
2. 使用距离过滤算法，确保任意两点之间的距离不小于目标点间距
3. 迭代处理直到所有剩余点都被处理完毕

这种方法能够生成分布均匀、密度可控的点云数据。

## 许可证

本项目为开源项目，可自由使用和修改。
