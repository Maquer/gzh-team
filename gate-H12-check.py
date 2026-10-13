#!/usr/bin/env python3
"""垫片：gate-H12-check.py → gzhkit.gates.h12（prompt 元数据检查）。
exit code: 0=全绿 / 1=FAIL / 2=输入错误（与 v3.3.0 一致）
"""
import json as _json

from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.h12 as plugin  # noqa: F401  （注册 h12）


def main():
    parser = cli.build_parser(
        'gate-H12-check.py', 'H12 prompt 元数据门禁（prompt 关键词/主体描述入图）',
        epilog='exit code: 0=全绿, 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()
    if not args.images:
        parser.error('缺少图片路径：用法 gate-H12-check.py <图片1> [图片2 ...]')
    out = get_gate('h12')(args, {})
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
