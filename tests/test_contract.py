#!/usr/bin/env python3
"""gzh-team v4.0.0 契约测试。

验证标准（设计文档）：
1. 41 个脚本 --help 退出 0，无 traceback
2. 无参数 / 错误参数 → 退出 2，无 traceback
3. ast.parse 全脚本语法通过

运行：python3 tests/test_contract.py
"""
import ast
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# 顶层 36 个 + training/ 5 个 = 41
EXPECTED_SCRIPTS = [
    # 门禁组（10）
    'gate-check.py', 'gate-G0-check.py', 'gate-G3-check.py', 'gate-G7-check.py',
    'gate-G8-check.py', 'gate-H11-check.py', 'gate-H12-check.py',
    'gate-H14-check.py', 'gate-H15-check.py', 'gate-version-check.py',
    # 视觉组（12）
    'cover-brief.py', 'cover-card.py', 'cover-dynamic.py', 'cover-new-style.py',
    'cover-pipeline.py', 'cover-recommend.py', 'cover-summary.py',
    'cover_styles.py', 'follow-cards.py', 'brand-font-schemes.py',
    'gzh-brand.py', 'gzh-typeset.py',
    # 协作杂项（14）
    'archive_note_generator.py', 'archives_optimizer.py',
    'component-registry.py', 'gzh-api-push.py', 'gzh-h14-explain.py',
    'gzh-precheck.py', 'gzh-structure-diversity.py', 'link-check.py',
    'persona-layers.py', 'persona.py', 'recover.py', 'split.py',
    'turn-reminders.py', 'verify-all.py',
    # training/（5）
    'training/gzh-call.py', 'training/gzh-dispatch.py',
    'training/role-patterns.py', 'training/run-baselines.py',
    'training/train-check.py',
]

PASS = 0
FAIL = 1


def run(script, *args, timeout=30):
    p = subprocess.run([PY, os.path.join(ROOT, script), *args],
                       capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    return p


def check(name, cond, detail=''):
    status = 'PASS' if cond else 'FAIL'
    print('[%s] %s %s' % (status, name, detail))
    return PASS if cond else FAIL


def main():
    failures = 0

    # 0. 文件清单完整
    missing = [s for s in EXPECTED_SCRIPTS
               if not os.path.exists(os.path.join(ROOT, s))]
    failures += check('scripts-present', not missing,
                      'missing=%s' % missing if missing else '41/41')

    # 1. ast 语法
    py_files = []
    for dirpath, _, fns in os.walk(ROOT):
        if 'tests' in dirpath:
            continue
        for fn in fns:
            if fn.endswith('.py'):
                py_files.append(os.path.join(dirpath, fn))
    for f in sorted(py_files):
        try:
            with open(f, encoding='utf-8') as fh:
                ast.parse(fh.read())
            ok = True
        except SyntaxError as e:
            ok = False
            print('   syntax error in %s: %s' % (f, e))
        failures += check('syntax:' + os.path.relpath(f, ROOT), ok)

    # 2. --help 退出 0 且无 traceback
    for s in EXPECTED_SCRIPTS:
        if not os.path.exists(os.path.join(ROOT, s)):
            continue
        try:
            p = run(s, '--help')
            ok = (p.returncode == 0 and 'Traceback' not in p.stderr
                  and 'Traceback' not in p.stdout)
            failures += check('help:' + s, ok,
                              'rc=%d' % p.returncode if not ok else '')
        except subprocess.TimeoutExpired:
            failures += check('help:' + s, False, 'timeout')

    # 3. 无参数 → exit 2（需要位置参数的脚本），无 traceback
    #    例外：纯信息类脚本（无必填参数）允许 exit 0
    needs_arg = [s for s in EXPECTED_SCRIPTS
                 if not s.startswith('cover_styles')
                 and 'persona' not in s and 'turn-reminders' not in s
                 and 'component-registry' not in s
                 and 'archives_optimizer' not in s
                 and 'archive_note_generator' not in s
                 and 'role-patterns' not in s]
    for s in needs_arg:
        if not os.path.exists(os.path.join(ROOT, s)):
            continue
        try:
            p = run(s)
            ok = (p.returncode == 2 and 'Traceback' not in p.stderr)
            # 允许某些脚本无参数时打印用法 exit 2，或走交互；只禁 traceback 和 exit 0 误导
            if p.returncode == 0:
                ok = False
            failures += check('noarg:' + s, ok,
                              'rc=%d' % p.returncode if not ok else '')
        except subprocess.TimeoutExpired:
            failures += check('noarg:' + s, False, 'timeout')

    print('\n=== %s (%d failures) ==='
          % ('ALL GREEN' if failures == 0 else 'FAILURES', failures))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
