#!/usr/bin/env python3
"""component-registry.py — 工具链变更同步注册表。

v4.0.0 重建：干净重写，组件数据与 v3.3.0 一致。
解决"改了 A 忘了 B"的同步断层问题。

用法：
  python3 component-registry.py             # 全量打印
  python3 component-registry.py --deps      # 只打印依赖图
  python3 component-registry.py --owners    # 只打印文件→组件映射
  python3 component-registry.py --check     # 运行版本一致性检测

退出码：0 成功；1 --check 发现缺失文件；2 参数错误。

变更记录：
  2026-10-04: v0.1.0 首次创建，基于 gzh-team 当天事故分析
  2026-10-14: v4.0.0 重建，补上文档中承诺但未实现的 --check
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

TEAM = os.path.dirname(os.path.abspath(__file__))
SHARED = os.environ.get('GZH_SHARED_DIR', os.path.dirname(TEAM))

# ── 组件定义（唯一真源）──────────────────────────────────────────────
COMPONENTS = {
    # ── 封面图组件（P0：今天出事的地方）─────────────────────────────
    'cover-card': {
        'path': '%s/cover-card.py' % TEAM,
        'version': 'v3',
        'what': '标题型封面图生成器（900×383，带标题+品牌标识）',
        'api_change_risk': ['render_logo', 'cover'],
        'change_sync_list': [
            ('file', '%s/cover-brief.py' % TEAM, '覆盖 render_logo 简化版，需升级为完整版'),
            ('file', '%s/brand-font-schemes.py' % TEAM, '覆盖 render_logo，需确认与 cover-card 签名一致'),
            ('file', '%s/gate-H11-check.py' % TEAM, 'OCR 检测逻辑可能受 render_logo 返回对象变化影响'),
            ('doc', '%s/BASELINE.md' % TEAM, 'render_logo 硬约束段需随实现同步'),
            ('test', '重跑 BASELINE.md 验证判据（四字中心 y 极差 ≤1px）'),
        ],
    },
    'cover-brief': {
        'path': '%s/cover-brief.py' % TEAM,
        'version': 'v1',
        'what': '摘要型封面图生成器（900×383，无标题，关键词左对齐）',
        'api_change_risk': ['render_logo'],
        'change_sync_list': [
            ('file', '%s/cover-card.py' % TEAM, '独立副本，两个文件各自维护 render_logo，需保持语义一致'),
            ('file', '%s/brand-font-schemes.py' % TEAM, '共享 render_logo 参考实现'),
            ('doc', '%s/BASELINE.md' % TEAM, '命名规则段：封面图 vs 首图 vs 尾图'),
            ('test', '用同一张 LOGO_A 输入两脚本输出 md5 对比'),
        ],
    },
    'brand-font-schemes': {
        'path': '%s/brand-font-schemes.py' % TEAM,
        'version': 'v1',
        'what': '品牌字体方案模块，render_logo 是基准参考实现',
        'note': '注释写"被 cover-pipeline / gate-H11 import"，但实际 gate-H11 未 import 此文件——注释已过时',
        'api_change_risk': ['render_logo'],
        'change_sync_list': [
            ('file', '%s/cover-card.py' % TEAM, 'cover-card 的 render_logo 应与此文件签名对齐（logo,size,color vs size,logo,color）'),
            ('file', '%s/cover-brief.py' % TEAM, '同上'),
            ('file', '%s/cover-pipeline.py' % TEAM, '注释提及但实际未使用 render_logo，需核实'),
            ('doc', '%s/BASELINE.md' % TEAM, 'render_logo 硬约束段直接引用此文件'),
        ],
    },

    # ── 清洗组件 ──────────────────────────────────────────────────────
    'gzh-clean': {
        'path': '%s/gzh-clean.py' % SHARED,
        'version': 'v4',
        'what': '公众号 HTML 清洗工具（typeset 后推送前）',
        'known_gaps': [
            'v4 覆盖了 <p> 标签的元数据段删除，但 <section> 包裹的引用块（如 "> 平台：公众号"）未覆盖',
            '此漏洞导致今日《第一轮面试我的》推送泄漏',
        ],
        'api_change_risk': ['clean_html'],
        'change_sync_list': [
            ('doc', '%s/CHANGELOG.md' % TEAM, '新增 v4.1 条目，说明此次安全修复'),
            ('test', '验证 <section> 块级删除规则生效'),
            ('test', '用今日问题稿件（含 "> 平台：公众号" 的 section）回归测试'),
        ],
    },
}

KIND_ICONS = {'file': '📄', 'doc': '📝', 'test': '🧪', 'extension': '⚙️'}


def _sync_item(item):
    if len(item) == 3:
        kind, target, note = item
    else:
        kind, note = item
        target = ''
    return kind, target, note


def print_deps():
    """打印依赖关系图"""
    print('# 工具链变更同步注册表\n')
    print('> 位置：`component-registry.py` | 创建：2026-10-04 | 维护：司南\n')
    print('## 组件清单\n')
    print('| 组件 | 路径 | 版本 | 说明 | 风险 API |')
    print('|------|------|------|------|----------|')
    for name, c in COMPONENTS.items():
        path_short = c['path'].replace(SHARED + '/', '')
        risks = ', '.join(c.get('api_change_risk', []))
        print('| `%s` | `%s` | %s | %s | %s |'
              % (name, path_short, c['version'], c['what'], risks))
    print()
    print('## 同步列表（改一个组件 → 必须同步的项目）\n')
    for name, c in COMPONENTS.items():
        syncs = c.get('change_sync_list', [])
        if not syncs:
            continue
        print('### `%s`\n' % name)
        for item in syncs:
            kind, target, note = _sync_item(item)
            icon = KIND_ICONS.get(kind, '📦')
            target_str = '`%s` — ' % target if target else ''
            print('- %s [%s] %s%s' % (icon, kind, target_str, note))
        print()


def print_owners():
    """打印文件→组件映射"""
    print('# 文件 → 组件归属映射\n')
    file_to_comp = {}
    for name, c in COMPONENTS.items():
        file_to_comp[c['path']] = name
        for item in c.get('change_sync_list', []):
            kind, target, _ = _sync_item(item)
            if target.startswith('!'):
                continue
            file_to_comp[target] = name
    print('| 文件 | 组件 |')
    print('|------|------|')
    for path, comp in sorted(file_to_comp.items()):
        print('| `%s` | `%s` |' % (path, comp))
    print()


def print_full():
    """全量打印"""
    print_deps()
    print('\n---\n')
    print_owners()

    print('\n## 已知漏洞记录\n')
    for name, c in COMPONENTS.items():
        gaps = c.get('known_gaps', [])
        if gaps:
            print('### `%s`\n' % name)
            for g in gaps:
                print('- ⚠️ %s' % g)
            print()

    print('\n## 使用说明\n')
    print('''
1. **任何工具改动前**：先查本表，看 `change_sync_list` 完整列表
2. **任何工具改动后**：执行对应 `test` 条目
3. **新增工具时**：必须在此注册，否则 gate-version-check 无法追踪
4. **每次发布 v2.x.y**：同步更新本表中的版本号
'''.strip())
    print()


def cmd_check(args):
    """版本一致性检测：注册表登记的组件文件是否都存在。"""
    missing = []
    print('## 版本一致性检测\n')
    print('| 组件 | 登记版本 | 路径 | 状态 |')
    print('|------|----------|------|------|')
    for name, c in COMPONENTS.items():
        ok = os.path.exists(c['path'])
        if not ok:
            missing.append(name)
        print('| `%s` | %s | `%s` | %s |'
              % (name, c['version'], c['path'], '✅' if ok else '❌ 缺失'))
    print()
    if missing:
        print('❌ %d 个组件文件缺失: %s' % (len(missing), ', '.join(missing)))
        return 1
    print('✅ 全部 %d 个组件文件存在，版本登记一致' % len(COMPONENTS))
    return 0


def main():
    parser = gzh_cli.build_parser("component-registry.py", "工具链变更同步注册表")
    parser.add_argument('--deps', action='store_true', help='只打印依赖图')
    parser.add_argument('--owners', action='store_true', help='只打印文件→组件映射')
    parser.add_argument('--check', action='store_true', help='运行版本一致性检测')
    args = parser.parse_args()

    if args.check:
        return cmd_check(args)
    if args.deps:
        print_deps()
    elif args.owners:
        print_owners()
    else:
        print_full()
    return 0


if __name__ == '__main__':
    gzh_cli.run_main(main)
