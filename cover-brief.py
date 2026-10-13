#!/usr/bin/env python3
"""cover-brief.py：公众号封面图生成器（900x383，摘要型封面）。

v4 垫片：CLI 参数与 v3.3.0 一致，渲染逻辑走 gzhkit.visual.canvas。
设计：不放标题，改为多行顶端对齐的小字号摘要（关键句/关键词）。
用法：python3 cover-brief.py --blurb "..." [--line "..." ...] [--date ...]
      [--out-dir DIR] [--no-seal]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli, report
from gzhkit.visual import canvas

HEAD_W, HEAD_H = canvas.COVER_W, canvas.COVER_H


def cover(blurb, date, out, seal=True, lines=None):
    """摘要型封面：无标题，多行小字摘要，前端（左）对齐。"""
    canvas.ensure_pillow()
    f_blurb = canvas.require_font('BOLD', 30)
    f_date = canvas.require_font('BOLD', 17)

    img, d = canvas.new_canvas(HEAD_W, HEAD_H, canvas.PAPER)

    # 左侧品牌红条
    d.rectangle([0, 0, 10, HEAD_H], fill=canvas.RED)

    # 品牌标识区（左上）：与 cover-card.py 同一套品牌块逻辑
    brand_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'assets', 'brand')
    canvas.draw_brand_block(img, d, brand_dir=brand_dir, prefer_asset=False,
                            lx=56, ly=28, logo_size=26)

    # 右上红印章（可选）：优先贴图，缺失 → 程序化回退
    if seal:
        canvas.draw_seal(img, d, brand_dir=brand_dir, style='square',
                         asset_name='seal-circle-84.png')
    sys.stderr.write('[H11-EXCLUDE] seal bbox = %d,0,%d,%d\n'
                     % (HEAD_W - 56 - 84, HEAD_W - 56, 28 + 84))

    # 摘要正文：前端左对齐，小字号
    left, max_w = 70, 760
    blurb_lines = lines if lines else canvas.wrap_lines(d, blurb, f_blurb, max_w)

    lh, start_y, y = 44, 130, 130
    for ln in blurb_lines:
        d.text((left, y), ln, font=f_blurb, fill=canvas.INK)
        y += lh

    canvas.draw_footer(d, date=date)
    img.save(out)
    return out


def main():
    ap = cli.build_parser('cover-brief.py', '公众号摘要型封面（无标题，多行小字摘要）900x383')
    ap.add_argument('--blurb', default='3 款本地 AI 实测：不联网也能用？')
    ap.add_argument('--line', action='append', help='摘要某一行（可多次），优先于 --blurb')
    ap.add_argument('--date', default='2026.10.04')
    ap.add_argument('--out-dir', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'assets', 'out'))
    ap.add_argument('--no-seal', action='store_true', help='不画右上红印章')
    a = ap.parse_args()

    if not a.blurb.strip() and not a.line:
        report.die_input('需要 --blurb 或至少一个 --line')
    os.makedirs(a.out_dir, exist_ok=True)
    stem = '摘要封面-' + (a.blurb[:10] if a.line is None else 'manual')
    hp = os.path.join(a.out_dir, '%s.png' % stem)
    print(cover(a.blurb, a.date, hp, seal=not a.no_seal,
                lines=a.line if a.line else None))
    return 0


if __name__ == '__main__':
    cli.run_main(main)
