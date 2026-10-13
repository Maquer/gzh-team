#!/usr/bin/env python3
"""gzhkit.visual.styles: 封面风格参数表（10 种预设：颜色/字体/布局）。

由 v3.3.0 cover_styles.py 干净重写迁入。预设数量固定 10 种。
消除重复：10 个风格的公共键经 _style() 构造器收敛，不再逐字复制。

调性 → 风格映射（TONE_TO_STYLE）与 gzh-typeset 融合版 TONES 的 5 档
调性名完全一致，保证「封面强调色 = 正文排版主色」，封面与内文是一套视觉。
每档第 1 推荐 = 主色最接近该调性 primary 的风格。
"""


def _style(name, desc, bg, accent, text_fill, sub_fill, list_fill,
           bar_pos='left', bar_w=5, title_align='left',
           badge_shape='rounded', badge_color='accent',
           bottom_line=True, deco='none'):
    """风格构造器：收敛 10 个预设的重复键。"""
    return {
        'name': name,
        'desc': desc,
        'bg': bg,
        'accent': accent,
        'text_fill': text_fill,
        'sub_fill': sub_fill,
        'list_fill': list_fill,
        'bar_pos': bar_pos,
        'bar_w': bar_w,
        'title_align': title_align,
        'badge_shape': badge_shape,
        'badge_color': badge_color,
        'bottom_line': bottom_line,
        'deco': deco,
    }


def _grad(top, bottom):
    return {'type': 'gradient', 'top': top, 'bottom': bottom}


def _solid(color):
    return {'type': 'solid', 'color': color}


DESIGNER_STYLES = {
    # ── 7 位设计师风格 ──────────────────────────────────
    'stout': _style(
        'Tyler Stout', '复古科幻·高饱和撞色',
        _grad((10, 10, 40), (40, 10, 60)),
        (255, 100, 50), (255, 255, 255), (200, 180, 255), (180, 220, 255),
        bar_w=6, deco='corners'),
    'moss': _style(
        'Olly Moss', '极简负空间·奶油底+红黑',
        _solid((252, 248, 240)),
        (200, 50, 50), (30, 30, 30), (80, 80, 80), (100, 100, 100),
        bar_w=3, badge_shape='none', bottom_line=False),
    'ansin': _style(
        'Martin Ansin', '黑白高对比·对称构图',
        _grad((15, 15, 15), (35, 35, 35)),
        (180, 30, 30), (255, 255, 255), (200, 200, 200), (180, 180, 180),
        bar_pos='center', bar_w=2, title_align='center',
        badge_shape='square', deco='frame'),
    'struzan': _style(
        'Drew Struzan', '暖调油画·琥珀金',
        _grad((60, 45, 30), (30, 25, 20)),
        (218, 165, 50), (255, 245, 230), (220, 200, 180), (200, 185, 170),
        bar_w=4),
    'pardee': _style(
        'Alex Pardee', '极简恐怖·白底黑字',
        _solid((245, 240, 235)),
        (30, 30, 30), (30, 30, 30), (80, 80, 80), (100, 100, 100),
        bar_w=2, badge_shape='none', bottom_line=False),
    'peak': _style(
        'Bob Peak', '装饰艺术·几何撞色',
        _grad((30, 20, 60), (60, 30, 20)),
        (255, 200, 50), (255, 255, 255), (255, 230, 200), (220, 220, 240),
        bar_pos='right', bar_w=8, badge_shape='square', deco='corners'),
    'weeks': _style(
        'Ken Taylor', '柔和渐变·蓝紫调',
        _grad((25, 30, 55), (45, 35, 70)),
        (140, 180, 230), (240, 240, 250), (200, 200, 230), (190, 200, 230),
        bar_w=4),
    # ── 3 个原有渐变预设（向后兼容）─────────────────────
    'deep-blue': _style(
        '深海蓝（默认）', '深色渐变·金色强调',
        _grad((26, 26, 46), (15, 32, 62)),
        (245, 197, 66), (255, 255, 255), (220, 220, 220), (210, 210, 220)),
    'deep-gray': _style(
        '石墨灰', '深灰渐变·蓝色强调',
        _grad((45, 45, 48), (24, 24, 27)),
        (74, 144, 217), (240, 240, 240), (200, 200, 200), (190, 190, 200)),
    'black': _style(
        '近黑', '近黑渐变·红色强调',
        _grad((15, 15, 18), (30, 30, 35)),
        (233, 69, 96), (255, 255, 255), (220, 220, 220), (210, 210, 220)),
}

# ── 调性 → 风格推荐映射 ──────────────────────────────────
TONE_TO_STYLE = {
    'authoritative': {  # 权威·合规  primary #B03A2E 砖红
        'label': '权威·合规', 'primary': (176, 58, 46),
        'rank': ['black', 'ansin', 'deep-blue']},
    'friendly': {       # 亲和·教程  primary #2E8B8B 青
        'label': '亲和·教程', 'primary': (46, 139, 139),
        'rank': ['weeks', 'moss', 'deep-gray']},
    'analytical': {     # 理性·深度  primary #2F5D8A 深蓝
        'label': '理性·深度', 'primary': (47, 93, 138),
        'rank': ['deep-blue', 'deep-gray', 'weeks']},
    'urgent': {         # 紧迫·热点  primary #C4551B 橙
        'label': '紧迫·热点', 'primary': (196, 85, 27),
        'rank': ['stout', 'peak', 'black']},
    'elegant': {        # 克制·美学  primary #8A7B5C 金棕
        'label': '克制·美学', 'primary': (138, 123, 92),
        'rank': ['struzan', 'moss', 'pardee']},
}


def list_styles():
    """打印 10 种风格一览（v3.3.0 cover_styles.py __main__ 行为）。"""
    for k, v in DESIGNER_STYLES.items():
        print(f"  {k:12s}  {v['name']:16s}  {v['desc']}")


if __name__ == '__main__':
    list_styles()
