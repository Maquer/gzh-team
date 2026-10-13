#!/usr/bin/env python3
"""gzhkit.gates.g3: G3 结构门禁（标题策略/字数/结构）。

按 5 类模板的判据检查结构案：节数 / 总字数 / 金句数 / 素材引用。
"""
import re

from . import register
from .. import config as C
from ..report import GateOutcome


def add_arguments(parser):
    parser.add_argument('file_pos', nargs='?', metavar='FILE',
                        help='结构案 Markdown 路径')
    parser.add_argument('--template', help='模板名称（可选，自动检测）')


def _detect_template(t):
    for name in C.G3_TEMPLATES:
        if re.search(r'(?<![\u4e00-\u9fff])%s(?![\u4e00-\u9fff])' % name, t):
            return name
    return C.G3_DEFAULT_TEMPLATE


def check(args, ctx):
    """执行 G3 结构门禁检查。ctx: text/verbose。"""
    out = GateOutcome('g3')
    t = ctx.get('text', '')

    template = getattr(args, 'template', None) or _detect_template(t)
    params = C.G3_TEMPLATES.get(template, C.G3_TEMPLATES[C.G3_DEFAULT_TEMPLATE])
    out.stat('模板', template)

    sections = len(re.findall(r'^###\s+', t, re.M))
    zh = len(re.findall(r'[\u4e00-\u9fff]', t))
    gold = t.count('【金句】') or len(re.findall(r'\*\*[^*\n]+\*\*', t))
    refs = len(re.findall(r'\[R-\d+\]', t))

    s_min, s_max = params['sections']
    w_min, w_max = params['total_words']

    rows = [
        ('节数', sections, '%d-%d' % (s_min, s_max),
         s_min <= sections <= s_max, 'block'),
        ('总字数', zh, '%d-%d' % (w_min, w_max),
         w_min <= zh <= w_max, 'block'),
        ('金句数', gold, '≥%d' % params['gold_min'],
         gold >= params['gold_min'], 'block'),
        ('素材引用', refs, '≥1', refs >= 1, 'warn'),
    ]
    for name, val, th, ok, sev in rows:
        out.stat(name, '%s（要求 %s）' % (val, th))
        if not ok:
            msg = 'G3-%s %s 未达要求（%s）' % (name, val, th)
            if sev == 'block':
                out.block('G3', msg)
            else:
                out.warn('G3', msg)
    return out


register('g3', '结构门禁')(check)
