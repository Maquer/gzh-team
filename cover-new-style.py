#!/usr/bin/env python3
"""
新版封面生成器 - 精准复刻「AI面试恐怖谷」风格
尺寸：900x383
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

# 颜色
RED = (194, 69, 60)
INK = (51, 51, 51)
PAPER = (250, 248, 245)  # 接近样板的米白色
GREY = (120, 120, 120)
WHITE = (255, 255, 255)

W, H = 900, 383
img = Image.new('RGB', (W, H), PAPER)
draw = ImageDraw.Draw(img)

# 字体加载
def load_font(name, size):
    paths = {
        'bold': '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc',
        'regular': '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc',
        'serif': '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc',
        'brush': '/usr/share/fonts/noto/MaShanZheng-Regular.ttf',
        'kai': '/usr/share/fonts/noto/LXGWWenKai-Regular.ttf',
        'fangzheng': '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    }
    fp = paths.get(name)
    if fp and os.path.exists(fp):
        try:
            return ImageFont.truetype(fp, size)
        except:
            pass
    return None

# 加载所有字体
fonts = {
    'bold': load_font('bold', 28),
    'regular': load_font('regular', 28),
    'brush': load_font('brush', 28),
    'kai': load_font('kai', 28),
}

def draw_text_xy(draw, text, x, y, font_key, size, color, align='left'):
    """绘制文本并返回bbox"""
    font = fonts.get(font_key, fonts['regular'])
    if font:
        font = ImageFont.truetype(font.path, size) if hasattr(font, 'path') else font
        draw.text((x, y), text, fill=color, font=font)
    else:
        draw.text((x, y), text, fill=color)
    bbox = draw.textbbox((x, y), text, font=font)
    return bbox

# ============================================================
# 左侧区域 (x: 0-540)
# ============================================================

# --- 品牌名区 ---
# 先画红色横线
draw.line([(20, 48), (100, 48)], fill=RED, width=2)

# 品牌名「<YOUR_BRAND>」
f_brush_30 = load_font('brush', 30)
if f_brush_30:
    draw.text((20, 10), '<YOUR_BRAND>', fill=RED, font=f_brush_30)
else:
    draw.text((20, 10), '<YOUR_BRAND>', fill=RED)

# 英文副标
f_reg_12 = load_font('regular', 12)
draw.text((22, 42), 'SANS HUI YE JI', fill=GREY, font=f_reg_12)

# --- 热搜标题 ---
f_bold_16 = load_font('bold', 16)
draw.text((20, 65), 'AI智能体生态观察', fill=RED, font=f_bold_16)
# 下划线
bbox = draw.textbbox((20, 65), 'AI智能体生态观察', font=f_bold_16)
draw.line([(bbox[0], bbox[3]+3), (bbox[2], bbox[3]+3)], fill=RED, width=2)

# --- 核心观点（大号黑字）---
f_bold_40 = load_font('bold', 40)
lines = ['我研究了90个', 'AI智能体项目', '发现最值钱的不是智能体本身']
y = 100
for line in lines:
    if f_bold_40:
        draw.text((20, y), line, fill=INK, font=f_bold_40)
    else:
        draw.text((20, y), line, fill=INK)
    y += 50

# --- 时间标签 ---
f_reg_14 = load_font('regular', 14)
draw.text((20, 300), '2026.10 · 深度观察', fill=GREY, font=f_reg_14)

# --- 底部Slogan ---
f_reg_12 = load_font('regular', 11)
draw.text((20, 340), '野路实测，笔记为证：留下能用的', fill=GREY, font=f_reg_12)

# ============================================================
# 右侧区域 (x: 540-900)
# ============================================================

# --- 圆形装饰 ---
cx, cy = 720, 185
r = 75

# 外圆（细线）
draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=RED, width=1)

# 内圆（虚线效果 - 用点表示）
for angle in range(0, 360, 12):
    rad = angle * 3.14159 / 180
    dx = cx + (r - 8) * (1 if angle < 180 else -1)
    dy = cy + (r - 8) * 0.5 * (angle / 180 if angle < 180 else 2 - angle/180)
    draw.ellipse([dx-2, dy-2, dx+2, dy+2], fill=RED)

# --- 艺术大字「智能体」---
f_brush_90 = load_font('brush', 90)
if f_brush_90:
    draw.text((540, 100), '智能体', fill=RED, font=f_brush_90)
else:
    draw.text((540, 100), '智能体', fill=RED)

# --- 副标题 ---
draw.text((545, 210), 'AI生态的真相', fill=GREY, font=f_reg_14)
draw.text((555, 228), 'THE ECOSYSTEM', fill=GREY, font=f_reg_12)

# ============================================================
# 印章（右上红色圆形）
# ============================================================
seal_size = 70
seal_x, seal_y = W - seal_size - 15, 15

# 红色圆圈
draw.ellipse([seal_x, seal_y, seal_x+seal_size, seal_y+seal_size], 
             outline=RED, fill=None, width=3)

# 印章文字（垂直排列）
f_brush_18 = load_font('brush', 18)
if f_brush_18:
    draw.text((seal_x + 20, seal_y + 8), '弎', fill=RED, font=f_brush_18)
    draw.text((seal_x + 20, seal_y + 35), '水', fill=RED, font=f_brush_18)
else:
    # 备用：简单圆形内写文字
    draw.text((seal_x + 15, seal_y + 20), '弎水', fill=RED)

# ============================================================
# 日期标签（右下角红色方框）
# ============================================================
date_text = '2026.10'
f_bold_14 = load_font('bold', 14)
if f_bold_14:
    bbox = draw.textbbox((0,0), date_text, font=f_bold_14)
    dw, dh = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x, y = W - 25 - dw, H - 25 - dh
    draw.rectangle([x-3, y-3, x+dw+3, y+dh+3], outline=RED, fill=PAPER, width=2)
    draw.text((x, y), date_text, fill=RED, font=f_bold_14)

# 保存
out_path = '/var/minis/shared/gzh-team/选题库/ai-agent-ecosystem-20261006/封面图.png'
img.save(out_path, 'PNG')
print(f"✅ 封面生成成功：{os.path.getsize(out_path)} 字节")
print(f"尺寸：{img.size}")
