#!/usr/bin/env python3
"""gzh-h14-explain.py：AI味可解释性评分。

v4.0.0 重建：干净重写，行为保留——每条命中规则详情 + 改写建议 + 统计。
用途：humanizer-check 的详细版，输出每条规则的命中详情和改写建议。
命令：
  python3 gzh-h14-explain.py <正文文件>           # 详细报告
  python3 gzh-h14-explain.py <正文文件> --policy  # 政策类豁免模式
  python3 gzh-h14-explain.py <正文文件> --json    # JSON输出（供脚本消费）

退出码：
  0 = 通过（≤5分）
  1 = 未通过（>5分，或无法解析分数；v3.3.0 曾用 2 表示 >25 分阻断，v4.0.0 统一为 1）
  2 = 参数错误 / 文件不可读 / humanizer-check 缺失或调用失败
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

# 配置
GZH_TEAM_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.environ.get('GZH_SHARED_DIR', os.path.dirname(GZH_TEAM_DIR))
HUMANIZER = os.path.join(SHARED_DIR, 'humanizer-check', 'humanizer-check.py')


def run_humanizer(text, policy=False):
    """调用 humanizer-check 获取详细结果。返回 (output, err)。"""
    if not os.path.exists(HUMANIZER):
        return None, 'humanizer-check.py不存在: %s' % HUMANIZER

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
        return None, '调用异常: %s' % e


def parse_results(output):
    """解析 humanizer-check 输出。"""
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
        results['rules'].append({
            'rule_id': m.group(1),
            'rule_name': m.group(2).strip(),
            'count': int(m.group(3)),
            'description': m.group(4).strip(),
            'example': m.group(5).strip()[:200],  # 截断过长的示例
        })

    # 提取豁免信息（如果有的话）
    exempt_pattern = re.compile(r'豁免[:：]?\s*(.+)', re.DOTALL)
    m = exempt_pattern.search(output)
    if m:
        results['summary']['exempted'] = m.group(1).strip()[:100]

    return results


def get_suggestions(rule_id):
    """获取规则改写建议。"""
    suggestions = {
        '3': '打破句式重复，调整句子结构',
        '6': '换用非序数词标题（如问答/案例/场景）',
        '10A': '缩短前置定语，拆分长修饰语',
        '10': '调整定语位置或简化修饰',
        '1': '改写翻案腔（"不是A而是B"→直接说B）',
        '2': '减少顿号罗列，改用分句或列举',
        '5': '减少空转冒号，改用完整句',
        '4B': '减少破折号，改用逗号或句号',
        '10C': '减少长句，拆分复杂句',
    }
    return suggestions.get(rule_id, '参考规则编号改写')


def print_detailed_report(text, filepath, output, policy=False):
    """打印详细报告。返回退出码（0 通过 / 1 未通过）。"""
    print('=' * 60)
    print('📝 AI味可解释性评分报告')
    print('=' * 60)

    if policy:
        print('\n📌 模式：政策类豁免（豁免规则1翻案腔/规则2顿号罗列/规则5冒号空转）')

    print('\n📄 文件：%s' % filepath)
    print('📊 正文字数：%d 字符' % len(text))

    results = parse_results(output)

    # 输出总分
    score = results['total_score']
    if score is not None:
        if score <= 5:
            print('\n📊 综合评分：%d 分  🟢 通过（≤5分放行）' % score)
        elif score <= 15:
            print('\n📊 综合评分：%d 分  🟡 警告（6-15分，建议重写≥50%%）' % score)
        else:
            print('\n📊 综合评分：%d 分  🔴 阻断（>25分，推倒重写）' % score)
    else:
        print('\n⚠️  无法解析总分')

    # 输出各规则详情
    if results['rules']:
        print('\n🔍 命中规则详情：')
        print('-' * 60)

        for rule in results['rules']:
            print('\n规则%s·%s' % (rule['rule_id'], rule['rule_name']))
            print('  命中：%d 处' % rule['count'])
            print('  描述：%s' % rule['description'])

            if rule['example']:
                print('  示例：%s...' % rule['example'][:100])

            # 改写建议
            suggestions = get_suggestions(rule['rule_id'])
            if suggestions:
                print('  💡 改写建议：%s' % suggestions)

        print('-' * 60)

    # 改写原则
    print('\n🔧 改写原则（白名单式）：')
    print('  1. 只改命中规则处，未命中句子逐字保留')
    print('  2. 每处改动对应明确规则编号')
    print('  3. 不润色、不改语气、不调结构')
    print('  4. 不补虚词、不换代词、不调句长')

    # 统计
    total_hits = sum(r['count'] for r in results['rules'])
    print('\n📈 统计：%d 条规则命中，共 %d 处' % (len(results['rules']), total_hits))

    # 判定（v4.0.0 统一：检查不通过 → exit 1）
    print('\n' + '=' * 60)
    if score is not None:
        if score <= 5:
            print('✅ 判定：通过（≤5分放行）')
            return 0
        print('⚠️  判定：未通过（%d分，建议重写≥50%%）' % score)
        return 1
    print('❌ 判定：无法判定')
    return 1


def main():
    parser = gzh_cli.build_parser(
        "gzh-h14-explain.py",
        "AI味可解释性评分（每条命中规则详情 + 改写建议 + 统计）")
    parser.add_argument('file', help='正文文件路径')
    parser.add_argument('--policy', action='store_true', help='政策类豁免模式')
    parser.add_argument('--json', dest='json_mode', action='store_true',
                        help='JSON输出（供脚本消费）')
    args = parser.parse_args()

    text = gzh_cli.read_text(args.file)

    output, err = run_humanizer(text, args.policy)
    if err:
        if args.json_mode:
            print(json.dumps({'error': err}, ensure_ascii=False))
        else:
            print('错误：%s' % err)
        return 2

    results = parse_results(output)

    if args.json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        score = results['total_score']
        return 0 if (score is not None and score <= 5) else 1

    return print_detailed_report(text, args.file, output, args.policy)


if __name__ == '__main__':
    gzh_cli.run_main(main)
