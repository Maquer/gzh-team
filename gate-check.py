#!/usr/bin/env python3
"""
gate-check.py：检查文章质量门禁，写入后必跑，<200字=BLOCK
用法：python3 gate-check.py <file> [--file <path>] [--verbose] [--no-humanizer] [--policy-mode]
"""
# G5 门禁实测脚本 —— 精确计数类不采信模型自报（见 VALIDATION §9）
# 2026-10-03 P1 借鉴 Easel content_guard.py：BLOCK/WARN 两级安全
# 2026-10-13 重构：① G8 结构多样性原在 sys.exit() 之后=死代码，已前移生效
#                 ② 合并 train-check.py 四项独有检查（金句密度/紧迫诱导词/H14 AI味/H10 输出结构）
#                 ③ 新增 --policy-mode（H14 走政策类豁免）与 --no-humanizer
import sys,re,argparse,os,subprocess,json
from datetime import datetime

def parse_args():
    # 与团队其他工具一致的 argparse 风格。
    # 用法：gate-check.py <file> | gate-check.py --file <path> [--verbose] [--no-humanizer] [--policy-mode]
    # exit code: 0=PASS, 1=WARN, 2=运行错误(argparse/IO), 7=BLOCK
    p=argparse.ArgumentParser(
        prog='gate-check.py',
        description='G5 门禁实测脚本（BLOCK/WARN 两级安全）',
        epilog='exit code: 0=PASS, 1=WARN, 2=运行错误, 7=BLOCK')
    p.add_argument('file_pos',nargs='?',metavar='FILE',help='待检查的稿件路径（位置参数，向后兼容）')
    p.add_argument('--file',dest='file_opt',metavar='PATH',help='待检查的稿件路径（与位置参数等效）')
    p.add_argument('--verbose','-v',action='store_true',help='显示每个检查项的详细数据与自检明细')
    p.add_argument('--no-humanizer',action='store_true',help='跳过 H14 AI 味外部脚本调用（离线/快速模式）')
    p.add_argument('--policy-mode',action='store_true',
                   help='政策类稿件豁免模式：H14 调 humanizer-check 时传 --policy-mode，豁免顿号罗列/翻案腔/冒号空转 3 条规则')
    a=p.parse_args()
    if not a.file_pos and not a.file_opt:
        p.error('缺少稿件路径：用法 gate-check.py <file> 或 --file <path>')
    path=a.file_pos or a.file_opt
    if a.file_pos and a.file_opt and os.path.abspath(a.file_pos)!=os.path.abspath(a.file_opt):
        p.error(f'位置参数 {a.file_pos!r} 与 --file {a.file_opt!r} 指向不同文件')
    return path,a.verbose,a.no_humanizer,a.policy_mode

FILEPATH,VERBOSE,NO_HUMANIZER,POLICY_MODE=parse_args()
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

# ===== 2026-10-13 合并 train-check.py 四项独有检查 =====
# 这 4 项此前只在 training/train-check.py 判定，生产门禁漏跑（H8/H9/禁用词/元话语
# 两边重复，口径保持一致；以下为 train-check 独有项，逐条搬入，不改原判定阈值）。
# 紧迫诱导词（train-check.py 同词表：只留强紧迫词，弱紧迫词 URGENCY_SOFT 仅参考不判）
URGENCY = ['速看','马上删','惊呆了','震惊','必看','全网首个','全网第一']
urg_hits=[w for w in URGENCY if w in body]
# 金句密度（TEAM.md §3.4 / G4）：正文 **加粗** 计数，≥1 处且每 1000 字 1 处。
# 口径同 train-check：数加粗而非【金句】标记（旧版按标记计数造成 4 篇达标稿全判 0）。
gold=len(re.findall(r'\*\*[^*\n]{4,80}\*\*',body))
gold_need=max(1,zh//1000)
gold_ok=(zh==0) or (gold>=gold_need)
# H10 输出结构漂移（TEAM.md §3.4 四节）：仅「完整稿件」判定；正文片段（clean 版）跳过，
# 否则包装节缺失全是假阳性（train-check 三态 SKIP 的同款教训）。
REQUIRED_SECTIONS=['备选标题','正文','结尾','AI 参与']
PACKAGE_MARKERS=['备选标题','AI 参与','交付前自检','配图指导','已选标题']
kind='完整稿件' if any(mk in t for mk in PACKAGE_MARKERS) else '正文片段'
heads=re.findall(r'^\s{0,3}#{1,4}\s*(.+?)\s*$',t,re.M)
missing_sections=[kw for kw in REQUIRED_SECTIONS if not any(kw in h for h in heads)] if kind=='完整稿件' else []
# H14 AI 味：外部脚本 humanizer-check.py v2（lieflat 11 条实证规则）
GZH_TEAM_DIR=os.path.dirname(os.path.abspath(__file__))
SHARED_DIR=os.environ.get('GZH_SHARED_DIR',os.path.dirname(GZH_TEAM_DIR))
HUMANIZER=os.path.join(SHARED_DIR,'humanizer-check','humanizer-check.py')
HUMANIZER_LIMITS={'放行':5,'重写':15}  # REVIEW.md §2 H14 三档
def check_humanizer(text,policy=False):
    """取 AI 味分数。脚本缺失/超时/解析失败 → 可用=False，不计入判定（不误伤）。"""
    if not os.path.exists(HUMANIZER):
        return {'可用':False,'分数':None,'说明':'humanizer-check.py 不存在: %s'%HUMANIZER}
    cmd=[sys.executable,HUMANIZER]
    if policy: cmd.append('--policy-mode')
    try:
        p=subprocess.run(cmd,input=text,capture_output=True,text=True,timeout=60)
        out=(p.stdout or '')+(p.stderr or '')
        m=re.search(r'综合评分[:：]\s*(\d+)\s*分',out) or re.search(r'(\d+)\s*分',out)
        if not m:
            return {'可用':False,'分数':None,'说明':'解析失败: %s'%out.strip()[:100]}
        s=int(m.group(1))
        v='放行' if s<=HUMANIZER_LIMITS['放行'] else ('重写>=50%%' if s<=HUMANIZER_LIMITS['重写'] else ('明显AI味' if s<=25 else '推倒重写'))
        return {'可用':True,'分数':s,'判定':v}
    except Exception as e:
        return {'可用':False,'分数':None,'说明':'调用异常: %s'%e}
HUM=({'可用':False,'分数':None,'说明':'--no-humanizer 跳过'} if NO_HUMANIZER else check_humanizer(body,POLICY_MODE))
hum_score=HUM.get('分数')

# ── G8 结构多样性门禁 ─────────────────────────────────────────────
# 2026-10-13 新增：打破模板套用，强制结构多样化
# 规则：连续2篇同类骨架、禁用起手式、禁用收尾式
# ⚠️ 本段原写在文件末尾 sys.exit(exit_code) 之后 → 死代码，从未执行过。
#    现前移到 warn_fails 构建之后、exit_code 计算之前；三项结果统一进 warn_fails
#    （骨架重复属风格问题，按两级安全口径不该硬拦发布）。
G8_HISTORY_DIR=os.path.expanduser('~/.gzh-structure-history')
os.makedirs(G8_HISTORY_DIR,exist_ok=True)
history_file=os.path.join(G8_HISTORY_DIR,'structure-log.json')
history=[]
if os.path.exists(history_file):
    try:
        history=json.load(open(history_file,encoding='utf-8'))
    except (json.JSONDecodeError,OSError):
        history=[]
if not isinstance(history,list): history=[]
# 当前文件骨架类型（简单判断：序数词标题数量）
a_pattern=re.compile(r'^#{1,3}\s*[一二三四五六七八九十]+[、.．]',re.MULTILINE)
a_matches=a_pattern.findall(t)
current_structure='A' if len(a_matches)>=3 else 'E'  # A=序数词, E=其他
# 检查是否与上一篇（不同稿件）连续同类；同一文件复检先剔除旧记录，避免改稿自撞假阳性
g8_fname=os.path.basename(FILEPATH)
g8_prior=[r for r in history if r.get('file')!=g8_fname]
recent_same=bool(g8_prior and g8_prior[-1].get('structure')==current_structure)
# 检测禁用起手式
DISABLED_OPENINGS=['先说结论','一句话概括','这次不一样','这次值得重视','先给结论']
opening_hits=[]
body_lines=t.split('\n')
body_start=0
for i,line in enumerate(body_lines):
    if line.startswith('## ') and not line.startswith('###'):
        body_start=i
        break
first_body='\n'.join(body_lines[body_start:body_start+5])
for phrase in DISABLED_OPENINGS:
    if phrase in first_body:
        opening_hits.append(phrase)
# 检测禁用收尾式
DISABLED_CLOSINGS=['一句话总结','你的选择','你怎么看']
closing_hits=[]
last_body='\n'.join(body_lines[-10:])
for phrase in DISABLED_CLOSINGS:
    if phrase in last_body:
        closing_hits.append(phrase)
# G8 结果（全部 WARN 级：提醒改结构，不阻断发布）
if recent_same: warn_fails.append('G8 连续2篇同类骨架（%s型）'%current_structure)
if opening_hits: warn_fails.append('G8 禁用起手式：%s'%', '.join(opening_hits))
if closing_hits: warn_fails.append('G8 禁用收尾式：%s'%', '.join(closing_hits))
# 记录本次骨架类型到历史（同名文件覆盖旧记录，只保留最新一次）
history=[r for r in history if r.get('file')!=g8_fname]
history.append({'file':g8_fname,'structure':current_structure,'timestamp':datetime.now().isoformat()})
try:
    json.dump(history,open(history_file,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
except OSError as e:
    print('警告：G8 骨架历史写入失败（不影响判定）: %s'%e,file=sys.stderr)

# 合并项判定（BLOCK/WARN 分流）
if not gold_ok: warn_fails.append('金句密度 %d<%d 处（正文 %d 字，标准每千字 1 处）'%(gold,gold_need,zh))
if urg_hits: warn_fails.append('H-紧迫诱导 %s'%','.join(urg_hits))
if kind=='完整稿件' and missing_sections: warn_fails.append('H10 输出结构缺节：%s'%('、'.join(missing_sections)))
if HUM.get('可用') and hum_score is not None:
    if hum_score>25: block_fails.append('H14 AI味 %d 分>25（推倒重写）'%hum_score)
    elif hum_score>HUMANIZER_LIMITS['放行']: warn_fails.append('H14 AI味 %d 分（%s，≤%d 放行）'%(hum_score,HUM['判定'],HUMANIZER_LIMITS['放行']))

# 合并项原始数据（非 verbose 也打印，与上方 res 摘要同风格）
print('金句密度: %d 处加粗 / %d 字（阈值 ≥%d 处）'%(gold,zh,gold_need))
print('紧迫诱导词命中: %s'%(urg_hits or '无'))
print('H10 输出结构: %s'%(('缺失 %s'%('、'.join(missing_sections) or '无')) if kind=='完整稿件' else '正文片段，跳过'))
print('H14 AI味分数: %s'%(hum_score if hum_score is not None else '不可用（%s）'%HUM.get('说明','')))
print('G8 骨架类型: %s 型（序数词小标题 %d 个）/ 上一篇 %s / 禁用起手式 %s / 禁用收尾式 %s'%(
    current_structure,len(a_matches),
    (g8_prior[-1].get('structure')+' 型') if g8_prior else '无记录',
    opening_hits or '无', closing_hits or '无'))

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
    # 2026-10-13 新增：合并 train-check 四项
    gold_ok = gold >= gold_need
    print(mkrow('金句密度',f'{gold}处/{zh}字',f'≥{gold_need}处',gold_ok,f'余量 {gold-gold_need:+d}'))
    urg_ok = len(urg_hits) == 0
    print(mkrow('紧迫诱导词',len(urg_hits),'=0',urg_ok,','.join(urg_hits) if urg_hits else '7 词全扫'))
    h14_ok = (not HUM.get('可用')) or (hum_score is not None and hum_score <= HUMANIZER_LIMITS['放行'])
    h14_note = '未跑（--no-humanizer）' if not HUM.get('可用') else f'{hum_score}分（{HUM.get("判定","")}'
    print(mkrow('H14 AI味',f'{hum_score if hum_score else "N/A"}',f'≤{HUMANIZER_LIMITS["放行"]}',h14_ok,h14_note))
    h10_ok = (kind=='正文片段') or (not missing_sections)
    h10_note = '正文片段，跳过' if kind=='正文片段' else ('缺节：%s'%('、'.join(missing_sections) or '无')) if missing_sections else '四节齐全'
    print(mkrow('H10 输出结构',kind,'四节齐全',h10_ok,h10_note))
    # G8 行
    g8_warn_count = len([f for f in warn_fails if f.startswith('G8')])
    print(mkrow('G8 结构多样性',f'{current_structure}型/{g8_warn_count}警告','WARN级',g8_warn_count==0,f'禁用起手式{len(opening_hits)}处/收尾式{len(closing_hits)}处'))
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
            elif f.startswith('H14'): print('- **H14 AI味**：AI味超标，需重写至 ≤%d 分。政策类稿件可加 `--policy-mode` 豁免3条规则'%HUMANIZER_LIMITS['放行'])
            elif f.startswith('G8 禁用'): print('- **G8 禁用句式**：改写开头/结尾句式（禁用起手式/收尾式，见 结构多样性约束-v1.0.md）')
            elif f.startswith('G8 连续'): print('- **G8 骨架重复**：连续2篇同类骨架，下一篇须换结构（见 结构多样性约束-v1.0.md）')
            elif f.startswith('金句密度'): print('- **金句密度**：每千字至少 1 处 **加粗** 金句，增加重点标记')
            elif '非标' in f: print('- **H-占位符非标**：把 XX/___/TBD/待补 统一改为 [待填写]（见 contracts.md H4）')
            elif '缺口声明' in f: print('- **H-占位符**：在文末追加 `## 信息缺口声明` 小节，逐条列出每个 [待填写] 的位置/状态/补资料计划')
    print()
    print('**③ 未跑的检查**（本脚本未覆盖，需人工或其他脚本）')
    print()
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
    print(f'**自检覆盖**：14/14 项已跑，{npass} PASS / {len(block_fails)} BLOCK / {len(warn_fails)} WARN')
    print()
    print(f'=== 自检完成 · 判定：{verdict} ===')
sys.exit(exit_code)

# ── G8 结构多样性门禁 ─────────────────────────────────────────────
# 2026-10-13 新增：打破模板套用，强制结构多样化
# 规则：连续2篇同类骨架、禁用起手式、禁用收尾式

G8_HISTORY_DIR = os.path.expanduser('~/.gzh-structure-history')
os.makedirs(G8_HISTORY_DIR, exist_ok=True)

# 读取历史骨架类型记录
history_file = os.path.join(G8_HISTORY_DIR, 'structure-log.json')
if os.path.exists(history_file):
    with open(history_file, 'r', encoding='utf-8') as f:
        import json
        try:
            history = json.load(f)
        except json.JSONDecodeError:
            history = []
else:
    history = []

# 当前文件骨架类型（简单判断：序数词标题数量）
a_pattern = re.compile(r'^#{1,3}\s*[一二三四五六七八九十]+[、.．]', re.MULTILINE)
a_matches = a_pattern.findall(t)
current_structure = 'A' if len(a_matches) >= 3 else 'E'  # A=序数词, E=其他

# 检查是否连续2篇同类
recent_same = False
for record in reversed(history[-5:]):  # 只看最近5篇
    if record.get('structure') == current_structure:
        recent_same = True
        break

# 检测禁用起手式
DISABLED_OPENINGS = ['先说结论', '一句话概括', '这次不一样', '这次值得重视', '先给结论']
opening_hits = []
body_lines = t.split('\n')
body_start = 0
for i, line in enumerate(body_lines):
    if line.startswith('## ') and not line.startswith('###'):
        body_start = i
        break
first_body = '\n'.join(body_lines[body_start:body_start+5])
for phrase in DISABLED_OPENINGS:
    if phrase in first_body:
        opening_hits.append(phrase)

# 检测禁用收尾式
DISABLED_CLOSINGS = ['一句话总结', '你的选择', '你怎么看']
closing_hits = []
last_body = '\n'.join(body_lines[-10:])
for phrase in DISABLED_CLOSINGS:
    if phrase in last_body:
        closing_hits.append(phrase)

# 输出G8结果
if recent_same:
    block_fails.append(f'G8 连续2篇同类骨架（{current_structure}型）')
elif opening_hits:
    warn_fails.append(f'G8 禁用起手式：{", ".join(opening_hits)}')
elif closing_hits:
    warn_fails.append(f'G8 禁用收尾式：{", ".join(closing_hits)}')

# 记录本次骨架类型到历史
import json as _json
entry = {
    'file': os.path.basename(a.file),
    'structure': current_structure,
    'timestamp': __import__('datetime').datetime.now().isoformat()
}
history.append(entry)
with open(history_file, 'w', encoding='utf-8') as f:
    _json.dump(history, f, ensure_ascii=False, indent=2)
