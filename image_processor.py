#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片处理器 - 负责图片的加载、水印处理和导出
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from PIL import ImageTransform
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
                # 直接使用路径加载字体，不再尝试查找粗体/斜体版本
                font = ImageFont.truetype(font_path, config.font_size)
            else:
                # 如果没有指定字体路径，尝试使用默认字体
                font = ImageFont.load_default()
                print("使用默认字体")
        except Exception as e:
            print(f"加载指定字体路径失败: {e}")
            # 加载失败，使用默认字体
            try:
                font = ImageFont.load_default()
                print("回退到默认字体")
            except:
                # 如果连默认字体都加载不了，设置为None
                font = None
        
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
            ]
            
            # 遍历查找可用的中文字体
            for path in chinese_fonts:
                try:
                    if os.path.exists(path):
                        print(f"找到中文字体: {path}")
                        font_path = path
                        font = ImageFont.truetype(path, config.font_size)
                        # 测试字体是否支持中文
                        if self.check_chinese_support_fonttools(font_path):
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
        
        # 计算水印位置
        pos_x = int((image.width - text_width) * config.position_x)
        pos_y = int((image.height - text_height) * config.position_y)
        
        # 解析颜色
        color = self._parse_color(config.font_color)
        color_with_opacity = (*color, int(255 * config.opacity))
        
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
        if font:
            # 处理斜体效果 - 使用临时图像旋转实现
            if config.font_italic:
                # 创建一个临时图像来绘制斜体文本 - 进一步增加左侧空间
                temp_size = (text_width + 80, text_height + 40)  # 增加左侧边距
                temp_img = Image.new('RGBA', temp_size, (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                
                # 为斜体文本增加透明度 - 这里将透明度增大15%使其更不透明
                italic_opacity_factor = 80  # 透明度系数，大于1表示更不透明（增大透明度）
                italic_alpha = min(255, int(255 * config.opacity*1.05 + italic_opacity_factor))  # 确保不超过255
                italic_color_with_opacity = (*color, italic_alpha)
                
                # 首先处理粗体效果（如果需要）
                if config.font_bold:
                    # 增强粗体效果：增加偏移量和绘制更多方向
                    # 模拟粗体：在原位置的上下左右及对角线各绘制一次
                    temp_draw.text((40-2, 20-2), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40+2, 20-2), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40-2, 20+2), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40+2, 20+2), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40-1, 20), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40+1, 20), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40, 20-1), text, font=font, fill=italic_color_with_opacity)
                    temp_draw.text((40, 20+1), text, font=font, fill=italic_color_with_opacity)
                
                # 绘制主文本到临时图像 - 进一步增加左边距
                temp_draw.text((40, 20), text, font=font, fill=italic_color_with_opacity)
                
                # 应用斜体变换 - 减少倾斜程度
                italic_img = temp_img.transform(
                    temp_size,  # 使用完整的临时图像大小
                    ImageTransform.AffineTransform((1, 15/45, 0, 0, 1, 0))  # 减少倾斜因子
                )
            
                # 计算放置位置并粘贴到水印层 - 进一步左移
                paste_x = pos_x - 20
                paste_y = pos_y - 10
                
                watermark.paste(italic_img, (paste_x, paste_y), italic_img)
            else:
                # 不是斜体，直接绘制
                # 处理粗体效果 - 通过多次绘制模拟粗体
                if config.font_bold:
                    # 增强粗体效果：增加偏移量和绘制更多方向
                    # 模拟粗体：在原位置的上下左右及对角线各绘制一次
                    draw.text((pos_x-2, pos_y-2), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x+2, pos_y-2), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x-2, pos_y+2), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x+2, pos_y+2), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x-1, pos_y), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x+1, pos_y), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x, pos_y-1), text, font=font, fill=color_with_opacity)
                    draw.text((pos_x, pos_y+1), text, font=font, fill=color_with_opacity)
                
                # 绘制主文本
                draw.text((pos_x, pos_y), text, font=font, fill=color_with_opacity)
        else:
            # 如果没有字体，使用PIL的默认文本绘制
            draw.text((pos_x, pos_y), text, fill=color_with_opacity)
        
        # 处理文字水印旋转 - 围绕文字中心旋转
        if config.rotation != 0 and font:
            # 计算原始文字中心位置
            text_center_x = pos_x + text_width // 2
            text_center_y = pos_y + text_height // 2
            
            # 清除之前绘制的内容，重新创建水印层
            watermark = Image.new('RGBA', image.size, (255, 255, 255, 0))
            
            # 计算旋转所需的最小临时图像大小
            import math
            angle_rad = math.radians(abs(config.rotation))
            # 使用三角函数计算旋转后所需的宽高
            temp_width = int(text_width * math.cos(angle_rad) + text_height * math.sin(angle_rad)) + 100
            temp_height = int(text_height * math.cos(angle_rad) + text_width * math.sin(angle_rad)) + 100
            temp_size = (max(temp_width, temp_height), max(temp_width, temp_height))  # 确保是正方形
            
            # 创建临时图像
            temp_img = Image.new('RGBA', temp_size, (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # 临时图像中心点
            temp_center = temp_size[0] // 2
            
            # 在临时图像中心绘制文本
            # 计算文本绘制位置，使文本在临时图像中居中
            if config.font_italic:
                # 对于斜体文本，先创建中间图像应用斜体变换
                italic_temp_size = (text_width + 50, text_height + 50)
                italic_temp = Image.new('RGBA', italic_temp_size, (255, 255, 255, 0))
                italic_draw = ImageDraw.Draw(italic_temp)
                
                # 为斜体文本增加透明度
                italic_opacity_factor = 80
                italic_alpha = min(255, int(255 * config.opacity*1.05 + italic_opacity_factor))
                italic_color_with_opacity = (*color, italic_alpha)
                
                # 斜体文本中心位置
                italic_center_x = italic_temp_size[0] // 2
                italic_center_y = italic_temp_size[1] // 2
                
                # 先添加描边效果（在粗体和主文本之前）
                if config.stroke_enabled:
                    stroke_color = self._parse_color(config.stroke_color)
                    stroke_width = config.stroke_width
                    # 描边只使用外边框，不是整个区域
                    for x_offset in range(-stroke_width, stroke_width + 1):
                        for y_offset in range(-stroke_width, stroke_width + 1):
                            # 只绘制真正的边框，不是整个方形区域
                            if abs(x_offset) == stroke_width or abs(y_offset) == stroke_width:
                                italic_draw.text(
                                    (italic_center_x - text_width // 2 + x_offset, 
                                     italic_center_y - text_height // 2 + y_offset), 
                                    text, font=font, fill=(*stroke_color, 255)
                                )
                
                # 添加阴影效果（在主文本之前）
                if config.shadow_enabled:
                    shadow_color = self._parse_color(config.shadow_color)
                    italic_draw.text(
                        (italic_center_x - text_width // 2 + config.shadow_offset_x, 
                         italic_center_y - text_height // 2 + config.shadow_offset_y), 
                        text, font=font, fill=(*shadow_color, 255)
                    )
                
                # 粗体效果
                if config.font_bold:
                    # 在原位置周围多个方向绘制文本以模拟粗体
                    directions = [(-1, -1), (1, -1), (-1, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dx, dy in directions:
                        italic_draw.text(
                            (italic_center_x - text_width // 2 + dx, 
                             italic_center_y - text_height // 2 + dy), 
                            text, font=font, fill=italic_color_with_opacity
                        )
                
                # 最后绘制主文本，确保它在所有效果之上
                italic_draw.text(
                    (italic_center_x - text_width // 2, italic_center_y - text_height // 2), 
                    text, font=font, fill=italic_color_with_opacity
                )
                
                # 应用斜体变换
                italic_img = italic_temp.transform(
                    italic_temp_size,
                    ImageTransform.AffineTransform((1, 15/45, 0, 0, 1, 0))
                )
                
                # 将斜体文本粘贴到主临时图像中心
                paste_x = temp_center - italic_img.width // 2
                paste_y = temp_center - italic_img.height // 2
                temp_img.paste(italic_img, (paste_x, paste_y), italic_img)
            else:
                # 非斜体文本
                # 先添加描边效果（在所有其他效果之前）
                if config.stroke_enabled:
                    stroke_color = self._parse_color(config.stroke_color)
                    stroke_width = config.stroke_width
                    # 描边只使用外边框，不是整个区域
                    for x_offset in range(-stroke_width, stroke_width + 1):
                        for y_offset in range(-stroke_width, stroke_width + 1):
                            # 只绘制真正的边框，不是整个方形区域
                            if abs(x_offset) == stroke_width or abs(y_offset) == stroke_width:
                                temp_draw.text(
                                    (temp_center - text_width // 2 + x_offset, 
                                     temp_center - text_height // 2 + y_offset), 
                                    text, font=font, fill=(*stroke_color, 255)
                                )
                
                # 添加阴影效果（在主文本之前）
                if config.shadow_enabled:
                    shadow_color = self._parse_color(config.shadow_color)
                    temp_draw.text(
                        (temp_center - text_width // 2 + config.shadow_offset_x, 
                         temp_center - text_height // 2 + config.shadow_offset_y),
                        text,
                        font=font,
                        fill=(*shadow_color, 255)
                    )
                
                # 粗体效果
                if config.font_bold:
                    directions = [(-1, -1), (1, -1), (-1, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dx, dy in directions:
                        temp_draw.text(
                            (temp_center - text_width // 2 + dx, 
                             temp_center - text_height // 2 + dy), 
                            text, font=font, fill=color_with_opacity
                        )
                
                # 最后绘制主文本，确保它在所有效果之上
                temp_draw.text(
                    (temp_center - text_width // 2, temp_center - text_height // 2), 
                    text, font=font, fill=color_with_opacity
                )
            
            # 旋转临时图像，确保expand=True以包含整个旋转结果
            rotated_img = temp_img.rotate(config.rotation, expand=True, fillcolor=(255, 255, 255, 0))
            
            # 计算旋转后的图像放置位置，确保旋转中心与原始文本中心重合
            paste_x = text_center_x - rotated_img.width // 2
            paste_y = text_center_y - rotated_img.height // 2
            
            # 粘贴旋转后的图像到水印层
            watermark.paste(rotated_img, (paste_x, paste_y), rotated_img)
        else:
            # 非旋转情况下，也需要确保正确的绘制顺序
            # 重新绘制水印层，确保正确的效果顺序
            if config.stroke_enabled and font:
                # 移除之前绘制的内容
                watermark = Image.new('RGBA', image.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark)
                
                # 重新按正确顺序绘制所有效果
                # 1. 先添加描边效果
                stroke_color = self._parse_color(config.stroke_color)
                stroke_width = config.stroke_width
                # 描边只使用外边框，不是整个区域
                for x_offset in range(-stroke_width, stroke_width + 1):
                    for y_offset in range(-stroke_width, stroke_width + 1):
                        # 只绘制真正的边框，不是整个方形区域
                        if abs(x_offset) == stroke_width or abs(y_offset) == stroke_width:
                            draw.text(
                                (pos_x + x_offset, pos_y + y_offset),
                                text,
                                font=font,
                                fill=(*stroke_color, 255)
                            )
                
                # 2. 然后添加阴影效果
                if config.shadow_enabled:
                    shadow_color = self._parse_color(config.shadow_color)
                    draw.text(
                        (pos_x + config.shadow_offset_x, pos_y + config.shadow_offset_y),
                        text,
                        font=font,
                        fill=(*shadow_color, 255)
                    )
                
                # 3. 处理粗体效果
                if config.font_bold:
                    directions = [(-1, -1), (1, -1), (-1, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dx, dy in directions:
                        draw.text(
                            (pos_x + dx, pos_y + dy),
                            text,
                            font=font,
                            fill=color_with_opacity
                        )
                
                # 4. 最后绘制主文本
                draw.text(
                    (pos_x, pos_y),
                    text,
                    font=font,
                    fill=color_with_opacity
                )
        
        # 合成图片
        result = Image.new('RGBA', image.size, (255, 255, 255, 0))
        result.paste(image, (0, 0))
        result.alpha_composite(watermark)
        
        # 如果图像模式不是RGBA，转换为RGB
        if result.mode == 'RGBA':
            background = Image.new('RGB', result.size, (255, 255, 255))
            background.paste(result, mask=result.split()[3])
            result = background
        
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