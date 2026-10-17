#!/usr/bin/env python3
"""垫片：gate-G8-check.py → gzhkit.gates.g8（G8 结构多样性）。
# ⚠️ CLI 入口层 — 实际逻辑在 gzhkit/gates/，本文件仅做参数解析和调用转发
exit code: 0=PASS / 1=FAIL / 2=输入错误（与 v3.3.0 一致）
注意：v4 的 g8 插件只做「结构多样性」（全 WARN 级），
v3.3.0 的 13 项发布前检查已拆入 g7 与 gate-check 编排器。
"""
from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.g8 as plugin  # noqa: F401  （注册 g8）


def main():
    parser = cli.build_parser(
        'gate-G8-check.py', 'G8 结构多样性门禁（骨架去重/禁用起手收尾式，全 WARN）',
        epilog='exit code: 0=PASS, 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    cli.add_verbose(parser)
    args = parser.parse_args()
    path = cli.resolve_file_arg(args, parser)
    text = cli.read_text(path)
    ctx = {'text': text, 'path': path, 'verbose': args.verbose}
    out = get_gate('g8')(args, ctx)
    report.print_stats(out)
    report.print_verdict(out)
    return 1 if out.blocks else 0


if __name__ == '__main__':
    cli.run_main(main)
