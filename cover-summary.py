#!/usr/bin/env python3
"""cover-summary.py：摘要型封面图生成器（900×383）。

v4 垫片：CLI 参数与 v3.3.0 一致（--summary1..4/--date/--out），
渲染逻辑走 gzhkit.visual.canvas。
4 行小字关键词左对齐，底部品牌条 + 日期。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli
from gzhkit.visual import canvas

W, H = canvas.COVER_W, canvas.COVER_H


def make_summary_cover(summaries, date='2026.10', out_path=None):
    """生成摘要型封面图。summaries: 4 行摘要文字列表。返回输出路径。"""
    canvas.ensure_pillow()
    if out_path is None:
        out_path = '封面图-摘要-%s.png' % date

    f_sub = canvas.require_font('NORMAL', 18)
    f_date = canvas.require_font('NORMAL', 14)

    img, d = canvas.new_canvas(W, H, canvas.CREAM)

    y_start, line_height = 80, 50
    for i, line in enumerate(summaries[:4]):
        d.text((50, y_start + i * line_height), line, font=f_sub,
               fill=(28, 28, 34))

    # 底部品牌区
    d.rectangle([0, H - 60, W, H], fill=canvas.RED)
    d.text((50, H - 40), '%s · %s' % (canvas.BRAND_NAME, canvas.BRAND_EN),
           font=f_sub, fill=canvas.WHITE)
    if date:
        d.text((W - 150, H - 40), date, font=f_date, fill=canvas.WHITE)

    img.save(out_path)
    return out_path


def main():
    ap = cli.build_parser('cover-summary.py', '摘要型封面图生成器')
    ap.add_argument('--summary1', required=True, help='摘要第1行')
    ap.add_argument('--summary2', required=True, help='摘要第2行')
    ap.add_argument('--summary3', required=True, help='摘要第3行')
    ap.add_argument('--summary4', required=True, help='摘要第4行')
    ap.add_argument('--date', default='2026.10')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    out_path = a.out or '封面图-摘要-%s.png' % a.date
    result = make_summary_cover([a.summary1, a.summary2, a.summary3, a.summary4],
                                a.date, out_path)
    print('✅ 已生成: %s' % result)
    return 0


if __name__ == '__main__':
    cli.run_main(main)
