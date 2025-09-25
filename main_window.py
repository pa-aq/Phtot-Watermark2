#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片水印工具 - 主窗口界面
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QListWidget, QListWidgetItem, QSplitter, QGroupBox, 
    QComboBox, QLineEdit, QSlider, QCheckBox, QColorDialog, QTabWidget,
    QDoubleSpinBox, QSpinBox, QMessageBox, QFrame, QGridLayout, QRadioButton, QInputDialog,
    QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal

from image_processor import ImageProcessor
from config_manager import ConfigManager, WatermarkConfig

# 设置全局字体大小，增加UI元素尺寸
def setup_global_font():
    # 创建一个基础字体，将大小设置为较大值
    font = QFont()
    font.setPointSize(20)  # 增加字体大小
    
    # 应用全局字体
    app = QApplication.instance()
    if app:
        app.setFont(font)

# 确保QApplication已经导入
from PyQt5.QtWidgets import QApplication

class ImageListItem(QWidget):
    """图片列表项"""
    
    def __init__(self, thumbnail: QPixmap, filename: str, parent=None):
        super().__init__(parent)
        
        # 设置布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 缩略图
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setPixmap(thumbnail)
        self.thumbnail_label.setFixedSize(80, 80)  # 增大缩略图尺寸
        self.thumbnail_label.setScaledContents(True)
        
        # 文件名
        self.filename_label = QLabel(filename)
        self.filename_label.setWordWrap(True)
        self.filename_label.setAlignment(Qt.AlignVCenter)
        
        # 添加到布局
        layout.addWidget(self.thumbnail_label)
        layout.addWidget(self.filename_label, 1)
        
        # 设置整体大小
        self.setMinimumHeight(90)  # 增加列表项高度


class WatermarkPreview(QLabel):
    """水印预览窗口，支持拖拽"""
    
    position_changed = pyqtSignal(float, float)  # 发送相对位置
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(600, 1000)  # 增大预览窗口初始尺寸
        self.setFrameStyle(QFrame.StyledPanel)
        
        # 拖拽状态
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.watermark_pos = QPoint()
        self.current_config = None
    
    def set_image(self, pixmap: QPixmap):
        """设置预览图片"""
        self.setPixmap(pixmap)
        self.setScaledContents(False)  # 保持原始比例
        
        # 调整标签大小以适应图片，确保滚动条能正常显示
        self.setMinimumSize(pixmap.width(), pixmap.height())
        self.resize(pixmap.width(), pixmap.height())
        
        # 如果存在预览容器，确保其尺寸也正确更新
        if hasattr(self.parent(), 'resize'):
            self.parent().resize(self.size())
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_dragging and self.pixmap():
            # 计算新位置
            delta = event.pos() - self.drag_start_pos
            self.drag_start_pos = event.pos()
            
            # 获取实际图片在标签中的位置和大小
            pixmap_rect = self.pixmap().rect()
            scaled_rect = self.pixmap().scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ).rect()
            
            # 计算相对位置
            if self.width() > scaled_rect.width():
                x_offset = (self.width() - scaled_rect.width()) // 2
            else:
                x_offset = 0
                
            if self.height() > scaled_rect.height():
                y_offset = (self.height() - scaled_rect.height()) // 2
            else:
                y_offset = 0
            
            # 计算相对比例
            scale_x = pixmap_rect.width() / scaled_rect.width()
            scale_y = pixmap_rect.height() / scaled_rect.height()
            
            # 计算新的相对位置
            relative_x = (event.pos().x() - x_offset) / scaled_rect.width()
            relative_y = (event.pos().y() - y_offset) / scaled_rect.height()
            
            # 限制在0-1范围内
            relative_x = max(0, min(1, relative_x))
            relative_y = max(0, min(1, relative_y))
            
            # 发送位置变化信号
            self.position_changed.emit(relative_x, relative_y)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.config_manager = config_manager
        self.image_processor = ImageProcessor()
        self.current_config = config_manager.last_config
        
        # 存储导入的图片
        self.images = []  # 存储(原始图片路径, PIL图片对象)元组
        self.current_image_index = -1
        
        # 设置窗口
        self.setWindowTitle("图片水印工具")
        self.resize(1200, 800)
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
        # 创建UI
        self.init_ui()
        
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        # 检查拖放的是否为文件
        if event.mimeData().hasUrls():
            # 检查是否只有一个文件且为图片文件
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
                    event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        # 与dragEnterEvent相同的检查
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
                    event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                # 添加图片
                self._add_image(file_path)
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        # 创建分割器
        main_splitter = QSplitter(Qt.Horizontal)
        left_right_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧图片列表区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 导入按钮
        import_layout = QHBoxLayout()
        self.import_single_btn = QPushButton("导入单张图片")
        self.import_batch_btn = QPushButton("批量导入")
        self.import_folder_btn = QPushButton("导入文件夹")
        self.clear_list_btn = QPushButton("清除列表")
        
        import_layout.addWidget(self.import_single_btn)
        import_layout.addWidget(self.import_batch_btn)
        import_layout.addWidget(self.import_folder_btn)
        import_layout.addWidget(self.clear_list_btn)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(128, 128))
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setSelectionMode(QListWidget.SingleSelection)
        
        left_layout.addLayout(import_layout)
        left_layout.addWidget(self.image_list)
        
        # 中央预览区域
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        # 设置滚动区域的尺寸
        self.scroll_area.setMinimumSize(900, 600)  # 设置最小尺寸
        # 或者使用固定尺寸
        # self.scroll_area.setFixedSize(800, 600)
        # 或者设置最大尺寸
        # self.scroll_area.setMaximumSize(1000, 800)
        # 或者使用resize方法
        # self.scroll_area.resize(800, 600)
        
        self.scroll_area.setWidgetResizable(False)  # 设为False以允许内容大于视图
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 预览窗口容器
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignCenter)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        # 预览窗口
        self.preview_label = WatermarkPreview()
        self.preview_layout.addWidget(self.preview_label)
        
        # 将容器设置为滚动区域的小部件
        self.scroll_area.setWidget(self.preview_container)
        
        # 预设位置按钮
        position_group = QGroupBox("预设位置")
        position_layout = QGridLayout(position_group)
        
        positions = [
            ("左上", 0, 0), ("中上", 0.5, 0), ("右上", 1, 0),
            ("左中", 0, 0.5), ("中心", 0.5, 0.5), ("右中", 1, 0.5),
            ("左下", 0, 1), ("中下", 0.5, 1), ("右下", 1, 1)
        ]
        
        for i, (text, x, y) in enumerate(positions):
            btn = QPushButton(text)
            btn.setFixedSize(60, 30)
            btn.clicked.connect(lambda checked, x=x, y=y: self.set_watermark_position(x, y))
            row = i // 3
            col = i % 3
            position_layout.addWidget(btn, row, col)
        
        # 将滚动区域添加到布局
        center_layout.addWidget(self.scroll_area, 1)
        center_layout.addWidget(position_group)
        
        # 右侧设置面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 选项卡
        self.tabs = QTabWidget()
        
        # 水印设置选项卡
        watermark_tab = QWidget()
        watermark_layout = QVBoxLayout(watermark_tab)
        
        # 水印类型
        type_group = QGroupBox("水印类型")
        type_layout = QHBoxLayout(type_group)
        
        self.text_watermark_radio = QRadioButton("文本水印")
        self.image_watermark_radio = QRadioButton("图片水印")
        
        if self.current_config.watermark_type == "text":
            self.text_watermark_radio.setChecked(True)
        else:
            self.image_watermark_radio.setChecked(True)
        
        type_layout.addWidget(self.text_watermark_radio)
        type_layout.addWidget(self.image_watermark_radio)
        
        # 文本水印设置
        self.text_settings_group = QGroupBox("文本设置")
        text_settings_layout = QVBoxLayout(self.text_settings_group)
        
        # 文本内容
        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("文本内容:"))
        self.text_input = QLineEdit(self.current_config.text_content)
        content_layout.addWidget(self.text_input, 1)
        
        # 字体设置
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        # 添加系统字体
        fonts = self.image_processor.get_supported_fonts()
        self.font_combo.addItems(fonts)
        if self.current_config.font_family in fonts:
            self.font_combo.setCurrentText(self.current_config.font_family)
        font_layout.addWidget(self.font_combo, 1)
        
        # 字号
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字号:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)
        self.font_size_spin.setValue(self.current_config.font_size)
        font_size_layout.addWidget(self.font_size_spin)
        
        # 字体样式
        font_style_layout = QHBoxLayout()
        self.bold_checkbox = QCheckBox("粗体")
        self.italic_checkbox = QCheckBox("斜体")
        self.bold_checkbox.setChecked(self.current_config.font_bold)
        self.italic_checkbox.setChecked(self.current_config.font_italic)
        font_style_layout.addWidget(self.bold_checkbox)
        font_style_layout.addWidget(self.italic_checkbox)
        font_style_layout.addStretch()
        
        # 字体颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"background-color: {self.current_config.font_color}")
        color_layout.addWidget(self.color_button)
        
        # 添加到文本设置布局
        text_settings_layout.addLayout(content_layout)
        text_settings_layout.addLayout(font_layout)
        text_settings_layout.addLayout(font_size_layout)
        text_settings_layout.addLayout(font_style_layout)
        text_settings_layout.addLayout(color_layout)
        
        # 图片水印设置
        self.image_settings_group = QGroupBox("图片设置")
        image_settings_layout = QVBoxLayout(self.image_settings_group)
        
        # 选择图片
        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(QLabel("水印图片:"))
        self.image_path_input = QLineEdit(self.current_config.image_path)
        self.image_path_input.setReadOnly(True)
        self.select_image_btn = QPushButton("浏览...")
        image_path_layout.addWidget(self.image_path_input, 1)
        image_path_layout.addWidget(self.select_image_btn)
        
        # 图片缩放
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放比例:"))
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 5.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(self.current_config.image_scale)
        scale_layout.addWidget(self.scale_spin)
        scale_layout.addWidget(QLabel("x"))
        
        image_settings_layout.addLayout(image_path_layout)
        image_settings_layout.addLayout(scale_layout)
        
        # 通用设置
        common_group = QGroupBox("通用设置")
        common_layout = QVBoxLayout(common_group)
        
        # 透明度
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.current_config.opacity * 100))
        self.opacity_label = QLabel(f"{int(self.current_config.opacity * 100)}%")
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        
        # 旋转
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("旋转角度:"))
        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-360, 360)
        self.rotation_spin.setSingleStep(1)
        self.rotation_spin.setValue(self.current_config.rotation)
        rotation_layout.addWidget(self.rotation_spin)
        rotation_layout.addWidget(QLabel("度"))
        
        # 高级效果
        advanced_group = QGroupBox("高级效果")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # 阴影
        shadow_layout = QHBoxLayout()
        self.shadow_checkbox = QCheckBox("阴影")
        self.shadow_checkbox.setChecked(self.current_config.shadow_enabled)
        shadow_layout.addWidget(self.shadow_checkbox)
        
        # 描边
        stroke_layout = QHBoxLayout()
        self.stroke_checkbox = QCheckBox("描边")
        self.stroke_checkbox.setChecked(self.current_config.stroke_enabled)
        stroke_layout.addWidget(self.stroke_checkbox)
        
        advanced_layout.addLayout(shadow_layout)
        advanced_layout.addLayout(stroke_layout)
        
        # 添加到通用设置
        common_layout.addLayout(opacity_layout)
        common_layout.addLayout(rotation_layout)
        common_layout.addWidget(advanced_group)
        
        # 模板管理
        template_group = QGroupBox("模板管理")
        template_layout = QVBoxLayout(template_group)
        
        template_buttons_layout = QHBoxLayout()
        self.save_template_btn = QPushButton("保存当前设置为模板")
        self.load_template_btn = QPushButton("加载模板")
        self.delete_template_btn = QPushButton("删除模板")
        
        template_buttons_layout.addWidget(self.save_template_btn)
        template_buttons_layout.addWidget(self.load_template_btn)
        template_buttons_layout.addWidget(self.delete_template_btn)
        
        template_layout.addLayout(template_buttons_layout)
        
        # 添加到水印设置选项卡
        watermark_layout.addWidget(type_group)
        watermark_layout.addWidget(self.text_settings_group)
        watermark_layout.addWidget(self.image_settings_group)
        watermark_layout.addWidget(common_group)
        watermark_layout.addWidget(template_group)
        watermark_layout.addStretch()
        
        # 导出选项卡
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout_inner = QVBoxLayout(output_group)
        
        # 输出文件夹
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("输出文件夹:"))
        self.output_dir_input = QLineEdit()
        self.select_output_dir_btn = QPushButton("浏览...")
        output_dir_layout.addWidget(self.output_dir_input, 1)
        output_dir_layout.addWidget(self.select_output_dir_btn)
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG"])
        format_layout.addWidget(self.format_combo)
        
        # 文件命名
        naming_group = QGroupBox("文件命名")
        naming_layout = QVBoxLayout(naming_group)
        
        self.original_name_radio = QRadioButton("保留原文件名")
        self.add_prefix_radio = QRadioButton("添加前缀")
        self.add_suffix_radio = QRadioButton("添加后缀")
        
        self.original_name_radio.setChecked(True)
        
        prefix_layout = QHBoxLayout()
        self.prefix_input = QLineEdit("wm_")
        prefix_layout.addWidget(QLabel("前缀:"))
        prefix_layout.addWidget(self.prefix_input)
        
        suffix_layout = QHBoxLayout()
        self.suffix_input = QLineEdit("_watermarked")
        suffix_layout.addWidget(QLabel("后缀:"))
        suffix_layout.addWidget(self.suffix_input)
        
        naming_layout.addWidget(self.original_name_radio)
        naming_layout.addWidget(self.add_prefix_radio)
        naming_layout.addLayout(prefix_layout)
        naming_layout.addWidget(self.add_suffix_radio)
        naming_layout.addLayout(suffix_layout)
        
        # JPEG质量
        quality_group = QGroupBox("JPEG质量")
        quality_layout = QHBoxLayout(quality_group)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        self.quality_label = QLabel("90%")
        
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)
        
        # 导出按钮
        self.export_button = QPushButton("导出选中图片")
        self.export_all_button = QPushButton("导出所有图片")
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.export_all_button)
        
        # 添加到导出选项卡
        output_layout_inner.addLayout(output_dir_layout)
        output_layout_inner.addLayout(format_layout)
        output_layout_inner.addWidget(naming_group)
        output_layout_inner.addWidget(quality_group)
        
        export_layout.addWidget(output_group)
        export_layout.addLayout(buttons_layout)
        export_layout.addStretch()
        
        # 添加选项卡
        self.tabs.addTab(watermark_tab, "水印设置")
        self.tabs.addTab(export_tab, "导出设置")
        
        right_layout.addWidget(self.tabs)
        
        # 添加到分割器
        main_splitter.addWidget(left_panel)
        left_right_splitter.addWidget(center_panel)
        left_right_splitter.addWidget(right_panel)
        main_splitter.addWidget(left_right_splitter)
        
        # 设置分割器比例
        main_splitter.setSizes([300, 900])
        left_right_splitter.setSizes([600, 300])
        
        # 添加到主布局
        main_layout.addWidget(main_splitter)
        
        # 连接信号槽
        self.connect_signals()
        
        # 更新UI状态
        self.update_ui_state()
    
    def connect_signals(self):
        """连接信号和槽函数"""
        # 导入相关
        self.import_single_btn.clicked.connect(self.import_single_image)
        self.import_batch_btn.clicked.connect(self.import_batch_images)
        self.import_folder_btn.clicked.connect(self.import_folder)
        self.clear_list_btn.clicked.connect(self.clear_image_list)
        
        # 图片列表选择
        self.image_list.currentRowChanged.connect(self.on_image_selected)
        
        # 水印类型切换
        self.text_watermark_radio.toggled.connect(self.update_ui_state)
        self.image_watermark_radio.toggled.connect(self.update_ui_state)
        
        # 文本设置
        self.text_input.textChanged.connect(self.update_watermark_preview)
        self.font_combo.currentTextChanged.connect(self.update_watermark_preview)
        self.font_size_spin.valueChanged.connect(self.update_watermark_preview)
        self.bold_checkbox.toggled.connect(self.update_watermark_preview)
        self.italic_checkbox.toggled.connect(self.update_watermark_preview)
        self.color_button.clicked.connect(self.select_text_color)
        
        # 图片设置
        self.select_image_btn.clicked.connect(self.select_watermark_image)
        self.scale_spin.valueChanged.connect(self.update_watermark_preview)
        
        # 通用设置
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.rotation_spin.valueChanged.connect(self.update_watermark_preview)
        
        # 高级效果
        self.shadow_checkbox.toggled.connect(self.update_watermark_preview)
        self.stroke_checkbox.toggled.connect(self.update_watermark_preview)
        
        # 位置设置
        self.preview_label.position_changed.connect(self.on_position_changed)
        
        # 模板管理
        self.save_template_btn.clicked.connect(self.save_template)
        self.load_template_btn.clicked.connect(self.load_template)
        self.delete_template_btn.clicked.connect(self.delete_template)
        
        # 导出设置
        self.select_output_dir_btn.clicked.connect(self.select_output_directory)
        self.format_combo.currentTextChanged.connect(self.update_export_options)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        self.export_button.clicked.connect(self.export_selected_image)
        self.export_all_button.clicked.connect(self.export_all_images)
    
    def update_ui_state(self):
        """更新UI状态"""
        # 根据水印类型显示/隐藏相应的设置面板
        is_text = self.text_watermark_radio.isChecked()
        self.text_settings_group.setVisible(is_text)
        self.image_settings_group.setVisible(not is_text)
        
        # 更新配置
        self.current_config.watermark_type = "text" if is_text else "image"
        
        # 更新预览
        self.update_watermark_preview()
    
    def import_single_image(self):
        """导入单张图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)"
        )
        if file_path:
            self._add_image(file_path)
    
    def import_batch_images(self):
        """批量导入图片"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多张图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)"
        )
        for file_path in file_paths:
            self._add_image(file_path)
    
    def import_folder(self):
        """导入文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            # 获取文件夹中的所有图片文件
            for root, _, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
                        file_path = os.path.join(root, file)
                        self._add_image(file_path)
    
    def _add_image(self, file_path: str):
        """添加图片到列表"""
        # 加载图片
        image = self.image_processor.load_image(file_path)
        if image:
            # 创建缩略图
            thumbnail = self.image_processor.create_thumbnail(image)
            thumbnail_pixmap = self.image_processor.image_to_pixmap(thumbnail)
            
            # 创建列表项
            filename = os.path.basename(file_path)
            list_item = QListWidgetItem()
            list_item_widget = ImageListItem(thumbnail_pixmap, filename)
            list_item.setSizeHint(list_item_widget.sizeHint())
            
            # 添加到列表
            self.image_list.addItem(list_item)
            self.image_list.setItemWidget(list_item, list_item_widget)
            
            # 存储图片信息
            self.images.append((file_path, image))
            
            # 如果是第一张图片，自动选中
            if len(self.images) == 1:
                self.image_list.setCurrentRow(0)
    
    def on_image_selected(self, index: int):
        """当选择图片时更新预览"""
        if 0 <= index < len(self.images):
            self.current_image_index = index
            self.update_watermark_preview()
    
    def update_watermark_preview(self):
        """更新水印预览"""
        if self.current_image_index < 0 or self.current_image_index >= len(self.images):
            return
        
        # 获取当前图片
        _, image = self.images[self.current_image_index]
        
        # 更新配置
        self._update_config_from_ui()
        
        # 处理图片
        processed_image = self.image_processor.process_image(image, self.current_config)
        
        # 转换为pixmap并显示
        pixmap = self.image_processor.image_to_pixmap(processed_image)
        self.preview_label.set_image(pixmap)
    
    def _update_config_from_ui(self):
        """从UI更新配置"""
        # 水印类型
        self.current_config.watermark_type = "text" if self.text_watermark_radio.isChecked() else "image"
        
        # 文本设置
        self.current_config.text_content = self.text_input.text()
        self.current_config.font_family = self.font_combo.currentText()
        self.current_config.font_size = self.font_size_spin.value()
        self.current_config.font_bold = self.bold_checkbox.isChecked()
        self.current_config.font_italic = self.italic_checkbox.isChecked()
        
        # 图片设置
        self.current_config.image_path = self.image_path_input.text()
        self.current_config.image_scale = self.scale_spin.value()
        
        # 通用设置
        self.current_config.opacity = self.opacity_slider.value() / 100
        self.current_config.rotation = self.rotation_spin.value()
        
        # 高级效果
        self.current_config.shadow_enabled = self.shadow_checkbox.isChecked()
        self.current_config.stroke_enabled = self.stroke_checkbox.isChecked()
    
    def select_text_color(self):
        """选择文本颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_str = color.name()
            self.color_button.setStyleSheet(f"background-color: {color_str}")
            self.current_config.font_color = color_str
            self.update_watermark_preview()
    
    def select_watermark_image(self):
        """选择水印图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.image_path_input.setText(file_path)
            self.update_watermark_preview()
    
    def on_opacity_changed(self, value: int):
        """当透明度变化时"""
        self.opacity_label.setText(f"{value}%")
        self.update_watermark_preview()
    
    def on_position_changed(self, x: float, y: float):
        """当水印位置变化时"""
        self.current_config.position_x = x
        self.current_config.position_y = y
        self.update_watermark_preview()
    
    def set_watermark_position(self, x: float, y: float):
        """设置水印位置"""
        self.current_config.position_x = x
        self.current_config.position_y = y
        self.update_watermark_preview()
    
    def save_template(self):
        """保存当前设置为模板"""
        # 获取模板名称
        name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称:")
        if ok and name:
            # 更新配置
            self._update_config_from_ui()
            
            # 保存模板
            if self.config_manager.save_template(name, self.current_config):
                QMessageBox.information(self, "成功", f"模板 '{name}' 已保存")
            else:
                QMessageBox.error(self, "错误", "保存模板失败")
    
    def load_template(self):
        """加载模板"""
        # 获取模板列表
        templates = self.config_manager.get_template_list()
        if not templates:
            QMessageBox.information(self, "提示", "没有找到保存的模板")
            return
        
        # 选择模板
        name, ok = QInputDialog.getItem(self, "加载模板", "请选择模板:", templates, 0, False)
        if ok:
            # 加载模板
            config = self.config_manager.load_template(name)
            if config:
                self.current_config = config
                self._update_ui_from_config()
                self.update_watermark_preview()
                QMessageBox.information(self, "成功", f"模板 '{name}' 已加载")
            else:
                QMessageBox.error(self, "错误", "加载模板失败")
    
    def delete_template(self):
        """删除模板"""
        # 获取模板列表
        templates = self.config_manager.get_template_list()
        if not templates:
            QMessageBox.information(self, "提示", "没有找到保存的模板")
            return
        
        # 选择模板
        name, ok = QInputDialog.getItem(self, "删除模板", "请选择要删除的模板:", templates, 0, False)
        if ok:
            # 确认删除
            reply = QMessageBox.question(
                self, "确认", f"确定要删除模板 '{name}' 吗?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 删除模板
                if self.config_manager.delete_template(name):
                    QMessageBox.information(self, "成功", f"模板 '{name}' 已删除")
                else:
                    QMessageBox.error(self, "错误", "删除模板失败")
    
    def _update_ui_from_config(self):
        """从配置更新UI"""
        # 水印类型
        if self.current_config.watermark_type == "text":
            self.text_watermark_radio.setChecked(True)
        else:
            self.image_watermark_radio.setChecked(True)
        
        # 文本设置
        self.text_input.setText(self.current_config.text_content)
        
        # 设置字体（如果存在）
        index = self.font_combo.findText(self.current_config.font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        
        self.font_size_spin.setValue(self.current_config.font_size)
        self.bold_checkbox.setChecked(self.current_config.font_bold)
        self.italic_checkbox.setChecked(self.current_config.font_italic)
        self.color_button.setStyleSheet(f"background-color: {self.current_config.font_color}")
        
        # 图片设置
        self.image_path_input.setText(self.current_config.image_path)
        self.scale_spin.setValue(self.current_config.image_scale)
        
        # 通用设置
        self.opacity_slider.setValue(int(self.current_config.opacity * 100))
        self.opacity_label.setText(f"{int(self.current_config.opacity * 100)}%")
        self.rotation_spin.setValue(self.current_config.rotation)
        
        # 高级效果
        self.shadow_checkbox.setChecked(self.current_config.shadow_enabled)
        self.stroke_checkbox.setChecked(self.current_config.stroke_enabled)
        
        # 更新UI状态
        self.update_ui_state()
    
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if directory:
            self.output_dir_input.setText(directory)
    
    def update_export_options(self):
        """更新导出选项"""
        # 可以根据格式调整选项的可见性
        pass
    
    def on_quality_changed(self, value: int):
        """当质量变化时"""
        self.quality_label.setText(f"{value}%")
    
    def export_selected_image(self):
        """导出选中的图片"""
        if self.current_image_index < 0 or self.current_image_index >= len(self.images):
            QMessageBox.warning(self, "警告", "请先选择要导出的图片")
            return
        
        self._export_images([self.current_image_index])
    
    def export_all_images(self):
        """导出所有图片"""
        if not self.images:
            QMessageBox.warning(self, "警告", "没有图片可导出")
            return
        
        self._export_images(list(range(len(self.images))))
    
    def _export_images(self, indices: list):
        """导出指定索引的图片"""
        # 检查输出目录
        output_dir = self.output_dir_input.text()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请先选择输出文件夹")
            return
        
        # 更新配置
        self._update_config_from_ui()
        
        # 获取导出设置
        file_format = self.format_combo.currentText()
        quality = self.quality_slider.value()
        
        # 导出文件
        success_count = 0
        failed_count = 0
        
        for index in indices:
            file_path, image = self.images[index]
            
            # 处理图片
            processed_image = self.image_processor.process_image(image, self.current_config)
            
            # 生成输出文件名
            original_filename = os.path.basename(file_path)
            name_without_ext, ext = os.path.splitext(original_filename)
            
            # 根据命名规则生成文件名
            if self.original_name_radio.isChecked():
                new_filename = original_filename
            elif self.add_prefix_radio.isChecked():
                new_filename = f"{self.prefix_input.text()}{name_without_ext}.{file_format.lower()}"
            else:  # add_suffix
                new_filename = f"{name_without_ext}{self.suffix_input.text()}.{file_format.lower()}"
            
            # 生成完整路径
            output_path = os.path.join(output_dir, new_filename)
            
            # 检查是否与原文件相同
            if os.path.abspath(output_path) == os.path.abspath(file_path):
                QMessageBox.warning(self, "警告", f"禁止覆盖原文件: {original_filename}")
                failed_count += 1
                continue
            
            # 导出图片
            if self.image_processor.export_image(processed_image, output_path, file_format, quality):
                success_count += 1
            else:
                failed_count += 1
        
        # 显示结果
        if success_count > 0:
            QMessageBox.information(self, "完成", f"成功导出 {success_count} 张图片")
        if failed_count > 0:
            QMessageBox.warning(self, "警告", f"有 {failed_count} 张图片导出失败")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存当前配置
        self._update_config_from_ui()
        self.config_manager.save_last_config(self.current_config)
        
        # 接受关闭事件
        event.accept()


    def clear_image_list(self):
        """清除图片列表"""
        # 确认对话框
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有图片吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清空列表
            self.image_list.clear()
            # 清空图片数据
            self.images = []
            # 重置当前索引
            self.current_image_index = -1
            # 清空预览窗口
            self.preview_label.clear()