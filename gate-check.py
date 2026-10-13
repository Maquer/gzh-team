#!/usr/bin/env python3
"""gate-check.py：门禁编排器（v4.0.0 瘦身版）。

用法：python3 gate-check.py <file> | --file <path> [--verbose] [--no-humanizer] [--policy-mode]
H1-H10 核心用 gzhkit.text 实现；G8/H14 调 gzhkit.gates 插件；汇总后按 0/1/7 退出。
exit code: 0=PASS, 1=WARN, 2=运行错误, 7=BLOCK
"""
import argparse
import sys

from gzhkit import cli
from gzhkit import config as C
from gzhkit import report
from gzhkit import text as T
from gzhkit.gates import get_gate
import gzhkit.gates.g8  # noqa: F401  （注册 g8）
import gzhkit.gates.h14  # noqa: F401  （注册 h14）


def _suggest(code, message):
    """按 finding 前缀给修复建议。"""
    if code == 'H8':
        return '正文 <200 字，疑似漏写。如为短稿/速评请主笔在「元信息」中写明类型，05 审核判合理性'
    if code == 'H9':
        return '将超 3 句段落拆为短句段落（每段 1-3 句，参见 TEAM.md §3.4）'
    if code == 'H-禁':
        return '改写或删除禁用词（首先/其次/此外/总而言之/不可否认/需要关注的是/接下来/需要注意的是/换句话说）'
    if code == 'H-元话语':
        return '删掉"这里多余/刚才说/删掉。/多余，删"等自我元话语'
    if code == '标题策略':
        return '补齐备选标题数量（5 个覆盖 5 类策略：悬念/数字/反常识/盘点/悬念+数字）'
    if code == 'H-注入':
        return '过 sanitize 净化（清洗模型尾部 system-reminder / </result> / <|im_end|> 等 8 种残留）'
    if code == 'H-占位符':
        return '把 XX/___/TBD/待补 统一改为 [待填写]（见 contracts.md H4）'
    if code == 'H-缺口声明':
        return '在文末追加 `## 信息缺口声明` 小节，逐条列出每个 [待填写] 的位置/状态/补资料计划'
    if code == 'H-元数据':
        return '正文不得含元数据段（平台：公众号 / 字数：约 / 调性：），移到元信息区'
    if code == '金句密度':
        return '每千字至少 1 处 **加粗** 金句，增加重点标记'
    if code == 'H-紧迫诱导':
        return '去掉强紧迫诱导词（速看/马上删/惊呆了/震惊/必看/全网首个/全网第一）'
    if code == 'H10':
        return '补齐缺失节（完整稿件要求：备选标题 / 正文 / 结尾 / AI 参与）'
    if code == 'G8':
        return '改写开头/结尾句式或换骨架（禁用起手式/收尾式，连续2篇勿同类骨架）'
    if code == 'H14':
        return 'AI 味超标需重写至 ≤%d 分；政策类稿件可加 --policy-mode 豁免 3 条规则' % C.HUMANIZER_LIMITS['放行']
    return ''


def run_core(path, text, ctx):
    """H1-H10 核心检查。返回 (GateOutcome, verbose_rows)。"""
    out = report.GateOutcome('gate')
    rows = []

    body = T.extract_body(text)
    zh = T.count_zh(body)
    tier = T.word_tier(zh)
    paras = T.split_paragraphs(body)
    over = T.overlong_paragraphs(body)

    # H8 字数：唯一 BLOCK 是 <200
    out.stat('正文字数', zh)
    out.stat('字数档位', '%s（参考区间）' % tier)
    rows.append(('H8 字数', zh, '参考区间（BLOCK 仅 <200）', zh >= C.WORD_MIN_BLOCK,
                 '以 %d 为参照点，余量 %+d' % (C.WORD_TIER_REF, zh - C.WORD_TIER_REF)))
    if zh < C.WORD_MIN_BLOCK:
        out.block('H8', '正文字数 %d<%d（疑似漏写）' % (zh, C.WORD_MIN_BLOCK))

    # H9 超 3 句段落
    out.stat('段落数', len(paras))
    out.stat('超3句段落数', len(over))
    rows.append(('H9 段落超3句', len(over), '=0', not over,
                 '%d 段需拆' % len(over) if over else '全达标'))
    if over:
        detail = '；'.join('第%d段%d句「%s…」' % o for o in over[:5])
        out.warn('H9', '%d 段超 3 句：%s' % (len(over), detail))

    # H-禁用词 / H-元话语
    hits = T.find_banned(body)
    meta = T.find_meta_words(body)
    out.stat('禁用词命中', hits or '无')
    out.stat('元话语命中', meta or '无')
    rows.append(('H-禁用词', len(hits), '=0', not hits,
                 '、'.join(hits) if hits else 'BANNED %d 词全扫' % len(C.BANNED_WORDS)))
    rows.append(('H-元话语', len(meta), '=0', not meta,
                 '、'.join(meta) if meta else '%d 词全扫' % len(C.META_WORDS)))
    if hits:
        out.warn('H-禁', '禁用词命中：%s' % '、'.join(hits))
    if meta:
        out.warn('H-元话语', '元话语命中：%s' % '、'.join(meta))

    # 标题策略数
    titles = T.find_titles(text)
    title_min = T.title_threshold(text)
    out.stat('标题策略数', '%d（阈值 ≥%d）' % (len(titles), title_min))
    rows.append(('标题策略数', len(titles), '≥%d' % title_min, len(titles) >= title_min,
                 '余量 %+d' % (len(titles) - title_min)))
    if len(titles) < title_min:
        out.warn('标题策略', '标题策略 %d<%d' % (len(titles), title_min))

    # AI 参与标注（信息项，不计入判定）
    ai_ok = T.has_ai_credit(text)
    out.stat('AI参与标注', '有' if ai_ok else '无')
    rows.append(('AI参与标注', '有' if ai_ok else '无', '有', ai_ok, '软检查'))

    # H-注入残留 → BLOCK
    inject = T.find_inject(text)
    out.stat('注入残留', len(inject))
    rows.append(('H-注入残留', len(inject), '=0', not inject, '8 种正则全扫'))
    if inject:
        out.block('H-注入', '注入残留 %d 处（须过 sanitize 净化）' % len(inject))

    # H-占位符：非标 → BLOCK；[待填写] 无缺口声明 → BLOCK
    ph, todo = T.find_placeholders(text)
    has_gap = C.GAP_SECTION_MARKER in text
    out.stat('非标占位符', ph or '无')
    out.stat('[待填写]数/缺口声明', '%d/%s' % (todo, '有' if has_gap else '无'))
    rows.append(('H-占位符 非标', len(ph), '=0', not ph,
                 '、'.join(ph) if ph else 'PLACEHOLDER_RE 全扫'))
    rows.append(('H-占位符 声明', '%d/%s' % (todo, '有' if has_gap else '无'),
                 '[待填写]须有缺口声明', not todo or has_gap, ''))
    if ph:
        out.block('H-占位符', '非标占位符 %d 处：%s（须用 [待填写]）'
                  % (len(ph), '、'.join(ph)))
    if todo and not has_gap:
        out.block('H-缺口声明', '%d 处 [待填写] 无文末 ## 信息缺口声明 小节' % todo)

    # H-元数据泄漏 → BLOCK
    meta_leak = T.find_meta_leak(text)
    out.stat('元数据泄漏', meta_leak or '无')
    if meta_leak:
        out.block('H-元数据', '元数据残留 %d 处：%s（正文不得含元数据段）'
                  % (len(meta_leak), '、'.join(sorted(set(meta_leak)))))
        rows.append(('H-元数据泄漏', len(meta_leak), '=0', False, '移到元信息区'))
    else:
        rows.append(('H-元数据泄漏', 0, '=0', True, 'META_LEAK_RE 全扫'))

    # 金句密度
    gold = T.count_gold(body)
    gold_need = T.gold_needed(zh)
    gold_ok = (zh == 0) or (gold >= gold_need)
    out.stat('金句密度', '%d 处加粗 / %d 字（阈值 ≥%d 处）' % (gold, zh, gold_need))
    rows.append(('金句密度', '%d处/%d字' % (gold, zh), '≥%d处' % gold_need, gold_ok,
                 '余量 %+d' % (gold - gold_need)))
    if not gold_ok:
        out.warn('金句密度', '金句密度 %d<%d 处（正文 %d 字，每千字 1 处）'
                 % (gold, gold_need, zh))

    # 紧迫诱导词
    urg = T.find_urgency(body)
    out.stat('紧迫诱导词命中', urg or '无')
    rows.append(('紧迫诱导词', len(urg), '=0', not urg,
                 '、'.join(urg) if urg else '%d 词全扫' % len(C.URGENCY_WORDS)))
    if urg:
        out.warn('H-紧迫诱导', '紧迫诱导词：%s' % '、'.join(urg))

    # H10 输出结构：仅完整稿件判定
    kind, missing = T.detect_sections(text)
    out.stat('H10 输出结构', '完整稿件' if kind == '完整稿件'
             else '正文片段（跳过）')
    h10_ok = (kind != '完整稿件') or (not missing)
    rows.append(('H10 输出结构', kind, '四节齐全', h10_ok,
                 '正文片段，跳过' if kind != '完整稿件'
                 else ('缺节：%s' % '、'.join(missing) if missing else '四节齐全')))
    if kind == '完整稿件' and missing:
        out.warn('H10', '输出结构缺节：%s' % '、'.join(missing))

    return out, rows


def merge_plugin(out, plugin_out):
    """把插件 outcome 的 findings/stats 并入主 outcome。"""
    prefix = plugin_out.gate_id.upper() + ' '
    for k, v in plugin_out.stats.items():
        key = k if k.startswith(prefix) else prefix + k
        out.stat(key, v)
    for f in plugin_out.findings:
        out.add(f.level, f.code, f.message, f.line)


def print_verbose(path, rows, out):
    print('\n=== 自检明细（--verbose）===')
    print('稿件：%s' % path)
    print('| 维度 | 得分 | 阈值 | 判定 | 备注 |')
    print('|------|------|------|------|------|')
    for d, s, th, ok, note in rows:
        print('| %s | %s | %s | %s | %s |' % (d, s, th, '✅' if ok else '❌', note))
    if out.blocks or out.warns:
        print()
        if out.blocks:
            print('**② BLOCK 修改建议（硬拦，必须修复）**')
        if out.warns:
            print('**② WARN 优化建议（只提醒，建议优化）**')
        for f in out.blocks + out.warns:
            tip = _suggest(f.code, f.message)
            print('- [%s] %s%s' % (f.code, f.message, ' → ' + tip if tip else ''))
    print()
    print('**③ 未跑的检查**（本脚本未覆盖，需人工或其他脚本）')
    print('- 未跑 link-check（外链可访问性、URL 有效性）')
    print('- 未跑 verify-all（H11/H12/H13 合规层）')
    print('- 未过 05 审核岗人工通读（AI 参与比例是否如实、数据是否可追溯）')
    print()
    n = len(rows)
    npass = sum(1 for r in rows if r[3])
    verdict = 'PASS' if not out.blocks and not out.warns else (
        'BLOCK' if out.blocks else 'WARN')
    print('**审核建议**：%s' % (
        '✅ 全项通过，可进 05 审核岗人工通读' if verdict == 'PASS'
        else ('❌ %d 项 BLOCK 硬拦，必须修复后复检' % len(out.blocks)
              if verdict == 'BLOCK'
              else '⚠️ %d 项 WARN 只提醒，建议优化后发布' % len(out.warns))))
    print('**自检覆盖**：%d/%d 项已跑，%d PASS / %d BLOCK / %d WARN'
          % (n, n, npass, len(out.blocks), len(out.warns)))
    print('=== 自检完成 · 判定：%s ===' % verdict)


def main():
    parser = cli.build_parser(
        'gate-check.py', 'G5 门禁编排器（H1-H10 核心 + G8/H14 插件）',
        epilog='exit code: 0=PASS, 1=WARN, 2=运行错误, 7=BLOCK')
    parser.add_argument('file_pos', nargs='?', metavar='FILE',
                        help='待检查的稿件路径（位置参数）')
    parser.add_argument('--file', dest='file_opt', metavar='PATH',
                        help='待检查的稿件路径（与位置参数等效）')
    cli.add_verbose(parser)
    parser.add_argument('--no-humanizer', action='store_true',
                        help='跳过 H14 AI 味外部脚本调用（离线/快速模式）')
    parser.add_argument('--policy-mode', action='store_true',
                        help='政策类稿件豁免模式：H14 透传 --policy-mode，豁免 3 条规则')
    args = parser.parse_args()

    path = cli.resolve_file_arg(args, parser)
    text = cli.read_text(path)
    body = T.extract_body(text)
    ctx = {'text': text, 'body': body, 'zh': T.count_zh(body),
           'path': path, 'verbose': args.verbose,
           'policy_mode': args.policy_mode, 'no_humanizer': args.no_humanizer}

    out, rows = run_core(path, text, ctx)

    # G8 结构多样性插件（WARN 级，不阻断）
    g8_out = get_gate('g8')(args, ctx)
    merge_plugin(out, g8_out)
    g8_warns = len([f for f in g8_out.warns])
    rows.append(('G8 结构多样性', '%d警告' % g8_warns, 'WARN级',
                 g8_warns == 0, '骨架/起手式/收尾式三项全 WARN'))

    # H14 AI 味插件（>25 → BLOCK；不可用不计入判定）
    h14_args = argparse.Namespace(mode='strict',
                                  no_humanizer=args.no_humanizer,
                                  policy_mode=args.policy_mode)
    h14_out = get_gate('h14')(h14_args, ctx)
    merge_plugin(out, h14_out)
    hum_score = h14_out.stats.get('H14 AI 味分数', 'N/A')
    h14_ok = not h14_out.blocks and (not isinstance(hum_score, int)
                                     or hum_score <= C.HUMANIZER_LIMITS['放行'])
    rows.append(('H14 AI味', hum_score, '≤%d' % C.HUMANIZER_LIMITS['放行'],
                 h14_ok, str(h14_out.stats.get('H14 说明', ''))))

    report.print_stats(out)
    report.print_verdict(out)

    if args.verbose:
        print_verbose(path, rows, out)

    return out.exit_code()


if __name__ == '__main__':
    cli.run_main(main)
