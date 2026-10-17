#!/usr/bin/env python3
"""gzhkit.gates.h9: H9 段落句数门禁（每段 ≤3 句）。

- 段落 >3 句 → WARN Finding（不阻断，提示拆分）。
- 判据来源：TEAM.md §3.4（段落 1-3 句）。
"""
import re as _re

from . import register
from .. import text as T
from ..report import GateOutcome


def add_arguments(parser):
    parser.add_argument('body', nargs='?', metavar='BODY',
                        help='正文路径（.md）或正文字符串')
    parser.add_argument('--limit', type=int, default=3,
                        help='段落最大句数（默认 3）')


def check(args, ctx):
    """执行 H9 段落句数检查。args: body/limit；ctx: path 兜底。"""
    from .. import config as C
    out = GateOutcome('h9')
    limit = getattr(args, 'limit', None) or C.H9_SENTENCE_LIMIT

    body = getattr(args, 'body', None)
    if not body:
        body = ctx.get('path', '')
    if not body:
        out.info('H9', '未提供正文，跳过')
        return out

    # 路径或字符串：按字符串处理
    import os
    text = body
    if os.path.isfile(body):
        try:
            with open(body, encoding='utf-8') as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as e:
            out.warn('H9', '正文读取失败，检查跳过（%s）' % e)
            return out

    long = T.overlong_paragraphs(text, limit)
    if not long:
        out.stat('H9 段落句数', 'PASS（无超 %d 句段落）' % limit)
    else:
        worst = max(long, key=lambda x: x[1])
        out.warn('H9', 'H9 有 %d 段超 %d 句（最严重：第%d段 %d句「%s」）'
                 % (len(long), limit, worst[0], worst[1], worst[2]))
        out.stat('H9 超长段数', len(long))
    return out


register('h9', '段落≤3句检查')(check)
