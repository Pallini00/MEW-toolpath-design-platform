import numpy as np
import matplotlib.pyplot as plt
from intersecting_structure_generation import ps_intersect, Path_fill
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import os
import math
from math import pi
from matplotlib.path import Path

def linear(t):
    return t
def sin(t):
    return np.sin(pi/2*t)
def cos(t):
    return 1-np.cos(pi/2*t)
def tan(t):
    return np.tan(pi/4*t)
def polynomial(t):
    return t**2*(4-2*t)/2

TRANSITION_FUNCTIONS = {
    'linear': linear,
    'sin': sin,
    'cos': cos,
    'tan': tan,
    'polynomial': polynomial
}


def generate_alpha_rect(pts_x, pts_y,
                        left_upper_x, left_upper_y,
                        right_lower_x, right_lower_y, extend=0.1, transition_types=None,
                        shape_type="rectangle", shape_params=None):
    """
    生成 alpha_rect：根据选框形状生成过渡区

    参数:
    - pts_x, pts_y: 一维数组，笛卡尔坐标点
    - left_upper_x, left_upper_y: 选框左上角坐标
    - right_lower_x, right_lower_y: 选框右下角坐标
    - extend: 过渡区扩展比例
    - transition_types: 过渡函数类型
    - shape_type: 选框形状类型 ("rectangle", "ellipse", "hexagon", "custom")
    - shape_params: 形状特定参数（如自定义多边形的顶点）
    """
    if transition_types is None:
        transition_types = {
            'left': 'linear',
            'right': 'linear',
            'top': 'linear',
            'bottom': 'linear'
        }

    # 计算选框中心点（重心）
    cx = (left_upper_x + right_lower_x) / 2
    cy = (left_upper_y + right_lower_y) / 2

    # 根据形状类型生成不同的过渡区
    if shape_type == "rectangle":
        return generate_rectangle_alpha(pts_x, pts_y, left_upper_x, left_upper_y,
                                        right_lower_x, right_lower_y, extend, transition_types, cx, cy)
    elif shape_type == "ellipse":
        return generate_ellipse_alpha(pts_x, pts_y, left_upper_x, left_upper_y,
                                      right_lower_x, right_lower_y, extend, transition_types, cx, cy)
    elif shape_type == "hexagon":
        return generate_hexagon_alpha(pts_x, pts_y, left_upper_x, left_upper_y,
                                      right_lower_x, right_lower_y, extend, transition_types, cx, cy)
    elif shape_type == "custom" and shape_params is not None:
        return generate_custom_polygon_alpha(pts_x, pts_y, shape_params, extend, transition_types, cx, cy)
    else:
        # 默认使用矩形过渡区
        return generate_rectangle_alpha(pts_x, pts_y, left_upper_x, left_upper_y,
                                        right_lower_x, right_lower_y, extend, transition_types, cx, cy)


def generate_rectangle_alpha(pts_x, pts_y, x1, y1, x2, y2, extend, transition_types, cx, cy):
    """矩形选框的过渡区生成"""
    # 确保正确顺序
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])

    # 矩形宽高
    width = x2 - x1
    height = y2 - y1
    rx = width / 2
    ry = height / 2

    # 外部扩展边界（扩展宽度为半轴长乘以extend）
    ext_x = rx * extend
    ext_y = ry * extend
    x1_ext = x1 - ext_x
    x2_ext = x2 + ext_x
    y1_ext = y1 - ext_y
    y2_ext = y2 + ext_y

    alpha = np.zeros_like(pts_x)

    # 内部矩形区域（完全变形）
    inside = (pts_x >= x1) & (pts_x <= x2) & (pts_y >= y1) & (pts_y <= y2)
    alpha[inside] = 1.0

    # 过渡区域（介于内部和外部扩展矩形之间）
    outside = (pts_x < x1_ext) | (pts_x > x2_ext) | (pts_y < y1_ext) | (pts_y > y2_ext)
    transition_mask = ~inside & ~outside

    if np.any(transition_mask):
        x = pts_x[transition_mask]
        y = pts_y[transition_mask]

        # 计算 x 方向的归一化距离（超出内部边界的比例）
        x_ratio = np.zeros_like(x)
        left_mask = x < x1
        x_ratio[left_mask] = (x1 - x[left_mask]) / (x1 - x1_ext)
        right_mask = x > x2
        x_ratio[right_mask] = (x[right_mask] - x2) / (x2_ext - x2)
        # 位于内部 x 范围内的点，x_ratio 保持为 0

        # 计算 y 方向的归一化距离
        y_ratio = np.zeros_like(y)
        bottom_mask = y < y1
        y_ratio[bottom_mask] = (y1 - y[bottom_mask]) / (y1 - y1_ext)
        top_mask = y > y2
        y_ratio[top_mask] = (y[top_mask] - y2) / (y2_ext - y2)

        # 取两个方向中较大的比例作为综合距离
        dist_ratio = np.maximum(x_ratio, y_ratio)
        dist_ratio = np.clip(dist_ratio, 0, 1)  # 确保在 [0,1]

        # 应用过渡函数（线性或选择的其他函数）
        transition_func = TRANSITION_FUNCTIONS.get(transition_types, linear)
        alpha[transition_mask] = 1 - transition_func(dist_ratio)

    return alpha


def generate_ellipse_alpha(pts_x, pts_y, x1, y1, x2, y2, extend, transition_types, cx, cy):
    """椭圆选框的过渡区生成"""
    # 计算椭圆半轴长
    a = abs(x2 - x1) / 2  # x方向半轴
    b = abs(y2 - y1) / 2  # y方向半轴

    # 扩展后的半轴长
    a_ext = a * (1 + extend)
    b_ext = b * (1 + extend)

    # 计算每个点到椭圆中心的归一化距离
    dx = pts_x - cx
    dy = pts_y - cy

    # 内部椭圆边界（距离 <= 1）
    inner_bound = (dx / a) ** 2 + (dy / b) ** 2

    # 外部椭圆边界（距离 <= 1+extend）
    outer_bound = (dx / a_ext) ** 2 + (dy / b_ext) ** 2

    # 计算alpha值
    alpha = np.zeros_like(pts_x)

    # 内部区域
    alpha[inner_bound <= 1] = 1.0

    # 过渡区域
    transition_mask = (inner_bound > 1) & (outer_bound <= 1)
    if np.any(transition_mask):
        # 计算在过渡带内的归一化距离 (0到1之间)
        dist_inner = np.sqrt(inner_bound[transition_mask])
        dist_ratio = (dist_inner - 1) / extend

        # 应用过渡函数
        transition_func = TRANSITION_FUNCTIONS.get(transition_types, linear)
        alpha[transition_mask] = 1 - transition_func(dist_ratio)

    return alpha


def generate_hexagon_alpha(pts_x, pts_y, x1, y1, x2, y2, extend, transition_types, cx, cy):
    """六边形选框的过渡区生成"""
    # 计算六边形外接圆半径
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    rx = width / 2
    ry = height / 2

    # 生成六边形顶点（内部）
    inner_vertices = generate_hexagon_vertices(cx, cy, rx, ry, 6)
    # 生成六边形顶点（外部）- 使用相同比例扩展
    rx_ext = rx * (1 + extend)
    ry_ext = ry * (1 + extend)
    outer_vertices = generate_hexagon_vertices(cx, cy, rx_ext, ry_ext, 6)

    return calculate_polygon_alpha(pts_x, pts_y, inner_vertices, outer_vertices, transition_types)


def generate_custom_polygon_alpha(pts_x, pts_y, shape_params, extend, transition_types, cx, cy):
    if 'vertices' not in shape_params:
        # 如果没有顶点信息，回退到矩形过渡区
        return generate_rectangle_alpha(pts_x, pts_y,
                                        cx - 10, cy - 10, cx + 10, cy + 10,
                                        extend, transition_types, cx, cy)

    vertices = shape_params['vertices']
    # 创建多边形路径（用于判断内部点）
    polygon_path = Path(vertices)
    points = np.column_stack((pts_x, pts_y))

    # 判断点是否在多边形内部
    inside = polygon_path.contains_points(points)

    # 计算多边形的边界，用于确定扩展距离
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    width = x_max - x_min
    height = y_max - y_min
    extend_dist = extend * max(width, height)   # 扩展距离

    alpha = np.zeros_like(pts_x)
    alpha[inside] = 1.0   # 内部点完全变形

    # 处理外部点：计算到多边形的最短距离，并据此分配过渡权重
    outside_mask = ~inside
    if np.any(outside_mask):
        outside_points = points[outside_mask]
        distances = np.zeros(len(outside_points))

        # 计算每个外部点到多边形各边的最短距离
        for i, point in enumerate(outside_points):
            min_dist = float('inf')
            for j in range(len(vertices)):
                p1 = vertices[j]
                p2 = vertices[(j + 1) % len(vertices)]
                dist = point_to_line_distance(point, p1, p2)
                if dist < min_dist:
                    min_dist = dist
            distances[i] = min_dist

        # 在扩展距离内的点进入过渡区
        in_transition = distances <= extend_dist
        if np.any(in_transition):
            # 归一化距离比
            dist_ratio = distances[in_transition] / extend_dist
            transition_func = TRANSITION_FUNCTIONS.get(transition_types, linear)
            alpha_values = 1 - transition_func(dist_ratio)

            # 将计算出的 alpha 值赋回原数组
            outside_indices = np.where(outside_mask)[0]
            trans_indices = outside_indices[in_transition]
            alpha[trans_indices] = alpha_values

    return alpha


def point_to_line_distance(point, line_start, line_end):
    """计算点到线段的距离"""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end
    # 线段长度的平方
    line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if line_length_sq == 0:
        # 如果线段是一个点，直接计算点到点的距离
        return np.sqrt((x - x1) ** 2 + (y - y1) ** 2)
    # 计算投影比例
    t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_length_sq))
    # 计算投影点
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)
    # 返回点到投影点的距离
    return np.sqrt((x - projection_x) ** 2 + (y - projection_y) ** 2)



def generate_hexagon_vertices(cx, cy, rx, ry, sides=6):
    """生成正多边形顶点"""
    vertices = []
    for i in range(sides):
        angle = 2 * np.pi * i / sides
        x = cx + rx * np.cos(angle)
        y = cy + ry * np.sin(angle)  # 使用ry而不是rx
        vertices.append([x, y])
    return vertices


def calculate_polygon_alpha(pts_x, pts_y, inner_vertices, outer_vertices, transition_types):
    """计算多边形区域的alpha值"""
    from matplotlib.path import Path

    # 创建内部和外部多边形路径
    inner_path = Path(inner_vertices)
    outer_path = Path(outer_vertices)

    # 检查点是否在多边形内
    points = np.column_stack((pts_x, pts_y))
    inside_inner = inner_path.contains_points(points)
    inside_outer = outer_path.contains_points(points)

    # 计算alpha值
    alpha = np.zeros_like(pts_x)

    # 内部区域
    alpha[inside_inner] = 1.0

    # 过渡区域（在外部多边形内但不在内部多边形内）
    transition_mask = inside_outer & ~inside_inner

    if np.any(transition_mask):
        # 对于过渡区域，计算到内部多边形的距离比
        # 这里简化处理：使用到重心的距离比
        inner_center = np.mean(inner_vertices, axis=0)
        outer_center = np.mean(outer_vertices, axis=0)

        # 计算每个点到内部多边形的归一化距离
        for i in np.where(transition_mask)[0]:
            point = points[i]
            # 计算到内部多边形的距离（简化：使用到最近顶点的距离）
            inner_dist = min(np.linalg.norm(point - vertex) for vertex in inner_vertices)
            outer_dist = min(np.linalg.norm(point - vertex) for vertex in outer_vertices)

            # 归一化距离比
            if outer_dist > inner_dist:
                dist_ratio = (inner_dist) / (outer_dist - inner_dist)
                dist_ratio = max(0, min(1, dist_ratio))

                # 应用过渡函数
                transition_func = TRANSITION_FUNCTIONS.get(transition_types, linear)
                alpha[i] = 1 - transition_func(dist_ratio)

    return alpha


def calculate_alpha_gradient(pts_x, pts_y, x1_int, x2_int, y1_int, y2_int,
                             x1_ext, x2_ext, y1_ext, y2_ext, transition_types):
    """计算矩形渐变alpha值"""
    alpha_rect = np.zeros_like(pts_x, dtype=float)

    # 逻辑掩码
    inside = (pts_x >= x1_int) & (pts_x <= x2_int) & (pts_y >= y1_int) & (pts_y <= y2_int)
    outer = (pts_x < x1_ext) | (pts_x > x2_ext) | (pts_y < y1_ext) | (pts_y > y2_ext)
    mid = ~inside & ~outer

    # 赋值内部区域
    alpha_rect[inside] = 1.0

    # 处理中间区域
    if np.any(mid):
        # x方向过渡
        left_zone = (pts_x >= x1_ext) & (pts_x < x1_int)
        right_zone = (pts_x > x2_int) & (pts_x <= x2_ext)

        # y方向过渡
        top_zone = (pts_y > y2_int) & (pts_y <= y2_ext)
        bottom_zone = (pts_y >= y1_ext) & (pts_y < y1_int)

        # x方向alpha计算
        x_alpha = np.ones_like(pts_x)
        left_func = TRANSITION_FUNCTIONS[transition_types['left']]
        right_func = TRANSITION_FUNCTIONS[transition_types['right']]
        x_alpha[left_zone] = left_func((pts_x[left_zone] - x1_ext) / (x1_int - x1_ext))
        x_alpha[right_zone] = right_func((x2_ext - pts_x[right_zone]) / (x2_ext - x2_int))

        # y方向alpha计算
        y_alpha = np.ones_like(pts_y)
        top_func = TRANSITION_FUNCTIONS[transition_types['top']]
        bottom_func = TRANSITION_FUNCTIONS[transition_types['bottom']]
        y_alpha[top_zone] = top_func((y2_ext - pts_y[top_zone]) / (y2_ext - y2_int))
        y_alpha[bottom_zone] = bottom_func((pts_y[bottom_zone] - y1_ext) / (y1_int - y1_ext))

        # 组合alpha值（取最小值）
        combined_alpha = np.minimum(x_alpha, y_alpha)
        alpha_rect[mid] = combined_alpha[mid]

    return alpha_rect


def shear_transformation(pts, alpha_rect, params=None):
    """
    使用变形矩阵对点集进行变换，仅在过渡带区域内应用渐变变换。
    """
    if params is None:
        params = {'x_scale': 20, 'y_scale': -20,'Theta_1':45,'Theta_2':120}  # 默认参数
    # 获取变形中心点
    cx = params.get('cx', 0)
    cy = params.get('cy', 0)
    X, Y = pts[:, 0], pts[:, 1]
    X_centered = X - cx
    Y_centered = Y - cy
    # 使用正确的参数键名
    Upper_right_scale = params['x_scale']
    Upper_left_scale = params['y_scale']
    Theta_1 = params['Theta_1']
    Theta_2 = params['Theta_2']
    m=1+Upper_right_scale/100
    n=1+Upper_left_scale/100
    D=np.array([[m,0],[0,n]])
    cos_1=math.cos(math.radians(Theta_1))
    sin_1 = math.sin(math.radians(Theta_1))
    cos_2 = math.cos(math.radians(Theta_2))
    sin_2 = math.sin(math.radians(Theta_2))
    S=np.array([[cos_1,cos_2],[sin_1,sin_2]])
    # 构造变形矩阵（不一定是正定矩阵，可以是任意线性变换）
    P = S@D@(S).T
    print(P)
    # 对所有点应用变形（包括过渡带）
    pts_transformed = pts.copy()
    transition_zone = alpha_rect > 0

    if np.any(transition_zone):
        # 提取过渡带点集并转置为 (2, N)
        pts_to_transform = np.column_stack((X_centered[transition_zone],
                                            Y_centered[transition_zone])).T  # 形状 (2, N)
        # 应用变形矩阵
        transformed_points = (P @ pts_to_transform).T
        transformed_points[:, 0] += cx
        transformed_points[:, 1] += cy
        # 混合原始点和变形点，使用alpha_rect作为权重
        # 对于alpha_rect=1的区域完全使用变形后的点
        # 对于alpha_rect=0的区域完全使用原始点
        # 中间区域线性插值
        alpha = alpha_rect[transition_zone].reshape(-1, 1)  # 形状 (N, 1)

        # 计算混合后的点
        blended_pts = (1 - alpha) * pts[transition_zone] + alpha * transformed_points
        pts_transformed[transition_zone] = blended_pts

    return pts_transformed


def get_shear_params(parent):
    """获取剪切变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Shear deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 创建图片标签（可选）
    image_label = QtWidgets.QLabel()
    image_path = "transform_function/Shear.png"  # 替换为你的图片路径
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
        layout.addRow(image_label)

    # 参数输入框
    Theta_1_edit = QtWidgets.QLineEdit("45")
    Upper_right_edit = QtWidgets.QLineEdit("20")
    Theta_2_edit = QtWidgets.QLineEdit("135")
    Upper_left_edit = QtWidgets.QLineEdit("-20")
    extend_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("Theta_1(°):", Theta_1_edit)
    layout.addRow("Transform_1(%):", Upper_right_edit)
    layout.addRow("Theta_2(°):", Theta_2_edit)
    layout.addRow("Transform_2(%):", Upper_left_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)

    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    # 确认/取消按钮
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'x_scale': float(Upper_right_edit.text()),
            'Theta_1': float(Theta_1_edit.text()),
            'y_scale': float(Upper_left_edit.text()),
            'Theta_2': float(Theta_2_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()  # 直接返回字符串
        }
    return None





def trigonometric(pts, alpha_rect, params=None):
    if params is None:
        params = {'A_wave': 0.3, 'B_wave': 1, 'C_wave': 0.3, 'D_wave': 1}
    X, Y = pts[:, 0], pts[:, 1]
    # 获取中心点坐标
    cx = params.get('cx', 0)
    cy = params.get('cy', 0)
    # 将坐标平移到以中心点为原点
    X_centered = X - cx
    Y_centered = Y - cy
    A_wave = params['A_wave']
    B_wave = params['B_wave']
    C_wave = params['C_wave']
    D_wave = params['D_wave']
    # 波纹变形参数（使用中心化坐标）
    x_wave = A_wave * np.sin(X_centered) * np.cos(Y_centered) * alpha_rect + B_wave * X_centered
    y_wave = C_wave * np.cos(X_centered) * np.sin(Y_centered) * alpha_rect + D_wave * Y_centered
    # 平移回原坐标系
    x_wave += cx
    y_wave += cy
    return np.column_stack((x_wave, y_wave))

def get_trigonometric_params(parent):
    """获取波纹变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Wave_dense deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Wave_dense.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    A_edit = QtWidgets.QLineEdit("0.3")
    B_edit = QtWidgets.QLineEdit("1.0")
    C_edit = QtWidgets.QLineEdit("0.3")
    D_edit = QtWidgets.QLineEdit("1.0")
    extend_edit = QtWidgets.QLineEdit("0.3")

    layout.addRow("A_wave :", A_edit)
    layout.addRow("B_wave :", B_edit)
    layout.addRow("C_wave :", C_edit)
    layout.addRow("D_wave :", D_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'A_wave': float(A_edit.text()),
            'B_wave': float(B_edit.text()),
            'C_wave': float(C_edit.text()),
            'D_wave': float(D_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None


def trigonometric_normal(pts, alpha_rect, params=None):
    if params is None:
        params = {'A_wave': 0.3, 'B_wave': 1, 'C_wave': 0.3, 'D_wave': 1}
    X, Y = pts[:, 0], pts[:, 1]
    # 获取中心点坐标
    cx = params.get('cx', 0)
    cy = params.get('cy', 0)
    # 将坐标平移到以中心点为原点
    X_centered = X - cx
    Y_centered = Y - cy
    A_wave = params['A_wave']
    B_wave = params['B_wave']
    C_wave = params['C_wave']
    D_wave = params['D_wave']
    # 波纹变形参数
    x_wave = A_wave * np.sin(X_centered) * np.sin(Y_centered) * alpha_rect + B_wave * X_centered
    y_wave = C_wave * np.cos(X_centered) * np.cos(Y_centered) * alpha_rect + D_wave * Y_centered
    x_wave += cx
    y_wave += cy
    return np.column_stack((x_wave, y_wave))


def get_trigonometric_normal_params(parent):
    """获取波纹变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Wave_normal deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Wave_normal.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    A_edit = QtWidgets.QLineEdit("0.3")
    B_edit = QtWidgets.QLineEdit("1.0")
    C_edit = QtWidgets.QLineEdit("0.3")
    D_edit = QtWidgets.QLineEdit("1.0")
    extend_edit = QtWidgets.QLineEdit("0.1")

    layout.addRow("A_wave :", A_edit)
    layout.addRow("B_wave :", B_edit)
    layout.addRow("C_wave :", C_edit)
    layout.addRow("D_wave :", D_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'A_wave': float(A_edit.text()),
            'B_wave': float(B_edit.text()),
            'C_wave': float(C_edit.text()),
            'D_wave': float(D_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




def swirl_transformation(pts, alpha_rect, params=None):
    """
    花瓣旋涡变形：在指定区域内应用旋涡效果
    参数:
    - pts: 点集，形状为(N,2)
    - alpha_rect: 一维数组，权重系数，范围[0, 1]
    - params: 参数字典，包含旋涡参数
    返回:
    - 变形后的点集
    """
    if params is None:
        params = {
            'A_swirl': 0.8, 'B_swirl': 0.12,
            'C_swirl': 1.2, 'D_swirl': 0.4,
            'cx': 0, 'cy': 0
        }
    X, Y = pts[:, 0], pts[:, 1]
    cx = params['cx']
    cy = params['cy']
    # 计算局部坐标
    Xs = X - cx
    Ys = Y - cy
    # 计算极坐标
    r_swirl = np.sqrt(Xs ** 2 + Ys ** 2)
    theta_swirl = np.arctan2(Ys, Xs)
    # 应用旋涡变形
    A_swirl = params['A_swirl']
    B_swirl = params['B_swirl']
    C_swirl = params['C_swirl']
    D_swirl = params['D_swirl']
    r_swirl_prime = r_swirl * (1 + A_swirl * alpha_rect * np.exp(-B_swirl * r_swirl))
    theta_swirl_prime = theta_swirl + C_swirl * alpha_rect * np.exp(-D_swirl * r_swirl)
    # 转换回笛卡尔坐标
    x_swirl = r_swirl_prime * np.cos(theta_swirl_prime) + cx
    y_swirl = r_swirl_prime * np.sin(theta_swirl_prime) + cy
    return np.column_stack((x_swirl, y_swirl))
def get_swirl_params(parent, cx=0, cy=0):
    """获取花瓣旋涡变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Swirl deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Swirl.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    # 创建参数输入框
    A_edit = QtWidgets.QLineEdit("0.3")
    B_edit = QtWidgets.QLineEdit("0.12")
    C_edit = QtWidgets.QLineEdit("0.2")
    D_edit = QtWidgets.QLineEdit("0.5")
    extend_edit = QtWidgets.QLineEdit("0.5")

    # 添加到布局
    layout.addRow("A_swirl :", A_edit)
    layout.addRow("B_swirl :", B_edit)
    layout.addRow("C_swirl :", C_edit)
    layout.addRow("D_swirl :", D_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)
    # 添加确定/取消按钮
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'A_swirl': float(A_edit.text()),
            'B_swirl': float(B_edit.text()),
            'C_swirl': float(C_edit.text()),
            'D_swirl': float(D_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




def rose_deformation(pts, alpha_rect, params=None):
    """
    应用玫瑰花边界变形

    参数:
    - pts: 二维数组，原始点坐标
    - alpha_rect: 一维数组，矩形区域的权重系数 [0,1]
    - params: 包含变形参数的字典

    返回:
    - 变形后的点坐标
    """
    if params is None:
        params = {'center_x': 0, 'center_y': 0, 'base_radius': 15,
                  'amplitude': 0.4, 'k_flower': 6, 'A_rose': 0.02, 'k_rose': 3}

    X, Y = pts[:, 0], pts[:, 1]
    cx = params.get('cx', params.get('center_x', 0))
    cy = params.get('cy', params.get('center_y', 0))
    base_radius = params['base_radius']
    amplitude = params['amplitude']
    k_flower = params['k_flower']
    A_rose = params['A_rose']
    k_rose = params['k_rose']

    # 局部坐标转换
    X_local = X - cx
    Y_local = Y - cy
    r = np.sqrt(X_local ** 2 + Y_local ** 2)
    theta = np.arctan2(Y_local, X_local)

    # 计算花瓣形状边界
    flower_radius = base_radius * (1 + amplitude * np.cos(k_flower * theta))

    # 设置过渡带
    r1 = flower_radius * 0.5
    r2 = r1 + 10  # 过渡带宽度

    # 计算玫瑰花alpha权重
    alpha_rose = np.zeros_like(r)
    inside = (r <= r1)
    outside = (r >= r2)
    mid = ~inside & ~outside

    alpha_rose[inside] = 1.0
    alpha_rose[mid] = 0.5 * (1 + np.cos(np.pi * (r[mid] - r1[mid]) / (r2[mid] - r1[mid])))

    # 应用扰动（与矩形区域权重结合）
    total_alpha = alpha_rose * alpha_rect
    r_prime = r * (1 + total_alpha * A_rose * np.cos(k_rose * r))

    # 转换回笛卡尔坐标
    x_rose = r_prime * np.cos(theta) + cx
    y_rose = r_prime * np.sin(theta) + cy

    # 组合变形结果
    x_final = X * (1 - total_alpha) + x_rose * total_alpha
    y_final = Y * (1 - total_alpha) + y_rose * total_alpha

    return np.column_stack((x_final, y_final))
def get_rose_params(parent):
    """获取玫瑰花变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Floral deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 创建输入框并设置默认值
    base_radius_edit = QtWidgets.QLineEdit("15")
    amplitude_edit = QtWidgets.QLineEdit("0.8")
    k_flower_edit = QtWidgets.QLineEdit("6")
    A_rose_edit = QtWidgets.QLineEdit("0.05")
    k_rose_edit = QtWidgets.QLineEdit("3")
    extend_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("Base radius:", base_radius_edit)
    layout.addRow("Petal amplitude:", amplitude_edit)
    layout.addRow("Number of petals:", k_flower_edit)
    layout.addRow("Disturbance amplitude:", A_rose_edit)
    layout.addRow("Perturbation wavenumber:", k_rose_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'base_radius': float(base_radius_edit.text()),
            'amplitude': float(amplitude_edit.text()),
            'k_flower': int(k_flower_edit.text()),
            'A_rose': float(A_rose_edit.text()),
            'k_rose': float(k_rose_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




def wrinkle(pts, alpha_rect, params=None):
    """褶皱变形"""
    if params is None:
        params = {
            'n': 4,
            'B_swirl': 0.2,
            'cx': 0,
            'cy': 0
        }
    X, Y = pts[:, 0], pts[:, 1]
    cx = params['cx']
    cy = params['cy']
    # 计算局部坐标
    Xs = X - cx
    Ys = Y - cy
    # 计算极坐标
    r_swirl = np.sqrt(Xs ** 2 + Ys ** 2)
    theta_swirl = np.arctan2(Ys, Xs)
    # 应用褶皱变形 - 修正变形公式
    n = params['n']
    B_swirl = params['B_swirl']
    # 计算变形后的半径（基于权重）
    r_swirl_prime = r_swirl * (1 + B_swirl * np.cos(n * theta_swirl) * alpha_rect)
    # 转换回笛卡尔坐标
    x_swirl = r_swirl_prime * np.cos(theta_swirl) + cx
    y_swirl = r_swirl_prime * np.sin(theta_swirl) + cy
    return np.column_stack((x_swirl, y_swirl))
def get_wrinkle_params(parent):
    """获取褶皱变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Wrinkle deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Wrinkle.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    # 创建输入框并设置默认值
    n_edit = QtWidgets.QLineEdit("4")
    B_swirl_edit = QtWidgets.QLineEdit("0.1")
    extend_edit = QtWidgets.QLineEdit("0.4")

    layout.addRow("Number of folds (n):", n_edit)
    layout.addRow("Deformation strength  (B_swirl):", B_swirl_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'n': int(n_edit.text()),
            'B_swirl': float(B_swirl_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




def rotate_stack(pts, alpha_rect, params=None):
    """旋转堆叠变形"""
    if params is None:
        params = {
            'B_swirl': 0.01,
            'D_swirl': 0.5,
            'cx': 0,
            'cy': 0
        }
    X, Y = pts[:, 0], pts[:, 1]
    cx = params['cx']
    cy = params['cy']
    # 计算局部坐标
    Xs = X - cx
    Ys = Y - cy
    # 计算极坐标
    r_swirl = np.sqrt(Xs ** 2 + Ys ** 2)
    theta_swirl = np.arctan2(Ys, Xs)
    # 应用旋转堆叠变形 - 修正变形公式
    B_swirl = params['B_swirl']
    D_swirl = params['D_swirl']
    # 计算变形后的半径（基于权重）
    r_swirl_prime = r_swirl * (1 + B_swirl * alpha_rect)
    theta_swirl_prime = theta_swirl + D_swirl * alpha_rect
    # 转换回笛卡尔坐标
    x_swirl = r_swirl_prime * np.cos(theta_swirl_prime) + cx
    y_swirl = r_swirl_prime * np.sin(theta_swirl_prime) + cy
    return np.column_stack((x_swirl, y_swirl))

def get_rotate_stack_params(parent):
    """获取旋转堆叠变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Rotate_stack deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Rotate_stack.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    # 创建输入框并设置默认值
    B_swirl_edit = QtWidgets.QLineEdit("0.01")
    D_swirl_edit = QtWidgets.QLineEdit("0.5")
    extend_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("B_swirl:", B_swirl_edit)
    layout.addRow("D_swirl:", D_swirl_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'B_swirl': float(B_swirl_edit.text()),
            'D_swirl': float(D_swirl_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None






def twist(pts, alpha_rect, params=None):
    """旋转堆叠变形"""
    if params is None:
        params = {
            'w_1': 0.01,
            'w_2': 0.5,
            'B':0.1,
            'cx': 0,
            'cy': 0
        }
    X, Y = pts[:, 0], pts[:, 1]
    cx = params['cx']
    cy = params['cy']
    # 计算局部坐标
    Xs = X - cx
    Ys = Y - cy
    # 计算极坐标
    r_swirl = np.sqrt(Xs ** 2 + Ys ** 2)
    theta_swirl = np.arctan2(Ys, Xs)
    # 应用旋转堆叠变形 - 修正变形公式
    w_1 = params['w_1']
    w_2 = params['w_2']
    B = params['B']
    # 计算变形后的半径（基于权重）
    r_swirl_prime = r_swirl * (1 + B*np.sin(w_1*theta_swirl) * alpha_rect + B *np.cos(w_2*r_swirl) * alpha_rect)
    theta_swirl_prime = theta_swirl + B*np.sin(w_2*r_swirl) * alpha_rect + B* np.cos(w_1*theta_swirl) * alpha_rect
    # 转换回笛卡尔坐标
    x_swirl = r_swirl_prime * np.cos(theta_swirl_prime) + cx
    y_swirl = r_swirl_prime * np.sin(theta_swirl_prime) + cy
    return np.column_stack((x_swirl, y_swirl))

def get_twist_params(parent):
    """获取四方窗口变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Twist deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Twist.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    # 创建输入框并设置默认值
    w_1_edit = QtWidgets.QLineEdit("0.01")
    w_2_edit = QtWidgets.QLineEdit("0.5")
    B_edit = QtWidgets.QLineEdit("0.1")
    extend_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("w_1:", w_1_edit)
    layout.addRow("w_2:", w_2_edit)
    layout.addRow("B:", B_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'w_1': float(w_1_edit.text()),
            'w_2': float(w_2_edit.text()),
            'B': float(B_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




def ripple(pts, alpha_rect, params=None):
    """波纹变形"""
    if params is None:
        params = {
            'w': 1,
            'B_swirl': 0.1,
            'C_swirl': 0.1,
            'cx': 0,
            'cy': 0
        }
    X, Y = pts[:, 0], pts[:, 1]
    cx = params['cx']
    cy = params['cy']
    # 计算局部坐标
    Xs = X - cx
    Ys = Y - cy
    # 计算极坐标
    r_swirl = np.sqrt(Xs ** 2 + Ys ** 2)
    theta_swirl = np.arctan2(Ys, Xs)
    # 应用褶皱变形 - 修正变形公式
    w = params['w']
    B_swirl = params['B_swirl']
    C_swirl = params['C_swirl']
    # 计算变形后的半径（基于权重）
    r_swirl_prime = r_swirl * (1 + B_swirl * np.cos(w * r_swirl) * alpha_rect * np.exp(-C_swirl * r_swirl))
    # 转换回笛卡尔坐标
    x_swirl = r_swirl_prime * np.cos(theta_swirl) + cx
    y_swirl = r_swirl_prime * np.sin(theta_swirl) + cy
    return np.column_stack((x_swirl, y_swirl))
def get_ripple_params(parent):
    """获取褶皱变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Ripple deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Ripple.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    # 创建输入框并设置默认值
    w_edit = QtWidgets.QLineEdit("1")
    B_swirl_edit = QtWidgets.QLineEdit("0.1")
    C_swirl_edit = QtWidgets.QLineEdit("0.1")
    extend_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("Number of folds (w):", w_edit)
    layout.addRow("Deformation strength (B_swirl):", B_swirl_edit)
    layout.addRow("Deformation strength (C_swirl):", C_swirl_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'w': float(w_edit.text()),
            'B_swirl': float(B_swirl_edit.text()),
            'C_swirl': float(C_swirl_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




def expand(pts, alpha_rect, params=None):
    """波纹变形"""
    if params is None:
        params = {
            'A': 1,
            'B': 0.1,
            'cx': 0,
            'cy': 0
        }
    X, Y = pts[:, 0], pts[:, 1]
    cx = params['cx']
    cy = params['cy']
    # 计算局部坐标
    Xs = X - cx
    Ys = Y - cy
    # 计算极坐标
    r_swirl = np.sqrt(Xs ** 2 + Ys ** 2)
    theta_swirl = np.arctan2(Ys, Xs)
    # 应用褶皱变形 - 修正变形公式
    A = params['A']
    B = params['B']
    # 计算变形后的半径（基于权重）
    r_swirl_prime = r_swirl * (1 + A * np.exp(-B * r_swirl) * alpha_rect )
    # 转换回笛卡尔坐标
    x_swirl = r_swirl_prime * np.cos(theta_swirl) + cx
    y_swirl = r_swirl_prime * np.sin(theta_swirl) + cy
    return np.column_stack((x_swirl, y_swirl))
def get_expand_params(parent):
    """获取褶皱变形参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Expand deformation parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 创建图片标签
    image_label = QtWidgets.QLabel()
    # 构建图片路径（假设图片位于'transform_function'文件夹）
    image_path = "transform_function/Expand.png"
    # 加载并显示图片（带错误处理）
    if os.path.exists(image_path):
        pixmap = QtGui.QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio))
    layout.addRow(image_label)  # 图片单独一行
    # 创建输入框并设置默认值
    A_edit = QtWidgets.QLineEdit("1")
    B_edit = QtWidgets.QLineEdit("1")
    extend_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("A:", A_edit)
    layout.addRow("B:", B_edit)
    layout.addRow("Transition Zone Ratio:", extend_edit)
    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'A': float(A_edit.text()),
            'B': float(B_edit.text()),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None





def custom_transform(pts, alpha_rect, params=None):
    """
    自定义变换函数，允许用户输入公式进行变换
    """
    if params is None:
        params = {
            'coord_system': 'cartesian',  # 'cartesian' 或 'polar'
            'x_formula': 'x',  # x坐标变换公式
            'y_formula': 'y',  # y坐标变换公式
            'extend': 0.1,
            'cx': 0,  # 添加中心点参数
            'cy': 0  # 添加中心点参数
        }

    X, Y = pts[:, 0], pts[:, 1]
    # 获取中心点坐标
    cx = params.get('cx', 0)
    cy = params.get('cy', 0)

    # 将坐标平移到以中心点为原点
    X_centered = X - cx
    Y_centered = Y - cy
    # 获取参数
    coord_system = params['coord_system']
    x_formula = params['x_formula']
    y_formula = params['y_formula']

    # 创建安全的评估环境
    safe_dict = {
        'np': np,
        'math': math,
        'pi': pi,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'exp': np.exp,
        'sqrt': np.sqrt,
        'log': np.log,
        'abs': np.abs
    }

    # 根据坐标系选择变换方式
    if coord_system == 'cartesian':
        # 笛卡尔坐标系变换
        safe_dict['x'] = X_centered  # 使用中心化后的x坐标
        safe_dict['y'] = Y_centered  # 使用中心化后的y坐标
        safe_dict['alpha'] = alpha_rect

        try:
            x_transformed = eval(x_formula, {"__builtins__": None}, safe_dict)
            y_transformed = eval(y_formula, {"__builtins__": None}, safe_dict)
        except Exception as e:
            print(f"Formula evaluation error: {e}")
            return pts

    elif coord_system == 'polar':
        # 极坐标系变换
        # 转换为极坐标
        r = np.sqrt(X_centered ** 2 + Y_centered ** 2)
        theta = np.arctan2(Y_centered, X_centered)

        safe_dict['r'] = r
        safe_dict['theta'] = theta
        safe_dict['alpha'] = alpha_rect

        try:
            r_transformed = eval(x_formula, {"__builtins__": None}, safe_dict)
            theta_transformed = eval(y_formula, {"__builtins__": None}, safe_dict)

            # 转换回笛卡尔坐标
            x_transformed = r_transformed * np.cos(theta_transformed)
            y_transformed = r_transformed * np.sin(theta_transformed)
        except Exception as e:
            print(f"Formula evaluation error: {e}")
            return pts
    x_final = x_transformed + cx
    y_final = y_transformed + cy
    return np.column_stack((x_final, y_final))

def get_custom_params(parent):
    """获取自定义变换参数对话框"""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Custom deformation parameter settings")
    dialog.setMinimumWidth(500)  # 设置对话框最小宽度以适应公式输入

    layout = QtWidgets.QFormLayout(dialog)

    # 坐标系选择
    coord_combo = QtWidgets.QComboBox()
    coord_combo.addItems(['cartesian', 'polar'])
    layout.addRow("Coordinate system:", coord_combo)

    # 公式输入框
    x_formula_edit = QtWidgets.QLineEdit("x + 0.5*alpha*np.sin(y)")
    x_formula_edit.setPlaceholderText("For example: x + 0.1*alpha*sin(5*y) or r*(1+0.1*alpha)")
    layout.addRow("X/R formula:", x_formula_edit)

    y_formula_edit = QtWidgets.QLineEdit("y + 0.5*alpha*np.cos(x)")
    y_formula_edit.setPlaceholderText("For example: y + 0.1*alpha*cos(5*x) or theta + 0.1*alpha")
    layout.addRow("Y/Theta formula:", y_formula_edit)

    # 过渡带比例
    extend_edit = QtWidgets.QLineEdit("0.1")
    layout.addRow("Transition Zone Ratio:", extend_edit)

    # 添加过渡方式选择
    transition_options = list(TRANSITION_FUNCTIONS.keys())
    radial_transition_combo = QtWidgets.QComboBox()
    radial_transition_combo.addItems(transition_options)
    radial_transition_combo.setCurrentText('linear')
    layout.addRow("Radial transition mode:", radial_transition_combo)

    # 添加说明标签
    info_label = QtWidgets.QLabel(
        "Available variables:\n"
        "- Cartesian coordinate system: x, y, alpha\n"
        "- Polar coordinate system: r, theta, alpha\n"
        "Available Functions: np.*, math.*, sin, cos, tan, exp, sqrt, log, abs"
    )
    info_label.setWordWrap(True)
    layout.addRow("Explanation:", info_label)

    # 确认/取消按钮
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return {
            'coord_system': coord_combo.currentText(),
            'x_formula': x_formula_edit.text(),
            'y_formula': y_formula_edit.text(),
            'extend': float(extend_edit.text()),
            'transition_types': radial_transition_combo.currentText()
        }
    return None




if __name__ == "__main__":
    pts_x, pts_y = ps_intersect(primary_sf=1, secondary_sf=1, theta=0, grid_number=50, side_offset=0.1, secondary=True,
                                centralized=True)
    pts = np.column_stack((pts_x, pts_y))
    pts = Path_fill(pts, 0.001)
    pts_x = pts[:, 0]
    pts_y = pts[:, 1]
    # 自定义选框
    x_min, x_max = -20, 20
    y_min, y_max = -20, 20
    shape_type = "rectangle"
    shape_params = None


    # 设置过渡函数类型
    transition_types = "linear"

    # 生成alpha值
    alpha = generate_alpha_rect(
        pts_x, pts_y,
        x_min, y_min, x_max, y_max,
        extend=0.5,
        transition_types=transition_types,
        shape_type=shape_type,
        shape_params=shape_params
    )

    # custom_params = {
    #     'coord_system': 'polar',
    #     'x_formula': 'r*(1 + 0.05*alpha*np.sin(0.5*r)*np.cos(7*theta)*np.exp(-0.02*r))',  # 直接写入公式
    #     'y_formula': 'theta + 0.03*alpha*np.cos(0.5*r)*np.sin(7*theta)*np.exp(-0.02*r)',
    #     'extend': 0.5
    # }#新变形结构3
    # custom_params = {
    #     'coord_system': 'polar',
    #     'x_formula': 'r*(1 + 0.08*alpha*np.sin(4*theta + 0.5*r)*np.tanh(0.1*r)*np.exp(-0.035*r))',
    #     'y_formula': 'theta + 0.04*alpha*np.cos(4*theta + 0.5*r)*np.tanh(0.1*r)*np.exp(-0.035*r)',
    #     'extend': 0.5
    # }  # 新变形结构4，涡旋旋转
    # custom_params = {
    #     'coord_system': 'cartesian',
    #     'x_formula': 'x + 0.5*alpha*(np.sin(0.5*y) - np.cos(0.5*x))',  # 直接写入公式,sin内部数字可决定花瓣数
    #     'y_formula': 'y + 0.5*alpha*(np.sin(0.5*x) - np.cos(0.5*y))',
    #     'extend': 0.5
    # }      #   混沌吸引，新变形结构5
    # custom_params = {
    #     'coord_system': 'cartesian',
    #     'x_formula': 'x + 0.5*alpha*(np.sin(0.5*x)*np.cos(0.5*y) + np.sin(0.5*(x+y))*np.cos(0.5*(x-y)))',  # 直接写入公式,sin内部数字可决定花瓣数
    #     'y_formula': 'y + 0.3*alpha*(np.cos(0.5*x)*np.sin(0.5*y) + np.cos(0.5*(x+y))*np.sin(0.5*(x-y)))',
    #     'extend': 0.5
    # }         #新变形结构6
    # custom_params = {
    #     'coord_system': 'cartesian',
    #     'x_formula': 'x + 0.4*alpha*(np.cos(0.5*x)*np.sin(0.5*y) - np.sin(0.5*x)*np.cos(0.5*y))',
    #     'y_formula': 'y + 0.4*alpha*(np.sin(0.5*x)*np.sin(0.5*y) + np.cos(0.5*x)*np.cos(0.5*y))',
    #     'extend': 0.5
    # }        #投影，新变形结构7

    ###########继续补充的变形类型
    # custom_params = {
    #     'coord_system': 'cartesian',
    # 'x_formula': 'x + 0.8*alpha*np.sin(0.5*x)',
    # 'y_formula': 'y + 0.8*alpha*np.cos(0.5*y)',
    #     'extend': 0.5
    # }         #新变形结构8
    # custom_params = {
    #     'coord_system': 'cartesian',
    #     'x_formula': 'x + 0.5*alpha*(np.sin(x)*np.exp(-0.1*x**2) - 0.5*np.cos(y)*np.exp(-0.1*y**2))',
    #     'y_formula': 'y + 0.5*alpha*(np.cos(x)*np.exp(-0.1*x**2) - 0.5*np.sin(y)*np.exp(-0.1*y**2))',
    #     'extend': 0.5
    # }  # 新变形结构9，星形内凹
    # custom_params = {
    #     'coord_system': 'polar',
    # 'x_formula': 'r*(1 + 0.15*alpha*np.tanh(0.6*np.sin(6*theta))*np.exp(-0.032*r))',
    # 'y_formula': 'theta + 0.12*alpha*np.tanh(0.6*np.cos(6*theta))*np.exp(-0.032*r)',
    #     'extend': 0.5
    # }        #新变形结构10，中心辐射褶皱
    custom_params = {
        'coord_system': 'cartesian',
        'x_formula': 'x + 0.5*alpha*np.sin(0.6*y)*np.cos(0.6*x)',
        'y_formula': 'y + 0.5*alpha*np.cos(0.6*x)*np.sin(0.6*y)',
        'extend': 0.5,'transition_types': 'linear'
    }     #新变形结构2






    #形成负泊松比结构




    # pts_transformed = custom_transform(pts, alpha)
    pts_transformed = custom_transform(pts, alpha,params=custom_params)
    plt.plot(pts_transformed[:, 0], pts_transformed[:, 1])
    plt.axis('equal')
    plt.show()



