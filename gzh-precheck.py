#!/usr/bin/env python3
"""gzh-precheck.py：写作中实时预检工具。

v4.0.0 重建：干净重写，检查逻辑与 v3.3.0 一致（行为保留）。
用途：主笔写作过程中快速检查，不用等写完再跑完整门禁。
命令：
  python3 gzh-precheck.py <正文文件>              # 快速检查（3项：字数/段落/骨架）
  python3 gzh-precheck.py <正文文件> --full       # 完整检查（含H14 AI味）
  python3 gzh-precheck.py <正文文件> --skeleton   # 只检查骨架类型

退出码：
  0 = 通过（可继续写作）
  1 = 警告或阻断（建议调整；v3.3.0 曾用 2 表示阻断，v4.0.0 统一为 1）
  2 = 参数错误 / 文件不可读
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

# 配置
GZH_TEAM_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.environ.get('GZH_SHARED_DIR', os.path.dirname(GZH_TEAM_DIR))
HUMANIZER = os.path.join(SHARED_DIR, 'humanizer-check', 'humanizer-check.py')
HISTORY_FILE = os.path.expanduser('~/.gzh-structure-history/structure-log.json')

# 禁用句库
OPENING_BANNED = ['先说结论', '这次不一样', '你知道吗', '最近发现']
CLOSING_BANNED = ['一句话总结', '你的选择', '你怎么看', '评论区聊聊']

# 骨架检测
ORDINAL_RE = re.compile(r'^#{1,3}\s*(一|二|三|四|五|六|七|八|九|十)\s*[、.]')
QA_RE = re.compile(r'^(Q[1-9]|[1-9]?)\s*[：:]')
CASE_RE = re.compile(r'^(案例|Case)\s*[1-9]')
LIST_RE = re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]')
SCENE_RE = re.compile(r'^(场景|Scenario)\s*[A-Z]')
DIALOG_RE = re.compile(r'^[甲乙丙丁]：')


def detect_structure(text):
    """检测骨架类型"""
    lines = text.split('\n')
    counts = {
        'A_ordinal': 0,
        'B_qa': 0,
        'C_case': 0,
        'D_list': 0,
        'E_scene': 0,
        'F_dialog': 0,
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ORDINAL_RE.match(line):
            counts['A_ordinal'] += 1
        elif QA_RE.match(line):
            counts['B_qa'] += 1
        elif CASE_RE.match(line):
            counts['C_case'] += 1
        elif LIST_RE.match(line):
            counts['D_list'] += 1
        elif SCENE_RE.match(line):
            counts['E_scene'] += 1
        elif DIALOG_RE.match(line):
            counts['F_dialog'] += 1

    max_type = max(counts, key=counts.get)
    max_count = counts[max_type]

    if max_count == 0:
        return 'unknown', 0, counts
    elif max_count >= 2:
        return max_type.split('_')[1], max_count, counts
    else:
        return 'mixed', max_count, counts


def check_opening_closing(text):
    """检查开头/结尾禁用句"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return [], []

    opening = lines[0] if lines else ''
    closing = lines[-1] if lines else ''

    opening_hits = [s for s in OPENING_BANNED if s in opening]
    closing_hits = [s for s in CLOSING_BANNED if s in closing]

    return opening_hits, closing_hits


def check_word_count(text):
    """检查字数"""
    # 去重
    text_dedup = text
    for _ in range(20):
        text_dedup = re.sub(r'(\S+?)\1{1,3}', r'\1', text_dedup)

    zh = len(re.findall(r'[\u4e00-\u9fff]', text_dedup))
    return zh


def check_paragraphs(text):
    """检查段落超3句"""
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    over = 0
    for p in paras:
        sents = len([x for x in re.split(r'[。！？]', p) if x.strip()])
        if sents > 3:
            over += 1
    return over, len(paras)


def check_humanizer(text, quick=True):
    """快速AI味检查"""
    if not os.path.exists(HUMANIZER):
        return None, 'humanizer-check.py 不存在'

    cmd = [sys.executable, HUMANIZER]
    if quick:
        cmd.append('--quick')  # 如果支持的话

    try:
        import subprocess
        p = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=30)
        out = (p.stdout or '') + (p.stderr or '')
        m = re.search(r'综合评分[:：]\s*(\d+)\s*分', out)
        if not m:
            m = re.search(r'(\d+)\s*分', out)
        if m:
            return int(m.group(1)), None
        return None, '解析失败: %s' % out.strip()[:100]
    except Exception as e:
        return None, '调用异常: %s' % e


def get_history():
    """获取历史骨架记录"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('history', [])
    except Exception:
        return []


def save_history(structure):
    """保存骨架记录（v3.3.0 起定义但未在 main 中调用，行为保留：不调用）。"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = get_history()
    history.append({
        'structure': structure,
        'timestamp': datetime.now().isoformat(),
    })
    # 只保留最近10条
    history = history[-10:]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump({'history': history}, f, ensure_ascii=False, indent=2)


def main():
    parser = gzh_cli.build_parser(
        "gzh-precheck.py",
        "写作中实时预检（快速3项 / --full 完整含H14 / --skeleton 骨架模式）")
    parser.add_argument('file', help='正文文件路径')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--full', action='store_true', help='完整检查（含H14 AI味）')
    group.add_argument('--skeleton', action='store_true', help='只检查骨架类型')
    args = parser.parse_args()

    text = gzh_cli.read_text(args.file)
    mode = '--full' if args.full else ('--skeleton' if args.skeleton else '--quick')

    print('=' * 60)
    print('📝 写作中预检报告')
    print('=' * 60)

    warnings = []
    blocks = []

    # 1. 字数检查
    zh = check_word_count(text)
    print('\n📊 正文字数：%d 字' % zh)
    if zh < 200:
        blocks.append('字数 %d < 200（疑似漏写）' % zh)
        print('   ❌ BLOCK：字数不足，至少需要 200 字')
    elif zh < 500:
        warnings.append('字数 %d < 500（短稿）' % zh)
        print('   ⚠️  WARN：字数偏少，短稿可发但建议扩充')
    else:
        print('   ✅ PASS：字数充足')

    # 2. 段落检查
    over, total = check_paragraphs(text)
    print('\n📄 段落检查：%d 段，%d 段超 3 句' % (total, over))
    if over > 0:
        warnings.append('%d 段超 3 句' % over)
        print('   ⚠️  WARN：%d 段需要拆分' % over)
    else:
        print('   ✅ PASS：全段落达标')

    # 3. 骨架检查
    if mode in ('--quick', '--skeleton'):
        structure, count, counts = detect_structure(text)
        print('\n🏗️  骨架类型：%s（%d 个标记）' % (structure, count))

        # 检查连续同类
        history = get_history()
        if history and len(history) >= 1:
            prev = history[-1].get('structure', 'unknown')
            if structure == prev and structure != 'unknown':
                warnings.append('连续2篇同类骨架（%s型）' % structure)
                print('   ⚠️  WARN：连续2篇%s型骨架，建议换结构' % structure)
            else:
                print('   ✅ PASS：与上一篇（%s型）不同' % prev)
        else:
            print('   ℹ️  首次发布，无历史记录')

        # 检查禁用句
        opening_hits, closing_hits = check_opening_closing(text)
        if opening_hits:
            warnings.append('禁用起手式：%s' % "，".join(opening_hits))
            print('   ⚠️  WARN：禁用起手式 %s' % "，".join(opening_hits))
        if closing_hits:
            warnings.append('禁用收尾式：%s' % "，".join(closing_hits))
            print('   ⚠️  WARN：禁用收尾式 %s' % "，".join(closing_hits))
        if not opening_hits and not closing_hits:
            print('   ✅ PASS：无禁用句式')

    # 4. AI味检查（仅--full模式）
    if mode == '--full':
        print('\n🤖 AI味检查：')
        score, err = check_humanizer(text, quick=False)
        if score is not None:
            print('   分数：%d 分' % score)
            if score > 25:
                blocks.append('H14 AI味 %d 分 > 25（推倒重写）' % score)
                print('   ❌ BLOCK：AI味超标，需要重写')
            elif score > 5:
                warnings.append('H14 AI味 %d 分' % score)
                print('   ⚠️  WARN：AI味偏高，建议优化')
            else:
                print('   ✅ PASS：AI味达标')
        else:
            print('   ℹ️  跳过：%s' % err)
    else:
        print('\n🤖 AI味检查：--full 模式才运行（当前 --%s）' % mode[2:])

    # 总结（v4.0.0 统一：检查不通过 → exit 1）
    print('\n' + '=' * 60)
    if blocks:
        print('❌ BLOCK：%d 项阻断' % len(blocks))
        for b in blocks:
            print('   • %s' % b)
        return 1
    if warnings:
        print('⚠️  WARN：%d 项警告（不阻断，建议调整）' % len(warnings))
        for w in warnings:
            print('   • %s' % w)
        return 1
    print('✅ PASS：全项通过，可继续写作')
    return 0


if __name__ == '__main__':
    gzh_cli.run_main(main)
