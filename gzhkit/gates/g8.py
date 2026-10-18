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
    """执行 G8 结构多样性检查。ctx: text/path/verbose。

    六型判定（2026-10-18 升级，原只判 A/E 两档）：
    - A 型：序数词小标题（一、二、三…）≥3 → 已停用
    - B 型：问答骨架（H2 含问号）
    - C 型：案例骨架（H2 含"案例"/"XX公司"/"以…为例"）
    - D 型：清单骨架（H2 含①②③或数字圆括号）
    - E 型：场景骨架（H2 含"作为…"/"如果…"/叙事短句）
    - F 型：对话骨架（H2 含"甲："/"乙："/"问"/"答"）
    无法归类 → ? 型
    """
    out = GateOutcome('g8')
    t = ctx.get('text', '')
    fname = os.path.basename(ctx.get('path', ''))

    history_dir = os.path.expanduser(os.path.join('~', C.G8_HISTORY_DIRNAME))
    os.makedirs(history_dir, exist_ok=True)
    history_file = os.path.join(history_dir, C.G8_HISTORY_FILE)
    history = _load_history(history_file)

    # ── 六型判定 ──────────────────────────────────────────────
    lines = t.split('\n')
    h2_list = [ln.strip() for ln in lines if re.match(r'^##\s+', ln)]
    
    # A 型：序数词小标题
    ordinal_matches = re.findall(C.G8_ORDINAL_RE, t, re.M)
    is_A = len(ordinal_matches) >= C.G8_ORDINAL_MIN
    
    # B 型：问答（H2 含问号）
    is_B = any('?' in h or '？' in h for h in h2_list)
    
    # C 型：案例（关键词命中 H2）
    case_patterns = ['案例', '公司', '为例', '某', '项目', '经历', 'XX']
    is_C = any(any(p in h for p in case_patterns) for h in h2_list)
    
    # D 型：清单（①②③ 或 (1)(2) 等）
    is_D = any(re.search(r'[①②③④⑤⑥⑦⑧⑨⑩]|[（(]\d+[)）]', h) for h in h2_list)
    
    # F 型：对话（甲/乙/问/答 在 H2）
    dialog_patterns = ['甲：', '乙：', '丙：', '问：', '答：', 'Q:', 'A:']
    is_F = any(p in h for h in h2_list for p in dialog_patterns)
    
    # E 型：场景（作为… / 如果… / 叙事性短句）
    scene_patterns = ['作为', '如果', '假如', '假如你是', '当你']
    is_E = any(p in h for h in h2_list for p in scene_patterns)
    
    # 优先级：A > B > C > D > E > F > ?
    if is_A:
        current = 'A'
    elif is_B:
        current = 'B'
    elif is_C:
        current = 'C'
    elif is_D:
        current = 'D'
    elif is_E:
        current = 'E'
    elif is_F:
        current = 'F'
    else:
        current = '?'
    
    out.stat('G8 骨架类型', '%s 型（序数词小标题 %d 个，H2 %d 个）' % (current, len(ordinal_matches), len(h2_list)))

    # ── 历史连续同类检测（同骨架出现 ≥2 次才 WARN）──────────
    prior = [r for r in history if r.get('file') != fname]
    recent_same_count = sum(1 for r in reversed(prior) if r.get('structure') == current)
    out.stat('上一篇骨架', ('%s 型' % prior[-1].get('structure')) if prior else '无记录')
    # 连续同类 ≥2 次（即当前 + 前一篇同类）才报警，避免 A/E 两档必然连续的问题
    if recent_same_count >= 2:
        out.warn('G8', '连续%d篇同类骨架（%s型）' % (recent_same_count + 1, current))
    
    # 若当前是 A 型（已停用），强制 WARN
    if current == 'A':
        out.warn('G8', 'A 型（序数词骨架）已停用，请改用 B/F 型')

    # ── 禁用起手式/收尾式 ────────────────────────────────────
    first_body = _first_section(t.split('\n'))
    opening_hits = [p for p in C.DISABLED_OPENINGS if p in first_body]
    out.stat('禁用起手式', opening_hits or '无')
    if opening_hits:
        out.warn('G8', '禁用起手式：%s' % '、'.join(opening_hits))

    last_body = '\n'.join(t.split('\n')[-10:])
    closing_hits = [p for p in C.DISABLED_CLOSINGS if p in last_body]
    out.stat('禁用收尾式', closing_hits or '无')
    if closing_hits:
        out.warn('G8', '禁用收尾式：%s' % '、'.join(closing_hits))

    # 记录本次骨架
    history = [r for r in history if r.get('file') != fname]
    history.append({'file': fname, 'structure': current,
                    'timestamp': datetime.now().isoformat()})
    _save_history(history_file, history)
    return out


register('g8', '结构多样性')(check)
