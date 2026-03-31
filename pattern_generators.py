from PyQt5 import QtWidgets, QtCore
from intersecting_structure_generation import ps_intersect,psdd_intersect, remove_adjacent_duplicates, Path_fill
import numpy as np
from math import sin, cos, tan, pi, sqrt
from circle_ary import arc
from customization import generate_pattern, arc as cust_arc
import matplotlib.pyplot as plt


def generate_regular_triangle():
    """生成三角形点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Triangle parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框
    primary_sf_edit = QtWidgets.QLineEdit("20")
    secondary_sf_edit = QtWidgets.QLineEdit("20")
    side_offset_edit = QtWidgets.QLineEdit("5")
    angle_between_edit = QtWidgets.QLineEdit("60")
    grid_number_edit = QtWidgets.QLineEdit("10")
    layout.addRow("Primary_sf:", primary_sf_edit)
    layout.addRow("Secondary_sf:", secondary_sf_edit)
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Angle_between(°):", angle_between_edit)
    layout.addRow("Grid_number:", grid_number_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        primary_sf = float(primary_sf_edit.text())
        secondary_sf = float(secondary_sf_edit.text())
        side_offset = float(side_offset_edit.text())
        angle_between = float(angle_between_edit.text())
        grid_number = int(grid_number_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])  # 参数格式错误
    # 将角度转换为弧度
    angle_rad = angle_between * pi / 180
    # 计算theta值（副方向与主方向垂直方向的夹角）
    theta = pi / 2 - angle_rad
    try:
        pts_x_single, pts_y_single = psdd_intersect(
            primary_sf=primary_sf,
            secondary_sf=secondary_sf,
            side_offset=side_offset,
            theta=theta,
            grid_number=grid_number,
            diagonal_secondary=False
        )
        cycle_number = 1
        pts_x = pts_x_single
        pts_y = pts_y_single
        for _ in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)
        pts = np.column_stack((pts_x, pts_y))
        pts = Path_fill(points=pts, max_dis=1)
        pts = remove_adjacent_duplicates(pts)
        return pts  # 返回点集数组
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_square():
    """生成四边形点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Quadrilateral parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框（使用正方形特有参数）
    primary_sf_edit = QtWidgets.QLineEdit("0.5")
    secondary_sf_edit = QtWidgets.QLineEdit("0.5")
    side_offset_edit = QtWidgets.QLineEdit("2.5")
    angle_between_edit = QtWidgets.QLineEdit("90")  # 注意theta不能是pi/2的奇数倍
    grid_number_edit = QtWidgets.QLineEdit("40")
    layout.addRow("Primary_sf:", primary_sf_edit)
    layout.addRow("Secondary_sf:", secondary_sf_edit)
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Angle_between(°) :", angle_between_edit)
    layout.addRow("Grid_number:", grid_number_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        primary_sf = float(primary_sf_edit.text())
        secondary_sf = float(secondary_sf_edit.text())
        side_offset = float(side_offset_edit.text())
        angle_between = float(angle_between_edit.text())
        grid_number = int(grid_number_edit.text())
        # 将角度转换为弧度
        angle_rad = angle_between * pi / 180
        # 计算theta值（副方向与主方向垂直方向的夹角）
        theta = pi / 2 - angle_rad

        # 验证theta参数（避免90度的奇数倍）
        if abs(theta % (pi / 2)) < 1e-5 and abs(theta) > 1e-5:
            raise ValueError("Andle between primary_sf and secondary_sf cannot be an odd multiple of 90 degrees.")

    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])
    try:
        # 调用正方形专用生成函数
        pts_x_single, pts_y_single = ps_intersect(
            primary_sf=primary_sf,
            secondary_sf=secondary_sf,
            side_offset=side_offset,
            theta=theta,
            grid_number=grid_number,
            rotation_angle=0
        )
        # 扩展周期
        cycle_number=2
        pts_x = pts_x_single.copy()
        pts_y = pts_y_single.copy()
        for _ in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)
        # 后处理
        pts = np.column_stack((pts_x, pts_y))
        pts = Path_fill(points=pts, max_dis=0.1)
        pts = remove_adjacent_duplicates(pts)
        return pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_hexagon():
    """生成六边形点集"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Hexagon parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框（根据六边形代码参数设置）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("8")
    col_number_edit = QtWidgets.QLineEdit("12")
    cycle_number_edit = QtWidgets.QLineEdit("1")
    layout.addRow("a:", a_edit)
    layout.addRow("Row_number:", row_number_edit)
    layout.addRow("Col_number:", col_number_edit)
    layout.addRow("Cycle_number:", cycle_number_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())*2
        cycle_number = int(cycle_number_edit.text())
        # 验证参数有效性
        if row_number % 2 != 0 or col_number % 2 != 0:
            raise ValueError("Row_number and col_number must be even.")
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])
    # 生成点集
    try:
        # 初始化点集数组
        pts_single_x = np.array([0])
        pts_single_y = np.array([0])
        # 计算旋转中心
        center_x = col_number / 2 * sqrt(3) / 2 * a
        center_y = 0.5 * (row_number - 1) * 1.5 * a
        # 生成基础点阵
        for i in range(row_number):
            for j in range(col_number):
                if i % 2 == 0:
                    pt_x = 0.5 * sqrt(3) * a * j
                else:
                    pt_x = 0.5 * a * sqrt(3) * col_number - 0.5 * sqrt(3) * a * j
                pt_y = 0.25 * a * (-1) ** (i + j) + 1.5 * a * i
                pts_single_x = np.append(pts_single_x, pt_x)
                pts_single_y = np.append(pts_single_y, pt_y)
        # 坐标系平移，单取向
        pts_single_x -= center_x
        pts_single_y -= center_y
        # 添加过渡点
        pt_insert_1_x = pts_single_x[-1] - col_number * sqrt(3) / 4 * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        # 第一次旋转（60度）
        pts_rotated_1_x = pts_single_x * cos(pi / 3) - pts_single_y * sin(pi / 3)
        pts_rotated_1_y = pts_single_x * sin(pi / 3) + pts_single_y * cos(pi / 3)
        pt_insert_2_y = pts_rotated_1_y[1]
        # 第二次旋转（120度）
        pts_rotated_2_x = pts_single_x * cos(2 * pi / 3) - pts_single_y * sin(2 * pi / 3)
        pts_rotated_2_y = pts_single_x * sin(2 * pi / 3) + pts_single_y * cos(2 * pi / 3)
        pt_insert_3_x = pts_rotated_1_x[-1]
        pt_insert_3_y = pt_insert_2_y
        pt_insert_4_x = pts_rotated_2_x[0]
        pt_insert_4_y = pt_insert_3_y
        # 合并所有点集
        pts_x = np.hstack((
            pts_single_x,
            np.array([pt_insert_1_x, pt_insert_2_x]),
            pts_rotated_1_x,
            np.array([pt_insert_3_x, pt_insert_4_x]),
            pts_rotated_2_x
        ))
        pts_y = np.hstack((
            pts_single_y,
            np.array([pt_insert_1_y, pt_insert_2_y]),
            pts_rotated_1_y,
            np.array([pt_insert_3_y, pt_insert_4_y]),
            pts_rotated_2_y
        ))
        # 周期扩展
        for _ in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_single_x)
            pts_y = np.append(pts_y, pts_single_y)
        # 后处理
        pts = np.column_stack((pts_x, pts_y))
        pts = Path_fill(points=pts, max_dis=1)
        pts = remove_adjacent_duplicates(pts)
        return pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])


def generate_mosaic_pattern1():
    """生成镶嵌结构1图案点集，包含参数输入界面"""
    # 创建Qt应用实例
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_1 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("2")
    side_offset_edit = QtWidgets.QLineEdit("5")
    grid_number_edit = QtWidgets.QLineEdit("8")
    max_dis_edit = QtWidgets.QLineEdit("0.5")
    cycle_number_edit = QtWidgets.QLineEdit("1")
    layout.addRow("a :", a_edit)
    layout.addRow("Side_offset :", side_offset_edit)
    layout.addRow("Grid_number :", grid_number_edit)
    layout.addRow("Points_dis :", max_dis_edit)
    layout.addRow("Cycle_number :", cycle_number_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        a = float(a_edit.text())/2
        side_offset = float(side_offset_edit.text())
        grid_number = int(grid_number_edit.text())
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])
    # 生成镶嵌结构图案点集
    try:
        # 计算几何参数
        primary_sf = sqrt(3) * a
        secondary_sf = 2 * a
        theta = -30 / 180 * pi  # 恒定角度
        rotation_angle = 120 / 180 * pi  # 恒定旋转角度

        # 生成基础菱形图案
        intersect_x, intersect_y = ps_intersect(
            primary_sf=primary_sf,
            secondary_sf=secondary_sf,
            side_offset=side_offset,
            theta=theta,
            grid_number=grid_number,
            centralized=True,
            rotation_angle=rotation_angle
        )

        # 添加水平线结构
        # 计算水平线起点位置
        x_inter_1 = grid_number / 2 * secondary_sf + 2 * side_offset
        y_inter_1 = 0
        x_inter_2 = x_inter_1
        y_inter_2 = grid_number / 2 * sqrt(3) * secondary_sf - 0.25 * sqrt(3) * secondary_sf
        # 添加起点
        intersect_x = np.append(intersect_x, [x_inter_1, x_inter_2])
        intersect_y = np.append(intersect_y, [y_inter_1, y_inter_2])

        # 生成水平线网格
        for i in range(grid_number):
            # 计算水平线四个角点
            y_base = y_inter_2 - 2 * i * sqrt(3) / 2 * secondary_sf
            x1 = x_inter_2 - side_offset
            y1 = y_base
            x2 = -grid_number / 2 * secondary_sf - side_offset
            y2 = y_base
            x3 = x2
            y3 = y_base - sqrt(3) / 2 * secondary_sf
            x4 = x1
            y4 = y3

            # 添加水平线
            intersect_x = np.append(intersect_x, [x1, x2, x3, x4])
            intersect_y = np.append(intersect_y, [y1, y2, y3, y4])

        # 创建单周期点集
        pts_single = np.column_stack((intersect_x, intersect_y))
        # 根据重复次数复制点集
        if cycle_number > 1:
            final_pts = np.vstack([pts_single] * cycle_number)
        else:
            final_pts = pts_single

        # 后处理
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_mosaic_pattern2():
    """生成镶嵌结构2图案点集，包含参数输入界面"""
    # 创建Qt应用实例
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_2 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("13")
    col_number_edit = QtWidgets.QLineEdit("8")
    max_dis_edit = QtWidgets.QLineEdit("1")
    cycle_number_edit = QtWidgets.QLineEdit("2")
    layout.addRow("a :", a_edit)
    layout.addRow("Row_number :", row_number_edit)
    layout.addRow("Col_number :", col_number_edit)
    layout.addRow("Point_dis :", max_dis_edit)
    layout.addRow("Cycle_number :", cycle_number_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())+1
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    # 生成镶嵌结构2图案点集
    try:
        # 初始化点集
        pts_single_x = np.array([0])
        pts_single_y = np.array([0])
        # 计算旋转中心
        center_x = col_number / 2 * (1 + sqrt(3)) * a - 0.5 * sqrt(3) * a
        center_y = (row_number - 1) / 4 * (1 + sqrt(3)) * a

        # 生成基础网格点
        for i in range(row_number):
            # 向右生成点
            for j in range(col_number):
                # 计算点的x坐标（根据行奇偶性调整）
                if i % 2 == 0:
                    pt_1_x = (1 + sqrt(3)) * a * j
                else:
                    pt_1_x = (1 + sqrt(3)) * a * j - 0.5 * (sqrt(3) + 1) *a
                # 计算点的y坐标
                pt_1_y = 0.5 * (1 + sqrt(3)) * a * i
                pt_2_x = pt_1_x + a
                pt_2_y = pt_1_y
                pt_3_x = pt_2_x + 0.5 * sqrt(3) * a
                pt_3_y = pt_2_y + 0.5 * a

                # 添加到点集
                pts_single_x = np.append(pts_single_x, [pt_1_x, pt_2_x, pt_3_x])
                pts_single_y = np.append(pts_single_y, [pt_1_y, pt_2_y, pt_3_y])
            # 向左生成点
            for k in range(col_number):
                # 计算点的坐标（基于上一个点）
                pt_1_x = pts_single_x[-1] - 0.5 * sqrt(3) * a
                pt_1_y = (1 + sqrt(3)) * a * i / 2
                pt_2_x = pt_1_x - a
                pt_2_y = pt_1_y
                pt_3_x = pt_2_x - 0.5 * sqrt(3) * a
                pt_3_y = pt_2_y - 0.5 * a

                # 添加到点集
                pts_single_x = np.append(pts_single_x, [pt_1_x, pt_2_x, pt_3_x])
                pts_single_y = np.append(pts_single_y, [pt_1_y, pt_2_y, pt_3_y])

        # 将原点移动到图形中心
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        # 旋转90°生成第二部分
        cos_theta = cos(pi / 2)
        sin_theta = sin(pi / 2)
        pts_single_x_rotated = pts_single_x * cos_theta - pts_single_y * sin_theta
        pts_single_y_rotated = pts_single_x * sin_theta + pts_single_y * cos_theta
        # 向上移动第二部分
        pts_single_y_rotated = pts_single_y_rotated + 0.5 * (1 + sqrt(3)) * a
        # 插入过渡点，确保平滑连接
        pt_insert_1_x = pts_single_x[-1] - (1 + sqrt(3)) * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        pt_insert_2_y = pts_single_y_rotated[0]

        pt_insert_3_x = pts_single_x_rotated[-1]
        pt_insert_3_y = pts_single_y_rotated[-1] - (1 + sqrt(3)) * a
        pt_insert_4_x = pts_single_x[0]
        pt_insert_4_y = pt_insert_3_y
        # 添加过渡点
        pts_single_x = np.append(pts_single_x, [pt_insert_1_x, pt_insert_2_x])
        pts_single_y = np.append(pts_single_y, [pt_insert_1_y, pt_insert_2_y])
        pts_single_x_rotated = np.append(pts_single_x_rotated, [pt_insert_3_x, pt_insert_4_x])
        pts_single_y_rotated = np.append(pts_single_y_rotated, [pt_insert_3_y, pt_insert_4_y])

        # 组合两部分
        final_x = np.hstack((pts_single_x, pts_single_x_rotated))
        final_y = np.hstack((pts_single_y, pts_single_y_rotated))
        # 根据周期数复制点集
        if cycle_number > 1:
            final_x = np.tile(final_x, cycle_number)
            final_y = np.tile(final_y, cycle_number)
        # 创建最终点集
        final_pts = np.column_stack((final_x, final_y))
        # 后处理
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])


def generate_mosaic_pattern3():
    """生成镶嵌结构3图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_3 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("20")
    row_number_edit = QtWidgets.QLineEdit("8")
    col_number_edit = QtWidgets.QLineEdit("8")
    max_dis_edit = QtWidgets.QLineEdit("0.2")
    layout.addRow("六边形边长 (a):", a_edit)
    layout.addRow("行数 (row_number):", row_number_edit)
    layout.addRow("列数 (col_number):", col_number_edit)
    layout.addRow("点间距 (max_dis):", max_dis_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心
        center_x = 2 * a * row_number / 2 + 2.5 * a * col_number / 2
        center_y = sqrt(3) * a * row_number / 2 - 0.5 * sqrt(3) * a * col_number / 2
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集
        for i in range(row_number):
            for j in range(col_number):
                pt_1_x = 2 * a * i + 2.5 * a * j
                pt_1_y = sqrt(3) * a * i - 0.5 * sqrt(3) * a * j
                pt_2_x = pt_1_x + 2 * a
                pt_2_y = pt_1_y
                pts_single_x = np.append(pts_single_x, pt_1_x)
                pts_single_x = np.append(pts_single_x, pt_2_x)
                pts_single_y = np.append(pts_single_y, pt_1_y)
                pts_single_y = np.append(pts_single_y, pt_2_y)
            for k in range(col_number):
                pt_1_x = 2 * a * i + col_number * 2.5 * a - 2.5 * a * k
                pt_1_y = sqrt(3) * a * i + (-col_number + 2 + k) * 0.5 * sqrt(3) * a
                pt_2_x = pt_1_x - 2 * a
                pt_2_y = pt_1_y
                pts_single_x = np.append(pts_single_x, pt_1_x)
                pts_single_x = np.append(pts_single_x, pt_2_x)
                pts_single_y = np.append(pts_single_y, pt_1_y)
                pts_single_y = np.append(pts_single_y, pt_2_y)
        pts_single_append_x = np.array([0])
        pts_single_append_y = np.array([0])

        for i in range(row_number):
            for j in range(col_number):
                if i % 2 == 0:
                    pt_1_x = 2 * a * i + 2.5 * a * j + a
                    pt_1_y = sqrt(3) * a * i - 0.5 * sqrt(3) * a * j
                    pt_2_x = pt_1_x + 2 * a
                    pt_2_y = pt_1_y
                else:
                    pt_1_x = 2 * a * i + 2.5 * a * (col_number - j) + 1.5 * a
                    pt_1_y = sqrt(3) * a * i - 0.5 * sqrt(3) * a * (col_number - j - 1)
                    pt_2_x = pt_1_x - 2 * a
                    pt_2_y = pt_1_y
                pts_single_append_x = np.append(pts_single_append_x, pt_1_x)
                pts_single_append_x = np.append(pts_single_append_x, pt_2_x)
                pts_single_append_y = np.append(pts_single_append_y, pt_1_y)
                pts_single_append_y = np.append(pts_single_append_y, pt_2_y)
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        pts_single_append_x = pts_single_append_x - center_x
        pts_single_append_y = pts_single_append_y - center_y
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_1, pts_single_y_rotated_1 = pts_single_x * cos(pi / 3) - pts_single_y * sin(pi / 3), \
                                                         pts_single_x * sin(pi / 3) + pts_single_y * cos(pi / 3)
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_2, pts_single_y_rotated_2 = pts_single_x * cos(2 * pi / 3) - pts_single_y * sin(
            2 * pi / 3), \
                                                         pts_single_x * sin(2 * pi / 3) + pts_single_y * cos(2 * pi / 3)
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_append_1, pts_single_y_rotated_append_1 = pts_single_append_x * cos(
            pi / 3) - pts_single_append_y * sin(pi / 3), \
                                                                       pts_single_append_x * sin(
                                                                           pi / 3) + pts_single_append_y * cos(pi / 3)
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_append_2, pts_single_y_rotated_append_2 = pts_single_append_x * cos(
            2 * pi / 3) - pts_single_append_y * sin(2 * pi / 3), \
                                                                       pts_single_append_x * sin(
                                                                           2 * pi / 3) + pts_single_append_y * cos(
                                                                           2 * pi / 3)

        # 插入过渡点，避免过渡线影响内部结构
        pt_insert_1_x = pts_single_x[0] - 2 * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        pt_insert_2_y = pts_single_y_rotated_1[0]
        pt_insert_3_x = pt_insert_1_x
        pt_insert_3_y = pts_single_y_rotated_1[-1]
        pt_insert_4_x = pt_insert_3_x
        pt_insert_4_y = pts_single_y_rotated_2[0]
        pt_insert_5_x = pts_single_append_x[0]
        pt_insert_5_y = pts_single_y_rotated_2[-1]
        pt_insert_6_x = pt_insert_5_x
        pt_insert_6_y = pt_insert_5_y
        pt_insert_7_x = pt_insert_1_x
        pt_insert_7_y = pts_single_append_y[-1]
        pt_insert_8_x = pt_insert_7_x
        pt_insert_8_y = pts_single_y_rotated_append_1[0]
        pt_insert_9_x = pt_insert_1_x
        pt_insert_9_y = pts_single_y_rotated_append_1[-1]
        pt_insert_10_x = pt_insert_9_x
        pt_insert_10_y = pts_single_y_rotated_append_2[0]
        pt_insert_11_x = pts_single_x[0]
        pt_insert_11_y = pts_single_y_rotated_append_2[-1]
        pt_insert_12_x = pt_insert_11_x
        pt_insert_12_y = pt_insert_11_y

        plt.scatter(pt_insert_11_x, pt_insert_11_y)
        plt.scatter(pt_insert_12_x, pt_insert_12_y)
        # plt.scatter(pt_insert_4_x, pt_insert_4_y)
        pts_single_x = np.append(np.append(pts_single_x, pt_insert_1_x), pt_insert_2_x)
        pts_single_y = np.append(np.append(pts_single_y, pt_insert_1_y), pt_insert_2_y)
        pts_single_x_rotated_1 = np.append(np.append(pts_single_x_rotated_1, pt_insert_3_x), pt_insert_4_x)
        pts_single_y_rotated_1 = np.append(np.append(pts_single_y_rotated_1, pt_insert_3_y), pt_insert_4_y)
        pts_single_x_rotated_2 = np.append(np.append(pts_single_x_rotated_2, pt_insert_5_x), pt_insert_6_x)
        pts_single_y_rotated_2 = np.append(np.append(pts_single_y_rotated_2, pt_insert_5_y), pt_insert_6_y)
        pts_single_append_x = np.append(np.append(pts_single_append_x, pt_insert_7_x), pt_insert_8_x)
        pts_single_append_y = np.append(np.append(pts_single_append_y, pt_insert_7_y), pt_insert_8_y)
        pts_single_x_rotated_append_1 = np.append(np.append(pts_single_x_rotated_append_1, pt_insert_9_x),
                                                  pt_insert_10_x)
        pts_single_y_rotated_append_1 = np.append(np.append(pts_single_y_rotated_append_1, pt_insert_9_y),
                                                  pt_insert_10_y)
        pts_single_x_rotated_append_2 = np.append(np.append(pts_single_x_rotated_append_2, pt_insert_11_x),
                                                  pt_insert_12_x)
        pts_single_y_rotated_append_2 = np.append(np.append(pts_single_y_rotated_append_2, pt_insert_11_y),
                                                  pt_insert_12_y)

        pts_single_x = np.hstack((pts_single_x, pts_single_x_rotated_1, pts_single_x_rotated_2))
        pts_single_y = np.hstack((pts_single_y, pts_single_y_rotated_1, pts_single_y_rotated_2))
        pts_single_append_x = np.hstack((pts_single_append_x, pts_single_y_rotated_append_1))
        pts_single_append_y = np.hstack((pts_single_append_y, pts_single_y_rotated_append_1))
        # 组合最终点集
        final_pts = np.column_stack((pts_single_x, pts_single_y))
        # 后处理
        final_pts = Path_fill(final_pts, max_dis=max_dis )
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])




def generate_normal_circle():
    """生成普通堆积圆形点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Normal Layout parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框
    side_offset_edit = QtWidgets.QLineEdit("2")
    radius_edit = QtWidgets.QLineEdit("3")
    grid_number_edit = QtWidgets.QLineEdit("10")
    max_dis_edit = QtWidgets.QLineEdit("0.1")
    cycle_number_edit = QtWidgets.QLineEdit("2")
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Radius:", radius_edit)
    layout.addRow("Grid_number:", grid_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)
    layout.addRow("Cycle_number:", cycle_number_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        side_offset = float(side_offset_edit.text())
        radius = float(radius_edit.text())
        grid_number = int(grid_number_edit.text())
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])
    # 生成点集
    try:
        # 生成基础圆弧的函数
        def arc(center_x: float, center_y: float, radius: float,
                start_angle: float, stop_angle: float, max_dis: float):
            """生成圆弧点列"""
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
        # 生成点集逻辑
        pts_x_single = np.array([0])
        pts_y_single = np.array([0])
        # x方向点列生成
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
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)
        pts = np.column_stack((pts_x, pts_y))
        pts = Path_fill(points=pts, max_dis=max_dis)
        pts = remove_adjacent_duplicates(pts)
        return pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def rotate_points(pts, theta, center):
    """旋转点集的通用函数"""
    cx, cy = center
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    rotation_matrix = np.array([[cos_theta, -sin_theta], [sin_theta, cos_theta]])
    translated_pts = pts - np.array([cx, cy])
    rotated_pts = translated_pts.dot(rotation_matrix.T)
    return rotated_pts + np.array([cx, cy])
def generate_dense_circle():
    """生成密集堆积圆形点集"""
    # 创建参数输入对话框
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Dense Layout parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 参数输入控件
    circle_number_edit = QtWidgets.QLineEdit("5")
    side_offset_edit = QtWidgets.QLineEdit("10")
    radius_edit = QtWidgets.QLineEdit("2")
    cycle_number_edit = QtWidgets.QLineEdit("5")
    max_dis_edit = QtWidgets.QLineEdit("0.1")
    ratio_edit = QtWidgets.QLineEdit("0.5")
    layout.addRow("Arc_number:", circle_number_edit)
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Radius:", radius_edit)
    layout.addRow("Cycle_number:", cycle_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)
    layout.addRow("Ratio:", ratio_edit)
    # 按钮逻辑
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])
    try:
        # 获取参数
        circle_number = int(circle_number_edit.text())*2
        side_offset = float(side_offset_edit.text())
        radius = float(radius_edit.text())
        cycle_number = int(cycle_number_edit.text())
        max_dis = float(max_dis_edit.text())
        ratio = float(ratio_edit.text())
        # 计算参数
        alternate = sqrt(3) / 2 * radius
        row_dis = sqrt(3) * radius
        # 生成基础点集
        pts_x_single = np.array([0.0])
        pts_y_single = np.array([0.0])
        # 生成圆形阵列（保持原有生成逻辑）
        for i in range(int(circle_number / 2)):
            for j in range(circle_number):
                center_x = side_offset + (0.5 + j) * radius
                center_y = 2 * i * row_dis + (-1) ** (j + 1) * alternate
                start_angle = 2 / 3 * pi * (-1) ** j
                stop_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] + side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
            for j in range(circle_number):
                center_x = side_offset + circle_number * radius - (0.5 + j) * radius
                center_y = (2 * i + 1) * row_dis + (-1) ** (j + 1) * alternate
                stop_angle = 2 / 3 * pi * (-1) ** j
                start_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] - side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
        pts_single = np.column_stack((pts_x_single, pts_y_single))
        # 计算原始图案的中心点(cx，cy)
        cx = side_offset + (circle_number / 2 - 0.5) * radius
        cy = -alternate + ((1 + circle_number / 2) / 2 - 1) * 2 * row_dis
        center = (cx, cy)
        # 原始图案顺逆时针各旋转60°得到旋转后的图案
        pts_single_rotated_1 = rotate_points(pts_single, pi / 3, center)
        pts_single_rotated_2 = rotate_points(pts_single, -pi / 3, center)

        # 计算边界框
        all_x = np.concatenate([pts_single[:, 0], pts_single_rotated_1[:, 0], pts_single_rotated_2[:, 0]])
        all_y = np.concatenate([pts_single[:, 1], pts_single_rotated_1[:, 1], pts_single_rotated_2[:, 1]])
        min_x, max_x = np.min(all_x), np.max(all_x)
        min_y, max_y = np.min(all_y), np.max(all_y)

        # 计算外部过渡点
        margin = 5  # 过渡点距离边界的距离
        pt_insert_1_x = min_x - margin
        pt_insert_1_y = pts_single[-1, 1]
        pt_insert_2_x = min_x - margin
        pt_insert_2_y = pts_single_rotated_1[0, 1] - margin
        pt_insert_3_x = min_x - margin
        pt_insert_3_y = pts_single_rotated_1[-1, 1] - margin
        pt_insert_4_x = min_x - margin
        pt_insert_4_y = pts_single_rotated_2[0, 1]
        pt_insert_5_x = min_x - margin
        pt_insert_5_y = pts_single_rotated_2[-1, 1]
        pt_insert_6_x = min_x - margin
        pt_insert_6_y = pts_single[0, 1]

        # 构建完整的点序列
        pts_x_complete = np.hstack((
            pts_single[:, 0],
            [pt_insert_1_x, pt_insert_2_x],
            pts_single_rotated_1[:, 0],
            [pt_insert_3_x, pt_insert_4_x],
            pts_single_rotated_2[:, 0],
            [pt_insert_5_x, pt_insert_6_x]
        ))

        pts_y_complete = np.hstack((
            pts_single[:, 1],
            [pt_insert_1_y, pt_insert_2_y],
            pts_single_rotated_1[:, 1],
            [pt_insert_3_y, pt_insert_4_y],
            pts_single_rotated_2[:, 1],
            [pt_insert_5_y, pt_insert_6_y]
        ))
        pts_x = pts_x_complete
        pts_y = pts_y_complete

        for i in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_complete)
            pts_y = np.append(pts_y, pts_y_complete)
        # 组合最终点集（添加中心点）
        final_pts = np.column_stack((pts_x, pts_y))
        # 后处理
        final_pts = Path_fill(points=final_pts, max_dis=max_dis * 5)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])


def generate_arc():
    """生成圆弧四边形图案，包含参数输入界面"""
    # 创建Qt应用实例
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Arc Quadrilateral Parameter Settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框
    radius_edit = QtWidgets.QDoubleSpinBox()
    radius_edit.setRange(0.1, 1000.0)
    radius_edit.setValue(1.0)
    layout.addRow("Radius:", radius_edit)

    max_dis_edit = QtWidgets.QDoubleSpinBox()
    max_dis_edit.setRange(0.001, 1.0)
    max_dis_edit.setValue(0.01)
    max_dis_edit.setDecimals(4)
    layout.addRow("Point_dis:", max_dis_edit)

    grid_number_edit = QtWidgets.QSpinBox()
    grid_number_edit.setRange(2, 100)
    grid_number_edit.setValue(6)
    grid_number_edit.setSingleStep(2)
    layout.addRow("Grid Number:", grid_number_edit)

    y_offset_edit = QtWidgets.QDoubleSpinBox()
    y_offset_edit.setRange(-1000, 1000)
    y_offset_edit.setValue(sqrt(2))  # 默认值
    layout.addRow("Y Offset:", y_offset_edit)

    orientation_edit = QtWidgets.QSpinBox()
    orientation_edit.setRange(1, 36)
    orientation_edit.setValue(2)
    layout.addRow("Orientation Number:", orientation_edit)

    layer_edit = QtWidgets.QSpinBox()
    layer_edit.setRange(1, 10)
    layer_edit.setValue(1)
    layout.addRow("Layer Number:", layer_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])

    try:
        # 获取参数值
        radius = radius_edit.value()
        max_dis = max_dis_edit.value()
        grid_number = grid_number_edit.value()
        y_offset = y_offset_edit.value()
        orientation_number = orientation_edit.value()
        layer_number = layer_edit.value()

        # 确保grid_number为偶数
        if grid_number % 2 != 0:
            grid_number += 1

        # 生成两个圆弧构成基本图案
        # 修正：直接获取点集数组而不是尝试解包
        arc1 = cust_arc(
            center_x=0.5 * sqrt(2) * radius,
            center_y=0.5 * sqrt(2) * radius,
            radius=radius,
            start_angle=-135 * pi / 180,  # 转换为弧度
            stop_angle=-45 * pi / 180,  # 转换为弧度
            max_dis=max_dis
        )

        arc2 = cust_arc(
            center_x=1.5 * sqrt(2) * radius,
            center_y=-0.5 * sqrt(2) * radius,
            radius=radius,
            start_angle=135 * pi / 180,  # 转换为弧度
            stop_angle=45 * pi / 180,  # 转换为弧度
            max_dis=max_dis
        )

        # 检查弧线是否为空
        if len(arc1) == 0 or len(arc2) == 0:
            QtWidgets.QMessageBox.warning(None, "错误", "生成的圆弧点集为空，请检查参数")
            return np.array([])

        # 计算连接点
        connection_point1 = arc1[-1]
        connection_point2 = arc2[0]

        # 生成连接线（10个点）
        connection_line = np.linspace(connection_point1, connection_point2, 10)

        # 组合基本图案
        base_pattern = np.vstack([arc1, connection_line, arc2])

        # 调用generate_pattern生成完整图案
        pattern = generate_pattern(
            forward=base_pattern,  # 使用组合后的图案
            backward=base_pattern,  # 使用相同的图案作为回程
            grid_number=grid_number,
            y_offset=y_offset,
            orientation_number=orientation_number,
            center_select=(0, 0),  # 使用默认中心
            layer_number=layer_number
        )

        # 后处理
        pattern = Path_fill(points=pattern, max_dis=max_dis)
        pattern = remove_adjacent_duplicates(pattern)

        return pattern

    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "错误", f"生成图案失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return np.array([])





def remove_adjacent_duplicates(points, tol=1e-5):
    """移除相邻的重复点"""
    if len(points) == 0:
        return points
    new_points = [points[0]]
    for i in range(1, len(points)):
        if np.linalg.norm(points[i] - new_points[-1]) > tol:
            new_points.append(points[i])
    return np.array(new_points)
def insert_points(points, m):
    """在两点之间按最大间距m插入新点"""
    if len(points) == 0:
        return np.array([])
    new_points = [points[0]]
    for i in range(1, len(points)):
        p1, p2 = points[i - 1], points[i]
        distance = np.linalg.norm(p2 - p1)

        if distance <= m:
            new_points.append(p2)
        else:
            num_insert = int(distance // m)
            for j in range(1, num_insert + 1):
                new_point = p1 + (p2 - p1) * (j * m / distance)
                new_points.append(new_point)
            new_points.append(p2)
    return np.array(new_points)

def generate_sine_wave():
    """生成正弦波点集的对话框"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Trigonometric parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 参数输入控件
    params = {
        'num_rows': QtWidgets.QLineEdit("20"),
        'amplitude': QtWidgets.QLineEdit("0.135"),
        'vertical_spacing': QtWidgets.QLineEdit("0.5"),
        'num_cycles': QtWidgets.QLineEdit("10"),
        'horizontal_range': QtWidgets.QLineEdit("10"),
        'adjacent_distance': QtWidgets.QLineEdit("0.07"),
        'cycle_number': QtWidgets.QLineEdit("2")
    }
    # 添加控件到布局
    for name, widget in params.items():
        layout.addRow(f"{name}:", widget)
    # 添加按钮
    btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    btn_box.accepted.connect(dialog.accept)
    btn_box.rejected.connect(dialog.reject)
    layout.addRow(btn_box)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])
    try:
        # 获取并转换参数
        num_rows = int(params['num_rows'].text())
        amplitude = float(params['amplitude'].text())
        vertical_spacing = float(params['vertical_spacing'].text())
        num_cycles = int(params['num_cycles'].text())
        horizontal_range = float(params['horizontal_range'].text())
        adjacent_distance = float(params['adjacent_distance'].text())
        cycle_number = int(params['cycle_number'].text())
        # 生成振幅列表
        amplitudes = [amplitude] * num_rows
        # 生成正弦波点集
        t = np.linspace(0, num_cycles * 2 * pi, 400)
        all_points = []
        for row in range(num_rows):
            vertical_offset = row * vertical_spacing

            # 当前行的正弦波
            y = amplitudes[row] * np.sin(t) + vertical_offset
            x = np.linspace(0, horizontal_range, len(y))  # 水平区间相同

            # 奇数行从左到右，偶数行从右到左
            if row % 2 == 0:  # 奇数行
                all_points.extend(zip(x, y))
            else:  # 偶数行
                all_points.extend(zip(x[::-1], y))

            # 添加过渡段到下一行
            if row < num_rows - 1:
                transition_x = [horizontal_range if row % 2 == 0 else 0] * 100  # 竖直过渡
                transition_y = np.linspace(vertical_offset, (row + 1) * vertical_spacing, 100)
                all_points.extend(zip(transition_x, transition_y))
        # 后续处理
        # 将点列转换为numpy数组
        all_points = np.array(all_points)
        # 去除相邻重合点
        all_points = remove_adjacent_duplicates(all_points)
        # 将图形中心化
        all_points[:, 0] -= horizontal_range / 2 - 0.5 * vertical_spacing  # 水平中心化
        all_points[:, 1] -= (num_rows - 1) * vertical_spacing / 2  # 垂直中心化
        # 第一个过渡点，注意总过渡线段长度是a的偶数倍
        insert_1_x = all_points[-1, 0]
        insert_1_y = all_points[-1, 1] + vertical_spacing
        # 单取向的旋转角度
        theta = pi / 2
        # 旋转矩阵
        rotate_matrix = np.array([cos(theta), -sin(theta), sin(theta), cos(theta)]).reshape(2, 2)
        # 单取向旋转90°
        all_points_rotated = np.dot(all_points, rotate_matrix)
        # 将单取向与过渡点1、旋转后的取向点列组合
        all_points = np.concatenate((all_points, np.array([insert_1_x, insert_1_y]).reshape(1, 2), all_points_rotated),
                                    axis=0)
        # 为了回到初始点额外加三个过渡点，切记总过渡线段长度是a的偶数倍
        insert_2_x = all_points[-1, 0] + 2 * vertical_spacing
        insert_2_y = all_points[-1, 1]
        insert_3_x = insert_2_x
        insert_3_y = insert_2_y - (num_rows + 1) * vertical_spacing
        insert_4_x = all_points[0, 0]
        insert_4_y = insert_3_y
        # 2-3-4过渡点的合集
        insert_ary_temp = np.array([insert_2_x, insert_2_y, insert_3_x, insert_3_y, insert_4_x, insert_4_y]).reshape(3,
                                                                                                                     2)
        # 将双取向点列与过渡点组合
        all_points = np.concatenate((all_points, insert_ary_temp), axis=0)
        # 利用insert_points函数将端点式点列填充为密集式点列
        all_points = insert_points(all_points, adjacent_distance)
        pts = all_points
        for i in range(cycle_number - 1):
            pts = np.concatenate((pts, all_points), axis=0)
        return pts
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error", f"Invalid parameter format: {str(e)}")
        return np.array([])



def generate_flower():
    """生成花朵图案点集，包含参数输入界面"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Flower parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框
    params = {
        "circle_number": QtWidgets.QLineEdit("15"),
        "ratio": QtWidgets.QLineEdit("0.8"),
        "side_offset": QtWidgets.QLineEdit("5"),
        "radius": QtWidgets.QLineEdit("2"),
        "max_dis": QtWidgets.QLineEdit("0.3"),
        "cycle_number": QtWidgets.QLineEdit("1")
    }
    for name, widget in params.items():
        layout.addRow(name, widget)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])
    try:
        # 获取参数值
        circle_number = int(params["circle_number"].text())
        ratio = float(params["ratio"].text())
        side_offset = float(params["side_offset"].text())
        radius = float(params["radius"].text())
        max_dis = float(params["max_dis"].text())
        cycle_number = int(params["cycle_number"].text())
        # 计算衍生参数
        alternate = sqrt(3) / 2 * radius
        row_dis = sqrt(3) * radius
        # 初始化点集
        pts_x_single = np.array([0.0])
        pts_y_single = np.array([0.0])
        # 生成基本图案
        for i in range(int(circle_number / 2)):
            for j in range(circle_number):
                center_x = side_offset + (0.5 + j) * radius
                center_y = 2 * i * row_dis + (-1) ** (j + 1) * alternate
                start_angle = 2 / 3 * pi * (-1) ** j
                stop_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] + side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
            for j in range(circle_number):
                center_x = side_offset + circle_number * radius - (0.5 + j) * radius
                center_y = (2 * i + 1) * row_dis + (-1) ** (j + 1) * alternate
                stop_angle = pi * (-1) ** j
                start_angle = 2 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] - side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
        # print(pts_x_single.size)
        pts_single = np.column_stack((pts_x_single, pts_y_single))
        plt.plot(pts_x_single, pts_y_single)
        cx = side_offset + (circle_number / 2 - 0.5) * radius
        cy = alternate + ((1 + circle_number / 2) / 2 - 1) * 2 * row_dis
        center = (cx, cy)
        pts_single_rotated_1 = rotate_points(pts_single, pi / 3, center)
        pts_single_rotated_2 = rotate_points(pts_single, -pi / 3, center)

        # 计算边界框
        all_x = np.concatenate([pts_single[:, 0], pts_single_rotated_1[:, 0], pts_single_rotated_2[:, 0]])
        all_y = np.concatenate([pts_single[:, 1], pts_single_rotated_1[:, 1], pts_single_rotated_2[:, 1]])
        min_x, max_x = np.min(all_x), np.max(all_x)
        min_y, max_y = np.min(all_y), np.max(all_y)

        # 计算外部过渡点
        margin = 5  # 过渡点距离边界的距离
        pt_insert_1_x = min_x - margin
        pt_insert_1_y = pts_single[-1, 1]
        pt_insert_2_x = min_x - margin
        pt_insert_2_y = pts_single_rotated_1[0, 1] - margin
        pt_insert_3_x = min_x - margin
        pt_insert_3_y = pts_single_rotated_1[-1, 1] - margin
        pt_insert_4_x = min_x - margin
        pt_insert_4_y = pts_single_rotated_2[0, 1]
        pt_insert_5_x = min_x - margin
        pt_insert_5_y = pts_single_rotated_2[-1, 1]
        pt_insert_6_x = min_x - margin
        pt_insert_6_y = pts_single[0, 1]

        # 构建完整的点序列
        pts_x_single = np.hstack((
            pts_single[:, 0],
            [pt_insert_1_x, pt_insert_2_x],
            pts_single_rotated_1[:, 0],
            [pt_insert_3_x, pt_insert_4_x],
            pts_single_rotated_2[:, 0],
            [pt_insert_5_x, pt_insert_6_x]
        ))

        pts_y_single = np.hstack((
            pts_single[:, 1],
            [pt_insert_1_y, pt_insert_2_y],
            pts_single_rotated_1[:, 1],
            [pt_insert_3_y, pt_insert_4_y],
            pts_single_rotated_2[:, 1],
            [pt_insert_5_y, pt_insert_6_y]
        ))
        pts_x = pts_x_single
        pts_y = pts_y_single
        for i in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)
        # 组合最终点集（添加中心点）
        final_pts = np.column_stack((pts_x, pts_y))
        # 后处理
        final_pts = Path_fill(final_pts, max_dis=max_dis * 5)  # 调整填充参数
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_windmill():
    """生成风车图案点集，包含参数输入界面"""
    # 创建Qt应用实例
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Windmill parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    circle_number_edit = QtWidgets.QLineEdit("27")
    side_offset_edit = QtWidgets.QLineEdit("10")
    radius_edit = QtWidgets.QLineEdit("2")
    max_dis_edit = QtWidgets.QLineEdit("0.1")
    cycle_number_edit = QtWidgets.QLineEdit("1")

    layout.addRow("circle_number:", circle_number_edit)
    layout.addRow("side_offset:", side_offset_edit)
    layout.addRow("radius:", radius_edit)
    layout.addRow("max_dis:", max_dis_edit)
    layout.addRow("cycle_number:", cycle_number_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        circle_number = int(circle_number_edit.text())
        side_offset = float(side_offset_edit.text())
        radius = float(radius_edit.text())
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    # 生成风车图案点集
    try:
        # 计算几何参数
        alternate = sqrt(3) / 2 * radius
        row_dis = sqrt(3) * radius
        # 初始化单臂点集
        pts_x_single = np.array([0.0])
        pts_y_single = np.array([0.0])

        # 生成单个臂的轨迹
        for i in range(int(circle_number / 2)):
            for j in range(circle_number):
                center_x = side_offset + (0.5 + j) * radius
                center_y = 2 * i * row_dis + (-1) ** (j + 1) * alternate
                start_angle = 2 / 3 * pi * (-1) ** j
                stop_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] + side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
            for j in range(circle_number):
                center_x = side_offset + circle_number * radius - (0.5 + j) * radius
                center_y = (2 * i + 1) * row_dis + (-1) ** (j + 1) * alternate
                stop_angle = pi * (-1) ** j
                start_angle = 2 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] - side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))

        pts_single = np.column_stack((pts_x_single, pts_y_single))
        cx = side_offset + (circle_number / 2 - 0.5) * radius
        cy = -alternate + ((1 + circle_number / 2) / 2 - 1) * 2 * row_dis
        center = (cx, cy)

        # 平移点使旋转中心到原点
        pts_single_translated = pts_single - np.array([cx, cy])

        # 旋转点
        pts_single_rotated_1 = rotate_points(pts_single, pi / 3, center)
        pts_single_rotated_2 = rotate_points(pts_single, -pi / 3, center)

        # 计算边界框
        all_x = np.concatenate([pts_single[:, 0], pts_single_rotated_1[:, 0], pts_single_rotated_2[:, 0]])
        all_y = np.concatenate([pts_single[:, 1], pts_single_rotated_1[:, 1], pts_single_rotated_2[:, 1]])
        min_x, max_x = np.min(all_x), np.max(all_x)
        min_y, max_y = np.min(all_y), np.max(all_y)

        # 计算外部过渡点
        margin = 5  # 过渡点距离边界的距离
        pt_insert_1_x = min_x - margin
        pt_insert_1_y = pts_single[-1, 1]
        pt_insert_2_x = min_x - margin
        pt_insert_2_y = pts_single_rotated_1[0, 1] - margin
        pt_insert_3_x = min_x - margin
        pt_insert_3_y = pts_single_rotated_1[-1, 1] - margin
        pt_insert_4_x = min_x - margin
        pt_insert_4_y = pts_single_rotated_2[0, 1]
        pt_insert_5_x = min_x - margin
        pt_insert_5_y = pts_single_rotated_2[-1, 1]
        pt_insert_6_x = min_x - margin
        pt_insert_6_y = pts_single[0, 1]

        # 构建完整的点序列
        pts_x_complete = np.hstack((
            pts_single[:, 0],
            [pt_insert_1_x, pt_insert_2_x],
            pts_single_rotated_1[:, 0],
            [pt_insert_3_x, pt_insert_4_x],
            pts_single_rotated_2[:, 0],
            [pt_insert_5_x, pt_insert_6_x]
        ))

        pts_y_complete = np.hstack((
            pts_single[:, 1],
            [pt_insert_1_y, pt_insert_2_y],
            pts_single_rotated_1[:, 1],
            [pt_insert_3_y, pt_insert_4_y],
            pts_single_rotated_2[:, 1],
            [pt_insert_5_y, pt_insert_6_y]
        ))
        pts_x = pts_x_complete
        pts_y = pts_y_complete
        for i in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_complete)
            pts_y = np.append(pts_y, pts_y_complete)
        # 组合最终点集（添加中心点）
        final_pts = np.column_stack((pts_x, pts_y))
        # 后处理
        final_pts = Path_fill(points=final_pts, max_dis=max_dis * 5)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_hexagonal_pattern():
    """生成六角图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Hexagram parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框（设置默认值）
    circle_number_edit = QtWidgets.QLineEdit("14")
    side_offset_edit = QtWidgets.QLineEdit("10")
    radius_edit = QtWidgets.QLineEdit("2")
    max_dis_edit = QtWidgets.QLineEdit("0.1")
    cycle_number_edit = QtWidgets.QLineEdit("2")
    layout.addRow("circle_number:", circle_number_edit)
    layout.addRow("side_offset:", side_offset_edit)
    layout.addRow("radius:", radius_edit)
    layout.addRow("max_dis:", max_dis_edit)
    layout.addRow("cycle_number:", cycle_number_edit)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作
    # 获取参数值
    try:
        circle_number = int(circle_number_edit.text())
        side_offset = float(side_offset_edit.text())
        radius = float(radius_edit.text())
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])
    # 生成基础点集
    try:
        alternate = sqrt(3) / 2 * radius
        row_dis = sqrt(3) * radius
        pts_x_single = np.array([0.0])
        pts_y_single = np.array([0.0])
        # 生成基础弧线段
        for i in range(int(circle_number / 2)):
            for j in range(circle_number):
                center_x = side_offset + (0.5 + j) * radius
                center_y = 2 * i * row_dis + (-1) ** (j + 1) * alternate
                start_angle = 2 / 3 * pi * (-1) ** j
                stop_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] + side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
            for j in range(circle_number):
                center_x = side_offset + circle_number * radius - (0.5 + j) * radius
                center_y = (2 * i + 1) * row_dis + (-1) ** (j + 1) * alternate
                stop_angle = 2 / 3 * pi * (-1) ** j
                start_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] - side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
        pts_single = np.column_stack((pts_x_single, pts_y_single))

        cx = side_offset + (circle_number / 2 - 0.5) * radius
        cy = alternate + ((1 + circle_number / 2) / 2 - 1) * 2 * row_dis
        center = (cx, cy)
        pts_single_rotated_1 = rotate_points(pts_single, pi / 3, center)
        pts_single_rotated_2 = rotate_points(pts_single, -pi / 3, center)

        # 计算边界框
        all_x = np.concatenate([pts_single[:, 0], pts_single_rotated_1[:, 0], pts_single_rotated_2[:, 0]])
        all_y = np.concatenate([pts_single[:, 1], pts_single_rotated_1[:, 1], pts_single_rotated_2[:, 1]])
        min_x, max_x = np.min(all_x), np.max(all_x)
        min_y, max_y = np.min(all_y), np.max(all_y)

        # 计算外部过渡点
        margin = 5  # 过渡点距离边界的距离
        pt_insert_1_x = min_x - margin
        pt_insert_1_y = pts_single[-1, 1]
        pt_insert_2_x = min_x - margin
        pt_insert_2_y = pts_single_rotated_1[0, 1] - margin
        pt_insert_3_x = min_x - margin
        pt_insert_3_y = pts_single_rotated_1[-1, 1] - margin
        pt_insert_4_x = min_x - margin
        pt_insert_4_y = pts_single_rotated_2[0, 1]
        pt_insert_5_x = min_x - margin
        pt_insert_5_y = pts_single_rotated_2[-1, 1]
        pt_insert_6_x = min_x - margin
        pt_insert_6_y = pts_single[0, 1]

        # 构建完整的点序列
        pts_x_single = np.hstack((
            pts_single[:, 0],
            [pt_insert_1_x, pt_insert_2_x],
            pts_single_rotated_1[:, 0],
            [pt_insert_3_x, pt_insert_4_x],
            pts_single_rotated_2[:, 0],
            [pt_insert_5_x, pt_insert_6_x]
        ))

        pts_y_single = np.hstack((
            pts_single[:, 1],
            [pt_insert_1_y, pt_insert_2_y],
            pts_single_rotated_1[:, 1],
            [pt_insert_3_y, pt_insert_4_y],
            pts_single_rotated_2[:, 1],
            [pt_insert_5_y, pt_insert_6_y]
        ))
        pts_x = pts_x_single
        pts_y = pts_y_single
        for i in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)
        # 组合最终点集（添加中心点）
        final_pts = np.column_stack((pts_x, pts_y))
        # 后处理
        final_pts = Path_fill(final_pts, max_dis=max_dis * 5)  # 调整填充参数
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_bell_pattern():
    """生成铃铛图案点集，包含参数输入界面"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Bell parameter settings")
    layout = QtWidgets.QFormLayout(dialog)
    # 添加参数输入框
    params = {
        "circle_number": QtWidgets.QLineEdit("20"),
        "side_offset": QtWidgets.QLineEdit("10"),
        "radius": QtWidgets.QLineEdit("2"),
        "max_dis": QtWidgets.QLineEdit("0.1"),
        "cycle_number": QtWidgets.QLineEdit("2")
    }
    for name, widget in params.items():
        layout.addRow(name, widget)
    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])
    try:
        # 获取参数值
        circle_number = int(params["circle_number"].text())
        side_offset = float(params["side_offset"].text())
        radius = float(params["radius"].text())
        max_dis = float(params["max_dis"].text())
        cycle_number = int(params["cycle_number"].text())
        # 计算衍生参数
        alternate = sqrt(3) / 2 * radius
        row_dis = sqrt(3) * radius
        # 初始化点集
        pts_x_single = np.array([0.0])
        pts_y_single = np.array([0.0])
        # 生成基础图案
        for i in range(int(circle_number / 2)):
            for j in range(circle_number):
                center_x = side_offset + (0.5 + j) * radius
                center_y = 2 * i * row_dis + (-1) ** (j + 1) * alternate
                start_angle = 2 / 3 * pi * (-1) ** j
                stop_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] + side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
            for j in range(circle_number):
                center_x = side_offset + circle_number * radius - (0.5 + j) * radius
                center_y = (2 * i + 1) * row_dis + (-1) ** (j + 1) * alternate
                stop_angle = 2 / 3 * pi * (-1) ** j
                start_angle = 1 / 3 * pi * (-1) ** j
                arc_x, arc_y = arc(center_x, center_y, radius, start_angle,
                                   stop_angle, max_dis)
                pts_x_single = np.hstack((pts_x_single, arc_x))
                pts_y_single = np.hstack((pts_y_single, arc_y))
            x1, y1 = pts_x_single[-1] - side_offset, pts_y_single[-1]
            x2, y2 = x1, y1 + row_dis
            pts_x_single = np.hstack((pts_x_single, [x1, x2]))
            pts_y_single = np.hstack((pts_y_single, [y1, y2]))
        pts_single = np.column_stack((pts_x_single, pts_y_single))

        cx = side_offset + (circle_number / 2 - 0.5) * radius
        cy = -0.5 * alternate + ((1 + circle_number / 2) / 2 - 1) * 2 * row_dis
        center = (cx, cy)
        pts_single_rotated_1 = rotate_points(pts_single, pi / 3, center)
        pts_single_rotated_2 = rotate_points(pts_single, -pi / 3, center)

        # 计算边界框
        all_x = np.concatenate([pts_single[:, 0], pts_single_rotated_1[:, 0], pts_single_rotated_2[:, 0]])
        all_y = np.concatenate([pts_single[:, 1], pts_single_rotated_1[:, 1], pts_single_rotated_2[:, 1]])
        min_x, max_x = np.min(all_x), np.max(all_x)
        min_y, max_y = np.min(all_y), np.max(all_y)

        # 计算外部过渡点
        margin = 5  # 过渡点距离边界的距离
        pt_insert_1_x = min_x - margin
        pt_insert_1_y = pts_single[-1, 1]
        pt_insert_2_x = min_x - margin
        pt_insert_2_y = pts_single_rotated_1[0, 1] - margin
        pt_insert_3_x = min_x - margin
        pt_insert_3_y = pts_single_rotated_1[-1, 1] - margin
        pt_insert_4_x = min_x - margin
        pt_insert_4_y = pts_single_rotated_2[0, 1]
        pt_insert_5_x = min_x - margin
        pt_insert_5_y = pts_single_rotated_2[-1, 1]
        pt_insert_6_x = min_x - margin
        pt_insert_6_y = pts_single[0, 1]

        # 构建完整的点序列
        pts_x_single = np.hstack((
            pts_single[:, 0],
            [pt_insert_1_x, pt_insert_2_x],
            pts_single_rotated_1[:, 0],
            [pt_insert_3_x, pt_insert_4_x],
            pts_single_rotated_2[:, 0],
            [pt_insert_5_x, pt_insert_6_x]
        ))

        pts_y_single = np.hstack((
            pts_single[:, 1],
            [pt_insert_1_y, pt_insert_2_y],
            pts_single_rotated_1[:, 1],
            [pt_insert_3_y, pt_insert_4_y],
            pts_single_rotated_2[:, 1],
            [pt_insert_5_y, pt_insert_6_y]
        ))
        # 组合最终点集
        pts_x = pts_x_single
        pts_y = pts_y_single
        for i in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)
        # 组合最终点集（添加中心点）
        final_pts = np.column_stack((pts_x, pts_y))
        # 后处理
        final_pts = Path_fill(remove_adjacent_duplicates(final_pts), max_dis)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_coin_pattern():
    """生成硬币图案点集，包含参数输入界面"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("cion parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框
    params = {
        "a": QtWidgets.QLineEdit("10"),
        "row_number": QtWidgets.QLineEdit("15"),  # 4n+1形式
        "col_number": QtWidgets.QLineEdit("10"),  # 2*(n+1)形式
        "max_dis": QtWidgets.QLineEdit("1"),
        "cycle_number": QtWidgets.QLineEdit("2")
    }
    for name, widget in params.items():
        layout.addRow(name, widget)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])
    try:
        # 获取参数值
        a = float(params["a"].text())
        row_number = int(params["row_number"].text())
        col_number = int(params["col_number"].text())
        max_dis = float(params["max_dis"].text())
        cycle_number = int(params["cycle_number"].text())
        # 计算旋转中心
        center_x = col_number / 2 * (1 + sqrt(3)) * a - 0.5 * sqrt(3) * a
        center_y = (row_number - 1) / 4 * (1 + sqrt(3)) * a
        # 初始化点集
        pts_x, pts_y = np.array([]), np.array([])
        # 生成基本三角形单元
        for i in range(row_number):
            # 上半部分三角形
            for j in range(col_number):
                if i % 2 == 0:
                    pt_1_x = (1 + sqrt(3)) * a * j
                else:
                    pt_1_x = (1 + sqrt(3)) * a * j - 0.5 * (sqrt(3) + 1) * a

                pt_1_y = 0.5 * (1 + sqrt(3)) * a * i
                pt_2_x = pt_1_x + a
                pt_2_y = pt_1_y
                pt_3_x = pt_2_x + 0.5 * sqrt(3) * a
                pt_3_y = pt_2_y + 0.5 * a
                pts_x = np.append(pts_x, [pt_1_x, pt_2_x, pt_3_x])
                pts_y = np.append(pts_y, [pt_1_y, pt_2_y, pt_3_y])
            # 下半部分三角形
            for k in range(col_number):
                pt_1_x = pts_x[-1] - 0.5 * sqrt(3) * a
                pt_1_y = 0.5 * (1 + sqrt(3)) * a * i
                pt_2_x = pt_1_x - a
                pt_2_y = pt_1_y
                pt_3_x = pt_2_x - 0.5 * sqrt(3) * a
                pt_3_y = pt_2_y - 0.5 * a
                pts_x = np.append(pts_x, [pt_1_x, pt_2_x, pt_3_x])
                pts_y = np.append(pts_y, [pt_1_y, pt_2_y, pt_3_y])

        # 将原点移至图形中心
        pts_x = pts_x - center_x
        pts_y = pts_y - center_y

        # 逆时针旋转90°得到取向2
        rotated_x = pts_x * cos(pi / 2) - pts_y * sin(pi / 2)
        rotated_y = pts_x * sin(pi / 2) + pts_y * cos(pi / 2)
        # 插入过渡点
        pt_insert_1_x = pts_x[-1] - (1 + sqrt(3)) * a
        pt_insert_1_y = pts_y[-1]
        pt_insert_2_x = pt_insert_1_x
        pt_insert_2_y = rotated_y[0]
        pt_insert_3_x = rotated_x[-1]
        pt_insert_3_y = rotated_y[-1] - (1 + sqrt(3)) * a
        pt_insert_4_x = pts_x[0]
        pt_insert_4_y = pt_insert_3_y

        # 合并原始点和旋转点
        pts_x = np.append(pts_x, [pt_insert_1_x, pt_insert_2_x])
        pts_y = np.append(pts_y, [pt_insert_1_y, pt_insert_2_y])
        rotated_x = np.append(rotated_x, [pt_insert_3_x, pt_insert_4_x])
        rotated_y = np.append(rotated_y, [pt_insert_3_y, pt_insert_4_y])
        # 组合最终点集
        final_x = np.hstack((pts_x, rotated_x))
        final_y = np.hstack((pts_y, rotated_y))
        # 循环复制
        if cycle_number > 1:
            base_x, base_y = final_x.copy(), final_y.copy()
            for _ in range(cycle_number - 1):
                final_x = np.append(final_x, base_x)
                final_y = np.append(final_y, base_y)
        # 组合点集并进行后处理
        final_pts = np.column_stack((final_x, final_y))

        final_pts = Path_fill(remove_adjacent_duplicates(final_pts), max_dis)
        return final_pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])




def generate_mosaic_pattern4():
    """生成镶嵌结构4图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_4 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("20")
    row_number_edit = QtWidgets.QLineEdit("12")
    col_number_edit = QtWidgets.QLineEdit("12")
    max_dis_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("a:", a_edit)
    layout.addRow("Row_number(2n):", row_number_edit)
    layout.addRow("Col_number(2n):", col_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心（与参考脚本一致）
        center_x = 2 * a * row_number / 2 + 2.5 * a * col_number / 2 - a
        center_y = sqrt(3) * a * row_number / 2 - 0.5 * sqrt(3) * a * col_number / 2
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集（与参考脚本一致）
        for i in range(row_number):
            for j in range(col_number):
                pt_1_x = 2 * a * i + 2.5 * a * j
                pt_1_y = sqrt(3) * a * i - 0.5 * sqrt(3) * a * j
                pt_2_x = pt_1_x + 2 * a
                pt_2_y = pt_1_y
                pts_single_x = np.append(pts_single_x, pt_1_x)
                pts_single_x = np.append(pts_single_x, pt_2_x)
                pts_single_y = np.append(pts_single_y, pt_1_y)
                pts_single_y = np.append(pts_single_y, pt_2_y)
            for k in range(col_number):
                pt_1_x = 2 * a * i + col_number * 2.5 * a - 2.5 * a * k
                pt_1_y = sqrt(3) * a * i + (-col_number + 2 + k) * 0.5 * sqrt(3) * a
                pt_2_x = pt_1_x - 2 * a
                pt_2_y = pt_1_y
                pts_single_x = np.append(pts_single_x, pt_1_x)
                pts_single_x = np.append(pts_single_x, pt_2_x)
                pts_single_y = np.append(pts_single_y, pt_1_y)
                pts_single_y = np.append(pts_single_y, pt_2_y)
        pts_single_append_x = np.array([0])
        pts_single_append_y = np.array([0])
        # 添加附加线条
        for i in range(row_number):
            for j in range(col_number):
                if i % 2 == 0:
                    pt_1_x = 2 * a * i + 2.5 * a * j + a
                    pt_1_y = sqrt(3) * a * i - 0.5 * sqrt(3) * a * j
                    pt_2_x = pt_1_x + 2 * a
                    pt_2_y = pt_1_y
                else:
                    pt_1_x = 2 * a * i + 2.5 * a * (col_number - j) + 1.5 * a
                    pt_1_y = sqrt(3) * a * i - 0.5 * sqrt(3) * a * (col_number - j - 1)
                    pt_2_x = pt_1_x - 2 * a
                    pt_2_y = pt_1_y
                pts_single_append_x = np.append(pts_single_append_x, pt_1_x)
                pts_single_append_x = np.append(pts_single_append_x, pt_2_x)
                pts_single_append_y = np.append(pts_single_append_y, pt_1_y)
                pts_single_append_y = np.append(pts_single_append_y, pt_2_y)

        # 原点移动至图形中心（一定在某六边形中心），以便旋转。
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        pts_single_append_x = pts_single_append_x - center_x
        pts_single_append_y = pts_single_append_y - center_y
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_1, pts_single_y_rotated_1 = pts_single_x * cos(pi / 3) - pts_single_y * sin(pi / 3), \
                                                         pts_single_x * sin(pi / 3) + pts_single_y * cos(pi / 3)
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_2, pts_single_y_rotated_2 = pts_single_x * cos(2 * pi / 3) - pts_single_y * sin(
            2 * pi / 3), \
                                                         pts_single_x * sin(2 * pi / 3) + pts_single_y * cos(2 * pi / 3)
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_append_1, pts_single_y_rotated_append_1 = pts_single_append_x * cos(
            pi / 3) - pts_single_append_y * sin(pi / 3), \
                                                                       pts_single_append_x * sin(
                                                                           pi / 3) + pts_single_append_y * cos(pi / 3)
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_append_2, pts_single_y_rotated_append_2 = pts_single_append_x * cos(
            2 * pi / 3) - pts_single_append_y * sin(2 * pi / 3), \
                                                                       pts_single_append_x * sin(
                                                                           2 * pi / 3) + pts_single_append_y * cos(
                                                                           2 * pi / 3)

        # 插入过渡点，避免过渡线影响内部结构
        pt_insert_1_x = pts_single_x[0] - 2 * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        pt_insert_2_y = pts_single_y_rotated_1[0]
        pt_insert_3_x = pt_insert_1_x
        pt_insert_3_y = pts_single_y_rotated_1[-1]
        pt_insert_4_x = pt_insert_3_x
        pt_insert_4_y = pts_single_y_rotated_2[0]
        pt_insert_5_x = pts_single_append_x[0]
        pt_insert_5_y = pts_single_y_rotated_2[-1]
        pt_insert_6_x = pt_insert_5_x
        pt_insert_6_y = pt_insert_5_y
        pt_insert_7_x = pt_insert_1_x
        pt_insert_7_y = pts_single_append_y[-1]
        pt_insert_8_x = pt_insert_7_x
        pt_insert_8_y = pts_single_y_rotated_append_1[0]
        pt_insert_9_x = pt_insert_1_x
        pt_insert_9_y = pts_single_y_rotated_append_1[-1]
        pt_insert_10_x = pt_insert_9_x
        pt_insert_10_y = pts_single_y_rotated_append_2[0]
        pt_insert_11_x = pts_single_x[0]
        pt_insert_11_y = pts_single_y_rotated_append_2[-1]
        pt_insert_12_x = pt_insert_11_x
        pt_insert_12_y = pt_insert_11_y
        pts_single_x = np.append(np.append(pts_single_x, pt_insert_1_x), pt_insert_2_x)
        pts_single_y = np.append(np.append(pts_single_y, pt_insert_1_y), pt_insert_2_y)
        pts_single_x_rotated_1 = np.append(np.append(pts_single_x_rotated_1, pt_insert_3_x), pt_insert_4_x)
        pts_single_y_rotated_1 = np.append(np.append(pts_single_y_rotated_1, pt_insert_3_y), pt_insert_4_y)
        pts_single_x_rotated_2 = np.append(np.append(pts_single_x_rotated_2, pt_insert_5_x), pt_insert_6_x)
        pts_single_y_rotated_2 = np.append(np.append(pts_single_y_rotated_2, pt_insert_5_y), pt_insert_6_y)
        pts_single_append_x = np.append(np.append(pts_single_append_x, pt_insert_7_x), pt_insert_8_x)
        pts_single_append_y = np.append(np.append(pts_single_append_y, pt_insert_7_y), pt_insert_8_y)
        pts_single_x_rotated_append_1 = np.append(np.append(pts_single_x_rotated_append_1, pt_insert_9_x),
                                                  pt_insert_10_x)
        pts_single_y_rotated_append_1 = np.append(np.append(pts_single_y_rotated_append_1, pt_insert_9_y),
                                                  pt_insert_10_y)
        pts_single_x_rotated_append_2 = np.append(np.append(pts_single_x_rotated_append_2, pt_insert_11_x),
                                                  pt_insert_12_x)
        pts_single_y_rotated_append_2 = np.append(np.append(pts_single_y_rotated_append_2, pt_insert_11_y),
                                                  pt_insert_12_y)

        pts_single_x = np.hstack((pts_single_x, pts_single_x_rotated_1, pts_single_x_rotated_2))
        pts_single_y = np.hstack((pts_single_y, pts_single_y_rotated_1, pts_single_y_rotated_2))
        # 组合最终点集
        final_pts = np.column_stack((pts_single_x, pts_single_y))
        # 后处理（路径填充和去重）
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])



def generate_mosaic_pattern5():
    """生成镶嵌结构5图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_5 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("13")
    col_number_edit = QtWidgets.QLineEdit("20")
    max_dis_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("a:", a_edit)
    layout.addRow("Row_number(2n+1):", row_number_edit)
    layout.addRow("Col_number(2n):", col_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心（与参考脚本一致）
        center_x = col_number / 2 * sqrt(3) / 2 * a
        center_y = 0.5 * (row_number - 1) * 1.5 * a
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集（与参考脚本一致）
        for j in range(col_number):
            for i in range(row_number):
                if j % 2 == 0:
                    if i % 4 == 0 or i % 4 == 3:
                        pt_x = j / 2 * a + 0.5 * a
                    else:
                        pt_x = j / 2 * a
                    pt_y = i * a
                else:
                    if i % 4 == 0 or i % 4 == 1:
                        pt_x = (j + 1) / 2 * a - 0.5 * a
                    else:
                        pt_x = (j + 1) / 2 * a
                    pt_y = (row_number - i - 1) * a
                pts_single_x = np.append(pts_single_x, pt_x)
                pts_single_y = np.append(pts_single_y, pt_y)
        for i in range(row_number):
            for j in range(col_number // 2 + 1):
                if i % 2 == 0:
                    pt_x = j * a
                else:
                    pt_x = ((col_number // 2 + 1) - j - 1) * a
                pt_y = i * a
                pts_single_x = np.append(pts_single_x, pt_x)
                pts_single_y = np.append(pts_single_y, pt_y)
        # 原点移动至图形中心（一定在某八边形形中心），以便旋转。
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        # 组合最终点集
        final_pts = np.column_stack((pts_single_x, pts_single_y))
        # 后处理（路径填充和去重）
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])




def generate_mosaic_pattern6():
    """生成镶嵌结构6图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_6 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("20")
    col_number_edit = QtWidgets.QLineEdit("10")
    cycle_number_edit = QtWidgets.QLineEdit("2")
    max_dis_edit = QtWidgets.QLineEdit("0.2")
    layout.addRow("a:", a_edit)
    layout.addRow("Row_number(2n):", row_number_edit)
    layout.addRow("Col_number(2n):", col_number_edit)
    layout.addRow("Cycle_number:", cycle_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心（与参考脚本一致）
        center_x = (1 + sqrt(3)) * a * col_number / 2 + 0.5 * a
        center_y = (1 + 0.5 * sqrt(3)) * a + (3 + sqrt(3)) * a * (row_number / 4 - 1) / 2
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集（与参考脚本一致）
        for i in range(row_number):
            if i % 4 == 0:
                for j in range(col_number):
                    pt_1_x = (1 + sqrt(3)) * a * j
                    pt_1_y = (3 + sqrt(3)) * a * i / 4
                    pt_2_x = pt_1_x + a
                    pt_2_y = pt_1_y
                    pt_3_x = pt_2_x + 0.5 * sqrt(3) * a
                    pt_3_y = pt_2_y + 0.5 * a
                    pts_single_x = np.append(pts_single_x, pt_1_x)
                    pts_single_x = np.append(pts_single_x, pt_2_x)
                    pts_single_x = np.append(pts_single_x, pt_3_x)
                    pts_single_y = np.append(pts_single_y, pt_1_y)
                    pts_single_y = np.append(pts_single_y, pt_2_y)
                    pts_single_y = np.append(pts_single_y, pt_3_y)
            elif i % 4 == 1:
                for j in range(col_number):
                    pt_1_x = (1 + sqrt(3)) * a * (col_number - j) + a - 0.5 * (1 + sqrt(3)) * a
                    pt_1_y = (3 + sqrt(3)) * a * (i - 1) / 4 + 0.5 * (sqrt(3) + 1) * a
                    pt_2_x = pt_1_x - a
                    pt_2_y = pt_1_y
                    pt_3_x = pt_2_x - 0.5 * sqrt(3) * a
                    pt_3_y = pt_2_y - 0.5 * a
                    pts_single_x = np.append(pts_single_x, pt_1_x)
                    pts_single_x = np.append(pts_single_x, pt_2_x)
                    pts_single_x = np.append(pts_single_x, pt_3_x)
                    pts_single_y = np.append(pts_single_y, pt_1_y)
                    pts_single_y = np.append(pts_single_y, pt_2_y)
                    pts_single_y = np.append(pts_single_y, pt_3_y)
            elif i % 4 == 2:
                for j in range(col_number):
                    pt_1_x = (1 + sqrt(3)) * a * j + 0.5 * (sqrt(3) + 1) * a
                    pt_1_y = (3 + sqrt(3)) * a * (i - 2) / 4 + 0.5 * (sqrt(3) + 1) * a + a
                    pt_2_x = pt_1_x + a
                    pt_2_y = pt_1_y
                    pt_3_x = pt_2_x + 0.5 * sqrt(3) * a
                    pt_3_y = pt_2_y + 0.5 * a
                    pts_single_x = np.append(pts_single_x, pt_1_x)
                    pts_single_x = np.append(pts_single_x, pt_2_x)
                    pts_single_x = np.append(pts_single_x, pt_3_x)
                    pts_single_y = np.append(pts_single_y, pt_1_y)
                    pts_single_y = np.append(pts_single_y, pt_2_y)
                    pts_single_y = np.append(pts_single_y, pt_3_y)
            elif i % 4 == 3:
                for j in range(col_number):
                    pt_1_x = (1 + sqrt(3)) * a * (col_number - j) + a
                    pt_1_y = (3 + sqrt(3)) * a * (i - 3) / 4 + (2 + sqrt(3)) * a
                    pt_2_x = pt_1_x - a
                    pt_2_y = pt_1_y
                    pt_3_x = pt_2_x - 0.5 * sqrt(3) * a
                    pt_3_y = pt_2_y - 0.5 * a
                    pts_single_x = np.append(pts_single_x, pt_1_x)
                    pts_single_x = np.append(pts_single_x, pt_2_x)
                    pts_single_x = np.append(pts_single_x, pt_3_x)
                    pts_single_y = np.append(pts_single_y, pt_1_y)
                    pts_single_y = np.append(pts_single_y, pt_2_y)
                    pts_single_y = np.append(pts_single_y, pt_3_y)
        # 原点移动至图形中心（一定在某六边形中心），以便旋转。
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_1, pts_single_y_rotated_1 = pts_single_x * cos(pi / 3) - pts_single_y * sin(pi / 3), \
                                                         pts_single_x * sin(pi / 3) + pts_single_y * cos(pi / 3)
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_2, pts_single_y_rotated_2 = pts_single_x * cos(2 * pi / 3) - pts_single_y * sin(
            2 * pi / 3), \
                                                         pts_single_x * sin(2 * pi / 3) + pts_single_y * cos(2 * pi / 3)
        ############################
        # plt.plot(pts_single_x, pts_single_y)
        ############################
        # 插入过渡点，避免过渡线影响内部结构
        pt_insert_1_x = pts_single_x[-1] - 2 * (1 + sqrt(3)) * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        pt_insert_2_y = pts_single_y_rotated_1[0]
        pt_insert_3_x = pt_insert_2_x
        pt_insert_3_y = pt_insert_2_y
        pt_insert_4_x = pts_single_x_rotated_2[0]
        pt_insert_4_y = pt_insert_2_y
        pt_insert_5_x = pts_single_x[0]
        pt_insert_5_y = pts_single_y_rotated_2[-1]
        pt_insert_6_x = pts_single_x[0]
        pt_insert_6_y = pts_single_y[0]
        pts_single_x = np.append(np.append(pts_single_x, pt_insert_1_x), pt_insert_2_x)
        pts_single_y = np.append(np.append(pts_single_y, pt_insert_1_y), pt_insert_2_y)
        pts_single_x_rotated_1 = np.append(np.append(pts_single_x_rotated_1, pt_insert_3_x), pt_insert_4_x)
        pts_single_y_rotated_1 = np.append(np.append(pts_single_y_rotated_1, pt_insert_3_y), pt_insert_4_y)
        pts_single_x_rotated_2 = np.append(np.append(pts_single_x_rotated_2, pt_insert_5_x), pt_insert_6_x)
        pts_single_y_rotated_2 = np.append(np.append(pts_single_y_rotated_2, pt_insert_5_y), pt_insert_6_y)
        pts_single_x = np.hstack((pts_single_x, pts_single_x_rotated_1, pts_single_x_rotated_2))
        pts_single_y = np.hstack((pts_single_y, pts_single_y_rotated_1, pts_single_y_rotated_2))
        cycle_number = 2  # 可变
        # cycle_number 是周期数，不是层数，层数=3*周期数
        pts_x = pts_single_x
        pts_y = pts_single_y
        for i in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_single_x)
            pts_y = np.append(pts_y, pts_single_y)
        # 组合最终点集
        final_pts = np.column_stack((pts_x, pts_y))
        # 后处理（路径填充和去重）
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])



def generate_mosaic_pattern7():
    """生成镶嵌结构7图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_7 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("24")
    col_number_edit = QtWidgets.QLineEdit("48")
    max_dis_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("a:", a_edit)
    layout.addRow("Row_number(4n):", row_number_edit)
    layout.addRow("Col_number(4n):", col_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心（与参考脚本一致）
        center_x = col_number * 0.25 * (a + a * 0.5 * sqrt(2)) - 0.5 * a
        center_y = (row_number * 0.5 - 1) * (a + a * 0.5 * sqrt(2)) + 0.5 * a + 0.25 * a * sqrt(2)
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集（与参考脚本一致）
        for i in range(row_number):
            for j in range(col_number):
                if i % 2 == 0:
                    if j % 2 == 0:
                        pt_x = (a + a * 0.5 * sqrt(2)) * j * 0.5
                    else:
                        pt_x = a * 0.5 * sqrt(2) + (a + a * 0.5 * sqrt(2)) * (j - 1) * 0.5
                else:
                    if j % 2 == 0:
                        pt_x = (a + a * 0.5 * sqrt(2)) * (col_number - j) * 0.5
                    else:
                        pt_x = a * 0.5 * sqrt(2) + (a + a * 0.5 * sqrt(2)) * (col_number - 1 - j) * 0.5
                pt_y = (-1) ** (i + j + 1) * (-1) ** (int((i + j) * 0.5)) * a * 0.25 * sqrt(2) * (-1) ** (
                    int(i / 2)) + (a + a * 0.5 * sqrt(2)) * i
                pts_single_x = np.append(pts_single_x, pt_x)
                pts_single_y = np.append(pts_single_y, pt_y)
        # 原点移动至图形中心（一定在某八边形形中心），以便旋转。
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        # 插入过渡点，避免过渡线影响内部结构
        pt_insert_1_x = pts_single_x[-1] - col_number * sqrt(3) / 40 * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        # 旋转90度
        pts_single_x_rotated_1, pts_single_y_rotated_1 = pts_single_x * cos(pi / 2) - pts_single_y * sin(pi / 2), \
                                                         pts_single_x * sin(pi / 2) + pts_single_y * cos(pi / 2)
        pt_insert_2_y = pts_single_y_rotated_1[1]
        # 所有取向与过渡点拼接
        pts_single_x = np.hstack(
            (pts_single_x, np.array(pt_insert_1_x), np.array(pt_insert_2_x), pts_single_x_rotated_1))
        pts_single_y = np.hstack(
            (pts_single_y, np.array(pt_insert_1_y), np.array(pt_insert_2_y), pts_single_y_rotated_1))
        # 组合最终点集
        final_pts = np.column_stack((pts_single_x, pts_single_y))
        # 后处理（路径填充和去重）
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])



def generate_mosaic_pattern8():
    """生成镶嵌结构8图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_8 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("12")
    col_number_edit = QtWidgets.QLineEdit("37")
    max_dis_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("a:", a_edit)
    layout.addRow("Row_number(4n):", row_number_edit)
    layout.addRow("Col_number(8n+5):", col_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心（与参考脚本一致）
        center_x = (col_number - 1) / 4 * (2 * a + a * sqrt(3)) / 2 + 0.5 * a
        center_y = (row_number - 2) / 2 * (1.5 * a + a * sqrt(3)) + a + 0.5 * a * sqrt(3)
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集（与参考脚本一致）
        for i in range(row_number):
            for j in range(col_number):
                if i % 2 == 0:
                    if j % 4 == 0:
                        pt_x = (2 * a + a * sqrt(3)) * j / 4
                        pt_y = i * (1.5 * a + a * sqrt(3))
                    elif (j - 1) % 4 == 0:
                        pt_x = (2 * a + a * sqrt(3)) * (j - 1) / 4 + a
                        pt_y = i * (1.5 * a + a * sqrt(3))
                    elif (j - 2) % 4 == 0:
                        pt_x = (2 * a + a * sqrt(3)) * (j - 2) / 4 + a + 0.5 * a * sqrt(3)
                        pt_y = i * (1.5 * a + a * sqrt(3)) + 0.5 * a
                    else:
                        pt_x = (2 * a + a * sqrt(3)) * (j - 3) / 4 + 2 * a + 0.5 * a * sqrt(3)
                        pt_y = i * (1.5 * a + a * sqrt(3)) + 0.5 * a
                else:
                    if j % 4 == 0:
                        pt_x = (2 * a + a * sqrt(3)) * (col_number - j - 1) / 4 + a + 0.5 * a * sqrt(3)
                        pt_y = i * (1.5 * a + a * sqrt(3))
                    elif (j - 1) % 4 == 0:
                        pt_x = (2 * a + a * sqrt(3)) * (col_number - j) / 4 + a
                        pt_y = i * (1.5 * a + a * sqrt(3)) + 0.5 * a
                    elif (j - 2) % 4 == 0:
                        pt_x = (2 * a + a * sqrt(3)) * (col_number - j + 1) / 4
                        pt_y = i * (1.5 * a + a * sqrt(3)) + 0.5 * a
                    else:
                        pt_x = (2 * a + a * sqrt(3)) * (col_number - j + 2) / 4 - 0.5 * a * sqrt(3)
                        pt_y = i * (1.5 * a + a * sqrt(3))
                pts_single_x = np.append(pts_single_x, pt_x)
                pts_single_y = np.append(pts_single_y, pt_y)
        # 原点移动至图形中心（一定在某八边形形中心），以便旋转。
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        # 插入过渡点，避免过渡线影响内部结构
        pt_insert_1_x = pts_single_x[-1] - col_number * sqrt(3) / 4 * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_1, pts_single_y_rotated_1 = pts_single_x * cos(pi / 3) - pts_single_y * sin(pi / 3), \
                                                         pts_single_x * sin(pi / 3) + pts_single_y * cos(pi / 3)
        pt_insert_2_y = pts_single_y_rotated_1[1]
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_2, pts_single_y_rotated_2 = pts_single_x * cos(2 * pi / 3) - pts_single_y * sin(
            2 * pi / 3), \
                                                         pts_single_x * sin(2 * pi / 3) + pts_single_y * cos(2 * pi / 3)
        pt_insert_3_x = pts_single_x_rotated_1[-1]
        pt_insert_3_y = pt_insert_2_y
        pt_insert_4_x = pts_single_x_rotated_2[0]
        pt_insert_4_y = pt_insert_3_y
        # 所有取向与过渡点拼接
        pts_single_x = np.hstack((
                                 pts_single_x, np.array(pt_insert_1_x), np.array(pt_insert_2_x), pts_single_x_rotated_1,
                                 np.array(pt_insert_3_x), np.array(pt_insert_4_x), pts_single_x_rotated_2))
        pts_single_y = np.hstack((
                                 pts_single_y, np.array(pt_insert_1_y), np.array(pt_insert_2_y), pts_single_y_rotated_1,
                                 np.array(pt_insert_3_y), np.array(pt_insert_4_y), pts_single_y_rotated_2))
        # 组合最终点集
        final_pts = np.column_stack((pts_single_x, pts_single_y))
        # 后处理（路径填充和去重）
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])


def generate_mosaic_pattern9():
    """生成镶嵌结构9图案点集，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Tessellation_9 parameter settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框（设置默认值）
    a_edit = QtWidgets.QLineEdit("10")
    row_number_edit = QtWidgets.QLineEdit("16")
    col_number_edit = QtWidgets.QLineEdit("61")
    max_dis_edit = QtWidgets.QLineEdit("0.2")

    layout.addRow("a:", a_edit)
    layout.addRow("Row_number(4n):", row_number_edit)
    layout.addRow("Col_number(6n+1):", col_number_edit)
    layout.addRow("Point_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        a = float(a_edit.text())
        row_number = int(row_number_edit.text())
        col_number = int(col_number_edit.text())
        max_dis = float(max_dis_edit.text())
    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    try:
        # 定位旋转中心（与参考脚本一致）
        center_x = row_number / 4 * (1.5 * a + 0.5 * a * sqrt(3)) + ((col_number - 1) / 6 - 1) * (
                    1.5 * a + 0.5 * a * sqrt(3)) + 0.5 * a
        center_y = row_number / 4 * (1.5 * a + 1.5 * a * sqrt(3))
        pts_single_x = np.array(0)
        pts_single_y = np.array(0)

        # 生成主线条点集（与参考脚本一致）
        for i in range(row_number):
            for j in range(col_number):
                if i % 2 == 0:
                    if j % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * j / 3 + (i / 2) * (a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = a * 0.5 + 0.5 * i * (1.5 * a + 1.5 * a * sqrt(3))
                    elif j % 3 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * j / 3 + (i / 2) * (a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = a + 0.5 * a * sqrt(3) + 0.5 * i * (1.5 * a + 1.5 * a * sqrt(3))
                    elif (j + 1) % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (j + 1) / 3 - a * 0.5 + (i / 2) * (
                                    a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = a * 0.5 + 0.5 * a * sqrt(3) + 0.5 * i * (1.5 * a + 1.5 * a * sqrt(3))
                    elif (j - 1) % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (j - 1) / 3 + a + (i / 2) * (
                                    a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = a * 0.5 + 0.5 * i * (1.5 * a + 1.5 * a * sqrt(3))
                    elif (j + 2) % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (j + 2) / 3 - a * 0.5 - a * 0.5 * sqrt(3) + (
                                    i / 2) * (a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = a + 0.5 * a * sqrt(3) + 0.5 * i * (1.5 * a + 1.5 * a * sqrt(3))
                    else:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (j - 2) / 3 + a * 1.5 + (i / 2) * (
                                    a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = a * 0.5 + 0.5 * a * sqrt(3) + 0.5 * i * (1.5 * a + 1.5 * a * sqrt(3))
                else:
                    if j % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (col_number - j - 1) / 3 + ((i - 1) / 2) * (
                                    a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = (i + 1) / 2 * (1.5 * a + 1.5 * a * sqrt(3)) - a - 0.5 * a * sqrt(3)
                    elif j % 3 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (col_number - j - 1) / 3 + ((i - 1) / 2) * (
                                    a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = (i + 1) / 2 * (1.5 * a + 1.5 * a * sqrt(3)) - 0.5 * a
                    elif (j + 1) % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (col_number - j - 2) / 3 + a + ((i - 1) / 2) * (
                                    a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = (i + 1) / 2 * (1.5 * a + 1.5 * a * sqrt(3)) - a - 0.5 * a * sqrt(3)
                    elif (j - 1) % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (col_number - j) / 3 - a * 0.5 * sqrt(3) + (
                                    (i - 1) / 2) * (a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = (i + 1) / 2 * (1.5 * a + 1.5 * a * sqrt(3)) - 0.5 * a - 0.5 * a * sqrt(3)
                    elif (j + 2) % 6 == 0:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (col_number - j - 3) / 3 + a + a * 0.5 * sqrt(3) + (
                                    (i - 1) / 2) * (a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = (i + 1) / 2 * (1.5 * a + 1.5 * a * sqrt(3)) - 0.5 * a - 0.5 * a * sqrt(3)
                    else:
                        pt_x = (a + a * 0.5 + a * 0.5 * sqrt(3)) * (col_number - j + 1) / 3 - a * 0.5 - a * 0.5 * sqrt(
                            3) + ((i - 1) / 2) * (a + a * 0.5 + a * 0.5 * sqrt(3))
                        pt_y = (i + 1) / 2 * (1.5 * a + 1.5 * a * sqrt(3)) - 0.5 * a
                pts_single_x = np.append(pts_single_x, pt_x)
                pts_single_y = np.append(pts_single_y, pt_y)
        # 原点移动至图形中心（一定在某八边形形中心），以便旋转。
        pts_single_x = pts_single_x - center_x
        pts_single_y = pts_single_y - center_y
        # 插入过渡点，避免过渡线影响内部结构
        pt_insert_1_x = pts_single_x[-1] - col_number * sqrt(3) / 4 * a
        pt_insert_1_y = pts_single_y[-1]
        pt_insert_2_x = pt_insert_1_x
        # 逆时针旋转60°得到取向2
        pts_single_x_rotated_1, pts_single_y_rotated_1 = pts_single_x * cos(pi / 3) - pts_single_y * sin(pi / 3), \
                                                         pts_single_x * sin(pi / 3) + pts_single_y * cos(pi / 3)
        pt_insert_2_y = pts_single_y_rotated_1[1]
        # 逆时针旋转120°得到取向3
        pts_single_x_rotated_2, pts_single_y_rotated_2 = pts_single_x * cos(2 * pi / 3) - pts_single_y * sin(
            2 * pi / 3), \
                                                         pts_single_x * sin(2 * pi / 3) + pts_single_y * cos(2 * pi / 3)
        pt_insert_3_x = pts_single_x_rotated_1[-1]
        pt_insert_3_y = pt_insert_2_y
        pt_insert_4_x = pts_single_x_rotated_2[0]
        pt_insert_4_y = pt_insert_3_y
        # 所有取向与过渡点拼接
        pts_single_x = np.hstack((
                                 pts_single_x, np.array(pt_insert_1_x), np.array(pt_insert_2_x), pts_single_x_rotated_1,
                                 np.array(pt_insert_3_x), np.array(pt_insert_4_x), pts_single_x_rotated_2))
        pts_single_y = np.hstack((
                                 pts_single_y, np.array(pt_insert_1_y), np.array(pt_insert_2_y), pts_single_y_rotated_1,
                                 np.array(pt_insert_3_y), np.array(pt_insert_4_y), pts_single_y_rotated_2))
        # 组合最终点集
        final_pts = np.column_stack((pts_single_x, pts_single_y))
        # 后处理（路径填充和去重）
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])


def generate_gradient_pattern():
    """使用自定义数组或公式生成图案的主函数"""
    # 创建Qt应用实例
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Custom Array Pattern Settings")
    dialog.setMinimumWidth(500)
    layout = QtWidgets.QFormLayout(dialog)

    # 添加选项卡 widget
    tab_widget = QtWidgets.QTabWidget()
    array_tab = QtWidgets.QWidget()
    formula_tab = QtWidgets.QWidget()
    tab_widget.addTab(array_tab, "Array Input")
    tab_widget.addTab(formula_tab, "Formula Input")

    # 数组输入选项卡
    array_layout = QtWidgets.QFormLayout(array_tab)
    primary_array_edit = QtWidgets.QLineEdit("1,2,3,4,5,6")
    secondary_array_edit = QtWidgets.QLineEdit("6,5,4,3,2,1")
    array_layout.addRow("Primary_sfs (comma-separated):", primary_array_edit)
    array_layout.addRow("Secondary_sfs (comma-separated):", secondary_array_edit)

    # 公式输入选项卡
    formula_layout = QtWidgets.QFormLayout(formula_tab)
    primary_formula_edit = QtWidgets.QLineEdit("np.linspace(1, 10, 6)")
    secondary_formula_edit = QtWidgets.QLineEdit("np.linspace(10, 1, 6)")
    formula_layout.addRow("Primary_sfs formula:", primary_formula_edit)
    formula_layout.addRow("Secondary_sfs formula:", secondary_formula_edit)

    # 通用参数
    side_offset_edit = QtWidgets.QLineEdit("1")
    layer_number_edit = QtWidgets.QLineEdit("1")
    max_dis_edit = QtWidgets.QLineEdit("0.1")

    layout.addRow(tab_widget)
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Layer_number:", layer_number_edit)
    layout.addRow("Max_dis:", max_dis_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        side_offset = float(side_offset_edit.text())
        layer_number = int(layer_number_edit.text())
        max_dis = float(max_dis_edit.text())

        # 根据当前选项卡决定使用哪种输入方式
        if tab_widget.currentIndex() == 0:  # 数组输入
            primary_sfs_str = primary_array_edit.text()
            secondary_sfs_str = secondary_array_edit.text()

            # 解析逗号分隔的数组
            primary_sfs = [float(x.strip()) for x in primary_sfs_str.split(',') if x.strip()]
            secondary_sfs = [float(x.strip()) for x in secondary_sfs_str.split(',') if x.strip()]
        else:  # 公式输入
            primary_formula = primary_formula_edit.text()
            secondary_formula = secondary_formula_edit.text()

            # 使用eval执行公式（注意安全性考虑，在实际应用中可能需要更安全的替代方案）
            primary_sfs = eval(primary_formula, {"np": np, "pi": np.pi})
            secondary_sfs = eval(secondary_formula, {"np": np, "pi": np.pi})

            # 确保结果是数组或列表
            if hasattr(primary_sfs, '__iter__'):
                primary_sfs = list(primary_sfs)
            else:
                primary_sfs = [primary_sfs]

            if hasattr(secondary_sfs, '__iter__'):
                secondary_sfs = list(secondary_sfs)
            else:
                secondary_sfs = [secondary_sfs]

        # 验证数组长度是否为偶数且相等
        if len(primary_sfs) % 2 != 0:
            raise ValueError(f"primary_sfs的长度必须是偶数，当前长度为{len(primary_sfs)}")

        if len(secondary_sfs) % 2 != 0:
            raise ValueError(f"secondary_sfs的长度必须是偶数，当前长度为{len(secondary_sfs)}")

        if len(primary_sfs) != len(secondary_sfs):
            raise ValueError(
                f"primary_sfs和secondary_sfs的长度必须相等，当前长度分别为{len(primary_sfs)}和{len(secondary_sfs)}")

    except Exception as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    # 使用variable_sf函数生成点集
    try:
        # 复制variable_sf函数的主要逻辑
        primary_sfs = np.hstack([[0], primary_sfs, [0]])
        secondary_sfs = np.hstack([[0], secondary_sfs, [0]])
        pts_x = np.array([0])
        pts_y = np.array([0])
        cum_primary_sfs = np.cumsum(primary_sfs)
        height = cum_primary_sfs[-1]
        cum_secondary_sfs = np.cumsum(secondary_sfs)
        width = cum_secondary_sfs[-1]

        for layer in range(layer_number):
            for i in range(int(len(primary_sfs) / 2)):
                x1 = 0
                y1 = cum_primary_sfs[2 * i]
                x2 = 2 * side_offset + width
                y2 = y1
                x3 = x2
                y3 = y2 + primary_sfs[2 * i + 1]
                x4 = 0
                y4 = y3
                pts_x = np.hstack([pts_x, x1, x2, x3, x4])
                pts_y = np.hstack([pts_y, y1, y2, y3, y4])
            pts_x = pts_x[:-1]
            pts_y = pts_y[:-1]
            pts_x = np.append(pts_x, pts_x[-1])
            pts_y = np.append(pts_y, pts_y[-1] + side_offset)

            for i in range(int(len(secondary_sfs) / 2)):
                x1 = side_offset + width - cum_secondary_sfs[2 * i]
                y1 = height + side_offset
                x2 = x1
                y2 = -side_offset
                x3 = x1 - secondary_sfs[2 * i + 1]
                y3 = y2
                x4 = x3
                y4 = height + side_offset
                pts_x = np.hstack([pts_x, x1, x2, x3, x4])
                pts_y = np.hstack([pts_y, y1, y2, y3, y4])
            pts_x = pts_x[:-1]
            pts_y = pts_y[:-1]
            pts_x = np.append(pts_x, pts_x[-1] - side_offset)
            pts_y = np.append(pts_y, pts_y[-1])

        # 后处理
        final_pts = np.column_stack((pts_x, pts_y))
        final_pts = Path_fill(points=final_pts, max_dis=max_dis)
        final_pts = remove_adjacent_duplicates(final_pts)
        return final_pts

    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])


def generate_ps_pattern():
    """生成主副方向交叉结构图案，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("PS Pattern Parameter Settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框
    primary_sf_edit = QtWidgets.QLineEdit("1")
    secondary_sf_edit = QtWidgets.QLineEdit("1")
    theta_edit = QtWidgets.QLineEdit("30")  # 角度，用户输入度数
    grid_number_edit = QtWidgets.QLineEdit("12")
    side_offset_edit = QtWidgets.QLineEdit("2")
    secondary_checkbox = QtWidgets.QCheckBox()
    secondary_checkbox.setChecked(True)
    centralized_checkbox = QtWidgets.QCheckBox()
    centralized_checkbox.setChecked(True)
    rotation_angle_edit = QtWidgets.QLineEdit("60")  # 角度，用户输入度数
    max_dis_edit = QtWidgets.QLineEdit("0.1")
    cycle_number_edit = QtWidgets.QLineEdit("1")

    layout.addRow("Primary_sf:", primary_sf_edit)
    layout.addRow("Secondary_sf:", secondary_sf_edit)
    layout.addRow("Theta (°):", theta_edit)
    layout.addRow("Rotation_angle (°):", rotation_angle_edit)
    layout.addRow("Grid_number:", grid_number_edit)
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Include Secondary:", secondary_checkbox)
    layout.addRow("Centralized:", centralized_checkbox)
    layout.addRow("Point_dis:", max_dis_edit)
    layout.addRow("Cycle_number:", cycle_number_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        primary_sf = float(primary_sf_edit.text())
        secondary_sf = float(secondary_sf_edit.text())
        theta_deg = float(theta_edit.text())
        grid_number = int(grid_number_edit.text())
        side_offset = float(side_offset_edit.text())
        secondary = secondary_checkbox.isChecked()
        centralized = centralized_checkbox.isChecked()
        rotation_angle_deg = float(rotation_angle_edit.text())
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())

        # 将角度转换为弧度
        theta = theta_deg * pi / 180
        rotation_angle = rotation_angle_deg * pi / 180

        # 验证参数有效性
        if grid_number <= 0:
            raise ValueError("Grid_number must be positive")

    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    # 生成点集
    try:
        pts_x_single, pts_y_single = ps_intersect(
            primary_sf=primary_sf,
            secondary_sf=secondary_sf,
            theta=theta,
            grid_number=grid_number,
            side_offset=side_offset,
            secondary=secondary,
            centralized=centralized,
            rotation_angle=rotation_angle
        )

        # 扩展周期
        pts_x = pts_x_single.copy()
        pts_y = pts_y_single.copy()
        for _ in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)

        # 后处理
        pts = np.column_stack((pts_x, pts_y))
        pts = Path_fill(points=pts, max_dis=max_dis)
        pts = remove_adjacent_duplicates(pts)
        return pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])



def generate_psdd_pattern():
    """生成主副方向与对角线交叉结构图案，包含参数输入界面"""
    # 创建Qt应用实例（如果尚未存在）
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    # 创建参数输入对话框
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("PSDD Pattern Parameter Settings")
    layout = QtWidgets.QFormLayout(dialog)

    # 添加参数输入框
    primary_sf_edit = QtWidgets.QLineEdit("1")
    secondary_sf_edit = QtWidgets.QLineEdit("1")
    theta_edit = QtWidgets.QLineEdit("30")  # 角度，用户输入度数
    grid_number_edit = QtWidgets.QLineEdit("12")
    side_offset_edit = QtWidgets.QLineEdit("2")
    diagonal_secondary_checkbox = QtWidgets.QCheckBox()
    diagonal_secondary_checkbox.setChecked(True)
    rotation_angle_edit = QtWidgets.QLineEdit("60")  # 角度，用户输入度数
    max_dis_edit = QtWidgets.QLineEdit("0.1")
    cycle_number_edit = QtWidgets.QLineEdit("1")

    layout.addRow("Primary_sf:", primary_sf_edit)
    layout.addRow("Secondary_sf:", secondary_sf_edit)
    layout.addRow("Theta (°):", theta_edit)
    layout.addRow("Rotation_angle (°):", rotation_angle_edit)
    layout.addRow("Grid_number:", grid_number_edit)
    layout.addRow("Side_offset:", side_offset_edit)
    layout.addRow("Diagonal Secondary:", diagonal_secondary_checkbox)
    layout.addRow("Point_dis:", max_dis_edit)
    layout.addRow("Cycle_number:", cycle_number_edit)

    # 添加按钮
    button_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addRow(button_box)

    # 显示对话框并等待用户输入
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return np.array([])  # 用户取消操作

    # 获取参数值
    try:
        primary_sf = float(primary_sf_edit.text())
        secondary_sf = float(secondary_sf_edit.text())
        theta_deg = float(theta_edit.text())
        grid_number = int(grid_number_edit.text())
        side_offset = float(side_offset_edit.text())
        diagonal_secondary = diagonal_secondary_checkbox.isChecked()
        rotation_angle_deg = float(rotation_angle_edit.text())
        max_dis = float(max_dis_edit.text())
        cycle_number = int(cycle_number_edit.text())

        # 将角度转换为弧度
        theta = theta_deg * pi / 180
        rotation_angle = rotation_angle_deg * pi / 180

        # 验证参数有效性
        if grid_number <= 0:
            raise ValueError("Grid_number must be positive")

    except ValueError as e:
        print(f"Invalid parameter format: {e}")
        return np.array([])

    # 生成点集
    try:
        pts_x_single, pts_y_single = psdd_intersect(
            primary_sf=primary_sf,
            secondary_sf=secondary_sf,
            theta=theta,
            grid_number=grid_number,
            side_offset=side_offset,
            rotation_angle=rotation_angle,
            diagonal_secondary=diagonal_secondary
        )

        # 扩展周期
        pts_x = pts_x_single.copy()
        pts_y = pts_y_single.copy()
        for _ in range(cycle_number - 1):
            pts_x = np.append(pts_x, pts_x_single)
            pts_y = np.append(pts_y, pts_y_single)

        # 后处理
        pts = np.column_stack((pts_x, pts_y))
        pts = Path_fill(points=pts, max_dis=max_dis)
        pts = remove_adjacent_duplicates(pts)
        return pts
    except Exception as e:
        print(f"Failed to generate points: {e}")
        return np.array([])




if __name__ == "__main__":
    points = generate_psdd_pattern()
    if len(points) > 0:
        plt.plot(points[:, 0], points[:, 1], 'b.', markersize=1)
        plt.axis('equal')
        plt.show()