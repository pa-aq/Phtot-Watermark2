import matplotlib.font_manager as fm
from fontTools.ttLib import TTFont
def check_chinese_support_fonttools(font_path):
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
 
def get_chinese_fonts_fast():
    """
    快速获取支持中文的字体
    """
    chinese_fonts = []
    all_fonts = fm.findSystemFonts()
    
    for font_path in all_fonts:
        # print(font_path)
        try:
            if check_chinese_support_fonttools(font_path):
                font_prop = fm.FontProperties(fname=font_path)
                font_name = font_prop.get_name()
                if '?' in font_name:
                    continue
                chinese_fonts.append({
                    'name': font_name,
                    'path': font_path,
                    'family': font_prop.get_family()[0] if font_prop.get_family() else font_name
                })
        except:
            continue
    
    return chinese_fonts


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

# create_chinese_text_image()

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_bold_effect(image, text, font, fill='black', bold_strength=2):
    """通过多次绘制创建粗体效果"""
    draw = ImageDraw.Draw(image)
    
    # 原始文本
    draw.text((10, 10), text, fill=fill, font=font)
    
    # 粗体效果：多次偏移绘制
    for dx in range(1, bold_strength + 1):
        for dy in range(1, bold_strength + 1):
            draw.text((10 + dx, 10 + dy), text, fill=fill, font=font)
            draw.text((10 - dx, 10 - dy), text, fill=fill, font=font)

def create_italic_effect(draw, text, position, font, fill='black', italic_angle=15):
    """创建斜体效果（通过剪切变换）"""
    from PIL import ImageTransform
    
    # 获取文本尺寸
    bbox = font.getbbox(text)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    
    # 创建临时图像绘制文本
    temp_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((0, 0), text, fill=fill, font=font)
    
    # 应用斜体变换
    italic_img = temp_img.transform(
        (width, height), 
        ImageTransform.AffineTransform((1, italic_angle/45, 0, 0, 1, 0))
    )
    
    # 粘贴到原图像
    image.paste(italic_img, position, italic_img)

# 使用示例
def demo_manual_effects():
    image = Image.new('RGB', (400, 200), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 24)
    
    # 正常文本
    draw.text((10, 10), "正常文本", fill='black', font=font)
    
    # 手动粗体
    create_bold_effect(image, "手动粗体", font, 'blue')
    
    # 手动斜体
    create_italic_effect(draw, "手动斜体", (10, 80), font, 'red')
    
    image.save("manual_effects.png")
    image.show()
# fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
# font_family = 'simfang'
# try:
#     font_path='C:\\Windows\\Fonts\\' + font_family+'.ttf'
#     print(font_path)
#     font = ImageFont.truetype(font_path,20)
#     print("成功从Windows字体目录加载字体")
# except OSError:
#     print("从Windows字体目录加载字体失败")

def find_italic_windows_specific(font_path):
    """
    Windows系统特定的斜体字体查找
    """
    if not os.path.exists(font_path):
        return None
    
    font_dir = os.path.dirname(font_path)
    font_filename = os.path.basename(font_path)
    
    # 通用Windows模式
    patterns = [
        font_filename.replace('.ttf', 'i.ttf'),
        font_filename.replace('.TTF', 'I.TTF'),
        font_filename.replace('.ttf', 'it.ttf'),
        font_filename.replace('.ttf', 'italic.ttf'),
    ]
    
    for pattern in patterns:
        if pattern == font_filename: continue
        print(f"pattern: {pattern}")
        italic_path = os.path.join(font_dir, pattern)
        if os.path.exists(italic_path):
            print(f"从字体目录中找到了斜体字体：{italic_path}")
            return italic_path
    
    return None


 
font_path='C:\\Windows\\Fonts\\simfang.ttf'
print(find_italic_windows_specific(font_path))