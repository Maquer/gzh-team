#!/usr/bin/env python3
"""垫片：gate-H11-check.py → gzhkit.gates.h11（图片 OCR：中文残留/水印）。
# ⚠️ CLI 入口层 — 实际逻辑在 gzhkit/gates/，本文件仅做参数解析和调用转发
exit code: 0=全绿 / 1=FAIL / 2=输入错误（与 v3.3.0 一致）
"""
import json as _json

from gzhkit import cli
from gzhkit import report
from gzhkit.gates import get_gate
import gzhkit.gates.h11 as plugin  # noqa: F401  （注册 h11）


def main():
    parser = cli.build_parser(
        'gate-H11-check.py', 'H11 图片 OCR 门禁（中文残留/水印检测）',
        epilog='exit code: 0=全绿, 1=FAIL, 2=输入错误')
    plugin.add_arguments(parser)
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()
    if not args.images:
        parser.error('缺少图片路径：用法 gate-H11-check.py <图片1> [图片2 ...]')
    out = get_gate('h11')(args, {})
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
