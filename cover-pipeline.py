#!/usr/bin/env python3
"""cover-pipeline.py：封面流水线（单一布局版）。

单一布局：锚点大字居中 + 左上品牌区 + 左下 slogan + 右下日期
输出：900×383 PNG，自动 OCR 门禁（H11）
用法：python3 cover-pipeline.py --title "标题" --anchor "锚点词" [--style deep-blue] [--date 2026.10]
退出码：0=全绿 / 1=H11 未过 / 2=输入错误（OCR 调用失败亦 2）
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli, report
from gzhkit.visual import canvas
from gzhkit.visual.styles import DESIGNER_STYLES

TARGET_W, TARGET_H = canvas.COVER_W, canvas.COVER_H  # 900x383
PAD = 40
WATERMARK_KEYWORDS = ['AI生成', 'AI 生成', '日日新', 'sensenova', '即梦', 'jimeng', 'SENSENOVA']


def make_gradient(w, h, top, bottom):
    """自上而下的线性渐变。"""
    canvas.ensure_pillow()
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / max(h - 1, 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return img


def make_radial_gradient(w, h, center_color, edge_color):
    """中心→四角的径向渐变。"""
    canvas.ensure_pillow()
    from PIL import Image
    img = Image.new('RGB', (w, h))
    px = img.load()
    cx, cy = w // 2, h // 2
    max_dist = math.sqrt(cx * cx + cy * cy)
    for y in range(h):
        for x in range(w):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max_dist
            px[x, y] = tuple(
                int(center_color[i] + (edge_color[i] - center_color[i]) * dist)
                for i in range(3))
    return img


def check_text(path, level='fast'):
    """调用 apple-vision OCR，返回 blocks 列表；调用失败返回 None。"""
    try:
        r = subprocess.run(
            ['apple-vision', 'ocr', path, '--lang', 'zh-Hans,en',
             '--level', level, '-q'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        import json
        return json.loads(r.stdout).get('blocks', []) if r.stdout.strip() else []
    except ValueError:
        return None


def check_text_dual(path):
    """fast 为主；accurate 只做兜底补充。"""
    fast = check_text(path, 'fast')
    accurate = check_text(path, 'accurate')
    if fast is None and accurate is None:
        return None
    blocks = list(fast or [])
    seen = {b.get('text', '').strip() for b in blocks}
    for b in (accurate or []):
        t = b.get('text', '').strip()
        if t and t not in seen and any(kw.lower() in t.lower() for kw in WATERMARK_KEYWORDS):
            blocks.append(b)
    return blocks


def is_flat(path, box, max_colors=2):
    canvas.ensure_pillow()
    from PIL import Image
    px = list(Image.open(path).convert('RGB').crop(box).getdata())
    return len(set(px)) <= max_colors, len(set(px)), len(px)


def main():
    ap = cli.build_parser('cover-pipeline.py',
                          '封面流水线：单一布局（锚点居中+品牌左上+slogan左下+日期右下）')
    ap.add_argument('--title', required=True, help='主标题')
    ap.add_argument('--anchor', required=True, help='锚点关键词（居中放大显示）')
    ap.add_argument('--style', choices=list(DESIGNER_STYLES.keys()), default='deep-blue',
                    help='设计师风格（10种，默认 deep-blue）')
    ap.add_argument('--date', default='', help='日期文字（默认当月 YYYY.MM）')
    ap.add_argument('--src', help='AI 底图路径（留空则用渐变背景）')
    ap.add_argument('--wm', help='水印 bbox: x1,y1,x2,y2')
    ap.add_argument('--out', default='cover-out.png')
    ap.add_argument('--keep-wm', action='store_true', help='保留水印')
    a = ap.parse_args()

    canvas.ensure_pillow()
    from PIL import Image, ImageDraw
    import datetime

    # ── 风格解析 ────────────────────────────────────────
    style = DESIGNER_STYLES[a.style]

    # ── 构建底图 ─────────────────────────────────────────
    if a.src:
        if not os.path.isfile(a.src):
            report.die_input('底图不存在：%s' % a.src)
        im = Image.open(a.src).convert('RGB')
        W, H = im.size
        print('[底图] AI 源图 %dx%d ratio=%.4f' % (W, H, W / H))
    else:
        bg = style['bg']
        if bg['type'] == 'solid':
            im = Image.new('RGB', (TARGET_W, TARGET_H), bg['color'])
        else:
            im = make_gradient(TARGET_W, TARGET_H, bg['top'], bg['bottom'])
            hl = tuple(c + 40 for c in bg['top'])
            highlight = make_radial_gradient(TARGET_W, TARGET_H, hl, bg['top'])
            im = Image.blend(highlight, im, 0.3)
        print('[底图] PIL %s (%s) → %s' % (a.style, style['name'], im.size))

    d = ImageDraw.Draw(im)

    # ── 水印覆盖 ─────────────────────────────────────────
    if a.src and a.wm and not a.keep_wm:
        x1, y1, x2, y2 = (int(v) for v in a.wm.split(','))
        sx1 = max(x1 - 60, 0)
        patch = im.crop((sx1, y1, max(x1 - 10, sx1 + 1), y2))
        px = list(patch.getdata()) or [(255, 255, 255)]
        bgc = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
        d.rectangle((x1, y1, x2, y2), fill=bgc)
        print('[去水印] 覆盖 (%d,%d,%d,%d) 用色 %s' % (x1, y1, x2, y2, bgc))
    elif a.src:
        print('[去水印] 跳过 → 发布必须开「AI 生成内容」声明开关')
    else:
        print('[去水印] PIL 模式无水印，跳过')

    # ── 裁切到目标尺寸 ───────────────────────────────────
    if a.src:
        W, H = im.size
        th = int(W * TARGET_H / TARGET_W)
        if th > H:
            tw = int(H * TARGET_W / TARGET_H)
            im = im.crop(((W - tw) // 2, 0, (W - tw) // 2 + tw, H))
        else:
            top = (H - th) // 2
            im = im.crop((0, top, W, top + th))
        im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
        print('[裁切] %s ratio=%.4f' % (im.size, im.size[0] / im.size[1]))
    else:
        print('[裁切] 跳过（已为目标尺寸 %dx%d）' % (TARGET_W, TARGET_H))

    d = ImageDraw.Draw(im)
    RED = canvas.RED
    GREY = canvas.GREY
    INK = canvas.INK
    HAIRLINE = canvas.HAIRLINE
    LIGHT_RED = canvas.LIGHT_RED
    BRAND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'brand')

    # ── 单一布局渲染 ──────────────────────────────────────
    # 1. 同心圆装饰（锚点大字背后的浅灰环，对齐基准封面）
    if style.get('deco') == 'rings':
        RCX, RCY = TARGET_W // 2 + 35, TARGET_H // 2 + 12
        for rr in (112, 148, 184):
            d.ellipse([RCX - rr, RCY - rr, RCX + rr, RCY + rr],
                      outline=(229, 229, 229), width=1)
        # 圆环右上方的稀疏点阵
        for dx, dy, rad in ((118, -58, 2), (142, -26, 3), (150, 8, 2),
                            (136, -84, 2), (168, -58, 2)):
            d.ellipse([RCX + dx - rad, RCY + dy - rad,
                      RCX + dx + rad, RCY + dy + rad],
                      fill=(217, 217, 217))

    # 2. 左上品牌区
    canvas.draw_brand_block(im, d, brand_dir=BRAND_DIR)

    # 2. 锚点大字居中
    anchor_text = a.anchor
    _font_size = 72 if len(anchor_text) <= 4 else 60
    f_anchor = canvas.require_font('BOLD', _font_size)
    abbox = d.textbbox((0, 0), anchor_text, font=f_anchor)
    aw = abbox[2] - abbox[0]
    ah = abbox[3] - abbox[1]
    ax = (TARGET_W - aw) // 2
    ay = (TARGET_H - ah) // 2 - 10
    # 纯色填充（基准封面锚点无描边，实测深红像素比 0.000）
    d.text((ax, ay), anchor_text, fill=style['accent'], font=f_anchor)

    # 3. 主标题（锚点上方小字）
    if a.title != anchor_text:
        f_title = canvas.require_font('NORMAL', 16)
        tbbox = d.textbbox((0, 0), a.title, font=f_title)
        tw_ = tbbox[2] - tbbox[0]
        tx_ = (TARGET_W - tw_) // 2
        ty_ = ay - 36
        if ty_ < 90:
            ty_ = ay + ah + 16
        d.text((tx_, ty_), a.title, fill=GREY, font=f_title)

    # 4. 底部 Slogan（左下）
    d.rectangle([56, TARGET_H - 74, TARGET_W - 56, TARGET_H - 73], fill=HAIRLINE)
    f_slogan = canvas.require_font('NORMAL', 16)
    d.text((56, TARGET_H - 56), canvas.SLOGAN, font=f_slogan, fill=GREY)

    # 5. 日期徽章（右下）
    date_str = a.date or datetime.datetime.now().strftime('%Y.%m')
    f_date = canvas.require_font('BOLD', 17)
    dw = d.textbbox((0, 0), date_str, font=f_date)[2]
    dx = TARGET_W - 56 - dw - 28
    d.rounded_rectangle([dx, TARGET_H - 62, TARGET_W - 56, TARGET_H - 30],
                        radius=6, outline=RED, width=2)
    d.text((dx + 14, TARGET_H - 55), date_str, font=f_date, fill=RED)

    # 6. 左侧品牌红条（基准版式：整条边，宽度取风格 bar_w）
    bw = int(style.get('bar_w', 0))
    if bw > 0:
        d.rectangle([0, 0, bw, TARGET_H], fill=RED)

    im.save(a.out, 'PNG')
    print('[输出] %s  (%dKB)' % (a.out, os.path.getsize(a.out) // 1024))

    # ── OCR 门禁 ────────────────────────────────────────
    blocks = check_text_dual(a.out)
    if blocks is None:
        print('[H11] OCR 调用失败，人工复核')
        return 2

    mine = {a.title, a.anchor} - {''}
    SUBSTR_INCLUDE = []
    for s in mine:
        SUBSTR_INCLUDE.extend([t.strip() for t in s.split() if len(t.strip()) >= 2])

    def in_text_zone(x, y, w, h):
        """锚点大字区域豁免（约画面中部 ±80px）。"""
        zx1, zy1, zx2, zy2 = TARGET_W // 2 - 200, 80, TARGET_W // 2 + 200, TARGET_H - 80
        x, y, w, h = x * TARGET_W, y * TARGET_H, w * TARGET_W, h * TARGET_H
        iw = min(x + w, zx2) - max(x, zx1)
        ih = min(y + h, zy2) - max(y, zy1)
        if iw <= 0 or ih <= 0:
            return False
        return (iw * ih) >= 0.5 * max(w * h, 1e-9)

    print('[H11] fast OCR 检出:')
    fail = False
    for b in blocks:
        t = b['text'].strip()
        conf = b.get('confidence', 0)
        if t in mine or not t:
            print('   ✓ [%s] 自加文字' % t)
            continue
        chinese_count = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
        if chinese_count == 0:
            print('   ⚠ [%s] 无中文字符（纯英文/符号），噪声块跳过' % t)
            continue
        if chinese_count / max(len(t.replace(' ', '')), 1) < 0.3 and conf < 0.8:
            print('   ⚠ [%s] 噪声块（中文占比<30%），跳过' % t)
            continue
        if any(sub in t for sub in SUBSTR_INCLUDE):
            print('   ✓ [%s] 含标题子串（豁免）' % t)
            continue
        x, y, w, h = b['bbox']
        if in_text_zone(x, y, w, h):
            print('   ✓ [%s] 位置豁免（锚点区，conf=%.2f）' % (t, conf))
            continue
        wm_hit = [kw for kw in WATERMARK_KEYWORDS if kw.lower() in t.lower()]
        if wm_hit:
            print('   ✗ [%s] 命中水印关键词 %s → H11 FAIL' % (t, wm_hit))
            fail = True
            continue
        box = (int(x * TARGET_W), int(y * TARGET_H),
               int((x + w) * TARGET_W), int((y + h) * TARGET_H))
        flat, ncol, npx = is_flat(a.out, box)
        if conf < 0.55 and flat:
            print('   ⚠ [%s] conf=%.2f 区域仅 %d 色/%dpx → OCR 幻觉' % (t, conf, ncol, npx))
        elif conf < 0.55:
            print('   ⚠ [%s] conf=%.2f 区域 %d 色 → 低置信，跳过' % (t, conf, ncol))
        else:
            print('   ✗ [%s] conf=%.2f 区域 %d 色 → 真实文字，H11 未过' % (t, conf, ncol))
            fail = True
    if not blocks:
        print('   （空）')
    print('\n门禁结论: %s' % ('H11 FAIL — 退回重出' if fail else '全绿 ✅'))
    if not a.src:
        print('[H13] PIL 模式无水印 → 无需后台 AI 声明开关')
    else:
        print('[H13] 提示: 去水印封面 → 发布开「AI 生成内容」声明开关')
    return 1 if fail else 0


if __name__ == '__main__':
    cli.run_main(main)
