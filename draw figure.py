import matplotlib.pyplot as plt
import numpy as np


def plot_points_with_quad_division(file_path, division_indices):
    """
    读取txt文件中的点集，并将点集按照给定的分界索引分成4块，分别绘制为不同颜色

    参数:
        file_path: txt文件路径，每行包含x和y坐标，用空格或逗号分隔
        division_indices: 包含3个分界点索引的列表(从0开始)，将数据分成4部分
                         例如 [n1, n2, n3] 表示:
                         - 第1部分: 0到n1-1
                         - 第2部分: n1到n2-1
                         - 第3部分: n2到n3-1
                         - 第4部分: n3到末尾
    """
    # 读取数据（支持逗号或空格分隔）
    try:
        data = np.loadtxt(file_path, delimiter=',')  # 尝试逗号分隔
    except ValueError:
        data = np.loadtxt(file_path)  # 回退到空格分隔

    # 检查分界索引是否有效
    if len(division_indices) != 3:
        raise ValueError("需要提供3个分界点索引，将数据分成4部分")

    division_indices = sorted(division_indices)
    if any(n < 0 or n >= len(data) for n in division_indices):
        raise ValueError(f"分界点索引应在0到{len(data) - 1}之间")

    # 分离x和y坐标
    x = data[:, 0]
    y = data[:, 1]

    # 定义4种颜色（可以使用不同的颜色代码）
    # colors = ['#E4C671', '#82B1D3', '#E49A5C', '#3F77A3']  # 黄, 蓝, 绿, 红
    colors = ['#E4C671', 'black', 'black', '#E4C671']
    sizes = [10, 10, 10, 10]  # 可以调整各部分点的大小
    alphas = [0.8, 0.8, 0.8, 0.8]

    # 创建图形（调整大小）
    plt.figure(figsize=(12, 8))

    # 划分区间并绘制
    segments = [
        (0, division_indices[0]),
        (division_indices[0], division_indices[1]),
        (division_indices[1], division_indices[2]),
        (division_indices[2], len(data))
    ]

    for i, (start, end) in enumerate(segments):
        plt.scatter(x[start:end], y[start:end], color=colors[i], s=sizes[i],
                    label=f'Segment {i + 1}')

    plt.gca().set_aspect('equal')

    # 添加图例和标题
    # plt.legend(fontsize=10, loc='upper right')
    plt.title('Point Set Divided into 4 Segments', fontsize=14, pad=20)
    plt.xlabel('X coordinate', fontsize=12)
    plt.ylabel('Y coordinate', fontsize=12)

    # 自动调整布局并显示
    plt.tight_layout()
    plt.savefig('output_quad_division.png', dpi=300, bbox_inches='tight')
    plt.show()


# 示例用法
if __name__ == "__main__":
    file_path = 'ps-1.txt'  # 替换为你的txt文件路径
    division_points = [778,1637, 2375]  # 修改为合理的分界点索引（从0开始）

    plot_points_with_quad_division(file_path, division_points)