#!/usr/bin/env python3
"""gzhkit.gates.g7: G7 发布前清单门禁（TEAM.md §3.7 十项清单脚本化）。

可自动判定：标题字数 / 封面尺寸 / 金句数量 / 防盗链 / 互动钩子 /
AI 味分数 / OCR（封面）/ 群发开关 / 评论开关 / 账号健康状态。
人工项（后台预览 / AI 声明开关 / 24h pre-mortem）只记录 INFO，不计入判定。
"""
import json
import os
import re
import subprocess

from . import register
from .. import config as C
from ..report import GateOutcome

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def add_arguments(parser):
    parser.add_argument('file_pos', nargs='?', metavar='FILE',
                        help='稿件 Markdown 路径')
    parser.add_argument('--cover', help='封面图路径')
    parser.add_argument('--html', help='排版稿 HTML 路径')
    parser.add_argument('--review', help='05 审核结论路径（含 AI 味分数）')
    parser.add_argument('--strict', action='store_true',
                        help='全部 PASS 才退出 0（此时 WARN 也算不通过）')
    parser.add_argument('--broadcast-ok', action='store_true',
                        help='显式确认「群发开关已开启」，strict 模式缺省即 FAIL')
    parser.add_argument('--comment-enabled', action='store_true',
                        help='显式确认「评论功能已开启」，strict 模式缺省即 FAIL')
    parser.add_argument('--label', default='',
                        help='账号健康追踪文件路径（默认 docs/account-health-label.md）')


def _cover_dims(path):
    """用 ImageMagick identify 读尺寸；失败返回 (0, 0)。"""
    try:
        r = subprocess.run(['identify', path], capture_output=True, text=True,
                           timeout=10)
        for token in r.stdout.split():
            m = re.match(r'(\d+)x(\d+)', token)
            if m:
                return int(m.group(1)), int(m.group(2))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 0, 0


def _ocr_cover(path):
    """apple-vision OCR；CLI 缺失/调用失败返回 None（→ INFO 跳过）。"""
    try:
        r = subprocess.run(
            ['apple-vision', 'ocr', path, '--lang', 'zh-Hans,en',
             '--level', 'fast', '-q'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get('blocks', []) if r.stdout.strip() else []
    except ValueError:
        return None


def check(args, ctx):
    """执行 G7 发布前清单检查。ctx: text/verbose。"""
    out = GateOutcome('g7')
    t = ctx.get('text', '')
    strict = bool(getattr(args, 'strict', False))

    # 1. 标题字数
    m = re.search(r'^#\s+(.+)$', t, re.M)
    if m:
        zh = len(re.findall(r'[\u4e00-\u9fff]', m.group(1).strip()))
        out.stat('标题字数', '%d（要求 %d-%d）' % (zh, C.G7_TITLE_ZH_MIN, C.G7_TITLE_ZH_MAX))
        if not (C.G7_TITLE_ZH_MIN <= zh <= C.G7_TITLE_ZH_MAX):
            out.block('G7', '标题 %d 字，要求 %d-%d' % (zh, C.G7_TITLE_ZH_MIN, C.G7_TITLE_ZH_MAX))
    else:
        out.block('G7', '无标题（# 标题行缺失）')

    # 2. 封面尺寸
    cover = getattr(args, 'cover', None)
    if cover:
        if os.path.isfile(cover):
            w, h = _cover_dims(cover)
            out.stat('封面尺寸', '%dx%d（要求 %dx%d）' % (w, h, C.G7_COVER_W, C.G7_COVER_H))
            if (w, h) != (C.G7_COVER_W, C.G7_COVER_H):
                out.block('G7', '封面 %dx%d，要求 %dx%d' % (w, h, C.G7_COVER_W, C.G7_COVER_H))
        else:
            out.block('G7', '封面文件不存在：%s' % cover)
    else:
        out.info('G7', '封面尺寸：未提供 --cover，跳过')

    # 3. 金句数量（≥1 加粗）
    gold = len(re.findall(r'\*\*[^*\n]+\*\*', t))
    out.stat('金句数量', '%d 处加粗（要求 ≥1）' % gold)
    if gold < 1:
        out.block('G7', '金句 0 处，要求 ≥1 处加粗')

    # 4. 防盗链注入
    html = ''
    html_path = getattr(args, 'html', None)
    if html_path and os.path.isfile(html_path):
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
    if html:
        low = html.lower()
        has_img = '<img' in low
        has_rp = 'referrerpolicy' in low or 'referrer' in low
        if has_img and not has_rp:
            out.block('G7', 'HTML 中有 <img> 但无 referrerpolicy（防盗链未注入）')
        elif has_rp:
            out.stat('防盗链注入', '已注入 referrerpolicy')
        else:
            out.info('G7', '防盗链注入：HTML 中无 <img>，跳过')
    else:
        out.info('G7', '防盗链注入：未提供 --html，跳过')

    # 5. 互动钩子
    has_hook = any(kw in t for kw in C.G7_HOOK_KEYWORDS)
    out.stat('互动钩子', '找到互动关键词' if has_hook else '未找到互动钩子')
    if not has_hook:
        out.block('G7', '无互动钩子（缺少"你/评论/留言/怎么/如何/你觉得/分享/投票/填"类词）')

    # 5b. 评论功能开关（strict 必确认）
    if strict and not getattr(args, 'comment_enabled', False):
        out.block('G7', '未提供 --comment-enabled 确认（评论功能是否已开启）')
    else:
        out.info('G7', '评论功能：%s' % ('已显式确认 --comment-enabled'
               if strict else '非 strict 模式默认跳过'))

    # 6. AI 味分数（从审核结论读）
    review_path = getattr(args, 'review', None)
    review = ''
    if review_path and os.path.isfile(review_path):
        with open(review_path, encoding='utf-8') as f:
            review = f.read()
    if review:
        m = re.search(r'AI\s*味[^\d]*(\d+)', review, re.I)
        if m:
            score = int(m.group(1))
            out.stat('AI 味分数', score)
            if score <= C.HUMANIZER_LIMITS['放行']:
                pass
            elif score <= C.HUMANIZER_BLOCK_SCORE:
                out.warn('G7', 'AI 味 %d 分（6-25，建议重写≥50%%）' % score)
            else:
                out.block('G7', 'AI 味 %d 分 >25，需推倒重写' % score)
        else:
            out.info('G7', 'AI 味分数：审核结论中无分数，跳过')
    else:
        out.info('G7', 'AI 味分数：未提供 --review，跳过')

    # 7. OCR 检查（封面中文残留）
    if cover and os.path.isfile(cover):
        blocks = _ocr_cover(cover)
        if blocks is None:
            out.info('G7', 'OCR 中文检查：apple-vision 不可用，跳过')
        else:
            cn = [b.get('text', '') for b in blocks
                  if re.search(r'[\u4e00-\u9fff]', b.get('text', ''))]
            if cn:
                out.block('G7', '封面 OCR 检出中文 %d 处：%s'
                          % (len(cn), ' / '.join(cn[:3])))
            else:
                out.stat('OCR 中文检查', '无中文残留')
    else:
        out.info('G7', 'OCR 中文检查：未提供 --cover，跳过')

    # 8-10. 人工项（只记录，不计入判定）
    for name in C.G7_ARTIFICIAL_ITEMS:
        out.info('G7', '%s：人工确认项，跳过' % name)

    # 11. 群发开关（strict 必确认）
    if strict and not getattr(args, 'broadcast_ok', False):
        out.block('G7', '未提供 --broadcast-ok 确认（群发开关是否已开启）')
    else:
        out.info('G7', '群发开关：%s' % ('已显式确认 --broadcast-ok'
               if strict else '非 strict 模式默认跳过'))

    # 12. 账号健康状态
    label_path = getattr(args, 'label', '') or os.path.join(
        REPO_ROOT, C.G7_ACCOUNT_HEALTH_FILE)
    if os.path.isfile(label_path):
        label = open(label_path, encoding='utf-8').read()
        has_red = '🔴' in label
        has_pending = '⏳ 待查' in label or '⏳ 待用户' in label
        if has_red and has_pending:
            out.block('G7', '账号健康状态 FAIL：%s 显示 🔴 + 待查，常规发布暂停' % label_path)
        elif has_red:
            out.block('G7', '账号健康状态 FAIL：🔴 标签仍在，常规发布暂停')
        else:
            out.stat('账号健康状态', '无 🔴 且无待查，标签已解除或无记录')
    else:
        out.info('G7', '账号健康状态：%s 不存在（新团队首次跑可忽略）' % label_path)

    return out


register('g7', '发布前清单')(check)
