#!/usr/bin/env python3
"""gzh-brand.py：公众号品牌视觉统一入口。

v4 垫片：子命令与 v3.3.0 一致（cover / all / check / list），
通过 subprocess 调度同目录下的垫片脚本。
基准 md5 锁定：改动基准图前先更新 BASELINE 表（公开版重建后基准已失效，
check 仅做机械比对，见重建报告）。
"""
import argparse
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEAM = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TEAM, 'assets', 'out')
BASELINE_DOC = os.path.join(TEAM, 'BASELINE.md')

# 基准 md5（前 8 位）。公开版脱敏重建后旧基准不再匹配，仅保留结构。
BASELINE = {
    '封面图-实测3款本地部署模型.png': 'a0307a88',
    '首图-关注引导.png':             '1a3a2ba3',
    '尾图-v4.png':                   'a219d658',
    '尾图-v4-预告.png':              '74941e00',
    '品牌名-方案A-定稿.png':         '746185e9',
}

COVER_TITLE = '实测3款本地部署模型'  # 基准封面图所用标题，改前先看 BASELINE.md


def md5(path, n=8):
    h = hashlib.md5(open(path, 'rb').read()).hexdigest()
    return h[:n]


def run(cmd):
    r = subprocess.run(cmd, cwd=TEAM, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write('[ERROR] %s exit=%d\n' % (' '.join(cmd), r.returncode))
        sys.stderr.write(r.stderr or r.stdout)
        return False
    for line in r.stdout.strip().splitlines():
        print('  %s' % line)
    return True


def gen_brand():
    return run([sys.executable, os.path.join(TEAM, 'brand-font-schemes.py'), '--all'])


def gen_cover(title=COVER_TITLE):
    # v3.3.0 曾把标题直接当正文路径传给 cover-dynamic.py（该路径不存在即失败）；
    # v4 改为走 cover-card.py --title（标题型封面的正确入口）。
    return run([sys.executable, os.path.join(TEAM, 'cover-card.py'),
                '--title', title])


def cmd_cover(a):
    print('生成封面图（带标题 900x383）…')
    if not gen_cover(a.title):
        return 1
    print('输出：%s/封面图-%s.png' % (OUT, a.title))
    return 0


def cmd_all(a):
    print('全量重生成 5 张基准图…')
    ok = gen_brand()
    ok = gen_cover() and ok
    return 0 if ok else 1


def cmd_check(a):
    os.makedirs(OUT, exist_ok=True)
    expect = set(BASELINE)
    actual = {f for f in os.listdir(OUT) if f.endswith('.png')}
    drift = missing = 0

    print('基准图 md5 校验')
    for f, want in BASELINE.items():
        if f not in actual:
            print('  [缺失] %s' % f)
            missing += 1
            continue
        got = md5(os.path.join(OUT, f))
        ok = got == want
        drift += 0 if ok else 1
        print('  %s %s  %s  %s'
              % ('[OK]  ' if ok else '[差异]', f, got,
                 'OK' if ok else 'DRIFT 期望 %s' % want))

    extra = sorted(actual - expect)
    if extra:
        print('\n[漂移] 目录内 %d 个非基准文件（应只有 %d 张）：'
              % (len(extra), len(BASELINE)))
        for f in extra:
            p = os.path.join(OUT, f)
            print('  %s  %7dB  %s  ← 待确认保留或删除' % (f, os.path.getsize(p), md5(p)))

    print('\n结论：%d 张基准中 %d 张匹配，%d 张漂移，%d 张缺失；额外文件 %d 个'
          % (len(BASELINE), len(BASELINE) - drift - missing, drift, missing, len(extra)))
    if drift or missing or extra:
        print('修复：`python3 gzh-brand.py all` 重生成（会覆盖漂移项）；'
              '确认要保留的额外文件后更新 BASELINE.md 与本脚本 BASELINE 表')
        return 1
    print('基准无漂移 ✓')
    return 0


def cmd_list(a):
    print('%-34s %-40s 尺寸' % ('产物', '脚本::函数'))
    for name, fn, size in [
        ('封面图-*.png', 'cover-card.py::cover()', '900x383'),
        ('封面图-动态提取.png', 'cover-dynamic.py::generate_cover()', '900x383'),
        ('首图-关注引导.png', 'brand-font-schemes.py::make_follow_cover()', '1080x216'),
        ('尾图-v4.png', 'brand-font-schemes.py::make_tail()', '900x400'),
        ('尾图-v4-预告.png', 'brand-font-schemes.py::make_tail(next_title=)', '900x400'),
        ('品牌名-方案A-定稿.png', 'brand-font-schemes.py::make_preview()', '450x200'),
    ]:
        print('%-34s %-40s %s' % (name, fn, size))
    print('\n基准文档：%s' % BASELINE_DOC)


def main():
    ap = argparse.ArgumentParser(
        prog='gzh-brand.py',
        description='公众号品牌视觉统一入口（封面图/首图/尾图，基准 md5 锁定）')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('cover', help='生成封面图（带标题 900x383）')
    p.add_argument('title', nargs='?', default=COVER_TITLE, help='标题（默认用基准标题）')
    p.set_defaults(func=cmd_cover)

    p = sub.add_parser('all', help='全量重生成品牌资产图')
    p.set_defaults(func=cmd_all)

    p = sub.add_parser('check', help='基准漂移检测（md5 比对 + 额外文件清点）')
    p.set_defaults(func=cmd_check)

    p = sub.add_parser('list', help='列出产物与生成脚本对应关系')
    p.set_defaults(func=cmd_list)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == '__main__':
    main()
