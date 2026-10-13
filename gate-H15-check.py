#!/usr/bin/env python3
"""垫片：gate-H15-check.py → gzhkit.gates.h15（尾图合规检查）。
exit code: 0=PASS / 1=FAIL / 2=输入错误（与 v3.3.0 一致）
"""
from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.h15 as plugin  # noqa: F401  （注册 h15）


def main():
    parser = cli.build_parser(
        'gate-H15-check.py', 'H15 尾图合规门禁（尺寸/违规词/导流词）',
        epilog='exit code: 0=PASS, 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    args = parser.parse_args()
    if not args.image:
        parser.error('缺少尾图路径：用法 gate-H15-check.py <尾图路径> [文案文本]')
    out = get_gate('h15')(args, {})
    report.print_stats(out)
    report.print_verdict(out)
    return 1 if out.blocks else 0


if __name__ == '__main__':
    cli.run_main(main)
