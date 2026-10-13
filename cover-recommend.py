#!/usr/bin/env python3
"""cover-recommend.py：文章→调性打分→风格→可执行命令。

v4 垫片：CLI 参数与 v3.3.0 一致，风格表走 gzhkit.visual.styles，
调性打分复用 gzh-typeset 融合版实现（importlib 加载，与 v3.3.0 同口径）。
用法：生成封面前调用 --article 正文.md 推荐风格
关键约束：需指定文章路径；--run 可直连出图，否则只输出命令
"""
import argparse
import datetime
import importlib.util
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit.visual.styles import DESIGNER_STYLES, TONE_TO_STYLE

HERE = os.path.dirname(os.path.abspath(__file__))
TYPESET_CANDIDATES = [
    os.environ.get('GZH_TYPESET_IMPL', ''),
    os.path.join(HERE, '..', 'gzh-typeset', 'gzh-typeset.py'),
]


def find_typeset_impl():
    for impl in TYPESET_CANDIDATES:
        if impl and os.path.isfile(impl) \
                and os.path.abspath(impl) != os.path.abspath(__file__):
            return impl
    return None


def load_detect_tone():
    impl = find_typeset_impl()
    if not impl:
        print('FATAL: 排版器不存在（候选：%s；可用环境变量 GZH_TYPESET_IMPL 指定）'
              % ' / '.join(c for c in TYPESET_CANDIDATES if c), file=sys.stderr)
        sys.exit(2)
    spec = importlib.util.spec_from_file_location('_typeset', impl)
    mod = importlib.util.module_from_spec(spec)
    # typeset 尾部有 argparse，但 __name__ != '__main__' 时走不进 main，导入安全
    spec.loader.exec_module(mod)
    return mod.detect_tone, mod.TONES


# ── 正文提取 ──────────────────────────────────────────────
BODY_RE = re.compile(
    r'(?:##\s*正文[^\n]*\n)(.*?)(?=\n##\s*(?:备选标题|已选标题|缺口判断|AI 参与|配图指导|交付前自检|自检|发布|项目状态|数据来源|结尾)|\Z)',
    re.S)
H1_RE = re.compile(r'^#\s+(.+?)\s*$', re.M)
STRATEGY_TAG_RE = re.compile(r'\s*[（(]\s*策略\s*[:：][^）)]+[）)]\s*[:：]?\s*')
DATE_RE = re.compile(r'(20\d{2})[.\-/年]?\s?(\d{1,2})[.\-/月]?\s?(\d{1,2})?')


def extract_title(md, fallback='未命名'):
    for m in H1_RE.finditer(md):
        t = STRATEGY_TAG_RE.sub('', m.group(1)).strip()
        t = re.sub(r'\s*[·|｜\-—]\s*(正文|初稿|终稿|定稿)\s*$', '', t).strip()
        if t and not t.startswith('正文') and len(t) >= 4:
            if len(t) <= 28:
                return t
            head = t[:28]
            for sep in ('，', '。', '：', '、', '；', ' ', ','):
                cut = head.rfind(sep)
                if cut >= 12:
                    return head[:cut].rstrip('，。：、；，')
            return head
    return fallback


def extract_points(md, limit=4):
    pts, seen = [], set()
    for m in re.finditer(r'^\s*\d+[\.、]\s*\*\*([^*]{4,20})\*\*', md, re.M):
        p = m.group(1).strip()
        if p not in seen:
            seen.add(p)
            pts.append(p)
        if len(pts) >= limit:
            return pts
    if len(pts) < 2:
        for m in re.finditer(r'^###\s+(.+?)\s*$', md, re.M):
            p = STRATEGY_TAG_RE.sub('', m.group(1)).strip()
            if 4 <= len(p) <= 20 and p not in seen \
                    and '自检' not in p and '参考' not in p:
                seen.add(p)
                pts.append(p)
            if len(pts) >= limit:
                break
    return pts


def extract_date(md, path=''):
    for src in (os.path.basename(path), md[:400]):
        m = DATE_RE.search(src)
        if m:
            return '%s.%02d' % (m.group(1), int(m.group(2)))
    now = datetime.date.today()
    return '%d.%02d' % (now.year, now.month)


def main():
    ap = argparse.ArgumentParser(prog='cover-recommend.py', description='封面调性推荐器')
    ap.add_argument('--article', required=True, help='正文 .md 路径')
    ap.add_argument('--tone', choices=list(TONE_TO_STYLE.keys()),
                    help='锁定调性（跳过打分）')
    ap.add_argument('--style', help='直接指定风格（跳过推荐）')
    ap.add_argument('--layout', default='structured', choices=['simple', 'structured'])
    ap.add_argument('--no-accent', action='store_true', help='不对齐排版主色')
    ap.add_argument('--points', default=None, help='手工覆盖要点（逗号分隔）')
    ap.add_argument('--title', default=None, help='手工覆盖标题')
    ap.add_argument('--date', default=None, help='手工覆盖日期')
    ap.add_argument('--out', default=None, help='输出路径')
    ap.add_argument('--quiet', action='store_true', help='只输出风格名')
    ap.add_argument('--run', action='store_true', help='直接执行 cover-pipeline.py 出图')
    a = ap.parse_args()

    if not os.path.exists(a.article):
        print('FATAL: 正文不存在 %s' % a.article, file=sys.stderr)
        return 2
    with open(a.article, encoding='utf-8') as f:
        md = f.read()

    # 1. 调性：锁定 > 打分
    if a.tone:
        tone, scores = a.tone, None
    else:
        detect_tone, _TONES = load_detect_tone()
        tone, scores = detect_tone(md)

    rec = TONE_TO_STYLE[tone]
    rank = rec['rank']
    chosen = a.style if a.style in DESIGNER_STYLES else rank[0]

    title = a.title or extract_title(md)
    points = a.points if a.points is not None else ','.join(extract_points(md))
    date = a.date or extract_date(md, a.article)
    # 输出名：正文.md → 用父目录名（选题 id），避免全叫「正文-cover.png」互相覆盖
    base = os.path.splitext(os.path.basename(a.article))[0]
    slug = base if base != '正文' else os.path.basename(os.path.dirname(os.path.abspath(a.article)))
    out = a.out or os.path.join(HERE, 'assets', '%s-cover.png' % slug)

    style = DESIGNER_STYLES[chosen]

    if a.quiet:
        print(chosen)
        return 0

    # 2. 报告推荐理由
    print('调性判定: %s (%s)%s' % (tone, rec['label'],
          '  [手工锁定]' if a.tone else '  [打分]'))
    if scores:
        top = scores[tone]
        val, hits = (top[0], top[1]) if isinstance(top, tuple) else (top, [])
        print('  得分 %s  命中 %s' % (val, ' '.join(hits) if hits else '无（回退默认）'))
    print('推荐风格: %s (%s · %s)' % (chosen, style['name'], style['desc']))
    print('备选:     %s' % ', '.join(rank[1:]))

    # 3. 调性主色对齐提示
    if not a.no_accent:
        p = rec['primary']
        print('配色:   (建议强调色对齐排版主色 #%02X%02X%02X'
              '，当前风格用 #%02X%02X%02X)'
              % (p[0], p[1], p[2],
                 style['accent'][0], style['accent'][1], style['accent'][2]))
    print('提取: 标题「%s」 要点 %d 项  日期 %s'
          % (title, len(points.split(',')) if points else 0, date))

    # 4. 拼命令
    cmd = ['python3', os.path.join(HERE, 'cover-pipeline.py'),
           '--base', 'pil', '--layout', a.layout, '--style', chosen,
           '--title', title]
    if points:
        cmd += ['--points', points]
    if date and style.get('badge_shape', 'none') != 'none':
        cmd += ['--date', date]
    cmd += ['--out', out]

    print('\n可直接执行:')
    print('  ' + ' '.join('"%s"' % c if ' ' in c or len(c) > 12 else c for c in cmd))
    print('\n输出: %s' % out)

    if a.run:
        print('\n[执行出图]')
        r = subprocess.run(cmd)
        return r.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
