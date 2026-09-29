#!/usr/bin/env python3
# desensitize-v1.py — 数据脱敏 v1（2026-09-29）
# 目的：移除公共仓库中的内部运营数据（真实标题/阅读量/账号状态/周报截图）
# 原则：保留方法论与流程，替换具体运营数据为占位符
# 运行：python3 desensitize-v1.py && git add -A && git commit -m 'desensitize v1'

import re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------- 替换规则 ----------
RULES = [
    # 真实文章标题 → 通用占位符
    ('4部门14条新规：你的AI文章标注了吗', '【合规解读 A 篇】'),
    ('4 部门 14 条新规落地一年：你的 AI 文章标注了吗', '【合规解读 A 篇】'),
    ('4部门14条新规', '【合规解读 A 篇】'),
    ('网安周开幕式藏了个"智能体安全风险"', '【资讯 B 篇】'),
    ('网安周开幕式', '【资讯 B 篇】'),
    ('框架 3.0 那 4 个动作', '【政策解读 C 篇】'),
    ('wanganzhou《框架 3.0 那 4 个动作》', '【政策解读 C 篇（重发）】'),
    ('用 Obsidian 做了 30 天第二大脑', '【工具实测 D 篇】'),
    ('iOS 上跑 Linux + AI 流水线', '【工具实测 E 篇】'),
    ('实测 3 个模型别本地部署', '【工具实测 F 篇】'),
    ('5 个提示词模板', '【工具实测 G 篇】'),
    ('《框架 3.0 那 4 个动作', '【政策解读 C 篇'),

    # 阅读量具体数字 → 量级描述（先长后短避免二次命中）
    ('总外部触达 58 人', '总外部触达 [N] 人（量级：数十）'),
    ('53 阅读', '[峰值] 阅读'),
    ('阅读 53', '阅读 [峰值]'),
    ('53**', '[峰值]**'),
    ('**53**', '**[峰值]**'),
    ('阅读 **53**', '阅读 **[峰值]**'),
    ('阅读 = 0', '阅读 = 0'),  # 0 本身不敏感（结果值）
    ('36 阅读', '几十阅读'),
    ('51 阅读', '[N] 阅读'),
    ('阅读 **51**', '阅读 **[N]**'),
    ('阅读 17', '阅读 [N]'),
    ('来源 17', '来源 [N]'),
    ('17 阅读', '[N] 阅读'),
    ('34 阅读', '[N] 阅读'),
    ('阅读量 34', '阅读量 [N]'),
    ('阅读 = 1', '阅读 ≈0'),
    ('阅读=1', '阅读≈0'),
    ('阅读 ≤1', '阅读≈0'),
    ('阅读 1', '阅读 [N]'),

    # 百分比（源自周报的真实数据）→ 量级
    ('73.5%', '约七成'),
    ('29.4%', '约三成'),
    ('2.9%', '约百分之三'),

    # 账号健康 → 通用化
    ('「不良信息」标签', '账号健康标签（平台判定）'),
    ('不良信息标签', '账号健康标签'),
    ('2025-04 天文稿', '历史低质内容批次'),
    ('天文聚合稿', '历史低质内容批次'),

    # 周报文件引用 → 标注已删除
    ('（media/weekly-report-20260928.png）', '（截图含账号名，v2.3.1 后脱敏删除）'),
    ('media/weekly-report-20260928.png', '（截图已删除，见 media/README.md）'),

    # 周报数字段落
    ('内容阅读量 34，搜一搜来源 25（73.5%），朋友圈 10（29.4%），关注你的人 1',
     '内容阅读量 [N]，搜索来源占约七成，社交来源约三成，关注的人 = 1（单数，非新增）'),
    ('周报 34 阅读中 25 来自搜一搜（73.5%）', '周报显示搜索渠道贡献约七成阅读'),
    ('搜索带来 25 阅读', '搜索带来 [N] 阅读'),
    ('搜一搜来源 25（73.5%）', '搜一搜来源占约七成'),

    # 粉丝数
    ('关注你的人 1', '关注你的人（个位数，仅 1）'),
]

def desensitize_file(path, rules):
    """应用替换规则，返回 (changed, counts)"""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    counts = {}
    for old, new in rules:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            counts[old[:30]] = n
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return bool(counts), counts

# ---------- 目标文件 ----------
TARGETS = [
    'docs/发布台账.md',
    'docs/account-health-label.md',
    'HANDOFF-20260923.md',
    'HANDOFF-20260924.md',
    'HANDOFF-20260925.md',
    'HANDOFF-20260927.md',
    'WRITING-PROGRESS.md',
    'NEXT-STEPS-20260925.md',
    'NEXT-STEPS-20260925-backup.md',
    'NEXT-STEPS-20260927.md',
    'CHANGELOG.md',
    'DEPRECATED.md',
    'README.md',
    'docs/v2.5.x-completion-20260929.md',
    '选题库/v2.5.2自审复盘-正文.md',
    '选题库/v2.5.2自审复盘-标题方案.md',
    '选题库/README.md',
]

if __name__ == '__main__':
    total = 0
    for rel in TARGETS:
        p = os.path.join(BASE, rel)
        if not os.path.isfile(p):
            print(f'⏭  {rel} 不存在，跳过')
            continue
        changed, counts = desensitize_file(p, RULES)
        if changed:
            print(f'✅ {rel}: {len(counts)} 类替换, 共 {sum(counts.values())} 处')
            total += sum(counts.values())
        else:
            print(f'⚪ {rel}: 无命中')
    print(f'\n合计 {total} 处替换')
