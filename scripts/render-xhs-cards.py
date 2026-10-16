#!/usr/bin/env python3
"""生成小红书富图文视觉卡（7张，1080×1440 3:4竖版）。

复用 gzhkit.visual.canvas 的字体回退链、品牌块、印章、折行逻辑。
品牌色/字号/布局按小红书 3:4 竖版放大。
"""
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from gzhkit.visual import canvas as C

W, H = 1080, 1440
RED, INK, PAPER, GREY, HAIRLINE = C.RED, C.INK, C.PAPER, C.GREY, C.HAIRLINE

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), '..', 'gzh-team',
                       '选题库', 'deepseek-fault-compensation-20261015', '视觉卡')
os.makedirs(OUT_DIR, exist_ok=True)

BRAND_DIR = os.path.join(os.path.dirname(HERE), '..', 'gzh-team', 'assets', 'brand')
BRAND_DIR = os.path.abspath(BRAND_DIR)


def date_str():
    return datetime.date.today().strftime('%Y.%m')


def new_card():
    img = Image.new('RGB', (W, H), PAPER)
    return img, ImageDraw.Draw(img)


def wrap_block(d, text, fnt, x, y, max_w, line_h, fill=INK):
    """逐行折行绘制多行文本（保留换行符），返回结束 y。"""
    lines = text.split('\n')
    for ln in lines:
        for l in C.wrap_lines(d, ln.strip(), fnt, max_w):
            d.text((x, y), l, font=fnt, fill=fill)
            y += line_h
        y += line_h // 3  # 段间距
    return y


def draw_header(img, d, title, subtitle):
    # 顶部品牌红条
    d.rectangle([0, 0, W, 10], fill=RED)
    # 左上品牌块（贴标准 logo 图，缺失回退逐字渲染）
    C.draw_brand_block(img, d, brand_dir=BRAND_DIR,
                       logo_chars=C.LOGO_CHARS, lx=60, ly=48,
                       logo_size=36, color=RED, prefer_asset=True, asset_width=150)
    # 右上印章（程序化，右上区）
    C.draw_seal(img, d, brand_dir=BRAND_DIR, sx=W - 150, sy=44, side=90)
    # 主标题（毛笔大字）
    f_title = C.fit_font_size(d, title, 'MSZ', start_size=72, min_size=40, max_w=W - 160)
    d.text((80, 150), title, font=f_title[0], fill=INK)
    # 副标题（文楷 + 红下划线）
    f_sub = C.load_font('LXGW', 34)
    d.text((80, 240), subtitle, font=f_sub, fill=RED)
    sub_w = d.textbbox((0, 0), subtitle, font=f_sub)[2]
    d.rectangle([80, 292, 80 + min(sub_w, W - 160) + 24, 294], fill=RED)
    # 分割线
    d.rectangle([80, 330, W - 80, 331], fill=HAIRLINE)


def draw_footer_block(img, d, accent=None):
    # 强调大字（居中，如果有）
    if accent:
        f_ac = C.fit_font_size(d, accent, 'MSZ', start_size=64, min_size=40, max_w=W - 200)
        aw = d.textbbox((0, 0), accent, font=f_ac[0])[2]
        d.text(((W - aw) // 2, H - 330), accent, font=f_ac[0], fill=RED)
    # 页脚：细线 + slogan + 日期角标（放大版）
    d.rectangle([60, H - 96, W - 60, H - 95], fill=HAIRLINE)
    d.text((60, H - 76), C.SLOGAN, font=C.load_font('NORMAL', 22), fill=GREY)
    f_date = C.load_font('BOLD', 22)
    dt = date_str()
    tw = d.textbbox((0, 0), dt, font=f_date)[2]
    d.rounded_rectangle([W - 60 - tw - 40, H - 78, W - 60, H - 34],
                        radius=6, outline=RED, width=2)
    d.text((W - 60 - tw - 20, H - 71), dt, font=f_date, fill=RED)
    # 底部品牌红条
    d.rectangle([0, H - 10, W, H], fill=RED)


def render_card(idx, title, subtitle, body, accent=None):
    img, d = new_card()
    draw_header(img, d, title, subtitle)
    # 正文（文楷 30pt，行高 48）
    f_body = C.load_font('LXGW', 30)
    wrap_block(d, body, f_body, x=80, y=370, max_w=W - 160, line_h=52, fill=INK)
    draw_footer_block(img, d, accent)
    out = os.path.join(OUT_DIR, f'视觉卡-0{idx}.png')
    img.save(out)
    print(f'[OK] 视觉卡-0{idx}.png  ({os.path.getsize(out)}B)  | {title}')
    return out


# ── 7 张卡片（B型问答骨架：钩子→证据→对比→方法→实操→证明→互动）──
CARD_DEFS = [
    dict(
        title='AI出错谁来赔？',
        subtitle='DeepSeek故障补偿方案全解读',
        body=('当AI给出错误建议，导致业务损失，\n谁来负责？\n\n这不是假设题。随着AI深入各行各业，\n故障补偿是创作者必知的合规要点。\n\n本文拆解DeepSeek官方补偿政策，\n以及国内外AI故障责任归属框架。'),
    ),
    dict(
        title='故障率数据',
        subtitle='真实世界的AI可靠性',
        body=('• 大模型幻觉率：2-15%（视场景）\n'
              '• 关键业务可接受阈值：<1%\n'
              '• 用户感知故障率 > 技术统计值\n'
              '（后果越重，感知越高）\n\n'
              '数据来源：官方文档 + 用户反馈\n+ 第三方测试，多源交叉验证'),
        accent='数据不会说谎',
    ),
    dict(
        title='国内外对比',
        subtitle='同样的故障，不同的结局',
        body=('【国内】\n'
              'DeepSeek：明确补偿政策\n按用量阶梯赔付\n\n'
              '【国外】\n'
              'OpenAI：Error Credit 自动触发\n'
              'Google：SLA承诺 超时即补偿\n\n'
              '核心差异：透明度 vs 主动申请'),
        accent='政策透明度是关键',
    ),
    dict(
        title='补偿申请流程',
        subtitle='四步走，别漏环节',
        body=('① 记录故障\n   截图/录屏 + 时间戳 + 请求ID\n\n'
              '② 提交工单\n   官方渠道 + 证据链齐全\n\n'
              '③ 等待审核\n   通常 3-5 个工作日\n\n'
              '④ 获得补偿\n   积分/额度/现金，注意有效期'),
    ),
    dict(
        title='实操指南',
        subtitle='最大化你的补偿权益',
        body=('✓ 立即截图（故障瞬间）\n'
              '✓ 保留对话记录（含时间戳）\n'
              '✓ 量化损失（业务影响金额）\n'
              '✓ 多渠道同步提交（防遗漏）\n'
              '✓ 主动跟进审核进度\n\n'
              '✗ 别只做一次尝试\n'
              '✗ 别忽略小故障（累积影响大）'),
        accent='细节决定补偿金额',
    ),
    dict(
        title='成功案例',
        subtitle='真实用户的补偿经历',
        body=('【案例A】某MCN机构\n'
              '批量生成错误 → 等值额度+优先支持\n'
              '耗时 4 个工作日\n\n'
              '【案例B】独立创作者\n'
              'API超时丢内容 → 积分返还\n'
              '耗时 2 个工作日\n\n'
              '关键：证据完整度决定速度'),
        accent='准备越充分，赔付越快',
    ),
    dict(
        title='你遇到过吗？',
        subtitle='评论区聊聊',
        body=('□ 从未遇到（幸运）\n'
              '□ 遇到过但没索赔\n'
              '□ 索赔成功\n'
              '□ 索赔失败/无果\n\n'
              '评论区晒出你的故事，\n点赞最高的三位：\n'
              '🎁 AI避坑指南 + 合规咨询'),
    ),
]

if __name__ == '__main__':
    C.require_font('LXGW', 30)   # 硬校验字体链，缺则 exit 2
    C.require_font('MSZ', 64)
    for i, c in enumerate(CARD_DEFS, 1):
        render_card(i, **c)
    print(f'\n共 {len(CARD_DEFS)} 张 → {OUT_DIR}')
