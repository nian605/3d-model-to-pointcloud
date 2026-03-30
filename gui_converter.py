"""
这是一个使用 Tkinter 构建的简单 GUI 界面，用于将 3D 模型转换为点云数据。
支持选择输入/输出文件夹、设置点间距，并实时查看处理进度。
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import trimesh
import numpy as np


class PointCloudConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("3D模型转点云工具")
        self.root.geometry("700x450")

        # 初始化变量
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.target_distance = tk.DoubleVar(value=0.1)
        self.current_model_file = None

        # 创建界面元素
        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 模型文件选择
        ttk.Label(main_frame, text="选择模型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="选择模型文件", command=self.browse_model).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.model_label = ttk.Label(main_frame, text="未选择", foreground="gray")
        self.model_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # 点间距设置
        ttk.Label(main_frame, text="目标点间距:").grid(row=1, column=0, sticky=tk.W, pady=5)
        distance_spinbox = ttk.Spinbox(main_frame, from_=0.01, to=10.0, increment=0.01,
                                       textvariable=self.target_distance, width=10)
        distance_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # 开始转换按钮
        self.start_button = ttk.Button(main_frame, text="开始转换", command=self.start_conversion)
        self.start_button.grid(row=2, column=0, columnspan=3, pady=20)

        # 进度条
        ttk.Label(main_frame, text="处理进度:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=500, mode="determinate")
        self.progress.grid(row=3, column=1, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        self.progress_label = ttk.Label(main_frame, text="0%")
        self.progress_label.grid(row=4, column=1, sticky=tk.W, padx=5)

        # 日志文本框
        ttk.Label(main_frame, text="处理日志:").grid(row=5, column=0, sticky=(tk.W, tk.N))
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=15)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def browse_model(self):
        filetypes = [
            ("3D模型文件", "*.obj *.stl *.ply *.glb *.gltf *.off *.dae"),
            ("所有文件", "*.*")
        ]
        input_dir = os.path.join(self.script_dir, "input")
        file = filedialog.askopenfilename(title="选择模型文件", initialdir=input_dir, filetypes=filetypes)
        if file:
            self.current_model_file = file
            self.model_label.config(text=os.path.basename(file), foreground="black")

    def start_conversion(self):
        if not self.current_model_file:
            messagebox.showwarning("警告", "请先选择一个模型文件")
            return

        # 禁用按钮，防止重复点击
        self.start_button.config(state=tk.DISABLED)
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_log("开始转换...\n")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")

        # 在新线程中执行转换，防止界面冻结
        thread = threading.Thread(target=self.run_conversion)
        thread.daemon = True
        thread.start()

    def run_conversion(self):
        model_path = self.current_model_file
        output_folder = os.path.join(self.script_dir, "output")
        target_distance = self.target_distance.get()

        try:
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder, exist_ok=True)
                self.update_log(f"已创建输出文件夹: {output_folder}\n")

            self.update_log(f"正在处理: {os.path.basename(model_path)}\n")
            self.update_log(f"输出文件夹: {output_folder}\n")

            # 转换模型为点云
            point_cloud_data = self.convert_single_model(model_path, target_distance)

            if point_cloud_data is not None:
                # 生成输出文件路径
                base_name = os.path.splitext(os.path.basename(model_path))[0]
                output_file_path = os.path.join(output_folder, f"{base_name}_pointcloud.txt")

                # 保存点云
                self.save_pointcloud_as_txt(point_cloud_data, output_file_path)

                self.update_log(f"已保存至: {output_file_path}\n")
                self.update_log(f"\n转换完成！可以继续选择下一个模型。\n")
            else:
                self.update_log(f"处理失败: {os.path.basename(model_path)}\n")

        except Exception as e:
            self.update_log(f"处理过程中发生错误: {str(e)}\n")

        finally:
            # 重置模型选择，保留文件夹路径
            self.current_model_file = None
            self.model_label.config(text="未选择", foreground="gray")
            self.enable_button()

    def convert_single_model(self, model_path, target_distance):
        """将单个3D模型转换为点云"""
        try:
            self.update_log(f"正在加载模型...\n")
            mesh = trimesh.load(model_path)

            if not isinstance(mesh, trimesh.Trimesh):
                raise ValueError(f"加载的对象不是一个有效的网格。")

            # 初始采样大量点
            initial_sample_count = min(500000, int(mesh.area / (target_distance * target_distance) * 10))
            self.update_log(f"正在从模型表面初步采样 {initial_sample_count} 个点...\n")
            initial_points = mesh.sample(count=initial_sample_count)

            if initial_points is None or len(initial_points) == 0:
                raise ValueError("未能从模型中采样到任何点，请检查模型是否有效。")

            total_points = len(initial_points)
            self.update_log(f"初步采样完成，共 {total_points} 个点。开始按距离过滤...\n")

            # 设置进度条最大值
            self.progress['maximum'] = 100
            self.progress['value'] = 0

            # 使用泊松盘采样算法的思想进行点过滤
            selected_points = []
            remaining_points = initial_points.copy()

            iteration = 0
            while len(remaining_points) > 0:
                iteration += 1

                # 选取第一个剩余点作为新点
                new_point = remaining_points[0]
                selected_points.append(new_point)

                # 计算所有剩余点到新点的距离
                distances = np.linalg.norm(remaining_points - new_point, axis=1)

                # 移除距离小于目标距离的点
                mask = distances >= target_distance
                remaining_points = remaining_points[mask]

                # 更新进度条
                if iteration % 100 == 0:
                    processed = total_points - len(remaining_points)
                    progress_percent = int((processed / total_points) * 100)
                    self.progress['value'] = progress_percent
                    self.progress_label.config(text=f"{progress_percent}%")
                    self.update_log(f"已处理 {processed}/{total_points} 个点，已选中 {len(selected_points)} 个点\n")
                    self.root.update_idletasks()

                if len(remaining_points) == 0:
                    break

            selected_points = np.array(selected_points)
            self.progress['value'] = 100
            self.progress_label.config(text="100%")
            self.update_log(f"按距离 {target_distance} 采样完成，共生成 {len(selected_points)} 个点。\n")

            return selected_points

        except FileNotFoundError:
            self.update_log(f"错误：找不到模型文件 '{model_path}'。\n")
            return None
        except Exception as e:
            self.update_log(f"处理 '{model_path}' 时发生错误: {e}\n")
            return None

    def save_pointcloud_as_txt(self, points, file_path):
        """将点云保存为 TXT 文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w') as f:
                for point in points:
                    f.write(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f}\n")
            print(f"点云已保存至: {file_path}")
        except Exception as e:
            self.update_log(f"保存文件 '{file_path}' 时发生错误: {e}\n")

    def update_log(self, message):
        """更新日志文本框"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)  # 自动滚动到底部
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()  # 强制更新界面

    def enable_button(self):
        """启用开始按钮"""
        self.start_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = PointCloudConverterApp(root)
    root.mainloop()