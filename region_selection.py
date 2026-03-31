from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import math


class RegionSelector(QtWidgets.QGraphicsPathItem):
    def __init__(self, scene, callback):
        super().__init__()
        self.scene = scene
        self.callback = callback
        self.start_point = None
        self.current_shape = "rectangle"  # 默认矩形
        self.custom_points = []  # 存储自定义多边形的点
        self.drawing_custom = False  # 是否正在绘制自定义多边形
        self.temp_line = None  # 临时线段（预览）

        self.setPen(QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashLine))
        self.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 50)))
        self.setZValue(100)
        self.hide()

        # 创建临时线段项
        self.temp_line_item = QtWidgets.QGraphicsLineItem()
        self.temp_line_item.setPen(QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashLine))
        self.temp_line_item.setZValue(99)
        self.temp_line_item.hide()
        self.scene.addItem(self.temp_line_item)

    def set_shape(self, shape_type):
        """设置选框形状类型"""
        self.current_shape = shape_type
        self.custom_points = []  # 重置自定义点
        self.drawing_custom = False
        self.temp_line_item.hide()

    def start_selection(self, pos):
        if self.current_shape == "custom":
            self.start_custom_selection(pos)
        else:
            self.start_point = self.scene.views()[0].mapToScene(pos)
            self.show()

    def start_custom_selection(self, pos):
        """开始自定义多边形选择"""
        scene_point = self.scene.views()[0].mapToScene(pos)

        if not self.drawing_custom:
            # 开始新的自定义多边形
            self.custom_points = [scene_point]
            self.drawing_custom = True
            self.temp_line_item.show()
        else:
            # 添加新的点
            self.custom_points.append(scene_point)

        # 更新路径显示
        self.update_custom_path()
        self.show()

    def update_selection(self, pos):
        if self.current_shape == "custom":
            self.update_custom_preview(pos)
        elif self.start_point is not None:
            end_point = self.scene.views()[0].mapToScene(pos)

            if self.current_shape == "rectangle":
                self.update_rectangle_selection(end_point)
            elif self.current_shape == "ellipse":
                self.update_ellipse_selection(end_point)
            elif self.current_shape == "hexagon":
                self.update_hexagon_selection(end_point)

    def update_custom_preview(self, pos):
        """更新自定义多边形的预览"""
        if not self.drawing_custom or len(self.custom_points) == 0:
            return

        current_point = self.scene.views()[0].mapToScene(pos)
        last_point = self.custom_points[-1]

        # 更新临时线段
        self.temp_line_item.setLine(QtCore.QLineF(last_point, current_point))

    def update_custom_path(self):
        """更新自定义多边形的路径显示"""
        if len(self.custom_points) < 2:
            return

        path = QtGui.QPainterPath()
        path.moveTo(self.custom_points[0])

        for i in range(1, len(self.custom_points)):
            path.lineTo(self.custom_points[i])

        # 如果有多于2个点，闭合路径
        if len(self.custom_points) > 2:
            path.closeSubpath()

        self.setPath(path)

    def finish_custom_selection(self):
        """完成自定义多边形选择"""
        if len(self.custom_points) > 2:
            # 闭合多边形
            self.update_custom_path()
            self.temp_line_item.hide()
            self.finalize_selection()
        else:
            # 点数不足，取消选择
            self.custom_points = []
            self.drawing_custom = False
            self.temp_line_item.hide()
            self.hide()

    def update_rectangle_selection(self, end_point):
        """更新矩形选框"""
        rect = QtCore.QRectF(self.start_point, end_point).normalized()
        path = QtGui.QPainterPath()
        path.addRect(rect)
        self.setPath(path)

    def update_ellipse_selection(self, end_point):
        """更新椭圆选框"""
        rect = QtCore.QRectF(self.start_point, end_point).normalized()
        path = QtGui.QPainterPath()
        path.addEllipse(rect)
        self.setPath(path)

    def update_hexagon_selection(self, end_point):
        """更新六边形选框"""
        rect = QtCore.QRectF(self.start_point, end_point).normalized()
        width = rect.width()
        height = rect.height()
        center = rect.center()
        rx = width / 2
        ry = height / 2

        # 创建正六边形
        hexagon_points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = center.x() + rx * math.cos(angle_rad)
            y = center.y() + ry * math.sin(angle_rad)  # 使用ry而不是rx
            hexagon_points.append(QtCore.QPointF(x, y))

        path = QtGui.QPainterPath()
        path.moveTo(hexagon_points[0])
        for i in range(1, 6):
            path.lineTo(hexagon_points[i])
        path.closeSubpath()
        self.setPath(path)

    def finish_selection(self):
        if self.current_shape == "custom":
            self.finish_custom_selection()
        else:
            self.finalize_selection()

    def finalize_selection(self):
        """最终确定选择区域"""
        try:
            view = self.scene.views()[0]
            main_window = view.window()

            if main_window.current_points is None or len(main_window.current_points) == 0:
                self.callback(None, None, None)
                return

            # 获取当前图形项
            proxy_item = main_window.current_item
            if not proxy_item:
                self.callback(None, None, None)
                return

            canvas = proxy_item.widget()
            ax = canvas.figure.axes[0]

            # 获取图形项在场景中的位置和变换
            item_pos = proxy_item.pos()

            # 获取画布尺寸
            canvas_width = canvas.width()
            canvas_height = canvas.height()

            # 修复坐标转换函数
            def scene_to_data(scene_point):
                # 将场景坐标转换为图形项局部坐标
                local_point = proxy_item.mapFromScene(scene_point)

                # 将局部坐标转换为画布坐标
                canvas_x = local_point.x()
                canvas_y = canvas_height - local_point.y()  # 翻转y轴

                # 将画布坐标转换为数据坐标
                try:
                    inv = ax.transData.inverted()
                    return inv.transform((canvas_x, canvas_y))
                except Exception as e:
                    print(f"坐标转换错误: {str(e)}")
                    return (0, 0)

            # 根据不同的形状类型进行点筛选
            if self.current_shape == "rectangle":
                selected_points, unselected_points, region_rect, shape_info = self._select_points_rectangle(scene_to_data)
            elif self.current_shape == "ellipse":
                selected_points, unselected_points, region_rect, shape_info = self._select_points_ellipse(scene_to_data)
            elif self.current_shape == "hexagon":
                selected_points, unselected_points, region_rect, shape_info = self._select_points_hexagon(scene_to_data)
            elif self.current_shape == "custom":
                selected_points, unselected_points, region_rect, shape_info = self._select_points_custom(scene_to_data)
            else:
                selected_points, unselected_points, region_rect, shape_info = None, None, None, None

            # 调用回调
            self.callback(selected_points, unselected_points, region_rect, shape_info)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(view.window(), "错误", f"区域选择出错: {str(e)}")
            self.callback(None, None, None)
        finally:
            self.cleanup_selection()

    def cleanup_selection(self):
        """清理选择状态"""
        self.hide()
        self.start_point = None
        self.custom_points = []
        self.drawing_custom = False
        self.temp_line_item.hide()

    def _select_points_rectangle(self, scene_to_data_func):
        """矩形选框的点筛选"""
        path = self.path()
        rect = path.boundingRect()

        # 转换矩形角点
        top_left_data = scene_to_data_func(rect.topLeft())
        bottom_right_data = scene_to_data_func(rect.bottomRight())

        # 确保正确的矩形边界
        x_min = min(top_left_data[0], bottom_right_data[0])
        x_max = max(top_left_data[0], bottom_right_data[0])
        y_min = min(top_left_data[1], bottom_right_data[1])
        y_max = max(top_left_data[1], bottom_right_data[1])

        # 筛选选中的点
        selected_mask = (
                (self.scene.views()[0].window().current_points[:, 0] >= x_min) &
                (self.scene.views()[0].window().current_points[:, 0] <= x_max) &
                (self.scene.views()[0].window().current_points[:, 1] >= y_min) &
                (self.scene.views()[0].window().current_points[:, 1] <= y_max)
        )

        selected_points = self.scene.views()[0].window().current_points[selected_mask]
        unselected_points = self.scene.views()[0].window().current_points[~selected_mask]

        region_rect = QtCore.QRectF(x_min, y_min, x_max - x_min, y_max - y_min)
        shape_info = {
            'type': 'rectangle',
            'params': None  # 矩形不需要额外参数
        }
        return selected_points, unselected_points, region_rect, shape_info

    def _select_points_ellipse(self, scene_to_data_func):
        """椭圆选框的点筛选"""
        path = self.path()
        rect = path.boundingRect()
        center = rect.center()
        rx = rect.width() / 2
        ry = rect.height() / 2

        # 转换中心点和半径到数据坐标
        center_data = scene_to_data_func(center)
        # 估算半径（近似转换）
        right_point = QtCore.QPointF(center.x() + rx, center.y())
        right_data = scene_to_data_func(right_point)
        rx_data = abs(right_data[0] - center_data[0])

        top_point = QtCore.QPointF(center.x(), center.y() + ry)
        top_data = scene_to_data_func(top_point)
        ry_data = abs(top_data[1] - center_data[1])

        # 椭圆方程判断点是否在椭圆内
        points = self.scene.views()[0].window().current_points
        selected_mask = (
                ((points[:, 0] - center_data[0]) ** 2 / rx_data ** 2) +
                ((points[:, 1] - center_data[1]) ** 2 / ry_data ** 2) <= 1
        )

        selected_points = points[selected_mask]
        unselected_points = points[~selected_mask]
        region_rect = QtCore.QRectF(
            center_data[0] - rx_data, center_data[1] - ry_data,
            2 * rx_data, 2 * ry_data
        )
        shape_params = {
            'type': 'ellipse',
            'center': (center_data[0], center_data[1]),
            'rx': rx_data,
            'ry': ry_data
        }
        return selected_points, unselected_points, region_rect, shape_params

    def _select_points_hexagon(self, scene_to_data_func):
        """六边形选框的点筛选"""
        path = self.path()
        rect = path.boundingRect()
        center = rect.center()
        width = rect.width()
        height = rect.height()

        # 转换中心点到数据坐标
        center_data = scene_to_data_func(center)

        # 分别计算x和y方向的半径（保持实际比例）
        right_point = QtCore.QPointF(center.x() + width / 2, center.y())
        right_data = scene_to_data_func(right_point)
        rx_data = abs(right_data[0] - center_data[0])
        top_point = QtCore.QPointF(center.x(), center.y() + height / 2)
        top_data = scene_to_data_func(top_point)
        ry_data = abs(top_data[1] - center_data[1])

        # 创建六边形路径用于点包含判断
        hexagon_vertices = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = center_data[0] + rx_data * math.cos(angle_rad)
            y = center_data[1] + ry_data * math.sin(angle_rad)  # 使用ry_data而不是rx_data
            hexagon_vertices.append([x, y])

        hexagon_path = Path(hexagon_vertices)
        points = self.scene.views()[0].window().current_points

        # 判断点是否在六边形内
        selected_mask = hexagon_path.contains_points(points)
        selected_points = points[selected_mask]
        unselected_points = points[~selected_mask]

        # 计算准确的边界矩形
        x_coords = [v[0] for v in hexagon_vertices]
        y_coords = [v[1] for v in hexagon_vertices]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        region_rect = QtCore.QRectF(x_min, y_min, x_max - x_min, y_max - y_min)
        shape_info = {
            'type': 'hexagon',
            'center': (center_data[0], center_data[1]),
            'rx': rx_data,
            'ry': ry_data,
            'sides': 6,
            'vertices': hexagon_vertices  # 保存顶点信息供后续使用
        }
        return selected_points, unselected_points, region_rect, shape_info

    def _select_points_custom(self, scene_to_data_func):
        """自定义多边形选框的点筛选"""
        if len(self.custom_points) < 3:
            return None, None, None

        # 转换自定义多边形的顶点到数据坐标
        polygon_vertices = []
        for scene_point in self.custom_points:
            data_point = scene_to_data_func(scene_point)
            polygon_vertices.append([data_point[0], data_point[1]])

        # 创建多边形路径
        polygon_path = Path(polygon_vertices)
        points = self.scene.views()[0].window().current_points

        # 判断点是否在多边形内
        selected_mask = polygon_path.contains_points(points)
        selected_points = points[selected_mask]
        unselected_points = points[~selected_mask]

        # 计算边界矩形
        x_coords = [v[0] for v in polygon_vertices]
        y_coords = [v[1] for v in polygon_vertices]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        region_rect = QtCore.QRectF(x_min, y_min, x_max - x_min, y_max - y_min)
        shape_params = {
            'type': 'custom',
            'vertices': polygon_vertices  # 多边形的顶点坐标列表
        }
        return selected_points, unselected_points, region_rect, shape_params

