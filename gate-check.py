#!/usr/bin/env python3
"""gate-check.py：门禁编排器（v4.0.0 瘦身版）。

用法：python3 gate-check.py <file> | --file <path> [--verbose] [--no-humanizer] [--policy-mode]
H1-H10 核心用 gzhkit.text 实现；G8/H14 调 gzhkit.gates 插件；汇总后按 0/1/7 退出。
exit code: 0=PASS, 1=WARN, 2=运行错误, 7=BLOCK
"""
import argparse
import re
import sys

from gzhkit import cli
from gzhkit import config as C
from gzhkit import report
from gzhkit import text as T
from gzhkit.gates import get_gate
import gzhkit.gates.g0  # noqa: F401  （注册 g0）
import gzhkit.gates.g3  # noqa: F401  （注册 g3）
import gzhkit.gates.g7  # noqa: F401  （注册 g7）
import gzhkit.gates.g8  # noqa: F401  （注册 g8）
import gzhkit.gates.h9  # noqa: F401  （注册 h9）
import gzhkit.gates.h11  # noqa: F401  （注册 h11）
import gzhkit.gates.h12  # noqa: F401  （注册 h12）
import gzhkit.gates.h14  # noqa: F401  （注册 h14）
import gzhkit.gates.h15  # noqa: F401  （注册 h15）
import os as _os


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

    # 调性取值域（2026-10-18 词表统一；非法=WARN 给替换建议，缺失=软检查不计判定）
    tone_val = T.find_tone(text)
    tone_state, tone_hint = T.check_tone(tone_val)
    out.stat('调性', tone_val or '未标注')
    if tone_state == 'bad':
        out.warn('H-调性', '调性「%s」不在 5 档词表 — %s' % (tone_val, tone_hint))
    rows.append(('调性取值域', tone_val or '未标注', '5 档枚举',
                 tone_state != 'bad',
                 tone_hint if tone_state == 'bad'
                 else '缺失=软检查不计判定；词表=docs/rules/tone-structure-map.md'))

    # 金句密度
    gold = T.count_gold(body)
    gold_need = T.gold_needed(zh)
    gold_ok = (zh == 0) or (gold >= gold_need)
    out.stat('金句密度', '%d 处加粗 / %d 字（阈值 ≥%d 处）' % (gold, zh, gold_need))
    rows.append(('金句密度', '%d处/%d字' % (gold, zh), '≥%d处' % gold_need, gold_ok,
                 '余量 %+d' % (gold - gold_need)))
    if not gold_ok:
        out.block('金句密度', '金句密度 %d<%d 处（正文 %d 字，每千字 1 处）— G7 发布前清单 BLOCK 项'
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

    # ===== 存在性检查（2026-10-15 新增，交叉检查 P1-12）=====
    # 5 项主笔必做产出物存在性，WARN 级不阻断

    # EX1 备选标题数量 ≥5（标题策略数只查策略覆盖，不查数量）
    title_count = len(T.find_titles(text))
    out.stat('备选标题数', '%d（阈值 ≥5）' % title_count)
    rows.append(('EX1 备选标题数', title_count, '≥5', title_count >= 5,
                 '余量 %+d' % (title_count - 5)))
    if title_count < 5:
        out.block('EX1', '备选标题 %d<5（角色卡要求 5 个覆盖 5 种策略）— G7 发布前清单 BLOCK 项' % title_count)

    # EX2 配图指导存在性
    has_photo_guide = bool(re.search(r'配图指导|配图|图片位置|图片作用', text))
    out.stat('配图指导', '有' if has_photo_guide else '无')
    rows.append(('EX2 配图指导', '有' if has_photo_guide else '无', '有', has_photo_guide,
                 '角色卡必做第 6 步'))
    if not has_photo_guide:
        out.block('EX2', '缺配图指导（每张图需：位置+作用+期望效果+替代文字）— 角色卡必填')

    # EX3 互动钩子存在性
    has_hook = bool(re.search(r'互动|投票|提问|评论区|聊聊|你怎么看|你呢|留言', body[-500:]))
    out.stat('互动钩子', '有' if has_hook else '无')
    rows.append(('EX3 互动钩子', '有' if has_hook else '无', '有', has_hook,
                 '正文末尾 500 字内检测'))
    if not has_hook:
        out.block('EX3', '缺结尾互动钩子（开放提问/投票/填空/争议/晒一晒）— G7 发布前清单 BLOCK 项')

    # EX4 自检清单/元信息存在性
    has_selfcheck = bool(re.search(r'自检|元信息|字数类型|合理性|AI参与|AI 味', text))
    out.stat('自检清单', '有' if has_selfcheck else '无')
    rows.append(('EX4 自检清单', '有' if has_selfcheck else '无', '有', has_selfcheck,
                 '角色卡产出物标准'))
    if not has_selfcheck:
        out.block('EX4', '缺自检清单/元信息（字数类型+合理性+标题策略+AI味评分）— 角色卡必填')

    # EX5 AI参与标注（升级为 BLOCK）
    if not ai_ok:
        out.block('EX5', '缺AI参与标注（工具名+用途+生成占比，角色卡必填）')

    # EX6 标题字数（15-30字，G7 要求）
    title_match = re.search(r'^#\s+(.+)$', text, re.M)
    if title_match:
        title_text = title_match.group(1).strip()
        zh_count = len(re.findall(r'[\u4e00-\u9fff]', title_text))
        title_len_ok = C.G7_TITLE_ZH_MIN <= zh_count <= C.G7_TITLE_ZH_MAX
        out.stat('标题字数', '%d 字（要求 %d-%d）' % (zh_count, C.G7_TITLE_ZH_MIN, C.G7_TITLE_ZH_MAX))
        rows.append(('EX6 标题字数', '%d字' % zh_count, '%d-%d字' % (C.G7_TITLE_ZH_MIN, C.G7_TITLE_ZH_MAX),
                     title_len_ok, 'G7 发布前清单要求'))
        if not title_len_ok:
            out.block('EX6', '标题 %d 字，要求 %d-%d 字（G7 发布前清单 BLOCK 项）'
                      % (zh_count, C.G7_TITLE_ZH_MIN, C.G7_TITLE_ZH_MAX))
    else:
        out.stat('标题字数', '无标题行')
        rows.append(('EX6 标题字数', '无', '15-30字', False, '无标题行'))
        out.block('EX6', '无标题行（# 标题缺失）')

    # EX7 防盗链：正文图片 src 是否含 referrerpolicy（G7 要求）
    has_img_tag = bool(re.search(r'<img[^>]*src\s*=', text, re.I))
    has_rp = bool(re.search(r'referrerpolicy|referrer', text, re.I))
    out.stat('防盗链注入', '有<img>' if has_img_tag else '无<img>，跳过')
    if has_img_tag and not has_rp:
        out.block('EX7', 'HTML 中有 <img> 但无 referrerpolicy（防盗链未注入，G7 BLOCK 项）')
    elif has_img_tag and has_rp:
        out.stat('防盗链注入', '已注入 referrerpolicy ✅')
    rows.append(('EX7 防盗链', '已注入' if has_rp else ('无<img>' if not has_img_tag else '未注入'),
                 '需有', has_img_tag and has_rp or not has_img_tag,
                 'G7 发布前清单要求'))

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

    # 图片文件：跳过文本检查，直接走图片门禁
    is_image = str(path).lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    if is_image and _os.path.isfile(str(path)):
        text = ''
        body = ''
    else:
        text = cli.read_text(path)
        body = T.extract_body(text)
    ctx = {'text': text, 'body': body, 'zh': T.count_zh(body) if body else 0,
           'path': path, 'verbose': args.verbose,
           'policy_mode': args.policy_mode, 'no_humanizer': args.no_humanizer}

    if is_image:
        # 图片文件：跳过 H1-H10 文本检查，直接走图片门禁
        out = report.GateOutcome('gate')
        rows = []
    else:
        out, rows = run_core(path, text, ctx)

    # G8 结构多样性插件（WARN 级，不阻断）
    g8_out = get_gate('g8')(args, ctx)
    merge_plugin(out, g8_out)
    g8_warns = len([f for f in g8_out.warns])
    rows.append(('G8 结构多样性', '%d警告' % g8_warns, 'WARN级',
                 g8_warns == 0, '骨架/起手式/收尾式三项全 WARN'))

    # H14 AI 味插件（solo 模式，只给参考分数不卡关）
    h14_args = argparse.Namespace(mode='solo',
                                  no_humanizer=args.no_humanizer,
                                  policy_mode=args.policy_mode)
    h14_out = get_gate('h14')(h14_args, ctx)
    merge_plugin(out, h14_out)
    hum_score = h14_out.stats.get('H14 AI 味分数', 'N/A')
    h14_ok = not h14_out.blocks and (not isinstance(hum_score, int)
                                     or hum_score <= C.HUMANIZER_LIMITS['放行'])
    rows.append(('H14 AI味', hum_score, '≤%d' % C.HUMANIZER_LIMITS['放行'],
                 h14_ok, str(h14_out.stats.get('H14 说明', ''))))

    # ===== 图片门禁（文件是图片时触发）=====
    is_image = str(path).lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    if is_image and _os.path.isfile(str(path)):
        # H11 图片 OCR 门禁
        h11_args = argparse.Namespace(image=str(path))
        h11_out = get_gate('h11')(h11_args, ctx)
        merge_plugin(out, h11_out)
        h11_blocks = len(h11_out.blocks)
        rows.append(('H11 图片OCR', '%d阻断' % h11_blocks, '无中文残留',
                     h11_blocks == 0, '水印/中文残留检测'))

        # H12 prompt 元数据门禁
        h12_args = argparse.Namespace(image=str(path))
        h12_out = get_gate('h12')(h12_args, ctx)
        merge_plugin(out, h12_out)
        h12_blocks = len(h12_out.blocks)
        rows.append(('H12 prompt残留', '%d阻断' % h12_blocks, '无prompt',
                     h12_blocks == 0, 'prompt参数/主体描述检测'))

        # H15 尾图合规门禁
        h15_args = argparse.Namespace(image=str(path), content='')
        h15_out = get_gate('h15')(h15_args, ctx)
        merge_plugin(out, h15_out)
        h15_blocks = len(h15_out.blocks)
        rows.append(('H15 尾图合规', '%d阻断' % h15_blocks, '尺寸/违规词',
                     h15_blocks == 0, '尺寸/OCR内容/导流词'))
    elif is_image:
        rows.append(('H11/H12/H15', '跳过', '图片门禁', True, '文件不存在'))

    # ===== 结构案门禁（正文含结构案时触发）=====
    if '结构案' in text or '## 结构' in text or '# 结构' in text:
        g3_args = argparse.Namespace(structure=text)
        try:
            g3_out = get_gate('g3')(g3_args, ctx)
            merge_plugin(out, g3_out)
            g3_blocks = len(g3_out.blocks)
            rows.append(('G3 结构案', '%d阻断' % g3_blocks, '节数/字数/金句',
                         g3_blocks == 0, '5类模板判据'))
        except Exception as e:
            rows.append(('G3 结构案', '跳过', '-', True, str(e)[:60]))

    # ===== 选题门禁（正文含选题卡时触发）=====
    if '选题' in text and ('选题卡' in text or '# 选题' in text):
        try:
            g0_args = argparse.Namespace(topic=text)
            g0_out = get_gate('g0')(g0_args, ctx)
            merge_plugin(out, g0_out)
            g0_blocks = len(g0_out.blocks)
            rows.append(('G0 选题', '%d阻断' % g0_blocks, '证据基础',
                         g0_blocks == 0, '选题排期/素材包判据'))
        except Exception as e:
            rows.append(('G0 选题', '跳过', '-', True, str(e)[:60]))

    report.print_stats(out)
    report.print_verdict(out)

    if args.verbose:
        print_verbose(path, rows, out)

    return out.exit_code()


if __name__ == '__main__':
    cli.run_main(main)
