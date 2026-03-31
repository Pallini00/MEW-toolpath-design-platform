import numpy as np
import matplotlib.pyplot as plt
from math import sin, cos, pi, sqrt
import cv2
from skimage.morphology import skeletonize
from PyQt5 import QtCore, QtGui, QtWidgets


class CustomParamDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Pattern Parameter Settings")
        layout = QtWidgets.QFormLayout(self)

        # 网格数
        self.grid_spin = QtWidgets.QSpinBox()
        self.grid_spin.setRange(2, 100)
        self.grid_spin.setValue(10)
        self.grid_spin.setSingleStep(2)
        layout.addRow("Number of cells (even):", self.grid_spin)

        # Y偏移量
        self.y_offset_spin = QtWidgets.QDoubleSpinBox()
        self.y_offset_spin.setRange(-1000, 1000)
        self.y_offset_spin.setValue(250.0)
        layout.addRow("Y-axis offset:", self.y_offset_spin)

        # 旋转份数
        self.orientation_spin = QtWidgets.QSpinBox()
        self.orientation_spin.setRange(1, 36)
        self.orientation_spin.setValue(2)
        layout.addRow("Number of rotations:", self.orientation_spin)

        # 中心选择
        center_layout = QtWidgets.QHBoxLayout()
        self.x_center_spin = QtWidgets.QSpinBox()
        self.x_center_spin.setRange(0, 1)
        self.x_center_spin.setValue(0)
        self.y_center_spin = QtWidgets.QSpinBox()
        self.y_center_spin.setRange(0, 1)
        self.y_center_spin.setValue(0)
        center_layout.addWidget(self.x_center_spin)
        center_layout.addWidget(QtWidgets.QLabel("X-offset"))
        center_layout.addWidget(self.y_center_spin)
        center_layout.addWidget(QtWidgets.QLabel("Y-offset"))
        layout.addRow("Center Selection:", center_layout)

        # 层数
        self.layer_spin = QtWidgets.QSpinBox()
        self.layer_spin.setRange(1, 10)
        self.layer_spin.setValue(1)
        layout.addRow("Number of layers:", self.layer_spin)

        # 按钮
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_params(self):
        return {
            'grid_number': self.grid_spin.value(),
            'y_offset': self.y_offset_spin.value(),
            'orientation_number': self.orientation_spin.value(),
            'center_select': (self.x_center_spin.value(), self.y_center_spin.value()),
            'layer_number': self.layer_spin.value()
        }


def arc(center_x: float, center_y: float, radius: float, start_angle: float, stop_angle: float, max_dis: float):
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
        pts = np.column_stack((pts_x, pts_y))
    return pts

def align(points, tol=1e-12):
    """
    顺时针把点列绕起点旋转，直到起点与终点的 y 坐标相同，
    然后平移整个点列，使得起点在 (0,0)。

    Parameters
    ----------
    points : (n, 2) array_like
        点列，第一行为起点，最后一行为终点。
    tol : float
        判断 y 是否已相等的容差。

    Returns
    -------
    adjusted : (n, 2) ndarray
        旋转并平移后的点列。
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("points must be an array of shape (n, 2)")
    if pts.shape[0] < 2:
        return pts.copy()

    p0, pN = pts[0], pts[-1]

    # 1. 旋转
    if abs(p0[1] - pN[1]) <= tol:
        rotated = pts.copy()
    else:
        v = pN - p0
        phi = np.arctan2(v[1], v[0])
        # 顺时针角度
        angle = -phi if phi >= 0 else -(2 * np.pi + phi)
        c, s = np.cos(angle), np.sin(angle)
        R = np.array([[c, -s], [s, c]])
        rotated = (pts - p0) @ R.T + p0
        rotated[-1, 1] = p0[1]  # 修正数值误差

    # 2. 平移起点到原点
    return rotated - rotated[0]


def generate_pattern(forward, backward,
                     grid_number, y_offset,
                     orientation_number, center_select,
                     layer_number,
                     translator=None):
    if not isinstance(forward, np.ndarray):
        forward = np.array(forward, dtype=float)
    if not isinstance(backward, np.ndarray):
        backward = np.array(backward, dtype=float)
    """
    构建周期图案。

    Parameters
    ----------
    forward, backward : (n,2) array_like
        基础两条线分别代表去程和回程的一级图案（必须是点阵：起点(0,0)，终点 y=0 的情况）。
    grid_number : even int
        水平方向和竖直方向的复制次数（必须为偶数）。
    y_offset : float
        backward 相对于 forward 在 y 方向的初始偏移量。
    orientation_number : int
        旋转份数（把 tertiary 旋转成 orientation_number 份）。
    center_select : tuple of {0,1}, shape (2,)
        旋转中心相对几何中心的位移选择。如果右移，第一个分量就选x，代表右移x个一级图案宽度，如果上移，第二个分量就选y，代表上移y个y_offset
    layer_number : int
        最终再垂直串联 layer_number 次（无额外偏移，仅串联）。代表层数。
    translator : (orientation_number,2) array_like, optional
        每一份旋转后的平移量（x,y）。默认全为0。

    Returns
    -------
    pattern : (M,2) ndarray
        最终的所有点组合。
    """
    # 0. 参数检查
    if grid_number % 2 != 0:
        raise ValueError("grid_number must be an even number")
    forward = np.asarray(forward, float)
    backward = np.asarray(backward, float)

    # translator 检查
    if translator is None:
        translator = np.zeros((orientation_number, 2))
    else:
        translator = np.asarray(translator, float)
        if translator.shape != (orientation_number, 2):
            raise ValueError(f"translator must be an array of shape ({orientation_number},2) ")

    # 1. align 两条线
    if not (abs(forward[0, 1] - forward[-1, 1]) < 1e-8 and np.allclose(forward[0], 0)):
        forward = align(forward)
    if not (abs(backward[0, 1] - backward[-1, 1]) < 1e-8 and np.allclose(backward[0], 0)):
        backward = align(backward)

    # 2. 统一宽度
    fw = forward[-1, 0] - forward[0, 0]
    bw = backward[-1, 0] - backward[0, 0]
    if abs(fw - bw) > 1e-8:
        scale = fw / bw
        backward[:, 0] *= scale

    # 3. 构造 forwards（forwards是forward沿x方向偏移复制的产物）
    forwards = np.vstack([forward + np.array([i * fw, 0]) for i in range(grid_number)])

    # 4. 构造 backwards（先 y 偏移，再横向复制，最后倒序，backwards含义与forwards类似）
    backwards = np.vstack([backward + np.array([i * fw, y_offset]) for i in range(grid_number)])[::-1]
    # forwards+backwards共同构成二级结构
    secondary = np.vstack([forwards, backwards])

    # 5. 构造 tertiary
    tertiary = np.vstack([secondary + np.array([0, j * 2 * y_offset]) for j in range(grid_number // 2)])

    # 6. 计算安全下方高度
    min_y = tertiary[:, 1].min()
    margin = abs(y_offset)
    detour_y = min_y - margin

    # 7. 计算旋转中心
    center = tertiary.mean(axis=0)
    dx = (center_select[0] * fw / 2)
    dy = (center_select[1] * y_offset / 2)
    rot_center = center + np.array([dx, dy])

    # 8. 生成多份并插入过渡
    def make_transition(p_end, p_start):
        # return np.array([
        #     p_end,
        #     [p_end[0], detour_y],
        #     [p_start[0], detour_y],
        #     p_start
        # ], dtype=float)
        local_min_y = min(p_end[1], p_start[1])
        safe_y = local_min_y - 0.3 * margin  # 使用 margin 的0.3倍作为局部偏移
        return np.array([
            p_end,
            [p_end[0], safe_y],
            [p_start[0], safe_y],
            p_start
        ], dtype=float)

    all_pieces = []
    prev = None
    for k in range(orientation_number):
        angle_deg = 180.0 / orientation_number * k
        theta = np.deg2rad(angle_deg)
        R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])

        rotated = (tertiary - rot_center) @ R.T + rot_center
        # 平移
        rotated += translator[k]

        if prev is not None:
            all_pieces.append(make_transition(prev[-1], rotated[0]))
        all_pieces.append(rotated)
        prev = rotated

    single = np.vstack(all_pieces)

    # 9. 串联
    pattern = np.vstack([single for _ in range(layer_number)])
    return pattern


# def generate_pattern(forward, backward,
#                      grid_number, y_offset,
#                      orientation_number, center_select,
#                      layer_number):
#     """
#     构建周期图案。
#
#     Parameters
#     ----------
#     forward, backward : (n,2) array_like
#         基础两条线（必须是点阵：起点(0,0)，终点 y=0 的情况）。
#     grid_number : even int
#         水平方向复制次数（必须为偶数）。
#     y_offset : float
#         backward 相对于 forward 在 y 方向的初始偏移量。
#     orientation_number : int
#         旋转份数（把 tertiary 旋转成 orientation_number 份）。
#     center_select : tuple of {0,1}, shape (2,)
#         旋转中心相对几何中心的位移选择：
#           - (0,0) → 中心
#           - (1,0) → 向右 half_width
#           - (0,1) → 向上 half_y_offset
#           - (1,1) → 右上
#     layer_number : int
#         最终再垂直串联 layer_number 次（无额外偏移，仅串联）。
#
#     Returns
#     -------
#     pattern : (M,2) ndarray
#         最终的所有点组合。
#     """
#     # 0. 参数检查
#     if grid_number % 2 != 0:
#         raise ValueError("grid_number 必须是偶数")
#     forward = np.asarray(forward, float)
#     backward = np.asarray(backward, float)
#
#     # 1. align 两条线
#     if not (abs(forward[0, 1] - forward[-1, 1]) < 1e-8 and np.allclose(forward[0], 0)):
#         forward = align(forward)
#     if not (abs(backward[0, 1] - backward[-1, 1]) < 1e-8 and np.allclose(backward[0], 0)):
#         backward = align(backward)
#
#     # 2. 统一宽度
#     fw = forward[-1, 0] - forward[0, 0]
#     bw = backward[-1, 0] - backward[0, 0]
#     if abs(fw - bw) > 1e-8:
#         scale = fw / bw
#         backward[:, 0] *= scale
#
#     # 3. 构造 forwards
#     segs_f = []
#     for i in range(grid_number):
#         segs_f.append(forward + np.array([i * fw, 0]))
#     forwards = np.vstack(segs_f)
#
#     # 4. 构造 backwards（先 y 偏移，再横向复制，最后倒序）
#     segs_b = []
#     for i in range(grid_number):
#         segs_b.append(backward + np.array([i * fw, y_offset]))
#     backwards = np.vstack(segs_b)[::-1]
#
#     secondary = np.vstack([forwards, backwards])
#
#     # 5. 构造 tertiary：以 2*y_offset 为步长向上复制 grid_number/2 次
#     terts = []
#     for j in range(grid_number // 2):
#         terts.append(secondary + np.array([0, j * 2 * y_offset]))
#     tertiary = np.vstack(terts)
#
#
#     # 6. 计算安全下方高度
#     min_y = tertiary[:, 1].min()
#     margin = abs(y_offset)
#     detour_y = min_y - margin
#
#     # 7. 计算旋转中心
#     center = tertiary.mean(axis=0)
#     dx = (center_select[0] * fw / 2)
#     dy = (center_select[1] * y_offset / 2)
#     rot_center = center + np.array([dx, dy])
#
#     # 8. 生成多份并插入过渡（过渡全在 detour_y 下方）
#     def make_transition(p_end, p_start):
#         return np.array([
#             p_end,
#             [p_end[0], detour_y],
#             [p_start[0], detour_y],
#             p_start
#         ], dtype=float)
#
#     all_pieces = []
#     prev = None
#     for k in range(orientation_number):
#         angle_deg = 180.0 / orientation_number * k
#         theta = np.deg2rad(angle_deg)
#         c, s = np.cos(theta), np.sin(theta)
#         R = np.array([[c, -s], [s, c]])
#
#         rotated = (tertiary - rot_center) @ R.T + rot_center
#
#         if prev is not None:
#             all_pieces.append(make_transition(prev[-1], rotated[0]))
#         all_pieces.append(rotated)
#         prev = rotated
#
#     single = np.vstack(all_pieces)
#
#     # 9. 最终串联 layer_number 次
#     layers = [single for _ in range(layer_number)]
#     pattern = np.vstack(layers)
#     return pattern




# ====== 简单测试 ======
if __name__ == "__main__":
    ##################
    # 下面的例子效果像编织结构
    # 构造一条折线示例
    # pt_1 = np.array([0, 0])
    # pt_2 = np.array([1, 1])
    # pt_3 = np.array([2, 0])
    # dx_1 = np.linspace(pt_1[0], pt_2[0], 100)
    # dy_1 = np.linspace(pt_1[1], pt_2[1], 100)
    # dx_2 = np.linspace(pt_2[0], pt_3[0], 100)
    # dy_2 = np.linspace(pt_2[1], pt_3[1], 100)
    # d_1 = np.column_stack((dx_1, dy_1))
    # d_2 = np.column_stack((dx_2, dy_2))
    # primary = np.vstack((d_1, d_2))
    # pat = generate_pattern(primary, primary,
    #                        grid_number=10,
    #                        y_offset=1,
    #                        orientation_number=2,
    #                        center_select=(0, 1),
    #                        layer_number=1)
    # 编织结构至此结束
    ###############################
    # 以下形成一种花生图案
    # arc_1 = arc(center_x=1, center_y=0, start_angle= pi, stop_angle=0, radius=1, max_dis=0.01)
    # arc_2 = arc(center_x=3, center_y=0, start_angle= -pi, stop_angle=0, radius=1, max_dis=0.01)
    # primary = np.vstack((arc_1, arc_2))
    # pat = generate_pattern(primary, primary,
    #                        grid_number=10,
    #                        y_offset=2,
    #                        orientation_number=2,
    #                        center_select=(0, 0),
    #                        layer_number=1)
    # # # 花生图案至此结束
    ###############################
    ###############################
    # # 以下为圆弧平行四边形
    # radius = 1
    # arc_1 = arc(center_x=0.5 * sqrt(2) * radius, center_y=0.5 * sqrt(2) * radius, start_angle=-0.75 * pi,
    #             stop_angle=-0.25 * pi, radius=radius, max_dis=0.01)
    # arc_2 = arc(center_x=1.5 * sqrt(2) * radius, center_y=-0.5 * sqrt(2) * radius, start_angle=0.75 * pi,
    #             stop_angle=0.25 * pi, radius=radius, max_dis=0.01)
    # primary = np.vstack((arc_1, arc_2))
    # pat = generate_pattern(primary, primary,
    #                        grid_number=6,
    #                        y_offset=sqrt(2) * radius,
    #                        orientation_number=2,
    #                        center_select=(0, 0),
    #                        layer_number=1)
    # print("最终点数：", pat.shape[0])
    # plt.plot(pat[:, 0], pat[:, 1])
    # plt.axis('equal')
    # plt.show()
    # #圆弧平行四边形至此结束
    ###############################
    #以下为狗骨头图案
    # radius = 1
    # arc_1 = arc(center_x=0.5 * sqrt(2) * radius, center_y=0.5 * sqrt(2) * radius, start_angle=-0.75 * pi,
    #             stop_angle=-0.25 * pi, radius=radius, max_dis=0.01)
    # arc_2 = arc(center_x=1.5 * sqrt(2) * radius, center_y=-0.5 * sqrt(2) * radius, start_angle=0.75 * pi,
    #             stop_angle=0.25 * pi, radius=radius, max_dis=0.01)
    # primary = np.vstack((arc_1, arc_2))
    # arc_3 = arc(center_x=0.5 * sqrt(2) * radius, center_y=-0.5 * sqrt(2) * radius, start_angle=0.75 * pi,
    #             stop_angle=0.25 * pi, radius=radius, max_dis=0.01)
    # arc_4 = arc(center_x=1.5 * sqrt(2) * radius, center_y=0.5 * sqrt(2) * radius, start_angle=-0.75 * pi,
    #             stop_angle=-0.25 * pi, radius=radius, max_dis=0.01)
    # primary_2 = np.vstack((arc_3, arc_4))
    # pat = generate_pattern(primary, primary_2,
    #                        grid_number=10,
    #                        y_offset=sqrt(2) * radius,
    #                        orientation_number=2,
    #                        center_select=(0, 1),
    #                        layer_number=1)
    #狗骨头图案至此结束
    ###############################
    #以下为圆普通堆积图案
    # radius = 1
    # arc_1 = arc(center_x=0.5 * sqrt(2) * radius, center_y=0.5 * sqrt(2) * radius, start_angle=-0.75 * pi,
    #             stop_angle=-0.25 * pi, radius=radius, max_dis=0.01)
    # arc_2 = arc(center_x=1.5 * sqrt(2) * radius, center_y=-0.5 * sqrt(2) * radius, start_angle=0.75 * pi,
    #             stop_angle=0.25 * pi, radius=radius, max_dis=0.01)
    # primary = np.vstack((arc_1, arc_2))
    # arc_3 = arc(center_x=0.5 * sqrt(2) * radius, center_y=-0.5 * sqrt(2) * radius, start_angle=0.75 * pi,
    #             stop_angle=0.25 * pi, radius=radius, max_dis=0.01)
    # arc_4 = arc(center_x=1.5 * sqrt(2) * radius, center_y=0.5 * sqrt(2) * radius, start_angle=-0.75 * pi,
    #             stop_angle=-0.25 * pi, radius=radius, max_dis=0.01)
    # primary_2 = np.vstack((arc_3, arc_4))
    # pat = generate_pattern(primary, primary_2,
    #                        grid_number=10,
    #                        y_offset=sqrt(2) * radius,
    #                        orientation_number=2,
    #                        center_select=(0, 1),
    #                        layer_number=1, translator=np.array([[0, 0], [0, sqrt(2) * radius]]))
    #圆普通堆积图案至此结束
    ###############################
    # pt_1 = np.array([0, 0])
    # pt_2 = np.array([1, 0])
    # pt_3 = np.array([2, 0])
    # dx_1 = np.linspace(pt_1[0], pt_2[0], 100)
    # dy_1 = np.linspace(pt_1[1], pt_2[1], 100)
    # dx_2 = np.linspace(pt_2[0], pt_3[0], 100)
    # dy_2 = np.linspace(pt_2[1], pt_3[1], 100)
    # d_1 = np.column_stack((dx_1, dy_1))
    # d_2 = np.column_stack((dx_2, dy_2))
    # primary = np.vstack((d_1, d_2))
    # pat = generate_pattern(primary, primary,
    #                        grid_number=10,
    #                        y_offset=2,
    #                        orientation_number=2,
    #                        center_select=(0, 0),
    #                        layer_number=1)
    # print("最终点数：", pat.shape[0])
    # plt.plot(pat[:, 0], pat[:, 1])
    # plt.axis('equal')
    # plt.show()


    ###############################
    #以下为新型结构1
    # def create_cosine_curve(width=2.0, amplitude=0.3, points=100):
    #     """创建余弦曲线"""
    #     x = np.linspace(0, width, points)
    #     y = amplitude * (np.cos(2 * np.pi * x / width) - 1)  # 调整到从0开始
    #     return np.column_stack((x, y))
    #
    #
    # def create_sloping_line(width=2.0, slope=0.1, points=100):
    #     """创建缓坡直线"""
    #     x = np.linspace(0, width, points)
    #     y = slope * x  # 轻微斜坡
    #     return np.column_stack((x, y))
    #
    #
    # # 生成基础单元
    # width = 2.0
    # forward = create_cosine_curve(width=width, amplitude=0.3, points=150)
    # backward = create_sloping_line(width=width, slope=0.1, points=150)
    #
    # # 生成两取向结构
    # pat = generate_pattern(forward, backward,
    #                         grid_number=6,
    #                         y_offset=1.0,  # 与宽度成2:1关系
    #                         orientation_number=3,
    #                         center_select=(0, 0),
    #                         layer_number=1)


    #新型结构1结束
    ################################

    # 以下为新型结构2
    # def create_simple_v_shape(width=2, depth=0.5):
    #     # 创建简单的V形
    #     x = np.array([0, width / 2, width])
    #     y = np.array([0, -depth, 0])
    #     # 插值增加点数
    #     t = np.linspace(0, 1, 50)
    #     x_interp = np.interp(t, [0, 0.5, 1], x)
    #     y_interp = np.interp(t, [0, 0.5, 1], y)
    #     return np.column_stack((x_interp, y_interp))
    #
    #
    # primary = create_simple_v_shape(width=2, depth=0.8)
    # pat = generate_pattern(primary, primary,
    #                        grid_number=12,
    #                        y_offset=2,
    #                        orientation_number=2,
    #                        center_select=(0, 0),
    #                        layer_number=1)
    # 新型结构2结束
    ################################

    # 以下为新型结构3
    def create_cosh_curve(width=2, amplitude=0.5, points=100):
        x = np.linspace(0, width, points)
        # 使用双曲余弦函数，中心对称
        y = amplitude * (np.cosh(2 * (x / width - 0.5)) - np.cosh(1))
        return np.column_stack((x, y))


    forward = create_cosh_curve(width=2, amplitude=0.6, points=100)
    backward = create_cosh_curve(width=2, amplitude=-0.6, points=100)

    pat = generate_pattern(forward, backward,
                           grid_number=16,
                           y_offset=2,
                           orientation_number=2,
                           center_select=(0, 0),
                           layer_number=1)
    # 新型结构3结束

    ################################

    # 以下为新型结构4
    # def create_piecewise_polynomial(width=2, points=100):
    #     x = np.linspace(0, width, points)
    #     mid = points // 2
    #     y = np.zeros(points)
    #
    #     # 前半部分：三次多项式
    #     y[:mid] = -0.8 * (x[:mid] / width * 2) ** 3 + 0.6 * (x[:mid] / width * 2) ** 2
    #
    #     # 后半部分：二次多项式
    #     y[mid:] = -0.5 * (x[mid:] / width * 2 - 1) ** 2 + 0.3
    #
    #     return np.column_stack((x, y))
    #
    #
    # forward = create_piecewise_polynomial(width=2, points=100)
    # backward = create_piecewise_polynomial(width=2, points=100)
    # backward[:, 1] = -backward[:, 1]  # 上下对称
    #
    # pat = generate_pattern(forward, backward,
    #                        grid_number=10,
    #                        y_offset=1.0,
    #                        orientation_number=2,
    #                        center_select=(0, 0),
    #                        layer_number=1)
    # 新型结构4结束
    #############



    ###############################
    # 以下为自定义图案
    def extract_centerline(image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        skeleton = skeletonize(binary // 255)
        skeleton = skeleton.astype(np.uint8) * 255
        contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            return np.array([])
        max_contour = max(contours, key=cv2.contourArea)
        points = max_contour.reshape(-1, 2).astype(np.int32)
        points[:, 1] = height - 1 - points[:, 1]  # 坐标系转换
        if len(points) > 0:
            # 找到点A（x和y均最小）
            min_x = points[:, 0].min()
            leftmost_indices = np.where(points[:, 0] == min_x)[0]
            min_y = points[leftmost_indices, 1].min()
            a_indices = leftmost_indices[points[leftmost_indices, 1] == min_y]
            a_index = a_indices[0]
            # 重新排列点集，从点A开始
            points = np.concatenate([points[a_index:], points[:a_index]])
            # 平移所有点，使点A位于原点
            a_point = points[0]
            points -= a_point
            # 新增：按路径顺序重新排序（改进版）
            ordered_points = [points[0]]
            remaining = points[1:].tolist()
            while remaining:
                last_point = ordered_points[-1]
                nearest = min(remaining, key=lambda p: np.linalg.norm(np.array(p) - last_point))
                ordered_points.append(nearest)
                remaining.remove(nearest)
            points = np.array(ordered_points)
            # 强制最后一个点的y值为0
            if len(points) > 0:
                points[-1, 1] = 0
        return points
    # 使用示例
    # points_1 = extract_centerline("basic_pattern_1.png")
    # points_2 = extract_centerline("basic_pattern_1.png")
    # pat = generate_pattern(points_1, points_2,
    #                        grid_number=10,
    #                        y_offset=250,
    #                        orientation_number=2,
    #                        center_select=(0, 0),
    #                        layer_number=1)
    # np.savetxt('design_pattern.txt', pat, fmt='%.6f', delimiter=',')
    # print("最终点数：", pat.shape[0])

    plt.plot(pat[:, 0], pat[:, 1])
    plt.axis('equal')
    plt.show()
    np.savetxt(' customization_output.txt', pat, fmt='%.4f', delimiter=' ')








