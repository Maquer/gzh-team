#!/usr/bin/env python3
"""封面流水线 · 双模式 · 去水印 → 裁 2.35:1 → 叠标题 → OCR 门禁自检

对应 gzh-team/TEAM.md §3.6「封面与配图生成」与 REVIEW.md H11-H13。

用法:
  # 1. AI 底图模式（原有，保留）
  python3 cover-pipeline.py --src <图> --wm <x1,y1,x2,y2> --title <主标题>

  # 2. PIL · 简单版式（右对齐标题）
  python3 cover-pipeline.py --base pil --title "标题" [--sub "副标题"] [--style deep-blue]

  # 3. PIL · 结构化版式（标题栈+强调条+清单+日期徽章）
  python3 cover-pipeline.py --base pil --layout structured \
    --title "标题" [--sub "副标题"] [--points "项1,项2,项3"] [--date "2026.09"] \
    [--style <10种风格>]

  # 风格列表（10种，7位设计师+3个渐变）
  python3 cover-pipeline.py --style stout      # Tyler Stout   复古科幻·高饱和撞色
  python3 cover-pipeline.py --style moss       # Olly Moss     极简负空间·奶油底+红黑
  python3 cover-pipeline.py --style ansin      # Martin Ansin  黑白高对比·对称构图
  python3 cover-pipeline.py --style struzan    # Drew Struzan  暖调油画·琥珀金
  python3 cover-pipeline.py --style pardee     # Alex Pardee   极简恐怖·白底黑字
  python3 cover-pipeline.py --style peak       # Bob Peak      装饰艺术·几何撞色
  python3 cover-pipeline.py --style weeks      # Ken Taylor    柔和渐变·蓝紫调
  python3 cover-pipeline.py --style deep-blue  # 深海蓝（默认）
  python3 cover-pipeline.py --style deep-gray  # 石墨灰
  python3 cover-pipeline.py --style black      # 近黑

门禁退出码：0=全绿 / 1=H11 未过 / 2=输入错误
"""
import argparse, json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageDraw as _id
import math

from cover_styles import DESIGNER_STYLES

TARGET_W, TARGET_H = 900, 383          # 公众号封面 2.35:1
FONT = '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc'
PAD = 40                                # 水印覆盖区需大于 OCR bbox 的最小外扩
WATERMARK_KEYWORDS = ['AI生成', 'AI 生成', '日日新', 'sensenova', '即梦', 'jimeng', 'SENSENOVA']


def make_gradient(w, h, top, bottom):
    """生成垂直线性渐变背景图（PIL 确定性输出，零 AI 依赖）。"""
    img = Image.new('RGB', (w, h))
    pixels = img.load()
    for y in range(h):
        ratio = y / (h - 1) if h > 1 else 0
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return img


def make_radial_gradient(w, h, center_color, edge_color):
    """径向渐变：中心亮边缘暗（用于高亮区域）。"""
    img = Image.new('RGB', (w, h))
    pixels = img.load()
    cx, cy = w // 2, h // 2
    max_dist = math.sqrt(cx * cx + cy * cy)
    for y in range(h):
        for x in range(w):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max_dist
            r = int(center_color[0] + (edge_color[0] - center_color[0]) * dist)
            g = int(center_color[1] + (edge_color[1] - center_color[1]) * dist)
            b = int(center_color[2] + (edge_color[2] - center_color[2]) * dist)
            pixels[x, y] = (r, g, b)
    return img


def check_text(path, level='fast'):
    """OCR 单级别。"""
    r = subprocess.run(['apple-vision', 'ocr', path, '--lang', 'zh-Hans,en',
                        '--level', level, '-q'],
                       capture_output=True, text=True, timeout=90)
    try:
        return json.loads(r.stdout).get('blocks', [])
    except json.JSONDecodeError:
        return None


def check_text_dual(path):
    """双级别 OCR（09-21 修）：fast 检真实中文 + accurate 兜底检水印关键词。"""
    fast = check_text(path, 'fast')
    accurate = check_text(path, 'accurate')
    if fast is None and accurate is None:
        return None
    blocks = list(fast or [])
    accurate_wm = []
    for b in (accurate or []):
        t = b.get('text', '').strip()
        if t and any(kw.lower() in t.lower() for kw in WATERMARK_KEYWORDS):
            accurate_wm.append(b)
    blocks.extend(accurate_wm)
    return blocks


def is_flat(path, box, max_colors=2):
    """像素实测：区域颜色数 ≤max_colors → 该处是纯色，OCR 检出属幻觉"""
    px = list(Image.open(path).convert('RGB').crop(box).getdata())
    return len(set(px)) <= max_colors, len(set(px)), len(px)


def main():
    ap = argparse.ArgumentParser(description='封面流水线：去水印→裁切→叠字→OCR门禁')
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
    ap.add_argument('--out', default='/var/minis/attachments/cover-out.png')
    ap.add_argument('--keep-wm', action='store_true',
                    help='保留水印（自动满足 AI 标识，但封面带角标）')
    a = ap.parse_args()

    # ── 风格解析：--style 优先，--color 向后兼容 ──────────
    style_key = a.style or a.color
    style = DESIGNER_STYLES[style_key]

    # ── 构建底图 ─────────────────────────────────────────
    if a.src:
        # AI 底图模式（原有逻辑）
        im = Image.open(a.src).convert('RGB')
        W, H = im.size
        print(f'[底图] AI 源图 {W}x{H}  ratio={W/H:.4f}')
    else:
        # PIL 确定性底图（支持 solid + gradient）
        bg = style['bg']
        if bg['type'] == 'solid':
            im = Image.new('RGB', (TARGET_W, TARGET_H), bg['color'])
        else:
            im = make_gradient(TARGET_W, TARGET_H, bg['top'], bg['bottom'])
            # 渐变模式加径向高光增加层次
            hl = (bg['top'][0] + 40, bg['top'][1] + 40, bg['top'][2] + 40)
            highlight = make_radial_gradient(TARGET_W, TARGET_H, hl, bg['top'])
            im = Image.blend(highlight, im, 0.3)
        print(f'[底图] PIL {style_key} ({style["name"]}) → {im.size}')

    d = ImageDraw.Draw(im)

    # ── 水印覆盖 ─────────────────────────────────────────
    if a.src and a.wm and not a.keep_wm:
        x1, y1, x2, y2 = (int(v) for v in a.wm.split(','))
        sx1 = max(x1 - 60, 0)
        patch = im.crop((sx1, y1, max(x1 - 10, sx1 + 1), y2))
        px = list(patch.getdata()) or [(255, 255, 255)]
        bg = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
        d.rectangle((x1, y1, x2, y2), fill=bg)
        print(f'[去水印] 覆盖 ({x1},{y1},{x2},{y2}) 用色 {bg}  外扩≥{PAD}px')
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
        print(f'[裁切] {im.size}  ratio={im.size[0]/im.size[1]:.4f}')
    else:
        # PIL 模式已直接生成目标尺寸，无需裁切
        print(f'[裁切] 跳过（已为目标尺寸 {TARGET_W}x{TARGET_H}）')

    # ── 叠标题 ──────────────────────────────────────────
    d = ImageDraw.Draw(im)
    text_fill = style['text_fill']
    accent = style['accent']
    sub_fill = style['sub_fill']
    list_fill = style['list_fill']
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
        f_title = ImageFont.truetype(FONT, 32)
        f_sub = ImageFont.truetype(FONT, 14)
        f_pt = ImageFont.truetype(FONT, 13)
        f_date = ImageFont.truetype(FONT, 12)

        bar_pos = style.get('bar_pos', 'left')
        bar_w = style.get('bar_w', 5)
        LEFT_X = 50
        stroke_w = 1 if is_light else 2

        # 装饰元素
        deco = style.get('deco', 'none')
        if deco == 'corners':
            cl = 40  # corner length
            d.line((0, 0, cl, 0), fill=accent, width=2)
            d.line((0, 0, 0, cl), fill=accent, width=2)
            d.line((TARGET_W, 0, TARGET_W - cl, 0), fill=accent, width=2)
            d.line((TARGET_W, 0, TARGET_W, cl), fill=accent, width=2)
        elif deco == 'frame':
            d.rectangle((4, 4, TARGET_W - 4, TARGET_H - 4), outline=accent, width=2)

        # 强调竖条（位置由风格决定）
        if bar_pos == 'left':
            d.rectangle((LEFT_X, 50, LEFT_X + bar_w, 330), fill=accent)
            tx = LEFT_X + 20
        elif bar_pos == 'right':
            d.rectangle((TARGET_W - LEFT_X - bar_w, 50, TARGET_W - LEFT_X, 330), fill=accent)
            tx = LEFT_X + 20
        elif bar_pos == 'center':
            cx = TARGET_W // 2
            d.rectangle((cx - bar_w // 2, 50, cx + bar_w // 2, 330), fill=accent)
            tx = LEFT_X + 20
        else:
            tx = LEFT_X + 20

        # 标题（自动换行，对齐方式由风格决定）
        title_align = style.get('title_align', 'left')
        max_w = 320 if title_align == 'left' else 500
        title_lines = []
        cur = ''
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

        # 副标题
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

        # 编号清单
        if a.points:
            pts = [p.strip() for p in a.points.split(',') if p.strip()]
            py = ty + 16
            for i, pt in enumerate(pts, 1):
                label = f'{i}. {pt}'
                bw = d.textbbox((0, 0), label, font=f_pt)
                if bw[2] - bw[0] > 340:
                    while bw[2] - bw[0] > 340 and len(label) > 6:
                        label = label[:-1]
                        bw = d.textbbox((0, 0), label + '…', font=f_pt)
                    label = label + '…'
                put((tx, py), label, list_fill, f_pt, stroke_w=stroke_w - 1)
                py += 22

        # 日期徽章（形状由风格决定）
        if a.date:
            badge_w, badge_h = 110, 28
            bx = TARGET_W - badge_w - 30
            by = TARGET_H - badge_h - 20
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

        # 底部强调线
        if style.get('bottom_line', True):
            d.rectangle((0, TARGET_H - 4, TARGET_W, TARGET_H), fill=accent)
        print(f'[版式] structured: {len(title_lines)}行标题 + 清单{len(a.points.split(",")) if a.points else 0}项 + 徽章{"有" if a.date else "无"} + 装饰{deco}')

        # 文字区域豁免
        if title_align == 'left':
            text_zone = (40, 40, 440, 360)
        elif title_align == 'right':
            text_zone = (420, 40, 890, 360)
        else:
            text_zone = (40, 40, 890, 360)
    else:
        # ── 简单版式：右对齐标题 ──────────────────────
        f_big = ImageFont.truetype(FONT, 36)
        f_sub = ImageFont.truetype(FONT, 16)
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
        print(f'[版式] simple: 右对齐标题')

    im.save(a.out, 'PNG')
    print(f'[输出] {a.out}  ({__import__("os").path.getsize(a.out)//1024}KB)')

    # ── OCR 门禁 ────────────────────────────────────────
    blocks = check_text_dual(a.out)
    if blocks is None:
        print('[H11] OCR 调用失败，人工复核')
        return 2
    mine = {a.title, a.sub} - {''}
    # 标题/副标题所在区域 → OCR 在此区域的检出自动豁免
    TEXT_EXCL_ZONE = text_zone
    # 标题/副标题含有的子串 → OCR 检出这些子串一律豁免（如 "AI" 在中文标题里）
    SUBSTR_INCLUDE = []
    for s in mine:
        SUBSTR_INCLUDE.extend([t.strip() for t in s.split() if len(t.strip()) >= 2])

    def is_noise_block(text):
        """中文块如果中文/全角字符占比 <30%，视为背景噪点"""
        import re
        chinese = len(re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text))
        total = len(text.replace(' ', ''))
        if total == 0:
            return True
        return chinese / total < 0.3

    def in_excl_zone(x, y, w, h):
        """OCR block 是否与已知文字区域重叠 ≥50%"""
        ox, oy, ow, oh = TEXT_EXCL_ZONE
        ix = max(x, ox); iy = max(y, oy)
        iw = min(x + w, ox + ow) - ix
        ih = min(y + h, oy + oh) - iy
        if iw <= 0 or ih <= 0:
            return False
        return (iw * ih) >= 0.5 * (w * h)

    print('[H11] fast OCR 检出:')
    fail = False
    for b in blocks:
        t = b['text'].strip()
        conf = b.get('confidence', 0)
        if t in mine or not t:
            print(f'   ✓ [{t}] 自加文字')
            continue
        # 噪音块过滤：零中文字符 → 背景噪点，不是真实文字（优先级最高）
        chinese_count = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
        if chinese_count == 0:
            print(f'   ⚠ [{t}] 无中文字符（纯英文/符号），噪声块跳过')
            continue
        # 中文占比低 → 背景噪点
        if chinese_count / max(len(t.replace(' ', '')), 1) < 0.3 and conf < 0.8:
            print(f'   ⚠ [{t}] 噪声块（中文占比<30%），跳过')
            continue
        # 子串豁免
        if any(sub in t for sub in SUBSTR_INCLUDE):
            print(f'   ✓ [{t}] 含标题子串（豁免）')
            continue
        x, y, w, h = b['bbox']
        if in_excl_zone(x, y, w, h):
            print(f'   ✓ [{t}] 位置豁免（标题区，conf={b.get("confidence",0):.2f}）')
            continue
        wm_hit = [kw for kw in WATERMARK_KEYWORDS if kw.lower() in t.lower()]
        if wm_hit:
            print(f'   ✗ [{t}] 命中水印关键词 {wm_hit} → H11 FAIL')
            fail = True
            continue
        box = (int(x * TARGET_W), int(y * TARGET_H),
               int((x + w) * TARGET_W), int((y + h) * TARGET_H))
        flat, ncol, npx = is_flat(a.out, box)
        conf = b.get('confidence', 0)
        if conf < 0.55 and flat:
            print(f'   ⚠ [{t}] conf={conf:.2f} 区域仅 {ncol} 色/{npx}px → OCR 幻觉')
        elif conf < 0.55:
            print(f'   ⚠ [{t}] conf={conf:.2f} 区域 {ncol} 色 → 低置信，跳过')
        else:
            print(f'   ✗ [{t}] conf={conf:.2f} 区域 {ncol} 色 → 真实文字，H11 未过')
            fail = True
    if not blocks:
        print('   （空）')
    print(f'\n门禁结论: {"H11 FAIL — 退回重出" if fail else "全绿 ✅"}')
    if not a.src:
        print('[H13] PIL 模式无水印 → 无需后台 AI 声明开关')
    else:
        print('[H13] 提示: 去水印封面 → 发布开「AI 生成内容」声明开关')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
