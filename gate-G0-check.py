#!/usr/bin/env python3
"""垫片：gate-G0-check.py → gzhkit.gates.g0（G0 选题门禁）。
exit code: 0=PASS（含 WARN）/ 1=FAIL / 2=输入错误（与 v3.3.0 一致）
"""
from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.g0 as plugin  # noqa: F401  （注册 g0）


def main():
    parser = cli.build_parser(
        'gate-G0-check.py', 'G0 选题门禁（选题阶段判据脚本化）',
        epilog='exit code: 0=PASS(含WARN), 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    cli.add_verbose(parser)
    args = parser.parse_args()
    path = cli.resolve_file_arg(args, parser)
    text = cli.read_text(path)
    ctx = {'text': text, 'path': path, 'verbose': args.verbose}
    out = get_gate('g0')(args, ctx)
    report.print_stats(out)
    report.print_verdict(out)
    return 1 if out.blocks else 0


if __name__ == '__main__':
    cli.run_main(main)
