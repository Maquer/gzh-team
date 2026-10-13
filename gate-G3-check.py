#!/usr/bin/env python3
"""垫片：gate-G3-check.py → gzhkit.gates.g3（G3 结构门禁）。
exit code: 0=PASS / 1=FAIL / 2=输入错误（与 v3.3.0 一致）
"""
import json as _json

from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.g3 as plugin  # noqa: F401  （注册 g3）


def main():
    parser = cli.build_parser(
        'gate-G3-check.py', 'G3 结构门禁（模板：节数/字数/金句/素材引用）',
        epilog='exit code: 0=PASS, 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()
    path = cli.resolve_file_arg(args, parser)
    text = cli.read_text(path)
    ctx = {'text': text, 'path': path}
    out = get_gate('g3')(args, ctx)
    if args.json:
        print(_json.dumps(
            {'stats': out.stats,
             'findings': [{'level': f.level, 'code': f.code,
                           'message': f.message} for f in out.findings]},
            ensure_ascii=False, indent=2))
    else:
        report.print_stats(out)
        report.print_verdict(out)
    return 1 if out.blocks else 0


if __name__ == '__main__':
    cli.run_main(main)
