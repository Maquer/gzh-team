#!/usr/bin/env python3
"""gzhkit.gates.g0: G0 选题门禁（选题阶段判据脚本化）。

判据来源：不做清单通用判据「证据基础是否公开」+ TEAM.md §3.1 选题排期表
+ §3.2 素材包 ≥8 条 / ≥3 A/B 级 / 反例 ≥1 条。
G0 未过直接砍选题，不进 G1。
"""
import re

from . import register
from .. import config as C
from ..report import GateOutcome


def add_arguments(parser):
    parser.add_argument('file_pos', nargs='?', metavar='FILE',
                        help='选题素材包 Markdown 路径')


def check(args, ctx):
    """执行 G0 选题门禁检查。ctx: text/path/verbose。"""
    out = GateOutcome('g0')
    t = ctx.get('text', '')
    fails, warns = [], []

    # 1. 选题信息 8 字段必填
    field_rows = re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', t, re.M)
    found = {n.strip() for n, v in field_rows
             if n.strip() in C.G0_REQUIRED_FIELDS and v.strip()}
    missing = [f for f in C.G0_REQUIRED_FIELDS if f not in found]
    out.stat('选题信息字段命中', '%d/%d' % (len(found), len(C.G0_REQUIRED_FIELDS)))
    if missing:
        fails.append('G0-字段 选题信息缺 %d 项：%s' % (len(missing), '，'.join(missing)))

    # 2. 主论点明确
    has_claim = bool(re.search(C.G0_MAIN_CLAIM_RE, t))
    out.stat('有主论点章节', has_claim)
    if not has_claim:
        fails.append('G0-主论点 无主论点/核心论点/结论章节（选题无主论点=读者读完不知道带走什么）')

    # 3. 素材条数与置信度
    unique_r = sorted(set(re.findall(r'R-\d{2}', t)))
    out.stat('素材条数', len(unique_r))
    if len(unique_r) < C.G0_MATERIAL_MIN:
        fails.append('G0-素材 素材 %d 条 <%d 条（TEAM.md §3.2 门槛）'
                     % (len(unique_r), C.G0_MATERIAL_MIN))
    ab_level = (len(re.findall(r'置信度[^\n]{0,10}(?:A|B)\s*级', t))
                + len(re.findall(r'置信度[^\n]{0,10}[高中]级', t)))
    out.stat('A/B 级素材数', ab_level)
    if ab_level < C.G0_AB_MIN:
        fails.append('G0-置信 A/B 级素材 %d 条 <%d 条' % (ab_level, C.G0_AB_MIN))

    # 4. 证据公开性
    r_blocks = re.split(r'(?=^###\s*R-\d{2})', t, flags=re.M)
    pub = text_only = internal = no_source = 0
    for blk in r_blocks[1:]:
        if not blk.startswith('### R-'):
            continue
        has_source = bool(re.search(C.G0_SOURCE_FIELD_RE, blk, re.M))
        has_url = bool(re.search(r'https?://', blk))
        has_internal = ('内部' in blk
                        and any(h in blk for h in C.G0_INTERNAL_HINTS))
        if has_internal:
            internal += 1
        elif has_url:
            pub += 1
        elif has_source:
            text_only += 1
        else:
            no_source += 1
    out.stat('公开证据条数', pub)
    out.stat('文字描述来源条数', text_only)
    out.stat('内部证据条数', internal)
    out.stat('无来源条数', no_source)
    if internal > 0:
        fails.append('G0-公开性 %d 条素材含内部证据（证据链泄露，见不做清单通用判据）' % internal)
    if no_source > 0:
        fails.append('G0-来源 %d 条素材无来源字段（TEAM.md §3.2 必填）' % no_source)
    if text_only > 0:
        warns.append('G0-来源 %d 条素材只有文字描述无 URL（建议补 URL 便于读者复核）' % text_only)

    # 5. 样本认知度
    known_hits = [h for h in C.KNOWN_SAMPLE_HINTS if h in t]
    out.stat('样本认知度命中', known_hits or '无')
    if not known_hits:
        fails.append('G0-样本 无一条素材命中读者"听说过"的项目关键词（见不做清单放弃案例）')

    # 6. 反例存在性（WARN 级）
    has_counter = bool(re.search(C.G0_COUNTER_RE, t))
    out.stat('有反例标注', has_counter)
    if not has_counter:
        warns.append('G0-反例 未找到反例/失败样本标注（TEAM.md §3.2 要求 ≥1 条反例）')

    # 7. 落选理由（可选）
    if re.search(C.G0_ALT_RE, t) and not re.search(C.G0_REJECT_RE, t):
        warns.append('G0-落选 存在备选/未选但未写落选理由（TEAM.md §3.1 字段）')

    # 8. 差异化角度（v1→v2 场景）
    if re.search(C.G0_V1_RE, t) and not re.search(C.G0_DIFF_ANGLE_RE, t):
        warns.append('G0-差异化 提及 v1 但未写差异化角度（防撞车判据）')

    for f in fails:
        out.block('G0', f)
    for w in warns:
        out.warn('G0', w)
    return out


register('g0', '选题门禁')(check)
