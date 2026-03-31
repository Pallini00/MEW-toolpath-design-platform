import ezdxf
import pyautocad
from PyQt5 import QtCore, QtGui, QtWidgets
import os
import sys
import importlib.util
import tempfile
import traceback
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from region_selection import RegionSelector
import customization
import pattern_transformation
from ui_styles import UIStyles
from basic_pattern_design import DrawingArea,DrawingWidget
import tempfile
import subprocess
import shutil
import curve_printing as cp



# ========== 登录窗口类 ==========
class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("LoginWindow")
        # 绑定登录按钮事件
        self.ui.pushButton.clicked.connect(self.check_login)

    def check_login(self):
        # 获取输入内容
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        # 简单验证逻辑
        if username and password:
            self.main_window = MainWindow()  # 创建主窗口实例
            self.main_window.show()  # 显示主窗口
            self.close()  # 关闭登录窗口
        else:
            QtWidgets.QMessageBox.warning(self, "Warning", "Username and password cannot be blank！")


# ========== 主窗口类 ==========
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("MainWindow")
        UIStyles.optimize_main_ui(self.ui)
        self.transform_menu = QtWidgets.QMenu(self)
        # 创建绘图区域实例
        self.drawing_widget = DrawingWidget()
        self.drawing_widget.setMinimumSize(400, 300)
        # 将绘图区域添加到布局
        self.ui.drawing_container.layout().addWidget(self.drawing_widget)
        # 绑定业务逻辑
        self.ui.pushButton_4.clicked.connect(self.export_image)
        self.ui.pushButton_6.clicked.connect(self.generate_gcode)
        self.ui.pushButton_3.clicked.connect(self.cancel)
        self.ui.pushButton_5.clicked.connect(self.show_transform_menu)
        self.ui.pushButton.clicked.connect(self.show_load_options)
        self.ui.pushButton_8.clicked.connect(self.import_txt_file)
        self.undo_stack = []
        self.max_undo_steps = 20  # 操作历史栈
        self.current_item = None  # 当前操作的图形项
        self.current_points = None  # 存储当前坐标点
        self.saving_state = False
        self.setup_initial_scene()  # 初始化场景
        self.setup_view_properties()
        self.setup_hover_preview()
        self.setup_tree_item_previews()
        # 添加点列容器
        self.point_set = []  # 存储所有点集的列表
        self.current_point_index = -1  # 当前显示的点集索引
        self.selected_points = None
        self.unselected_points = None
        # 设置场景变化监听
        self.scene.changed.connect(self.scene_changed)
        self.ui.treeWidget.itemClicked.connect(self.handle_tree_item_clicked)
        # 添加区域选择器
        self.region_selector = RegionSelector(self.scene, self.handle_region_selected)
        self.scene.addItem(self.region_selector)
        # 连接鼠标事件
        self.ui.graphicsView.setMouseTracking(True)
        self.ui.graphicsView.viewport().installEventFilter(self)
        self.selecting_region = False
        self.ui.pushButton_7.clicked.connect(self.show_region_shape_menu)
        self.region_coords = None  # 存储区域坐标 (Xmin, Ymin, Xmax, Ymax)
        self.coord_label = QtWidgets.QLabel()
        self.statusBar().addPermanentWidget(self.coord_label)
        self.has_selected_region = False
        self.region_shape = "rectangle"
        self.region_selector_manager = RegionSelector(self.scene, self.handle_region_selected)
        self.selector_menu = None  # 选择器类型菜单

    def show_region_shape_menu(self):
        """显示选框形状选择菜单"""
        if self.current_points is None or len(self.current_points) == 0:
            QtWidgets.QMessageBox.warning(self, "Warning", "No points selected")
            return
        shape_menu = QtWidgets.QMenu(self)
        rectangle_action = shape_menu.addAction("Rectangle Selection")
        ellipse_action = shape_menu.addAction("Ellipse Selection")
        hexagon_action = shape_menu.addAction("Hexagon Selection")
        custom_action = shape_menu.addAction("Custom Polygon Selection")
        # 连接菜单项到相应的处理函数
        rectangle_action.triggered.connect(lambda: self.activate_region_selection("rectangle"))
        ellipse_action.triggered.connect(lambda: self.activate_region_selection("ellipse"))
        hexagon_action.triggered.connect(lambda: self.activate_region_selection("hexagon"))
        custom_action.triggered.connect(lambda: self.activate_region_selection("custom"))
        # 显示菜单
        global_pos = self.ui.pushButton_7.mapToGlobal(QtCore.QPoint(0, self.ui.pushButton_7.height()))
        shape_menu.exec_(global_pos)

    def setup_region_selector(self):
        """创建并添加区域选择器到场景"""
        self.region_selector = RegionSelector(self.scene, self.handle_region_selected)
        self.scene.addItem(self.region_selector)
        self.region_selector.setZValue(100)  # 确保选择框在最上层
    def setup_hover_preview(self):
        """设置悬停预览功能"""
        # 启用鼠标跟踪
        self.ui.treeWidget.setMouseTracking(True)
        # 连接悬停信号
        self.ui.treeWidget.itemEntered.connect(self.show_item_preview)
        self.ui.treeWidget.leaveEvent = self.hide_preview_on_leave
        # 创建预览标签
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setWindowFlags(QtCore.Qt.ToolTip | QtCore.Qt.FramelessWindowHint)
        self.preview_label.setStyleSheet("""
            background-color: white; 
            border: 2px solid #4a90e2;
            border-radius: 5px;
            padding: 5px;
        """)
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.preview_label.setFixedSize(150, 150)

    def hide_preview_on_leave(self, event):
        """当鼠标离开 treeWidget 时隐藏预览"""
        self.preview_label.hide()
        event.accept()

    def setup_tree_item_previews(self):
        """为treeWidget的项目设置预览数据"""
        # 创建预览图片字典
        self.preview_images = {}
        # 多边形预览
        top0 = self.ui.treeWidget.topLevelItem(0)
        self.preview_images["Triangle"] = self.create_preview_image("Triangle")
        self.preview_images["Quadrilateral"] = self.create_preview_image("Quadrilateral")
        self.preview_images["Hexagon"] = self.create_preview_image("Hexagon")
        self.preview_images["Tessellation_1"] = self.create_preview_image("Tessellation_1")
        self.preview_images["Tessellation_2"] = self.create_preview_image("Tessellation_2")
        self.preview_images["Tessellation_3"] = self.create_preview_image("Tessellation_3")
        self.preview_images["Tessellation_4"] = self.create_preview_image("Tessellation_4")
        self.preview_images["Tessellation_5"] = self.create_preview_image("Tessellation_5")
        self.preview_images["Tessellation_6"] = self.create_preview_image("Tessellation_6")
        self.preview_images["Tessellation_7"] = self.create_preview_image("Tessellation_7")
        self.preview_images["Tessellation_8"] = self.create_preview_image("Tessellation_8")
        self.preview_images["Tessellation_9"] = self.create_preview_image("Tessellation_9")
        # 圆形预览
        top1 = self.ui.treeWidget.topLevelItem(1)
        self.preview_images["Normal Layout"] = self.create_preview_image("Normal Layout")
        self.preview_images["Dense Layout"] = self.create_preview_image("Dense Layout")
        self.preview_images["Arc"] = self.create_preview_image("Arc")
        # 三角函数预览
        top2 = self.ui.treeWidget.topLevelItem(2)
        self.preview_images["Trigonometric"] = self.create_preview_image("Trigonometric")
        # 其他预览
        top3 = self.ui.treeWidget.topLevelItem(3)
        self.preview_images["Windmill"] = self.create_preview_image("Windmill")
        self.preview_images["Bell"] = self.create_preview_image("Bell")
        self.preview_images["Flowery"] = self.create_preview_image("Flowery")
        self.preview_images["Hexagram"] = self.create_preview_image("Hexagram")
        self.preview_images["Coin"] = self.create_preview_image("Coin")
        self.preview_images["Gradient"] = self.create_preview_image("Gradient")

    def create_preview_image(self, shape_name):
        """根据形状名称加载预览图像"""
        # 创建图片路径映射
        image_paths = {
            "Triangle": "Exiting_pattern/Triangle.png",
            "Quadrilateral": "Exiting_pattern/Quadrilateral.png",
            "Hexagon": "Exiting_pattern/Hexagon.png",
            "Tessellation_1": "Exiting_pattern/Tessellation_1.png",
            "Tessellation_2": "Exiting_pattern/Tessellation_2.png",
            "Tessellation_3": "Exiting_pattern/Tessellation_3.png",
            "Tessellation_4": "Exiting_pattern/Tessellation_4.png",
            "Tessellation_5": "Exiting_pattern/Tessellation_5.png",
            "Tessellation_6": "Exiting_pattern/Tessellation_6.png",
            "Tessellation_7": "Exiting_pattern/Tessellation_7.png",
            "Tessellation_8": "Exiting_pattern/Tessellation_8.png",
            "Tessellation_9": "Exiting_pattern/Tessellation_9.png",
            "Normal Layout": "Exiting_pattern/Normal Layout.png",
            "Dense Layout": "Exiting_pattern/Dense Layout.png",
            "Arc": "Exiting_pattern/Arc.png",
            "Trigonometric": "Exiting_pattern/Trigonometric.png",
            "Windmill": "Exiting_pattern/Windmill.png",
            "Bell": "Exiting_pattern/Bell.png",
            "Flowery": "Exiting_pattern/Flowery.png",
            "Hexagram": "Exiting_pattern/Hexagram.png",
            "Coin": "Exiting_pattern/Coin.png",
            "Gradient": "Exiting_pattern/Gradient.png"
        }
        # 获取图片路径
        path = image_paths.get(shape_name)
        if not path:
            # 默认图片
            path = "path/to/default/image.png"
        # 加载图片
        pixmap = QtGui.QPixmap(path)
        # 缩放图片到合适尺寸
        if not pixmap.isNull():
            pixmap = pixmap.scaled(130, 130, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        return pixmap

    def show_item_preview(self, item, column):
        """显示项目的预览图"""
        if not item or item.childCount() > 0:  # 只对子项目显示预览
            self.preview_label.hide()
            return
        # 获取项目文本
        item_text = item.text(0)
        if not item_text:
            return
        # 获取预览图
        pixmap = self.preview_images.get(item_text)
        if not pixmap:
            return
        # 设置预览标签
        self.preview_label.setPixmap(pixmap)
        self.preview_label.adjustSize()
        # 获取鼠标位置
        cursor_pos = QtGui.QCursor.pos()
        # 显示预览标签（稍微偏移以避免遮挡鼠标）
        self.preview_label.move(cursor_pos.x() + 15, cursor_pos.y() + 15)
        self.preview_label.show()

    def show_load_options(self):
        """弹出选项让用户选择加载方式"""
        items = ["A: Load two TXT files (forward/backward)", "B: Process image to Eulerian path"]
        choice, ok = QtWidgets.QInputDialog.getItem(
            self, "Select Load Mode", "Choose an option:", items, 0, False)
        if not ok:
            return
        if choice.startswith("A"):
            self.open_file_dialog()  # 原有的方法
        else:
            self.load_image_for_eulerian()



    def setup_view_properties(self):
        """设置视图属性以实现等比例缩放"""
        # 设置抗锯齿渲染
        self.ui.graphicsView.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.ui.graphicsView.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        # 设置视图的缩放行为
        self.ui.graphicsView.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.ui.graphicsView.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.ui.graphicsView.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        # 设置缩放因子限制
        self.min_scale = 0.1
        self.max_scale = 10.0
        self.current_scale = 1.0
        # 安装事件过滤器以处理滚轮缩放
        self.ui.graphicsView.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        """处理视图的滚轮缩放事件"""
        if source is self.ui.graphicsView.viewport() and event.type() == QtCore.QEvent.Wheel:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                # 计算缩放因子
                delta = event.angleDelta().y()
                factor = 1.1 if delta > 0 else 0.9
                # 应用缩放并限制范围
                self.current_scale *= factor
                if self.current_scale < self.min_scale:
                    self.current_scale = self.min_scale
                    return True  # 阻止进一步处理
                elif self.current_scale > self.max_scale:
                    self.current_scale = self.max_scale
                    return True  # 阻止进一步处理
                self.ui.graphicsView.scale(factor, factor)
                return True  # 阻止进一步处理

        """处理鼠标事件以实现区域选择"""
        if source is self.ui.graphicsView.viewport():
            # 自定义多边形选择的特殊处理
            if self.selecting_region and self.region_shape == "custom":
                if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                    # 添加点
                    self.region_selector.start_selection(event.pos())
                    return True
                elif event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.RightButton:
                    # 右键完成选择
                    self.selecting_region = False
                    self.region_selector.finish_selection()
                    return True
                elif event.type() == QtCore.QEvent.MouseMove:
                    # 更新预览
                    self.region_selector.update_selection(event.pos())
            elif event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton and self.selecting_region:
                # 开始区域选择
                self.region_selector.start_selection(event.pos())
                return True
            elif event.type() == QtCore.QEvent.MouseMove and self.selecting_region:
                # 更新区域选择
                self.region_selector.update_selection(event.pos())
            elif event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton and self.selecting_region:
                # 完成区域选择
                if self.region_shape != "custom":
                    self.selecting_region = False
                    self.region_selector.finish_selection()
                    return True

        # 处理鼠标移动事件（显示坐标）
        if source is self.ui.graphicsView.viewport() and event.type() == QtCore.QEvent.MouseMove:
            # 获取鼠标位置
            mouse_pos = event.pos()
            # 转换为场景坐标
            scene_pos = self.ui.graphicsView.mapToScene(mouse_pos)
            # 在状态栏显示原始坐标
            self.coord_label.setText(f"X: {scene_pos.x():.2f}, Y: {scene_pos.y():.2f}")
            # 如果有当前图形项且是Matplotlib画布
            if self.current_item and isinstance(self.current_item, QtWidgets.QGraphicsProxyWidget):
                proxy_item = self.current_item
                # 将场景坐标转换为图形项局部坐标
                item_point = proxy_item.mapFromScene(scene_pos)
                canvas = proxy_item.widget()

                if isinstance(canvas, FigureCanvas):
                    # 获取画布尺寸
                    canvas_width = canvas.width()
                    canvas_height = canvas.height()
                    # 转换为画布坐标（注意y轴翻转）
                    canvas_x = item_point.x()
                    canvas_y = canvas_height - item_point.y()
                    try:
                        # 获取坐标轴
                        ax = canvas.figure.axes[0]
                        # 转换为数据坐标
                        inv = ax.transData.inverted()
                        data_point = inv.transform((canvas_x, canvas_y))
                        x, y = data_point
                        # 在状态栏显示坐标
                        self.coord_label.setText(f"X: {x:.3f}, Y: {y:.3f}")
                    except:
                        self.coord_label.setText("")
        return super().eventFilter(source, event)

    def activate_region_selection(self, shape_type):
        """激活区域选择功能"""
        if self.current_points is None or len(self.current_points) == 0:
            QtWidgets.QMessageBox.warning(self, "Warning", "No points selected")
            return
        self.selecting_region = True
        self.region_shape = shape_type
        self.region_selector.set_shape(shape_type)
        # 禁用视图缩放
        self.ui.graphicsView.setInteractive(False)
        self.coord_label.setVisible(True)
        # 确保图形视图具有焦点
        self.ui.graphicsView.setFocus()
        shape_names = {
            "rectangle": "Rectangle",
            "ellipse": "Ellipse",
            "hexagon": "Hexagon",
            "custom": "Custom"
        }
        if shape_type == "custom":
            instruction = (
                f"{shape_names[shape_type]}Region selection mode\n"
                "Left-click to add a polygon vertex\n"
                "Right-click to complete the polygon drawing"
            )
        else:
            instruction = (
                f"{shape_names[shape_type]}Region selection mode\n"
                "Hold down the left mouse button and drag to select an area\n"
                "Release the mouse button to complete the selection"
            )
        QtWidgets.QMessageBox.information(
            self, "Region selection",
            instruction
        )


    def setup_initial_scene(self):
        """初始化图形场景"""
        self.scene = QtWidgets.QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)
        self.setup_region_selector()
        # 添加一个示例矩形
        rect_item = self.scene.addRect(QtCore.QRectF(0, 0, 450, 450),
                                       QtGui.QPen(QtCore.Qt.blue),
                                       QtGui.QBrush(QtCore.Qt.lightGray))
        rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        rect_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.current_item = rect_item
        self.save_state()  # 保存初始状态

    def scene_changed(self):
        """当场景发生变化时自动保存状态"""
        if self.scene.items():
            self.save_state()

    def save_state(self):
        """保存当前场景状态到撤销栈"""
        # 防止在撤销过程中保存状态
        if not hasattr(self, 'saving_state') or self.saving_state:
            return
        try:
            self.saving_state = True  # 设置状态保存标志
            # 保存当前坐标点
            current_points = self.current_points.tolist() if self.current_points is not None else None
            # 保存所有图形项的状态
            state = {
                'items': [],
                'current_points': current_points
            }
            for item in self.scene.items():
                if isinstance(item, QtWidgets.QGraphicsItem):
                    item_state = {
                        'pos': item.pos(),
                        'rotation': item.rotation(),
                        'scale': item.scale(),
                        'zvalue': item.zValue(),
                        'type': type(item).__name__,
                        'properties': {}
                    }
                    # 保存特定类型项的额外属性
                    if isinstance(item, QtWidgets.QGraphicsRectItem):
                        item_state['properties'] = {
                            'rect': item.rect(),
                            'pen': item.pen(),
                            'brush': item.brush()
                        }
                    elif isinstance(item, QtWidgets.QGraphicsProxyWidget):
                        # 对于Matplotlib画布，保存坐标点
                        widget = item.widget()
                        if isinstance(widget, FigureCanvas):
                            item_state['properties'] = {
                                'points': self.current_points.tolist() if self.current_points is not None else []
                            }

                    state['items'].append(item_state)
            # 限制撤销栈大小
            if len(self.undo_stack) >= self.max_undo_steps:
                self.undo_stack.pop(0)  # 移除最旧的状态
            self.undo_stack.append(state)
        finally:
            self.saving_state = False  # 清除状态保存标志
        self.undo_stack.append(state)


    def clear_scene(self):
        """清除场景中除区域选择器外的所有图形项"""
        items_to_keep = [item for item in self.scene.items() if isinstance(item, RegionSelector)]
        for item in self.scene.items()[:]:  # 使用副本遍历
            if item not in items_to_keep:
                self.scene.removeItem(item)
        # 重置点集相关变量
        self.point_set = []
        self.current_point_index = -1
        self.current_points = None
        self.unselected_points = None
        self.selected_points = None
        self.original_points = None
        self.region_coords = None
        self.has_selected_region = False
        self.selecting_region = False


    def handle_tree_item_clicked(self, item, column):
        """处理树形控件项点击事件"""
        # 只处理叶子节点（具体图案）
        if item.childCount() == 0:
            pattern_name = item.text(0)
            if pattern_name == "PS Pattern":
                self.generate_ps_pattern()
            if pattern_name == "PSDD Pattern":
                self.generate_psdd_pattern()
            if pattern_name == "Triangle":
                self.generate_regular_triangle()
            if pattern_name == "Quadrilateral":
                self.generate_square()
            if pattern_name == "Hexagon":
                self.generate_hexagon()
            if pattern_name == "Tessellation_1":
                self.generate_mosaic_pattern1()
            if pattern_name == "Tessellation_2":
                self.generate_mosaic_pattern2()
            if pattern_name == "Tessellation_3":
                self.generate_mosaic_pattern3()
            if pattern_name == "Tessellation_4":
                self.generate_mosaic_pattern4()
            if pattern_name == "Tessellation_5":
                self.generate_mosaic_pattern5()
            if pattern_name == "Tessellation_6":
                self.generate_mosaic_pattern6()
            if pattern_name == "Tessellation_7":
                self.generate_mosaic_pattern7()
            if pattern_name == "Tessellation_8":
                self.generate_mosaic_pattern8()
            if pattern_name == "Tessellation_9":
                self.generate_mosaic_pattern9()
            if pattern_name == "Normal Layout":
                self.generate_normal_circle()
            if pattern_name == "Dense Layout":
                self.generate_dense_circle()
            if pattern_name == "Arc":
                self.generate_arc()
            if pattern_name == "Trigonometric":
                self.generate_sine_wave()
            if pattern_name == "Flowery":
                self.generate_flowery()
            if pattern_name == "Windmill":
                self.generate_windmill()
            if pattern_name == "Hexagram":
                self.generate_hexagonal_pattern()
            if pattern_name == "Bell":
                self.generate_bell_pattern()
            if pattern_name == "Coin":
                self.generate_coin_pattern()
            if pattern_name == "Gradient":
                self.generate_gradient_pattern()

    def handle_region_selected(self, selected_points, unselected_points, region_rect, shape_info=None):
        """处理区域选择结果"""
        if selected_points is None or len(selected_points) == 0:
            QtWidgets.QMessageBox.information(self, "Region selection", "No points selected",QtWidgets.QMessageBox.Ok)
            self.has_selected_region = False
            return
        # 存储区域坐标 (Xmin, Ymin, Xmax, Ymax)
        self.region_coords = (
            region_rect.left(), region_rect.top(),
            region_rect.right(), region_rect.bottom()
        )
        # 存储选中的点和未选中的点
        self.original_points = self.current_points.copy()
        self.selected_points = selected_points
        self.unselected_points = unselected_points
        # 更新当前点集为选中的点
        self.current_points = selected_points
        # 添加到点集容器（只添加选中点）
        self.point_set.append(selected_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形（双色显示）
        self.update_figure_from_points()
        self.ui.pushButton_5.setEnabled(True)
        self.has_selected_region = True
        # 保存形状信息（关键修改）
        if shape_info is not None:
            self.region_shape_type = shape_info.get('type', 'rectangle')
            self.region_shape_params = shape_info
        else:
            self.region_shape_type = 'rectangle'
            self.region_shape_params = None
        # 显示信息但不关闭窗口
        QtWidgets.QMessageBox.information(
            self, "Complete the region selection",
            f"Selected {len(selected_points)} points\n"
            "choose transformation on selected points",QtWidgets.QMessageBox.Ok
        )
        self.ui.graphicsView.setInteractive(True)
        self.coord_label.setText("")




    def generate_ps_pattern(self):
        try:
            # 动态导入regular_ps_pattern模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            ps_pattern = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ps_pattern)
            points = ps_pattern.generate_ps_pattern()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_1:\n{str(e)}"
            )

    def generate_psdd_pattern(self):
        try:
            # 动态导入regular_ps_pattern模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            psdd_pattern = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(psdd_pattern)
            points = psdd_pattern.generate_psdd_pattern()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_1:\n{str(e)}"
            )

    def generate_regular_triangle(self):
        """调用regular_triangle.py生成三角形点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            regular_triangle = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(regular_triangle)
            points = regular_triangle.generate_regular_triangle()
        # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
               reply = QtWidgets.QMessageBox.information(
                  self, "Successfully", f"Generated {len(points)} points successfully",
                QtWidgets.QMessageBox.Ok
            )
               if reply == QtWidgets.QMessageBox.Ok:
                   self.clear_scene()
                   self.current_points = points
                   self.point_set.append(points.copy())
                   self.current_point_index = len(self.point_set) - 1
                   self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                  QtWidgets.QMessageBox.warning(
                  self, "Warning", "Invalid coordinate point data generated"
                  )

        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
            self, "Error", f"Failed to generate triangle:\n{str(e)}"
            )

    def generate_square(self):
        """调用regular_triangle.py生成四边形点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            square = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(square)
            points = square.generate_square()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate quadrilateral:\n{str(e)}"
            )

    def generate_hexagon(self):
        """调用regular_hexagon.py生成六边形点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            hexagon = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hexagon)
            points = hexagon.generate_hexagon()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate hexagon:\n{str(e)}"
            )



    def generate_mosaic_pattern1(self):
        """调用regular_triangle.py生成镶嵌结构1点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_1 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_1)
            points = mosaic_1.generate_mosaic_pattern1()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_1:\n{str(e)}"
            )



    def generate_mosaic_pattern2(self):
        """调用regular_triangle.py生成镶嵌结构2点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_2 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_2)
            points = mosaic_2.generate_mosaic_pattern2()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_2:\n{str(e)}"
            )



    def generate_mosaic_pattern3(self):
        """调用regular_triangle.py生成镶嵌结构3点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_3 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_3)
            points = mosaic_3.generate_mosaic_pattern3()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_3:\n{str(e)}"
            )



    def generate_mosaic_pattern4(self):
        """调用regular_triangle.py生成镶嵌结构4点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_4 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_4)
            points = mosaic_4.generate_mosaic_pattern4()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_4:\n{str(e)}"
            )

    def generate_mosaic_pattern5(self):
        """调用regular_triangle.py生成镶嵌结构5点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_5 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_5)
            points = mosaic_5.generate_mosaic_pattern5()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_5:\n{str(e)}"
            )


    def generate_mosaic_pattern6(self):
        """调用regular_triangle.py生成镶嵌结构6点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_6 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_6)
            points = mosaic_6.generate_mosaic_pattern6()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_6:\n{str(e)}"
            )


    def generate_mosaic_pattern7(self):
        """调用regular_triangle.py生成镶嵌结构7点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_7 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_7)
            points = mosaic_7.generate_mosaic_pattern7()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_7:\n{str(e)}"
            )


    def generate_mosaic_pattern8(self):
        """调用regular_triangle.py生成镶嵌结构8点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_8 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_8)
            points = mosaic_8.generate_mosaic_pattern8()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_8:\n{str(e)}"
            )



    def generate_mosaic_pattern9(self):
        """调用regular_triangle.py生成镶嵌结构9点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            mosaic_9 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mosaic_9)
            points = mosaic_9.generate_mosaic_pattern9()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate tessellate_9:\n{str(e)}"
            )



    def generate_normal_circle(self):
        """调用regular_triangle.py生成普通堆积点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            normal_circle = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(normal_circle)
            points = normal_circle.generate_normal_circle()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate normal layout:\n{str(e)}"
            )

    def generate_dense_circle(self):
        """调用regular_triangle.py生成密集堆积点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            dense_circle = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dense_circle)
            points = dense_circle.generate_dense_circle()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate dense layout:\n{str(e)}"
            )


    def generate_arc(self):
        """调用regular_triangle.py生成密集堆积点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            arc = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(arc)
            points = arc.generate_arc()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate arc:\n{str(e)}"
            )


    def generate_sine_wave(self):
        """调用regular_triangle.py生成三角函数点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            sine_wave = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sine_wave)
            points = sine_wave.generate_sine_wave()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate trigonometric:\n{str(e)}"
            )


    def generate_flowery(self):
        """调用regular_triangle.py生成花朵图案点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            flower = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(flower)
            points = flower.generate_flower()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate flowery:\n{str(e)}"
            )


    def generate_windmill(self):
        """调用regular_triangle.py生成风车图案点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            windmill = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(windmill)
            points = windmill.generate_windmill()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate windmill:\n{str(e)}"
            )



    def generate_hexagonal_pattern(self):
        """调用regular_triangle.py生成六角图案点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            hexagonal_pattern = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hexagonal_pattern)
            points = hexagonal_pattern.generate_hexagonal_pattern()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate hexagram:\n{str(e)}"
            )



    def generate_bell_pattern(self):
        """调用regular_triangle.py生成铃铛图案点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            bell_pattern = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bell_pattern)
            points = bell_pattern.generate_bell_pattern()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate bell:\n{str(e)}"
            )




    def generate_coin_pattern(self):
        """调用regular_triangle.py生成硬币图案点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            coin_pattern = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(coin_pattern)
            points = coin_pattern.generate_coin_pattern()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate coin:\n{str(e)}"
            )




    def generate_gradient_pattern(self):
        """调用regular_triangle.py生成渐变图案点集"""
        try:
            # 动态导入regular_triangle模块
            import pattern_generators
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.join(current_dir, "pattern_generators.py")
            spec = importlib.util.spec_from_file_location("pattern_generators", module_path)
            gradient_pattern = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gradient_pattern)
            points = gradient_pattern.generate_gradient_pattern()
            # 确保points是二维数组
            if points.size > 0 and points.ndim == 2 and points.shape[1] == 2:
                reply = QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Generated {len(points)} points successfully",
                    QtWidgets.QMessageBox.Ok
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.clear_scene()
                    self.current_points = points
                    self.point_set.append(points.copy())
                    self.current_point_index = len(self.point_set) - 1
                    self.update_figure_from_points()  # 用户点击OK后更新视图
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "Invalid coordinate point data generated"
                )
        except Exception as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate gradient pattern:\n{str(e)}"
            )





    def get_figure_data(self, figure):
        """获取Matplotlib图形的数据"""
        from io import BytesIO
        import pickle
        fig_data = {
            'points': self.current_points,  # 保存原始坐标数据
            'figure_settings': {
                'figsize': figure.get_size_inches(),
                'dpi': figure.get_dpi()
            }
        }
        buffer = BytesIO()
        pickle.dump(fig_data, buffer)
        buffer.seek(0)
        return buffer.getvalue()


    def restore_figure(self, figure_data):
        """从数据恢复Matplotlib图形"""
        from io import BytesIO
        from matplotlib.image import imread
        import pickle
        import numpy as np
        buffer = BytesIO(figure_data)
        fig_data = pickle.load(buffer)

        # 恢复原始坐标点
        points = fig_data['points']

        # 重新创建图形（使用原始数据）
        fig = Figure(figsize=fig_data['figure_settings']['figsize'],
                     dpi=fig_data['figure_settings']['dpi'])
        ax = fig.add_subplot(111)

        # 重新绘制图形（与process_txt_file中相同的逻辑）
        ax.plot(points[:, 0], points[:, 1],  s=0.1,color='black', edgecolors='black',label='point')
        if len(points) > 1:
            ax.plot(points[:, 0], points[:, 1], color='black', alpha=0.5,linewidth=0.5, label='line')
        ax.set_title('Pattern Visualization')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.grid(True, linestyle='--', alpha=0.1)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        ax.set_aspect('equal', 'box')
        # 恢复坐标范围
        x_min, x_max = np.min(points[:, 0]), np.max(points[:, 0])
        y_min, y_max = np.min(points[:, 1]), np.max(points[:, 1])
        padding = max((x_max - x_min) * 0.1, (y_max - y_min) * 0.1, 0.5)
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.25)
        return fig

    def cancel(self):
        """撤销上一步操作 - 基于点列容器实现"""
        # 检查是否有可撤销的操作
        if len(self.point_set) > 1 and self.current_point_index > 0:
            try:
                # 回退到前一个点列状态
                self.current_point_index -= 1
                # 恢复点列
                self.current_points = self.point_set[self.current_point_index]
                # 更新图形
                self.update_figure_from_points()

                QtWidgets.QMessageBox.information(
                    self, "Successfully", "Undo successfully"
                )
            except Exception as e:
                traceback.print_exc()
                QtWidgets.QMessageBox.critical(
                    self, "Undo Error", f"Undo operation failed:\n{str(e)}"
                )
        else:
            QtWidgets.QMessageBox.information(
                self, "Undo Disabled", "No undoable actions"
            )


    def create_figure_from_points(self, points):
        """根据坐标点创建Matplotlib图形"""
        fig = Figure(figsize=(5, 4), dpi=1000)
        ax = fig.add_subplot(111)
        # 绘制坐标点（散点图）
        ax.plot(points[:, 0], points[:, 1],  s=0.001,color='black', edgecolors='black',label='point')
        # 如果点足够多，可以绘制连接线
        if len(points) > 1:
            ax.plot(points[:, 0], points[:, 1], color='black', alpha=0.5,linewidth=0.5, label='line')
        # 设置图形属性
        ax.set_title('Pattern Visualization')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.grid(True, linestyle='--', alpha=0.1)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        ax.set_aspect('equal', 'box')
        x_min, x_max = np.min(points[:, 0]), np.max(points[:, 0])
        y_min, y_max = np.min(points[:, 1]), np.max(points[:, 1])
        padding = max((x_max - x_min) * 0.1, (y_max - y_min) * 0.1, 0.5)  # 添加10%的边距
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.25)
        return fig

    def reset_region_selection(self):
        """重置区域选择状态"""
        self.has_selected_region = False
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None

    def show_transform_menu(self):
        # 清空原有菜单项
        self.transform_menu.clear()
        # 添加菜单项
        # 添加新的菜单项 A、B、C、D
        option_a = self.transform_menu.addAction("Translate")
        option_b = self.transform_menu.addAction("Rotate")
        option_c = self.transform_menu.addAction("Shear")
        option_d = self.transform_menu.addAction("Wave_normal")
        option_e = self.transform_menu.addAction("Wave_dense")
        option_f = self.transform_menu.addAction("Floral")
        option_g = self.transform_menu.addAction("Twist")
        option_h = self.transform_menu.addAction("Ripple")
        option_i = self.transform_menu.addAction("Swirl")
        option_j = self.transform_menu.addAction("Wrinkle")
        option_k = self.transform_menu.addAction("Rotate_stack")
        option_l = self.transform_menu.addAction("Expand")
        option_m = self.transform_menu.addAction("Customization")
        if self.has_selected_region:
            option_a.setEnabled(False)  # 禁用平移
            option_b.setEnabled(False)  # 禁用旋转
        else:
            option_a.setEnabled(True)  # 启用平移
            option_b.setEnabled(True)  # 启用旋转
        # 连接菜单项的触发信号到处理函数
        option_a.triggered.connect(lambda: self.handle_transform_option("Translate"))
        option_b.triggered.connect(lambda: self.handle_transform_option("Rotate"))
        option_c.triggered.connect(lambda: self.handle_transform_option("Shear"))
        option_d.triggered.connect(lambda: self.handle_transform_option("Wave_normal"))
        option_e.triggered.connect(lambda: self.handle_transform_option("Wave_dense"))
        option_f.triggered.connect(lambda: self.handle_transform_option("Floral"))
        option_g.triggered.connect(lambda: self.handle_transform_option("Twist"))
        option_h.triggered.connect(lambda: self.handle_transform_option("Ripple"))
        option_i.triggered.connect(lambda: self.handle_transform_option("Swirl"))
        option_j.triggered.connect(lambda: self.handle_transform_option("Wrinkle"))
        option_k.triggered.connect(lambda: self.handle_transform_option("Rotate_stack"))
        option_l.triggered.connect(lambda: self.handle_transform_option("Expand"))
        option_m.triggered.connect(lambda: self.handle_transform_option("Customization"))
        global_pos = self.ui.pushButton_5.mapToGlobal(QtCore.QPoint(0, self.ui.pushButton_5.height()))
        self.transform_menu.exec_(global_pos)

    def open_file_dialog(self):
        """打开文件对话框并读取两个文件路径"""
        file_filter = "Text files (*.txt);;Image files (*.png *.jpg *.jpeg *.bmp);;All files (*)"
        temp_files = []

        try:
            # 选择第一个文件
            file_path1, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Choose first file（forward）",
                "",
                file_filter
            )
            if not file_path1:
                return

            # 选择第二个文件
            file_path2, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Choose second file（backward）",
                "",
                file_filter
            )
            if not file_path2:
                return

            # 处理第一个文件
            if file_path1.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                # 是图片，转换为txt
                temp_file1 = self.convert_image_to_txt(file_path1)
                if temp_file1 is None:
                    return
                temp_files.append(temp_file1)
                file_path1_txt = temp_file1
            else:
                file_path1_txt = file_path1

            # 处理第二个文件
            if file_path2.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                # 是图片，转换为txt
                temp_file2 = self.convert_image_to_txt(file_path2)
                if temp_file2 is None:
                    return
                temp_files.append(temp_file2)
                file_path2_txt = temp_file2
            else:
                file_path2_txt = file_path2

            # 在lineEdit中显示文件路径
            self.ui.lineEdit.setText(f"{file_path1}; {file_path2}")
            # 执行处理两个文件
            self.process_two_txt_files(file_path1_txt, file_path2_txt)

        finally:
            # 删除临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Warning: Failed to delete temp file {temp_file}: {str(e)}")

    def convert_image_to_txt(self, image_path):
        """将图片转换为临时TXT文件，返回临时文件路径"""
        try:
            # 调用image_line.py处理图片
            # 首先确保image_line.py在相同目录下
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_line_path = os.path.join(current_dir, "image_line.py")

            if not os.path.exists(image_line_path):
                QtWidgets.QMessageBox.critical(
                    self, "Error", "image_line.py not found in the same directory!"
                )
                return None

            # 创建一个临时文件来存储输出
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_file.close()

            # 运行image_line.py作为子进程
            cmd = [sys.executable, image_line_path, image_path]  # 添加image_path参数
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir)

            if result.returncode != 0:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    f"Failed to process image:\n{result.stderr}"
                )
                return None

            # 检查是否生成了points.txt文件
            points_file = os.path.join(current_dir, "points.txt")
            if not os.path.exists(points_file):
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "points.txt was not generated by image_line.py"
                )
                return None

            # 将points.txt复制到临时文件
            shutil.copy(points_file, temp_file.name)

            # 删除原始的points.txt
            try:
                os.remove(points_file)
            except:
                pass

            return temp_file.name

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"Failed to convert image to TXT:\n{str(e)}"
            )
            return None

    def process_two_txt_files(self, file_path1, file_path2):
        """处理两个TXT文件，读取坐标点并生成图案"""
        try:
            # 先弹出参数对话框
            dialog = customization.CustomParamDialog(self)
            if dialog.exec_() != QtWidgets.QDialog.Accepted:
                return  # 用户取消，不执行后续操作

            # 用户确认参数后再清除场景
            self.clear_scene()
            self.point_set = []
            self.current_point_index = -1
            self.current_points = None
            self.unselected_points = None

            params = dialog.get_params()

            # 处理第一个文件
            points1 = self.read_points_from_txt(file_path1)
            if points1 is None or len(points1) == 0:
                QtWidgets.QMessageBox.warning(self, "Warning", "No valid coordinate points found in the first file")
                return

            # 处理第二个文件
            points2 = self.read_points_from_txt(file_path2)
            if points2 is None or len(points2) == 0:
                QtWidgets.QMessageBox.warning(self, "Warning", "No valid coordinate points found in the second file")
                return

            # 调用 customization 模块生成图案
            try:
                pat = customization.generate_pattern(points1, points2,
                                                     grid_number=params['grid_number'],
                                                     y_offset=params['y_offset'],
                                                     orientation_number=params['orientation_number'],
                                                     center_select=params['center_select'],
                                                     layer_number=params['layer_number'])

                # 将生成的点集赋值给当前点集
                self.current_points = pat
                self.unselected_points = None
                # 添加到点集容器
                self.point_set.append(pat.copy())
                self.current_point_index = len(self.point_set) - 1
                # 更新图形
                self.update_figure_from_points()
                QtWidgets.QMessageBox.information(
                self, "Successfully",
                f"Generated patterns successfully，including {len(pat)} points")

            except Exception as e:
                import traceback
                traceback.print_exc()
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    f"Failed to generate patterns:\n{str(e)}"
                )

        except Exception as e:
            error_msg = f"Failed to process TXT files:\n{str(e)}\n\n{traceback.format_exc()}"
            QtWidgets.QMessageBox.critical(self, "Error", error_msg)

    def load_image_for_eulerian(self):
        """欧拉回路处理图像并导入生成的路径点"""
        # 选择图像文件
        file_filter = "Image files (*.png *.jpg *.jpeg *.bmp);;All files (*)"
        image_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select an image for Eulerian path processing", "", file_filter)
        if not image_path:
            return

        # 确定脚本路径（位于当前文件所在目录的 Eulerian-Path-main 子文件夹中）
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.join(current_dir, "Eulerian-Path-main")
        script_path = os.path.join(script_dir, "process_image.py")

        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.critical(self, "Error", f"Script not found: {script_path}")
            return

        # 调用子进程执行脚本（可设置 max_size 参数，这里使用默认值）
        try:
            # 可选：弹出对话框让用户输入 max_size
            max_size, ok = QtWidgets.QInputDialog.getInt(
                self, "Max Size", "Enter max image dimension (default 1024):", 1024, 64, 4096)
            if not ok:
                return

            # 弹出对话框让用户输入 scale 因子
            scale, ok = QtWidgets.QInputDialog.getDouble(
                self, "Scale Factor",
                "Enter scale factor for path points (default 1.0, no scaling):",
                1.0, 0.0001, 1000.0, 4)  # 最小值0.001，最大值10000，3位小数
            if not ok:
                return

            # 构建命令
            cmd = [sys.executable, script_path, image_path, "--max_size", str(max_size)]
            if scale != 1.0:
                cmd.extend(["--scale", str(scale)])

            # 运行子进程，设置工作目录为脚本所在目录，以便导入 src 模块
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

            if result.returncode != 0:
                QtWidgets.QMessageBox.critical(
                    self, "Processing Failed",
                    f"Error output:\n{result.stderr}"
                )
                return

            # 根据图像路径推断生成的 txt 文件路径
            base = os.path.splitext(os.path.basename(image_path))[0]
            if scale != 1.0:
                generated_txt = os.path.join(script_dir, base + "_scaled.txt")
            else:
                generated_txt = os.path.join(script_dir, base + "_path.txt")

            if not os.path.exists(generated_txt):
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Expected output file not found:\n{generated_txt}")
                return

            # 使用现有的导入方法将点集加载到程序中
            points = self.read_points_from_txt(generated_txt)
            if points is None or len(points) == 0:
                QtWidgets.QMessageBox.warning(self, "Warning", "No valid coordinate points found in the file")
                return

                # 旋转180度（绕几何中心）
            center = np.mean(points, axis=0)
            rotated_points = (points - center) * -1 + center

            # 清除场景并设置旋转后的点集
            self.clear_scene()
            self.current_points = rotated_points
            self.unselected_points = None
            self.selected_points = None
            self.original_points = None

            # 添加到点集容器
            self.point_set.append(rotated_points.copy())
            self.current_point_index = len(self.point_set) - 1

            # 刷新显示
            self.update_figure_from_points()

            # 可选：删除临时生成的 txt 文件（或保留）
            # os.remove(generated_txt)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Exception occurred:\n{str(e)}")



    def read_gcode_from_txt(self, file_path):
        """从G-code格式的TXT文件读取坐标点"""
        try:
            # 尝试不同编码打开文件
            encodings = ['utf-8', 'gbk', 'latin-1', 'utf-16']
            lines = None
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        lines = file.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            if lines is None:
                QtWidgets.QMessageBox.warning(
                    self, "Error",
                    "Failed to encode"
                )
                return None
            # 解析G-code坐标点
            points = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith(';') or line.startswith('#'):
                    continue  # 跳过空行和注释行
                # 尝试解析G-code格式 (G1 X... Y...)
                if line.startswith('G1') or line.startswith('G01'):
                    x_value = None
                    y_value = None
                    # 分割命令
                    parts = line.split()
                    for part in parts:
                        if part.startswith('X'):
                            try:
                                x_value = float(part[1:])
                            except ValueError:
                                continue
                        elif part.startswith('Y'):
                            try:
                                y_value = float(part[1:])
                            except ValueError:
                                continue
                    if x_value is not None and y_value is not None:
                        points.append((x_value, y_value))
            return np.array(points) if points else None
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"Failed to read G-code file: {str(e)}"
            )
            return None

    def read_points_from_txt(self, file_path):
        """从TXT文件读取坐标点，支持两种格式：普通坐标和G-code"""
        try:
            # 首先尝试读取为普通坐标格式
            points = self._read_plain_points(file_path)
            if points is not None and len(points) > 0:
                return points

            # 如果普通格式读取失败，尝试G-code格式
            points = self.read_gcode_from_txt(file_path)
            return points

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"Failed to read the file: {str(e)}"
            )
            return None

    def _read_plain_points(self, file_path):
        """读取普通坐标格式的TXT文件（原有的读取逻辑）"""
        try:
            # 尝试不同编码打开文件
            encodings = ['utf-8', 'gbk', 'latin-1', 'utf-16']
            lines = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        lines = file.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            if lines is None:
                return None
            # 解析普通坐标点格式
            points = []
            for line in lines:
                # 跳过空行和注释行
                if not line.strip() or line.strip().startswith('#'):
                    continue
                # 尝试不同的分隔符
                if ',' in line:
                    parts = line.split(',')
                elif ';' in line:
                    parts = line.split(';')
                elif '\t' in line:
                    parts = line.split('\t')
                else:
                    parts = line.split()
                # 确保有两个数值
                if len(parts) >= 2:
                    try:
                        x = float(parts[0].strip())
                        y = float(parts[1].strip())
                        points.append((x, y))
                    except ValueError:
                        continue  # 跳过无效行
            return np.array(points) if points else None
        except Exception:
            return None


    def fit_view_to_item(self):
        """调整视图以适合当前图形项"""
        if self.current_item and hasattr(self.current_item, 'boundingRect'):
            # 重置视图变换
            self.ui.graphicsView.resetTransform()
            self.current_scale = 1.0
            # 获取图形项的边界矩形
            rect = self.current_item.boundingRect()
            # 获取视图大小
            view_rect = self.ui.graphicsView.viewport().rect()
            # 计算缩放因子（保持宽高比）
            w_scale = view_rect.width() / rect.width()
            h_scale = view_rect.height() / rect.height()
            scale_factor = min(w_scale, h_scale) * 0.9  # 添加一点边距
            # 应用缩放
            self.ui.graphicsView.scale(scale_factor, scale_factor)
            self.current_scale = scale_factor
            # 居中显示
            self.ui.graphicsView.centerOn(self.current_item)

    def handle_transform_option(self, option):
        """处理选择的变换选项"""
        QtWidgets.QMessageBox.information(
            self, "Transformation", f"Choose: {option}"
        )
        # 这里可以根据选项执行不同的操作
        if option == "Translate":
            self.transform_translate()
        elif option == "Rotate":
            self.transform_rotate()
        elif option == "Shear":
            self.transform_shear()
        elif option == "Wave_normal":
            self.transform_wave_normal()
        elif option == "Wave_dense":
            self.transform_wave_dense()
        elif option == "Floral":
            self.transform_floral()
        elif option == "Twist":
            self.transform_twist()
        elif option == "Ripple":
            self.transform_ripple()
        elif option == "Swirl":
            self.transform_swirl()
        elif option == "Wrinkle":
            self.transform_wrinkle()
        elif option == "Rotate_stack":
            self.transform_rotate_stack()
        elif option == "Expand":
            self.transform_expand()
        elif option == "Customization":
            self.transform_customization()
        self.update_figure_from_points()
        # 保存状态
        self.save_state()

    def transform_rotate(self):
        """旋转变换"""
        angle, ok = QtWidgets.QInputDialog.getDouble(self, "Rotate", "Rotate_angle(°):", 0.0)
        if ok:
            # 转换为弧度
            angle_rad = np.radians(angle)
            # 计算旋转矩阵
            rotation_matrix = np.array([
                [np.cos(angle_rad), -np.sin(angle_rad)],
                [np.sin(angle_rad), np.cos(angle_rad)]
            ])
            # 创建新点集并应用变换
            new_points = self.point_set[self.current_point_index].copy()
            # 计算中心点
            center = np.mean(new_points, axis=0)
            # 应用旋转
            new_points -= center  # 平移到原点
            new_points = np.dot(new_points, rotation_matrix.T)  # 旋转
            new_points += center  # 平移回原位置

            # 添加到点集容器
            self.point_set.append(new_points)
            self.current_point_index = len(self.point_set) - 1
            self.current_points = new_points
        print("Rotation Done")

    def transform_translate(self):
        """平移变换"""
        dx, ok1 = QtWidgets.QInputDialog.getDouble(self, "Translate", "Translate_X:", 0.0)
        if not ok1:
            return

        dy, ok2 = QtWidgets.QInputDialog.getDouble(self, "Translate", "Translate_Y:", 0.0)
        if not ok2:
            return

        # 创建新点集并应用变换
        new_points = self.point_set[self.current_point_index].copy()
        # 应用平移
        new_points[:, 0] += dx
        new_points[:, 1] += dy
        # 更新选中点
        self.point_set.append(new_points)
        self.current_point_index = len(self.point_set) - 1
        self.current_points = new_points
        # 更新图形
        self.update_figure_from_points()
        print("Translation Done")

    def transform_shear(self):
        """剪切变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_shear_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.shear_transformation(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Shear Done")
        self.reset_region_selection()



    def transform_wave_normal(self):
        """普通波纹变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_trigonometric_normal_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.trigonometric_normal(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Wave_normal Done")
        self.reset_region_selection()


    def transform_wave_dense(self):
        """密集波纹变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_trigonometric_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.trigonometric(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Wave_dense Done")
        self.reset_region_selection()


    def transform_floral(self):
        """玫瑰花边界变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_rose_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.rose_deformation(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Floral Done")
        self.reset_region_selection()



    def transform_twist(self):
        """四方窗口变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_twist_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.twist(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Twist Done")
        self.reset_region_selection()



    def transform_ripple(self):
        """圆形波纹变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_ripple_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.ripple(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Ripple Done")
        self.reset_region_selection()

    def transform_swirl(self):
        """涡旋变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_swirl_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.swirl_transformation(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Swirl Done")
        self.reset_region_selection()




    def transform_wrinkle(self):
        """褶皱变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_wrinkle_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.wrinkle(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Wrinkle Done")
        self.reset_region_selection()




    def transform_rotate_stack(self):
        """旋转堆叠变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_rotate_stack_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.rotate_stack(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Rotate_stack Done")
        self.reset_region_selection()



    def transform_expand(self):
        """褶皱变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_expand_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.expand(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Expand Done")
        self.reset_region_selection()



    def transform_customization(self):
        """褶皱变形"""
        if not hasattr(self, 'region_coords') or self.region_coords is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select region first")
            return
        # 提取区域坐标
        x_min, y_min, x_max, y_max = self.region_coords
        all_points = self.original_points.copy()
        # 自动计算中心坐标
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        params = pattern_transformation.get_custom_params(self)
        if params is None:
            return
        # 传递形状类型和参数（关键修改）
        shape_type = getattr(self, 'region_shape_type', 'rectangle')
        shape_params = getattr(self, 'region_shape_params', None)
        alpha_rect = pattern_transformation.generate_alpha_rect(
            all_points[:, 0],
            all_points[:, 1],
            x_min, y_min, x_max, y_max,
            extend=params['extend'],
            transition_types=params.get('transition_types'),  # 现在是一个字符串
            shape_type=shape_type,
            shape_params=shape_params
        )
        # 应用玫瑰花变形
        new_points = pattern_transformation.custom_transform(
            all_points,
            alpha_rect,
            {**params, 'cx': cx, 'cy': cy}  # 合并参数
        )
        self.current_points = new_points
        # 添加到点集容器
        self.point_set.append(self.current_points.copy())
        self.current_point_index = len(self.point_set) - 1
        # 更新图形
        self.region_coords = None
        self.selected_points = None
        self.unselected_points = None
        self.original_points = None
        self.update_figure_from_points()
        print("Customization Done")
        self.reset_region_selection()





    def update_figure_from_points(self):
        """根据当前坐标点更新图形，区分选中点和未选中点"""
        # 清除现有场景内容，但保留区域选择器
        items_to_keep = [item for item in self.scene.items() if isinstance(item, RegionSelector)]
        for item in self.scene.items()[:]:
            if item not in items_to_keep:
                self.scene.removeItem(item)
        # 创建新的Matplotlib图形
        fig = Figure(figsize=(5, 4), dpi=1000)
        ax = fig.add_subplot(111)
        # 如果有未选中点，先绘制未选中点（灰色）
        if self.unselected_points is not None and len(self.unselected_points) > 0:
            ax.plot(self.unselected_points[:, 0], self.unselected_points[:, 1],
                    '-', linewidth=1,color='gray', alpha=0.3, label='Unselected Points')
        # 绘制选中点（蓝色）
        ax.plot(self.current_points[:, 0], self.current_points[:, 1],
                   '-', linewidth=1, color='black', label='Selected Points')
        # 如果点足够多，可以绘制连接线（只绘制选中点）
        # if len(self.current_points) > 1:
        #     ax.plot(self.current_points[:, 0], self.current_points[:, 1],
        #              linewidth=1,color='black', alpha=0.5,  label='Line')
        # 设置图形属性
        ax.set_title('Pattern Visualization')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.grid(True, linestyle='--', alpha=0.1)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        ax.set_aspect('equal', 'box')
        # 计算坐标范围（包括所有点）
        all_points = self.current_points
        if self.unselected_points is not None:
            all_points = np.vstack((self.current_points, self.unselected_points))
        x_min, x_max = np.min(all_points[:, 0]), np.max(all_points[:, 0])
        y_min, y_max = np.min(all_points[:, 1]), np.max(all_points[:, 1])
        padding = max((x_max - x_min) * 0.1, (y_max - y_min) * 0.1, 0.5)
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.15)
        # 创建Matplotlib画布并添加到场景
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(400, 300)
        proxy = QtWidgets.QGraphicsProxyWidget()
        proxy.setWidget(canvas)
        self.scene.addItem(proxy)
        proxy.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        proxy.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.current_item = proxy
        # 保存状态
        self.save_state()
        self.fit_view_to_item()

    def export_image(self):
        """将graphicsView中的内容导出为图像文件或点集TXT文件"""
        try:
            # 检查是否有可导出的点集数据
            if self.current_points is None or len(self.current_points) == 0:
                QtWidgets.QMessageBox.warning(
                    self, "Warning", "No point data to export")
                return
            # 获取保存路径和选择的文件类型
            file_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save File", "",
                "PNG (*.png);;JPEG (*.jpg *.jpeg);;TXT Point Set (*.txt);;All kinds (*)"
            )
            if not file_path:
                return  # 用户取消保存
            # 根据选择的文件类型决定保存内容
            if selected_filter == "TXT Point Set (*.txt)" or file_path.lower().endswith('.txt'):
                # 保存为TXT点集文件
                if not file_path.lower().endswith('.txt'):
                    file_path += '.txt'
                try:
                    # # 将点集数据保存为TXT文件  a,b格式
                    # np.savetxt(file_path, self.current_points,
                    #            fmt='%.6f', delimiter=',')
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for point in self.current_points:
                            f.write(f"{point[0]:.4f} {point[1]:.4f}\n")
                    QtWidgets.QMessageBox.information(
                        self, "Successfully", f"Saved point set to: {file_path}")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self, "Error", f"Failed to save TXT file:\n{str(e)}")
            else:
                # 保存为图像文件
                if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # 根据选择的过滤器添加扩展名
                    if selected_filter == "PNG (*.png)":
                        file_path += '.png'
                    elif selected_filter == "JPEG (*.jpg *.jpeg)":
                        file_path += '.jpg'
                # 创建图像对象
                image = QtGui.QImage(self.scene.sceneRect().size().toSize(),
                                     QtGui.QImage.Format_ARGB32)
                image.fill(QtCore.Qt.white)
                # 创建绘制器
                painter = QtGui.QPainter(image)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                # 渲染场景到图像
                self.scene.render(painter)
                painter.end()
                # 保存图像
                if file_path.lower().endswith('.png'):
                    image.save(file_path, "PNG")
                elif file_path.lower().endswith(('.jpg', '.jpeg')):
                    image.save(file_path, "JPEG", 90)  # 90表示JPEG质量
                QtWidgets.QMessageBox.information(
                    self, "Successfully", f"Saved the image to: {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to export:\n{str(e)}")


    def import_txt_file(self):
        """导入单个TXT文件并显示点集"""
        file_filter = "Text files (*.txt);;All files (*)"
        # 选择文件
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Choose TXT file",
            "",
            file_filter
        )
        if not file_path:
            return
        # 处理TXT文件
        self.process_single_txt_file(file_path)

    def process_single_txt_file(self, file_path):
        """处理import TXT文件，读取坐标点并生成图案"""
        try:
            # 读取点集
            points = self.read_points_from_txt(file_path)
            if points is None or len(points) == 0:
                QtWidgets.QMessageBox.warning(
                    self, "Warning",
                    "No valid coordinate points found in the file"
                )
                return
            # 清除当前场景
            self.clear_scene()
            # 设置当前点集
            self.current_points = points
            self.unselected_points = None
            self.selected_points = None
            self.original_points = None

            # 添加到点集容器
            self.point_set.append(points.copy())
            self.current_point_index = len(self.point_set) - 1
            self.update_figure_from_points()

            # 显示成功消息
            QtWidgets.QMessageBox.information(
                self, "Successfully",
                f"Imported {len(points)} points from file"
            )

            # 在lineEdit中显示文件路径
            self.ui.lineEdit.setText(file_path)
        except Exception as e:
            error_msg = f"Failed to process TXT file:\n{str(e)}\n\n{traceback.format_exc()}"
            QtWidgets.QMessageBox.critical(self, "Error", error_msg)




    def generate_gcode(self):
        # 检查是否有可用点集
        if self.current_points is None or len(self.current_points) == 0:
            QtWidgets.QMessageBox.warning(self, "Warning",
                                          "No points available. Please load or generate a pattern first.")
            return

        # 输入参数 l 和 Vcp
        l, ok1 = QtWidgets.QInputDialog.getDouble(self, "Parameter l", "Enter offset distance l:", 1.0, 0.0, 1000.0, 2)
        if not ok1:
            return
        Vcp, ok2 = QtWidgets.QInputDialog.getDouble(self, "Parameter Vcp",
                                                    "Enter velocity Vcp (constant for all points):", 1.0, 0.0, 1000.0,
                                                    2)
        if not ok2:
            return
        try:
            offset_points, Vnp = cp.compute_offset_curve(self.current_points, l, Vcp)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to compute offset curve:\n{str(e)}")
            return

            # 询问是否保存结果
        reply = QtWidgets.QMessageBox.question(self, "Save Result", "Do you want to save the offset points?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Offset Points", "",
                                                                 "Text files (*.txt);;All files (*)")
            if file_path:
                try:
                    with open(file_path, 'w') as f:
                        for (x, y), v in zip(offset_points, Vnp):
                            f.write(f"{x:.4f} {y:.4f} {v:.4f}\n")
                    QtWidgets.QMessageBox.information(self, "Success", f"Saved to {file_path}")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
        else:
            # 可选：将偏移曲线直接显示在 Pattern Preview 中
            self.current_points = offset_points
            self.point_set.append(self.current_points.copy())
            self.current_point_index = len(self.point_set) - 1
            self.update_figure_from_points()
            QtWidgets.QMessageBox.information(self, "Success", "Offset curve generated and displayed.")





# ========== 新登录界面UI类 ==========
class Ui_LoginWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("LoginWindow")
        MainWindow.resize(1000, 800)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # 使用布局管理器
        layout = QtWidgets.QVBoxLayout(self.centralwidget)

        # 用户名输入框
        user_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel("User ID")
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setPlaceholderText("input your name")
        user_layout.addWidget(self.label)
        user_layout.addWidget(self.lineEdit)
        layout.addLayout(user_layout)

        # 密码输入框
        pass_layout = QtWidgets.QHBoxLayout()
        self.label_2 = QtWidgets.QLabel("Password")
        self.lineEdit_2 = QtWidgets.QLineEdit()
        self.lineEdit_2.setPlaceholderText("input your password")
        self.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.Password)
        pass_layout.addWidget(self.label_2)
        pass_layout.addWidget(self.lineEdit_2)
        layout.addLayout(pass_layout)

        # 登录按钮
        self.pushButton = QtWidgets.QPushButton("login")
        layout.addWidget(self.pushButton, alignment=QtCore.Qt.AlignCenter)

        # 添加弹簧使内容居中
        layout.addStretch(1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 965, 40))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)


# ========== 主界面UI类（使用布局管理器） ==========
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1500, 1000)

        # 创建中央部件
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # 主布局 - 垂直布局
        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)

        # 顶部按钮布局
        top_button_layout = QtWidgets.QHBoxLayout()
        # 添加左弹簧，使按钮整体居中
        top_button_layout.addStretch()
        self.pushButton_3 = QtWidgets.QPushButton("Cancel")
        self.pushButton_5 = QtWidgets.QPushButton("Transform")
        self.pushButton_4 = QtWidgets.QPushButton("Export")
        self.pushButton_6 = QtWidgets.QPushButton("Toolpath Correction")
        self.pushButton_7 = QtWidgets.QPushButton("Region Selection")
        self.pushButton_8 = QtWidgets.QPushButton("Import")
        # 统一设置按钮固定宽度
        for btn in [self.pushButton_7, self.pushButton_3, self.pushButton_5,
                    self.pushButton_8, self.pushButton_4, self.pushButton_6]:
            btn.setFixedWidth(300)
        top_button_layout.addWidget(self.pushButton_7)
        top_button_layout.addWidget(self.pushButton_3)
        top_button_layout.addWidget(self.pushButton_5)
        top_button_layout.addWidget(self.pushButton_8)
        top_button_layout.addWidget(self.pushButton_4)
        top_button_layout.addWidget(self.pushButton_6)

        # 添加右弹簧，使按钮居中且左右对称
        top_button_layout.addStretch()
        # 设置固定间距，缩放时按钮之间的距离不变
        top_button_layout.setSpacing(12)
        main_layout.addLayout(top_button_layout)

        # 中间内容布局 - 网格布局
        content_layout = QtWidgets.QGridLayout()
        content_layout.setSpacing(10)

        # ===== 第一列：树形控件 =====
        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setObjectName("treeWidget")
        self.label_3 = QtWidgets.QLabel("Basic Patterns")
        content_layout.addWidget(self.treeWidget, 1, 0)
        content_layout.addWidget(self.label_3, 2, 0)

        # 填充树形控件内容
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_2 = QtWidgets.QTreeWidgetItem(item_1)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_0 = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)
        item_1 = QtWidgets.QTreeWidgetItem(item_0)


        # ===== 第二列：绘图区域 =====
        # 创建容器框架
        self.drawing_container = QtWidgets.QFrame()
        self.drawing_container.setFrameShape(QtWidgets.QFrame.StyledPanel)
        drawing_layout = QtWidgets.QVBoxLayout(self.drawing_container)
        # 绘图区域将在运行时添加
        self.label_drawing = QtWidgets.QLabel("Pattern Design")
        self.label_drawing.setAlignment(QtCore.Qt.AlignCenter)
        content_layout.addWidget(self.drawing_container, 1, 1)
        content_layout.addWidget(self.label_drawing, 2, 1)


        # ===== 第三列：图形视图 =====
        self.graphicsView = QtWidgets.QGraphicsView()
        self.label_4 = QtWidgets.QLabel("Pattern Example")
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        content_layout.addWidget(self.graphicsView, 1, 2)
        content_layout.addWidget(self.label_4, 2, 2)

        # 设置列宽比例 (左侧1:右侧1)
        content_layout.setColumnStretch(0, 1)
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(2, 1)
        # 设置行高比例
        content_layout.setRowStretch(1, 3)  # 树形控件和图形视图占3份高度
        content_layout.setRowStretch(2, 1)  # 标签占1份高度
        main_layout.addLayout(content_layout, 1)  # 1表示占据剩余空间的比例
        self.label_3.setMaximumHeight(40)
        self.label_drawing.setMaximumHeight(40)
        self.label_4.setMaximumHeight(40)


        # 底部区域
        bottom_layout = QtWidgets.QHBoxLayout()
        self.label_2 = QtWidgets.QLabel("User-defined Pattern")
        self.lineEdit = QtWidgets.QLineEdit()
        self.pushButton = QtWidgets.QPushButton("Load File")

        bottom_layout.addWidget(self.label_2)
        bottom_layout.addWidget(self.lineEdit, 1)  # 1表示占据剩余空间的比例
        bottom_layout.addWidget(self.pushButton)

        main_layout.addLayout(bottom_layout)

        # 设置主布局的间距和边距
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        MainWindow.setCentralWidget(self.centralwidget)

        # 菜单栏
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1400, 22))
        self.menubar.setObjectName("menubar")
        self.menudesign = QtWidgets.QMenu(self.menubar)
        self.menudesign.setObjectName("menudesign")
        MainWindow.setMenuBar(self.menubar)

        # 状态栏
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menudesign.menuAction())

        # 设置控件文本
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

        # 设置树形控件文本
        self.treeWidget.headerItem().setText(0, _translate("MainWindow", "Existing Patterns"))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, _translate("MainWindow", "Linear Pattern"))
        self.treeWidget.topLevelItem(0).child(0).setText(0, _translate("MainWindow", "PS Pattern"))
        self.treeWidget.topLevelItem(0).child(1).setText(0, _translate("MainWindow", "PSDD Pattern"))
        self.treeWidget.topLevelItem(1).setText(0, _translate("MainWindow", "Polygon"))
        self.treeWidget.topLevelItem(1).child(0).setText(0, _translate("MainWindow", "Triangle"))
        self.treeWidget.topLevelItem(1).child(1).setText(0, _translate("MainWindow", "Quadrilateral"))
        self.treeWidget.topLevelItem(1).child(2).setText(0, _translate("MainWindow", "Hexagon"))
        self.treeWidget.topLevelItem(1).child(3).setText(0, _translate("MainWindow", "Polygon Tessellation"))
        self.treeWidget.topLevelItem(1).child(3).child(0).setText(0, _translate("MainWindow", "Tessellation_1"))
        self.treeWidget.topLevelItem(1).child(3).child(1).setText(0, _translate("MainWindow", "Tessellation_2"))
        self.treeWidget.topLevelItem(1).child(3).child(2).setText(0, _translate("MainWindow", "Tessellation_3"))
        self.treeWidget.topLevelItem(1).child(3).child(3).setText(0, _translate("MainWindow", "Tessellation_4"))
        self.treeWidget.topLevelItem(1).child(3).child(4).setText(0, _translate("MainWindow", "Tessellation_5"))
        self.treeWidget.topLevelItem(1).child(3).child(5).setText(0, _translate("MainWindow", "Tessellation_6"))
        self.treeWidget.topLevelItem(1).child(3).child(6).setText(0, _translate("MainWindow", "Tessellation_7"))
        self.treeWidget.topLevelItem(1).child(3).child(7).setText(0, _translate("MainWindow", "Tessellation_8"))
        self.treeWidget.topLevelItem(1).child(3).child(8).setText(0, _translate("MainWindow", "Tessellation_9"))
        self.treeWidget.topLevelItem(2).setText(0, _translate("MainWindow", "Circular"))
        self.treeWidget.topLevelItem(2).child(0).setText(0, _translate("MainWindow", "Normal Layout"))
        self.treeWidget.topLevelItem(2).child(1).setText(0, _translate("MainWindow", "Dense Layout"))
        self.treeWidget.topLevelItem(2).child(2).setText(0, _translate("MainWindow", "Arc"))
        self.treeWidget.topLevelItem(3).setText(0, _translate("MainWindow", "Trigonometric"))
        self.treeWidget.topLevelItem(4).setText(0, _translate("MainWindow", "Special Patterns"))
        self.treeWidget.topLevelItem(4).child(0).setText(0, _translate("MainWindow", "Windmill"))
        self.treeWidget.topLevelItem(4).child(1).setText(0, _translate("MainWindow", "Bell"))
        self.treeWidget.topLevelItem(4).child(2).setText(0, _translate("MainWindow", "Flowery"))
        self.treeWidget.topLevelItem(4).child(3).setText(0, _translate("MainWindow", "Hexagram"))
        self.treeWidget.topLevelItem(4).child(4).setText(0, _translate("MainWindow", "Coin"))
        self.treeWidget.topLevelItem(4).child(5).setText(0, _translate("MainWindow", "Gradient"))
        self.treeWidget.setSortingEnabled(__sortingEnabled)

        # 设置菜单文本
        self.menudesign.setTitle(_translate("MainWindow", "Design"))
        self.label_drawing.setText(_translate("MainWindow", "Pattern Design"))
        self.label_4.setText(_translate("MainWindow", "Pattern Preview"))


# ========== 程序入口 ==========
if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    UIStyles.apply_styles(app)
    login_window = LoginWindow()
    UIStyles.optimize_login_ui(login_window.ui)
    login_window.show()

    sys.exit(app.exec_())

