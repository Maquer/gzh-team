#!/usr/bin/env python3
"""
摘要型封面图生成器（900×383）
4行小字关键词左对齐，无标题，品牌红条+印章
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

# 品牌色
RED = (194, 69, 60)
CREAM = (245, 242, 235)
GREY = (110, 110, 110)
BLACK = (28, 28, 34)

def font(name, size):
    return ImageFont.truetype(name, size)

def make_summary_cover(summaries, date="2026.10", out_path=None):
    """
    生成摘要型封面图
    
    参数:
        summaries: 列表，4行摘要文字
        date: 日期字符串
        out_path: 输出路径
    
    返回:
        输出路径
    """
    W, H = 900, 383
    
    if out_path is None:
        out_path = f"封面图-摘要-{date}.png"
    
    # 创建画布
    img = Image.new('RGBA', (W, H), CREAM + (255,))
    d = ImageDraw.Draw(img)
    
    # 字体路径
    font_dir = "/usr/share/fonts/noto"
    f_title = font(f"{font_dir}/NotoSansCJK-Bold.ttc", 28)
    f_sub = font(f"{font_dir}/NotoSansCJK-Regular.ttc", 18)
    f_date = font(f"{font_dir}/NotoSansCJK-Regular.ttc", 14)
    
    # 绘制内容
    y_start = 80
    line_height = 50
    
    # 标题（可选）
    for i, line in enumerate(summaries[:4]):
        x = 50
        d.text((x, y_start + i * line_height), line, font=f_sub, fill=BLACK)
    
    # 底部品牌区
    d.rectangle([0, H - 60, W, H], fill=RED)
    d.text((50, H - 40), "<YOUR_BRAND> · <YOUR_BRAND_EN>", font=f_sub, fill=(255, 255, 255))
    
    if date:
        d.text((W - 150, H - 40), date, font=f_date, fill=(255, 255, 255))
    
    # 保存
    img.save(out_path)
    return out_path

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='摘要型封面图生成器')
    ap.add_argument('--summary1', required=True, help='摘要第1行')
    ap.add_argument('--summary2', required=True, help='摘要第2行')
    ap.add_argument('--summary3', required=True, help='摘要第3行')
    ap.add_argument('--summary4', required=True, help='摘要第4行')
    ap.add_argument('--date', default='2026.10')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    
    summaries = [a.summary1, a.summary2, a.summary3, a.summary4]
    out_path = a.out or f"封面图-摘要-{a.date}.png"
    result = make_summary_cover(summaries, a.date, out_path)
    print(f"✅ 已生成: {result}")
