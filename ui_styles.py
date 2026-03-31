# ui_styles.py
from PyQt5 import QtCore, QtGui, QtWidgets


class UIStyles:
    """界面风格与布局优化类（莫兰迪灰蓝色系）"""

    @staticmethod
    def apply_styles(app):
        """应用全局样式表"""
        style_sheet = """
        /* ===== 全局样式 ===== */
        QWidget {
            font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
            font-size: 12pt;          /* 适中的全局字体大小 */
            color: #4A5568;
            background-color: #F7FAFC;
        }

        /* ===== 标签 ===== */
        QLabel {
            font-size: 12pt;
            font-weight: 500;
        }

        /* ===== 登录界面特有标题 ===== */
        QLabel#titleLabel {
            font-size: 16pt;
            font-weight: 600;
            margin-bottom: 24px;
        }

        /* ===== 输入框 ===== */
        QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 12px 16px;
            font-size: 12pt;
            min-height: 30px;
        }

        QLineEdit:focus {
            border: 1px solid #CBD5E0;
            box-shadow: 0 0 0 3px rgba(160, 174, 192, 0.2);
        }

        /* ===== 按钮 ===== */
        QPushButton {
            background-color: #667895;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;        /* 减少内边距，确保文字完整显示 */
            font-size: 12pt;
            font-weight: 600;
            min-height: 30px;
        }

        QPushButton:hover {
            background-color: #5A6B85;
        }

        QPushButton:pressed {
            background-color: #4D5D75;
        }

        /* ===== 主界面树形控件 ===== */
        QTreeWidget {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            font-size: 12pt;
        }

        QTreeWidget::item {
            padding: 8px 12px;
            min-height: 32px;
        }

        QTreeWidget::item:selected {
            background-color: #E2E8F0;
            color: #2D3748;
        }

        QTreeWidget::item:hover {
            background-color: #F7FAFC;
        }

        /* ===== 图形视图 ===== */
        QGraphicsView {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
        }

        /* ===== 菜单栏和菜单 ===== */
        QMenuBar {
            background-color: #FFFFFF;
            padding: 4px;
            border-bottom: 1px solid #E2E8F0;
            font-size: 12pt;
        }

        QMenuBar::item {
            padding: 6px 12px;
            border-radius: 4px;
        }

        QMenuBar::item:selected {
            background-color: #E2E8F0;
        }

        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 4px;
            padding: 6px 0;
            font-size: 12pt;
        }

        QMenu::item {
            padding: 8px 24px 8px 16px;
        }

        QMenu::item:selected {
            background-color: #E2E8F0;
        }

        /* ===== 状态栏 ===== */
        QStatusBar {
            background-color: #FFFFFF;
            color: #718096;
            border-top: 1px solid #E2E8F0;
            font-size: 12pt;
            padding: 4px 12px;
        }

        /* ===== 分隔线 ===== */
        QFrame[class="separator"] {
            background-color: #E2E8F0;
            height: 1px;
            margin: 8px 0;
        }
        """
        app.setStyleSheet(style_sheet)

    @staticmethod
    def optimize_login_ui(ui):
        """优化登录界面布局（居中 + 边缘留白）"""
        # 主布局设置大边距实现留白
        main_layout = ui.centralwidget.layout()
        main_layout.setContentsMargins(60, 40, 60, 60)
        main_layout.setSpacing(24)

        # 添加容器Widget实现内容居中
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(24)
        container.setMaximumWidth(600)  # 限制内容宽度

        # 替换原布局中的内容到容器
        while main_layout.count():
            item = main_layout.takeAt(0)
            if item.widget():
                container_layout.addWidget(item.widget())
            elif item.layout():
                container_layout.addLayout(item.layout())

        # 添加Logo（占位图，实际需替换）
        logo_label = QtWidgets.QLabel()
        logo_pixmap = QtGui.QPixmap(100, 100)
        logo_pixmap.fill(QtGui.QColor("#667895"))
        logo_label.setPixmap(logo_pixmap.scaled(80, 80, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        logo_label.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.insertWidget(0, logo_label)

        # 添加标题
        title_label = QtWidgets.QLabel("Pattern Design System")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        container_layout.insertWidget(1, title_label)

        # 设置输入框和按钮的尺寸策略
        for widget in [ui.lineEdit, ui.lineEdit_2, ui.pushButton]:
            widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # 登录按钮特殊样式（字体大小已在全局样式表中定义）
        ui.pushButton.setStyleSheet("""
            QPushButton {
                background-color: #667895;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #5A6B85;
            }
        """)

        # 将容器添加回主布局（自动居中）
        main_layout.addWidget(container, alignment=QtCore.Qt.AlignCenter)

    @staticmethod
    def optimize_main_ui(ui):
        """优化主界面布局（三栏结构 + 留白）"""
        # 主布局设置统一边距
        main_layout = ui.centralwidget.layout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 顶部按钮栏优化
        top_layout = main_layout.itemAt(0).layout()
        if top_layout:
            top_layout.setContentsMargins(0, 0, 0, 12)
            top_layout.setSpacing(12)
            for i in range(top_layout.count()):
                widget = top_layout.itemAt(i).widget()
                if widget:
                    widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)


        # 添加全局分隔线
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setObjectName("separator")
        main_layout.insertWidget(1, separator)

        # 内容区域（左树形控件 + 右图形视图）
        content_layout = main_layout.itemAt(2).layout()
        if content_layout:
            content_layout.setSpacing(16)

            # 树形控件设置
            ui.treeWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            ui.treeWidget.setMinimumWidth(240)

            # 图形视图设置
            ui.graphicsView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            ui.graphicsView.setMinimumWidth(300)

        # 底部输入区域
        bottom_layout = main_layout.itemAt(3).layout()
        if bottom_layout:
            bottom_layout.setContentsMargins(0, 12, 0, 0)
            bottom_layout.setSpacing(12)
            ui.label_2.setFixedWidth(300)  # 标签宽度可以固定
            # 移除固定宽度，让按钮自适应内容
            ui.pushButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            # 可选设置最小宽度确保文字不换行
            ui.pushButton.setMinimumWidth(120)

    @staticmethod
    def create_icons():
        """创建占位图标（实际项目应使用真实资源）"""
        return {
            "logo": QtGui.QPixmap(100, 100),
            "triangle": QtGui.QPixmap(24, 24),
            "circle": QtGui.QPixmap(24, 24)
        }