#!/usr/bin/env python3
"""垫片：gate-H14-check.py → gzhkit.gates.h14（AI 味检测）。
# ⚠️ CLI 入口层 — 实际逻辑在 gzhkit/gates/，本文件仅做参数解析和调用转发
exit code（与 v3.3.0 一致）：solo=始终 0（只给参考分数，不卡关产出）；
strict=0/1/2；脚本不可用时不计入判定（v4 放宽，v3.3.0 记 FAIL）。
"""
import json as _json

from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.h14 as plugin  # noqa: F401  （注册 h14）


def main():
    parser = cli.build_parser(
        'gate-H14-check.py', 'H14 AI 味门禁（外部 humanizer-check.py）',
        epilog='exit code: solo 始终 0; strict 0/1; 2=输入错误')
    plugin.add_arguments(parser)
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()
    if not args.files:
        parser.error('缺少正文路径：用法 gate-H14-check.py <正文.md> [--mode solo|strict]')

    out = report.GateOutcome('h14')
    for path in args.files:
        import os
        if not os.path.isfile(path):
            out.block('H14', '[%s] 文件不存在' % path)
            continue
        text = cli.read_text(path)
        ctx = {'text': text, 'path': path}
        sub = get_gate('h14')(args, ctx)
        for f in sub.findings:
            out.add(f.level, 'H14',
                    '[%s] %s' % (path, f.message), f.line)
        for k, v in sub.stats.items():
            out.stat('%s/%s' % (path, k), v)

    if args.json:
        print(_json.dumps(
            {'mode': args.mode, 'stats': out.stats,
             'findings': [{'level': f.level, 'code': f.code,
                           'message': f.message} for f in out.findings]},
            ensure_ascii=False, indent=2))
    else:
        report.print_stats(out)
        report.print_verdict(out)
    if args.mode == 'solo':
        return 0
    return 1 if out.blocks else 0


if __name__ == '__main__':
    cli.run_main(main)
