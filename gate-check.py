#!/usr/bin/env python3
"""
gate-check.py：检查文章质量门禁，写入后必跑，<200字=BLOCK
用法：python3 gate-check.py <file> [--file <path>] [--verbose]
"""
# G5 门禁实测脚本 —— 精确计数类不采信模型自报（见 VALIDATION §9）
# 2026-10-03 P1 借鉴 Easel content_guard.py：BLOCK/WARN 两级安全
import sys,re,argparse,os

def parse_args():
    # 与团队其他工具一致的 argparse 风格。
    # 用法：gate-check.py <file> | gate-check.py --file <path> [--verbose]
    # exit code: 0=PASS, 1=WARN, 2=运行错误(argparse/IO), 7=BLOCK
    p=argparse.ArgumentParser(
        prog='gate-check.py',
        description='G5 门禁实测脚本（BLOCK/WARN 两级安全）',
        epilog='exit code: 0=PASS, 1=WARN, 2=运行错误, 7=BLOCK')
    p.add_argument('file_pos',nargs='?',metavar='FILE',help='待检查的稿件路径（位置参数，向后兼容）')
    p.add_argument('--file',dest='file_opt',metavar='PATH',help='待检查的稿件路径（与位置参数等效）')
    p.add_argument('--verbose','-v',action='store_true',help='显示每个检查项的详细数据与自检明细')
    a=p.parse_args()
    if not a.file_pos and not a.file_opt:
        p.error('缺少稿件路径：用法 gate-check.py <file> 或 --file <path>')
    path=a.file_pos or a.file_opt
    if a.file_pos and a.file_opt and os.path.abspath(a.file_pos)!=os.path.abspath(a.file_opt):
        p.error(f'位置参数 {a.file_pos!r} 与 --file {a.file_opt!r} 指向不同文件')
    return path,a.verbose

FILEPATH,VERBOSE=parse_args()
try:
    t=open(FILEPATH).read()
except OSError as e:
    print(f'错误：无法读取稿件 {FILEPATH}: {e}',file=sys.stderr)
    sys.exit(2)
# 终止节补齐「结尾」「发布」：规范(TEAM.md §3.4)要求文章有 ## 结尾 节。
# 当节序为 正文→结尾 时，旧列表缺 结尾 会把结尾字数算进正文，H8 虚高。
# 实测：对历史 5 篇影响为 0（它们的 配图/AI参与 节在 结尾 之前先终止）；
#       对 A/B 生成的 正文→结尾 结构影响 60-300 字（2026-09-18 实测）。
m=re.search(r'##\s*正文(.*?)(?=\n#{2,3}\s*(配图|缺口判断|AI 参与|自检|结尾|发布))',t,re.S)
body=m.group(1) if m else t
zh=len(re.findall(r'[\u4e00-\u9fff]',body))
paras=[p.strip() for p in re.split(r'\n\s*\n',body) if p.strip() and not p.strip().startswith(('**','##','【','```'))]
sents=lambda p:len([x for x in re.split(r'[。！？]',re.sub(r'\*\*|【金句】','',p)) if x.strip()])
over=[(i+1,sents(p),p[:18]) for i,p in enumerate(paras) if sents(p)>3]
BANNED=['首先','其次','此外','总而言之','不可否认','需要关注的是','接下来','需要注意的是','换句话说']
# 中文无 \b，用"前后非中文"做软边界，避免 URL/代码中误报
hits=[w for w in BANNED if re.search(rf'(?<![\u4e00-\u9fff]){re.escape(w)}(?![\u4e00-\u9fff])', body)]
meta=[w for w in ['这里多余','刚才说','删掉。','多余，删'] if w in body]
titles=re.findall(r'（[^）]+）',t)
# 阈值：备选阶段要求 5 个（覆盖 5 类策略），已选阶段要求 ≥1（选定标题须标注策略）
title_min=1 if '已选标题' in t else 5
# H-注入：草稿不得含行首注入标记（system-reminder / </result> / <system> 等）
# 防模型返回尾部被拼接伪指令流进发布产物；清洗漏网或绕过 sanitize 时兜底
INJECT_RE=re.compile(r'^\s*(?:system[-_ ]?reminder|system\s*prompt|system\s*:|</?(?:result|system|minis)\b[^>]*>|<\|im_end\|>|ignore\s+(?:all\s+)?previous\s+instructions)',re.I|re.M)
inject_hits=INJECT_RE.findall(t)
# 占位符统一规则（contracts.md H4，2026-09-19 借鉴专业文档生成团队）
# [待填写] = 预期行为（资料不足如实标记，对齐严审之"不扣分"），但必须在文末 ## 信息缺口声明 小节显式列出
# 非标占位符（XX/___/xxx/待补/TBD）= 内容缺陷（主笔没处理完就交）→ FAIL
PLACEHOLDER_RE=re.compile(r'XX+|xx+|_{2,}|TBD|tbd|待补')
ph_hits=PLACEHOLDER_RE.findall(t)
todo_hits=t.count('[待填写]')
has_gap_section='信息缺口声明' in t
# H8 政策变更（2026-09-24 A 级决策）：字数不再设硬下限，由主笔+审核按题材判合理性
# 800-1200 降为「参考区间」，短稿/长稿都可发，唯一 FAIL 条件是 <200 疑似漏写
res={'正文字数':zh,'字数档位':'长稿' if zh>=1200 else ('标准' if zh>=800 else ('短稿' if zh>=500 else ('速评' if zh>=300 else '疑似漏写'))),'段落数':len(paras),
     '超3句段落数':len(over),'超标明细':over,'禁用词命中':hits,
     '元话语命中':meta,'标题策略数':len(titles),'标题策略阈值':title_min,
     'AI参与标注':bool(re.search(r'AI\s*参与(程度|占比)',''.join(t)) or 'AI 参与' in t),
     '注入残留':len(inject_hits),
     '非标占位符':ph_hits,'待填写数':todo_hits,'有缺口声明':has_gap_section}
for k,v in res.items(): print(f'{k}: {v}')
# H-元数据：正文不得包含"平台：公众号"等元数据段（引用块格式）
META_RE = re.compile(r'平台：公众号|字数：约|调性：')
meta_hits = META_RE.findall(t)
# ===== 2026-10-03 P1 借鉴 Easel content_guard.py：两级安全 =====
# BLOCK 级 = 硬拦发布（exit 7），WARN 级 = 只提醒不阻断
# 原单级 FAIL 全部改为按严重程度分流
block_fails=[]  # 硬拦：安全/完整性问题
warn_fails=[]    # 软提醒：质量/风格问题

# BLOCK 级：安全与完整性（原硬 FAIL 中的安全类）
if zh<200: block_fails.append(f'H8 字数 {zh}<200（疑似漏写，如为短稿请说明理由）')
if inject_hits: block_fails.append('H-注入 %d 处残留（须过 sanitize 净化）'%len(inject_hits))
if ph_hits: block_fails.append('H-占位符 非标 %d 处: %s（须用 [待填写]，见 contracts.md H4）'%(len(ph_hits),','.join(ph_hits)))
if todo_hits and not has_gap_section: block_fails.append('H-占位符 %d 处 [待填写] 无文末 ## 信息缺口声明 小节'%todo_hits)
# H-元数据：正文不得包含元数据段（BLOCK 级——泄漏到正文是不可接受的）
if meta_hits:
    block_fails.append(f'H-元数据 {len(meta_hits)} 处残留: {",".join(set(meta_hits))}')

# WARN 级：质量与风格（只提醒，不阻断发布）
if over: warn_fails.append('H9 %d 段超 3 句'%len(over))
if hits: warn_fails.append('H-禁 %s'%','.join(hits))
if meta: warn_fails.append('H-元话语 %s'%','.join(meta))
if len(titles)<title_min: warn_fails.append('标题策略 %d<%d'%(len(titles),title_min))

# exit code: 0=PASS, 1=WARN only, 7=BLOCK
exit_code = 7 if block_fails else (1 if warn_fails else 0)
print('\n=== 门禁判定（两级：BLOCK/WARN）===')
if block_fails:
    print('❌ BLOCK: '+' / '.join(block_fails))
    print('   → exit 7，硬拦发布，必须修复后复检')
elif warn_fails:
    print('⚠️  WARN: '+' / '.join(warn_fails))
    print('   → 只提醒不阻断，建议优化后发布')
else:
    print('✅ PASS: BLOCK 0 / WARN 0，全项达标')

# 自检明细输出（--verbose）— 2026-09-21 借鉴宇龙"先列修改与核验明细，再交付最终成果"
# 输出三段：① 核验明细（每维度得分/阈值/判定/余量） ② 未跑的检查段（硬编码清单） ③ 审核建议
if VERBOSE:
    def mkrow(d,s,th,ok,note):
        return f'| {d} | {s} | {th} | {"✅" if ok else "❌"} | {note} |'
    zh_margin = zh - 800  # 800 仅作"标准档"参照点，非硬阈值
    title_margin = len(titles) - title_min
    zh_tier='长稿' if zh>=1200 else ('标准' if zh>=800 else ('短稿' if zh>=500 else ('速评' if zh>=300 else '疑似漏写')))
    print('\n=== 自检明细（--verbose）===')
    print()
    print(f'稿件：{FILEPATH}')
    print()
    # 逐项原始数据（先摆事实，再看判定表）
    print('**⓪ 检查项原始数据**')
    print()
    print(f'- 正文字数：{zh}（档位 {zh_tier}，参照点 800，余量 {zh_margin:+d}）')
    print(f'- 段落数：{len(paras)}（已排除 **/##/【/``` 开头的非正文块）')
    print(f'- 超 3 句段落：{len(over)} 段' + ('' if not over else ' → ' + '; '.join(f'第{i}段{s}句「{p}…」' for i,s,p in over)))
    print(f'- 禁用词命中：{len(hits)} 个' + ('' if not hits else ' → ' + '、'.join(hits)))
    print(f'- 元话语命中：{len(meta)} 个' + ('' if not meta else ' → ' + '、'.join(meta)))
    print(f'- 标题策略（括号标注）：{len(titles)} 个 / 阈值 ≥{title_min}' + ('' if not titles else ' → ' + '、'.join(titles)))
    print(f'- 注入残留：{len(inject_hits)} 处' + ('' if not inject_hits else ' → ' + ' | '.join(repr(x)[:60] for x in inject_hits)))
    print(f'- 元数据残留：{len(meta_hits)} 处' + ('' if not meta_hits else ' → ' + '、'.join(sorted(set(meta_hits)))))
    print(f'- 非标占位符：{len(ph_hits)} 处' + ('' if not ph_hits else ' → ' + '、'.join(ph_hits)))
    print(f'- [待填写]：{todo_hits} 处 / 信息缺口声明：{"有" if has_gap_section else "无"}')
    print(f'- AI 参与标注：{"有" if res["AI参与标注"] else "无"}')
    print()
    print('**① 核验明细**（跑了哪些检查，得分/阈值/判定）')
    print()
    print('| 维度 | 得分 | 阈值 | 判定 | 备注 |')
    print('|------|------|------|------|------|')
    print(mkrow('H8 字数',zh,f'参考区间（档位：{zh_tier}）',zh>=200,f'以 800 为参照点，余量 {zh_margin:+d}；合理性由 05 审核判'))
    print(mkrow('段落数',len(paras),'参考',True,'仅统计'))
    print(mkrow('H9 段落超 3 句',len(over),'=0',not over,f'{len(over)} 段需拆' if over else '全达标'))
    print(mkrow('H-禁用词',len(hits),'=0',not hits,','.join(hits) if hits else 'BANNED 9 词全扫'))
    print(mkrow('H-元话语',len(meta),'=0',not meta,','.join(meta) if meta else '4 词全扫'))
    print(mkrow('标题策略数',len(titles),f'≥{title_min}',len(titles)>=title_min,f'余量 {title_margin:+d}'))
    ai_ok=bool(re.search(r'AI\s*参与(程度|占比)|^##\s*AI\s*参与', t, re.I|re.M))
    print(mkrow('AI参与标注','有' if ai_ok else '无','有',ai_ok,'软检查'))
    print(mkrow('H-注入残留',len(inject_hits),'=0',not inject_hits,'8 种正则全扫'))
    print(mkrow('H-占位符 非标',len(ph_hits),'=0',not ph_hits,','.join(ph_hits) if ph_hits else 'PLACEHOLDER_RE 全扫'))
    print(mkrow('H-占位符 声明',f'{todo_hits}/{has_gap_section}','[待填写] 须有缺口声明',not todo_hits or has_gap_section,''))
    if block_fails or warn_fails:
        print()
        if block_fails:
            print('**② BLOCK 修改建议（硬拦，必须修复）**')
            print()
        if warn_fails:
            print('**② WARN 优化建议（只提醒，建议优化）**')
            print()
        all_items = block_fails + warn_fails
        for f in all_items:
            if f.startswith('H8 字数'): print('- **H8**：正文 <200 字，疑似漏写。如为短稿/速评稿请主笔在「元信息」中写明类型（速评/短评），05 审核判合理性')
            elif f.startswith('H9'): print('- **H9**：将超 3 句段落拆为短句段落（每段 1-3 句，参见 TEAM.md §3.4）')
            elif f.startswith('H-禁'): print('- **H-禁**：改写或删除禁用词（BANNED 9 词：首先/其次/此外/总而言之/不可否认/需要关注的是/接下来/需要注意的是/换句话说）')
            elif f.startswith('H-元话语'): print('- **H-元话语**：删掉"这里多余/刚才说/删掉。/多余，删"等自我元话语')
            elif f.startswith('标题策略'): print('- **标题策略数不足**：补齐备选标题数量（5 个覆盖 5 类策略：悬念/数字/反常识/盘点/悬念+数字）')
            elif f.startswith('H-注入'): print('- **H-注入**：过 sanitize 净化（清洗模型尾部 system-reminder / </result> / <|im_end|> 等 8 种残留）')
            elif '非标' in f: print('- **H-占位符非标**：把 XX/___/TBD/待补 统一改为 [待填写]（见 contracts.md H4）')
            elif '缺口声明' in f: print('- **H-占位符**：在文末追加 `## 信息缺口声明` 小节，逐条列出每个 [待填写] 的位置/状态/补资料计划')
    print()
    print('**③ 未跑的检查**（本脚本未覆盖，需人工或其他脚本）')
    print()
    print('- 未跑 `train-check.py`（C1-C7 风格维度：比例/年代/印刷纹理/negative 段等）')
    print('- 未跑 `link-check.py`（外链可访问性、URL 有效性）')
    print('- 未跑 `verify-all.py`（H11/H12/H13 合规层：敏感词/绝对化用语/广告法/AI 生成标识）')
    print('- 未过 05 审核岗**人工通读**（AI 参与比例是否如实、数据是否可追溯）')
    print()
    verdict = 'PASS' if not block_fails and not warn_fails else ('BLOCK' if block_fails else 'WARN')
    npass = 10 - len(block_fails) - len(warn_fails)
    if not block_fails and not warn_fails:
        print('**审核建议**：✅ BLOCK 0 / WARN 0，全项通过，可进 05 审核岗人工通读')
    elif block_fails:
        print(f'**审核建议**：❌ {len(block_fails)} 项 BLOCK 硬拦，必须修复后复检')
    else:
        print(f'**审核建议**：⚠️  {len(warn_fails)} 项 WARN 只提醒，建议优化后发布')
    print(f'**自检覆盖**：10/10 项已跑，{npass} PASS / {len(block_fails)} BLOCK / {len(warn_fails)} WARN')
    print()
    print(f'=== 自检完成 · 判定：{verdict} ===')
sys.exit(exit_code)
