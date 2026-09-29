#!/usr/bin/env python3
# G5 门禁实测脚本 —— 精确计数类不采信模型自报（见 VALIDATION §9）
import sys,re
t=open(sys.argv[1]).read()
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
hits=[w for w in BANNED if w in body]
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
fails=[]
if zh<200: fails.append(f'H8 字数 {zh}<200（疑似漏写，如为短稿请说明理由）')
if over: fails.append('H9 %d 段超 3 句'%len(over))
if hits: fails.append('H-禁 %s'%','.join(hits))
if meta: fails.append('H-元话语 %s'%','.join(meta))
if len(titles)<title_min: fails.append('标题策略 %d<%d'%(len(titles),title_min))
if inject_hits: fails.append('H-注入 %d 处残留（须过 sanitize 净化）'%len(inject_hits))
if ph_hits: fails.append('H-占位符 非标 %d 处: %s（须用 [待填写]，见 contracts.md H4）'%(len(ph_hits),','.join(ph_hits)))
if todo_hits and not has_gap_section: fails.append('H-占位符 %d 处 [待填写] 无文末 ## 信息缺口声明 小节'%todo_hits)
print('\n=== 门禁判定 ===')
print('FAIL: '+' / '.join(fails)) if fails else print('PASS: 字数/段落/禁用词/标题策略/注入/占位符 全达标')

# 自检明细输出（--verbose）— 2026-09-21 借鉴宇龙"先列修改与核验明细，再交付最终成果"
# 输出三段：① 核验明细（每维度得分/阈值/判定/余量） ② 未跑的检查段（硬编码清单） ③ 审核建议
if '--verbose' in sys.argv:
    def mkrow(d,s,th,ok,note):
        return f'| {d} | {s} | {th} | {"✅" if ok else "❌"} | {note} |'
    zh_margin = zh - 800  # 800 仅作"标准档"参照点，非硬阈值
    title_margin = len(titles) - title_min
    zh_tier='长稿' if zh>=1200 else ('标准' if zh>=800 else ('短稿' if zh>=500 else ('速评' if zh>=300 else '疑似漏写')))
    print('\n=== 自检明细（--verbose）===')
    print()
    print('**① 核验明细**（跑了哪些检查，得分/阈值/判定）')
    print()
    print('| 维度 | 得分 | 阈值 | 判定 | 备注 |')
    print('|------|------|------|------|------|')
    print(mkrow('H8 字数',zh,f'参考区间（档位：{zh_tier}）','字数≥200 且合理性自判',zh>=200,f'以 800 为参照点，余量 {zh_margin:+d}；合理性由 05 审核判'))
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
    if fails:
        print()
        print('**② 修改建议（对应失败项）**')
        print()
        for f in fails:
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
    verdict = 'PASS' if not fails else 'FAIL'
    npass = 10 - len(fails)
    print(f'**审核建议**：' + ('✅ 全项通过，可进 05 审核岗人工通读' if not fails else f'❌ 有 {len(fails)} 项失败，先修 FAIL 项再复检'))
    print(f'**自检覆盖**：10/10 项已跑，{npass} PASS / {len(fails)} FAIL / 0 WARN')
    print()
    print(f'=== 自检完成 · 判定：{verdict} ===')
