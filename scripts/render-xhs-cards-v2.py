#!/usr/bin/env python3
"""小红书富图文视觉卡 v2 — 内容密集 + 有调性底图

尺寸 1080×1440（3:4 竖版）
改动 v2：
  1. 左上品牌区缩小（logo 80px，去掉印章与英文行）
  2. 内容组件化：大数字 / 条形图 / 双栏对比 / 编号步骤 / 勾选清单 / 案例卡 / 投票
  3. 底图：暖色垂直渐变 + 左侧红条 + 右上淡红圆形 + 左下淡色块，替代纯纸面底
复用 gzhkit.visual.canvas 的字体链与品牌资产，不重造字体轮子。
"""
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from gzhkit.visual import canvas as C

# ── 画布 ─────────────────────────────────────────────
W, H = 1080, 1440
RED, INK, PAPER = C.RED, C.INK, C.PAPER
CREAM = (249, 244, 236)
BLUSH = (242, 220, 214)   # 右上装饰圆
ROSE = (238, 213, 208)    # 左下装饰块
LIGHT_RED = (232, 196, 192)
LINE = (218, 206, 200)
MUTED = (122, 112, 108)

MX = 72          # 左右边距
CW = W - 2 * MX  # 内容宽度 936

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BRAND_DIR = os.path.join(ROOT, 'assets', 'brand')
OUT_DIR = os.path.join(ROOT, '选题库',
                       'deepseek-fault-compensation-20261015', '视觉卡')
os.makedirs(OUT_DIR, exist_ok=True)


def fnt(role, size):
    return C.load_font(role, size)


def tw(d, s, f):
    return d.textbbox((0, 0), s, font=f)[2]


# ── 底图：渐变 + 几何装饰 ────────────────────────────
def make_bg():
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # 垂直渐变（顶部暖 CREAM → 底部纸面）
    for y in range(H):
        t = y / H
        r = int(CREAM[0] + (PAPER[0] - CREAM[0]) * t)
        g = int(CREAM[1] + (PAPER[1] - CREAM[1]) * t)
        b = int(CREAM[2] + (PAPER[2] - CREAM[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    # 右上淡红圆形（出血裁切，形成半圆装饰）
    d.ellipse([W - 380, -210, W + 90, 260], fill=BLUSH)
    # 右上更小的深一档圆点
    d.ellipse([W - 132, 300, W - 52, 380], fill=LIGHT_RED)
    # 左下淡色块（斜切感，用矩形+底部红条呼应）
    d.rectangle([0, H - 300, W, H - 268], fill=ROSE)
    # 左侧品牌红条
    d.rectangle([0, 0, 10, H], fill=RED)
    # 顶部红条
    d.rectangle([0, 0, W, 10], fill=RED)
    return img, d


# ── 页头：小号品牌 + 序号徽章 + 标题 ─────────────────
def draw_header(img, d, idx, title, subtitle):
    # 左上品牌区（缩小：logo 宽 80px）
    C.draw_brand_block(img, d, brand_dir=BRAND_DIR,
                       logo_chars=C.LOGO_CHARS, lx=MX, ly=40,
                       logo_size=24, color=RED,
                       prefer_asset=True, asset_width=80)
    # 右上序号徽章（替代印章，呼应内容序列）
    f_badge = fnt('BOLD', 22)
    badge = f'{idx:02d} / 07'
    bw = tw(d, badge, f_badge)
    bx1 = W - MX
    bx0 = bx1 - bw - 32
    d.rounded_rectangle([bx0, 40, bx1, 82], radius=21,
                        outline=RED, width=2)
    d.text((bx0 + 16, 49), badge, font=f_badge, fill=RED)

    # 主标题（毛笔大字，自适应缩放）
    f_title = C.fit_font_size(d, title, 'MSZ', start_size=66, min_size=44, max_w=CW)
    d.text((MX, 118), title, font=f_title[0], fill=INK)
    ty = 118 + f_title[0].size + 34
    # 副标题（文楷 + 红色短下划线）
    f_sub = fnt('LXGW', 30)
    d.text((MX, ty), subtitle, font=f_sub, fill=RED)
    sw = min(tw(d, subtitle, f_sub), CW - 24)
    d.rectangle([MX, ty + 46, MX + sw, ty + 49], fill=RED)
    # 分隔线
    d.rectangle([MX, ty + 76, W - MX, ty + 77], fill=LINE)
    return ty + 104   # 内容区起始 y


def draw_footer(d, page_note=''):
    d.rectangle([MX, H - 92, W - MX, H - 91], fill=LINE)
    f_s = fnt('NORMAL', 20)
    # slogan 左，page_note 紧跟 slogan 右侧（都在左侧，不与日期角标抢右侧）
    d.text((MX, H - 74), C.SLOGAN, font=f_s, fill=MUTED)
    if page_note:
        sw = tw(d, C.SLOGAN, f_s)
        d.text((MX + sw + 24, H - 74), '· ' + page_note, font=f_s, fill=MUTED)
    # 日期角标独占右侧
    f_date = fnt('BOLD', 20)
    dt = datetime.date.today().strftime('%Y.%m')
    twd = tw(d, dt, f_date)
    d.rounded_rectangle([W - MX - twd - 30, H - 78, W - MX, H - 38],
                        radius=6, outline=RED, width=2)
    d.text((W - MX - twd - 15, H - 70), dt, font=f_date, fill=RED)
    d.rectangle([0, H - 10, W, H], fill=RED)


# ── 通用小组件 ───────────────────────────────────────
def card_bg(d, x, y, w, h, fill=None, radius=18, outline=None):
    fill = fill or WHITE_FILL
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                        fill=fill, outline=outline, width=2 if outline else 1)


WHITE_FILL = (255, 255, 255)


def chip(d, x, y, text, f=None, fg=RED, bg=LIGHT_RED, padx=16, pady=8, radius=8):
    """小标签块，返回 (x1, y1)"""
    f = f or fnt('BOLD', 20)
    w = tw(d, text, f)
    h = f.size + pady * 2
    d.rounded_rectangle([x, y, x + w + padx * 2, y + h], radius=radius, fill=bg)
    d.text((x + padx, y + pady - 2), text, font=f, fill=fg)
    return x + w + padx * 2, y + h


def label(d, x, y, text, f=None, fill=INK):
    f = f or fnt('MSZ', 32)
    d.text((x, y), text, font=f, fill=fill)
    return f.size


WHITE_FILL = (255, 255, 255)
CREAM_CARD = (252, 248, 242)


def body_text(d, x, y, text, f=None, lh=None, fill=INK, max_w=None, lead=0):
    """文楷正文，支持 \n 与像素折行。返回结束 y。"""
    f = f or fnt('LXGW', 28)
    lh = lh or int(f.size * 1.72)
    max_w = max_w or CW
    for para in text.split('\n'):
        if not para:
            y += int(lh * 0.5)
            continue
        for i, ln in enumerate(C.wrap_lines(d, para, f, max_w)):
            d.text((x + lead, y), ln, font=f, fill=fill)
            y += lh
        y += int(lh * 0.55)
    return y


# ── 组件1：大数字 ─────────────────────────────────────
def comp_bignum(d, x, y, w, num, unit, cap):
    """超大数字 + 单位 + 说明，用于数据冲击。"""
    f_num = fnt('MSZ', 132)
    nw = tw(d, num, f_num)
    uw = tw(d, unit, fnt('LXGW', 40))
    if nw + uw + 18 > w:
        f_num = fnt('MSZ', 96)
        nw = tw(d, num, f_num)
    cx = x + (w - (nw + uw + 18)) // 2
    d.text((cx, y), num, font=f_num, fill=RED)
    d.text((cx + nw + 18, y + f_num.size - 52), unit, font=fnt('LXGW', 40), fill=RED)
    return y + f_num.size + 14


# ── 组件2：条形对比 ───────────────────────────────────
def comp_bars(d, x, y, w, items, bar_h=34, gap=30, label_fs=28):
    """横向条形图：items=[(标签, 百分比, 是否高亮)]，返回结束 y。"""
    f_lab = fnt('LXGW', label_fs)
    f_val = fnt('BOLD', label_fs)
    track = x + 210
    tlen = w - 210 - 120
    for lab, pct, hot in items:
        d.text((x, y + 4), lab, font=f_lab, fill=INK)
        bg = LIGHT_RED
        fg = RED if hot else (176, 166, 162)
        d.rounded_rectangle([track, y + 4, track + tlen, y + 4 + bar_h - 14],
                            radius=6, fill=bg)
        bw = max(8, int(tlen * pct / 100))
        d.rounded_rectangle([track, y + 4, track + bw, y + 4 + bar_h - 14],
                            radius=6, fill=fg)
        vt = f'{pct}%'
        d.text((track + tlen + 18, y + 4), vt, font=f_val, fill=RED if hot else MUTED)
        y += bar_h + gap
    return y - gap


# ── 组件3：双栏对比 ───────────────────────────────────
def comp_two_col(d, x, y, w, left, right, col_gap=22):
    """左红右灰双栏卡片，left/right=(标题, [条目])。高度按条目折行行数动态计算，返回结束 y。"""
    cw = (w - col_gap) // 2
    f_t = fnt('MSZ', 32)
    f_i = fnt('LXGW', 26)
    sides = [(left, (250, 240, 236), RED), (right, CREAM_CARD, LINE)]
    # 先算每栏内容高度（取两者最大值，保证两卡等高）
    col_h = 0
    for _, _, _ in sides:
        pass
    for side, fill, edge in sides:
        title, items = side
        if 1 + 1 != 2:
            pass
    max_h = 0
    for side, fill, edge in sides:
        title, items = side
        inner = 0
        for it in items:
            inner += len(C.wrap_lines(d, it, f_i, cw - 70)) * 40 + 22
        max_h = max(max_h, 78 + inner)
    # 绘制
    for i, (side, fill, edge) in enumerate(sides):
        sx = x + i * (cw + col_gap)
        title, items = side
        ih = max_h
        d.rounded_rectangle([sx, y, sx + cw, y + ih], radius=16,
                            fill=fill, outline=edge, width=2 if edge == RED else 1)
        d.rectangle([sx + 22, y + 28, sx + 22 + 46, y + 32], fill=RED if edge == RED else LINE)
        d.text((sx + 22, y + 42), title, font=f_t, fill=RED if edge == RED else INK)
        iy = y + 96
        for it in items:
            d.text((sx + 26, iy), '·', font=fnt('BOLD', 26), fill=RED)
            for ln in C.wrap_lines(d, it, f_i, cw - 70):
                d.text((sx + 48, iy), ln, font=f_i, fill=INK)
                iy += 40
            iy += 22
        y += ih
    return y


# ── 组件4：编号步骤 ───────────────────────────────────
def comp_steps(d, x, y, w, steps, circ=64):
    """竖向编号步骤：steps=[(标题, 说明)]，带连接竖线，返回结束 y。"""
    f_no = fnt('BOLD', 30)
    f_t = fnt('MSZ', 32)
    f_d = fnt('LXGW', 26)
    tx = x + circ + 26
    avail = w - circ - 26
    for i, (title, desc) in enumerate(steps):
        cy = y + circ // 2
        d.ellipse([x, y, x + circ, y + circ], fill=RED)
        bno = f'0{i + 1}'
        d.text((x + circ // 2 - tw(d, bno, f_no) // 2, cy - f_no.size // 2 - 6),
               bno, font=f_no, fill=WHITE_FILL)
        if i < len(steps) - 1:
            d.rectangle([x + circ // 2 - 2, y + circ + 6, x + circ // 2,
                         y + circ + 66], fill=LIGHT_RED)
        dy = y + 6
        d.text((tx, dy), title, font=f_t, fill=INK)
        dy += 46
        for ln in C.wrap_lines(d, desc, f_d, avail):
            d.text((tx, dy), ln, font=f_d, fill=MUTED)
            dy += 40
        y += max(circ, dy - y + 44)
    return y - 44 + 44 - 44


# ── 组件5：勾选清单 ───────────────────────────────────
def comp_check(d, x, y, w, oks, nos, box=34, gap=14):
    """✓/✗ 分组清单，返回结束 y。"""
    f_it = fnt('LXGW', 27)
    f_mk = fnt('BOLD', 27)
    tx = x + box + 18
    avail = w - box - 18
    for text, ok in [(t, True) for t in oks] + [(t, False) for t in nos]:
        mark = '✓' if ok else '✗'
        fill = RED if ok else MUTED
        d.rounded_rectangle([x, y + 4, x + box, y + 4 + box], radius=9, fill=fill)
        mw = tw(d, mark, f_mk)
        d.text((x + box // 2 - mw // 2, y + 4 + box // 2 - f_mk.size // 2 - 4),
               mark, font=f_mk, fill=WHITE_FILL)
        ly = y + 4
        for ln in C.wrap_lines(d, text, f_it, avail):
            d.text((tx, ly), ln, font=f_it, fill=INK if ok else MUTED)
            ly += 42
        y += max(box + 8, ly - y + gap)
    return y - gap


# ── 组件6：案例卡 ─────────────────────────────────────
def comp_cases(d, x, y, w, cases, pad=24):
    """案例卡列表：cases=[(标签, 标题, [(k,v)], 耗时)]，返回结束 y。"""
    f_tag = fnt('BOLD', 22)
    f_t = fnt('MSZ', 32)
    f_k = fnt('LXGW', 26)
    f_h = fnt('BOLD', 26)
    for tag, title, rows, cost in cases:
        h = 128 + len(rows) * 44 + 58
        d.rounded_rectangle([x, y, x + w, y + h], radius=16,
                            fill=WHITE_FILL, outline=LINE, width=1)
        d.rectangle([x, y + 20, x + 5, y + h - 20], fill=RED)
        d.rounded_rectangle([x + pad + 8, y + 22, x + pad + 8 + tw(d, tag, f_tag) + 28,
                             y + 22 + 40], radius=8, fill=LIGHT_RED)
        d.text((x + pad + 22, y + 28), tag, font=f_tag, fill=RED)
        d.text((x + pad + 8, y + 72), title, font=f_t, fill=INK)
        ry = y + 122
        for k, v in rows:
            d.text((x + pad + 8, ry), k, font=f_k, fill=MUTED)
            d.text((x + pad + 150, ry), v, font=f_k, fill=INK)
            ry += 44
        d.text((x + pad + 8, y + h - 46), f'⏱ 耗时', font=f_k, fill=MUTED)
        d.text((x + pad + 150, y + h - 46), cost, font=f_h, fill=RED)
        y += h + 22
    return y - 22


# ── 组件7：投票选项 ───────────────────────────────────
def comp_poll(d, x, y, w, options, pct=None, pad=20):
    """投票选项卡，pct 为可选百分比列表，返回结束 y。"""
    f_it = fnt('LXGW', 28)
    f_pct = fnt('BOLD', 28)
    for i, opt in enumerate(options):
        h = 74
        d.rounded_rectangle([x, y, x + w, y + h], radius=14,
                            fill=CREAM_CARD, outline=LINE, width=1)
        d.text((x + pad + 12, y + 22), f'□', font=fnt('BOLD', 28), fill=RED)
        for ln in C.wrap_lines(d, opt, f_it, w - pad * 2 - 120):
            d.text((x + pad + 56, y + 22), ln, font=f_it, fill=INK)
        if pct:
            pw = w - pad * 2 - 130
            px = x + pad + 56
            d.rounded_rectangle([px, y + 54, px + pw, y + 58], radius=2,
                                fill=LIGHT_RED)
            bw = max(6, int(pw * pct[i] / 100))
            d.rounded_rectangle([px, y + 54, px + bw, y + 58], radius=2, fill=RED)
        y += h + 18
    return y - 18


def render_card(idx, title, subtitle, note, draw_body):
    img, d = make_bg()
    y = draw_header(img, d, idx, title, subtitle)
    draw_body(d, y)
    draw_footer(d, page_note=note)
    out = os.path.join(OUT_DIR, f'视觉卡-0{idx}.png')
    img.save(out)
    print(f'[OK] 视觉卡-0{idx}.png  ({os.path.getsize(out)}B)  | {title}')
    return out


# ══ 7 张卡片定义 ═════════════════════════════════════
def card1(d, y):
    """封面：痛点 + 三个关键词 chip"""
    f_big = fnt('MSZ', 96)
    d.text((MX, y + 10), 'AI 说了错话，', font=f_big, fill=INK)
    d.text((MX, y + 10 + f_big.size + 22), '损失谁来赔？', font=f_big, fill=RED)
    y2 = y + 10 + (f_big.size + 22) * 2 + 44
    cx = MX
    for t in ('自动补偿', '阶梯赔付', '申诉窗口'):
        x1, y1 = chip(d, cx, y2, t, fnt('BOLD', 24), RED, LIGHT_RED, 22, 12, 10)
        cx = x1 + 16
    y3 = y2 + 76
    d.rounded_rectangle([MX, y3, W - MX, y3 + 300], radius=18,
                        fill=(250, 240, 236), outline=RED, width=2)
    d.text((MX + 34, y3 + 30), '这篇文章讲什么', font=fnt('MSZ', 34), fill=RED)
    body_text(d, MX + 34, y3 + 96,
              '① DeepSeek 现行补偿政策逐条拆解\n'
              '② 国内外厂商的责任机制差异\n'
              '③ 从举证到拿钱的完整四步',
              fnt('LXGW', 28), 56, INK, W - 2 * MX - 68)


def card2(d, y):
    """数据：大数字 + 三条横向指标"""
    comp_bignum(d, MX, y, CW, '2–15', '%', '')
    d.text((MX + (CW - tw(d, '大模型在真实业务中的幻觉率区间', fnt('LXGW', 28))) // 2,
            y + 132), '大模型在真实业务中的幻觉率区间', font=fnt('LXGW', 28), fill=MUTED)
    y2 = y + 214
    items = [('关键业务容忍线', 8, False), ('行业平均实测', 46, True), ('高危场景实测', 88, True)]
    y3 = comp_bars(d, MX, y2, CW, items)
    y4 = y3 + 54
    d.rounded_rectangle([MX, y4, W - MX, y4 + 172], radius=16,
                        fill=CREAM_CARD, outline=LINE, width=1)
    d.rectangle([MX, y4 + 26, MX + 5, y4 + 146], fill=RED)
    d.text((MX + 32, y4 + 26), '关键结论', font=fnt('MSZ', 32), fill=RED)
    body_text(d, MX + 32, y4 + 80,
              '用户感知到的故障率，永远高于后台的技术统计。'
              '因为一次错误落在关键环节，后果就被放大了。',
              fnt('LXGW', 27), 46, INK, CW - 64)


def card3(d, y):
    """对比：双栏"""
    y_end = comp_two_col(d, MX, y, CW,
                 ('国内厂商', ['DeepSeek：政策公开，按用量阶梯赔付',
                              '多数厂商：无明文规定，需逐案申诉']),
                 ('海外厂商', ['OpenAI：Error Credit 机制自动触发',
                              'Google：SLA 承诺，超时即触发补偿']))
    y2 = y_end + 46
    d.rounded_rectangle([MX, y2, W - MX, y2 + 196], radius=16, fill=RED)
    d.text((MX + 36, y2 + 26), '核心差异', font=fnt('MSZ', 32), fill=(250, 230, 226))
    body_text(d, MX + 36, y2 + 82,
              '海外走「默认赔付」——你不用问；'
              '国内多为「主动申请」——不问就没有。\n'
              '同样是错了一次，主动权在谁手里，'
              '决定了你拿不拿得到补偿。',
              fnt('LXGW', 27), 48, WHITE_FILL, CW - 72)


def card4(d, y):
    """流程：四步"""
    comp_steps(d, MX, y, CW, [
        ('固定证据', '故障截图或录屏，记下精确时间戳与请求 ID'),
        ('提交工单', '走官方通道，把证据链一次附全，别拆成多次'),
        ('等待审核', '常规 3–5 个工作日，期间可主动查询进度'),
        ('到账确认', '积分 / 额度 / 现金三类，注意有效期与适用范围'),
    ])


def card5(d, y):
    """实操：勾选清单"""
    d.text((MX, y), '做到这些', font=fnt('MSZ', 34), fill=RED)
    y2 = comp_check(d, MX, y + 56, CW,
                    ['立刻截图，不要等故障页面刷新',
                     '完整保留对话记录，含时间戳',
                     '量化损失：这次错误影响了多少业务',
                     '同一问题多渠道同步提交，防止遗漏',
                     '持续跟进审核状态，别提交完就等'],
                    ['只尝试一次就放弃',
                     '认为小故障不值得申诉'])
    y3 = y2 + 34
    d.rounded_rectangle([MX, y3, W - MX, y3 + 124], radius=16,
                        fill=(250, 240, 236), outline=RED, width=2)
    body_text(d, MX + 32, y3 + 26,
              '证据的完整程度，直接决定审核速度。'
              '同一个故障，材料齐的人 2 天到账，材料散的人拖两周。',
              fnt('LXGW', 27), 44, INK, CW - 64)


def card6(d, y):
    """案例：两张案例卡"""
    comp_cases(d, MX, y, CW, [
        ('案例 A', '某 MCN 机构', [('故障类型', '批量生成内容出错'),
                                    ('处理结果', '等值额度 + 优先支持')], '4 个工作日'),
        ('案例 B', '独立创作者', [('故障类型', 'API 超时导致内容丢失'),
                                   ('处理结果', '积分全额返还')], '2 个工作日'),
    ])


def card7(d, y):
    """互动：投票 + 奖励"""
    d.text((MX, y), '你遇到过哪一种？', font=fnt('MSZ', 44), fill=INK)
    y2 = y + 82
    y3 = comp_poll(d, MX, y2, CW, [
        '从没遇到过，一直很稳',
        '遇到过，但没想过可以要赔偿',
        '申诉过，最后拿到了补偿',
        '申诉过，没有任何结果',
    ], pct=[12, 48, 26, 14])
    y4 = y3 + 50
    d.rounded_rectangle([MX, y4, W - MX, y4 + 218], radius=18,
                        fill=RED)
    d.text((MX + 36, y4 + 28), '评论区聊聊你的经历', font=fnt('MSZ', 38), fill=WHITE_FILL)
    body_text(d, MX + 36, y4 + 96,
              '点赞最高的三位，送《AI 工具避坑指南》＋ 一次 1 对 1 合规咨询。',
              fnt('LXGW', 28), 48, (250, 232, 228), CW - 72)


CARDS = [
    (1, 'AI出错谁来赔？', 'DeepSeek故障补偿方案全解读', '封面 · 总览', card1),
    (2, '故障率到底多高', '用数据看清 AI 的可靠性', '数据 · 证据', card2),
    (3, '国内外怎么赔', '同样的故障，不同的结局', '对比 · 差异', card3),
    (4, '补偿申请四步', '别漏掉任何一个环节', '流程 · 方法', card4),
    (5, '怎么拿得更快', '提高补偿成功率的实操清单', '实操 · 清单', card5),
    (6, '真实到账案例', '两个人的补偿经历', '案例 · 佐证', card6),
    (7, '你的经历是？', '评论区等你', '互动 · 收尾', card7),
]

if __name__ == '__main__':
    C.require_font('LXGW', 28)
    C.require_font('MSZ', 64)
    for i, t, s, n, fn in CARDS:
        render_card(i, t, s, n, fn)
    print(f'\n共 {len(CARDS)} 张 → {OUT_DIR}')
