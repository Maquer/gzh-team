#!/usr/bin/env python3
"""
gzh-brand.py：公众号品牌视觉统一入口（minis-cli gzh 子命令）
用法：生成品牌视觉资产时调用（cover/all/check/list 子命令）
关键约束：需指定子命令，基准 md5 锁定见 BASELINE.md
"""
import argparse
import hashlib
import os
import subprocess
import sys

TEAM = '/var/minis/shared/gzh-team'
OUT = f'{TEAM}/assets/out'
BASELINE_DOC = f'{TEAM}/BASELINE.md'

# 基准 md5（前 8 位）。改动基准图前必须先改这里 + BASELINE.md。
BASELINE = {
    '封面图-实测3款本地部署模型.png': '06eb8371',
    '首图-关注引导.png':             '37ed8611',
    '尾图-v4.png':                   '3ad5c9d2',
    '尾图-v4-预告.png':              'f012ecb4',
    '品牌名-方案A-定稿.png':         'd94b84fa',
}

COVER_TITLE = '实测3款本地部署模型'   # 基准封面图所用标题，改前先看 BASELINE.md


def md5(path, n=8):
    h = hashlib.md5(open(path, 'rb').read()).hexdigest()
    return h[:n]


def run(cmd):
    r = subprocess.run(cmd, cwd=TEAM, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f'[ERROR] {' '.join(cmd)} exit={r.returncode}\n')
        sys.stderr.write(r.stderr or r.stdout)
        return False
    for line in r.stdout.strip().splitlines():
        print(f'  {line}')
    return True


def gen_brand():
    return run(['python3', f'{TEAM}/brand-font-schemes.py'])


def gen_cover(title=COVER_TITLE):
    return run(['python3', f'{TEAM}/cover-dynamic.py', title])


def cmd_cover(a):
    print('生成封面图（带标题 900x383）…')
    if not gen_cover(a.title):
        return 1
    print(f'输出：{OUT}/封面图-{a.title}.png')
    return 0


def cmd_all(a):
    print('全量重生成 5 张基准图…')
    ok = gen_brand()
    ok &= gen_cover()
    return 0 if ok else 1


def cmd_check(a):
    os.makedirs(OUT, exist_ok=True)
    expect = set(BASELINE)
    actual = {f for f in os.listdir(OUT) if f.endswith('.png')}
    drift = missing = 0

    print('基准图 md5 校验')
    for f, want in BASELINE.items():
        if f not in actual:
            print(f'  [缺失] {f}')
            missing += 1
            continue
        got = md5(f'{OUT}/{f}')
        ok = got == want
        drift += 0 if ok else 1
        mark = 'OK' if ok else f'DRIFT 期望 {want}'
        print(f'  {"[OK]  " if ok else "[差异]"} {f}  {got}  {mark}')

    extra = sorted(actual - expect)
    if extra:
        print(f'\n[漂移] 目录内 {len(extra)} 个非基准文件（应只有 {len(BASELINE)} 张）：')
        for f in extra:
            print(f'  {f}  {os.path.getsize(f"{OUT}/{f}"):>7}B  {md5(f"{OUT}/{f}")}  ← 待确认保留或删除')

    print(f'\n结论：{len(BASELINE)} 张基准中 {len(BASELINE) - drift - missing} 张匹配'
          f'，{drift} 张漂移，{missing} 张缺失；额外文件 {len(extra)} 个')
    if drift or missing or extra:
        print('修复：`minis-cli gzh all` 重生成（会覆盖漂移项）；'
              '确认要保留的额外文件后更新 BASELINE.md 与本脚本 BASELINE 表')
        return 1
    print('基准无漂移 ✓')
    return 0


def cmd_list(a):
    print(f'{"产物":34s} {"脚本::函数":40s} 尺寸')
    for name, fn, size in [
        ('封面图-*.png', 'cover-dynamic.py::generate_cover()', '900x383'),
        ('首图-关注引导.png', 'brand-font-schemes.py::make_follow_cover()', '450x200'),
        ('尾图-v4.png', 'brand-font-schemes.py::make_tail()', '900x400'),
        ('尾图-v4-预告.png', 'brand-font-schemes.py::make_tail(next_title=)', '900x400'),
        ('品牌名-方案A-定稿.png', 'brand-font-schemes.py::make_preview()', '1000x320'),
    ]:
        print(f'{name:34s} {fn:40s} {size}')
    print(f'\n基准文档：{BASELINE_DOC}')


def main():
    ap = argparse.ArgumentParser(
        prog='minis-cli gzh',
        description='公众号品牌视觉统一入口（封面图/首图/尾图，基准 md5 锁定）')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('cover', help='生成封面图（带标题 900x383）')
    p.add_argument('title', nargs='?', default=COVER_TITLE, help='标题（默认用基准标题）')
    p.set_defaults(func=cmd_cover)

    p = sub.add_parser('all', help='全量重生成 5 张基准图')
    p.set_defaults(func=cmd_all)

    p = sub.add_parser('check', help='基准漂移检测（md5 比对 + 额外文件清点）')
    p.set_defaults(func=cmd_check)

    p = sub.add_parser('list', help='列出产物与生成脚本对应关系')
    p.set_defaults(func=cmd_list)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == '__main__':
    main()
