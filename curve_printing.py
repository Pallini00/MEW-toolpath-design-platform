import numpy as np
from matplotlib import pyplot as plt

def et(x, y):
    dx_dt = np.gradient(x)
    dy_dt = np.gradient(y)
    norm = np.sqrt(dx_dt**2 + dy_dt**2)
    norm[norm == 0] = 1e-10          # 避免除零
    return dx_dt / norm, dy_dt / norm

def curvature(x, y):
    dx_dt = np.gradient(x)
    dy_dt = np.gradient(y)
    d2x_dt2 = np.gradient(dx_dt)
    d2y_dt2 = np.gradient(dy_dt)
    denom = (dx_dt**2 + dy_dt**2) ** (3/2)
    denom[denom == 0] = 1e-10
    return np.abs(dx_dt * d2y_dt2 - dy_dt * d2x_dt2) / denom

def compute_offset_curve(points, l, Vcp):
    """
    计算偏移曲线和速度
    :param points: N×2 numpy数组，坐标点
    :param l: 偏移距离
    :param Vcp: 标量（常数速度）或与点数相同的数组
    :return: (offset_points, Vnp)
    """
    x = points[:, 0]
    y = points[:, 1]

    curv = curvature(x, y)
    et_x, et_y = et(x, y)

    offset_x = x + l * et_x
    offset_y = y + l * et_y
    offset_points = np.column_stack((offset_x, offset_y))

    if np.isscalar(Vcp):
        Vcp = np.full_like(x, Vcp)
    Vnp = Vcp * np.sqrt(1 + (l * curv)**2)

    return offset_points, Vnp

if __name__ == "__main__":
    # 原有交互式输入逻辑
    l = 1
    print("Enter the point data in the format x y Vcp (separated by spaces): ")
    print("Type 'done' when finished.")
    data = []
    while True:
        inp = input()
        if inp == 'done':
            break
        parts = inp.split()
        if len(parts) == 3:
            data.append(list(map(float, parts)))
    data = np.array(data)
    xp = data[:, 0]
    yp = data[:, 1]
    vcp = data[:, 2]

    offset_pts, vnp = compute_offset_curve(data[:, :2], l, vcp)

    plt.plot(xp, yp, label='original', color=(0.18, 0.46, 0.71), linewidth=3)
    plt.plot(offset_pts[:, 0], offset_pts[:, 1], label='digital', color=(0.75, 0, 0), linewidth=3, linestyle='--')
    plt.legend()
    plt.axis('equal')
    plt.savefig('output_image.png', dpi=600)
    plt.show()

    print("Coordinates and Velocity:")
    for i in range(len(offset_pts)):
        print("{:.2f} {:.2f} {:.2f}".format(offset_pts[i, 0], offset_pts[i, 1], round(vnp[i], 2)))