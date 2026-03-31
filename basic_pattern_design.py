import sys
import math
import copy
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QColorDialog, QFileDialog,
                             QRadioButton, QButtonGroup, QFrame, QSpinBox, QLabel,
                             QGridLayout, QInputDialog, QMessageBox, QStatusBar)
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QBrush, QPainterPath, QKeyEvent
from PyQt5.QtCore import Qt, QPoint, QRect, QLineF, QPointF, QRectF


class Shape:
    LINE = "line"
    ARC = "arc"
    FREEHAND = "freehand"


class DrawingObject:
    def __init__(self, shape_type, points, color, pen_width):
        self.shape_type = shape_type
        self.points = points
        self.color = color
        self.pen_width = pen_width
        self.selected = False
        self.editing = False
        self.bounding_rect = None
        self.update_bounding_rect()
        self.rotation_angle = 0  # 添加旋转角度属性

    def update_bounding_rect(self):
        if not self.points:
            self.bounding_rect = QRect()
            return

        min_x = min(p.x() for p in self.points)
        max_x = max(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_y = max(p.y() for p in self.points)

        padding = max(10, self.pen_width * 2)
        self.bounding_rect = QRect(min_x - padding, min_y - padding,
                                   (max_x - min_x) + padding * 2,
                                   (max_y - min_y) + padding * 2)

    def draw(self, painter):
        painter.save()  # 保存当前画笔状态

        # 应用旋转
        if self.rotation_angle != 0:
            center = self.bounding_rect.center()
            painter.translate(center)
            painter.rotate(self.rotation_angle)
            painter.translate(-center)

        pen = QPen(self.color, self.pen_width)
        painter.setPen(pen)

        if self.shape_type == Shape.LINE and len(self.points) >= 2:
            painter.drawLine(self.points[0], self.points[1])

        elif self.shape_type == Shape.ARC and len(self.points) >= 2:
            x1 = min(self.points[0].x(), self.points[1].x())
            y1 = min(self.points[0].y(), self.points[1].y())
            x2 = max(self.points[0].x(), self.points[1].x())
            y2 = max(self.points[0].y(), self.points[1].y())
            rect = QRect(x1, y1, x2 - x1, y2 - y1)

            start_angle = 0
            span_angle = 180 * 16
            painter.drawArc(rect, start_angle, span_angle)

        elif self.shape_type == Shape.FREEHAND and len(self.points) >= 2:
            path = QPainterPath()
            path.moveTo(self.points[0])
            for point in self.points[1:]:
                path.lineTo(point)
            painter.drawPath(path)

        painter.restore()  # 恢复画笔状态

        # 绘制控制点（如果对象被选中或正在编辑）
        if (self.selected or self.editing) and self.editing:
            painter.setBrush(QBrush(Qt.red))
            painter.setPen(QPen(Qt.red, 1))
            for point in self.points:
                painter.drawEllipse(QRect(point.x() - 5, point.y() - 5, 10, 10))

    def contains_point(self, point, threshold=10):
        if self.bounding_rect and not self.bounding_rect.contains(point):
            return False

        for p in self.points:
            if math.sqrt((p.x() - point.x()) ** 2 + (p.y() - point.y()) ** 2) <= threshold:
                return True

        if self.shape_type == Shape.FREEHAND:
            for i in range(len(self.points) - 1):
                if self.point_near_line(point, self.points[i], self.points[i + 1], threshold):
                    return True

        elif self.shape_type == Shape.LINE and len(self.points) >= 2:
            return self.point_near_line(point, self.points[0], self.points[1], threshold)

        elif self.shape_type == Shape.ARC and len(self.points) >= 2:
            # 对于圆弧，检查点是否在圆弧附近
            x1 = min(self.points[0].x(), self.points[1].x())
            y1 = min(self.points[0].y(), self.points[1].y())
            x2 = max(self.points[0].x(), self.points[1].x())
            y2 = max(self.points[0].y(), self.points[1].y())

            # 计算圆弧的中心和半径
            center_x = (x1 + x2) / 2
            center_y = y1  # 圆弧是上半圆，所以中心y坐标在顶部
            radius = (x2 - x1) / 2

            # 检查点是否在圆弧附近
            distance = math.sqrt((point.x() - center_x) ** 2 + (point.y() - center_y) ** 2)
            return abs(distance - radius) <= threshold

        return False

    def point_near_line(self, point, line_start, line_end, threshold):
        A = point.x() - line_start.x()
        B = point.y() - line_start.y()
        C = line_end.x() - line_start.x()
        D = line_end.y() - line_start.y()

        dot = A * C + B * D
        len_sq = C * C + D * D
        param = -1.0

        if len_sq != 0:
            param = dot / len_sq

        if param < 0:
            xx = line_start.x()
            yy = line_start.y()
        elif param > 1:
            xx = line_end.x()
            yy = line_end.y()
        else:
            xx = line_start.x() + param * C
            yy = line_start.y() + param * D

        dx = point.x() - xx
        dy = point.y() - yy

        return math.sqrt(dx * dx + dy * dy) <= threshold

    def get_point_index(self, point, threshold=10):
        for i, p in enumerate(self.points):
            if math.sqrt((p.x() - point.x()) ** 2 + (p.y() - point.y()) ** 2) <= threshold:
                return i
        return -1

    def rotate(self, angle, center=None):
        """旋转对象"""
        if center is None:
            center = self.bounding_rect.center()

        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        new_points = []
        for point in self.points:
            # 将点相对于中心点进行旋转
            x = point.x() - center.x()
            y = point.y() - center.y()

            new_x = x * cos_a - y * sin_a + center.x()
            new_y = x * sin_a + y * cos_a + center.y()

            new_points.append(QPoint(int(new_x), int(new_y)))

        self.points = new_points
        self.update_bounding_rect()
        self.rotation_angle = (self.rotation_angle + angle) % 360  # 更新总旋转角度

    def move(self, dx, dy):
        """移动对象"""
        new_points = []
        for point in self.points:
            new_x = point.x() + dx
            new_y = point.y() + dy
            new_points.append(QPoint(int(new_x), int(new_y)))

        self.points = new_points
        self.update_bounding_rect()

    def get_outline_points(self, step=1):
        """获取形状的轮廓点集"""
        points = []

        if self.shape_type == Shape.LINE and len(self.points) >= 2:
            # 计算直线上的多个点
            start = self.points[0]
            end = self.points[1]
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            length = math.sqrt(dx ** 2 + dy ** 2)

            if length == 0:
                return []

            # 沿直线采样多个点
            num_steps = max(2, int(length / step))
            for i in range(num_steps):
                t = i / (num_steps - 1)
                x = start.x() + t * dx
                y = start.y() + t * dy
                points.append(QPoint(int(x), int(y)))

        elif self.shape_type == Shape.ARC and len(self.points) >= 2:
            # 计算圆弧上的多个点
            x1 = min(self.points[0].x(), self.points[1].x())
            y1 = min(self.points[0].y(), self.points[1].y())
            x2 = max(self.points[0].x(), self.points[1].x())
            y2 = max(self.points[0].y(), self.points[1].y())

            # 圆弧是上半圆
            center_x = (x1 + x2) / 2
            center_y = y1  # 圆弧顶部
            radius = (x2 - x1) / 2

            # 沿圆弧采样多个点
            num_steps = max(10, int(math.pi * radius / step))
            for i in range(num_steps):
                angle = math.pi * i / (num_steps - 1)  # 从0到π
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append(QPoint(int(x), int(y)))

        elif self.shape_type == Shape.FREEHAND and len(self.points) >= 2:
            # 自由曲线直接使用已有点
            points = self.points.copy()

        return points


class DrawingArea(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Sunken | QFrame.StyledPanel)
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)  # 启用鼠标跟踪以显示坐标

        # 绘图属性
        self.color = Qt.black
        self.shape = Shape.LINE
        self.pen_width = 2

        # 绘图状态
        self.last_point = QPoint()
        self.current_point = QPoint()
        self.drawing = False
        self.drawing_object = None
        self.objects = []
        self.selected_object = None
        self.editing_point_index = -1
        self.edit_mode = False
        self.rotate_mode = False
        self.move_mode = False
        self.rotation_start_pos = None
        self.rotation_center = None
        self.move_start_pos = None
        self.move_object_offset = QPoint(0, 0)

        # 用于自由绘制的路径
        self.freehand_path = []

        # 历史记录（用于撤销功能）
        self.history = []
        self.save_state()  # 保存初始状态

        # 缩放因子（1.0 = 100%）
        self.zoom_factor = 1.0
        self.zoom_step = 0.1
        self.min_zoom = 0.1

        # 坐标系原点位置（画布坐标）
        self.origin_x = 50
        self.origin_y = 350  # 默认原点y位置
        self.grid_spacing = 20  # 网格间距

    def get_main_window(self):
        """安全获取父窗口的QMainWindow实例"""
        parent = self.parent()
        while parent:
            if isinstance(parent, QMainWindow):
                return parent
            parent = parent.parent()
        return None

    def set_shape(self, shape):
        self.shape = shape
        self.exit_all_modes()
        self.drawing = False
        self.drawing_object = None
        self.freehand_path = []

    def clear_selected(self):
        """删除当前选中的对象"""
        if self.selected_object:
            self.objects.remove(self.selected_object)
            self.selected_object = None
            self.save_state()
            self.update()
        else:
            # 如果没有选中任何对象，显示提示信息
            QMessageBox.information(self, "Warning", "Please select an object first, then click the Delete button.")

    def clear_all(self):
        """清除整个画布"""
        self.save_state()
        self.objects.clear()
        self.selected_object = None
        self.update()

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                   "PNG (*.png);;All kinds(*)")
        if file_path:
            image = QImage(self.size(), QImage.Format_ARGB32)
            image.fill(Qt.white)

            painter = QPainter(image)
            painter.scale(self.zoom_factor, self.zoom_factor)

            # 绘制坐标原点和参考线
            self.draw_grid_and_axes(painter)

            for obj in self.objects:
                obj.draw(painter)
            painter.end()

            image.save(file_path)

    def wheelEvent(self, event):
        # 确保缩放范围安全
        zoom = self.zoom_factor * (1.1 if event.angleDelta().y() > 0 else 0.9)
        self.zoom_factor = max(self.min_zoom, min(zoom, 5.0))  # 限制在0.1-5.0之间
        self.update()

    def enter_edit_mode(self):
        self.edit_mode = True
        self.rotate_mode = False
        self.move_mode = False
        self.update()

    def enter_rotate_mode(self):
        self.rotate_mode = True
        self.edit_mode = False
        self.move_mode = False
        self.update()

    def enter_move_mode(self):
        self.move_mode = True
        self.edit_mode = False
        self.rotate_mode = False
        self.update()

    def exit_all_modes(self):
        self.edit_mode = False
        self.rotate_mode = False
        self.move_mode = False
        if self.selected_object:
            self.selected_object.selected = False
            self.selected_object.editing = False
        self.selected_object = None
        self.editing_point_index = -1
        self.rotation_start_pos = None
        self.rotation_center = None
        self.move_start_pos = None
        self.update()

    def save_state(self):
        """保存当前绘图状态到历史记录"""
        state = copy.deepcopy(self.objects)
        self.history.append(state)
        if len(self.history) > 20:
            self.history.pop(0)

    def undo(self):
        """撤销上一步操作"""
        if len(self.history) > 1:
            self.history.pop()
            previous_state = self.history[-1]
            self.objects = copy.deepcopy(previous_state)
            self.exit_all_modes()
            self.update()

    def draw_grid_and_axes(self, painter):
        """绘制坐标系网格和坐标轴"""
        # 设置网格画笔（浅灰色虚线）
        grid_pen = QPen(QColor(200, 200, 200), 1, Qt.DashLine)
        # 设置坐标轴画笔（黑色实线）
        axes_pen = QPen(Qt.black, 1, Qt.SolidLine)

        painter.save()

        # 计算网格范围（基于当前视图和缩放）
        view_rect = self.rect()
        left = 0
        right = view_rect.width()
        top = 0
        bottom = view_rect.height()

        # 绘制网格
        painter.setPen(grid_pen)

        # 绘制垂直网格线（从左到右）
        x = self.origin_x * self.zoom_factor % (self.grid_spacing * self.zoom_factor)
        while x < right:
            if x > left:
                painter.drawLine(QLineF(x, top, x, bottom))
            x += self.grid_spacing * self.zoom_factor

        # 绘制水平网格线（从上到下）
        y = self.origin_y * self.zoom_factor % (self.grid_spacing * self.zoom_factor)
        while y < bottom:
            if y > top:
                painter.drawLine(QLineF(left, y, right, y))
            y += self.grid_spacing * self.zoom_factor

        # 绘制坐标轴
        painter.setPen(axes_pen)
        # X轴
        painter.drawLine(QLineF(0, self.origin_y * self.zoom_factor, right, self.origin_y * self.zoom_factor))
        # Y轴
        painter.drawLine(QLineF(self.origin_x * self.zoom_factor, 0, self.origin_x * self.zoom_factor, bottom))

        # 绘制坐标轴箭头
        arrow_size = 5 * self.zoom_factor
        # X轴箭头
        painter.drawLine(QLineF(right, self.origin_y * self.zoom_factor,
                                right - arrow_size, self.origin_y * self.zoom_factor - arrow_size))
        painter.drawLine(QLineF(right, self.origin_y * self.zoom_factor,
                                right - arrow_size, self.origin_y * self.zoom_factor + arrow_size))
        # Y轴箭头
        painter.drawLine(QLineF(self.origin_x * self.zoom_factor, 0,
                                self.origin_x * self.zoom_factor - arrow_size, arrow_size))
        painter.drawLine(QLineF(self.origin_x * self.zoom_factor, 0,
                                self.origin_x * self.zoom_factor + arrow_size, arrow_size))

        # 绘制坐标原点标记
        painter.setPen(QPen(Qt.red, 1))
        painter.setBrush(QBrush(Qt.red))
        origin_screen_x = self.origin_x * self.zoom_factor
        origin_screen_y = self.origin_y * self.zoom_factor
        painter.drawEllipse(QRectF(origin_screen_x - 2, origin_screen_y - 2, 4, 4))

        painter.restore()

    def mousePressEvent(self, event):
        # 获取鼠标在画布上的物理坐标
        physical_x = event.pos().x()
        physical_y = event.pos().y()

        # 转换为逻辑坐标（考虑缩放）
        logical_x = physical_x / self.zoom_factor
        logical_y = physical_y / self.zoom_factor

        # 转换为整数逻辑坐标（用于绘图操作）
        pos = QPoint(int(logical_x), int(logical_y))

        if event.button() == Qt.LeftButton:
            self.last_point = pos
            self.current_point = pos

            if self.rotate_mode:
                if self.selected_object:
                    # 如果已经选中对象，开始旋转
                    self.rotation_start_pos = pos
                    self.rotation_center = self.selected_object.bounding_rect.center()
                else:
                    # 如果没有选中对象，先选择对象
                    for obj in reversed(self.objects):
                        if obj.contains_point(pos):
                            # 取消之前选中的对象
                            if self.selected_object:
                                self.selected_object.selected = False
                                self.selected_object.editing = False

                            # 设置新选中的对象
                            self.selected_object = obj
                            self.selected_object.selected = True
                            self.selected_object.editing = True
                            self.update()
                            return
                    # 如果没有点击任何对象，取消当前选择
                    if self.selected_object:
                        self.selected_object.selected = False
                        self.selected_object.editing = False
                        self.selected_object = None
                        self.update()
                return

            elif self.move_mode:
                if self.selected_object:
                    # 检查是否点击了对象本身（而不是控制点）
                    if self.selected_object.contains_point(pos):
                        self.move_start_pos = pos
                        # 计算鼠标位置相对于对象中心点的偏移
                        obj_center = self.selected_object.bounding_rect.center()
                        self.move_object_offset = obj_center - pos
                    else:
                        # 如果没有点击当前选中的对象，尝试选择其他对象
                        self.selected_object.selected = False
                        self.selected_object.editing = False
                        self.selected_object = None

                        for obj in reversed(self.objects):
                            if obj.contains_point(pos):
                                obj.selected = True
                                obj.editing = True
                                self.selected_object = obj
                                self.move_start_pos = pos
                                obj_center = obj.bounding_rect.center()
                                self.move_object_offset = obj_center - pos
                                break
                        self.update()
                else:
                    # 如果没有选中的对象，尝试选择一个
                    for obj in reversed(self.objects):
                        if obj.contains_point(pos):
                            obj.selected = True
                            obj.editing = True
                            self.selected_object = obj
                            self.move_start_pos = pos
                            obj_center = obj.bounding_rect.center()
                            self.move_object_offset = obj_center - pos
                            break
                    self.update()
                return

            elif self.edit_mode:
                if self.selected_object:
                    point_index = self.selected_object.get_point_index(pos)
                    if point_index >= 0:
                        self.editing_point_index = point_index
                        return

                # 在编辑模式下选择对象
                self.selected_object = None
                for obj in reversed(self.objects):
                    if obj.contains_point(pos):
                        if obj.selected:
                            obj.selected = False
                            obj.editing = False
                            self.selected_object = None
                        else:
                            for o in self.objects:
                                o.selected = False
                                o.editing = False

                            obj.selected = True
                            obj.editing = True
                            self.selected_object = obj
                        self.update()
                        return

                if self.selected_object is None:
                    for obj in self.objects:
                        obj.selected = False
                        obj.editing = False
                    self.update()
                return

            self.drawing = True
            if self.shape == Shape.FREEHAND:
                self.freehand_path = [pos]
            else:
                self.drawing_object = DrawingObject(self.shape, [pos], self.color, self.pen_width)

    def mouseMoveEvent(self, event):
        # 获取鼠标在画布上的物理坐标
        physical_x = event.pos().x()
        physical_y = event.pos().y()

        # 转换为逻辑坐标（考虑缩放）
        logical_x = physical_x / self.zoom_factor
        logical_y = physical_y / self.zoom_factor

        # 转换为整数逻辑坐标（用于绘图操作）
        pos = QPoint(int(logical_x), int(logical_y))

        # 计算数学坐标（与导出时的计算方式保持一致）
        # 使用与导出时相同的逻辑：相对于原点的偏移
        math_x = logical_x - self.origin_x
        math_y = self.origin_y - logical_y  # y轴翻转

        # 更新坐标显示
        parent_widget = self.parentWidget()
        if parent_widget and hasattr(parent_widget, 'coord_label'):
            parent_widget.coord_label.setText(
                f"Mouse coordinates: Canvas({logical_x:.1f}, {logical_y:.1f}) | Mathematical ({math_x:.1f}, {math_y:.1f})"
            )

        if self.rotate_mode and self.selected_object and self.rotation_start_pos:
            # 计算旋转角度
            center = self.rotation_center
            start_vec = QLineF(center.x(), center.y(),
                               self.rotation_start_pos.x(), self.rotation_start_pos.y())
            current_vec = QLineF(center.x(), center.y(),
                                 pos.x(), pos.y())

            angle = current_vec.angleTo(start_vec)
            if angle > 180:
                angle -= 360

            # 临时旋转对象用于预览
            self.selected_object.rotation_angle += angle
            self.rotation_start_pos = pos
            self.update()
            return

        elif self.move_mode and self.selected_object and self.move_start_pos:
            # 计算移动距离
            dx = pos.x() - self.move_start_pos.x()
            dy = pos.y() - self.move_start_pos.y()

            # 移动对象
            self.selected_object.move(dx, dy)
            self.move_start_pos = pos
            self.update()
            return

        elif self.edit_mode and self.editing_point_index >= 0 and self.selected_object:
            self.selected_object.points[self.editing_point_index] = pos
            self.selected_object.update_bounding_rect()
            self.update()
            return

        if self.drawing:
            self.current_point = pos
            if self.shape == Shape.FREEHAND:
                self.freehand_path.append(pos)
            elif self.drawing_object:
                if len(self.drawing_object.points) == 1:
                    self.drawing_object.points.append(pos)
                else:
                    self.drawing_object.points[-1] = pos
            self.update()

    def mouseReleaseEvent(self, event):
        # 获取鼠标在画布上的物理坐标
        physical_x = event.pos().x()
        physical_y = event.pos().y()

        # 转换为逻辑坐标（考虑缩放）
        logical_x = physical_x / self.zoom_factor
        logical_y = physical_y / self.zoom_factor

        # 转换为整数逻辑坐标（用于绘图操作）
        pos = QPoint(int(logical_x), int(logical_y))

        if self.rotate_mode and self.selected_object and self.rotation_start_pos:
            # 结束旋转并保存状态
            self.save_state()
            self.rotation_start_pos = None
            return

        elif self.move_mode and self.selected_object and self.move_start_pos:
            # 结束移动并保存状态
            self.save_state()
            self.move_start_pos = None
            return

        if self.edit_mode and self.editing_point_index >= 0:
            self.editing_point_index = -1
            self.save_state()
            return

        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False

            if self.shape == Shape.FREEHAND:
                if len(self.freehand_path) > 1:
                    obj = DrawingObject(
                        Shape.FREEHAND,
                        self.freehand_path.copy(),
                        self.color,
                        self.pen_width
                    )
                    self.objects.append(obj)
                    self.save_state()
            elif self.drawing_object:
                if len(self.drawing_object.points) == 1:
                    self.drawing_object.points.append(pos)
                self.drawing_object.update_bounding_rect()
                self.objects.append(self.drawing_object)
                self.drawing_object = None
                self.save_state()

            self.freehand_path = []
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.scale(self.zoom_factor, self.zoom_factor)
        painter.fillRect(self.rect(), Qt.white)

        # 绘制坐标系网格和坐标轴
        self.draw_grid_and_axes(painter)

        for obj in self.objects:
            obj.draw(painter)

        if self.drawing_object:
            self.drawing_object.draw(painter)

        if self.shape == Shape.FREEHAND and self.freehand_path:
            painter.setPen(QPen(self.color, self.pen_width))
            if len(self.freehand_path) > 1:
                path = QPainterPath()
                path.moveTo(self.freehand_path[0])
                for point in self.freehand_path[1:]:
                    path.lineTo(point)
                painter.drawPath(path)
            elif len(self.freehand_path) == 1:
                painter.drawPoint(self.freehand_path[0])

        if self.edit_mode:
            painter.setPen(QPen(Qt.blue, 1, Qt.DashLine))
            if not self.selected_object:
                painter.drawText(20, 30, "Edit Mode: Click the graphic to select it for editing")
            else:
                painter.drawText(20, 30, f"Edit Mode: {self.selected_object.shape_type} objects have been selected")

        if self.rotate_mode:
            painter.setPen(QPen(Qt.red, 1, Qt.DashLine))
            if self.selected_object:
                center = self.selected_object.bounding_rect.center()
                painter.drawEllipse(QRect(center.x() - 3, center.y() - 3, 6, 6))
                painter.drawText(20, 30, "Rotate Mode: Drag the mouse to rotate the object")
            else:
                painter.drawText(20, 30, "Rotate Mode: Click to select the object you want to rotate")

        if self.move_mode:
            painter.setPen(QPen(Qt.green, 1, Qt.DashLine))
            if self.selected_object:
                painter.drawText(20, 30, "Mobile Mode: Drag the mouse to move the object")
            else:
                painter.drawText(20, 30, "Mobile Mode: Click to select the object you want to move")

    def save_points_to_file(self):
        """将裁剪、平移和排序后的点集保存到TXT文件"""
        # 获取坐标原点位置
        origin_x = self.origin_x
        origin_y = self.origin_y

        # 收集所有形状在x轴以上的轮廓点
        all_points = []
        for obj in self.objects:
            # 获取形状的轮廓点
            outline_points = obj.get_outline_points(step=10)

            # 过滤x轴以上的点 (在画布坐标系中，y值小于原点y值表示在x轴上方)
            for point in outline_points:
                if point.y() < origin_y:
                    all_points.append(point)

        if not all_points:
            QMessageBox.information(self, "Warning", "No graphic data available for saving")
            return

        # 找到最左下角的点（在画布坐标系中）
        # 最左下角 = x最小 + y最大（因为画布中y向下增长）
        min_x = min(p.x() for p in all_points)
        max_y = max(p.y() for p in all_points)

        # 转换到数学坐标系（左下角为原点，y向上）
        math_points = []
        for point in all_points:
            # x坐标：相对于最左点
            # y坐标：相对于原点，并转换为正数（翻转y轴）
            math_x = point.x() - min_x
            math_y = origin_y - point.y()  # 相对于x轴翻转

            # 确保所有点在正象限
            if math_x < 0 or math_y < 0:
                continue

            math_points.append((math_x, math_y))

        if not math_points:
            QMessageBox.information(self, "Warning", "No valid points after conversion")
            return

        # 找到转换后的最左下角点（数学坐标系）
        start_point = min(math_points, key=lambda p: (p[0], p[1]))

        # 修复排序算法
        sorted_points = self._sort_points_by_proximity(math_points, start_point)

        # 保存到文件
        file_path, _ = QFileDialog.getSaveFileName(self, "Save point set data", "",
                                                   "TXT (*.txt);;All kinds (*)")
        if file_path:
            try:
                # 确保文件扩展名正确
                if not file_path.lower().endswith('.txt'):
                    file_path += '.txt'

                with open(file_path, 'w') as f:
                    # 确保起始点是(0,0)
                    if sorted_points and sorted_points[0] != (0, 0):
                        # 计算偏移量使起始点为(0,0)
                        offset_x, offset_y = sorted_points[0]
                        adjusted_points = [(x - offset_x, y - offset_y) for x, y in sorted_points]
                        sorted_points = adjusted_points

                    for x, y in sorted_points:
                        f.write(f"{x:.2f},{y:.2f}\n")  # 保存两位小数

                QMessageBox.information(self, "Successfully", f"Point set data has been saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error occurred when saving file: {str(e)}")

    def _sort_points_by_proximity(self, points, start_point=None):
        """使用最近点原则对点集进行排序（修复版）"""
        if not points:
            return []

        # 转换为列表以便修改
        points = list(points)

        # 设置起始点
        if start_point is None:
            # 默认找最左下角的点 (x最小, y最小)
            start_point = min(points, key=lambda p: (p[0], p[1]))

        sorted_points = [start_point]
        points.remove(start_point)

        while points:
            last_point = sorted_points[-1]
            # 找到剩余点中距离上一个点最近的点
            next_point = min(points,
                             key=lambda p: math.sqrt((p[0] - last_point[0]) ** 2 + (p[1] - last_point[1]) ** 2))
            sorted_points.append(next_point)
            points.remove(next_point)

        return sorted_points


class DrawingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 300)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # ===== 第一行工具栏：形状选择 =====
        shape_toolbar = QHBoxLayout()
        shape_toolbar.setContentsMargins(0, 0, 0, 0)
        shape_toolbar.setSpacing(10)

        shape_label = QLabel("Shape:")
        shape_toolbar.addWidget(shape_label)

        self.shape_group = QButtonGroup(self)
        self.line_btn = QRadioButton("Line")
        self.line_btn.setChecked(True)
        self.shape_group.addButton(self.line_btn)
        shape_toolbar.addWidget(self.line_btn)

        self.arc_btn = QRadioButton("Arc")
        self.shape_group.addButton(self.arc_btn)
        shape_toolbar.addWidget(self.arc_btn)

        self.freehand_btn = QRadioButton("Free_style")
        self.shape_group.addButton(self.freehand_btn)
        shape_toolbar.addWidget(self.freehand_btn)

        shape_toolbar.addStretch()
        main_layout.addLayout(shape_toolbar)

        # ===== 第二行工具栏：编辑和设置 =====
        edit_toolbar = QHBoxLayout()
        edit_toolbar.setContentsMargins(0, 0, 0, 0)
        edit_toolbar.setSpacing(10)

        # 编辑按钮
        self.edit_btn = QPushButton("Vertex")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setMinimumWidth(100)  # 改为最小宽度，允许内容扩展
        edit_toolbar.addWidget(self.edit_btn)

        # 旋转按钮
        self.rotate_btn = QPushButton("Rotation")
        self.rotate_btn.setCheckable(True)
        self.rotate_btn.setMinimumWidth(100)
        edit_toolbar.addWidget(self.rotate_btn)

        # 移动按钮
        self.move_btn = QPushButton("Move")
        self.move_btn.setCheckable(True)
        self.move_btn.setMinimumWidth(100)
        edit_toolbar.addWidget(self.move_btn)

        # 添加弹簧使按钮居中
        edit_toolbar.addStretch()
        main_layout.addLayout(edit_toolbar)

        # ===== 新增：坐标显示栏 =====
        self.coord_label = QLabel("Mouse coordinates: Canvas(0.0, 0.0) | Mathematical(0.0, 0.0)")
        self.coord_label.setAlignment(Qt.AlignCenter)
        self.coord_label.setStyleSheet("border: 1px solid #ccc; padding: 2px;")
        main_layout.addWidget(self.coord_label)

        # ===== 画布区域 =====
        self.drawing_area = DrawingArea()
        main_layout.addWidget(self.drawing_area, 1)

        # ===== 第三行工具栏：操作按钮 =====
        action_toolbar = QHBoxLayout()
        action_toolbar.setContentsMargins(0, 0, 0, 0)
        action_toolbar.setSpacing(10)

        # 撤销按钮
        self.undo_btn = QPushButton("Cancel")
        self.undo_btn.setMinimumWidth(80)
        action_toolbar.addWidget(self.undo_btn)

        # 删除选中按钮
        self.clear_btn = QPushButton("Delete")
        self.clear_btn.setMinimumWidth(80)
        action_toolbar.addWidget(self.clear_btn)

        # 清除画布按钮
        self.clear_all_btn = QPushButton("Clear")
        self.clear_all_btn.setMinimumWidth(80)
        action_toolbar.addWidget(self.clear_all_btn)

        # OK按钮
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setMinimumWidth(80)
        action_toolbar.addWidget(self.ok_btn)

        action_toolbar.addStretch()
        main_layout.addLayout(action_toolbar)

        # 连接信号
        self.shape_group.buttonClicked.connect(self.set_shape)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.rotate_btn.clicked.connect(self.toggle_rotate_mode)
        self.move_btn.clicked.connect(self.toggle_move_mode)
        self.undo_btn.clicked.connect(self.drawing_area.undo)
        self.clear_btn.clicked.connect(self.drawing_area.clear_selected)
        self.clear_all_btn.clicked.connect(self.drawing_area.clear_all)
        self.ok_btn.clicked.connect(self.drawing_area.save_points_to_file)

    def set_shape(self, button):
        if button == self.line_btn:
            self.drawing_area.set_shape(Shape.LINE)
        elif button == self.arc_btn:
            self.drawing_area.set_shape(Shape.ARC)
        elif button == self.freehand_btn:
            self.drawing_area.set_shape(Shape.FREEHAND)
        self.drawing_area.exit_all_modes()
        self.edit_btn.setChecked(False)
        self.rotate_btn.setChecked(False)
        self.move_btn.setChecked(False)

    def toggle_edit_mode(self, checked):
        if checked:
            self.drawing_area.enter_edit_mode()
            self.rotate_btn.setChecked(False)
            self.move_btn.setChecked(False)
        else:
            self.drawing_area.exit_all_modes()

    def toggle_rotate_mode(self, checked):
        if checked:
            self.drawing_area.enter_rotate_mode()
            self.edit_btn.setChecked(False)
            self.move_btn.setChecked(False)
        else:
            self.drawing_area.exit_all_modes()

    def toggle_move_mode(self, checked):
        if checked:
            self.drawing_area.enter_move_mode()
            self.edit_btn.setChecked(False)
            self.rotate_btn.setChecked(False)
        else:
            self.drawing_area.exit_all_modes()


class DrawingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing Application")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        title_label = QLabel("Pattern Design Tool")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        main_layout.addWidget(title_label)

        self.drawing_widget = DrawingWidget()
        main_layout.addWidget(self.drawing_widget, 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DrawingApp()
    window.show()
    sys.exit(app.exec_())