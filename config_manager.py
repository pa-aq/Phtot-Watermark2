#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理器 - 负责处理水印模板的保存、加载和管理
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


@dataclass
class WatermarkConfig:
    """水印配置数据类"""
    # 水印类型配置
    watermark_type: str = "text"  # text 或 image
    
    # 文本水印配置
    text_content: str = "水印文字"
    font_family: str = "Arial"
    font_size: int = 24
    font_bold: bool = False
    font_italic: bool = False
    font_color: str = "#000000"
    
    # 图片水印配置
    image_path: str = ""
    image_scale: float = 1.0
    
    # 通用配置
    opacity: float = 0.5
    position_x: float = 0.5  # 0-1 范围，相对位置
    position_y: float = 0.5
    rotation: float = 0.0
    
    # 高级配置
    shadow_enabled: bool = False
    shadow_offset_x: int = 2
    shadow_offset_y: int = 2
    shadow_blur: int = 3
    shadow_color: str = "#000000"
    
    stroke_enabled: bool = False
    stroke_width: int = 1
    stroke_color: str = "#FFFFFF"


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 获取应用数据目录
        self.app_data_dir = self._get_app_data_dir()
        self.template_dir = os.path.join(self.app_data_dir, "templates")
        self.settings_file = os.path.join(self.app_data_dir, "settings.json")
        
        # 确保目录存在
        self._ensure_directories()
        
        # 加载上次使用的配置
        self.last_config = self._load_last_config()
    
    def _get_app_data_dir(self) -> str:
        """获取应用数据目录"""
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ['APPDATA'], "Photo-Watermark2")
        else:  # 其他平台
            return os.path.join(str(Path.home()), ".photo-watermark2")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)
    
    def _load_last_config(self) -> WatermarkConfig:
        """加载上次使用的配置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将数据转换为配置对象
                    config = WatermarkConfig()
                    for key, value in data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                    return config
        except Exception as e:
            print(f"加载上次配置失败: {e}")
        
        # 返回默认配置
        return WatermarkConfig()
    
    def save_last_config(self, config: WatermarkConfig):
        """保存当前配置为上次使用的配置"""
        try:
            data = asdict(config)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def save_template(self, name: str, config: WatermarkConfig) -> bool:
        """保存配置为模板"""
        try:
            template_file = os.path.join(self.template_dir, f"{name}.json")
            data = asdict(config)
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False
    
    def load_template(self, name: str) -> Optional[WatermarkConfig]:
        """加载模板"""
        try:
            template_file = os.path.join(self.template_dir, f"{name}.json")
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将数据转换为配置对象
                    config = WatermarkConfig()
                    for key, value in data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                    return config
        except Exception as e:
            print(f"加载模板失败: {e}")
        return None
    
    def get_template_list(self) -> List[str]:
        """获取所有模板列表"""
        templates = []
        try:
            if os.path.exists(self.template_dir):
                for file in os.listdir(self.template_dir):
                    if file.endswith('.json'):
                        templates.append(file[:-5])  # 移除 .json 后缀
        except Exception as e:
            print(f"获取模板列表失败: {e}")
        return sorted(templates)
    
    def delete_template(self, name: str) -> bool:
        """删除模板"""
        try:
            template_file = os.path.join(self.template_dir, f"{name}.json")
            if os.path.exists(template_file):
                os.remove(template_file)
                return True
        except Exception as e:
            print(f"删除模板失败: {e}")
        return False