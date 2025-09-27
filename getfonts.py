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
print(get_chinese_fonts_fast())
# fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
# font_family = 'simfang'
# try:
#     font_path='C:\\Windows\\Fonts\\' + font_family+'.ttf'
#     print(font_path)
#     font = ImageFont.truetype(font_path,
#                             20)
#     print("成功从Windows字体目录加载字体")
# except OSError:
#     print("从Windows字体目录加载字体失败")
 
# # 如果你想获取更加详细的字体名称而不是路径，你可以使用以下代码
# font_names = [matplotlib.font_manager.FontProperties(fname=font).get_name() for font in fonts]
# unique_font_names = sorted(set(font_names))  # 去除重复的字体名称并排序
 