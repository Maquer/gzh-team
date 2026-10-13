#!/usr/bin/env python3
"""gzh-structure-diversity.py：检查结构多样性约束（G8门禁）。

v4.0.0 重建：干净重写，识别逻辑与 v3.3.0 一致。
用法：python3 gzh-structure-diversity.py <file> [--verbose] [--history FILE]

硬约束：
  1. 连续2篇不能用同类骨架（A-F型）
  2. 禁止固定起手式（先说结论/这次不一样等）
  3. 禁止固定收尾式（一句话总结/你的选择等）

骨架类型识别：
  A 序数词：一、二、三、四、五 明确编号
  B 问答体：Q:/问/答/回答 交替出现
  C 案例体：完整故事线，有人物有转折
  D 清单体：· 符号开头 + 无标题段落
  E 场景体：从具体场景/人物切入
  F 对话体：A:/B: 虚拟对话

退出码：0 通过；1 警告；7 BLOCK（连续同类骨架）；2 参数错误 / 文件不可读。
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli


# ── 骨架类型识别函数 ──────────────────────────────────────────────
def detect_structure(text):
    """返回 (骨架类型, 置信度, 证据)"""
    lines = text.split('\n')

    # A: 序数词骨架
    a_pattern = re.compile(r'^#{1,3}\s*[一二三四五六七八九十]+[、.．．]', re.MULTILINE)
    a_matches = a_pattern.findall(text)
    if len(a_matches) >= 3:
        return ('A', '高', '发现%d处序数词标题' % len(a_matches))

    # B: 问答骨架
    b_pattern = re.compile(r'[Qq][Uu][Ee]?:|[？?]([^？?\n]{5,})[？?]|^[^\n]*？[^\n]*$',
                           re.MULTILINE | re.IGNORECASE)
    b_matches = b_pattern.findall(text)
    q_count = len([m for m in b_matches if m.strip()])
    if q_count >= 3:
        return ('B', '中', '发现%d处问答结构' % q_count)

    # C: 案例骨架（需人工确认，此处仅做初步标记）
    c_keywords = ['某年某月', '有一天', '我记得', '那天', '他/她/我', '结果', '最后']
    c_count = sum(1 for kw in c_keywords if re.search(kw, text))
    if c_count >= 4:
        return ('C', '低', '发现%d处案例特征词' % c_count)

    # D: 清单骨架
    d_pattern = re.compile(r'^[·\-\*]\s+', re.MULTILINE)
    d_matches = d_pattern.findall(text)
    if len(d_matches) >= 5 and len(a_matches) < 2:
        return ('D', '中', '发现%d处列表项，无序数词' % len(d_matches))

    # E: 场景骨架（默认兜底）
    return ('E', '低', '无明显模板特征，可能为场景/其他类型')


# ── 禁用起手式检测 ────────────────────────────────────────────────
DISABLED_OPENINGS = [
    r'先说结论',
    r'一句话概括',
    r'这次不一样',
    r'这次值得重视',
    r'这意味着什么',
    r'先给结论',
    r'直接说结论',
]


def check_openings(text):
    """检查是否使用禁用起手式"""
    lines = text.split('\n')
    # 取前5行正文（跳过H1和元信息）
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('## ') and not line.startswith('###'):
            body_start = i
            break

    first_lines = '\n'.join(lines[body_start:body_start + 5])
    hits = []
    for pat in DISABLED_OPENINGS:
        if re.search(pat, first_lines):
            hits.append('发现禁用起手式：%s' % pat)
    return hits


# ── 禁用收尾式检测 ────────────────────────────────────────────────
DISABLED_CLOSINGS = [
    r'一句话总结',
    r'你的选择',
    r'你怎么看',
    r'评论区聊聊',
    r'欢迎在评论区',
]


def check_closings(text):
    """检查是否使用禁用收尾式"""
    lines = text.split('\n')
    last_lines = '\n'.join(lines[-10:])
    hits = []
    for pat in DISABLED_CLOSINGS:
        if re.search(pat, last_lines):
            hits.append('发现禁用收尾式：%s' % pat)
    return hits


def main():
    parser = gzh_cli.build_parser("gzh-structure-diversity.py", "G8 结构多样性门禁")
    parser.add_argument('file', help='稿件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    parser.add_argument('--history', default=None, help='历史稿件目录（用于检测连续同类）')
    args = parser.parse_args()

    text = gzh_cli.read_text(args.file)

    blocks = []
    warns = []

    # 1. 检测骨架类型
    structure, confidence, evidence = detect_structure(text)
    if args.verbose:
        print('骨架类型: %s (%s) - %s' % (structure, confidence, evidence))

    # 2. 检测连续同类（如果有历史记录）
    if args.history:
        history_dir = Path(args.history)
        latest = None
        latest_struct = None
        for f in sorted(history_dir.glob('*/正文.md')):
            if f != Path(args.file):
                latest = f
                latest_struct, _, _ = detect_structure(f.read_text('utf-8'))

        if latest and latest_struct == structure:
            blocks.append('连续2篇同类骨架：%s 和 %s 都是 %s 型'
                          % (latest.name, args.file, structure))
        elif args.verbose:
            print('历史对比：上一篇 %s 是 %s 型，本次是 %s 型 ✓'
                  % (latest.name, latest_struct, structure))

    # 3. 检测禁用起手式
    for hit in check_openings(text):
        warns.append(hit)
        if args.verbose:
            print('警告: %s' % hit)

    # 4. 检测禁用收尾式
    for hit in check_closings(text):
        warns.append(hit)
        if args.verbose:
            print('警告: %s' % hit)

    # 输出结果
    print('\n=== G8 结构多样性门禁 ===')
    print('稿件: %s' % args.file)
    print('骨架类型: %s (%s)' % (structure, confidence))

    if blocks:
        print('\n❌ BLOCK (%d项):' % len(blocks))
        for b in blocks:
            print('  - %s' % b)
        return 7

    if warns:
        print('\n⚠️ WARN (%d项):' % len(warns))
        for w in warns:
            print('  - %s' % w)
        print('\n建议修改后重新检查，不阻塞发布')
        return 1

    print('\n✅ PASS: 结构多样性检查通过')
    return 0


if __name__ == '__main__':
    gzh_cli.run_main(main)
