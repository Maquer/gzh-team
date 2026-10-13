#!/usr/bin/env python3
"""gzh-typeset.py：公众号排版工具（Markdown→微信 HTML）转发器。

v4 垫片：本文件只是转发层，真正的排版实现在仓库外的 gzh-typeset 融合版。
查找顺序：$GZH_TYPESET_IMPL → ../gzh-typeset/gzh-typeset.py。
转发目标缺失时明确提示 + exit 2（不 traceback）。

用法：python3 gzh-typeset.py <input.md> [output.html] [排版器原有参数...]
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get('GZH_TYPESET_IMPL', ''),
    os.path.join(_HERE, '..', 'gzh-typeset', 'gzh-typeset.py'),
]


def find_impl():
    for impl in _CANDIDATES:
        if impl and os.path.isfile(impl) \
                and os.path.abspath(impl) != os.path.abspath(__file__):
            return impl
    return None


def main():
    # --help 由转发层直接处理（契约：--help 退出 0）；其余参数原样转发
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print('用法：python3 gzh-typeset.py <input.md> [output.html] [排版器参数...]')
        print()
        print('转发器：将参数原样转发给 gzh-typeset 融合版实现。')
        print('实现查找顺序：$GZH_TYPESET_IMPL → ../gzh-typeset/gzh-typeset.py')
        impl = find_impl()
        print('当前实现：%s' % (impl if impl else '未找到（转发将 exit 2）'))
        return 0
    impl = find_impl()
    if impl is None:
        print('gzh-typeset.py: 未找到排版实现。', file=sys.stderr)
        print('查找过：%s' % '；'.join(c for c in _CANDIDATES if c), file=sys.stderr)
        print('可用环境变量 GZH_TYPESET_IMPL 指定 gzh-typeset 融合版路径。',
              file=sys.stderr)
        return 2
    r = subprocess.run([sys.executable, impl] + sys.argv[1:])
    return r.returncode


if __name__ == '__main__':
    cli.run_main(main)
