import argparse
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.image_processor import ImageProcessor
from src.graph_builder import GraphBuilder
from src.eulerian_logic import EulerianPathFinder
from src.path_generator import PathGenerator


def process_file(file_path, max_size=1024):
    print(f"Processing file: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    # 1. Processing
    print("Step 1: Image Processing & Skeletonization...")
    processor = ImageProcessor(image_path=file_path, max_dimension=max_size)
    processor.preprocess()
    skeleton = processor.get_skeleton()

    # 2. Graph Building
    print("Step 2: Building Graph from Skeleton...")
    builder = GraphBuilder(skeleton)
    builder.build_graph()
    # Apply refinements
    if hasattr(builder, 'merge_close_nodes'):
        builder.merge_close_nodes(distance_threshold=5.0)
    builder.prune_graph(min_path_length=10)
    G = builder.graph

    print(f"    Raw Graph Nodes: {len(G.nodes())}")
    print(f"    Raw Graph Edges: {len(G.edges())}")

    # 3. Eulerian Logic
    print("Step 3: Analyzing Connectivity...")
    euler = EulerianPathFinder(G)
    status = euler.analyze()
    odd_count, _ = euler.count_odd_nodes()
    print(f"    Topology Status: {status.upper()} (Odd Nodes: {odd_count})")

    G_final = euler.make_eulerian(force_double_wall=False)
    print(f"    Target Graph Edges: {len(G_final.edges())}")

    # 4. Path Generation
    print("Step 4: Generating Continuous Path...")
    generator = PathGenerator(G_final)
    try:
        path = generator.generate_path()
        print(f"    Success! Path generated with {len(path)} pixels.")

        # ---------- 新增：保存路径点集为 txt 文件 ----------
        height, width = skeleton.shape
        txt_filename = os.path.splitext(file_path)[0] + "_path.txt"
        with open(txt_filename, 'w') as f:
            for point in path:
                # point 是 (y, x) 格式，这里转换为 (x, y) 写入，可根据需要调整
                x = point[1]  # 直接取列坐标
                y = point[0]  # 直接取行坐标
                f.write(f"{x} {y}\n")
        print(f"    Path points saved to {txt_filename}")

    except Exception as e:
        print(f"    Error generating path: {e}")
        return

    # 5. Visualization (Static Plot)
    print("Step 5: Saving Visualization...")
    plt.figure(figsize=(10, 10))
    plt.imshow(skeleton, cmap='gray')

    path_arr = np.array(path)
    # Color mapping for path progress (Start=Blue -> End=Red)
    # This helps see the stitching
    plt.scatter(path_arr[:, 1], path_arr[:, 0], c=np.arange(len(path)), cmap='plasma', s=1, alpha=0.5)

    output_filename = os.path.basename(file_path) + "_result.png"
    plt.title(f"Processed: {os.path.basename(file_path)}\nPath Length: {len(path)} px")
    plt.savefig(output_filename)
    print(f"    Visualization saved to {output_filename}")

    # Optional: Save numpy path
    # np.save(file_path + ".npy", path_arr)


def scale_path_points(input_txt, output_txt, scale_factor):
    """
    读取包含点坐标的 txt 文件（每行格式：x y），将坐标乘以缩放因子，
    并保存到新文件。
    """
    if not os.path.exists(input_txt):
        print(f"错误：文件 {input_txt} 不存在")
        return

    with open(input_txt, 'r') as f_in:
        lines = f_in.readlines()

    scaled_points = []
    for line in lines:
        line = line.strip()
        if not line:  # 跳过空行
            continue
        cleaned = line.strip('()').strip()
        parts = cleaned.split()
        if len(parts) != 2:
            print(f"警告：跳过无效行：{line}")
            continue
        try:
            x = float(parts[0])
            y = float(parts[1])
            scaled_points.append((x * scale_factor, y * scale_factor))
        except ValueError:
            print(f"警告：无法转换坐标的行：{line}")
            continue

    with open(output_txt, 'w') as f_out:
        for x, y in scaled_points:
            f_out.write(f"{x:.4f} {y:.4f}\n")

    print(f"缩放完成，共处理 {len(scaled_points)} 个点。")
    print(f"结果已保存至：{output_txt}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an image into a continuous Eulerian path.")
    parser.add_argument("input_file", help="Path to the input image file (png, jpg, etc.)")
    parser.add_argument("--max_size", type=int, default=1024, help="Max dimension for image resizing (default: 1024)")
    parser.add_argument("--scale", type=float, default=None, help="Optional scaling factor for output points")
    args = parser.parse_args()

    # 调用主处理函数
    process_file(args.input_file, args.max_size)

    # 如果提供了缩放因子，则对生成的路径点进行缩放
    if args.scale is not None:
        base = os.path.splitext(args.input_file)[0]
        input_txt = base + "_path.txt"
        output_txt = base + "_scaled.txt"
        scale_path_points(input_txt, output_txt, args.scale)


    #单独调试使用
    # parser = argparse.ArgumentParser(...)
    # parser.add_argument("--max_size", type=int, default=1024)
    # args = parser.parse_args()
    # process_file("ice_cream.png", args.max_size)  # 直接传入固定文件名
    # # 示例：缩放 dragon_path.txt，因子为 2.0，保存为 new_path.txt
    # scale_path_points("ice_cream_path.txt", "new_path.txt", scale_factor=1)

