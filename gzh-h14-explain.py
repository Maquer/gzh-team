#!/usr/bin/env python3
"""
gzh-h14-explain.py：AI味可解释性评分

用途：humanizer-check的详细版，输出每条规则的命中详情和改写建议
命令：
  python3 gzh-h14-explain.py <正文文件>           # 详细报告
  python3 gzh-h14-explain.py <正文文件> --policy  # 政策类豁免模式
  python3 gzh-h14-explain.py <正文文件> --json    # JSON输出（供脚本消费）

退出码：
  0 = 通过（≤5分）
  1 = 警告（6-15分，建议重写≥50%）
  2 = 阻断（>25分，推倒重写）
"""

import sys
import re
import os
import json
import subprocess
from collections import defaultdict

# 配置
GZH_TEAM_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.environ.get('GZH_SHARED_DIR', os.path.dirname(GZH_TEAM_DIR))
HUMANIZER = os.path.join(SHARED_DIR, 'humanizer-check', 'humanizer-check.py')

def run_humanizer(text, policy=False):
    """调用humanizer-check获取详细结果"""
    if not os.path.exists(HUMANIZER):
        return None, f'humanizer-check.py不存在: {HUMANIZER}'
    
    cmd = [sys.executable, HUMANIZER]
    if policy:
        cmd.append('--policy-mode')
    
    try:
        p = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=60)
        out = (p.stdout or '') + (p.stderr or '')
        return out, None
    except subprocess.TimeoutExpired:
        return None, '超时（60秒）'
    except Exception as e:
        return None, f'调用异常: {e}'

def parse_results(output):
    """解析humanizer-check输出"""
    results = {
        'total_score': None,
        'rules': [],
        'summary': {}
    }
    
    if not output:
        return results
    
    # 提取总分
    m = re.search(r'综合评分[:：]\s*(\d+)\s*分', output)
    if m:
        results['total_score'] = int(m.group(1))
    
    # 提取各规则（格式：🔍 规则X·名称（N处）: ⚠️ 描述 📄 示例）
    rule_pattern = re.compile(
        r'🔍\s*规则(\w+)\s*[·・](.+?)\s*[（(](\d+)\s*处[）)]\s*:\s*\n'
        r'\s+[⚠️❌]\s*(.+?)\s*\n'
        r'\s+📄\s*(.+)',
        re.DOTALL
    )
    
    for m in rule_pattern.finditer(output):
        rule_id = m.group(1)
        rule_name = m.group(2).strip()
        count = int(m.group(3))
        description = m.group(4).strip()
        example = m.group(5).strip()
        
        results['rules'].append({
            'rule_id': rule_id,
            'rule_name': rule_name,
            'count': count,
            'description': description,
            'example': example[:200]  # 截断过长的示例
        })
    
    # 提取豁免信息（如果有的话）
    exempt_pattern = re.compile(r'豁免[:：]?\s*(.+)', re.DOTALL)
    m = exempt_pattern.search(output)
    if m:
        results['summary']['exempted'] = m.group(1).strip()[:100]
    
    return results

def print_detailed_report(text, filepath, policy=False):
    """打印详细报告"""
    print('=' * 60)
    print('📝 AI味可解释性评分报告')
    print('=' * 60)
    
    if policy:
        print('\n📌 模式：政策类豁免（豁免规则1翻案腔/规则2顿号罗列/规则5冒号空转）')
    
    print(f'\n📄 文件：{filepath}')
    print(f'📊 正文字数：{len(text)} 字符')
    
    output, err = run_humanizer(text, policy)
    
    if err:
        print(f'\n❌ 错误：{err}')
        sys.exit(2)
    
    results = parse_results(output)
    
    # 输出总分
    if results['total_score'] is not None:
        score = results['total_score']
        if score <= 5:
            print(f'\n📊 综合评分：{score} 分  🟢 通过（≤5分放行）')
        elif score <= 15:
            print(f'\n📊 综合评分：{score} 分  🟡 警告（6-15分，建议重写≥50%）')
        else:
            print(f'\n📊 综合评分：{score} 分  🔴 阻断（>25分，推倒重写）')
    else:
        print('\n⚠️  无法解析总分')
    
    # 输出各规则详情
    if results['rules']:
        print('\n🔍 命中规则详情：')
        print('-' * 60)
        
        for rule in results['rules']:
            print(f'\n规则{rule["rule_id"]}·{rule["rule_name"]}')
            print(f'  命中：{rule["count"]} 处')
            print(f'  描述：{rule["description"]}')
            
            if rule['example']:
                print(f'  示例：{rule["example"][:100]}...')
            
            # 改写建议
            suggestions = get_suggestions(rule['rule_id'])
            if suggestions:
                print(f'  💡 改写建议：{suggestions}')
        
        print('-' * 60)
    
    # 改写原则
    print('\n🔧 改写原则（白名单式）：')
    print('  1. 只改命中规则处，未命中句子逐字保留')
    print('  2. 每处改动对应明确规则编号')
    print('  3. 不润色、不改语气、不调结构')
    print('  4. 不补虚词、不换代词、不调句长')
    
    # 统计
    total_hits = sum(r['count'] for r in results['rules'])
    print(f'\n📈 统计：{len(results["rules"])} 条规则命中，共 {total_hits} 处')
    
    # 判定
    print('\n' + '=' * 60)
    if results['total_score'] is not None:
        score = results['total_score']
        if score <= 5:
            print('✅ 判定：通过（≤5分放行）')
            sys.exit(0)
        elif score <= 25:
            print('⚠️  判定：警告（6-25分，建议重写≥50%）')
            sys.exit(1)
        else:
            print('❌ 判定：阻断（>25分，推倒重写）')
            sys.exit(2)
    else:
        print('❌ 判定：无法判定')
        sys.exit(2)

def get_suggestions(rule_id):
    """获取规则改写建议"""
    suggestions = {
        '3': '打破句式重复，调整句子结构',
        '6': '换用非序数词标题（如问答/案例/场景）',
        '10A': '缩短前置定语，拆分长修饰语',
        '10': '调整定语位置或简化修饰',
        '1': '改写翻案腔（"不是A而是B"→直接说B）',
        '2': '减少顿号罗列，改用分句或列举',
        '5': '减少空转冒号，改用完整句',
        '4B': '减少破折号，改用逗号或句号',
        '10C': '减少长句，拆分复杂句'
    }
    return suggestions.get(rule_id, '参考规则编号改写')

def main():
    if len(sys.argv) < 2:
        print('用法：python3 gzh-h14-explain.py <正文文件> [--policy|--json]')
        sys.exit(2)
    
    filepath = sys.argv[1]
    policy = '--policy' in sys.argv
    json_mode = '--json' in sys.argv
    
    try:
        with open(filepath) as f:
            text = f.read()
    except Exception as e:
        print(f'错误：无法读取文件 {filepath}: {e}')
        sys.exit(2)
    
    output, err = run_humanizer(text, policy)
    
    if err:
        if json_mode:
            print(json.dumps({'error': err}, ensure_ascii=False))
        else:
            print(f'错误：{err}')
        sys.exit(2)
    
    results = parse_results(output)
    
    if json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0 if results['total_score'] and results['total_score'] <= 5 else 1)
    else:
        print_detailed_report(text, filepath, policy)

if __name__ == '__main__':
    main()
