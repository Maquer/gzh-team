#!/usr/bin/env python3
"""
cover-brief.py：公众号封面图生成器（900x383，摘要型封面）
用法：python3 cover-brief.py --blurb "..." --out-dir ...
设计：不放标题，改为 4 行顶端对齐的小字号摘要（关键句/关键词），概括文章内容
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

RED = (194, 69, 60)
INK = (51, 51, 51)
PAPER = (245, 245, 245)
GREY = (140, 140, 140)
WHITE = (255, 255, 255)

FONT_B = '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc'
FONT_R = '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc'
FONT_SERIF = '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc'
FONT_MSZ = '/usr/share/fonts/noto/MaShanZheng-Regular.ttf'
FONT_LXGW = '/usr/share/fonts/noto/LXGWWenKai-Regular.ttf'

FONT_MAP = {'Serif': FONT_SERIF, 'Sans': FONT_B, 'MSZ': FONT_MSZ, 'LXGW': FONT_LXGW}
LOGO_A = [('弎', 'LXGW'), ('水', 'LXGW'), ('野', 'MSZ'), ('记', 'MSZ')]
BRAND = '<YOUR_BRAND>'
SLOGAN = '野路实测，笔记为证：留下能用的'
HEAD_W, HEAD_H = 900, 383


def render_logo(logo, size, color):
    """渲染品牌 logo（2x 超采样 + 每字单独 RGBA paste），返回带 yeji_x/shui_right/shu_x0 属性的 Image"""
    gap, pad, ss = 6, 20, 2
    items = []
    for ch, fn in logo:
        try:
            fb = ImageFont.truetype(FONT_MAP[fn], size * ss, index=2)
        except OSError:
            fb = ImageFont.truetype(FONT_MAP[fn], size * ss, index=0)
        cell = Image.new('RGBA', (size * 3 * ss, size * 3 * ss), (0, 0, 0, 0))
        ImageDraw.Draw(cell).text((size * ss, size * ss), ch, font=fb, fill=color)
        items.append((ch, cell.crop(cell.getbbox())))
    H = size * 2 + 40
    W = sum(round(g.width / ss) for _, g in items) + \
        gap * (len(items) - 1) + pad * 2 + 2
    big = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
    cy = big.height / 2
    span = {}
    x = pad * ss
    for ch, g in items:
        px2 = int(x)
        py2 = int(round(cy - g.height / 2))
        big.paste(g, (px2, py2), g)
        bx = big.getchannel('A').crop((px2, py2, px2 + g.width, py2 + g.height))
        a0 = a1 = None
        for k in range(bx.width):
            if bx.crop((k, 0, k + 1, bx.height)).getextrema()[1] > 128:
                if a0 is None:
                    a0 = k
                a1 = k
        if a0 is not None:
            span[ch] = ((px2 + a0) / ss, (px2 + a1) / ss)
        x += g.width + gap * ss
    sps = list(span.values())
    yeji_left = shui_right = shu_x0 = None
    if len(sps) >= 3:
        shu_x0 = sps[0][0]
        shui_right = sps[1][1]
        yeji_left = sps[2][0]
    im = big.resize((W, H), Image.LANCZOS)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
        if yeji_left is not None:
            im.yeji_x = yeji_left - bbox[0]
        if shui_right is not None:
            im.shui_right = shui_right - bbox[0]
        if shu_x0 is not None:
            im.shu_x0 = shu_x0 - bbox[0]
    return im


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(path, size)


def measured(draw, text, fnt, max_w):
    width = lambda s: draw.textbbox((0, 0), s, font=fnt)[2]
    if width(text) <= max_w:
        return [text]
    lines, cur = [], ''
    for ch in text:
        if width(cur + ch) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def cover(blurb, date, out, seal=True, lines=None):
    """摘要型封面：无标题，多行小字摘要，前端（左）对齐"""
    img = Image.new('RGB', (HEAD_W, HEAD_H), PAPER)
    d = ImageDraw.Draw(img)
    f_blurb = font(FONT_B, 30)
    f_date = font(FONT_B, 17)

    # 左侧品牌红条
    d.rectangle([0, 0, 10, HEAD_H], fill=RED)

    # 品牌标识区（左上）—— 对齐 cover-card.py 的完整逻辑
    logo = render_logo(LOGO_A, 26, RED)
    lx, ly = 56, 28
    img.paste(logo, (lx, ly), logo)
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = font(FONT_R, 13)
    en_top = ly + logo.height + 2
    bbox = d.textbbox((yeji_left, en_top), 'SANSHUI YEJI', font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), 'SANSHUI YEJI', font=f_en, fill=GREY, anchor='lt')

    # 右上红印章（可选）
    side, sx, sy = 84, HEAD_W - 56 - 84, 28
    seal_img = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'assets', 'brand', 'seal-circle-84.png')
    if seal and os.path.exists(seal_img):
        img.paste(Image.open(seal_img), (sx, sy), Image.open(seal_img))
    sys.stderr.write(f'[H11-EXCLUDE] seal bbox = {sx},0,{sx + side},{sy + side}\n')

    # 摘要正文：前端左对齐，小字号
    left = 70
    max_w = 760
    if lines:
        blurb_lines = lines
    else:
        blurb_lines = measured(d, blurb, f_blurb, max_w)

    lh = 44
    start_y = 130
    y = start_y
    for ln in blurb_lines:
        d.text((left, y), ln, font=f_blurb, fill=INK)
        y += lh

    # 底部：品牌红细线 + 日期角标
    d.rectangle([56, HEAD_H - 74, HEAD_W - 56, HEAD_H - 73], fill=(215, 215, 215))
    d.text((56, HEAD_H - 56), SLOGAN, font=font(FONT_R, 16), fill=GREY)
    if date:
        w = d.textbbox((0, 0), date, font=f_date)[2]
        d.rounded_rectangle([HEAD_W - 56 - w - 28, HEAD_H - 62,
                             HEAD_W - 56, HEAD_H - 30], radius=6, outline=RED, width=2)
        d.text((HEAD_W - 56 - w - 14, HEAD_H - 55), date, font=f_date, fill=RED)
    img.save(out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='公众号摘要型封面（无标题，多行小字摘要）900x383')
    ap.add_argument('--blurb', default='3 款本地 AI 实测：不联网也能用？')
    ap.add_argument('--line', action='append', help='摘要某一行（可多次），优先于 --blurb')
    ap.add_argument('--date', default='2026.10.04')
    ap.add_argument('--out-dir', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'assets', 'out'))
    ap.add_argument('--no-seal', action='store_true', help='不画右上红印章')
    a = ap.parse_args()

    if not a.blurb.strip() and not a.line:
        sys.exit('[ERROR] 需要 --blurb 或至少一个 --line')
    os.makedirs(a.out_dir, exist_ok=True)
    stem = '摘要封面-' + (a.blurb[:10] if a.line is None else 'manual')
    hp = os.path.join(a.out_dir, f'{stem}.png')
    lines = a.line if a.line else None
    print(cover(a.blurb, a.date, hp, seal=not a.no_seal, lines=lines))
