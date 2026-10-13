#!/usr/bin/env python3
"""gzhkit.report: 统一报告格式。

级别：BLOCK（硬拦）/ WARN（提醒）/ INFO（信息）。
v3.x 各脚本输出格式不一，此处统一为：
  摘要行（res 风格 key: value）→ 明细 → === 门禁判定 ===
"""
import sys

from .cli import EXIT_BLOCK, EXIT_ERROR, EXIT_PASS, EXIT_WARN

LEVEL_BLOCK = 'BLOCK'
LEVEL_WARN = 'WARN'
LEVEL_INFO = 'INFO'


class Finding:
    """一条检查结论。line 可选（行号引用，G5 要求）。"""

    def __init__(self, level, code, message, line=None):
        self.level = level
        self.code = code
        self.message = message
        self.line = line

    def __str__(self):
        loc = ' (L%d)' % self.line if self.line else ''
        return '%s %s%s' % (self.code, self.message, loc)


class GateOutcome:
    """一次门禁执行结果。"""

    def __init__(self, gate_id):
        self.gate_id = gate_id
        self.findings = []
        self.stats = {}  # 摘要 key: value，原样打印

    def add(self, level, code, message, line=None):
        self.findings.append(Finding(level, code, message, line))

    def block(self, code, message, line=None):
        self.add(LEVEL_BLOCK, code, message, line)

    def warn(self, code, message, line=None):
        self.add(LEVEL_WARN, code, message, line)

    def info(self, code, message, line=None):
        self.add(LEVEL_INFO, code, message, line)

    def stat(self, key, value):
        self.stats[key] = value

    @property
    def blocks(self):
        return [f for f in self.findings if f.level == LEVEL_BLOCK]

    @property
    def warns(self):
        return [f for f in self.findings if f.level == LEVEL_WARN]

    def exit_code(self):
        if self.blocks:
            return EXIT_BLOCK
        if self.warns:
            return EXIT_WARN
        return EXIT_PASS


def print_stats(outcome, out=sys.stdout):
    for k, v in outcome.stats.items():
        print('%s: %s' % (k, v), file=out)


def print_verdict(outcome, out=sys.stdout):
    """=== 门禁判定 === 汇总（v3.x 文案保留）。"""
    print('\n=== 门禁判定（两级：BLOCK/WARN）===', file=out)
    if outcome.blocks:
        print('❌ BLOCK: ' + ' / '.join(str(f) for f in outcome.blocks), file=out)
        print('   → exit 7，硬拦发布，必须修复后复检', file=out)
    elif outcome.warns:
        print('⚠️  WARN: ' + ' / '.join(str(f) for f in outcome.warns), file=out)
        print('   → 只提醒不阻断，建议优化后发布', file=out)
    else:
        print('✅ PASS: BLOCK 0 / WARN 0，全项达标', file=out)


def exit_for(outcome):
    """按 BLOCK/WARN/PASS 映射退出码；异常路径由 cli 处理为 2。"""
    return outcome.exit_code()


def die_input(message):
    """输入错误 → stderr + exit 2。"""
    print('错误：%s' % message, file=sys.stderr)
    sys.exit(EXIT_ERROR)
