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
    # ── 7 位设计师风格（浅色系 2026-10-16 改版）──────────
    'stout': _style(
        'Tyler Stout', '浅暖底·橙红撞色',
        _grad((252, 245, 238), (245, 235, 225)),
        (220, 80, 40), (40, 30, 25), (120, 90, 70), (100, 80, 60),
        bar_w=6, deco='corners'),
    'moss': _style(
        'Olly Moss', '奶油底·红黑极简',
        _solid((252, 248, 240)),
        (200, 50, 50), (30, 30, 30), (80, 80, 80), (100, 100, 100),
        bar_w=3, badge_shape='none', bottom_line=False),
    'ansin': _style(
        'Martin Ansin', '浅灰底·红黑高对比',
        _grad((245, 245, 248), (235, 235, 240)),
        (180, 30, 30), (30, 30, 30), (80, 80, 80), (100, 100, 100),
        bar_pos='center', bar_w=2, title_align='center',
        badge_shape='square', deco='frame'),
    'struzan': _style(
        'Drew Struzan', '浅琥珀底·金棕调',
        _grad((252, 246, 232), (245, 238, 220)),
        (180, 130, 40), (50, 40, 30), (120, 100, 70), (100, 90, 70),
        bar_w=4),
    'pardee': _style(
        'Alex Pardee', '白底·黑字极简',
        _solid((245, 240, 235)),
        (30, 30, 30), (30, 30, 30), (80, 80, 80), (100, 100, 100),
        bar_w=2, badge_shape='none', bottom_line=False),
    'peak': _style(
        'Bob Peak', '浅紫底·几何撞色',
        _grad((248, 244, 252), (240, 234, 248)),
        (160, 100, 200), (40, 35, 50), (100, 90, 120), (90, 80, 110),
        bar_pos='right', bar_w=8, badge_shape='square', deco='corners'),
    'weeks': _style(
        'Ken Taylor', '浅蓝紫底·柔和',
        _grad((240, 244, 252), (232, 238, 250)),
        (80, 120, 180), (30, 40, 60), (80, 90, 120), (70, 85, 110),
        bar_w=4),
    # ── 3 个原有渐变预设（浅色系改版）─────────────────────
    'deep-blue': _style(
        '浅蓝（默认）', '浅蓝渐变·蓝强调',
        _grad((238, 242, 252), (225, 232, 248)),
        (47, 93, 138), (30, 40, 60), (80, 90, 110), (70, 85, 105)),
    'deep-gray': _style(
        '浅灰', '浅灰渐变·蓝强调',
        _grad((245, 245, 248), (235, 235, 240)),
        (74, 144, 217), (30, 35, 40), (80, 85, 90), (70, 80, 85)),
    'black': _style(
        '浅暖灰', '浅暖灰·红强调',
        _grad((248, 245, 242), (240, 236, 232)),
        (194, 69, 60), (40, 35, 30), (110, 95, 85), (100, 90, 80)),
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
