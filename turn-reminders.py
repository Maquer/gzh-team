#!/usr/bin/env python3
"""
turn-reminders.py：每轮行为提醒工具（5步骤+轮转）
用法：python3 turn-reminders.py <step> [--rotate]
关键约束：需指定步骤(writing/review/publish/strategy/structure)
"""
# turn-reminders.py — 每轮行为提醒（P1 借鉴 Easel 轮间提醒模式）

# Easel 参考：每轮对话开始/结束给出简要行为提醒，防止长对话中
# 遗漏关键约束（AI味、门禁、标题策略等）。

# 用法:
#   python3 turn-reminders.py show                          # 列出所有提醒
#   python3 turn-reminders.py get <step>                    # 获取某步骤提醒
#   python3 turn-reminders.py inject --step writing <task>  # 注入提醒+任务
#   python3 turn-reminders.py rotate --turn 3               # 第N轮提醒（循环）
import sys

# 按工作流步骤分类的提醒
REMINDERS = {
    "writing": [
        "AI味 ≤5 分才进审核（跑 humanizer-check.py）",
        "金句必须加粗或独立成行（脚本按格式识别）",
        "段落用空行分隔（不空行算句数会错）",
        "标题出5个5种策略，行尾标（策略名）",
        "禁用词扫描：首先/其次/此外/总而言之/不可否认/需要关注的是/接下来/需要注意的是/换句话说",
    ],
    "review": [
        "每条 finding 必须指位置：入口→步骤→实际影响（缺一段不算）",
        "AI味只信 humanizer-check.py 脚本分数，不信人感",
        "H1-H15 清单逐条过，红/黄/绿三档标注",
        "只给意见不改稿——改稿是主笔的事",
        "BLOCK 项必须修复才能发布，WARN 项建议优化",
    ],
    "publish": [
        "元数据段（平台/字数/调性）已清洗吗？（gate-check H-元数据）",
        "注入残留扫描：system-reminder/</result>/</system> 等",
        "占位符统一用 [待填写]，文末须有 ## 信息缺口声明",
        "字数档位：长稿≥1200/标准800-1200/短稿500-800/速评300-500",
        "H8 字数 <200 = BLOCK 硬拦（疑似漏写）",
    ],
    "strategy": [
        "选题必须带3个来源（≥2个可链接）+1个真反例",
        "热度≠需求：读者读完能带走一个具体动作才算成立",
        "先定不做清单（边界），再做写什么（空间）",
        "决策依据必须指向具体门禁或实测数据，给不出依据叫猜",
    ],
    "structure": [
        "先定核心问题（读者带走的那句话），再分节",
        "每节回答'读者读完能干什么'——答不出就删",
        "宁可3节打透不要6节各讲一半",
        "字数预算合计必须落在800-1200",
        "每删掉一节论证都还成立，那它本来就不该在",
    ],
}

STEP_ALIASES = {
    "write": "writing", "笔": "writing", "主笔": "writing",
    "review": "review", "审": "review", "审核": "review",
    "publish": "publish", "发": "publish", "发布": "publish",
    "strategy": "strategy", "策": "strategy", "选题": "strategy",
    "structure": "structure", "结构": "structure", "梳理": "structure",
}


def normalize_step(step):
    s = step.strip().lower()
    return STEP_ALIASES.get(s, s)


def cmd_show():
    print("=== 每轮行为提醒 ===\n")
    for step, items in REMINDERS.items():
        print(f"【{step}】({len(items)} 条)")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        print()


def cmd_get(step):
    step = normalize_step(step)
    items = REMINDERS.get(step)
    if not items:
        print(f"❌ 未知步骤: {step}，可用: {', '.join(REMINDERS.keys())}")
        sys.exit(1)
    print(f"=== {step} 提醒 ===")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")


def cmd_inject(step, task=None):
    step = normalize_step(step)
    items = REMINDERS.get(step)
    if not items:
        print(f"❌ 未知步骤: {step}，可用: {', '.join(REMINDERS.keys())}")
        sys.exit(1)
    
    reminder_lines = []
    for item in items:
        reminder_lines.append(f"  - {item}")
    
    prompt = f"## 本轮行为提醒（{step}）\n" + "\n".join(reminder_lines)
    
    task_text = task or ""
    if task_text:
        prompt += f"\n\n## 任务\n{task_text}"
    
    print(prompt)


def cmd_rotate(turn):
    all_steps = list(REMINDERS.keys())
    step = all_steps[turn % len(all_steps)]
    items = REMINDERS[step]
    # 在步骤内也轮转：第1轮取前2条，第2轮取后2条
    half = len(items) // 2
    subset = items[:half] if turn % 2 == 0 else items[half:]
    print(f"[轮 {turn} → {step} 第 {turn % 2 + 1} 组]")
    for item in subset:
        print(f"  - {item}")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="每轮行为提醒")
    sub = ap.add_subparsers(dest="cmd")
    
    sub.add_parser("show", help="列出所有提醒")
    
    p_get = sub.add_parser("get", help="获取步骤提醒")
    p_get.add_argument("step")
    
    p_inj = sub.add_parser("inject", help="注入提醒+任务")
    p_inj.add_argument("--step", required=True)
    p_inj.add_argument("--task", default=None, help="任务描述")
    
    p_rot = sub.add_parser("rotate", help="轮转提醒")
    p_rot.add_argument("--turn", type=int, required=True)
    
    args = ap.parse_args()
    if args.cmd == "show":
        cmd_show()
    elif args.cmd == "get":
        cmd_get(args.step)
    elif args.cmd == "inject":
        cmd_inject(args.step, args.task)
    elif args.cmd == "rotate":
        cmd_rotate(args.turn)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
