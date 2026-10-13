#!/usr/bin/env python3
"""
gzh-precheck.py：写作中实时预检工具

用途：主笔写作过程中快速检查，不用等写完再跑完整门禁
命令：
  python3 gzh-precheck.py <正文文件>              # 快速检查（3项）
  python3 gzh-precheck.py <正文文件> --full       # 完整检查（含H14）
  python3 gzh-precheck.py <正文文件> --skeleton   # 只检查骨架类型

退出码：
  0 = 通过（可继续写作）
  1 = 警告（建议调整，但不阻断）
  2 = 阻断（必须修改）
"""

import sys
import re
import os
import json
import subprocess
from collections import Counter

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
        p = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=30)
        out = (p.stdout or '') + (p.stderr or '')
        m = re.search(r'综合评分[:：]\s*(\d+)\s*分', out)
        if not m:
            m = re.search(r'(\d+)\s*分', out)
        if m:
            return int(m.group(1)), None
        return None, f'解析失败: {out.strip()[:100]}'
    except subprocess.TimeoutExpired:
        return None, '超时（30秒）'
    except Exception as e:
        return None, f'调用异常: {e}'

def get_history():
    """获取历史骨架记录"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            data = json.load(f)
        return data.get('history', [])
    except:
        return []

def save_history(structure):
    """保存骨架记录"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = get_history()
    history.append({
        'file': sys.argv[1] if len(sys.argv) > 1 else 'unknown',
        'structure': structure,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })
    # 只保留最近10条
    history = history[-10:]
    with open(HISTORY_FILE, 'w') as f:
        json.dump({'history': history}, f, ensure_ascii=False, indent=2)

def main():
    if len(sys.argv) < 2:
        print('用法：python3 gzh-precheck.py <正文文件> [--full|--skeleton]')
        sys.exit(2)
    
    filepath = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else '--quick'
    
    try:
        with open(filepath) as f:
            text = f.read()
    except Exception as e:
        print(f'错误：无法读取文件 {filepath}: {e}')
        sys.exit(2)
    
    print('=' * 60)
    print('📝 写作中预检报告')
    print('=' * 60)
    
    warnings = []
    blocks = []
    
    # 1. 字数检查
    zh = check_word_count(text)
    print(f'\n📊 正文字数：{zh} 字')
    if zh < 200:
        blocks.append(f'字数 {zh} < 200（疑似漏写）')
        print(f'   ❌ BLOCK：字数不足，至少需要 200 字')
    elif zh < 500:
        warnings.append(f'字数 {zh} < 500（短稿）')
        print(f'   ⚠️  WARN：字数偏少，短稿可发但建议扩充')
    else:
        print(f'   ✅ PASS：字数充足')
    
    # 2. 段落检查
    over, total = check_paragraphs(text)
    print(f'\n📄 段落检查：{total} 段，{over} 段超 3 句')
    if over > 0:
        warnings.append(f'{over} 段超 3 句')
        print(f'   ⚠️  WARN：{over} 段需要拆分')
    else:
        print(f'   ✅ PASS：全段落达标')
    
    # 3. 骨架检查
    if mode in ('--quick', '--skeleton'):
        structure, count, counts = detect_structure(text)
        print(f'\n🏗️  骨架类型：{structure}（{count} 个标记）')
        
        # 检查连续同类
        history = get_history()
        if history and len(history) >= 1:
            prev = history[-1].get('structure', 'unknown')
            if structure == prev and structure != 'unknown':
                warnings.append(f'连续2篇同类骨架（{structure}型）')
                print(f'   ⚠️  WARN：连续2篇{structure}型骨架，建议换结构')
            else:
                print(f'   ✅ PASS：与上一篇（{prev}型）不同')
        else:
            print(f'   ℹ️  首次发布，无历史记录')
        
        # 检查禁用句
        opening_hits, closing_hits = check_opening_closing(text)
        if opening_hits:
            warnings.append(f'禁用起手式：{", ".join(opening_hits)}')
            print(f'   ⚠️  WARN：禁用起手式 {", ".join(opening_hits)}')
        if closing_hits:
            warnings.append(f'禁用收尾式：{", ".join(closing_hits)}')
            print(f'   ⚠️  WARN：禁用收尾式 {", ".join(closing_hits)}')
        if not opening_hits and not closing_hits:
            print(f'   ✅ PASS：无禁用句式')
    
    # 4. AI味检查（仅--full模式）
    if mode == '--full':
        print(f'\n🤖 AI味检查：')
        score, err = check_humanizer(text, quick=False)
        if score is not None:
            print(f'   分数：{score} 分')
            if score > 25:
                blocks.append(f'H14 AI味 {score} 分 > 25（推倒重写）')
                print(f'   ❌ BLOCK：AI味超标，需要重写')
            elif score > 5:
                warnings.append(f'H14 AI味 {score} 分')
                print(f'   ⚠️  WARN：AI味偏高，建议优化')
            else:
                print(f'   ✅ PASS：AI味达标')
        else:
            print(f'   ℹ️  跳过：{err}')
    else:
        print(f'\n🤖 AI味检查：--full 模式才运行（当前 --{mode[2:]}）')
    
    # 总结
    print('\n' + '=' * 60)
    if blocks:
        print(f'❌ BLOCK：{len(blocks)} 项阻断')
        for b in blocks:
            print(f'   • {b}')
        sys.exit(2)
    elif warnings:
        print(f'⚠️  WARN：{len(warnings)} 项警告（不阻断，建议调整）')
        for w in warnings:
            print(f'   • {w}')
        sys.exit(1)
    else:
        print('✅ PASS：全项通过，可继续写作')
        sys.exit(0)

if __name__ == '__main__':
    main()
