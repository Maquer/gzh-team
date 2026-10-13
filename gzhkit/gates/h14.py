#!/usr/bin/env python3
"""gzhkit.gates.h14: H14 AI 味门禁（调外部 humanizer-check.py）。

支持 policy_mode（透传 --policy-mode 豁免 3 条规则）与 no_humanizer 跳过。
脚本缺失 / 超时 / 解析失败 → 不可用，不计入判定（不误伤）。
脚本路径：<repo>/../humanizer-check/humanizer-check.py 或
$GZH_SHARED_DIR/humanizer-check/humanizer-check.py。
"""
import os
import re
import subprocess
import sys

from . import register
from .. import config as C
from ..report import GateOutcome

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def _humanizer_script():
    shared = os.environ.get('GZH_SHARED_DIR',
                            os.path.dirname(REPO_ROOT))
    candidates = [
        os.path.join(REPO_ROOT, '..', 'humanizer-check', 'humanizer-check.py'),
        os.path.join(shared, 'humanizer-check', 'humanizer-check.py'),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def run_humanizer(text, policy_mode=False):
    """调用外部脚本。返回 dict：可用/分数/判定/说明。"""
    script = _humanizer_script()
    if not script:
        return {'可用': False, '分数': None, '说明': 'humanizer-check.py 不存在'}
    cmd = [sys.executable, script]
    if policy_mode:
        cmd.append('--policy-mode')
    try:
        p = subprocess.run(cmd, input=text, capture_output=True, text=True,
                           timeout=C.HUMANIZER_TIMEOUT)
        out = (p.stdout or '') + (p.stderr or '')
        m = (re.search(r'综合评分[:：]\s*(\d+)\s*分', out)
             or re.search(r'(\d+)\s*分', out))
        if not m:
            return {'可用': False, '分数': None,
                    '说明': '解析失败: %s' % out.strip()[:100]}
        s = int(m.group(1))
        if s <= C.HUMANIZER_LIMITS['放行']:
            v = '放行'
        elif s <= C.HUMANIZER_LIMITS['重写']:
            v = '重写≥50%'
        elif s <= C.HUMANIZER_BLOCK_SCORE:
            v = '明显AI味'
        else:
            v = '推倒重写'
        return {'可用': True, '分数': s, '判定': v}
    except Exception as e:  # 超时 / 进程异常 → 不可用
        return {'可用': False, '分数': None, '说明': '调用异常: %s' % e}


def add_arguments(parser):
    parser.add_argument('files', nargs='*', metavar='FILE',
                        help='待检查的正文路径（可多篇）')
    parser.add_argument('--mode', choices=['solo', 'strict'], default='solo',
                        help='solo=只给参考分数不卡关；strict=三档硬判定')
    parser.add_argument('--no-humanizer', action='store_true',
                        help='跳过外部脚本调用（离线/快速模式）')
    parser.add_argument('--policy-mode', action='store_true',
                        help='政策类稿件豁免模式：透传 --policy-mode 给 humanizer-check')


def check(args, ctx):
    """执行 H14 AI 味检查。ctx: text/no_humanizer/policy_mode/verbose。"""
    out = GateOutcome('h14')
    no_humanizer = bool(getattr(args, 'no_humanizer', False)
                        or ctx.get('no_humanizer', False))
    policy_mode = bool(getattr(args, 'policy_mode', False)
                       or ctx.get('policy_mode', False))
    solo = getattr(args, 'mode', 'strict') == 'solo'

    if no_humanizer:
        out.info('H14', '跳过（--no-humanizer）')
        return out

    hum = run_humanizer(ctx.get('text', ''), policy_mode)
    out.stat('H14 AI 味分数', hum.get('分数') if hum.get('可用') else '不可用')
    out.stat('H14 说明', hum.get('判定') or hum.get('说明'))

    if not hum.get('可用'):
        # 不可用 → 不计入判定
        out.info('H14', '不可用（%s），不计入判定' % hum.get('说明'))
        return out

    s = hum['分数']
    if s <= C.HUMANIZER_LIMITS['放行']:
        out.info('H14', 'AI 味 %d 分（放行）' % s)
    elif s <= C.HUMANIZER_LIMITS['重写']:
        out.warn('H14', 'AI 味 %d 分（%s，建议重写≥50%%）' % (s, hum['判定']))
    elif s <= C.HUMANIZER_BLOCK_SCORE:
        out.warn('H14', 'AI 味 %d 分（%s，建议重写）' % (s, hum['判定']))
    else:
        if solo:
            # solo 模式不卡关 → 降级为 WARN
            out.warn('H14', 'AI 味 %d 分（%s，solo 模式仅参考）' % (s, hum['判定']))
        else:
            out.block('H14', 'AI 味 %d 分 >%d（%s）' % (s, C.HUMANIZER_BLOCK_SCORE, hum['判定']))
    return out


register('h14', 'AI 味检查')(check)
