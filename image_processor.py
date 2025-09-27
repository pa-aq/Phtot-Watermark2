#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片处理器 - 负责图片的加载、水印处理和导出
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from PyQt5.QtGui import QPixmap, QImage
from typing import Optional, Tuple, List
from config_manager import WatermarkConfig
from fontTools.ttLib import TTFont
import matplotlib.font_manager as fm


class ImageProcessor:
    """图片处理器类"""
    
    def __init__(self):
        """初始化图片处理器"""
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    def load_image(self, file_path: str) -> Optional[Image.Image]:
        """加载图片"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 检查文件扩展名
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.supported_formats:
                raise ValueError(f"不支持的文件格式: {ext}")
            
            # 打开图片
            image = Image.open(file_path)
            # 转换为RGBA模式以支持透明通道
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            return image
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None
    
    def image_to_pixmap(self, image: Image.Image) -> QPixmap:
        """将PIL图片转换为PyQt的QPixmap"""
        try:
            # 如果图片是RGBA模式，需要特殊处理
            if image.mode == 'RGBA':
                # 创建带有Alpha通道的QImage
                q_image = QImage(image.tobytes(), image.width, image.height, image.width * 4, QImage.Format_RGBA8888)
            else:
                # 转换为RGB模式
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                q_image = QImage(image.tobytes(), image.width, image.height, image.width * 3, QImage.Format_RGB888)
            
            return QPixmap.fromImage(q_image)
        except Exception as e:
            print(f"转换图片失败: {e}")
            return QPixmap()
    
    def add_text_watermark(self, image: Image.Image, config: WatermarkConfig) -> Image.Image:
        """添加文本水印"""
        # 确保文本是字符串类型
        text = str(config.text_content)
        
        # 创建一个透明的水印层
        watermark = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        
        # 设置字体
        font = None
        font_path = config.font_family  # 现在config.font_family存储的是字体路径
        
        # 尝试直接使用配置中的字体路径
        try:
            if font_path:
                print(f"尝试加载字体路径: {font_path}")
                # 直接使用路径加载字体
                font = ImageFont.truetype(font_path, config.font_size)
                print(f"成功加载字体: {font_path}")
                
                # 测试字体是否支持中文
                try:
                    test_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1), (255, 255, 255, 0)))
                    test_text = "测试"
                    # 尝试使用textbbox或textsize获取文本尺寸
                    try:
                        test_draw.textbbox((0, 0), test_text, font=font)
                    except:
                        test_draw.textsize(test_text, font=font)
                    print("字体支持中文")
                except Exception as e:
                    print(f"字体可能不支持中文: {e}，尝试使用系统中文字体")
                    font = None
            else:
                print("未指定字体路径")
        except Exception as e:
            print(f"加载指定字体路径失败: {e}")
        
        # 如果指定字体失败或不支持中文，尝试使用系统中文字体
        if font is None:
            print("尝试使用系统中文字体")
            import os
            import sys
            
            # 定义更多支持中文的字体路径
            chinese_fonts = [
                # Windows 常用中文字体
                'C:/Windows/Fonts/simhei.ttf',      # 黑体
                'C:/Windows/Fonts/simsun.ttc',      # 宋体
                'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
                'C:/Windows/Fonts/msyhbd.ttc',      # 微软雅黑 粗体
                'C:/Windows/Fonts/msyhl.ttc',       # 微软雅黑 细体
                'C:/Windows/Fonts/STKAITI.ttf',     # 楷体
                'C:/Windows/Fonts/STSONG.ttf',      # 宋体
                'C:/Windows/Fonts/STXIHEI.ttf',     # 细黑
                'C:/Windows/Fonts/STXINGKA.ttf',    # 行楷
                'C:/Windows/Fonts/STFANGSO.ttf',    # 仿宋
                # 当前目录可能存在的字体文件
                'simhei.ttf',
                'msyh.ttc'
            ]
            
            # 遍历查找可用的中文字体
            for path in chinese_fonts:
                try:
                    if os.path.exists(path):
                        print(f"找到中文字体: {path}")
                        font_path = path
                        font = ImageFont.truetype(path, config.font_size)
                        # 测试字体是否支持中文
                        test_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1), (255, 255, 255, 0)))
                        test_text = "测试"
                        # 尝试使用textbbox或textsize获取文本尺寸
                        try:
                            test_draw.textbbox((0, 0), test_text, font=font)
                        except:
                            test_draw.textsize(test_text, font=font)
                        print("字体支持中文，使用该字体")
                        break
                except Exception as e:
                    print(f"尝试加载字体 {path} 失败: {e}")
        
        # 如果仍然没有找到支持中文的字体，使用PIL默认字体作为最后的备选
        if font is None:
            print("未找到支持中文的字体，使用PIL默认字体")
            try:
                font = ImageFont.load_default()
            except:
                font = None
                print("无法加载默认字体")
        
        # 获取文本尺寸
        if font:
            try:
                # 使用getbbox获取文本边界框（PIL 10.0+支持）
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # 兼容性处理
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except Exception as e:
                    print(f"获取文本尺寸失败: {e}")
                    # 默认尺寸估计
                    text_width = len(text) * 12
                    text_height = 20
        else:
            # 默认尺寸估计
            text_width = len(text) * 12
            text_height = 20
        
        # print(f"文本尺寸: 宽={text_width}, 高={text_height}")
        
        # 计算水印位置
        pos_x = int((image.width - text_width) * config.position_x)
        pos_y = int((image.height - text_height) * config.position_y)
        
        # print(f"水印位置: x={pos_x}, y={pos_y}")
        
        # 解析颜色
        color = self._parse_color(config.font_color)
        
        # 添加描边效果
        if config.stroke_enabled:
            stroke_color = self._parse_color(config.stroke_color)
            stroke_width = config.stroke_width
            # 绘制描边（在文本周围绘制多个偏移的文本）
            for x_offset in range(-stroke_width, stroke_width + 1):
                for y_offset in range(-stroke_width, stroke_width + 1):
                    if x_offset != 0 or y_offset != 0:
                        draw.text(
                            (pos_x + x_offset, pos_y + y_offset),
                            text,
                            font=font,
                            fill=(*stroke_color, 255)
                        )
        
        # 添加阴影效果
        if config.shadow_enabled:
            shadow_color = self._parse_color(config.shadow_color)
            draw.text(
                (pos_x + config.shadow_offset_x, pos_y + config.shadow_offset_y),
                text,
                font=font,
                fill=(*shadow_color, 255)
            )
        
        # 绘制主文本
        draw.text(
            (pos_x, pos_y),
            text,
            font=font,
            fill=(*color, int(255 * config.opacity))
        )
        
        # 旋转水印（如果需要）
        if config.rotation != 0:
            watermark = watermark.rotate(config.rotation, expand=1, fillcolor=(255, 255, 255, 0))
            # 重新计算位置
            new_pos_x = pos_x - (watermark.width - image.width) // 2
            new_pos_y = pos_y - (watermark.height - image.height) // 2
            result = Image.new('RGBA', watermark.size, (255, 255, 255, 0))
            result.paste(image, (new_pos_x, new_pos_y))
            result.alpha_composite(watermark)
            # 裁剪回原图尺寸
            return result.crop((new_pos_x, new_pos_y, new_pos_x + image.width, new_pos_y + image.height))
        else:
            # 合成图片
            result = Image.new('RGBA', image.size, (255, 255, 255, 0))
            result.paste(image, (0, 0))
            result.alpha_composite(watermark)
            return result
    
    def add_image_watermark(self, image: Image.Image, watermark_image_path: str, config: WatermarkConfig) -> Image.Image:
        """添加图片水印"""
        try:
            # 加载水印图片
            watermark_img = Image.open(watermark_image_path)
            if watermark_img.mode != 'RGBA':
                watermark_img = watermark_img.convert('RGBA')
            
            # 调整水印大小
            new_width = int(watermark_img.width * config.image_scale)
            new_height = int(watermark_img.height * config.image_scale)
            watermark_img = watermark_img.resize((new_width, new_height), Image.LANCZOS)
            
            # 调整透明度
            if config.opacity < 1.0:
                alpha = watermark_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(config.opacity)
                watermark_img.putalpha(alpha)
            
            # 旋转水印
            if config.rotation != 0:
                watermark_img = watermark_img.rotate(config.rotation, expand=1, fillcolor=(255, 255, 255, 0))
            
            # 计算水印位置
            pos_x = int((image.width - watermark_img.width) * config.position_x)
            pos_y = int((image.height - watermark_img.height) * config.position_y)
            
            # 合成图片
            result = Image.new('RGBA', image.size, (255, 255, 255, 0))
            result.paste(image, (0, 0))
            result.paste(watermark_img, (pos_x, pos_y), watermark_img)
            
            return result
        except Exception as e:
            print(f"添加图片水印失败: {e}")
            return image.copy()
    
    def process_image(self, image: Image.Image, config: WatermarkConfig) -> Image.Image:
        """处理图片，添加水印"""
        if config.watermark_type == "text":
            return self.add_text_watermark(image, config)
        elif config.watermark_type == "image" and config.image_path:
            return self.add_image_watermark(image, config.image_path, config)
        return image.copy()
    
    def export_image(self, image: Image.Image, output_path: str, file_format: str = 'PNG', 
                    quality: int = 90, resize: Optional[Tuple[int, int]] = None) -> bool:
        """导出图片"""
        try:
            # 调整大小（如果需要）
            export_img = image.copy()
            if resize:
                export_img = export_img.resize(resize, Image.LANCZOS)
            
            # 转换为适合输出的模式
            if file_format.upper() == 'JPEG':
                # JPEG不支持透明通道，转换为RGB
                if export_img.mode == 'RGBA':
                    background = Image.new('RGB', export_img.size, (255, 255, 255))
                    background.paste(export_img, mask=export_img.split()[3])
                    export_img = background
                export_img.save(output_path, format='JPEG', quality=quality)
            else:  # PNG
                if export_img.mode != 'RGBA':
                    export_img = export_img.convert('RGBA')
                export_img.save(output_path, format='PNG')
            
            return True
        except Exception as e:
            print(f"导出图片失败: {e}")
            return False
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """解析颜色字符串为RGB元组"""
        try:
            if color_str.startswith('#'):
                # 处理HEX颜色
                color_str = color_str.lstrip('#')
                if len(color_str) == 6:
                    return tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
            # 默认黑色
            return (0, 0, 0)
        except:
            return (0, 0, 0)
    
    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int] = (128, 128)) -> Image.Image:
        """创建缩略图"""
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.LANCZOS)
        return thumbnail
    
    def check_chinese_support_fonttools(self,font_path):
        """
        使用fonttools快速检测中文支持
        """
        try:
            font = TTFont(font_path)
            cmap_table = font['cmap']
            
            for table in cmap_table.tables:
                if table.format == 4:
                    cmap = table.cmap
                    # 检查基本汉字范围（CJK统一汉字）
                    test_codepoints = [
                        0x4E2D,  # "中"
                        0x6587,  # "文"
                        0x6D4B,  # "测"
                        0x8BD5,  # "试"
                    ]
                    
                    supported = sum(1 for cp in test_codepoints if cp in cmap)
                    return supported >= 3  # 至少支持3个测试字符
                    
            return False
        except:
            return False
    def get_supported_fonts(self):
        """
        快速获取支持中文的字体
        """
        chinese_fonts = []
        all_fonts = fm.findSystemFonts()
        
        for font_path in all_fonts:
            try:
                if self.check_chinese_support_fonttools(font_path):
                    font_prop = fm.FontProperties(fname=font_path)
                    font_name = font_prop.get_name()
                    if '?' not in font_name:
                        chinese_fonts.append({
                            'name': font_name,
                            'path': font_path,
                        })
            except:
                continue
        # print(f"支持中文的字体: {chinese_fonts}")
        return chinese_fonts