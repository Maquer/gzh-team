#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 2 次岗位培训：7 岗基线实测（2026-09-19）
跑 7 个非主笔岗的基线，产出基线数据填 TRAINING.md §2 表格。
用法：python3 run-baselines.py --model <model_id>
"""
import subprocess, json, os, io, time, argparse, re
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, 'baselines')

BANNED = ['首先','其次','此外','总而言之','不可否认','需要关注的是','接下来',
          '需要注意的是','换句话说']
URGENCY = ['速看','马上删','惊呆了','震惊','必看','全网首个','全网第一']
URGENCY_SOFT = ['立即','紧急','限时']  # 弱紧迫词，脚本不判 FAIL
META = ['我作为 AI','作为助手','让我们深入探讨','总而言之，让我们','接下来让我们一起']

# 7 岗任务（09 结构梳理不在 dispatch 映射，跳过）
TASKS = [
    ('01-选题规划师', '为「AI 写作工具评测」出 3 个候选选题卡。每卡必须含：选题方向 / 3 来源（至少 2 个可链接）/ 1 反例 / 读者需求锚点 / 选题排期表行（状态/优先级/预计字数/预计调性）。'),
    ('03-审核',       '审一篇已有稿件（我提供内容在下面）。按团队 G5 审核门禁出审核报告：H1-H14 逐条判 PASS/FAIL，给具体修改建议。稿件内容：# 4 部门 14 条新规落地一年：你的 AI 文章标注了吗\n\n## 已选标题\n4 部门 14 条新规落地一年：你的 AI 文章标注了吗（反常识）\n\n## 正文\n去年 9 月 1 日，4 部门联合发布的 AI 生成内容标识办法正式施行。一年过去，你的公众号文章标注了吗？\n\n**新规的核心是**：AI 生成或辅助生成的内容必须显式标注。\n\n不标注的后果包括限流、下架、账号封禁。\n\n## 结尾\n欢迎在看、点赞、转发。\n'),
    ('04-排版',       '为上面这篇稿件出排版方案。给出主题色（5 套预设之一）+ 模板选择 + 双版本输出（HTML+纯文本）+ 配图清单（每张含比例 2.35:1/16:9/1:1 之一）。'),
    ('05-发布',       '为上面这篇稿件出发布决策。给出：发布时间（晚间/周末，避开 22:30 后）/ 封面选择 / 摘要（120 字）/ 互动话术 / 推送节奏。'),
    ('06-负责人',     '调度「AI 写作工具评测」选题的生产。给出：选题评估（做/不做 + 理由）/ 排期 / 分工 / 优先级。'),
    ('07-读者互动官', '回复 3 条评论。评论 1：「这个 AI 标识真的能查到吗？」评论 2：「我们小团队做不了啊」评论 3：「已经标注了，感觉没用」'),
    ('08-数据分析师', '分析上周公众号阅读量数据。数据：周一 1200 / 周二 1500 / 周三 800 / 周四 2000 / 周五 3000 / 周六 5000 / 周日 4500。给出：核心指标 / 趋势 / 异常点 / 建议。'),
    ('09-结构梳理', '为「AI 写作工具评测」选题出结构方案。给出：结构案（标题 / 观点 / 分节结构 / 字数预算）/ 每节要回答的问题 / 金句位 / 配图位 / 反例。'),
]

def dispatch_prompt(role, task):
    r = subprocess.run(['python3', f'{BASE}/gzh-dispatch.py', task,
                        '--role-card', role, '--dry-run'],
                       capture_output=True, text=True, timeout=30)
    return r.stdout

def call_model(prompt, model, max_tokens=4000):
    payload = {"messages":[{"role":"user","content":prompt}],"max_tokens":max_tokens}
    with io.open('/tmp/_base_prompt.json','w',encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    r = subprocess.run(['minis-model-use','run','--model',model,
                        '--input','/tmp/_base_prompt.json'],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        return None, r.stderr[:200]
    try:
        d = json.loads(r.stdout)
        # minis-model-use 返回结构：{ok, data:{output_text, ...}}
        txt = d.get('data', {}).get('output_text') or d.get('output_text') or d.get('content') or ''
        if not txt:
            return None, 'empty output: ' + json.dumps(d, ensure_ascii=False)[:200]
        return txt, None
    except Exception as e:
        return None, f'parse: {e}'

def check_rules(text):
    out = {}
    out['元话语'] = [w for w in META if w in text]
    out['禁用词'] = [w for w in BANNED if w in text]
    out['紧迫诱导词'] = [w for w in URGENCY if w in text]
    out['占位符'] = re.findall(r'XX+|xx+|_{2,}|TBD|tbd|待补', text)
    out['pass'] = not (out['元话语'] or out['禁用词'] or out['紧迫诱导词'] or out['占位符'])
    return out

def run_one(role, task, model, interval):
    print(f'\n=== {role} ===')
    prompt = dispatch_prompt(role, task)
    text, err = call_model(prompt, model)
    if not text:
        print(f'  失败: {err}')
        return {'role':role,'task':task,'file':None,'rules':None,'status':'fail','err':err}
    safe_role = role.replace('-','_')
    out_path = os.path.join(OUT_DIR, f'baseline-{safe_role}.md')
    io.open(out_path,'w',encoding='utf-8').write(text)
    print(f'  产出: {out_path} ({len(text)} 字符)')
    time.sleep(interval)
    rules = check_rules(text)
    print(f'  通用规则: {rules["pass"]} (元话语={rules["元话语"]} 禁用词={rules["禁用词"]} 紧迫={rules["紧迫诱导词"]} 占位符={rules["占位符"]})')
    return {'role':role,'task':task,'file':out_path,'rules':rules,'status':'ok','chars':len(text)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='sensenova-6.8-flash-lite')
    ap.add_argument('--interval', type=int, default=45)
    ap.add_argument('--only', default=None, help='只跑某个岗（如 01-选题规划师）')
    args = ap.parse_args()
    print('模型:', args.model, '| 间隔:', args.interval, 's')
    tasks = TASKS if not args.only else [t for t in TASKS if t[0]==args.only]
    results = []
    for role, task in tasks:
        try:
            results.append(run_one(role, task, args.model, args.interval))
        except Exception as e:
            print(f'  异常: {e}')
            results.append({'role':role,'task':task,'file':None,'rules':None,'status':'error','err':str(e)})
    summary = {'model':args.model, 'timestamp':time.strftime('%Y-%m-%d %H:%M'),
               'results':results, 'total':len(results),
               'ok':sum(1 for r in results if r['status']=='ok'),
               'rules_pass':sum(1 for r in results if r['rules'] and r['rules']['pass'])}
    report_path = os.path.join(OUT_DIR, f'report-{time.strftime("%Y%m%d-%H%M")}.json')
    io.open(report_path,'w',encoding='utf-8').write(json.dumps(summary, ensure_ascii=False, indent=2))
    print('\n' + '='*60)
    print(f'完成: {summary["ok"]}/{summary["total"]} 岗成功')
    print(f'通用规则通过率: {summary["rules_pass"]}/{summary["ok"]}')
    print(f'报告: {report_path}')

if __name__ == '__main__':
    main()
