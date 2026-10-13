#!/usr/bin/env python3
"""cover-card.py：公众号封面图生成器（900x383，确定性 PIL）。

v4 垫片：CLI 参数与 v3.3.0 一致，渲染逻辑走 gzhkit.visual.canvas。
关键约束：零 AI 生图依赖，纯 PIL 渲染。
用法：python3 cover-card.py --title "标题" [--sub 副标题] [--date 2026.10]
      [--out-dir DIR] [--no-seal] [--mode title|summary] [--summary 行 ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli, report
from gzhkit.visual import canvas

HEAD_W, HEAD_H = canvas.COVER_W, canvas.COVER_H


def cover(title, sub, date, out, seal=True):
    """标题型封面。"""
    return _cover_impl(title=title, sub=sub, date=date, out=out,
                       seal=seal, mode='title')


def cover_summary(lines, date, out, seal=True):
    """摘要型封面：4 行小字左对齐，复用全部品牌元素。"""
    return _cover_impl(title=None, sub=None, date=date, out=out,
                       seal=seal, mode='summary', summary_lines=lines)


def _cover_impl(title, sub, date, out, seal=True, mode='title', summary_lines=None):
    canvas.ensure_pillow()
    # 需要真实中文字体：缺字体 → 明错 + exit 2（不 traceback）
    f_title = canvas.require_font('BOLD', 56)
    f_sub = canvas.require_font('NORMAL', 22)
    f_date = canvas.require_font('BOLD', 17)

    img, d = canvas.new_canvas(HEAD_W, HEAD_H, canvas.PAPER)

    # 左侧品牌红条（装饰，面积 <20%）
    d.rectangle([0, 0, 10, HEAD_H], fill=canvas.RED)

    # 品牌标识区（左上，固定）：逐字混排 + 红线 + 英文
    brand_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'assets', 'brand')
    canvas.draw_brand_block(img, d, brand_dir=brand_dir, prefer_asset=False,
                            lx=56, ly=32, logo_size=30)

    # 右上印章：优先贴预制印章图，缺失 → 程序化 2x2 红印回退
    if seal:
        canvas.draw_seal(img, d, brand_dir=brand_dir, style='square',
                         asset_name='seal-circle-84.png')
    # 注：印章为装饰性美术字，OCR 会误读。跑 H11 门禁时须排除该 bbox，
    # --no-seal 可整块关掉。
    sys.stderr.write('[H11-EXCLUDE] seal bbox = %d,0,%d,%d\n'
                     % (HEAD_W - 56 - 84, HEAD_W - 56, 28 + 84))

    if mode == 'title' and title:
        max_w = int(HEAD_W * 0.70)
        lines = canvas.wrap_lines(d, title.replace('，', ' '), f_title, max_w)
        lh = f_title.size + 12
        top = 104 if len(lines) <= 2 else 92
        y = top
        for ln in lines:
            w = d.textbbox((0, 0), ln, font=f_title)[2]
            d.text(((HEAD_W - w) // 2, y), ln, font=f_title, fill=canvas.INK)
            y += lh
        if len(lines) > 2:
            sys.stderr.write('[WARN] 标题折成 %d 行，建议缩短\n' % len(lines))
        if sub:
            for sl in canvas.wrap_lines(d, sub, f_sub, max_w):
                w = d.textbbox((0, 0), sl, font=f_sub)[2]
                d.text(((HEAD_W - w) // 2, y + 6), sl, font=f_sub,
                       fill=(110, 110, 110))
                y += 28
    elif mode == 'summary' and summary_lines:
        f_sum = canvas.require_font('BOLD', 26)
        max_w = int(HEAD_W * 0.80)
        y = 110
        for line in summary_lines[:4]:
            d.text((56, y), line, font=f_sum, fill=canvas.INK)
            y += 42

    canvas.draw_footer(d, date=date)
    img.save(out)
    return out


def main():
    ap = cli.build_parser('cover-card.py', '公众号封面图 PIL 生成器（900x383）')
    ap.add_argument('--title', default=None, help='标题型封面标题')
    ap.add_argument('--sub', default='', help='副标题')
    ap.add_argument('--date', default='2026.10')
    ap.add_argument('--out-dir', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'assets', 'out'))
    ap.add_argument('--no-seal', action='store_true', help='不画右上红印章')
    ap.add_argument('--mode', choices=['title', 'summary'], default='title',
                    help='title=标题型（默认），summary=摘要型（4行小字）')
    ap.add_argument('--summary', nargs='+', help='摘要型：4行文字')
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)

    if a.mode == 'summary':
        if not a.summary:
            report.die_input('--mode summary 需要 --summary 参数，4 行文字')
        stem = a.summary[0][:8].replace(' ', '').replace('，', '')
        hp = os.path.join(a.out_dir, '封面图-%s.png' % stem)
        print(cover_summary(a.summary, a.date, hp, seal=not a.no_seal))
    else:
        if not a.title or not a.title.strip():
            report.die_input('--mode title 需要 --title 参数')
        if len(a.title) > 40:
            sys.stderr.write('[WARN] 标题 %d 字过长\n' % len(a.title))
        non_cjk = [ch for ch in a.title
                   if ord(ch) > 0x9FFF and ord(ch) not in range(0x3000, 0x303F)]
        if non_cjk:
            sys.stderr.write('[WARN] 标题含 %d 个非 CJK 字符\n' % len(non_cjk))
        stem = a.title[:12].replace(' ', '').replace('，', '')
        hp = os.path.join(a.out_dir, '封面图-%s.png' % stem)
        print(cover(a.title, a.sub, a.date, hp, seal=not a.no_seal))
    return 0


if __name__ == '__main__':
    cli.run_main(main)
