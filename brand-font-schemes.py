#!/usr/bin/env python3
"""brand-font-schemes.py：品牌字体方案模块。

v4 垫片：对外接口与 v3.3.0 一致（FONT_MAP / LOGO_A / render_logo /
make_tail / make_follow_cover / make_preview），实现走 gzhkit.visual.canvas。
字体分工（v3.2.0，原样保留）：品牌名前二字=文楷 LXGW，后二字=毛笔 MaShanZheng。
关键约束：被 import 时不执行渲染；直接运行时生成 4 张品牌资产图。
品牌字已脱敏为占位字符，自有部署替换 canvas.LOGO_CHARS 即可。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit.visual import canvas

BRAND = canvas.BRAND_NAME
SLOGAN = canvas.SLOGAN
EN = canvas.BRAND_EN
RED = canvas.RED
INK = canvas.INK
PAPER = canvas.PAPER
WHITE = canvas.WHITE
GREY = canvas.GREY

# 字体角色映射（v3.3.0 FONT_MAP 的语义，路径收敛到 canvas 回退链）
FONT_MAP = {'MaShanZheng': 'MSZ', 'LXGW': 'LXGW', 'Serif': 'SERIF', 'Sans': 'BOLD'}

# 方案 A：逐字组合 logo = 前二字文楷 + 后二字毛笔
LOGO_A = canvas.LOGO_CHARS
LOGO_SIZE_A = 42

HERE = os.path.dirname(os.path.abspath(__file__))
QR_PATH = os.path.join(HERE, 'assets', 'brand', 'qr-code.png')
QR_SIZE = 240


def fnt(name, size):
    """v3.3.0 fnt(name, size) 兼容入口：name 取 FONT_MAP 的键。"""
    return canvas.load_font(FONT_MAP.get(name, 'NORMAL'), size)


def render_logo(size, logo=None, color=RED):
    """v3.3.0 render_logo(size, logo, color) 兼容入口。"""
    return canvas.render_logo(logo or LOGO_A, size, color)


def _brand_block(img, d, logo_size, lx, ly, en_size=14):
    """品牌名（补字组合）+ 横线 + 英文，三处共用。"""
    logo = render_logo(logo_size, LOGO_A, RED)
    img.paste(logo, (lx, ly), logo)
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = fnt('Sans', en_size)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), EN, font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), EN, font=f_en, fill=GREY, anchor='lt')
    return logo


def make_tail(out_path, next_title=None):
    """尾图 900x400：左红条 + 品牌块 + 关注 CTA + slogan + 日期角标 + 二维码。"""
    canvas.ensure_pillow()
    from PIL import Image, ImageDraw
    W, H = 900, 400
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 10, H], fill=RED)

    _brand_block(img, d, LOGO_SIZE_A, 56, 40)

    d.text((56, 148), '点右上角 · 关注不迷路', font=fnt('Sans', 22), fill=INK)
    if next_title:
        d.text((56, 180), '下一篇 · %s' % next_title, font=fnt('Sans', 16), fill=RED)

    # 灰色分隔线
    d.rectangle([56, 326, 56 + 440, 327], fill=(225, 225, 225))
    d.text((56, H - 56), SLOGAN, font=fnt('Sans', 16), fill=GREY)

    # 日期角标（右下）
    f_date = fnt('Sans', 14)
    date_text = '2026.09'
    bb = d.textbbox((0, 0), date_text, font=f_date)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    px, pty, pby = 12, 4, 2
    bx1, by1 = W - 56, H - 26
    bx0, by0 = bx1 - (tw + px * 2), by1 - (th + pty + pby)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=4, outline=RED, width=2)
    d.text((bx0 + px - bb[0], by0 + pty - bb[1]), date_text, font=f_date, fill=RED)

    # 右侧二维码（无白底卡片；缺失 → 警告并跳过，exit 0）
    qzx, qzw, qy = 620, 280, 60
    qx = qzx + (qzw - QR_SIZE) // 2
    try:
        qr = Image.open(QR_PATH).convert('RGB').crop((256, 152, 864, 760))
        img.paste(qr.resize((QR_SIZE, QR_SIZE), Image.LANCZOS), (qx, qy))
    except Exception as e:
        print('[WARN] QR 缺失或加载失败（%s），已跳过' % e)
    f_qr = fnt('Sans', 18)
    lab = '↑ 扫码关注'
    lw = d.textbbox((0, 0), lab, font=f_qr)[2]
    d.text((qzx + (qzw - lw) // 2, qy + QR_SIZE + 14), lab, font=f_qr, fill=RED)

    img.save(out_path)
    print(out_path)
    return out_path


def make_follow_cover(out_path):
    """首图·关注引导：文首横幅（1080x216），品牌名 + 英文 + 关注 CTA + slogan。"""
    canvas.ensure_pillow()
    from PIL import Image, ImageDraw
    W, H = 1080, 216
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 6, W, H], fill=RED)  # 底部品牌红条

    logo = render_logo(LOGO_SIZE_A, LOGO_A, RED)
    lx, ly = 56, (H - logo.height) // 2 - 16
    img.paste(logo, (lx, ly), logo)
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = fnt('Sans', 14)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), EN, font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), EN, font=f_en, fill=GREY, anchor='lt')

    # 右侧：关注 CTA + slogan（右对齐）
    f_cta = fnt('Sans', 30)
    cta = '点击上方蓝字 · 关注不迷路'
    cw = d.textbbox((0, 0), cta, font=f_cta)[2]
    d.text((W - 56 - cw, 62), cta, font=f_cta, fill=INK)
    f_slog = fnt('Sans', 18)
    sw = d.textbbox((0, 0), SLOGAN, font=f_slog)[2]
    d.text((W - 56 - sw, 118), SLOGAN, font=f_slog, fill=GREY)

    img.save(out_path)
    print(out_path)
    return out_path


def make_preview(out_path):
    """品牌名方案预览图（450x200）。"""
    canvas.ensure_pillow()
    from PIL import Image, ImageDraw
    W, H = 450, 200
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 8, H], fill=RED)

    lx, ly = 28, 16
    _brand_block(img, d, 26, lx, ly, en_size=11)

    d.text((lx, ly + 78), '点右上角 · 关注不迷路', font=fnt('Sans', 18), fill=INK)

    # 浅灰分隔线 + slogan
    d.rectangle([lx, 160, W - 28, 161], fill=(225, 225, 225))
    d.text((lx, H - 26), SLOGAN, font=fnt('Sans', 12), fill=GREY)

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
    # v3.3.0 无参数即渲染；v4 契约要求无参数 → exit 2，渲染需显式 --all
    import argparse
    ap = argparse.ArgumentParser(
        prog='brand-font-schemes.py',
        description='品牌字体方案：生成品牌资产图（--all）或被 import 复用')
    ap.add_argument('--all', action='store_true',
                    help='生成 4 张品牌资产图（v3.3.0 默认行为）')
    ap.add_argument('--out-dir', default=os.path.join(HERE, 'assets', 'out'),
                    help='输出目录')
    ap.add_argument('--next-title', default='Prompt 模板配方',
                    help='尾图预告版的下一篇标题')
    a = ap.parse_args()
    if not a.all:
        ap.print_usage(sys.stderr)
        print('brand-font-schemes.py: 需要 --all 才生成图片（无参数时 exit 2）。',
              file=sys.stderr)
        sys.exit(2)
    os.makedirs(a.out_dir, exist_ok=True)
    make_tail(os.path.join(a.out_dir, '尾图-v4.png'))
    make_tail(os.path.join(a.out_dir, '尾图-v4-预告.png'), next_title=a.next_title)
    make_follow_cover(os.path.join(a.out_dir, '首图-关注引导.png'))
    make_preview(os.path.join(a.out_dir, '品牌名-方案A-定稿.png'))
