#!/usr/bin/env python3
"""垫片：gate-G7-check.py → gzhkit.gates.g7（G7 发布前清单）。
# ⚠️ CLI 入口层 — 实际逻辑在 gzhkit/gates/，本文件仅做参数解析和调用转发
exit code: 0=全绿 / 1=FAIL（strict 下 WARN 也算） / 2=输入错误（与 v3.3.0 一致）
"""
import json as _json

from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.g7 as plugin  # noqa: F401  （注册 g7）


def main():
    parser = cli.build_parser(
        'gate-G7-check.py', 'G7 发布前清单门禁（TEAM.md §3.7 十项清单）',
        epilog='exit code: 0=全绿, 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()
    path = cli.resolve_file_arg(args, parser)
    text = cli.read_text(path)
    ctx = {'text': text, 'path': path}
    out = get_gate('g7')(args, ctx)
    if args.json:
        print(_json.dumps(
            {'stats': out.stats,
             'findings': [{'level': f.level, 'code': f.code,
                           'message': f.message} for f in out.findings]},
            ensure_ascii=False, indent=2))
    else:
        report.print_stats(out)
        report.print_verdict(out)
    strict = bool(getattr(args, 'strict', False))
    return 1 if (out.blocks or (strict and out.warns)) else 0


if __name__ == '__main__':
    cli.run_main(main)
