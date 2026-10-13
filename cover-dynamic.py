#!/usr/bin/env python3
"""cover-dynamic.py：公众号封面图生成器（动态提取版）。

v4 垫片：CLI 参数与 v3.3.0 一致，渲染逻辑走 gzhkit.visual.canvas。
从正文 .md 自动提取锚点关键词 + 4 行摘要，也可用参数覆盖。
品牌 logo/印章优先用 assets/brand 下预制图，缺失 → 字体渲染回退，
退出码仍 0（v3.2.0 回退规则保留）。

字体分工（v3.2.0，原样保留）：摘要区用文楷 LXGW（信息承载层，可读性优先）。
用法：python3 cover-dynamic.py <正文.md> [--keyword X] [--summaries "a;b;c;d"]
      [--subtitle "中;en"] [--date YYYY.MM]
"""
import datetime
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli, report
from gzhkit.visual import canvas

HEAD_W, HEAD_H = canvas.COVER_W, canvas.COVER_H
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BRAND_DIR = os.path.join(BASE_DIR, 'assets', 'brand')
OUT_DIR = os.path.join(BASE_DIR, 'assets', 'out')


# ── 动态提取 ──────────────────────────────────────────────
def extract_keyword(text):
    """锚点关键词：引号词（频次×长度打分）→ **加粗** → 标题前 4 字词 → 兜底。"""
    quotes = re.findall(r'[“”「」](.+?)[“”「」]', text)
    if quotes:
        best, best_score = None, -1
        first_line = text.split('\n')[0]
        for qc in {q.strip() for q in quotes}:
            if not qc:
                continue
            score = text.count(qc) * 10
            n_zh = len(re.findall(r'[一-鿿]', qc))
            if 3 <= n_zh <= 4:
                score += 15
            if n_zh <= 2 or n_zh > 6:
                score -= 10
            if qc in first_line:
                score += 30
            if score > best_score:
                best_score, best = score, qc
        if best:
            return best
    for b in re.findall(r'\*\*([^*]{2,8})\*\*', text):
        bc = re.sub(r'[。、；：！？\-—]', '', b.strip())
        if 3 <= len(re.findall(r'[一-鿿]', bc)) <= 4:
            return bc
    title = text.split('\n')[0].lstrip('# ').strip()
    words = re.findall(r'[一-鿿]{3,4}', title)
    return words[0] if words else '核心观点'


def extract_summaries(text):
    """4 行摘要：标题改写 / 现象句 / 结论句 / 日期。"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    def clean(s):
        s = re.sub(r'[""\u02ba「」“”]', '', s)
        s = re.sub(r'[，。、；：！？]', '', s)
        return re.sub(r'\s+', '', s)

    title = lines[0].lstrip('# ').strip()
    s1 = re.sub(r'^(我[研究了|发现]|研究[了|过]|测试[了|过]).*?(发现|最|不是|才是)', '', title)
    s1 = re.sub(r'[^a-zA-Z一-鿿]+', ' ', s1).strip()[:14]
    body = [l for l in lines[1:] if l and not l.startswith('#') and l != '---']
    s2 = next((clean(l) for l in body if 6 <= len(clean(l)) <= 14), '现象描述')
    s3 = '核心观点'
    for l in body:
        if any(k in l for k in ('结论', '最关键', '判断', '核心')):
            c = clean(l)
            if 6 <= len(c) <= 14:
                s3 = c
                break
    if s3 == '核心观点':
        for l in reversed(body):
            c = clean(l)
            if 4 <= len(c) <= 14:
                s3 = c
                break
    return [s1, s2[:14], s3[:14], datetime.datetime.now().strftime('%Y.%m')]


# ── 已知文章摘要缓存（自动提取质量不足时登记在此）────────
# 格式：正文绝对路径 → {'keyword': str, 'summaries': [str×4],
#                      'subtitle_cn': str, 'subtitle_en': str}
ARTICLE_CACHE = {}


def _get_cached_article(art_path):
    return ARTICLE_CACHE.get(os.path.abspath(art_path))


# ── 主渲染 ────────────────────────────────────────────────
def generate_cover(art_path, keyword=None, summaries=None,
                   subtitle_cn=None, subtitle_en=None, date_str=None):
    canvas.ensure_pillow()
    text = cli.read_text(art_path)  # 读失败 → stderr + exit 2

    cached = _get_cached_article(os.path.abspath(art_path))
    if cached:
        print('✅ 使用缓存摘要: %s' % os.path.basename(art_path))
        keyword = cached.get('keyword', keyword)
        summaries = summaries or cached.get('summaries')
        subtitle_cn = subtitle_cn or cached.get('subtitle_cn')
        subtitle_en = subtitle_en or cached.get('subtitle_en')

    anchor_text = keyword or extract_keyword(text)
    extracted = extract_summaries(text)
    use_summaries = summaries if summaries else extracted
    title = text.split('\n')[0].lstrip('# ').strip()
    default_cn = subtitle_cn or ('当「%s」开始' % anchor_text)
    default_en = subtitle_en or title.upper()[:30]
    if date_str is None:
        date_str = datetime.datetime.now().strftime('%Y.%m')

    print('锚点关键词: %s' % anchor_text)
    print('摘要行:')
    for i, s in enumerate(use_summaries, 1):
        print('  %d. %s' % (i, s))
    print('副标题: %s' % default_cn)
    print('英文: %s' % default_en)

    img, d = canvas.new_canvas(HEAD_W, HEAD_H, canvas.PAPER)

    # 左侧红条
    d.rectangle([0, 0, 10, HEAD_H], fill=canvas.RED)

    # 品牌块：优先贴预制 logo 图，缺失 → 逐字字体渲染回退（exit 0）
    canvas.draw_brand_block(img, d, brand_dir=BRAND_DIR, prefer_asset=True,
                            lx=58, ly=32, logo_size=30)

    # 印章：优先贴预制印章图，缺失 → 圆形程序化回退
    canvas.draw_seal(img, d, brand_dir=BRAND_DIR, style='circle',
                     asset_name='seal-uploaded-84.png')

    # 4 行摘要（左对齐）：文楷承载信息层，字号自适应
    fs = [20, 26, 32, 22]
    y = 115
    MAX_SUM_W = 370  # 摘要单行最大宽度，留足与右侧锚点的呼吸间距
    for i, line in enumerate(use_summaries):
        x = 56
        fnt, size = canvas.fit_font_size(d, line, 'LXGW', fs[i], 14, MAX_SUM_W + 20)
        color = canvas.RED if i == 2 else canvas.INK  # 第 3 行（观点）品牌红高亮
        d.text((x, y), line, font=fnt, fill=color)
        y += size + 18

    # 锚点大字 + 圆形装饰：衬线体做视觉锚点
    # ax=520 确保与左侧摘要（最远 x≈446）之间留 ~74px 呼吸间距
    ax = 520
    f_anchor = canvas.load_font('SERIF', 84 if len(anchor_text) >= 2 else 88)
    abox = d.textbbox((0, 0), anchor_text, font=f_anchor)
    aw, ah = abox[2] - abox[0], abox[3] - abox[1]
    ay = 128
    cx, cy, r = ax + aw // 2, ay + ah // 2, 88
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=canvas.LIGHT_RED, width=2)
    for i in range(24):
        ang = (i * 360 / 24 - 45) * math.pi / 180
        dx = cx + (r + 18) * math.cos(ang)
        dy = cy + (r + 18) * math.sin(ang)
        d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=canvas.DOT_GREY)
    d.text((ax, ay), anchor_text, font=f_anchor, fill=canvas.RED)
    d.rectangle([ax, ay + ah + 8, ax + aw, ay + ah + 10], fill=canvas.RED)
    d.text((ax + 2, ay + ah + 22), default_cn,
           font=canvas.load_font('NORMAL', 15), fill=canvas.GREY)
    d.text((ax + 2, ay + ah + 44), default_en,
           font=canvas.load_font('NORMAL', 12), fill=canvas.MID_GREY)

    # 底部 slogan + 日期标签
    canvas.draw_footer(d, date=date_str)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, '封面图-动态提取.png')
    img.save(out_path, quality=95)
    print('\n封面图已保存: %s' % out_path)
    return out_path


def main():
    ap = cli.build_parser('cover-dynamic.py', '公众号封面图生成器（动态提取版）')
    ap.add_argument('article', nargs='?', help='正文 .md 路径')
    ap.add_argument('--keyword', default=None, help='覆盖锚点关键词')
    ap.add_argument('--summaries', default=None, help='覆盖 4 行摘要，分号分隔')
    ap.add_argument('--subtitle', default=None, help='覆盖副标题，"中文;EN"')
    ap.add_argument('--date', default=None, help='覆盖日期，默认当月 YYYY.MM')
    a = ap.parse_args()

    if not a.article:
        report.die_input('缺少正文路径：用法 cover-dynamic.py <正文.md> [选项]')
    subs = a.subtitle.split(';') if a.subtitle else []
    generate_cover(a.article, keyword=a.keyword,
                   summaries=a.summaries.split(';') if a.summaries else None,
                   subtitle_cn=subs[0] if len(subs) > 0 else None,
                   subtitle_en=subs[1] if len(subs) > 1 else None,
                   date_str=a.date)
    return 0


if __name__ == '__main__':
    cli.run_main(main)
