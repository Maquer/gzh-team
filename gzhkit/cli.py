#!/usr/bin/env python3
"""gzhkit.cli: 统一 CLI 框架。

退出码契约（与 v3.3.0 实际行为一致）：
  0 = PASS（通过）
  1 = WARN（只提醒，不阻断）
  2 = 输入错误 / 缺少依赖（argparse 错误、文件不可读、缺 Pillow 等）
  7 = BLOCK（硬拦发布；gate-check.py 沿用 v3.3.0 的 7）

注意：设计文档写 0/1/2 是简化，v3.3.0 的 gate-check.py 实际用 7 表示 BLOCK，
此处保留真实行为，见重建报告。
"""
import argparse
import os
import sys

EXIT_PASS = 0
EXIT_WARN = 1
EXIT_ERROR = 2
EXIT_BLOCK = 7


def build_parser(prog, description, epilog=None):
    """标准 argparse 模板：prog/description/epilog 必填，--help 自动完备。"""
    return argparse.ArgumentParser(prog=prog, description=description, epilog=epilog)


def add_verbose(parser):
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示每个检查项的详细数据与自检明细')
    return parser


def resolve_file_arg(args, parser):
    """处理 file_pos / --file 双入口，冲突时 exit 2。返回绝对路径。"""
    pos = getattr(args, 'file_pos', None)
    opt = getattr(args, 'file_opt', None)
    if not pos and not opt:
        parser.error('缺少文件路径：用法 %s <file> 或 --file <path>' % parser.prog)
    if pos and opt and os.path.abspath(pos) != os.path.abspath(opt):
        parser.error('位置参数 %r 与 --file %r 指向不同文件' % (pos, opt))
    return os.path.abspath(pos or opt)


def read_text(path):
    """读文件，失败时打印到 stderr 并 exit 2（不抛 traceback）。"""
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except OSError as e:
        print('错误：无法读取文件 %s: %s' % (path, e), file=sys.stderr)
        sys.exit(EXIT_ERROR)


def missing_dependency(name, hint=''):
    """缺依赖时统一报错：exit 2，不抛 traceback。"""
    print('错误：缺少依赖 %s。%s' % (name, hint), file=sys.stderr)
    sys.exit(EXIT_ERROR)


def run_main(main_fn):
    """垫片入口包装：main_fn 返回退出码；未捕获异常转 exit 2（无 traceback）。"""
    try:
        sys.exit(main_fn())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 - 顶层兜底，保证契约退出码
        print('运行错误：%s' % e, file=sys.stderr)
        sys.exit(EXIT_ERROR)
