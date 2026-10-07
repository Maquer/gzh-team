#!/usr/bin/env python3

"""
cover-card.py：公众号封面图生成器（900x383，确定性PIL）
用法：python3 cover-card.py <参数>
关键约束：零AI生图依赖，纯PIL渲染
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont
RED = (194, 69, 60)          # #C2453C 主色
INK = (51, 51, 51)           # #333333 文字
PAPER = (245, 245, 245)      # #F5F5F5 背景
WHITE = (255, 255, 255)
GREY = (140, 140, 140)

FONT_B = '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc'
FONT_R = '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc'
FONT_SERIF = '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc'
FONT_MSZ = '/usr/share/fonts/noto/MaShanZheng-Regular.ttf'   # 毛笔楷书
FONT_LXGW = '/usr/share/fonts/noto/LXGWWenKai-Regular.ttf'  # 霞鹜文楷

# 品牌名补字组合：弎水=文楷，野记=毛笔（毛笔体缺「弎」，故逐字混排）
FONT_MAP = {'Serif': FONT_SERIF, 'Sans': FONT_B, 'MSZ': FONT_MSZ, 'LXGW': FONT_LXGW}
LOGO_A = [('弎', 'LXGW'), ('水', 'LXGW'), ('野', 'MSZ'), ('记', 'MSZ')]
BRAND = '<YOUR_BRAND>'
SLOGAN = '野路实测，笔记为证：留下能用的'

HEAD_W, HEAD_H = 900, 383     # 2.35:1 头条封面


def render_logo(logo, size, color):
    """渲染品牌 logo（2x 超采样 + 每字单独 RGBA paste）"""
    yeji_left = shui_right = shu_x0 = None
    if isinstance(logo, str):
        fb = ImageFont.truetype(FONT_MAP[logo], size)
        bb = fb.getbbox(BRAND)
        im = Image.new('RGBA', (bb[2] - bb[0] + 8, size * 2 + 40), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.text((4 - bb[0], size + 20 - bb[1]), BRAND, font=fb, fill=color)
    else:
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
        if len(sps) >= 3:
            shu_x0 = sps[0][0]
            shui_right = sps[1][1]
            yeji_left = sps[2][0]
        im = big.resize((W, H), Image.LANCZOS)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
        if yeji_left is not None:
            im.yeji_x = im.yeji_left = yeji_left - bbox[0]
        if shui_right is not None:
            im.shui_right = shui_right - bbox[0]
        if shu_x0 is not None:
            im.shu_x0 = shu_x0 - bbox[0]
    return im


def font(path, size, index=2):
    try:
        return ImageFont.truetype(path, size, index=index)
    except OSError:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return None
    return im


def measured(draw, text, fnt, max_w):
    width = lambda s: draw.textbbox((0, 0), s, font=fnt)[2]
    if width(text) <= max_w:
        return [text]
    # 优先在分隔符处切；否则穷举所有切点，选「两行宽度最接近」的那个
    for sep in ('，', '。', '：', '·', ' ', '、'):
        idx = text.find(sep)
        if idx > 0 and width(text[:idx]) <= max_w and width(text[idx + 1:]) <= max_w:
            return [text[:idx].rstrip('，。：、'), text[idx + 1:].lstrip('，。：、 ')]
    best, best_diff = None, 10 ** 9
    for i in range(1, len(text)):
        a, b = text[:i], text[i:]
        if width(a) <= max_w and width(b) <= max_w:
            diff = abs(width(a) - width(b))
            if diff < best_diff:
                best, best_diff = (a, b), diff
    if best:
        return list(best)
    # 兜底：贪心折行
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


def cover(title, sub, date, out, seal=True):
    return _cover_impl(title=title, sub=sub, date=date, out=out, seal=seal, mode='title')

def cover_summary(lines, date, out, seal=True):
    """摘要型封面：4 行小字左对齐，复用全部品牌元素（logo/印章/slogan/红条）"""
    return _cover_impl(title=None, sub=None, date=date, out=out, seal=seal, mode='summary', summary_lines=lines)

def _cover_impl(title, sub, date, out, seal=True, mode='title', summary_lines=None):
    img = Image.new('RGB', (HEAD_W, HEAD_H), PAPER)
    d = ImageDraw.Draw(img)
    f_title = font(FONT_B, 56)
    f_sub = font(FONT_R, 22)
    f_date = font(FONT_B, 17)

    # 左侧品牌红条（装饰，面积 <20%）
    d.rectangle([0, 0, 10, HEAD_H], fill=RED)
    # 品牌标识区（左上，固定）——补字组合 + 弎水下方横线 + 英文在野记下方
    logo = render_logo(LOGO_A, 30, RED)
    lx, ly = 56, 32
    img.paste(logo, (lx, ly), logo)
    # 横线左端=ryon字视觉左、右端=水字视觉右；英文左端=野字视觉左
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = font(FONT_R, 14)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), 'SANSHUI YEJI', font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), 'SANSHUI YEJI', font=f_en, fill=GREY, anchor='lt')

    # 品牌印章：程序化绘制 2x2 红印（<YOUR_BRAND>，右起竖读），避免裁切带白边
    # 品牌印章：优先贴真实红圆印章图（透明底）；缺图时退回程序化 2x2 红印
    side, sx, sy = 84, HEAD_W - 56 - 84, 28
    seal_img = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'assets', 'brand', 'seal-circle-84.png')
    if seal and os.path.exists(seal_img):
        img.paste(Image.open(seal_img), (sx, sy), Image.open(seal_img))
    elif seal:
        d.rectangle([sx, sy, sx + side, sy + side], fill=RED)
        f_seal = font(FONT_SERIF, 27)
        cell = side // 2
        # 右起竖读：弎(右上) 水(右下) 野(左上) 记(左下)
        d.rectangle([sx + cell + 6, sy + 6, sx + side - 6, sy + cell - 6], fill=WHITE)
        for ch, (cx, cy, fill) in [('野', (0, 0, WHITE)), ('弎', (1, 0, RED)),
                                   ('记', (0, 1, WHITE)), ('水', (1, 1, WHITE))]:
            bb = d.textbbox((0, 0), ch, font=f_seal)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            d.text((sx + cx * cell + (cell - cw) // 2 - bb[0],
                    sy + cy * cell + (cell - chh) // 2 - bb[1]),
                   ch, font=f_seal, fill=fill)
    # 注：印章为装饰性美术字，OCR 会误读（弎→國 水→杰）。跑 H11 门禁时须排除
    # 该 bbox：--exclude-box 值见 stderr 输出。--no-seal 可整块关掉。
    sys.stderr.write(f'[H11-EXCLUDE] seal bbox = {sx},0,{sx + side},{sy + side}\n')

    # 主标题（居中安全区内，<=2 行）
    if mode == 'title' and title:
        max_w = int(HEAD_W * 0.70)
        lines = measured(d, title.replace('，', ' '), f_title, max_w)
        lh = f_title.size + 12
        total = lh * len(lines)
        top = 104 if len(lines) <= 2 else 92
        y = top
        for ln in lines:
            w = d.textbbox((0, 0), ln, font=f_title)[2]
            d.text(((HEAD_W - w) // 2, y), ln, font=f_title, fill=INK)
            y += lh
        if len(lines) > 2:
            sys.stderr.write(f'[WARN] 标题折成 {len(lines)} 行，建议缩短\n')
        # 副标题
        if sub:
            sub_lines = measured(d, sub, f_sub, max_w)
            for sl in sub_lines:
                w = d.textbbox((0, 0), sl, font=f_sub)[2]
                d.text(((HEAD_W - w) // 2, y + 6), sl, font=f_sub, fill=(110, 110, 110))
                y += 28
    elif mode == 'summary' and summary_lines:
        # 摘要型：4 行小字左对齐
        f_sum = font(FONT_B, 26)
        max_w = int(HEAD_W * 0.80)
        y = 110
        for line in summary_lines[:4]:
            d.text((56, y), line, font=f_sum, fill=INK)
            y += 42

    # 底部：品牌红细线 + 日期角标
    d.rectangle([56, HEAD_H - 74, HEAD_W - 56, HEAD_H - 73], fill=(215, 215, 215))
    d.text((56, HEAD_H - 56), SLOGAN, font=font(FONT_R, 16), fill=GREY)
    if date:
        dt = date
        w = d.textbbox((0, 0), dt, font=f_date)[2]
        d.rounded_rectangle([HEAD_W - 56 - w - 28, HEAD_H - 62,
                             HEAD_W - 56, HEAD_H - 30], radius=6, outline=RED, width=2)
        d.text((HEAD_W - 56 - w - 14, HEAD_H - 55), dt, font=f_date, fill=RED)
    img.save(out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='公众号封面图 PIL 生成器（900x383）')
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
            sys.exit('[ERROR] --mode summary 需要 --summary 参数，4 行文字')
        stem = a.summary[0][:8].replace(' ', '').replace('，', '')
        hp = os.path.join(a.out_dir, f'封面图-{stem}.png')
        print(cover_summary(a.summary, a.date, hp, seal=not a.no_seal))
    else:
        if not a.title or not a.title.strip():
            sys.exit('[ERROR] --mode title 需要 --title 参数')
        if len(a.title) > 40:
            sys.stderr.write(f'[WARN] 标题 {len(a.title)} 字过长\n')
        non_cjk = [ch for ch in a.title if ord(ch) > 0x9FFF and ord(ch) not in range(0x3000, 0x303F)]
        if non_cjk:
            sys.stderr.write(f'[WARN] 标题含 {len(non_cjk)} 个非 CJK 字符\n')
        stem = a.title[:12].replace(' ', '').replace('，', '')
        hp = os.path.join(a.out_dir, f'封面图-{stem}.png')
        print(cover(a.title, a.sub, a.date, hp, seal=not a.no_seal))
