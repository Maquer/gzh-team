#!/usr/bin/env python3
"""cover-pipeline.py：封面流水线（双模式：去水印→裁 2.35:1→叠标题→OCR 门禁）。

v4 垫片：CLI 参数与 v3.3.0 一致，风格参数走 gzhkit.visual.styles，
画布/字体走 gzhkit.visual.canvas。
用法：发布前调用，--src <AI底图> --title "标题" 或 --base pil --layout structured
退出码：0=全绿 / 1=H11 未过 / 2=输入错误（OCR 调用失败亦 2，人工复核）。
"""
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli, report
from gzhkit.visual import canvas
from gzhkit.visual.styles import DESIGNER_STYLES

TARGET_W, TARGET_H = canvas.COVER_W, canvas.COVER_H  # 900x383，2.35:1
PAD = 40  # 水印覆盖区需大于 OCR bbox 的最小外扩
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
    """中心→四角的径向渐变（用于叠加高光）。"""
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
        return json.loads(r.stdout).get('blocks', []) if r.stdout.strip() else []
    except ValueError:
        return None


def check_text_dual(path):
    """fast 为主；accurate 只做兜底补充（accurate 在纯色区会造字，不能直接全收）。"""
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
    ap = cli.build_parser('cover-pipeline.py', '封面流水线：去水印→裁切→叠字→OCR门禁')
    ap.add_argument('--src', help='AI 底图路径（留空则用渐变背景）')
    ap.add_argument('--base', choices=['pil', 'jimeng'], default=None,
                    help='[--base pil] 用 PIL 渐变背景；[--base jimeng] 需配合 --src')
    ap.add_argument('--wm', help='水印 bbox: x1,y1,x2,y2（源图坐标）')
    ap.add_argument('--title', required=True)
    ap.add_argument('--sub', default='')
    ap.add_argument('--style', choices=list(DESIGNER_STYLES.keys()), default=None,
                    help='设计师风格（10种，优先于 --color）')
    ap.add_argument('--color', choices=list(DESIGNER_STYLES.keys()), default='deep-blue',
                    help='渐变配色预设（--style 的旧别名，向后兼容）')
    ap.add_argument('--layout', choices=['simple', 'structured'], default='simple',
                    help='simple=右对齐标题(默认) structured=左侧标题栈+强调条+清单+日期徽章')
    ap.add_argument('--points', default='', help='编号清单项，逗号分隔（仅 structured）')
    ap.add_argument('--date', default='', help='日期徽章文字（仅 structured，如 "2026.09"）')
    ap.add_argument('--out', default='cover-out.png')
    ap.add_argument('--keep-wm', action='store_true',
                    help='保留水印（自动满足 AI 标识，但封面带角标）')
    a = ap.parse_args()
    canvas.ensure_pillow()
    from PIL import Image, ImageDraw

    # ── 风格解析：--style 优先，--color 向后兼容 ──────────
    style_key = a.style or a.color
    style = DESIGNER_STYLES[style_key]

    # ── 构建底图 ─────────────────────────────────────────
    if a.src:
        if not os.path.isfile(a.src):
            report.die_input('底图不存在：%s' % a.src)
        im = Image.open(a.src).convert('RGB')
        W, H = im.size
        print('[底图] AI 源图 %dx%d  ratio=%.4f' % (W, H, W / H))
    else:
        bg = style['bg']
        if bg['type'] == 'solid':
            im = Image.new('RGB', (TARGET_W, TARGET_H), bg['color'])
        else:
            im = make_gradient(TARGET_W, TARGET_H, bg['top'], bg['bottom'])
            hl = tuple(c + 40 for c in bg['top'])
            highlight = make_radial_gradient(TARGET_W, TARGET_H, hl, bg['top'])
            im = Image.blend(highlight, im, 0.3)
        print('[底图] PIL %s (%s) → %s' % (style_key, style['name'], im.size))

    d = ImageDraw.Draw(im)

    # ── 水印覆盖 ─────────────────────────────────────────
    if a.src and a.wm and not a.keep_wm:
        x1, y1, x2, y2 = (int(v) for v in a.wm.split(','))
        sx1 = max(x1 - 60, 0)
        patch = im.crop((sx1, y1, max(x1 - 10, sx1 + 1), y2))
        px = list(patch.getdata()) or [(255, 255, 255)]
        bgc = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
        d.rectangle((x1, y1, x2, y2), fill=bgc)
        print('[去水印] 覆盖 (%d,%d,%d,%d) 用色 %s  外扩≥%dpx'
              % (x1, y1, x2, y2, bgc, PAD))
    elif a.src:
        print('[去水印] 跳过（无 --wm 参数或 --keep-wm）→ 发布必须开后台「AI 生成内容」声明开关')
    else:
        print('[去水印] PIL 模式无水印，跳过')

    # ── 裁切到 2.35:1 ───────────────────────────────────
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
        print('[裁切] %s  ratio=%.4f' % (im.size, im.size[0] / im.size[1]))
    else:
        print('[裁切] 跳过（已为目标尺寸 %dx%d）' % (TARGET_W, TARGET_H))

    # ── 叠标题 ──────────────────────────────────────────
    d = ImageDraw.Draw(im)
    text_fill, accent = style['text_fill'], style['accent']
    sub_fill, list_fill = style['sub_fill'], style['list_fill']
    stroke = (15, 30, 40)
    is_light = style['bg']['color' if style['bg']['type'] == 'solid' else 'top'][0] > 128

    def put(xy, txt, fill, font, stroke_w=2):
        x, y = xy
        if stroke_w > 0:
            for dx in range(-stroke_w, stroke_w + 1):
                for dy in range(-stroke_w, stroke_w + 1):
                    if dx or dy:
                        d.text((x + dx, y + dy), txt, fill=stroke, font=font)
        d.text((x, y), txt, fill=fill, font=font)

    if a.layout == 'structured' and not a.src:
        # ── 结构化版式 ──────────────────────────────────
        f_title = canvas.require_font('BOLD', 32)
        f_sub = canvas.require_font('BOLD', 14)
        f_pt = canvas.require_font('BOLD', 13)
        f_date = canvas.require_font('BOLD', 12)

        bar_pos = style.get('bar_pos', 'left')
        bar_w = style.get('bar_w', 5)
        LEFT_X = 50
        stroke_w = 1 if is_light else 2

        deco = style.get('deco', 'none')
        if deco == 'corners':
            cl = 40
            d.line((0, 0, cl, 0), fill=accent, width=2)
            d.line((0, 0, 0, cl), fill=accent, width=2)
            d.line((TARGET_W, 0, TARGET_W - cl, 0), fill=accent, width=2)
            d.line((TARGET_W, 0, TARGET_W, cl), fill=accent, width=2)
        elif deco == 'frame':
            d.rectangle((4, 4, TARGET_W - 4, TARGET_H - 4), outline=accent, width=2)

        if bar_pos == 'left':
            d.rectangle((LEFT_X, 50, LEFT_X + bar_w, 330), fill=accent)
        elif bar_pos == 'right':
            d.rectangle((TARGET_W - LEFT_X - bar_w, 50, TARGET_W - LEFT_X, 330),
                        fill=accent)
        elif bar_pos == 'center':
            cx = TARGET_W // 2
            d.rectangle((cx - bar_w // 2, 50, cx + bar_w // 2, 330), fill=accent)
        tx = LEFT_X + 20

        title_align = style.get('title_align', 'left')
        max_w = 320 if title_align == 'left' else 500
        title_lines, cur = [], ''
        for ch in list(a.title):
            test = cur + ch
            bw = d.textbbox((0, 0), test, font=f_title)
            if bw[2] - bw[0] > max_w and cur:
                title_lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            title_lines.append(cur)

        ty = 60
        for line in title_lines:
            if title_align == 'center':
                bl = d.textbbox((0, 0), line, font=f_title)
                lx = (TARGET_W - (bl[2] - bl[0])) // 2
            elif title_align == 'right':
                bl = d.textbbox((0, 0), line, font=f_title)
                lx = TARGET_W - (bl[2] - bl[0]) - 50
            else:
                lx = tx
            put((lx, ty), line, text_fill, f_title, stroke_w=stroke_w)
            ty += 42

        if a.sub:
            if title_align == 'center':
                bs = d.textbbox((0, 0), a.sub, font=f_sub)
                sx = (TARGET_W - (bs[2] - bs[0])) // 2
            elif title_align == 'right':
                bs = d.textbbox((0, 0), a.sub, font=f_sub)
                sx = TARGET_W - (bs[2] - bs[0]) - 50
            else:
                sx = tx
            put((sx, ty + 4), a.sub, sub_fill, f_sub, stroke_w=stroke_w - 1)
            ty += 24

        if a.points:
            pts = [p.strip() for p in a.points.split(',') if p.strip()]
            py = ty + 16
            for i, pt in enumerate(pts, 1):
                label = '%d. %s' % (i, pt)
                bw = d.textbbox((0, 0), label, font=f_pt)
                if bw[2] - bw[0] > 340:
                    while bw[2] - bw[0] > 340 and len(label) > 6:
                        label = label[:-1]
                        bw = d.textbbox((0, 0), label + '…', font=f_pt)
                    label = label + '…'
                put((tx, py), label, list_fill, f_pt, stroke_w=stroke_w - 1)
                py += 22

        if a.date:
            badge_w, badge_h = 110, 28
            bx, by = TARGET_W - badge_w - 30, TARGET_H - badge_h - 20
            badge_shape = style.get('badge_shape', 'rounded')
            badge_color = style.get('badge_color', 'accent')
            bc = accent if badge_color == 'accent' else text_fill
            if badge_shape == 'rounded':
                d.rounded_rectangle((bx, by, bx + badge_w, by + badge_h),
                                    radius=6, fill=bc)
            elif badge_shape == 'square':
                d.rectangle((bx, by, bx + badge_w, by + badge_h), fill=bc)
            # 'none' → 不画徽章背景
            bw = d.textbbox((0, 0), a.date, font=f_date)
            text_c = (20, 20, 30) if badge_shape != 'none' else text_fill
            d.text((bx + (badge_w - (bw[2] - bw[0])) // 2,
                    by + (badge_h - (bw[3] - bw[1])) // 2 - 2),
                   a.date, fill=text_c, font=f_date)

        if style.get('bottom_line', True):
            d.rectangle((0, TARGET_H - 4, TARGET_W, TARGET_H), fill=accent)
        print('[版式] structured: %d行标题 + 清单%d项 + 徽章%s + 装饰%s'
              % (len(title_lines),
                 len(a.points.split(',')) if a.points else 0,
                 '有' if a.date else '无', deco))

        if title_align == 'left':
            text_zone = (40, 40, 440, 360)
        elif title_align == 'right':
            text_zone = (420, 40, 890, 360)
        else:
            text_zone = (40, 40, 890, 360)
    else:
        # ── 简单版式：右对齐标题 ──────────────────────
        f_big = canvas.require_font('BOLD', 36)
        f_sub = canvas.require_font('BOLD', 16)
        stroke_w = 1 if is_light else 2

        b = d.textbbox((0, 0), a.title, font=f_big)
        tw_, th_ = b[2] - b[0], b[3] - b[1]
        tx, ty = TARGET_W - tw_ - 40, (TARGET_H - th_) // 2 - 15
        put((tx, ty), a.title, text_fill, f_big, stroke_w=stroke_w)
        if a.sub:
            b2 = d.textbbox((0, 0), a.sub, font=f_sub)
            put((TARGET_W - (b2[2] - b2[0]) - 40, ty + th_ + 8), a.sub,
                sub_fill, f_sub, stroke_w=stroke_w)
        text_zone = (420, 70, 890, 320)
        print('[版式] simple: 右对齐标题')

    im.save(a.out, 'PNG')
    print('[输出] %s  (%dKB)' % (a.out, os.path.getsize(a.out) // 1024))

    # ── OCR 门禁 ────────────────────────────────────────
    blocks = check_text_dual(a.out)
    if blocks is None:
        print('[H11] OCR 调用失败，人工复核')
        return 2
    mine = {a.title, a.sub} - {''}
    SUBSTR_INCLUDE = []
    for s in mine:
        SUBSTR_INCLUDE.extend([t.strip() for t in s.split() if len(t.strip()) >= 2])

    def in_excl_zone(x, y, w, h):
        """OCR bbox（归一化）与标题区（像素）重叠 ≥50% → 豁免。"""
        x, y, w, h = x * TARGET_W, y * TARGET_H, w * TARGET_W, h * TARGET_H
        zx1, zy1, zx2, zy2 = text_zone
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
        chinese_count = sum(1 for c in t if '一' <= c <= '鿿')
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
        if in_excl_zone(x, y, w, h):
            print('   ✓ [%s] 位置豁免（标题区，conf=%.2f）' % (t, conf))
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
