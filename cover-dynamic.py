#!/usr/bin/env python3
"""公众号封面图生成器（动态提取版 v1.9.0）
用法：python3 cover-dynamic.py <正文.md路径> [--keyword X] [--summaries "a;b;c;d"] [--subtitle "中;en"] [--date YYYY.MM]
"""
import sys, re, os, math, datetime
from PIL import Image, ImageDraw, ImageFont

HEAD_W, HEAD_H = 900, 383
OUT_DIR = '/var/minis/shared/gzh-team/assets/out'
os.makedirs(OUT_DIR, exist_ok=True)

RED    = (194, 69, 60)
PAPER  = (245, 245, 245)
INK    = (51, 51, 51)
GREY   = (140, 140, 140)
MID_GREY = (160, 160, 160)
LIGHT_RED = (232, 196, 192)
DOT_GREY = (232, 180, 176)

BRAND = '<YOUR_BRAND>'
EN_BRAND = 'SANSHUI YEJI'
SLOGAN = '野路实测，笔记为证：留下能用的'

# ── 字体（优先霞鹜，回退到 Noto CJK）─────────────────────────
_FONT_ALT = [
    '/usr/share/fonts/noto/LXGWWenKai-Regular.ttf',
    '/usr/share/fonts/noto/MaShanZheng-Regular.ttf',
]
_FONT_CJK = {
    'BOLD':   '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc',
    'NORMAL': '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc',
    'SERIF':  '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc',
}

def _try_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return None

def font_cjk(style, size):
    """按 style(BOLD/NORMAL/SERIF) 返回字体，找不到时自动回退"""
    p = _FONT_CJK[style]
    f = _try_font(p, size)
    if f: return f
    # 回退：遍历备选
    for alt in _FONT_ALT:
        if os.path.exists(alt):
            f = _try_font(alt, size)
            if f: return f
    return ImageFont.load_default()  # 最后手段

def font_lxgw(size):
    """LXGW 文楷（品牌用）"""
    for p in _FONT_ALT:
        if os.path.exists(p):
            f = _try_font(p, size)
            if f: return f
    return font_cjk('NORMAL', size)

# ── 动态提取 ──────────────────────────────────────────────────
def extract_keyword(text):
    quotes = re.findall(r'[\u201c\u201d\u300c\u300d](.+?)[\u201c\u201d\u300c\u300d]', text)
    if quotes:
        best, best_score = None, -1
        for q in set(quotes):
            qc = q.strip()
            if not qc: continue
            full_freq = text.count(qc)
            score = full_freq * 10
            L = len(re.findall(r'[\u4e00-\u9fff]', qc))
            if 3 <= L <= 4: score += 15
            if L <= 2: score -= 10
            if L > 6: score -= 10
            if qc in text.split('\n')[0]: score += 30
            if score > best_score: best_score = score; best = qc
        if best: return best
    bolds = re.findall(r'\*\*([^*]{2,8})\*\*', text)
    for b in bolds:
        bc = re.sub(r'[。、；：！？\-—]', '', b.strip())
        if 3 <= len(re.findall(r'[\u4e00-\u9fff]', bc)) <= 4:
            return bc
    title = text.split('\n')[0].lstrip('# ').strip()
    words = re.findall(r'[\u4e00-\u9fff]{3,4}', title)
    return words[0] if words else '核心观点'

def extract_summaries(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    def clean(s):
        s = re.sub(r'["""\uff02\u300c\u300d\u201c\u201d]', '', s)
        s = re.sub(r'[，。、；：！？]', '', s)
        s = re.sub(r'\s+', '', s)
        return s
    title = lines[0].lstrip('# ').strip()
    s1 = re.sub(r'^(我[研究了|发现]|研究[了|过]|测试[了|过]).*?(发现|最|不是|才是)', '', title)
    s1 = re.sub(r'[^a-zA-Z\u4e00-\u9fff]+', ' ', s1).strip()[:14]
    body_lines = [l for l in lines[1:] if l and not l.startswith('#') and l != '---']
    s2 = '现象描述'
    for l in body_lines:
        c = clean(l)
        if 6 <= len(c) <= 14: s2 = c; break
    s3 = '核心观点'
    for l in body_lines:
        if any(k in l for k in ('结论', '最关键', '判断', '核心', '结论一', '结论二', '结论三')):
            c = clean(l)
            if 6 <= len(c) <= 14: s3 = c; break
    if s3 == '核心观点':
        for l in reversed(body_lines):
            c = clean(l)
            if 4 <= len(c) <= 14: s3 = c; break
    return [s1, s2[:14], s3[:14], datetime.datetime.now().strftime('%Y.%m')]

# ── 品牌 Logo 渲染（复刻 cover-card.py 像素对齐逻辑）──────────
def render_logo(logo_chars, size):
    """logo_chars: list of (char, font_style) where font_style='LXGW'|'MSZ'|'N'"""
    gap, pad, ss = 6, 20, 2
    items = []
    for ch, style in logo_chars:
        if style == 'LXGW':
            fb = font_lxgw(size * ss)
        elif style == 'MSZ':
            fb = font_lxgw(size * ss)  # 暂无 MaShanZheng fallback
        else:
            fb = font_cjk('NORMAL', size * ss)
        cell = Image.new('RGBA', (size * 3 * ss, size * 3 * ss), (0, 0, 0, 0))
        ImageDraw.Draw(cell).text((size * ss, size * ss), ch, font=fb, fill=RED)
        bbox = cell.getbbox()
        if bbox:
            items.append((ch, cell.crop(bbox)))
        else:
            items.append((ch, cell))
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
        bx = big.getchannel('A').crop((px2, py2, px2 + g.width, py2 + g.height))
        a0 = a1 = None
        for k in range(bx.width):
            if bx.crop((k, 0, k + 1, bx.height)).getextrema()[1] > 128:
                if a0 is None: a0 = k
                a1 = k
        if a0 is not None:
            span[ch] = ((px2 + a0) / ss, (px2 + a1) / ss)
        x += g.width + gap * ss
    sps = list(span.values())
    if len(sps) >= 3:
        shu_x0, shui_right, yeji_left = sps[0][0], sps[1][1], sps[2][0]
    else:
        shu_x0 = shui_right = yeji_left = None
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

# ── 主渲染 ────────────────────────────────────────────────────
def generate_cover(art_path, keyword=None, summaries=None,
                   subtitle_cn=None, subtitle_en=None, date_str=None):
    with open(art_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # 优先从缓存获取
    cached = _get_cached_article(os.path.abspath(art_path))
    if cached:
        print(f'✅ 使用缓存摘要: {os.path.basename(art_path)}')
        keyword = cached.get('keyword', keyword)
        summaries = summaries or cached.get('summaries')
        subtitle_cn = subtitle_cn or cached.get('subtitle_cn')
        subtitle_en = subtitle_en or cached.get('subtitle_en')
    anchor_text = keyword or extract_keyword(text)
    extracted = extract_summaries(text)
    use_summaries = summaries if summaries else extracted
    title = text.split('\n')[0].lstrip('# ').strip()
    default_cn = f'当「{anchor_text}」开始' if not subtitle_cn else subtitle_cn
    default_en = title.upper()[:30] if not subtitle_en else subtitle_en
    if date_str is None: date_str = datetime.datetime.now().strftime('%Y.%m')

    print(f'锚点关键词: {anchor_text}')
    print(f'摘要行:')
    for i, s in enumerate(use_summaries, 1):
        print(f'  {i}. {s}')
    print(f'副标题: {default_cn}')
    print(f'英文: {default_en}')

    img = Image.new('RGB', (HEAD_W, HEAD_H), PAPER)
    d = ImageDraw.Draw(img)

    # 左侧红条
    d.rectangle([0, 0, 10, HEAD_H], fill=RED)

    # Logo（红色，30px）
    logo_chars = [('弎','LXGW'),('水','LXGW'),('野','MSZ'),('记','MSZ')]
    logo = render_logo(logo_chars, 30)
    lx, ly = 56, 32
    img.paste(logo, (lx, ly), logo)
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = font_cjk('NORMAL', 14)
    en_top = ly + logo.height + 3
    bbox_en = d.textbbox((yeji_left, en_top), EN_BRAND, font=f_en, anchor='lt')
    en_mid = (bbox_en[1] + bbox_en[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), EN_BRAND, font=f_en, fill=GREY, anchor='lt')

    # 印章
    seal_path = '/var/minis/shared/gzh-team/assets/brand/seal-circle-84.png'
    sx, sy = HEAD_W - 56 - 84, 28
    if os.path.exists(seal_path):
        seal = Image.open(seal_path)
        img.paste(seal, (sx, sy), seal)
    else:
        d.rectangle([sx, sy, sx + 84, sy + 84], fill=RED)

    # 4行阶梯文字（OPT2）
    fs = [20, 26, 32, 22]
    offs = [0, 12, 24, 36]
    y = 115
    MAX_SUM_W = 400  # 摘要单行最大宽度，超长自动缩字，避免与右侧艺术字重叠
    for i, line in enumerate(use_summaries):
        x = 56 + offs[i]
        # 自适应字号：先按预定字号量宽，超限则缩小
        scaled = None
        size = fs[i]
        while size >= 14:
            fnt = font_cjk('BOLD', size)
            tw = d.textbbox((0, 0), line, font=fnt)[2]
            if (x + tw) <= x + MAX_SUM_W + 20:
                scaled = size
                break
            size -= 2
        fnt = font_cjk('BOLD', scaled if scaled else 14)
        d.text((x, y), line, font=fnt, fill=INK)
        tw = d.textbbox((0, 0), line, font=fnt)[2]
        if i == 0:
            uy = y + size + 4
            d.rectangle([x, uy, x + tw, uy + 2], fill=RED)
        y += size + 18

    # 锚点大字 + 圆形装饰（OPT3）
    ax = 560
    f_anchor = font_cjk('SERIF', 72 if len(anchor_text) >= 2 else 76)
    abbox = d.textbbox((0, 0), anchor_text, font=f_anchor)
    aw = abbox[2] - abbox[0]
    ah = abbox[3] - abbox[1]
    ay = 138
    circle_cx = ax + aw // 2
    circle_cy = ay + ah // 2
    circle_r = 70
    d.ellipse([circle_cx - circle_r, circle_cy - circle_r,
               circle_cx + circle_r, circle_cy + circle_r], outline=LIGHT_RED, width=2)
    arc_radius = circle_r + 15
    for i in range(24):
        angle = (i * 360 / 24 - 45) * math.pi / 180
        dx = circle_cx + arc_radius * math.cos(angle)
        dy = circle_cy + arc_radius * math.sin(angle)
        d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=DOT_GREY)
    d.text((ax, ay), anchor_text, font=f_anchor, fill=RED)
    d.rectangle([ax, ay + ah + 8, ax + aw, ay + ah + 10], fill=RED)
    f_sub = font_cjk('NORMAL', 14)
    d.text((ax + 2, ay + ah + 22), default_cn, font=f_sub, fill=GREY)
    f_en2 = font_cjk('NORMAL', 11)
    d.text((ax + 2, ay + ah + 42), default_en, font=f_en2, fill=MID_GREY)

    # 底部 Slogan + 日期标签
    d.rectangle([56, HEAD_H - 74, HEAD_W - 56, HEAD_H - 73], fill=(215, 215, 215))
    f_slogan = font_cjk('NORMAL', 16)
    d.text((56, HEAD_H - 56), SLOGAN, font=f_slogan, fill=GREY)
    f_date = font_cjk('BOLD', 17)
    w = d.textbbox((0, 0), date_str, font=f_date)[2]
    d.rounded_rectangle([HEAD_W - 56 - w - 28, HEAD_H - 62, HEAD_W - 56, HEAD_H - 30],
                        radius=6, outline=RED, width=2)
    d.text((HEAD_W - 56 - w - 14, HEAD_H - 55), date_str, font=f_date, fill=RED)

    out_path = f'{OUT_DIR}/封面图-动态提取.png'
    img.save(out_path, quality=95)
    print(f'\n封面图已保存: {out_path}')
    return out_path

# ── 已知文章摘要缓存（自动提取质量不足时使用）────────────────
# 格式：正文路径 → {'keyword': str, 'summaries': list[str], 'subtitle': (cn, en)}
ARTICLE_CACHE = {
    '/var/minis/shared/gzh-team/选题库/ai-agent-ecosystem-20261006/正文.md': {
        'keyword': '技能层',
        'summaries': [
            '研究了90个AI Agent项目',
            '框架层开源等于免费',
            '记忆层是被低估的赛道',
            '2026.10',
        ],
        'subtitle_cn': '当记忆层和技能的窗口打开时',
        'subtitle_en': 'WHEN MEMORY AND SKILL LAYERS OPEN',
    },
}

def _get_cached_article(art_path):
    """从缓存返回摘要参数，找到返回 dict，否则返回 None"""
    return ARTICLE_CACHE.get(os.path.abspath(art_path))

# ── CLI ───────────────────────────────────────────────────────
def parse_args():
    args = {'keyword': None, 'summaries': None, 'subtitle_cn': None,
            'subtitle_en': None, 'date': None}
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '--keyword' and i + 1 < len(sys.argv):
            args['keyword'] = sys.argv[i + 1]; i += 2
        elif a == '--summaries' and i + 1 < len(sys.argv):
            args['summaries'] = sys.argv[i + 1].split(';'); i += 2
        elif a == '--subtitle' and i + 1 < len(sys.argv):
            parts = sys.argv[i + 1].split(';')
            args['subtitle_cn'] = parts[0] if len(parts) > 0 else None
            args['subtitle_en'] = parts[1] if len(parts) > 1 else None
            i += 2
        elif a == '--date' and i + 1 < len(sys.argv):
            args['date'] = sys.argv[i + 1]; i += 2
        else:
            i += 1
    return args

if __name__ == '__main__':
    art_path = sys.argv[1] if len(sys.argv) > 1 else '/var/minis/shared/gzh-team/选题库/ai-interview-tdd-20261004/正文.md'
    args = parse_args()
    generate_cover(art_path, keyword=args['keyword'], summaries=args['summaries'],
                   subtitle_cn=args['subtitle_cn'], subtitle_en=args['subtitle_en'],
                   date_str=args['date'])
