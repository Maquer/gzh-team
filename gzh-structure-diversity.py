#!/usr/bin/env python3
"""
gzh-structure-diversity.py：检查结构多样性约束（G8门禁）
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
"""
import sys,re,argparse,os
from pathlib import Path

# ── 骨架类型识别函数 ──────────────────────────────────────────────
def detect_structure(text):
    """返回 (骨架类型, 置信度, 证据)"""
    lines = text.split('\n')
    
    # A: 序数词骨架
    a_pattern = re.compile(r'^#{1,3}\s*[一二三四五六七八九十]+[、.．．]', re.MULTILINE)
    a_matches = a_pattern.findall(text)
    if len(a_matches) >= 3:
        return ('A', '高', f'发现{len(a_matches)}处序数词标题')
    
    # B: 问答骨架
    b_pattern = re.compile(r'[Qq][Uu][Ee]?:|[？?]([^？?\n]{5,})[？?]|^[^\n]*？[^\n]*$', re.MULTILINE | re.IGNORECASE)
    b_matches = b_pattern.findall(text)
    q_count = len([m for m in b_matches if m.strip()])
    if q_count >= 3:
        return ('B', '中', f'发现{q_count}处问答结构')
    
    # C: 案例骨架（需人工确认，此处仅做初步标记）
    c_keywords = ['某年某月', '有一天', '我记得', '那天', '他/她/我', '结果', '最后']
    c_count = sum(1 for kw in c_keywords if re.search(kw, text))
    if c_count >= 4:
        return ('C', '低', f'发现{c_count}处案例特征词')
    
    # D: 清单骨架
    d_pattern = re.compile(r'^[·\-\*]\s+', re.MULTILINE)
    d_matches = d_pattern.findall(text)
    if len(d_matches) >= 5 and len(a_matches) < 2:
        return ('D', '中', f'发现{len(d_matches)}处列表项，无序数词')
    
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
    
    first_lines = '\n'.join(lines[body_start:body_start+5])
    hits = []
    for pat in DISABLED_OPENINGS:
        if re.search(pat, first_lines):
            hits.append(f'发现禁用起手式：{pat}')
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
            hits.append(f'发现禁用收尾式：{pat}')
    return hits


# ── 主函数 ────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='G8 结构多样性门禁')
    ap.add_argument('file', help='稿件路径')
    ap.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    ap.add_argument('--history', default=None, help='历史稿件目录（用于检测连续同类）')
    a = ap.parse_args()
    
    with open(a.file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    blocks = []
    warns = []
    
    # 1. 检测骨架类型
    structure, confidence, evidence = detect_structure(text)
    if a.verbose:
        print(f'骨架类型: {structure} ({confidence}) - {evidence}')
    
    # 2. 检测连续同类（如果有历史记录）
    if a.history:
        history_dir = Path(a.history)
        latest = None
        latest_struct = None
        for f in sorted(history_dir.glob('*/正文.md')):
            if f != Path(a.file):
                latest = f
                latest_struct, _, _ = detect_structure(f.read_text('utf-8'))
        
        if latest and latest_struct == structure:
            blocks.append(f'连续2篇同类骨架：{latest.name} 和 {a.file} 都是 {structure} 型')
        elif a.verbose:
            print(f'历史对比：上一篇 {latest.name} 是 {latest_struct} 型，本次是 {structure} 型 ✓')
    
    # 3. 检测禁用起手式
    opening_hits = check_openings(text)
    for hit in opening_hits:
        warns.append(hit)
        if a.verbose:
            print(f'警告: {hit}')
    
    # 4. 检测禁用收尾式
    closing_hits = check_closings(text)
    for hit in closing_hits:
        warns.append(hit)
        if a.verbose:
            print(f'警告: {hit}')
    
    # 输出结果
    print(f'\n=== G8 结构多样性门禁 ===')
    print(f'稿件: {a.file}')
    print(f'骨架类型: {structure} ({confidence})')
    
    if blocks:
        print(f'\n❌ BLOCK ({len(blocks)}项):')
        for b in blocks:
            print(f'  - {b}')
        sys.exit(7)
    
    if warns:
        print(f'\n⚠️ WARN ({len(warns)}项):')
        for w in warns:
            print(f'  - {w}')
        print('\n建议修改后重新检查，不阻塞发布')
        sys.exit(1)
    
    print('\n✅ PASS: 结构多样性检查通过')
    sys.exit(0)


if __name__ == '__main__':
    main()
