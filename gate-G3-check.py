#!/usr/bin/env python3
"""
gate-G3-check.py：G3门禁检查（标题策略/字数/结构）
用法：python3 gate-G3-check.py <参数>
关键约束：exit 0=PASS, 1=FAIL
"""
import argparse
import json
import os
import re
import sys

TEMPLATES = {
    '标准观点': {'sections': (3,5), 'words_per_section': (200,350), 'total_words': (800,1200), 'gold_min': 2},
    '评测横比': {'sections': (5,7), 'words_per_section': (150,300), 'total_words': (800,1500), 'gold_min': 3},
    '教程方法': {'sections': (4,6), 'words_per_section': (150,250), 'total_words': (600,1200), 'gold_min': 2},
    '资讯热点': {'sections': (3,4), 'words_per_section': (200,400), 'total_words': (600,1200), 'gold_min': 2},
    '复盘成长': {'sections': (4,6), 'words_per_section': (200,300), 'total_words': (800,1200), 'gold_min': 2},
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('markdown', help='结构案 Markdown 路径')
    ap.add_argument('--template', help='模板名称（可选，自动检测）')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    if not os.path.isfile(args.markdown):
        print(f'ERROR: 文件不存在 {args.markdown}', file=sys.stderr)
        sys.exit(2)

    t = open(args.markdown).read()

    # 检测模板类型（用正则匹配模板名作为独立词，避免子串误匹配）
    template_name = args.template
    if not template_name:
        for name in TEMPLATES:
            if re.search(rf'(?<![\u4e00-\u9fff]){name}(?![\u4e00-\u9fff])', t):
                template_name = name
                break
        if not template_name:
            template_name = '标准观点'  # 默认

    params = TEMPLATES.get(template_name, TEMPLATES['标准观点'])

    # 统计节数
    sections = len(re.findall(r'^###\s+', t, re.M))

    # 统计字数
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', t))

    # 统计金句（优先数【金句】标记，退化时数加粗）
    gold_count = t.count('【金句】')
    if gold_count == 0:
        gold_count = len(re.findall(r'\*\*[^*]+\*\*', t))

    # 检查素材引用
    material_refs = len(re.findall(r'\[R-\d+\]', t))

    results = []
    fails = []

    # 1. 节数
    s_min, s_max = params['sections']
    status = 'PASS' if s_min <= sections <= s_max else 'FAIL'
    detail = f'{sections} 节（要求 {s_min}-{s_max}）'
    results.append({'项': '节数', '状态': status, '依据': detail})
    if status == 'FAIL':
        fails.append(f'节数 {sections}，要求 {s_min}-{s_max}')

    # 2. 总字数
    w_min, w_max = params['total_words']
    status = 'PASS' if w_min <= zh_chars <= w_max else 'FAIL'
    detail = f'{zh_chars} 字（要求 {w_min}-{w_max}）'
    results.append({'项': '总字数', '状态': status, '依据': detail})
    if status == 'FAIL':
        fails.append(f'总字数 {zh_chars}，要求 {w_min}-{w_max}')

    # 3. 金句数量
    status = 'PASS' if gold_count >= params['gold_min'] else 'FAIL'
    detail = f'{gold_count} 处加粗（要求 ≥{params["gold_min"]}）'
    results.append({'项': '金句数量', '状态': status, '依据': detail})
    if status == 'FAIL':
        fails.append(f'金句 {gold_count} 处，要求 ≥{params["gold_min"]}')

    # 4. 素材引用
    status = 'PASS' if material_refs >= 1 else 'WARN'
    detail = f'{material_refs} 处素材引用'
    results.append({'项': '素材引用', '状态': status, '依据': detail})

    # 输出
    pass_count = sum(1 for r in results if r['状态'] == 'PASS')
    fail_count = sum(1 for r in results if r['状态'] == 'FAIL')
    warn_count = sum(1 for r in results if r['状态'] == 'WARN')

    if args.json:
        print(json.dumps({'template': template_name, 'pass': pass_count, 'fail': fail_count, 'warn': warn_count, 'results': results}, ensure_ascii=False, indent=2))
    else:
        print(f'G3 结构门禁检查（模板：{template_name}）')
        print(f'{"─"*50}')
        for r in results:
            icon = {'PASS': '✅', 'FAIL': '❌', 'WARN': '⚠️'}.get(r['状态'], '❓')
            print(f'{icon} {r["项"]}: {r["依据"]}')
        print(f'{"─"*50}')
        print(f'PASS: {pass_count} | FAIL: {fail_count} | WARN: {warn_count}')
        if fails:
            print('\n❌ FAIL 项:')
            for f in fails:
                print(f'  - {f}')

    sys.exit(1 if fail_count > 0 else 0)

if __name__ == '__main__':
    main()