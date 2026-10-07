#!/usr/bin/env python3
"""brand-font-schemes.py：品牌字体方案模块（弎水=文楷，野记=毛笔）
用法：被 cover-pipeline.py / gate-H11.py import 时引用 FONT_MAP/LOGO_A/render_logo
关键约束：不直接运行，仅供 import；需要 Noto 字体文件存在
"""
import os
from PIL import Image, ImageDraw, ImageFont

BRAND = '<YOUR_BRAND>'
SLOGAN = '野路实测，笔记为证：留下能用的'
EN = 'SANSHUI YEJI'
RED = (194, 69, 60)
INK = (51, 51, 51)
PAPER = (245, 245, 245)
WHITE = (255, 255, 255)
GREY = (140, 140, 140)

N = '/usr/share/fonts/noto/'
FONT_MAP = {
    'MaShanZheng': f'{N}MaShanZheng-Regular.ttf',   # 毛笔楷书
    'LXGW':        f'{N}LXGWWenKai-Regular.ttf',    # 霞鹜文楷
    'Serif':       f'{N}NotoSerifCJK-Bold.ttc',     # 宋体（粗）
    'Sans':        f'{N}NotoSansCJK-Bold.ttc',      # 黑体（粗）
}

def fnt(name, size, index=2):
    p = FONT_MAP[name]
    try:
        return ImageFont.truetype(p, size, index=index)
    except Exception:
        return ImageFont.truetype(p, size, index=0)

# 方案 A：逐字组合 logo = [('弎','LXGW'),('水','LXGW'),('野','MaShanZheng'),('记','MaShanZheng')]
LOGO_A = [('弎', 'LXGW'), ('水', 'LXGW'), ('野', 'MaShanZheng'), ('记', 'MaShanZheng')]
LOGO_SIZE_A = 42

QR_PATH = '/var/minis/shared/gzh-team/assets/brand/qr-code.png'
QR_SIZE = 240


def render_logo(size, logo, color):
    yeji_left = shui_right = shu_x0 = None
    if isinstance(logo, str):
        fb = fnt(logo, size)
        bb = fb.getbbox(BRAND)
        im = Image.new('RGBA', (bb[2] - bb[0] + 8, size * 2 + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((4 - bb[0], size + 20 - bb[1]), BRAND, font=fb, fill=color)
    else:
        gap, pad, ss = 8, 20, 2
        # ss=2 超采样：1x 网格上各字像素高奇偶不同，整数 py 会让中心在 cy
        # 上下各漂 0.5~1px（30px 档尤其明显）；放大到 2x 后高度全为偶数，
        # py 精确命中 cy，缩回 1x 由 LANCZOS 完成亚像素混合，四字中心一致。
        glyphs = []
        for ch, fn in logo:
            fb = fnt(fn, size * ss)
            cell = Image.new('RGBA', (size * 3 * ss, size * 3 * ss), (0, 0, 0, 0))
            ImageDraw.Draw(cell).text((size * ss, size * ss), ch, font=fb, fill=color)
            glyphs.append((ch, cell.crop(cell.getbbox())))
        H = size * 2 + 40
        W = sum(round(g.width / ss) for _, g in glyphs) + \
            gap * (len(glyphs) - 1) + pad * 2 + 2
        big = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
        cy = big.height / 2
        span = {}
        x = pad * ss
        for ch, g in glyphs:
            px2 = int(x)
            py2 = int(round(cy - g.height / 2))
            big.paste(g, (px2, py2), g)
            # 同帧用 alpha>128 测视觉边界：LANCZOS 会让 alpha>0 的边缘扩散
            # 1~4px，直接记 paste 位置会与"肉眼看到的字边"错位
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
        # 按 logo 顺序取：横线覆盖前两个字，英文左端对齐第三个字。
        # 用索引而非字面量，避免把「ryon」误打成 ASCII "ryon" 导致静默失效。
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


def make_tail(out_path, next_title=None):
    W, H = 900, 400
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, H], fill=RED)          # 左侧品牌红条

    # 品牌名（补字组合）+ 弎水下方横线 + 英文在野记下方
    logo = render_logo(LOGO_SIZE_A, LOGO_A, RED)
    lx, ly = 56, 40
    img.paste(logo, (lx, ly), logo)

    # 横线覆盖弎水宽（lx→yeji_x）；英文在野记下方左对齐，横线在英文实际中线
    # 横线左端=ryon字左、右端=水字右（真像素边界）；英文左端=野字左
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = fnt('Sans', 14)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), EN, font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), EN, font=f_en, fill=GREY, anchor='lt')

    f_cta = fnt('Sans', 22)
    d.text((56, 148), '点右上角 · 关注不迷路', font=f_cta, fill=INK)
    if next_title:
        f_next = fnt('Sans', 16)
        d.text((56, 180), f'下一篇 · {next_title}', font=f_next, fill=RED)

    # 灰色分隔线：slogan 字形实际 top y=350，间隙 23px 对齐封面图（333-310）
    d.rectangle([56, 326, 56 + 440, 327], fill=(225, 225, 225))

    f_slog = fnt('Sans', 16)
    d.text((56, H - 56), SLOGAN, font=f_slog, fill=GREY)

    # 日期角标（右下）
    f_date = fnt('Sans', 14)
    date_text = '2026.09'
    bb = d.textbbox((0, 0), date_text, font=f_date)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    px, pty, pby = 12, 4, 2
    bw2, bh2 = tw + px * 2, th + pty + pby
    bx1, by1 = W - 56, H - 26
    bx0, by0 = bx1 - bw2, by1 - bh2
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, outline=RED, width=2)
    d.text((bx0 + px - bb[0], by0 + pty - bb[1]), date_text, font=f_date, fill=RED)

    # 右侧二维码（无白底卡片）
    qzx, qzw = 620, 280
    qy = 60
    qx = qzx + (qzw - QR_SIZE) // 2
    try:
        qr = Image.open(QR_PATH).convert('RGB').crop((256, 152, 864, 760))
        img.paste(qr.resize((QR_SIZE, QR_SIZE), Image.LANCZOS), (qx, qy))
    except Exception as e:
        print('[WARN] QR', e)
    f_qr = fnt('Sans', 18)
    lab = '↑ 扫码关注'
    lw = d.textbbox((0, 0), lab, font=f_qr)[2]
    d.text((qzx + (qzw - lw) // 2, qy + QR_SIZE + 14), lab, font=f_qr, fill=RED)

    img.save(out_path)
    print(out_path)
    return out_path


def make_preview(out_path):
    W, H = 450, 200
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 8, H], fill=RED)         # 左红条（尾图10→缩8）

    # 品牌名（补字组合）+ 弎水下方横线 + 英文在野记下方
    logo = render_logo(26, LOGO_A, RED)
    lx, ly = 28, 16
    img.paste(logo, (lx, ly), logo)

    # 横线覆盖弎水宽；英文在野记下方左对齐，横线在英文实际中线
    # 横线左端=ryon字左、右端=水字右（真像素边界）；英文左端=野字左
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = fnt('Sans', 11)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), EN, font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), EN, font=f_en, fill=GREY, anchor='lt')

    # 关注 CTA
    f_cta = fnt('Sans', 18)
    d.text((lx, en_top + 22), '点右上角 · 关注不迷路', font=f_cta, fill=INK)

    # 浅灰分隔线：slogan 字形实际 top y=178，字号 12=封面图 16 的 0.75 倍，间隙 17px
    d.rectangle([lx, 160, W - 28, 161], fill=(225, 225, 225))

    # Slogan
    f_slog = fnt('Sans', 12)
    d.text((lx, H - 26), SLOGAN, font=f_slog, fill=GREY)

    # 日期角标（右下）
    f_date = fnt('Sans', 11)
    dt = '2026.09'
    bb = d.textbbox((0, 0), dt, font=f_date)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = 8, 2
    bx1, by1 = W - 20, H - 10
    bx0, by0 = bx1 - (tw + pad_x * 2), by1 - (th + pad_y * 2)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=3, outline=RED, width=1)
    d.text((bx0 + pad_x - bb[0], by0 + pad_y - bb[1]), dt, font=f_date, fill=RED)

    img.save(out_path)
    print(out_path)
    return out_path


if __name__ == '__main__':
    out_dir = '/var/minis/shared/gzh-team/assets/out'
    os.makedirs(out_dir, exist_ok=True)
    make_tail(f'{out_dir}/尾图-v4.png')
    make_tail(f'{out_dir}/尾图-v4-预告.png', next_title='Prompt 模板配方')
    make_follow_cover(f'{out_dir}/首图-关注引导.png')
    make_preview(f'{out_dir}/品牌名-方案A-定稿.png')
