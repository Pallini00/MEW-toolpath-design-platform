import matplotlib.pyplot as plt
import numpy as np
from math import sin, cos, tan, pi, sqrt
from intersecting_structure_generation import Path_fill, remove_adjacent_duplicates

def arc(center_x:float, center_y:float, radius:float, start_angle:float, stop_angle:float, max_dis:float):
    """
    arc用于生成弧长点列，圆心坐标为（center_x, center_y），半径为radius，起始角度与终止角度为start_angle和stop_angle；
    start_angle与stop_angle无固定大小关系，点列由start_angle开始向stop_angle排列。
    函数输出形式为两个1维Numpy数组，pts_x = (x1, x2, x3……），pts_y = (y1, y2, y3……）
    """
    pts_x = np.array([])
    pts_y = np.array([])
    pts_number = int(abs(radius * (stop_angle - start_angle) / max_dis))
    angle_increment = (stop_angle - start_angle) / pts_number
    for i in range(pts_number):
        pt_x = center_x + radius * cos(start_angle + i * angle_increment)
        pt_y = center_y + radius * sin(start_angle + i * angle_increment)
        pts_x = np.append(pts_x, pt_x)
        pts_y = np.append(pts_y, pt_y)
    return pts_x, pts_y


if __name__ == "__main__":
    side_offset = 2
    radius = 3
    grid_number = 20
    # grid_number决定一行或一列的格子数
    # !!! grid_number为偶数时，可生成圆形图案；为奇数时，可生成弯曲方形图案。
    max_dis = 0.01
    pts_x_single = np.array([0])
    pts_y_single = np.array([0])
    #########################
    # 开始生成x方向的点列
    for i in range(int(grid_number / 2)):
        for j in range(grid_number):
            center_x = side_offset + (0.5 + j) * radius * sqrt(2)
            center_y = (-1) ** (j + 1) * radius * sqrt(2) / 2 + i * 2 * radius * sqrt(2)
            start_angle = 3 / 4 * pi * (-1) ** j
            stop_angle = 1 / 4 * pi * (-1) ** j
            pts_quarter_circle_x, pts_quarter_circle_y = arc(center_x, center_y, radius, start_angle,
                                                             stop_angle, max_dis)
            pts_x_single = np.hstack((pts_x_single, pts_quarter_circle_x))
            pts_y_single = np.hstack((pts_y_single, pts_quarter_circle_y))
        ##########################
        x1, y1 = pts_x_single[-1] + side_offset, pts_y_single[-1]
        x2, y2 = x1, y1 + sqrt(2) * radius
        pts_x_single = np.hstack((pts_x_single, np.array([x1, x2])))
        pts_y_single = np.hstack((pts_y_single, np.array([y1, y2])))
        ##########################
        for j in range(grid_number):
            center_x = x2 - side_offset - (0.5 + j) * radius * sqrt(2)
            center_y = y2 + (-1) ** (j + 1) * radius * sqrt(2) / 2
            start_angle = 1 / 4 * pi * (-1) ** j
            stop_angle = 3 / 4 * pi * (-1) ** j
            pts_quarter_circle_x, pts_quarter_circle_y = arc(center_x, center_y, radius, start_angle,
                                                             stop_angle, max_dis)
            pts_x_single = np.hstack((pts_x_single, pts_quarter_circle_x))
            pts_y_single = np.hstack((pts_y_single, pts_quarter_circle_y))
        ##########################
        x1, y1 = pts_x_single[-1] - side_offset, pts_y_single[-1]
        x2, y2 = x1, y1 + sqrt(2) * radius
        pts_x_single = np.hstack((pts_x_single, np.array([x1, x2])))
        pts_y_single = np.hstack((pts_y_single, np.array([y1, y2])))
    ######################
    # 开始生成y方向的点列
    for i in range(int(grid_number / 2)):
        for j in range(grid_number + 2):
            center_x = side_offset + 2 * i * radius * sqrt(2) + (-1) ** (j + 1) * 0.5 * sqrt(2) * radius
            center_y = grid_number * sqrt(2) * radius + (0.5 - j) * sqrt(2) * radius
            start_angle = (1.5 + 0.5 * (-1) ** j) * pi + (-1) ** j * pi / 4
            stop_angle = (1.5 + 0.5 * (-1) ** j) * pi - (-1) ** j * pi / 4
            pts_quarter_circle_x, pts_quarter_circle_y = arc(center_x, center_y, radius, start_angle,
                                                             stop_angle, max_dis)
            pts_x_single = np.hstack((pts_x_single, pts_quarter_circle_x))
            pts_y_single = np.hstack((pts_y_single, pts_quarter_circle_y))
        ##########################
        x1, y1 = pts_x_single[-1], pts_y_single[-1] - side_offset
        x2, y2 = x1 + sqrt(2) * radius, y1
        pts_x_single = np.hstack((pts_x_single, np.array([x1, x2])))
        pts_y_single = np.hstack((pts_y_single, np.array([y1, y2])))
        ##########################
        for j in range(grid_number + 2):
            center_x = side_offset + (2 * i + 1) * radius * sqrt(2) + (-1) ** (j + 1) * 0.5 * sqrt(2) * radius
            center_y = (j - 0.5) * sqrt(2) * radius
            stop_angle = (1.5 + 0.5 * (-1) ** j) * pi + (-1) ** j * pi / 4
            start_angle = (1.5 + 0.5 * (-1) ** j) * pi - (-1) ** j * pi / 4
            pts_quarter_circle_x, pts_quarter_circle_y = arc(center_x, center_y, radius, start_angle,
                                                             stop_angle, max_dis)
            pts_x_single = np.hstack((pts_x_single, pts_quarter_circle_x))
            pts_y_single = np.hstack((pts_y_single, pts_quarter_circle_y))
    x1, y1 = pts_x_single[-1], pts_y_single[-1] + side_offset
    x2, y2 = -side_offset, y1
    x3, y3 = x2, 0
    pts_x_single = np.hstack((pts_x_single, np.array([x1, x2, x3])))
    pts_y_single = np.hstack((pts_y_single, np.array([y1, y2, y3])))
    ##########################################################
    cycle_number = 2  # variable
    pts_x = pts_x_single
    pts_y = pts_y_single
    for i in range(cycle_number - 1):
        pts_x = np.append(pts_x,  pts_x_single)
        pts_y = np.append(pts_y, pts_y_single)
    pts = np.column_stack((pts_x, pts_y))
    pts = Path_fill(points=pts, max_dis=0.5)
    pts = remove_adjacent_duplicates(pts)
    plt.plot(pts[:, 0], pts[:, 1])
    plt.axis('equal')
    plt.show()
