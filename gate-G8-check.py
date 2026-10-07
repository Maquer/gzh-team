#!/usr/bin/env python3
"""
gate-G8-check.py：发布前检查判据脚本化
用法：发布前调用 python3 gate-G8-check.py <发布前检查.md> [--html 排版稿.html]
关键约束：exit 0=PASS, 1=FAIL；G8 未过不予发布
"""
# G8 门禁脚本 —— 发布前检查判据脚本化
# 判据来源：
#   1) REVIEW.md §1-2 的 H1-H14 审核清单（合规 + AI 味 + 生图）
#   2) TEAM.md §3.6-3.7 排版/发布岗产出物标准
#   3) 09-21 AI 写作副业 v2 踩坑（gzh-api-push 不带 --thumb 直接 40007 invalid media_id）
#   4) 09-20 AI 写作稿排版 bug（标题重复 / 分割线残留 / ## 具体路径段丢失）
#   5) 09-21 Skill 生态 v2 经验（v1→v2 撞车判定）
# 用法：python3 gate-G8-check.py <发布前检查.md> [--html 排版稿.html]
# 定位：G8 未过不予发布，必须补齐 FAIL 项
import sys, re

if len(sys.argv) < 2:
    print('用法：python3 gate-G8-check.py <发布前检查.md> [--html 排版稿.html]')
    sys.exit(2)

check_file = sys.argv[1]
html_file = None
if '--html' in sys.argv:
    idx = sys.argv.index('--html')
    if idx + 1 < len(sys.argv):
        html_file = sys.argv[idx+1]

t = open(check_file).read()
html = open(html_file).read() if html_file else ''

res = {}
fails = []
warns = []

# ---------- 1. 摘要字段（≤120 字）----------
m = re.search(r'##\s*摘要[^#]*?\n+([^\n#]+(?:\n[^\n#]+)*)', t, re.S)
if m:
    abstract = m.group(1).strip().strip('—–-="「」')
    zh_count = len(re.findall(r'[\u4e00-\u9fff]', abstract))
    res['摘要字数'] = zh_count
    if zh_count > 120:
        fails.append(f'G8-摘要 {zh_count} 字 >120 字')
    elif zh_count < 30:
        warns.append(f'G8-摘要 {zh_count} 字偏短（建议 ≥30 字给读者上下文）')
else:
    res['摘要存在'] = False
    fails.append('G8-摘要 无「## 摘要」章节')

# ---------- 2. G7 清单存在 ----------
has_g7 = bool(re.search(r'G7\s*清单|##\s*G7', t))
res['G7 清单存在'] = has_g7
if not has_g7:
    fails.append('G8-G7 无 G7 清单章节（发布前检查必含）')

# ---------- 3. G7 清单条目数 ----------
g7_rows = re.findall(r'^\|\s*\d+\s*\|[^|]+\|[^|]+\|', t, re.M)
res['G7 条目数'] = len(g7_rows)
if has_g7 and len(g7_rows) < 8:
    warns.append(f'G8-G7 G7 清单仅 {len(g7_rows)} 条（建议 ≥8 条覆盖完整发布清单）')

# ---------- 4. G7 清单未打勾项 ----------
unchecked = re.findall(r'\|\s*(?:⚠️|❌|待做|未做|TBD)', t)
res['G7 未达标项'] = len(unchecked)
if unchecked:
    warns.append(f'G8-G7 {len(unchecked)} 项 G7 清单未达标（⚠️/待做/未做）')

# ---------- 5. pre-mortem 存在 ----------
has_premortem = bool(re.search(r'pre-mortem|pre_mortem|24h pre-mortem', t, re.I))
res['pre-mortem 存在'] = has_premortem
if not has_premortem:
    warns.append('G8-premortem 无 pre-mortem 章节（24h pre-mortem 是发布前硬门槛）')

# ---------- 6. v1→v2 撞车判定 ----------
mentions_v1 = bool(re.search(r'与 v1|v1→v2|v1 |vs v1', t))
has_diff = bool(re.search(r'撞车判定|论证结构不同|差异化角度|角度切换', t))
res['提及 v1'] = mentions_v1
res['有撞车判定'] = has_diff
if mentions_v1 and not has_diff:
    fails.append('G8-撞车 提及 v1 但无撞车判定章节（H1-H7 契约 v1→v2 硬条款）')

# ---------- 7. 封面 media_id 声明（09-21 踩坑修复）----------
has_media_id = bool(re.search(r'media_id|media id|MediaID|QQm0YJ', t))
res['封面 media_id 声明'] = has_media_id
if not has_media_id:
    warns.append('G8-封面 未见 media_id 声明（gzh-api-push 需 --thumb media_id，缺失会 40007 invalid media_id）')

# ---------- 8. AI 参与声明 ----------
has_ai_disclose = bool(re.search(r'AI\s*参与|AI\s*生成|AI\s*辅助|人工智能', t))
res['AI 参与声明'] = has_ai_disclose
if not has_ai_disclose:
    warns.append('G8-AI 无 AI 参与声明（《人工智能生成合成内容标识办法》2025-09-01 施行）')

# ---------- 9. 数据置信度标注 ----------
has_confidence = bool(re.search(r'置信度|数据缺口|来源[：:]\s*https?://', t))
res['数据置信度标注'] = has_confidence
if not has_confidence:
    warns.append('G8-置信 无置信度/来源/数据缺口 标注（数字必须有出处）')

# ---------- 10. 排版稿大小 ----------
if html_file and html:
    html_size = len(html.encode('utf-8'))
    res['排版稿字节'] = html_size
    if html_size < 8000:
        warns.append(f'G8-排版稿 {html_size}B <8KB（可能缺章节）')
    elif html_size > 25000:
        warns.append(f'G8-排版稿 {html_size}B >25KB（可能超微信编辑器推荐）')

# ---------- 11. 排版稿结构检查 ----------
if html:
    h1_count = html.count('<h1')
    # gzh-typeset.py 用内联 font-weight:700 做加粗，不用 <strong> 标签
    # 兼容三种方式：<strong> / <b> / font-weight:700 或 800
    strong_count = (html.count('<strong') + html.count('<b>')
                    + len(re.findall(r'font-weight:\s*(?:700|800|900|bold)', html)))
    table_count = html.count('<table')
    res['h1 数'] = h1_count
    res['strong 数'] = strong_count
    res['table 数'] = table_count
    if h1_count != 1:
        fails.append(f'G8-排版稿 h1={h1_count}（必须恰好 1 个，标题重复会被判为正文）')
    if strong_count < 2:
        warns.append(f'G8-排版稿 strong={strong_count} <2（金句加粗不足）')

# ---------- 12. 排版稿禁用词 + sepia 专业文档层 AI 检测 ----------
if html:
    # 原有 BANNED 9 词（gate-check 对齐）
    BANNED_BASE = ['首先', '其次', '此外', '总而言之', '不可否认',
                   '需要关注的是', '接下来', '需要注意的是', '换句话说']
    # 10-04 P1 借鉴 sepia professional-pass / tech-articles 域：
    # 补充 14 条"AI 说教模板"模式（正则，匹配完整短语而非单词）
    # 设计原则（sepia "calibrate to human distribution"）：
    #   - 只匹配"套话短语"，不匹配正常用语（"接下来我会..."是人的话）
    #   - 每条模式必须包含上下文语境，减少误报
    SEPIA_PATTERNS = [
        # 序数说教全链（"首先...其次...再次...最后" 全出现才算）
        (r'(?:首先.{0,50}其次.{0,50}再次)|(?:其次.{0,50}最后.{0,20}(?:总结|综上))', 'G8-sepia 序数说教全链'),
        # 套话总结
        (r'(?:综上(?:所述)?|总而言之|可以(?:认为|说).{0,10}结论)', 'G8-sepia 套话总结'),
        # 套话强调（"需要关注的是" 完整短语，不带"是"的不算）
        (r'需要关注的是|值得注意的是|值得警惕的是', 'G8-sepia 强调性套话'),
        # 预设共识（"众所周知" 系列）
        (r'(?:众所周知|不言而喻|众所周知的是|不难发现)', 'G8-sepia 预设共识套话'),
        # 号召式套话
        (r'(?:让我们(?:一起)?|不妨(?:一起)?|希望大家)', 'G8-sepia 号召式套话'),
        # 背景铺陈（"在当今时代" / "随着...不断发展" 完整语境）
        (r'(?:在当今|在当下|在这个).{0,8}(?:时代|社会|背景下)', 'G8-sepia 背景铺陈套话'),
        (r'随着.{0,15}(?:的(?:不断(?:发展|增长|普及|进步)|快速(?:发展|增长))|不断(?:发展|增长|进步|普及))', 'G8-sepia 发展铺陈套话'),
        # 转折后套话（"然而/但是...事实上/实际上" 紧接）
        (r'(?:然而|但是|与此同时).{0,15}(?:事实上|实际上|从(?:根本上|本质上))', 'G8-sepia 转折后套话'),
        # 对称结构（"不仅...而且" 完整句）
        (r'不仅.{0,30}而且.{0,30}', 'G8-sepia 对称结构套话'),
        # 维度套话（"从X层面" 完整短语，X 须是常见抽象名词）
        (r'(?:从|在)(?:宏观|微观|技术|业务|理论|实践|制度|政策|市场|战略)层面.{0,10}', 'G8-sepia 维度套话'),
        # 结尾套话（"最后，让我们..." / "最终，不妨..."）
        (r'(?:最后|最终|归根结底).{0,10}(?:让我们|我们一起|不妨|需要)', 'G8-sepia 结尾套话'),
        # 数字无来源（"数据表明" / "研究表明" 无具体出处 = 可疑）
        (r'(?:数据|研究|调查|实验)(?:表明|显示|证明).{0,20}(?:显著|巨大|重要)', 'G8-sepia 数字无来源'),
    ]

    html_text = re.sub(r'<[^>]+>', '', html)
    # 原有单词 BANNED（WARN 级，不 BLOCK）
    base_hits = [w for w in BANNED_BASE if w in html_text]
    # sepia 正则模式
    sepia_hits = []
    for pat, label in SEPIA_PATTERNS:
        matches = list(re.finditer(pat, html_text, re.I))
        if matches:
            ctx = matches[0].group(0)[:40]
            sepia_hits.append(f'{label} → "{ctx}"')

    res['BANNED词命中'] = base_hits
    res['sepia模式命中'] = sepia_hits
    if base_hits:
        warns.append(f'G8-BANNED {len(base_hits)} 个禁用词: {"、".join(base_hits)}')
    if sepia_hits:
        warns.append(f'G8-sepia {len(sepia_hits)} 处 AI 说教模板（降 AI 味参考）')

# ---------- 13. 排版稿 markdown 残留 ----------
if html:
    # 先剥离 HTML 标签，只检查纯文本中是否有未转换的 markdown 加粗
    html_text = re.sub(r'<[^>]+>', '', html)
    orphan_bold = re.findall(r'\*\*[^*]{1,20}(?!\*\*)', html_text)
    orphan_hr = '<p>---</p>' in html or '<hr/>' in html.lower()
    res['markdown 残留'] = {
        '未闭合加粗': len(orphan_bold),
        '孤立分割线': orphan_hr,
    }
    if orphan_bold:
        warns.append(f'G8-markdown {len(orphan_bold)} 处未闭合 ** 加粗（视觉断裂）')
    if orphan_hr:
        warns.append('G8-markdown 存在孤立 <p>---</p>（分割线残留）')

# ---------- 输出 ----------
print('=== G8 门禁实测（发布前）===')
for k, v in res.items():
    print(f'{k}: {v}')

print('\n=== 门禁判定 ===')
if fails:
    print(f'FAIL ({len(fails)} 项)：')
    for f in fails:
        print(f'  - {f}')
    if warns:
        print(f'WARN ({len(warns)} 项)：')
        for w in warns:
            print(f'  - {w}')
    sys.exit(1)
elif warns:
    print(f'PASS_WITH_WARN（{len(warns)} 项建议改进）：')
    for w in warns:
        print(f'  - {w}')
    sys.exit(0)
else:
    print('PASS：发布前 13 项判据全达标，可推草稿箱')
    sys.exit(0)
