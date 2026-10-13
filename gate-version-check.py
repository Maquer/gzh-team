#!/usr/bin/env python3
"""垫片：gate-version-check.py —— 版本号全链一致性检查。

CHANGELOG.md 最新条目为 SSOT；校验 TEAM.md（frontmatter version / 头部
"> vX.Y.Z" 行）与 README.md（标题 / 版本历史表最新行 / 尾注）一致；
最新条目须含四要素（**触发** / **修改文件** / **影响面** / **决策或变更内容**）。
exit code: 0=PASS / 1=FAIL / 2=运行错误（与 v3.3.0 一致）
"""
import os
import re
import sys

from gzhkit import cli

VER = r"v?(\d+\.\d+(?:\.\d+)?)"


def _read(base, name):
    p = os.path.join(base, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return f.read()


def _find(pattern, text, group=1, last=False):
    if not text:
        return None
    ms = re.findall(pattern, text, flags=re.M)
    if not ms:
        return None
    return ms[-1] if last else ms[0]


USAGE = ('用法：python3 gate-version-check.py\n'
         '  校验 CHANGELOG.md / TEAM.md / README.md 版本号全链一致（CHANGELOG 为 SSOT）。\n'
         '  exit code: 0=PASS / 1=FAIL / 2=运行错误')


def main():
    parser = cli.build_parser(
        'gate-version-check.py', '版本号全链一致性检查（CHANGELOG 为 SSOT）',
        epilog='exit code: 0=PASS, 1=FAIL, 2=运行错误')
    parser.add_argument('base', metavar='REPO_ROOT',
                        help='仓库根目录（含 CHANGELOG.md / TEAM.md / README.md）')
    args = parser.parse_args()
    base = args.base
    results = []

    def check(label, value, expect):
        ok = value is not None and value == expect
        results.append((ok, label, value if value is not None else '缺失'))
        return ok

    # ---- CHANGELOG 最新条目 = SSOT ----
    chlog = _read(base, 'CHANGELOG.md')
    heads = re.findall(r'^## .*', chlog or '', flags=re.M)
    ssot, entry_body = None, ''
    if heads:
        last = heads[-1]
        m = re.search(VER, last)
        ssot = m.group(1) if m else None
        entry_body = chlog[chlog.rfind(last):]
        results.append((ssot is not None, 'CHANGELOG 最新条目含版本号', last))
        for kw in ['触发', '修改文件', '影响面']:
            ok = '**' + kw in entry_body
            results.append((ok, '条目四要素: ' + kw,
                            '✅' if ok else '❌ 缺 **%s**' % kw))
        decided = any(('**' + k) in entry_body
                      for k in ['决策', '变更内容', '最终裁定'])
        results.append((decided, '条目四要素: 决策/变更内容',
                        '✅' if decided else '❌ 缺 **决策** 或 **变更内容**'))
    else:
        results.append((False, 'CHANGELOG 无任何条目', '❌'))

    # ---- 各处版本号 ----
    team = _read(base, 'TEAM.md')
    readme = _read(base, 'README.md')
    if ssot:
        check('TEAM.md frontmatter version',
              _find(r'^version:\s*"([^"]+)"', team), ssot)
        check('TEAM.md 头部行 > vX.Y.Z', _find(r'^>\s*v' + VER, team), ssot)
        check('README 标题', _find(r'^#\s+公众号写作团队\s+v' + VER, readme), ssot)
        check('README 版本历史表最新行',
              _find(r'^\|\s*\*{0,2}v' + VER + r'\*{0,2}\s*\|', readme, last=True), ssot)
        check('README 尾注', _find(r'\*版本：v' + VER + r'\*', readme), ssot)
    else:
        results.append((False, '无法确定 SSOT 版本，跳过比对', '❌'))

    for ok, label, val in results:
        print('%s %s: %s' % ('✅' if ok else '🔴', label, val))
    print('---')
    fails = [r for r in results if not r[0]]
    if fails:
        print('FAIL: %d 项不通过。SSOT=CHANGELOG 最新版本 %s' % (len(fails), ssot))
        print('按 TEAM.md §2 提交前五步：补 CHANGELOG 条目 / 同步三处版本号后重跑。')
        return 1
    print('PASS: 版本号全链一致 = v%s，最新条目四要素齐全。' % ssot)
    return 0


if __name__ == '__main__':
    cli.run_main(main)
