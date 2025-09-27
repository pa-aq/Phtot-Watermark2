from PIL import Image, ImageDraw, ImageFont
# def create_chinese_text_image():
#     # 查找系统中文字体
#     chinese_fonts = [f for f in fm.findSystemFonts() if 'sim' in f.lower() or 'hei' in f.lower()]
    
#     if not chinese_fonts:
#         print("未找到中文字体")
#         return
#     print(chinese_fonts)
#     # 使用第一个找到的中文字体
#     font_path = chinese_fonts[0]
#     font = ImageFont.truetype(font_path, size=24)
    
#     # 创建图像
#     image = Image.new('RGB', (600, 300), color='white')
#     draw = ImageDraw.Draw(image)
    
#     # 中文文本
#     texts = [
#         "中文测试示例",
#         "你好，世界！",
#         "Python图像处理"
#     ]
    
#     # 绘制多行文本
#     y_position = 50
#     for text in texts:
#         bbox = font.getbbox(text)
#         text_width = bbox[2] - bbox[0]
#         x_position = (600 - text_width) / 2
        
#         draw.text((x_position, y_position), text, fill='blue', font=font)
#         y_position += 50
    
#     image.save("chinese_text.png")
#     image.show()
