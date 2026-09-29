"""封面风格参数表 · 10 种预设

从 hai-bao-she-ji/references/artist-styles.md 的 7 位设计师风格提取，
加上 3 个原有渐变预设。每种风格定义 PIL 可消费的参数：
  bg        背景类型 (gradient/solid) + 颜色
  accent    强调色（竖条/底部线/徽章）
  text_*    标题/副标题/清单文字色
  bar_*     强调条位置+宽度
  title_*   标题对齐方式
  badge_*   日期徽章形状
  bottom_*  底部强调线开关
  deco      装饰元素 (none/corners/frame)

用法:
  from cover_styles import DESIGNER_STYLES
  s = DESIGNER_STYLES['moss']
  # s['bg']['type'] == 'solid', s['accent'] == (200,50,50), ...
"""

DESIGNER_STYLES = {
    # ── 7 位设计师风格（从 artist-styles.md 提取）──────────
    'stout': {
        'name': 'Tyler Stout',
        'desc': '复古科幻·高饱和撞色',
        'bg': {'type': 'gradient', 'top': (10, 10, 40), 'bottom': (40, 10, 60)},
        'accent': (255, 100, 50),
        'text_fill': (255, 255, 255),
        'sub_fill': (200, 180, 255),
        'list_fill': (180, 220, 255),
        'bar_pos': 'left', 'bar_w': 6,
        'title_align': 'left',
        'badge_shape': 'rounded', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'corners',
    },
    'moss': {
        'name': 'Olly Moss',
        'desc': '极简负空间·奶油底+红黑',
        'bg': {'type': 'solid', 'color': (252, 248, 240)},
        'accent': (200, 50, 50),
        'text_fill': (30, 30, 30),
        'sub_fill': (80, 80, 80),
        'list_fill': (100, 100, 100),
        'bar_pos': 'left', 'bar_w': 3,
        'title_align': 'left',
        'badge_shape': 'none',
        'bottom_line': False,
        'deco': 'none',
    },
    'ansin': {
        'name': 'Martin Ansin',
        'desc': '黑白高对比·对称构图',
        'bg': {'type': 'gradient', 'top': (15, 15, 15), 'bottom': (35, 35, 35)},
        'accent': (180, 30, 30),
        'text_fill': (255, 255, 255),
        'sub_fill': (200, 200, 200),
        'list_fill': (180, 180, 180),
        'bar_pos': 'center', 'bar_w': 2,
        'title_align': 'center',
        'badge_shape': 'square', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'frame',
    },
    'struzan': {
        'name': 'Drew Struzan',
        'desc': '暖调油画·琥珀金',
        'bg': {'type': 'gradient', 'top': (60, 45, 30), 'bottom': (30, 25, 20)},
        'accent': (218, 165, 50),
        'text_fill': (255, 245, 230),
        'sub_fill': (220, 200, 180),
        'list_fill': (200, 185, 170),
        'bar_pos': 'left', 'bar_w': 4,
        'title_align': 'left',
        'badge_shape': 'rounded', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'none',
    },
    'pardee': {
        'name': 'Alex Pardee',
        'desc': '极简恐怖·白底黑字',
        'bg': {'type': 'solid', 'color': (245, 240, 235)},
        'accent': (30, 30, 30),
        'text_fill': (30, 30, 30),
        'sub_fill': (80, 80, 80),
        'list_fill': (100, 100, 100),
        'bar_pos': 'left', 'bar_w': 2,
        'title_align': 'left',
        'badge_shape': 'none',
        'bottom_line': False,
        'deco': 'none',
    },
    'peak': {
        'name': 'Bob Peak',
        'desc': '装饰艺术·几何撞色',
        'bg': {'type': 'gradient', 'top': (30, 20, 60), 'bottom': (60, 30, 20)},
        'accent': (255, 200, 50),
        'text_fill': (255, 255, 255),
        'sub_fill': (255, 230, 200),
        'list_fill': (220, 220, 240),
        'bar_pos': 'right', 'bar_w': 8,
        'title_align': 'left',
        'badge_shape': 'square', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'corners',
    },
    'weeks': {
        'name': 'Ken Taylor',
        'desc': '柔和渐变·蓝紫调',
        'bg': {'type': 'gradient', 'top': (25, 30, 55), 'bottom': (45, 35, 70)},
        'accent': (140, 180, 230),
        'text_fill': (240, 240, 250),
        'sub_fill': (200, 200, 230),
        'list_fill': (190, 200, 230),
        'bar_pos': 'left', 'bar_w': 4,
        'title_align': 'left',
        'badge_shape': 'rounded', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'none',
    },
    # ── 3 个原有渐变预设（向后兼容）──────────────────────
    'deep-blue': {
        'name': '深海蓝（默认）',
        'desc': '深色渐变·金色强调',
        'bg': {'type': 'gradient', 'top': (26, 26, 46), 'bottom': (15, 32, 62)},
        'accent': (245, 197, 66),
        'text_fill': (255, 255, 255),
        'sub_fill': (220, 220, 220),
        'list_fill': (210, 210, 220),
        'bar_pos': 'left', 'bar_w': 5,
        'title_align': 'left',
        'badge_shape': 'rounded', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'none',
    },
    'deep-gray': {
        'name': '石墨灰',
        'desc': '深灰渐变·蓝色强调',
        'bg': {'type': 'gradient', 'top': (45, 45, 48), 'bottom': (24, 24, 27)},
        'accent': (74, 144, 217),
        'text_fill': (240, 240, 240),
        'sub_fill': (200, 200, 200),
        'list_fill': (190, 190, 200),
        'bar_pos': 'left', 'bar_w': 5,
        'title_align': 'left',
        'badge_shape': 'rounded', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'none',
    },
    'black': {
        'name': '近黑',
        'desc': '近黑渐变·红色强调',
        'bg': {'type': 'gradient', 'top': (15, 15, 18), 'bottom': (30, 30, 35)},
        'accent': (233, 69, 96),
        'text_fill': (255, 255, 255),
        'sub_fill': (220, 220, 220),
        'list_fill': (210, 210, 220),
        'bar_pos': 'left', 'bar_w': 5,
        'title_align': 'left',
        'badge_shape': 'rounded', 'badge_color': 'accent',
        'bottom_line': True,
        'deco': 'none',
    },
}

# ── 调性 → 风格推荐映射 ──────────────────────────────────
# 调性名与 gzh-typeset.py 融合版 TONES 完全一致（5 档），
# 保证「封面强调色 = 正文排版主色」，封面与内文是一套视觉。
# 每档第 1 推荐 = 主色最接近该调性 primary 的风格。
TONE_TO_STYLE = {
    'authoritative': {  # 权威·合规  primary #B03A2E 砖红
        'label': '权威·合规', 'primary': (176, 58, 46),
        'rank': ['black', 'ansin', 'deep-blue']},
    '🙂 friendly': {     # 亲和·教程  primary #2E8B8B 青
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
# 修正 friendly 的 key（避免 emoji 污染，保留纯 key 供代码用）
TONE_TO_STYLE['friendly'] = TONE_TO_STYLE.pop('🙂 friendly')


def list_styles():
    """列出所有风格名+描述。"""
    for k, v in DESIGNER_STYLES.items():
        print(f"  {k:12s}  {v['name']:16s}  {v['desc']}")


if __name__ == '__main__':
    list_styles()
