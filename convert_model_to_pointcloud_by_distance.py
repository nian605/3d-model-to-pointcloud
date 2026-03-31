# -*- coding: utf-8 -*-
"""
这是一个 Python 脚本，用于将指定文件夹中的 3D 模型批量转换为点云数据，
按指定点间距采样，输出为TXT格式，并保存到指定输出文件夹。
"""

import trimesh
import numpy as np
import os
import argparse
import glob


def convert_model_to_pointcloud_by_distance(model_path, target_distance=0.1, max_iterations=100000):
    """
    将 3D 模型转换为点云，通过目标点间距进行采样。

    Args:
        model_path (str): 输入的 3D 模型文件路径。
        target_distance (float): 目标点间距。
        max_iterations (int): 最大迭代次数，防止无限循环。

    Returns:
        numpy.ndarray: 包含点云坐标的 N x 3 数组。
    """
    try:
        print(f"正在加载模型: {model_path}")
        mesh = trimesh.load(model_path)

        if not isinstance(mesh, trimesh.Trimesh):
            raise ValueError(f"加载的对象不是一个有效的网格。")

        # 初始采样（降低倍数以减少内存占用）
        initial_sample_count = min(200000, int(mesh.area / (target_distance * target_distance) * 3))
        print(f"正在从模型表面初步采样 {initial_sample_count} 个点...")
        initial_points = mesh.sample(count=initial_sample_count)

        if initial_points is None or len(initial_points) == 0:
            raise ValueError("未能从模型中采样到任何点，请检查模型是否有效。")

        print(f"初步采样完成，共 {len(initial_points)} 个点。开始按距离过滤...")

        # 优化内存：预分配结果数组，避免数组复制
        mask = np.ones(len(initial_points), dtype=bool)
        max_result = min(len(initial_points), max_iterations)
        selected_points = np.empty((max_result, 3), dtype=np.float64)
        count = 0

        iteration = 0
        while np.any(mask) and count < max_result:
            iteration += 1
            if iteration % 1000 == 0:
                print(f"正在进行第 {iteration} 次迭代，已选中 {count} 个点...")

            # 找到第一个未被选中的点
            idx = np.where(mask)[0][0]
            selected_points[count] = initial_points[idx]
            count += 1

            # 直接计算距离，避免复制数组
            distances = np.linalg.norm(initial_points[mask] - initial_points[idx], axis=1)

            # 更新掩码
            valid_indices = np.where(mask)[0]
            mask[valid_indices[distances < target_distance]] = False

        selected_points = selected_points[:count]
        print(f"按距离 {target_distance} 采样完成，共生成 {len(selected_points)} 个点。")

        return selected_points

    except FileNotFoundError:
        print(f"错误：找不到模型文件 '{model_path}'。")
        return None
    except Exception as e:
        print(f"处理 '{model_path}' 时发生错误: {e}")
        return None


def save_pointcloud_as_txt(points, file_path):
    """
    将点云保存为 TXT 文件，每行包含 X Y Z 坐标。

    Args:
        points (numpy.ndarray): N x 3 的点云数组。
        file_path (str): 输出文件路径。
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as f:
            for point in points:
                f.write(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f}\n")
        print(f"点云已保存至: {file_path}")
    except Exception as e:
        print(f"保存文件 '{file_path}' 时发生错误: {e}")


def batch_process_models(input_folder, output_folder, target_distance=0.1):
    """
    批量处理文件夹中的模型文件。

    Args:
        input_folder (str): 输入文件夹路径。
        output_folder (str): 输出文件夹路径。
        target_distance (float): 目标点间距。
    """
    # 支持的模型格式
    supported_formats = ['*.obj', '*.stl', '*.ply', '*.glb', '*.gltf', '*.off', '*.dae']

    # 获取所有支持的模型文件
    model_files = []
    for fmt in supported_formats:
        model_files.extend(glob.glob(os.path.join(input_folder, fmt)))
        model_files.extend(glob.glob(os.path.join(input_folder, fmt.upper())))  # 也检查大写扩展名

    if not model_files:
        print(f"在 '{input_folder}' 中未找到支持的模型文件。")
        return

    print(f"找到 {len(model_files)} 个模型文件，开始批量处理...")

    for i, model_path in enumerate(model_files):
        print(f"\n[{i + 1}/{len(model_files)}] 正在处理: {os.path.basename(model_path)}")

        # 转换模型为点云
        point_cloud_data = convert_model_to_pointcloud_by_distance(
            model_path=model_path,
            target_distance=target_distance
        )

        if point_cloud_data is not None:
            # 生成输出文件路径
            base_name = os.path.splitext(os.path.basename(model_path))[0]
            output_file_path = os.path.join(output_folder, f"{base_name}_pointcloud.txt")

            # 保存点云
            save_pointcloud_as_txt(point_cloud_data, output_file_path)

            print(f"已处理完毕: {os.path.basename(model_path)} -> {os.path.basename(output_file_path)}")
        else:
            print(f"处理失败: {os.path.basename(model_path)}")


if __name__ == "__main__":
    # 设置默认路径（相对于脚本所在目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_input_folder = os.path.join(script_dir, "input")
    default_output_folder = os.path.join(script_dir, "output")

    parser = argparse.ArgumentParser(description='批量将 3D 模型转换为点云（按距离采样）')
    parser.add_argument('-i', '--input', type=str, default=default_input_folder,
                        help=f'输入文件夹路径 (默认: {default_input_folder})')
    parser.add_argument('-o', '--output', type=str, default=default_output_folder,
                        help=f'输出文件夹路径 (默认: {default_output_folder})')
    parser.add_argument('-d', '--distance', type=float, default=0.1, help='目标点间距 (默认 0.1)')

    args = parser.parse_args()

    # 创建输出文件夹（如果不存在）
    os.makedirs(args.output, exist_ok=True)

    print(f"输入文件夹: {args.input}")
    print(f"输出文件夹: {args.output}")
    print(f"目标点间距: {args.distance}")

    # 执行批量处理
    batch_process_models(args.input, args.output, args.distance)

    print("\n批量处理完成！")