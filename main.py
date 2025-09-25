#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片水印工具 - 主入口文件
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from main_window import MainWindow, setup_global_font
from config_manager import ConfigManager

# 设置中文字体支持
os.environ['QT_FONT_DPI'] = '96'


def main():
    """主函数入口"""
    # 首先设置高DPI缩放支持（必须在创建QApplication前设置）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 确保中文显示正常
    app.setApplicationName("图片水印工具")
    app.setApplicationDisplayName("图片水印工具")
    
    # 应用全局字体设置，增大UI元素尺寸
    setup_global_font()
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 创建主窗口
    window = MainWindow(config_manager)
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()