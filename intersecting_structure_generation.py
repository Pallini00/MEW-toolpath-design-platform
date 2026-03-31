import numpy as np
import matplotlib.pyplot as plt
from math import pi, sin, cos, tan, atan, sqrt
from math import pi, sin, cos, tan, atan, atan2, sqrt

def insert_points(points, m):
    new_points = [points[0]]  # 初始化新数组，包含第一个点

    for i in range(1, len(points)):
        p1, p2 = points[i - 1], points[i]
        distance = np.linalg.norm(p2 - p1)  # 计算两个点的距离

        if distance <= m:
            # 如果距离小于等于 m，则直接将第二个点添加到新数组
            new_points.append(p2)
        else:
            # 计算需要插入的点数
            num_points = int(distance // m)
            # 计算线性插值
            for j in range(1, num_points + 1):
                new_point = p1 + (p2 - p1) * (j * m / distance)
                new_points.append(new_point)
            # 添加第二个点
            new_points.append(p2)

    return np.array(new_points)

def arc_from_pts_angle(start, end, theta, pts_number, counterclockwise):
    #找到弦的中点
    mid_pt = 0.5 * (start + end)
    #计算弦的长度
    chord_length = np.linalg.norm(end - start)
    #计算半径
    radius = 0.5 * chord_length / sin(theta / 2)
    #计算始点到终点的弦向量
    chord = end - start
    #计算弦向量的单位向量
    chord_unit = chord / chord_length
    #计算弦向量的垂直方向的单位向量ortho_unit
    #注意圆弧是否为逆时针方向会影响ortho_unit的方向
    # 如逆/顺时针，则chord_unit逆/顺旋90°得到ortho_unit
    #向量(x, y) 逆/顺时针旋转得到（y, -x) 或（-y, x）
    if counterclockwise:
        ortho_unit = np.array([-chord_unit[1], chord_unit[0]])
    #如果逆时针方向，角度增量为正，反之为负
        angle_increment = theta / pts_number
    else:
        ortho_unit = np.array([chord_unit[1], -chord_unit[0]])
        angle_increment = -theta / pts_number
    #计算弦心距
    h = sqrt(radius ** 2 - (0.5 * chord_length) ** 2)
    #圆心坐标等于弦中点坐标+弦心距向量
    center = mid_pt + h * ortho_unit
    #计算初始角
    start_angle = atan2(start[1] - center[1], start[0] - center[0])
    pts_x = np.array([])
    pts_y = np.array([])
    #通过圆心、半径及角度递变生成圆弧上的等距点列
    for i in range(pts_number):
        pt_x = center[0] + radius * cos(start_angle + i * angle_increment)
        pt_y = center[1] + radius * sin(start_angle + i * angle_increment)
        pts_x = np.append(pts_x, pt_x)
        pts_y = np.append(pts_y, pt_y)
    return np.column_stack((pts_x, pts_y))

# remove_adjacent_duplicates用于去除路径中相邻的重合点。
def remove_adjacent_duplicates(pts):
    if len(pts) == 0:
        return pts

    unique_pts = [pts[0]]

    for i in range(1, len(pts)):
        if not np.array_equal(pts[i], pts[i - 1]):
            unique_pts.append(pts[i])

    return np.array(unique_pts)


# Path_fill用于填充路径，相邻点距离<max_dis。
# points 是n行2列的数组
def Path_fill(points, max_dis: float):
    def distance(p1, p2):
        return np.sqrt(np.sum((p1 - p2) ** 2))

    def interpolate(p1, p2, num_points):
        return np.linspace(p1, p2, num_points + 2)[1:-1]

    new_points = [points[0]]

    for i in range(1, len(points)):
        p1 = points[i - 1]
        p2 = points[i]
        dist = distance(p1, p2)

        if dist > max_dis:
            num_points = int(dist / max_dis)
            new_points.extend(interpolate(p1, p2, num_points))

        new_points.append(p2)

    return np.array(new_points)


##############################################################



def ps_intersect(primary_sf: float = 1, secondary_sf: float = 1, theta: float = 0, grid_number: int = 4,
                 side_offset: float = 2, secondary: bool = True, centralized: bool = False, rotation_angle: float = 0):
    """
    ps_intersect (意为primary-secondary intersect)函数用于生成两个方向线段组成的交叉结构；
    主方向线段的间距为primary_sf，主方向与副方向线段的相邻交点的距离为secondary_sf；
    主方向与水平方向的夹角为rotation_angle，副方向与主方向垂直方向的夹角为theta，角度一律采用弧度制，side_offset为网格外部的偏移距离；
    每个方向上的网格数为grid_number。centralized决定所得图案是否归心处理，若为False，则图案起点为（0,0），若为True，则图案中心为（0,0）；
    若不需要副方向线段，则secondary设为False；
    函数输出形式为两个1维Numpy数组，pts_x = (x1, x2, x3……），pts_y = (y1, y2, y3……）。
    """
    original_pts = np.array([0, 0]).reshape(1, 2)
    # 开始打印主方向
    for i in range(int(grid_number / 2) + 1):
        x1 = 2 * i * primary_sf * tan(theta)
        y1 = 2 * i * primary_sf
        x2 = x1 + grid_number * secondary_sf + 2 * side_offset
        y2 = y1
        x3 = x2 + primary_sf * tan(theta)
        y3 = y2 + primary_sf
        x4 = x3 - grid_number * secondary_sf - 2 * side_offset
        y4 = y3
        cycle_ary = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)]).reshape(4, 2)
        original_pts = np.vstack((original_pts, cycle_ary))
    original_pts = original_pts[:-2, :]
    x0 = original_pts[-1, 0]
    y0 = original_pts[-1, 1]
    # 开始打印副方向
    if secondary:
        for j in range(int(grid_number / 2) + 1):
            x1 = x0 - side_offset * (1 - sin(theta)) - 2 * j * secondary_sf
            y1 = y0 + side_offset * cos(theta)
            y2 = - side_offset * cos(theta)
            x2 = x1 - (y1 - y2) * tan(theta)
            x3 = x2 - secondary_sf
            y3 = y2
            x4 = x1 - secondary_sf
            y4 = y1
            cycle_ary = np.array([(x1, y1), (x2, y2), (x3, y3), (x4, y4)]).reshape(4, 2)
            original_pts = np.vstack((original_pts, cycle_ary))
    original_pts = original_pts[1:-2, :]  # remove the first and last point
    original_pts_x = original_pts[:, 0]
    original_pts_y = original_pts[0:, 1]
    if centralized:
        x_center = side_offset + grid_number / 2 * primary_sf * tan(theta) + grid_number / 2 * secondary_sf
        y_center = grid_number / 2 * primary_sf
        original_pts_x = original_pts[:, 0] - x_center
        original_pts_y = original_pts[:, 1] - y_center
    original_pts_x, original_pts_y = original_pts_x * cos(rotation_angle) - original_pts_y * sin(rotation_angle), \
                                     original_pts_x * sin(rotation_angle) + original_pts_y * cos(rotation_angle)
    return original_pts_x, original_pts_y





def psdd_intersect(primary_sf: sqrt(3)/2, secondary_sf: sqrt(3)/2, theta: float =0, grid_number: int = 4,
                   side_offset: float = 2, rotation_angle: float = 0, diagonal_secondary: bool = False):
    """
    psdd_intersect意为primary-secondary-diagonal1-diagonal2交错结构；
    psdd_intersect所传参数含义与ps基本相同，但不存在centralized参数，所生成图案中心均在原点；
    diagonal_secondary决定是否存在副对角线图案。
    """
    # 调用ps_intersect生成主副方向线段
    pts_x, pts_y = ps_intersect(primary_sf=primary_sf, secondary_sf=secondary_sf,
                                side_offset=side_offset,
                                theta=theta, grid_number=grid_number,
                                centralized=True,
                                rotation_angle=rotation_angle)
    # 依据几何关系计算对角线网格的参数
    diagonal_rotation_angle = atan(primary_sf / (secondary_sf + primary_sf * tan(theta)))
    diagonal_primary_sf = primary_sf / cos(theta) * sin(pi / 2 - theta - diagonal_rotation_angle)
    diagonal_secondary_sf = 0.5 * sqrt((secondary_sf + primary_sf * tan(theta)) ** 2 + primary_sf ** 2)
    diagonal_theta = -(pi / 2 - diagonal_rotation_angle - atan(primary_sf / (secondary_sf - primary_sf * tan(theta))))
    # 调用ps_intersect生成主副对角线方向线段
    diagonal_pts_x, diagonal_pts_y = ps_intersect(primary_sf=diagonal_primary_sf,
                                                  secondary_sf=diagonal_secondary_sf,
                                                  theta=diagonal_theta, grid_number=grid_number,
                                                  side_offset=side_offset,
                                                  secondary=diagonal_secondary, centralized=True,
                                                  rotation_angle=diagonal_rotation_angle + rotation_angle)
    # 拼合主副方向与对角线方向线段
    pts_x = np.hstack((pts_x, diagonal_pts_x))
    pts_y = np.hstack((pts_y, diagonal_pts_y))
    return pts_x, pts_y


if __name__ == "__main__":
    ############################
    """（1）：若要生成60°角的菱形图案，则必须要求primary_sf：secondary_sf = sqrt(3)/2, theta为-30
    （2）：在（1）基础上，若要生成正三角形图案，则grid_number需要设为偶数，且diagonal_secondary=False
    （3）：在（1）基础上，若要生成正六边形与正三角形镶嵌图案，则grid_number需要设为奇数，且diagonal_secondary=False
    （4）：！！！grid_number为奇数时，若diagonal_secondary=True，生成错位分割图案，若diagonal_secondary=False，生成六边形与三角形镶嵌图案
    （5）：！！！grid_number为偶数时，若diagonal_secondary=True，生成完全分割图案，若diagonal_secondary=False，生成半分割，即三角形图案。
    """
    # 规定几何参数
    primary_sf = sqrt(3)
    secondary_sf = 2
    side_offset = 4
    theta = -pi / 6  # 注意theta不能是pi/2的奇数倍，包括-pi/2，否则会出错！！！
    grid_number = 12
    rotation_angle = -30/180*pi #正值为逆时针旋转，负值为顺时针旋转
    #############################
    """
    若只需要产生主副方向组成的双向图案，则调用ps_intersect函数
    若需要额外产生对角线方向（包括只有主对角线方向）的三向或四向图案，则调用 psdd_intersect函数
    """
    #
    # pts_x_single, pts_y_single = ps_intersect(primary_sf=primary_sf, secondary_sf=secondary_sf,
    #                                             side_offset=side_offset,
    #                                             theta=theta, grid_number=grid_number,
    #                                             rotation_angle=rotation_angle)
    pts_x_single, pts_y_single = psdd_intersect(primary_sf=primary_sf, secondary_sf=secondary_sf,
                                                side_offset=side_offset,
                                                theta=theta, grid_number=grid_number,
                                                diagonal_secondary=False,
                                                rotation_angle=rotation_angle)

    cycle_number = 1  # 可变
    # cycle_number 是周期数，不是层数，如只有主副方向，则层数=2*周期数，如有主副方向与主副对角线方向，则层数=4*层数
    pts_x = pts_x_single
    pts_y = pts_y_single
    for i in range(cycle_number - 1):
        pts_x = np.append(pts_x, pts_x_single)
        pts_y = np.append(pts_y, pts_y_single)
    pts = np.column_stack((pts_x, pts_y))
    pts = Path_fill(points=pts, max_dis=1)
    pts = remove_adjacent_duplicates(pts)
    plt.plot(pts[:, 0], pts[:, 1])
    plt.axis('equal')
    plt.show()
