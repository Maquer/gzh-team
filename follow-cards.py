#!/usr/bin/env python3
"""公众号关注首图 + 尾图生成器 · 确定性 PIL，零 AI 依赖

首图 = 文章开头关注提醒卡（1080x216 banner，无二维码，防读完忘了关注）
尾图 = 文末关注引导卡（1080x1350 portrait，含二维码 + 价值点 + 往期）

品牌视觉与 wanganzhou-cover-v4 统一：深蓝渐变底 + 青色强调。

用法:
  python3 follow-cards.py                    # 两张都出（二维码占位）
  python3 follow-cards.py --qr qr.png        # 指定公众号二维码
  python3 follow-cards.py --name 账号名 --slogan "一句话"
  python3 follow-cards.py --points "点1,点2,点3" --past "往期1|往期2|往期3"
  python3 follow-cards.py --only head        # 只出首图
  python3 follow-cards.py --check            # OCR 门禁校验

设计边界（勿误用）:
  - 无 --qr 时二维码区域是占位框，必须替换后才能用于正式发布。
  - 全部文字为程序化绘制，不写进 AI prompt，零 AI 味/零错字风险。
  - 尺寸固定为公众号阅读体验实测值，勿随意改动。
"""
import argparse, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))


def make_gradient(w, h, top, bottom):
    """垂直线性渐变（PIL 确定性，零 AI 依赖）。与封面流水线同实现。"""
    img = Image.new('RGB', (w, h))
    px = img.load()
    for y in range(h):
        r = y / (h - 1) if h > 1 else 0
        c = (int(top[0] + (bottom[0] - top[0]) * r),
             int(top[1] + (bottom[1] - top[1]) * r),
             int(top[2] + (bottom[2] - top[2]) * r))
        for x in range(w):
            px[x, y] = c
    return img

# ── 品牌常量（账号级，跨文章统一）──────────────────────
ACCOUNT = '弎水野记'
SLOGAN = '野路实测，笔记为证：留下能用的'

BG_TOP = (6, 22, 48)
BG_BOTTOM = (14, 58, 108)
ACCENT = (0, 201, 167)
TEXT_MAIN = (255, 255, 255)
TEXT_SUB = (168, 200, 226)
TEXT_DIM = (116, 148, 178)
BRAND_RED = (197, 59, 59)
WHITE = (255, 255, 255)

FONT_B = '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc'
FONT_R = '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc'

HEAD_W, HEAD_H = 1080, 216       # 开头提醒卡
TAIL_W, TAIL_H = 1080, 1350      # 文末引导卡
MARGIN = 72

POINTS_DEFAULT = [
    '每篇都给一个能照做的动作',
    '只写我真踩过坑的，不写官方话术',
    '每周 1-2 篇，不追热点只追变化',
]

# ── 文本度量与排版工具 ────────────────────────────────
def f(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def tw(draw, text, font):
    """文本宽度（CJK 必须走 textbbox，len()*size 会算错）。"""
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw, text, font, max_w):
    """按宽度断行，优先在标点处断，避免切半个词。"""
    lines, cur = [], ''
    for ch in text:
        w, _ = tw(draw, cur + ch, font)
        if w > max_w and cur:
            lines.append(cur)
            cur = ch if ch not in '，。、；：,.' else ''
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def center_x(draw, text, font, cx):
    w, _ = tw(draw, text, font)
    return cx - w // 2


def bar(d, x, y, w, h, color, radius=3):
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=color)


def dashed_rect(d, box, color, width=3, dash=14, gap=9):
    """PIL 无虚线，手写：沿矩形边界按 dash/gap 交替画线段。"""
    x0, y0, x1, y1 = box
    segs = []
    for (a, b, c, dd) in ((x0, y0, x1, y0), (x1, y0, x1, y1),
                          (x1, y1, x0, y1), (x0, y1, x0, y0)):
        total = abs(c - a) + abs(dd - b)
        px, end = 0, total
        while px < end:
            q = min(px + dash, end)
            if a == c:
                t1, t2 = px / total * (dd - b), q / total * (dd - b)
                segs.append([(a, b + t1), (a, b + t2)])
            else:
                t1, t2 = px / total * (c - a), q / total * (c - a)
                segs.append([(a + t1, b), (a + t2, b)])
            px = q + gap
    for s in segs:
        d.line(s, fill=color, width=width, joint='curve')


def check_text(path):
    """OCR 门禁：调用 apple-vision 抽检渲染文字是否与预期一致。"""
    if not os.path.exists(path):
        return False, '文件不存在'
    r = subprocess.run(['apple-vision', 'ocr', '--lang', 'zh-Hans', path],
                       capture_output=True, text=True, timeout=60)
    got = (r.stdout + r.stderr).replace(' ', '')
    need = ACCOUNT.replace(' ', '')
    return (need in got), got[:200]


# ── 首图：开头关注提醒卡 ──────────────────────────────
def render_head(name, slogan, out, logo_path=None):
    img = make_gradient(HEAD_W, HEAD_H, BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)

    # ── 底部品牌红条（全宽，锚定品牌色）
    d.rectangle([0, HEAD_H - 5, HEAD_W, HEAD_H], fill=BRAND_RED)

    # ── 左侧品牌 Logo
    ls = 150
    lx = MARGIN
    ly = (HEAD_H - ls) // 2 - 2
    logo_ok = False
    if logo_path and os.path.isfile(logo_path):
        try:
            logo = Image.open(logo_path).convert('RGBA')
            logo = logo.resize((ls, ls), Image.LANCZOS)
            img.paste(logo, (lx, ly), logo)
            logo_ok = True
        except Exception as e:
            print(f'⚠️ Logo 加载失败 {e}，改用文字块')
    if not logo_ok:
        d.ellipse([lx, ly, lx+ls, ly+ls], fill=BRAND_RED)
        fn_first = f(56)
        fw, _ = tw(d, name[0], fn_first)
        d.text((lx + ls//2 - fw//2, ly + ls//2 - 38), name[0], font=fn_first, fill=WHITE)

    # ── 文本起点在 Logo 右侧
    tx = lx + ls + 24
    fn_name = f(46)
    fn_slog = f(23, bold=False)
    d.text((tx, 52), name, font=fn_name, fill=TEXT_MAIN)
    d.text((tx, 122), slogan, font=fn_slog, fill=TEXT_SUB)

    # ── 中缝分隔线（品牌红，连接左右两块）
    d.line([(586, 48), (586, 168)], fill=BRAND_RED, width=2)

    # ── 右块：关注动作指引
    fn_cta = f(32)
    fn_hint = f(22, bold=False)
    cta = '↑ 点上方公众号名 · 关注不迷路'
    cw, _ = tw(d, cta, fn_cta)
    d.text((HEAD_W - MARGIN - cw, 58), cta, font=fn_cta, fill=ACCENT)
    hint = '发一篇不错过一篇'
    hw, _ = tw(d, hint, fn_hint)
    d.text((HEAD_W - MARGIN - hw, 116), hint, font=fn_hint, fill=TEXT_DIM)

    img.save(out, 'PNG', optimize=True)
    return out


# ── 二维码区域：--qr 提供真图，否则占位框 ────────────
def draw_qr(d, box, qr_path):
    x0, y0, x1, y1 = box
    size = x1 - x0
    pad = 16
    # 白色底框（二维码识别需高对比留白）
    d.rounded_rectangle(
        [x0 - pad, y0 - pad, x1 + pad, y1 + pad],
        radius=24, fill=WHITE)

    if qr_path and os.path.isfile(qr_path):
        try:
            q = Image.open(qr_path).convert('RGB')
            q = q.resize((size, size), Image.NEAREST)  # QR 码需保锐利，不用 LANCZOS
            img = d._image
            img.paste(q, (x0, y0))
            return True
        except Exception as e:
            print(f'⚠️ 二维码加载失败 {e}，改用占位框')
            d = ImageDraw.Draw(img)

    # 无二维码：画品牌标记区（品牌红 + 2×2 字阵，与官方 logo 排法一致）
    # 这是完整模式而非占位，卡片不依赖二维码也成立
    d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=BRAND_RED)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    fs = f(76)
    # 2×2：右上「弎」左上「野」/ 右下「水」左下「记」，读作「弎水野记」
    grid = {
        '野': (cx - 42, cy - 96), '弎': (cx + 42, cy - 96),
        '记': (cx - 42, cy + 20), '水': (cx + 42, cy + 20),
    }
    for ch, (gx, gy) in grid.items():
        w, h = tw(d, ch, fs)
        d.text((gx - w // 2, gy - h // 2), ch, font=fs, fill=WHITE)
    fn_p = f(19, bold=False)
    pinyin = 'SANSHUI YEJI'
    pw, ph = tw(d, pinyin, fn_p)
    d.text((cx - pw // 2, cy + 140), pinyin, font=fn_p, fill=(232, 200, 196))
    return False


# ── 尾图：文末关注引导卡 ──────────────────────────────
def render_tail(name, slogan, points, past, qr_path, out):
    img = make_gradient(TAIL_W, TAIL_H, BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)

    # ── 头部：账号名 + slogan ──
    bar(d, 0, 0, 10, 250, ACCENT, radius=0)
    fn_name = f(64)
    fn_slog = f(28, bold=False)
    d.text((MARGIN, 86), name, font=fn_name, fill=TEXT_MAIN)
    d.text((MARGIN, 188), slogan, font=fn_slog, fill=TEXT_SUB)
    d.line([(MARGIN, 268), (TAIL_W - MARGIN, 268)], fill=(46, 88, 132), width=1)

    # ── 中部左：二维码 ──
    qr_box = (MARGIN, 320, MARGIN + 360, 320 + 360)
    has_qr = draw_qr(d, qr_box, qr_path)

    # ── 中部右：价值点（编号 + 文本，按宽度断行）──
    px = MARGIN + 360 + 68
    fn_num, fn_ptb = f(28), f(30)
    y = 330
    for i, pt in enumerate(points[:3], 1):
        num = f'{i:02d}'
        nw, _ = tw(d, num, fn_num)
        d.text((px, y), num, font=fn_num, fill=ACCENT)
        tx = px + nw + 22
        for line in wrap(d, pt, fn_ptb, TAIL_W - MARGIN - tx):
            d.text((tx, y), line, font=fn_ptb, fill=TEXT_MAIN)
            y += 44
        y += 34

    # ── CTA：长按识别二维码 / 关注提示 ──
    fn_cta = f(34)
    d.line([(MARGIN, 760), (TAIL_W - MARGIN, 760)], fill=(46, 88, 132), width=1)
    cta = f'长按识别二维码 · 关注「{name}」' if has_qr else f'关注「{name}」'
    d.text((center_x(d, cta, fn_cta, TAIL_W // 2), 810), cta,
           font=fn_cta, fill=ACCENT)
    fn_sub = f(23, bold=False)
    sub = '每篇文末都有，不用记地址'
    d.text((center_x(d, sub, fn_sub, TAIL_W // 2), 868), sub,
           font=fn_sub, fill=TEXT_DIM)

    # ── 往期推荐 ──
    if past:
        d.line([(MARGIN, 940), (TAIL_W - MARGIN, 940)], fill=(46, 88, 132), width=1)
        fn_lab = f(24, bold=False)
        d.text((MARGIN, 976), '往期，值得一读', font=fn_lab, fill=TEXT_DIM)
        fn_it = f(28, bold=False)
        iy = 1036
        for p in past[:3]:
            bw, _ = tw(d, '·', fn_it)
            d.text((MARGIN, iy), '·', font=fn_it, fill=ACCENT)
            for line in wrap(d, p, fn_it, TAIL_W - 2 * MARGIN - bw - 16):
                d.text((MARGIN + bw + 16, iy), line, font=fn_it, fill=TEXT_SUB)
                iy += 42
            iy += 12

    # ── 底部品牌条 ──
    bar(d, 0, TAIL_H - 8, TAIL_W, 8, BRAND_RED, radius=0)

    img.save(out, 'PNG', optimize=True)
    return out, has_qr


# ── CLI ────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='公众号关注首图/尾图生成器')
    ap.add_argument('--name', default=ACCOUNT, help=f'账号名（默认 {ACCOUNT}）')
    ap.add_argument('--slogan', default=SLOGAN, help='一句话定位')
    ap.add_argument('--points', default=None,
                    help='尾图价值点，逗号分隔（最多 3 条）')
    ap.add_argument('--past', default=None,
                    help='往期推荐，竖线分隔（最多 3 条）')
    ap.add_argument('--qr', default=None, help='公众号二维码图片路径')
    ap.add_argument('--logo', default=os.path.join(HERE, 'assets', 'brand', 'avatar.png'),
                    help='品牌 Logo 图片路径（默认 assets/brand/avatar.png）')
    ap.add_argument('--only', choices=['head', 'tail'], help='只出一张')
    ap.add_argument('--outdir', default=os.path.join(HERE, 'assets'))
    ap.add_argument('--check', action='store_true', help='OCR 门禁校验')
    a = ap.parse_args()

    points = [p.strip() for p in a.points.split(',') if p.strip()] if a.points else POINTS_DEFAULT
    past = [p.strip() for p in a.past.split('|') if p.strip()] if a.past else []
    os.makedirs(a.outdir, exist_ok=True)

    made, warn = [], False

    if a.only in (None, 'head'):
        p = os.path.join(a.outdir, 'follow-head.png')
        render_head(a.name, a.slogan, p, a.logo)
        made.append(p)
        print(f'[首图] {p}  ({HEAD_W}x{HEAD_H})')

    if a.only in (None, 'tail'):
        p = os.path.join(a.outdir, 'follow-tail.png')
        _, has_qr = render_tail(a.name, a.slogan, points, past, a.qr, p)
        made.append(p)
        print(f'[尾图] {p}  ({TAIL_W}x{TAIL_H})  二维码: {"✅ 已嵌入" if has_qr else "⚠️ 占位框"}')
        if not has_qr:
            warn = True

    if warn:
        print()
        print('⚠️  尾图二维码是占位框，未嵌入真实二维码。')
        print('   正式发布前请提供二维码图片：--qr /path/to/qr.png')

    if a.check:
        print()
        for p in made:
            ok, got = check_text(p)
            print(f'{"✅" if ok else "❌"} OCR {os.path.basename(p)}: 账号名{"命中" if ok else "未命中"}')

    sys.exit(1 if warn else 0)


if __name__ == '__main__':
    main()
