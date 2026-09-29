#!/usr/bin/env python3
"""封面调性推荐器 · 文章 → 调性打分 → 风格 → 可执行命令

复用 gzh-typeset.py 融合版的 detect_tone（5 档调性 + 关键词加权），
保证「封面调性 = 正文排版调性」，封面强调色对齐排版主色。

用法:
  # 从正文 .md 自动推荐（推荐：自动提标题/要点/日期）
  python3 cover-recommend.py --article 正文.md

  # 只要推荐不要命令
  python3 cover-recommend.py --article 正文.md --quiet

  # 锁定调性（跳过打分）
  python3 cover-recommend.py --article 正文.md --tone urgent

  # 直接出图（推荐→调性主色对齐→调 cover-pipeline.py）
  python3 cover-recommend.py --article 正文.md --run

设计边界（勿误用）:
  - 打分纯属词面统计，无 LLM。命中词为 0 时回退 analytical（与 typeset 一致）。
  - 只推荐 1 主推 + 2 备选，不自动出图（除非 --run）。
  - 标题/要点/日期为「尽力提取」，正文结构不规范时建议手工覆盖参数。
"""
import argparse, datetime, importlib.util, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TYPESET = '/var/minis/shared/gzh-typeset/gzh-typeset.py'

sys.path.insert(0, HERE)
from cover_styles import DESIGNER_STYLES, TONE_TO_STYLE


def load_detect_tone():
    """从融合版 typeset 动态载入 detect_tone + TONES（文件名带连字符，只能 importlib）。"""
    if not os.path.exists(TYPESET):
        print(f'FATAL: 排版器不存在 {TYPESET}', file=sys.stderr)
        sys.exit(2)
    spec = importlib.util.spec_from_file_location('_typeset', TYPESET)
    mod = importlib.util.module_from_spec(spec)
    # typeset 尾部有 argparse，导入时会执行；用 __name__!='__main__' 走不进 main，安全
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
        # 去掉尾部段名标记：「xxx · 正文」「xxx - 正文」「xxx｜正文」
        t = re.sub(r'\s*[·|｜\-—]\s*(正文|初稿|终稿|定稿)\s*$', '', t).strip()
        if t and not t.startswith('正文') and len(t) >= 4:
            if len(t) <= 28:
                return t
            # 超长优先在标点处断，避免切一半词
            head = t[:28]
            for sep in ('，', '。', '：', '、', '；', ' ', ','):
                cut = head.rfind(sep)
                if cut >= 12:
                    return head[:cut].rstrip('，。：、；，')
            return head
    return fallback


def extract_points(md, limit=4):
    """提编号清单项：优先 `1. **粗体**` 动作句，退到 H2/H3 小标题。"""
    pts, seen = [], set()
    # 1. 粗体动作句：`1. **xxx**` 或 `**xxx**：`
    for m in re.finditer(r'^\s*\d+[\.、]\s*\*\*([^*]{4,20})\*\*', md, re.M):
        p = m.group(1).strip()
        if p not in seen:
            seen.add(p); pts.append(p)
        if len(pts) >= limit:
            return pts
    # 2. 退到 H3 小标题
    if len(pts) < 2:
        for m in re.finditer(r'^###\s+(.+?)\s*$', md, re.M):
            p = STRATEGY_TAG_RE.sub('', m.group(1)).strip()
            if 4 <= len(p) <= 20 and p not in seen and '自检' not in p and '参考' not in p:
                seen.add(p); pts.append(p)
            if len(pts) >= limit:
                break
    return pts


def extract_date(md, path=''):
    for src in (os.path.basename(path), md[:400]):
        m = DATE_RE.search(src)
        if m:
            y, mo = m.group(1), m.group(2)
            return f'{y}.{int(mo):02d}'
    now = datetime.date.today()
    return f'{now.year}.{now.month:02d}'


def main():
    ap = argparse.ArgumentParser(description='封面调性推荐器')
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
        print(f'FATAL: 正文不存在 {a.article}', file=sys.stderr)
        return 2
    md = open(a.article, encoding='utf-8').read()

    # 1. 调性：锁定 > 打分
    if a.tone:
        tone = a.tone
        scores = None
    else:
        detect_tone, TONES = load_detect_tone()
        tone, scores = detect_tone(md)

    rec = TONE_TO_STYLE[tone]
    rank = rec['rank']

    if a.style:
        chosen = a.style if a.style in DESIGNER_STYLES else rank[0]
    else:
        chosen = rank[0]

    title = a.title or extract_title(md)
    points = a.points if a.points is not None else ','.join(extract_points(md))
    date = a.date or extract_date(md, a.article)
    # 输出名：正文.md → 用父目录名（选题 id），避免全叫「正文-cover.png」互相覆盖
    base = os.path.splitext(os.path.basename(a.article))[0]
    slug = base if base != '正文' else os.path.basename(os.path.dirname(os.path.abspath(a.article)))
    out = a.out or os.path.join(HERE, 'assets', f'{slug}-cover.png')

    style = DESIGNER_STYLES[chosen]

    if a.quiet:
        print(chosen)
        return 0

    # 2. 报告推荐理由
    print(f'调性判定: {tone} ({rec["label"]})'
          + ('  [手工锁定]' if a.tone else '  [打分]'))
    if scores:
        top = scores[tone]
        hits = top[1] if isinstance(top, tuple) else []
        val = top[0] if isinstance(top, tuple) else top
        print(f'  得分 {val}  命中 {" ".join(hits) if hits else "无（回退默认）"}')
    print(f'推荐风格: {chosen} ({style["name"]} · {style["desc"]})')
    print(f'备选:     {", ".join(rank[1:])}')

    # 3. 调性主色对齐提示
    accent_note = ''
    if not a.no_accent:
        p = rec['primary']
        accent_note = (f'  (建议强调色对齐排版主色 #{p[0]:02X}{p[1]:02X}{p[2]:02X}'
                       f'，当前风格用 #{style["accent"][0]:02X}{style["accent"][1]:02X}{style["accent"][2]:02X})')
    print(f'提取: 标题「{title}」 要点 {len(points.split(",")) if points else 0} 项  日期 {date}')
    print(f'配色: {accent_note}')

    # 4. 拼命令
    cmd = ['python3', os.path.join(HERE, 'cover-pipeline.py'),
           '--base', 'pil', '--layout', a.layout, '--style', chosen,
           '--title', title]
    if points:
        cmd += ['--points', points]
    style_needs_date = style.get('badge_shape', 'none') != 'none'
    if date and style_needs_date:
        cmd += ['--date', date]
    cmd += ['--out', out]

    print('\n可直接执行:')
    print('  ' + ' '.join(f'"{c}"' if ' ' in c or len(c) > 12 else c for c in cmd))
    print(f'\n输出: {out}')

    if a.run:
        print('\n[执行出图]')
        r = subprocess.run(cmd)
        return r.returncode
    return 0


sys.exit(main())
