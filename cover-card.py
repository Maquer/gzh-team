#!/usr/bin/env python3
"""公众号封面图生成器（带标题 900x383）· 确定性 PIL，零 AI 生图依赖

为什么不用 AI 生图：sensenova/即梦 渲染中文必出错字与重复行（实测），
  H11 门禁（无中文错字）过不了。文字一律 PIL 程序化绘制。
（关注型尾图已于 09-26 舍弃，统一改用灰底 tail-v4 补字品牌名那套。）

规范依据：
  docs/visual/head-cover-spec.md v1.0  封面图 900x383 (2.35:1)，安全区居中 ±15%
  命名区分：封面图=带标题 900x383（本脚本）；首图=关注引导 450x200（brand-font-schemes.py）
  docs/visual/brand-colors.md    v1.1  品牌红 #C2453C + 黑/白（v1.1 覆盖 v1.0 深蓝暂定）

用法:
  python3 cover-card.py --title "实测 5 款 AI 写作工具，我放弃了 4 个" \
      --sub "6 个真实场景 · 只讲我用得下去的那一个" --date 2026.09
  python3 cover-card.py --title "..." --out-dir assets/out
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont

# ── 品牌常量（brand-colors.md v1.1）───────────────────────
BRAND = '弎水野记'
SLOGAN = '野路实测，笔记为证：留下能用的'
RED = (194, 69, 60)          # #C2453C 主色
INK = (51, 51, 51)           # #333333 文字
PAPER = (245, 245, 245)      # #F5F5F5 背景
WHITE = (255, 255, 255)
GREY = (140, 140, 140)

FONT_B = '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc'
FONT_R = '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc'
FONT_SERIF = '/usr/share/fonts/noto/NotoSerifCJK-Bold.ttc'
FONT_MSZ = '/usr/share/fonts/noto/MaShanZheng-Regular.ttf'   # 毛笔楷书
FONT_LXGW = '/usr/share/fonts/noto/LXGWWenKai-Regular.ttf'  # 霞鹜文楷

# 品牌名补字组合：弎水=文楷，野记=毛笔（毛笔体缺「弎」，故逐字混排）
FONT_MAP = {'Serif': FONT_SERIF, 'Sans': FONT_B, 'MSZ': FONT_MSZ, 'LXGW': FONT_LXGW}
LOGO_A = [('弎', 'LXGW'), ('水', 'LXGW'), ('野', 'MSZ'), ('记', 'MSZ')]

HEAD_W, HEAD_H = 900, 383     # 2.35:1 头条封面


def font(path, size, index=2):
    """index=2 = SC 字面（0=JP 1=KR 2=SC）。缺字面时退回 0。"""
    try:
        f = ImageFont.truetype(path, size, index=index)
    except OSError:
        f = ImageFont.truetype(path, size, index=0)
    # 断言：字体真的覆盖这些汉字，禁止静默降级成豆腐块
    cmap = f.getmask('弎野记').getbbox()
    if cmap is None or cmap[2] - cmap[0] < 4:
        raise SystemExit(f'字体缺字: {path} index={index} 无法渲染 CJK')
    return f


def render_logo(size, logo, color):
    """渲染品牌名（补字组合），返回透明 RGBA 图（裁到内容）。
    挂在图上的属性（均相对裁剪后图左，供外部对齐）：
      .shu_x0              — 第 1 个字视觉左边界（横线左端）
      .shui_right          — 第 2 个字视觉右边界（横线右端）
      .yeji_x / .yeji_left — 第 3 个字视觉左边界（英文左端）
    视觉边界 = 2x 画布上 alpha>128 的列范围（缩放前测），误差 ≤0.5px。
    逐字分支：每个字单独渲染成位图（paste 不重光栅化，避开 FreeType
    subpixel hinting 随 y 小数变化导致的"测量与成品不一致"），在 2x
    超采样画布上把像素垂直中心钉在同一 cy，再 LANCZOS 缩回 1x。不超
    采样的话，1x 网格上各字像素高奇偶不同，整数舍入会让中心相差
    0.5~1px，30px 档肉眼可见。
    """
    yeji_left = shui_right = shu_x0 = None
    if isinstance(logo, str):
        fb = font(FONT_MAP[logo], size)
        bb = fb.getbbox(BRAND)
        im = Image.new('RGBA', (bb[2] - bb[0] + 8, size * 2 + 40), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.text((4 - bb[0], size + 20 - bb[1]), BRAND, font=fb, fill=color)
    else:
        gap, pad, ss = 6, 20, 2
        # ss=2 超采样：1x 网格上各字像素高奇偶不同，整数 py 会让中心在 cy
        # 上下各漂 0.5~1px（30px 档尤其明显）；放大到 2x 后高度全为偶数，
        # py 精确命中 cy，缩回 1x 由 LANCZOS 完成亚像素混合，四字中心一致。
        items = []
        for ch, fn in logo:
            try:
                fb = ImageFont.truetype(FONT_MAP[fn], size * ss, index=2)
            except OSError:
                fb = ImageFont.truetype(FONT_MAP[fn], size * ss, index=0)
            cell = Image.new('RGBA', (size * 3 * ss, size * 3 * ss), (0, 0, 0, 0))
            ImageDraw.Draw(cell).text((size * ss, size * ss), ch, font=fb, fill=color)
            items.append((ch, cell.crop(cell.getbbox())))
        H = size * 2 + 40
        W = sum(round(g.width / ss) for _, g in items) + \
            gap * (len(items) - 1) + pad * 2 + 2
        big = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
        cy = big.height / 2
        span = {}
        x = pad * ss
        for ch, g in items:
            px2 = int(x)
            py2 = int(round(cy - g.height / 2))
            big.paste(g, (px2, py2), g)
            # 同帧用 alpha>128 测视觉边界：LANCZOS 会让 alpha>0 的边缘扩散
            # 1~4px，直接记 paste 位置会与"肉眼看到的字边"错位
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
        # 按 logo 顺序取：横线覆盖前两个字，英文左端对齐第三个字。
        # 用索引而非字面量，避免把「ryon」误打成 ASCII "ryon" 导致静默失效。
        sps = list(span.values())
        if len(sps) >= 3:
            shu_x0 = sps[0][0]
            shui_right = sps[1][1]
            yeji_left = sps[2][0]
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


def measured(draw, text, fnt, max_w):
    """超宽自动缩字号，返回 (font, 是否缩过)。"""
    size = fnt.size
    while size > 18 and draw.textbbox((0, 0), text, font=fnt)[2] > max_w:
        size -= 2
        fnt = font(fnt.path, size, getattr(fnt, 'index', 2))
    return fnt, size != fnt.size


def wrap(draw, text, fnt, max_w):
    """折行（CJK 无空格），两行时按字数均衡切分，避免孤字。"""
    width = lambda s: draw.textbbox((0, 0), s, font=fnt)[2]
    if width(text) <= max_w:
        return [text]
    # 优先在分隔符处切；否则穷举所有切点，选「两行宽度最接近」的那个
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
    # 兜底：贪心折行
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


def cover(title, sub, date, out, seal=True):
    img = Image.new('RGB', (HEAD_W, HEAD_H), PAPER)
    d = ImageDraw.Draw(img)
    f_title = font(FONT_B, 56)
    f_sub = font(FONT_R, 22)
    f_date = font(FONT_B, 17)

    # 左侧品牌红条（装饰，面积 <20%）
    d.rectangle([0, 0, 10, HEAD_H], fill=RED)
    # 品牌标识区（左上，固定）——补字组合 + 弎水下方横线 + 英文在野记下方
    logo = render_logo(30, LOGO_A, RED)
    lx, ly = 56, 32
    img.paste(logo, (lx, ly), logo)
    # 横线左端=ryon字视觉左、右端=水字视觉右；英文左端=野字视觉左
    yeji_left = lx + getattr(logo, 'yeji_x', 0)
    shui_right = lx + getattr(logo, 'shui_right', yeji_left)
    shu_x0 = lx + getattr(logo, 'shu_x0', 0)
    f_en = font(FONT_R, 14)
    en_top = ly + logo.height + 3
    bbox = d.textbbox((yeji_left, en_top), 'SANSHUI YEJI', font=f_en, anchor='lt')
    en_mid = (bbox[1] + bbox[3]) / 2
    d.rectangle([shu_x0, int(en_mid), shui_right, int(en_mid) + 1], fill=RED)
    d.text((yeji_left, en_top), 'SANSHUI YEJI', font=f_en, fill=GREY, anchor='lt')

    # 品牌印章：程序化绘制 2x2 红印（弎水野记，右起竖读），避免裁切带白边
    # 品牌印章：优先贴真实红圆印章图（透明底）；缺图时退回程序化 2x2 红印
    side, sx, sy = 84, HEAD_W - 56 - 84, 28
    seal_img = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'assets', 'brand', 'seal-circle-84.png')
    if seal and os.path.exists(seal_img):
        img.paste(Image.open(seal_img), (sx, sy), Image.open(seal_img))
    elif seal:
        d.rectangle([sx, sy, sx + side, sy + side], fill=RED)
        f_seal = font(FONT_SERIF, 27)
        cell = side // 2
        # 右起竖读：弎(右上) 水(右下) 野(左上) 记(左下)
        d.rectangle([sx + cell + 6, sy + 6, sx + side - 6, sy + cell - 6], fill=WHITE)
        for ch, (cx, cy, fill) in [('野', (0, 0, WHITE)), ('弎', (1, 0, RED)),
                                   ('记', (0, 1, WHITE)), ('水', (1, 1, WHITE))]:
            bb = d.textbbox((0, 0), ch, font=f_seal)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            d.text((sx + cx * cell + (cell - cw) // 2 - bb[0],
                    sy + cy * cell + (cell - chh) // 2 - bb[1]),
                   ch, font=f_seal, fill=fill)
    # 注：印章为装饰性美术字，OCR 会误读（弎→國 水→杰）。跑 H11 门禁时须排除
    # 该 bbox：--exclude-box 值见 stderr 输出。--no-seal 可整块关掉。
    sys.stderr.write(f'[H11-EXCLUDE] seal bbox = {sx},0,{sx + side},{sy + side}\n')

    # 主标题（居中安全区内，<=2 行）
    max_w = int(HEAD_W * 0.70)
    f_title, _ = measured(d, title.replace('，', ' '), f_title, max_w)
    lines = wrap(d, title, f_title, max_w)
    lh = f_title.size + 12
    total = lh * len(lines)
    top = 104 if len(lines) <= 2 else 92
    y = top
    for ln in lines:
        w = d.textbbox((0, 0), ln, font=f_title)[2]
        d.text(((HEAD_W - w) // 2, y), ln, font=f_title, fill=INK)
        y += lh
    if len(lines) > 2:
        sys.stderr.write(f'[WARN] 标题折成 {len(lines)} 行，建议缩短\n')

    # 副标题
    if sub:
        f_sub, _ = measured(d, sub, f_sub, max_w)
        w = d.textbbox((0, 0), sub, font=f_sub)[2]
        d.text(((HEAD_W - w) // 2, y + 6), sub, font=f_sub, fill=(110, 110, 110))

    # 底部：品牌红细线 + 日期角标
    d.rectangle([56, HEAD_H - 74, HEAD_W - 56, HEAD_H - 73], fill=(215, 215, 215))
    d.text((56, HEAD_H - 56), SLOGAN, font=font(FONT_R, 16), fill=GREY)
    if date:
        dt = date
        w = d.textbbox((0, 0), dt, font=f_date)[2]
        d.rounded_rectangle([HEAD_W - 56 - w - 28, HEAD_H - 62,
                             HEAD_W - 56, HEAD_H - 30], radius=6, outline=RED, width=2)
        d.text((HEAD_W - 56 - w - 14, HEAD_H - 55), dt, font=f_date, fill=RED)
    img.save(out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='公众号封面图 PIL 生成器（带标题 900x383）')
    ap.add_argument('--title', default='实测 5 款 AI 写作工具，我放弃了 4 个')
    ap.add_argument('--sub', default='6 个真实场景 · 只留我用得下去的那个')
    ap.add_argument('--date', default='2026.09')
    ap.add_argument('--out-dir', default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'assets', 'out'))
    ap.add_argument('--no-seal', action='store_true', help='不画右上红印章')
    a = ap.parse_args()

    # ── 输入校验（红蓝军对抗测试修复 WS-1/WS-2/WS-3）──
    if not a.title.strip():
        sys.exit('[ERROR] --title 不能为空。')
    if len(a.title) > 40:
        sys.stderr.write(f'[WARN] 标题 {len(a.title)} 字过长，建议 ≤40 字，否则缩字号后不可读\n')
    if a.sub and len(a.sub) > 60:
        sys.stderr.write(f'[WARN] 副标题 {len(a.sub)} 字过长，建议 ≤60 字\n')
    # 检查标题含非 CJK/ASCII 字符（emoji 等）
    non_cjk = [ch for ch in a.title if ord(ch) > 0x9FFF and ord(ch) not in range(0x3000, 0x303F)]
    if non_cjk:
        sys.stderr.write(f'[WARN] 标题含 {len(non_cjk)} 个非 CJK 字符（emoji 等），'
                         f'可能渲染为豆腐块：{"".join(non_cjk[:5])}\n')

    os.makedirs(a.out_dir, exist_ok=True)
    stem = a.title[:12].replace(' ', '').replace('，', '')
    hp = os.path.join(a.out_dir, f'封面图-{stem}.png')
    print(cover(a.title, a.sub, a.date, hp, seal=not a.no_seal))
