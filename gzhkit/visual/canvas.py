#!/usr/bin/env python3
"""gzhkit.visual.canvas: PIL 画布公共函数。

v3.x 的 cover-card / cover-brief / cover-dynamic / cover-new-style /
cover-pipeline / follow-cards / brand-font-schemes 各自重复实现的部分，
收敛到此：字体加载回退链、900×383 画布、品牌块、印章、页脚、文字排版。

字体分工（v3.2.0，原样保留）：
  - 摘要/信息承载层 → 文楷 LXGW WenKai（可读性优先）
  - 热点大字/艺术字 → 毛笔 MaShanZheng
  MaShanZheng 缺字时回退文楷（v3.3.0 cover-dynamic 既有逻辑），再退 Noto Sans CJK。

回退契约：
  - 缺 Pillow → 明错 + exit 2（不 traceback）
  - 字体链全灭 → load_font() 给 PIL 位图字体并 stderr 警告（cover-dynamic
    保留 v3.2.0「缺素材走字体渲染回退，退出码仍 0」）；require_font() 则
    明错 + exit 2（供需要真实中文字体的工具在入口处调用）
  - 缺品牌素材图（logo/印章/二维码 png）→ 程序化字体渲染回退，exit 0 可出图

公开版约束：品牌字一律用占位符，真实品牌字不得入库（见 config.BRAND_PLACEHOLDER）。
"""
import os
import sys

from .. import cli
from .. import config as C

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_OK = True
except ImportError:  # noqa: F401 - 守卫，供 ensure_pillow() 统一报错
    PIL_OK = False
    Image = ImageDraw = ImageFont = None

# ── 版式基准（v3.x 全系列通用）──────────────────────────
COVER_W, COVER_H = 900, 383          # 公众号封面 2.35:1
HEAD_W, HEAD_H = 1080, 216           # 关注首图
TAIL_W, TAIL_H = 1080, 1350          # 文末引导卡

# ── 色板 ────────────────────────────────────────────────
RED = (194, 69, 60)                  # 品牌红 #C2453C
INK = (51, 51, 51)                   # 正文墨黑
PAPER = (245, 245, 245)              # 纸面底
CREAM = (245, 242, 235)
WHITE = (255, 255, 255)
GREY = (140, 140, 140)
MID_GREY = (160, 160, 160)
DIM = (110, 110, 110)
HAIRLINE = (215, 215, 215)
LIGHT_RED = (232, 196, 192)
DOT_GREY = (232, 180, 176)

# ── 品牌占位（公开版默认；自有部署替换为真实品牌字/图）──
BRAND_NAME = C.BRAND_PLACEHOLDER     # '<YOUR_BRAND>'
BRAND_EN = C.BRAND_EN_PLACEHOLDER    # '<YOUR_BRAND_EN>'
SLOGAN = '用心实测，留下能用的'
# logo 逐字混排：前二字=文楷，后二字=毛笔（v3.2.0 字体分工）
LOGO_CHARS = [('品', 'LXGW'), ('牌', 'LXGW'), ('风', 'MSZ'), ('采', 'MSZ')]
# 2x2 程序化印章字序（右起竖读）
SEAL_CHARS = ('品', '牌', '风', '采')

# 自有部署覆盖层：gzhkit/brand_local.py（已 gitignore，不入库，见 D6 脱敏约束）。
# 缺该文件时保持占位符 —— 但 LOGO_CHARS 回退渲染的是占位字，
# 真机上 logo 图缺失会画出错误品牌名，故覆盖层存在与否都会打一行提示。
BRAND_LOCAL_LOADED = False
try:
    from .. import brand_local as _brand_local
    BRAND_NAME = getattr(_brand_local, 'BRAND_NAME', BRAND_NAME)
    BRAND_EN = getattr(_brand_local, 'BRAND_EN', BRAND_EN)
    SLOGAN = getattr(_brand_local, 'SLOGAN', SLOGAN)
    LOGO_CHARS = getattr(_brand_local, 'LOGO_CHARS', LOGO_CHARS)
    SEAL_CHARS = getattr(_brand_local, 'SEAL_CHARS', SEAL_CHARS)
    BRAND_LOCAL_LOADED = True
except ImportError:
    pass

# ── 字体回退链 ──────────────────────────────────────────
_NOTO = '/usr/share/fonts/noto/'
_FONT_FILES = {
    # 角色 → 按优先级排列的候选路径
    'BOLD':   [_NOTO + 'NotoSansCJK-Bold.ttc'],
    'NORMAL': [_NOTO + 'NotoSansCJK-Regular.ttc'],
    'SERIF':  [_NOTO + 'NotoSerifCJK-Bold.ttc'],
    'LXGW':   [_NOTO + 'LXGWWenKai-Regular.ttf'],      # 文楷：摘要/品牌
    'MSZ':    [_NOTO + 'MaShanZheng-Regular.ttf'],    # 毛笔：热点大字
}
# MSZ 缺字时的跨角色回退（v3.3.0 cover-dynamic 既有逻辑：暂无 MaShanZheng 回退）
_ROLE_FALLBACK = {
    'BOLD': ['BOLD', 'NORMAL'],
    'NORMAL': ['NORMAL', 'LXGW'],
    'SERIF': ['SERIF', 'BOLD'],
    'LXGW': ['LXGW', 'NORMAL'],
    'MSZ': ['MSZ', 'LXGW', 'NORMAL'],
}

_bitmap_warned = False


def ensure_pillow():
    """缺 Pillow → 明错 + exit 2，不 traceback。"""
    if not PIL_OK:
        cli.missing_dependency('Pillow', '请先安装：pip install Pillow')


def _try_truetype(path, size):
    for index in (2, 0):  # .ttc 先试 index=2（v3.3.0 cover-card 逻辑）
        try:
            return ImageFont.truetype(path, size, index=index)
        except Exception:
            continue
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return None


def _find_font(role, size):
    """走回退链找字体。返回 (font, ok)；ok=False 表示退到 PIL 位图字体。"""
    for r in _ROLE_FALLBACK.get(role, [role]):
        for path in _FONT_FILES.get(r, []):
            if os.path.exists(path):
                f = _try_truetype(path, size)
                if f is not None:
                    return f, True
    return ImageFont.load_default(), False


def load_font(role, size):
    """软加载：链全灭时给 PIL 位图字体并 stderr 警告（不抛异常不退出）。

    cover-dynamic 等保留 v3.2.0「缺字体仍出图、exit 0」的路径用此函数。
    """
    global _bitmap_warned
    f, ok = _find_font(role, size)
    if not ok and not _bitmap_warned:
        _bitmap_warned = True
        print('警告：未找到可用的中文字体（%s），已退回 PIL 位图字体，'
              '中文将显示为方框。' % _NOTO, file=sys.stderr)
    return f


def require_font(role, size):
    """硬加载：链全灭时明错 + exit 2（不 traceback）。

    需要真实中文字体才能出有意义成品的工具，在入口处用此函数。
    """
    f, ok = _find_font(role, size)
    if not ok:
        cli.missing_dependency(
            '中文字体',
            '在 %s 下未找到 Noto CJK / 文楷 / 毛笔字体文件，'
            '无法渲染中文封面。' % _NOTO)
    return f


def font_lxgw(size):
    """文楷（品牌/摘要用，v3.2.0 分工保留）。"""
    return load_font('LXGW', size)


def font_msz(size):
    """毛笔（热点大字用，v3.2.0 分工保留；缺字时退文楷）。"""
    return load_font('MSZ', size)


# ── 画布 ────────────────────────────────────────────────
def new_canvas(w=COVER_W, h=COVER_H, bg=PAPER):
    """标准画布，返回 (img, draw)。"""
    ensure_pillow()
    img = Image.new('RGB', (w, h), bg)
    return img, ImageDraw.Draw(img)


# ── 品牌 logo：逐字混排（2x 超采样）──────────────────────
def render_logo(logo_chars=None, size=30, color=RED):
    """渲染品牌 logo，返回带 yeji_x / shui_right / shu_x0 属性的 RGBA 图。

    logo_chars: [(字, 字体角色)]，字体角色 'LXGW'|'MSZ'|'NORMAL'。
    属性含义（v3.3.0 cover-card 像素对齐逻辑）：
      shu_x0    第 1 字视觉左 → 红线起点
      shui_right 第 2 字视觉右 → 红线终点
      yeji_x    第 3 字视觉左 → 英文起点
    """
    ensure_pillow()
    logo_chars = logo_chars or LOGO_CHARS
    gap, pad, ss = 6, 20, 2
    items = []
    for ch, role in logo_chars:
        fb = load_font(role, size * ss)
        cell = Image.new('RGBA', (size * 3 * ss, size * 3 * ss), (0, 0, 0, 0))
        ImageDraw.Draw(cell).text((size * ss, size * ss), ch, font=fb, fill=color)
        bbox = cell.getbbox()
        items.append((ch, cell.crop(bbox) if bbox else cell))
    H = size * 2 + 40
    W = sum(round(g.width / ss) for _, g in items) + gap * (len(items) - 1) + pad * 2 + 2
    big = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
    cy = big.height / 2
    span = {}
    x = pad * ss
    for ch, g in items:
        px2 = int(x)
        py2 = int(round(cy - g.height / 2))
        big.paste(g, (px2, py2), g)
        # 同帧 alpha>128 测视觉边界（LANCZOS 会让 alpha>0 边缘扩散 1~4px）
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
        shu_x0, shui_right, yeji_left = sps[0][0], sps[1][1], sps[2][0]
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


def draw_brand_block(img, d, brand_dir=None, logo_chars=None, en_text=None,
                     lx=56, ly=32, logo_size=30, color=RED,
                     prefer_asset=True, asset_width=130):
    """左上品牌块：logo + 英文 + 红线。

    优先贴 assets/brand 下的预制 logo 图（缺失 → 逐字字体渲染回退，
    v3.2.0 回退规则，exit 0）。返回几何 dict。
    """
    logo_chars = logo_chars or LOGO_CHARS
    en_text = BRAND_EN if en_text is None else en_text
    logo = None
    if prefer_asset and brand_dir:
        p = os.path.join(brand_dir, 'logo-mixed-transparent.png')
        if os.path.exists(p):
            try:
                lg = Image.open(p)
                th = int(round(asset_width / lg.width * lg.height))
                logo = lg.resize((asset_width, th), Image.LANCZOS)
            except Exception as e:
                print('警告：品牌 logo 图加载失败 %s，改用字体渲染' % e,
                      file=sys.stderr)
                logo = None
    if logo is None:
        logo = render_logo(logo_chars, logo_size, color)
    img.paste(logo, (lx, ly), logo)

    if prefer_asset and brand_dir and logo is not None and not hasattr(logo, 'yeji_x'):
        aspect = logo.width / max(logo.height, 1)
        wide_lockup = aspect > 2.2
    else:
        wide_lockup = False

    if wide_lockup:
        # 品牌区已有标准图（横排毛笔字标 logo-brand.png）：只贴图，
        # 不再叠加红线/英文行 —— 标准图自身即完整品牌识别，重排反而破坏。
        return {'lx': lx, 'ly': ly, 'logo_h': logo.height,
                'yeji_left': lx, 'shui_right': lx + logo.width,
                'shu_x0': lx, 'en_top': ly + logo.height, 'rule_y': None,
                'image_only': True}

    if prefer_asset and brand_dir and logo is not None and not hasattr(logo, 'yeji_x'):
        # 方形印章母图：按 455 宽的实测字间隙换算（弎水 | 野记 两列）
        s = asset_width / 455.0
        shu_x0 = lx
        shui_right = lx + 226 * s
        yeji_left = lx + 234 * s
    else:
        yeji_left = lx + getattr(logo, 'yeji_x', 0)
        shui_right = lx + getattr(logo, 'shui_right', yeji_left)
        shu_x0 = lx + getattr(logo, 'shu_x0', 0)

    f_en = load_font('NORMAL', 14)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), en_text, font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=color)
    d.text((yeji_left, en_top), en_text, font=f_en, fill=GREY, anchor='lt')
    return {'lx': lx, 'ly': ly, 'logo_h': logo.height,
            'yeji_left': yeji_left, 'shui_right': shui_right, 'shu_x0': shu_x0,
            'en_top': en_top}


def draw_seal(img, d, brand_dir=None, sx=None, sy=None, side=84,
              style='circle', seal_chars=None, asset_name=None, color=RED):
    """右上印章：优先贴预制印章图，缺失 → 程序化绘制回退（exit 0）。

    style='circle': 红色双线圆 + 4 字；'square': 2x2 红印（右起竖读）。
    """
    ensure_pillow()
    seal_chars = seal_chars or SEAL_CHARS
    if sx is None:
        sx = COVER_W - 56 - side
    if sy is None:
        sy = 28
    pasted = False
    if brand_dir and asset_name:
        p = os.path.join(brand_dir, asset_name)
        if os.path.exists(p):
            try:
                seal = Image.open(p)
                img.paste(seal, (sx, sy), seal)
                pasted = True
            except Exception as e:
                print('警告：印章图加载失败 %s，改用程序化绘制' % e, file=sys.stderr)
    if not pasted:
        if style == 'square':
            d.rectangle([sx, sy, sx + side, sy + side], fill=color)
            f_seal = load_font('SERIF', 27)
            cell = side // 2
            d.rectangle([sx + cell + 6, sy + 6, sx + side - 6, sy + cell - 6],
                        fill=WHITE)
            # 右起竖读：(右上, 右下, 左上, 左下)
            for ch, (cx, cy, fill) in [
                    (seal_chars[2], (0, 0, WHITE)), (seal_chars[0], (1, 0, color)),
                    (seal_chars[3], (0, 1, WHITE)), (seal_chars[1], (1, 1, WHITE))]:
                bb = d.textbbox((0, 0), ch, font=f_seal)
                cw, chh = bb[2] - bb[0], bb[3] - bb[1]
                d.text((sx + cx * cell + (cell - cw) // 2 - bb[0],
                        sy + cy * cell + (cell - chh) // 2 - bb[1]),
                       ch, font=f_seal, fill=fill)
        else:
            d.ellipse([sx, sy, sx + side, sy + side], outline=color, width=3)
            d.ellipse([sx + 6, sy + 6, sx + side - 6, sy + side - 6],
                      outline=color, width=1)
            f_seal = load_font('SERIF', 24)
            ccx, ccy = sx + side // 2, sy + side // 2
            for ch, dx, dy in [(seal_chars[2], -20, -22), (seal_chars[0], 6, -22),
                               (seal_chars[3], -20, 4), (seal_chars[1], 6, 4)]:
                d.text((ccx + dx, ccy + dy), ch, font=f_seal, fill=color)
    return sx, sy, side


def draw_footer(d, slogan=None, date=None, w=COVER_W, h=COVER_H, color=RED):
    """底部：灰细线 + slogan + 日期角标（cover-card/brief/dynamic 通用）。"""
    slogan = SLOGAN if slogan is None else slogan
    d.rectangle([56, h - 74, w - 56, h - 73], fill=HAIRLINE)
    d.text((56, h - 56), slogan, font=load_font('NORMAL', 16), fill=GREY)
    if date:
        f_date = load_font('BOLD', 17)
        tw = d.textbbox((0, 0), date, font=f_date)[2]
        d.rounded_rectangle([w - 56 - tw - 28, h - 62, w - 56, h - 30],
                            radius=6, outline=color, width=2)
        d.text((w - 56 - tw - 14, h - 55), date, font=f_date, fill=color)


# ── 文字排版 ──────────────────────────────────────────────
def wrap_lines(draw, text, fnt, max_w):
    """按像素宽度折行：优先在分隔符处切，否则选两行宽度最接近的切点，
    兜底贪心逐字折行（合并 v3.3.0 cover-card.measured 与 cover-brief 逻辑）。"""
    width = lambda s: draw.textbbox((0, 0), s, font=fnt)[2]
    if width(text) <= max_w:
        return [text]
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


def fit_font_size(draw, text, role, start_size, min_size, max_w):
    """自适应字号：从 start_size 递减到刚好塞进 max_w。返回 (font, size)。"""
    size = start_size
    while size >= min_size:
        fnt = load_font(role, size)
        if draw.textbbox((0, 0), text, font=fnt)[2] <= max_w:
            return fnt, size
        size -= 2
    return load_font(role, min_size), min_size
