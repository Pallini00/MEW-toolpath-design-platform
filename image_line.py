
import cv2
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
import sys


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


# # 使用示例
# points = extract_centerline("basic_pattern_1.png")
#
# if len(points) > 0:
#     # plt.plot(points[:, 0], points[:, 1], 'r-', linewidth=1, label='Centerline')
#     # plt.scatter(points[:, 0], points[:, 1], c='red', s=1, label='Points')
#     # plt.scatter(0, 0, c='blue', s=50, label='Origin (0,0)')
#     # plt.scatter(points[-1, 0], 0, c='green', s=50, label='Modified Last Point')
#     np.savetxt('points.txt', points, fmt='%d', delimiter=' ')
# else:
#     print("未检测到线条")
#
# # plt.xlabel('X')
# # plt.ylabel('Y')
# # plt.grid()
# # plt.legend()
# # plt.gca().set_aspect('equal')
# # plt.show()
# print("修改后的点集坐标：\n", points)


if __name__ == "__main__":
    # 从命令行参数获取图片路径
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("请提供图片路径作为参数")
        sys.exit(1)

    points = extract_centerline(image_path)

    if len(points) > 0:
        np.savetxt('points.txt', points, fmt='%d', delimiter=' ')
    else:
        print("未检测到线条")