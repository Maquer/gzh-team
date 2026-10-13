#!/usr/bin/env python3
"""gzhkit.gates.g8: G8 结构多样性门禁。

打破模板套用：序数词小标题 ≥3 → A 型骨架，否则 E 型；
查 ~/.gzh-structure-history/structure-log.json 看上一篇（不同稿件）
是否同类；禁用起手式/收尾式。三项全部 WARN 级，不阻断发布。
写历史时同名文件覆盖旧记录，只保留最新一次。
"""
import json
import os
import re
from datetime import datetime

from . import register
from .. import config as C
from ..report import GateOutcome


def add_arguments(parser):
    parser.add_argument('file_pos', nargs='?', metavar='FILE',
                        help='稿件路径（用于历史记录去重）')


def _load_history(path):
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save_history(path, history):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _first_section(lines):
    """正文起始：第一个二级标题（非三级）起的 5 行。"""
    start = 0
    for i, line in enumerate(lines):
        if line.startswith('## ') and not line.startswith('###'):
            start = i
            break
    return '\n'.join(lines[start:start + 5])


def check(args, ctx):
    """执行 G8 结构多样性检查。ctx: text/path/verbose。"""
    out = GateOutcome('g8')
    t = ctx.get('text', '')
    fname = os.path.basename(ctx.get('path', ''))

    history_dir = os.path.expanduser(os.path.join('~', C.G8_HISTORY_DIRNAME))
    os.makedirs(history_dir, exist_ok=True)
    history_file = os.path.join(history_dir, C.G8_HISTORY_FILE)
    history = _load_history(history_file)

    # 当前骨架类型
    a_matches = re.findall(C.G8_ORDINAL_RE, t, re.M)
    current = 'A' if len(a_matches) >= C.G8_ORDINAL_MIN else 'E'
    out.stat('G8 骨架类型', '%s 型（序数词小标题 %d 个）' % (current, len(a_matches)))

    # 上一篇（不同稿件）是否同类——同一文件复检先剔除旧记录，防改稿自撞假阳性
    prior = [r for r in history if r.get('file') != fname]
    recent_same = bool(prior and prior[-1].get('structure') == current)
    out.stat('上一篇骨架', ('%s 型' % prior[-1].get('structure')) if prior else '无记录')
    if recent_same:
        out.warn('G8', '连续2篇同类骨架（%s型）' % current)

    # 禁用起手式（开头 5 行）
    first_body = _first_section(t.split('\n'))
    opening_hits = [p for p in C.DISABLED_OPENINGS if p in first_body]
    out.stat('禁用起手式', opening_hits or '无')
    if opening_hits:
        out.warn('G8', '禁用起手式：%s' % '、'.join(opening_hits))

    # 禁用收尾式（末尾 10 行）
    last_body = '\n'.join(t.split('\n')[-10:])
    closing_hits = [p for p in C.DISABLED_CLOSINGS if p in last_body]
    out.stat('禁用收尾式', closing_hits or '无')
    if closing_hits:
        out.warn('G8', '禁用收尾式：%s' % '、'.join(closing_hits))

    # 记录本次骨架（同名文件覆盖）
    history = [r for r in history if r.get('file') != fname]
    history.append({'file': fname, 'structure': current,
                    'timestamp': datetime.now().isoformat()})
    _save_history(history_file, history)
    return out


register('g8', '结构多样性')(check)
