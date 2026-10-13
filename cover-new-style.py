#!/usr/bin/env python3
"""cover-new-style.py：新版封面生成器（900x383）。

v4 垫片：版式复刻 v3.3.0（左侧品牌+热搜标题+核心观点 / 右侧圆形装饰+
艺术大字 / 右上印章 / 右下日期标签），渲染逻辑走 gzhkit.visual.canvas。
v3.3.0 只接受输出路径位置参数；v4 保留该兼容，并增加 --keyword 等覆盖项。

字体分工（v3.2.0，原样保留）：热点大字用毛笔 MaShanZheng。
用法：python3 cover-new-style.py [输出路径] [--keyword X] [--lines "a;b;c"]
      [--topic T] [--date YYYY.MM]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli
from gzhkit.visual import canvas

W, H = canvas.COVER_W, canvas.COVER_H
PAPER_WARM = (250, 248, 245)  # 接近样板的米白色


def generate_new_style(out_path, keyword='智能体', lines=None,
                       topic='AI智能体生态观察', topic_en='THE ECOSYSTEM',
                       topic_cn_sub='AI生态的真相', date='2026.10'):
    canvas.ensure_pillow()
    lines = lines or ['我研究了90个', 'AI智能体项目', '发现最值钱的不是智能体本身']

    img, d = canvas.new_canvas(W, H, PAPER_WARM)

    # ── 左侧品牌区 ──
    d.line([(20, 48), (100, 48)], fill=canvas.RED, width=2)
    f_brand = canvas.require_font('MSZ', 30)
    d.text((20, 10), canvas.BRAND_NAME, fill=canvas.RED, font=f_brand)
    d.text((22, 42), canvas.BRAND_EN, fill=canvas.GREY,
           font=canvas.require_font('NORMAL', 12))

    # ── 热搜标题 ──
    f_topic = canvas.require_font('BOLD', 16)
    d.text((20, 65), topic, fill=canvas.RED, font=f_topic)
    bbox = d.textbbox((20, 65), topic, font=f_topic)
    d.line([(bbox[0], bbox[3] + 3), (bbox[2], bbox[3] + 3)], fill=canvas.RED, width=2)

    # ── 核心观点（大号黑字）──
    f_view = canvas.require_font('BOLD', 40)
    y = 100
    for line in lines:
        d.text((20, y), line, fill=canvas.INK, font=f_view)
        y += 50

    f_small = canvas.require_font('NORMAL', 14)
    d.text((20, 300), '%s · 深度观察' % date, fill=canvas.GREY, font=f_small)
    d.text((20, 340), canvas.SLOGAN, fill=canvas.GREY,
           font=canvas.require_font('NORMAL', 11))

    # ── 右侧圆形装饰 ──
    cx, cy, r = 720, 185, 75
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=canvas.RED, width=1)
    for angle in range(0, 360, 12):
        rad = angle * 3.14159 / 180
        dx = cx + (r - 8) * (1 if angle < 180 else -1)
        dy = cy + (r - 8) * 0.5 * (angle / 180 if angle < 180 else 2 - angle / 180)
        d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=canvas.RED)

    # ── 艺术大字（毛笔）──
    f_art = canvas.require_font('MSZ', 90)
    d.text((540, 100), keyword, fill=canvas.RED, font=f_art)
    d.text((545, 210), topic_cn_sub, fill=canvas.GREY, font=f_small)
    d.text((555, 228), topic_en, fill=canvas.GREY,
           font=canvas.require_font('NORMAL', 12))

    # ── 印章（右上红色圆形，程序化绘制）──
    seal_size, sx, sy = 70, W - 70 - 15, 15
    d.ellipse([sx, sy, sx + seal_size, sy + seal_size],
              outline=canvas.RED, width=3)
    f_seal = canvas.require_font('MSZ', 18)
    d.text((sx + 20, sy + 8), canvas.SEAL_CHARS[0], fill=canvas.RED, font=f_seal)
    d.text((sx + 20, sy + 35), canvas.SEAL_CHARS[1], fill=canvas.RED, font=f_seal)

    # ── 日期标签（右下角红色方框）──
    f_date = canvas.require_font('BOLD', 14)
    bbox = d.textbbox((0, 0), date, font=f_date)
    dw, dh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = W - 25 - dw, H - 25 - dh
    d.rectangle([x - 3, y - 3, x + dw + 3, y + dh + 3],
                outline=canvas.RED, fill=PAPER_WARM, width=2)
    d.text((x, y), date, fill=canvas.RED, font=f_date)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path, 'PNG')
    print('✅ 封面生成成功：%d 字节' % os.path.getsize(out_path))
    print('尺寸：%s' % (img.size,))
    return out_path


def main():
    ap = cli.build_parser('cover-new-style.py', '新版封面生成器（900x383）')
    ap.add_argument('out', nargs='?',
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         'assets', 'out', '封面图-新风格.png'),
                    help='输出路径')
    ap.add_argument('--keyword', default='智能体', help='右侧艺术大字')
    ap.add_argument('--lines', default=None, help='左侧核心观点行，分号分隔')
    ap.add_argument('--topic', default='AI智能体生态观察', help='热搜标题')
    ap.add_argument('--date', default='2026.10', help='日期标签')
    a = ap.parse_args()

    generate_new_style(a.out, keyword=a.keyword,
                       lines=a.lines.split(';') if a.lines else None,
                       topic=a.topic, date=a.date)
    return 0


if __name__ == '__main__':
    cli.run_main(main)
