#!/usr/bin/env python3
# G0 门禁脚本 —— 选题阶段判据脚本化（对齐不做清单通用判据 + TEAM.md §3.1 选题排期表）
# 判据来源：
#   1) 不做清单通用判据「证据基础是否公开」
#   2) 不做清单「样本知名度」教训（Skill 分发治理放弃案例）
#   3) TEAM.md §3.1 选题排期表 8 字段必填
#   4) TEAM.md §3.2 素材包 ≥8 条 / ≥3 A/B 级 / 反例 ≥1 条
# 用法：python3 gate-G0-check.py <素材包.md>
# 定位：G0 未过直接砍选题，不进 G1。与 G1 永不可省。
import sys, re

if len(sys.argv) < 2:
    print('用法：python3 gate-G0-check.py <素材包.md>')
    sys.exit(2)

t = open(sys.argv[1]).read()

res = {}
fails = []
warns = []

# ---------- 1. 选题信息 8 字段必填 ----------
# 从「选题信息」表里抓字段名，对齐 TEAM.md §3.1
required_fields = ['选题', '目标读者', '读者痛点', '预期收益', '素材可得性', '风险', '优先级', '状态']
# 抓 markdown 表里所有字段行 `| xxx | yyy |`
field_rows = re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', t, re.M)
found_fields = set()
for name, val in field_rows:
    name = name.strip()
    if name in required_fields and val.strip():
        found_fields.add(name)
res['选题信息字段命中'] = f'{len(found_fields)}/{len(required_fields)}'
res['缺失字段'] = [f for f in required_fields if f not in found_fields]
if len(found_fields) < len(required_fields):
    fails.append(f'G0-字段 选题信息缺 {len(required_fields)-len(found_fields)} 项：{",".join(res["缺失字段"])}')

# ---------- 2. 主论点明确 ----------
# 兼容多种写法：主论点 / 核心论点 / 结论 / 核心判断 / 一句话结论
has_main_claim = bool(re.search(r'##\s*(?:主论点|核心论点|结论|核心判断|一句话结论)|主论点[：:]', t))
res['有主论点章节'] = has_main_claim
if not has_main_claim:
    fails.append('G0-主论点 无「主论点/核心论点/结论」章节（选题无主论点=读者读完不知道要带走什么）')

# ---------- 3. 素材条数与置信度 ----------
# R-xx 编号识别
r_ids = re.findall(r'R-\d{2}', t)
unique_r = sorted(set(r_ids))
res['素材条数'] = len(unique_r)
if len(unique_r) < 8:
    fails.append(f'G0-素材 素材 {len(unique_r)} 条 <8 条（TEAM.md §3.2 门槛）')

# 置信度分级（A/B/C/D 或 高/中/低）
ab_level = len(re.findall(r'置信度[^\n]{0,10}(?:A|B)\s*级', t)) + len(re.findall(r'置信度[^\n]{0,10}[高中]级', t))
res['A/B 级素材数'] = ab_level
if ab_level < 3:
    fails.append(f'G0-置信 A/B 级素材 {ab_level} 条 <3 条')

# ---------- 4. 证据公开性（关键判据，不做清单通用判据）----------
# 判据：R-xx 素材块必须有"来源"字段（可以是 URL 或文字描述）
# 严格判：URL 是首选（TEAM.md §3.2 结构案），文字描述算降级（有出处但读者不能一键跳转）
r_blocks = re.split(r'(?=^###\s*R-\d{2})', t, flags=re.M)
pub_count = 0      # 有 URL 的来源
text_only_count = 0  # 只有文字描述无 URL
internal_count = 0
no_source_count = 0
for blk in r_blocks[1:]:
    if not blk.startswith('### R-'):
        continue
    has_source_field = bool(re.search(r'\*\*来源\*\*[：:]|^-?\s*来源[：:]', blk, re.M))
    has_url = bool(re.search(r'https?://', blk))
    has_internal = '内部' in blk and ('内部文件' in blk or '内部手册' in blk or '内部编号' in blk)
    if has_internal:
        internal_count += 1
    elif has_url:
        pub_count += 1
    elif has_source_field:
        text_only_count += 1
    else:
        no_source_count += 1

res['公开证据条数'] = pub_count
res['文字描述来源条数'] = text_only_count
res['内部证据条数'] = internal_count
res['无来源条数'] = no_source_count

# 硬门槛：内部证据必须 0 条（有内部证据=证据链泄露）
if internal_count > 0:
    fails.append(f'G0-公开性 {internal_count} 条素材含内部证据（读者无上下文读不下去，见不做清单通用判据）')
if no_source_count > 0:
    fails.append(f'G0-来源 {no_source_count} 条素材无来源字段（TEAM.md §3.2 必填）')
if text_only_count > 0:
    warns.append(f'G0-来源 {text_only_count} 条素材只有文字描述无 URL（建议补 URL 便于读者复核）')

# ---------- 5. 样本认知度（Skill 分发治理放弃案例的教训）----------
# 判据：至少要 1 条素材来自"账号读者听说过或正在用"的项目
# 关键词白名单（基于 09-21 不做清单 + 账号定位）
KNOWN_SAMPLE_HINTS = ['Claude Code', 'Cursor', 'Copilot', 'Vercel', 'VSCode', 'GitHub Copilot',
                      'ChatGPT', 'Gemini', 'Claude', 'Kimi', 'DeepSeek', 'Doubao', '通义',
                      '小红书', '抖音', 'B站', '知乎', '微博', '公众号', '微信',
                      'Fiverr', 'Upwork', 'X', 'Twitter', 'YouTube']
known_hits = [h for h in KNOWN_SAMPLE_HINTS if h in t]
res['样本认知度命中'] = known_hits
if len(known_hits) == 0:
    fails.append('G0-样本 无一条素材命中账号读者"听说过"的项目关键词（见不做清单 Skill 分发治理放弃案例）')

# ---------- 6. 反例存在性 ----------
# 判据：至少 1 处提到"反例"或"失败样本"或"反面"
has_counter = bool(re.search(r'反例|反面|失败样本|反证|反对意见', t))
res['有反例标注'] = has_counter
if not has_counter:
    warns.append('G0-反例 未找到反例/失败样本/反证 标注（TEAM.md §3.2 要求 ≥1 条反例）')

# ---------- 7. 落选理由（可选，多选题时必填）----------
# 如果文档里提到"备选"或"未选"，必须有"落选理由"
has_alt = bool(re.search(r'备选|未选|落选', t))
has_reject_reason = bool(re.search(r'落选理由|否决|放弃理由', t))
if has_alt and not has_reject_reason:
    warns.append('G0-落选 存在备选/未选但未写落选理由（TEAM.md §3.1 选题排期表字段）')

# ---------- 8. 差异化角度（v1→v2 场景）----------
# 如果有"v1"提及，必须有"差异化角度"或"论证结构切换"章节
mentions_v1 = bool(re.search(r'与 v1|v1 |v1→', t))
has_diff_angle = bool(re.search(r'差异化角度|角度切换|论证结构不同', t))
if mentions_v1 and not has_diff_angle:
    warns.append('G0-差异化 提及 v1 但未写差异化角度（防撞车判据 D）')

# ---------- 输出 ----------
print('=== G0 门禁实测（选题阶段）===')
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
    print('PASS：选题阶段 8 项判据全达标，可进 G1')
    sys.exit(0)
