#!/usr/bin/env python3
"""recover.py：由拆分产物反向重建冻结源 TEAM.md.bak-pre-split。

v4.0.0 重建：最小改动，只做结构清理——顶层逻辑收进 main()，
import 不再执行（v3.x 通病）；重建算法逐字保留。
用法：python3 recover.py
关键约束：依赖 split.py 的 MAP 与 docs/ 下拆分产物；
产物布局与冻结源不符时不写出（exit 1）；输入缺失时 exit 2。

注意：MAP 直接从 split.py 源码中读取，保证两边映射一致。
"""
import io
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT_PY = os.path.join(HERE, 'split.py')
N = 1020  # 冻结源 TEAM.md.bak-pre-split 的行数


def load_map():
    """从 split.py 源码读取 MAP。失败返回 None。"""
    try:
        s = io.open(SPLIT_PY, encoding='utf-8').read().split('\n')
        i = [k for k, l in enumerate(s) if l.strip().startswith('MAP = [')][0]
        j = [k for k, l in enumerate(s[i + 1:], i + 1) if l.strip() == ']'][0]
    except (OSError, IndexError):
        return None
    d = {'N': N}
    try:
        exec(textwrap.dedent('\n'.join(s[i:j + 1])), d)
    except Exception:
        return None
    return sorted(d['MAP'])


def read_product(path):
    """读取拆分产物正文（去 frontmatter）。失败抛 OSError。"""
    r = io.open(path, encoding='utf-8').read()
    k = r.index('\n---\n\n')
    return r[k + 6:].rstrip('\n').split('\n')


def main():
    parser = gzh_cli.build_parser(
        "recover.py", "由拆分产物反向重建冻结源 TEAM.md.bak-pre-split")
    parser.parse_args()  # 仅 --help；无参数
    M = load_map()
    if M is None:
        print('recover.py: 无法从 split.py 读取 MAP，未重建。', file=sys.stderr)
        return 2

    try:
        st = io.open('TEAM.md', encoding='utf-8').read().split('\n')
    except OSError as e:
        print('recover.py: 无法读取 TEAM.md: %s，未重建。' % e, file=sys.stderr)
        return 2

    files = {}
    for a, b, p in M:
        if p != 'IDX':
            files.setdefault(p, []).append((a, b))
    F = {}
    G = {}
    try:
        for p, segs in files.items():
            body = read_product(p)
            exp = sum(b - a + 1 for a, b in segs) + len(segs) - 1
            F[p] = body
            G[p] = exp - len(body)
            assert len(body) > 0 and any(x.strip() for x in body), (p, body[:2])
    except (OSError, ValueError) as e:
        print('recover.py: 拆分产物缺失或损坏 (%s)，未重建。' % e, file=sys.stderr)
        return 2

    O = {}
    L = []
    t = 0
    for a, b, p in M:
        n = b - a + 1
        if p == 'IDX':
            L += st[a - 1:b]
            t += 1
            continue
        segs = files[p]
        li = segs.index((a, b))
        if li == len(segs) - 1:
            n -= G[p]
        cur = O.get(p, 0)
        assert len(F[p][cur:cur + n]) == n, (p, cur, n)
        L += F[p][cur:cur + n]
        O[p] = cur + n + (1 if li < len(segs) - 1 else 0)
        if li == len(segs) - 1:
            L += [''] * G[p]

    if len(L) != 1019:
        print('recover.py: 重建得到 %d 行，与冻结源布局（1019 行）不符；'
              'docs/ 已被改动，未写出备份。' % len(L), file=sys.stderr)
        return 1
    if L and L[-1] == '' and len(L) > 1:
        pass  # 已有尾部空行
    elif not L or L[-1] != '':
        L.append('')  # frozen 末尾有空行，重建时补上
    assert len(L) == 1020 or (L and L[-1] == '' and len(L) == 1019), len(L)
    io.open('TEAM.md.bak-pre-split', 'w', encoding='utf-8').write('\n'.join(L))
    print('lines', len(L), 'bytes', len('\n'.join(L).encode()), 'idx', t)
    return 0


if __name__ == '__main__':
    gzh_cli.run_main(main)
