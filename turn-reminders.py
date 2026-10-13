#!/usr/bin/env python3
"""turn-reminders.py: every-round behavior reminders (5 steps + rotation).

v4.0.0 rebuild: clean rewrite, reminder content identical to v3.3.0.
Usage:
  python3 turn-reminders.py show                          # list all reminders
  python3 turn-reminders.py get <step>                    # reminders for a step
  python3 turn-reminders.py inject --step writing --task <task>
  python3 turn-reminders.py rotate --turn 3               # Nth-round reminder (loops)

Constraint: a step is required (writing/review/publish/strategy/structure).
Exit codes: 0 ok; 2 bad args / unknown step.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

REMINDERS = {
    "writing": [
        "AI\u5473 \u22645 \u5206\u624d\u8fdb\u5ba1\u6838\uff08\u8dd1 humanizer-check.py\uff09",
        "\u91d1\u53e5\u5fc5\u987b\u52a0\u7c97\u6216\u72ec\u7acb\u6210\u884c\uff08\u811a\u672c\u6309\u683c\u5f0f\u8bc6\u522b\uff09",
        "\u6bb5\u843d\u7528\u7a7a\u884c\u5206\u9694\uff08\u4e0d\u7a7a\u884c\u7b97\u53e5\u6570\u4f1a\u9519\uff09",
        "\u6807\u9898\u51fa5\u4e2a5\u79cd\u7b56\u7565\uff0c\u884c\u5c3e\u6807\uff08\u7b56\u7565\u540d\uff09",
        "\u7981\u7528\u8bcd\u626b\u63cf\uff1a\u9996\u5148/\u5176\u6b21/\u6b64\u5916/\u603b\u800c\u8a00\u4e4b/\u4e0d\u53ef\u5426\u8ba4/\u9700\u8981\u5173\u6ce8\u7684\u662f/\u63a5\u4e0b\u6765/\u9700\u8981\u6ce8\u610f\u7684\u662f/\u6362\u53e5\u8bdd\u8bf4",
    ],
    "review": [
        "\u6bcf\u6761 finding \u5fc5\u987b\u6307\u4f4d\u7f6e\uff1a\u5165\u53e3\u2192\u6b65\u9aa4\u2192\u5b9e\u9645\u5f71\u54cd\uff08\u7f3a\u4e00\u6bb5\u4e0d\u7b97\uff09",
        "AI\u5473\u53ea\u4fe1 humanizer-check.py \u811a\u672c\u5206\u6570\uff0c\u4e0d\u4fe1\u4eba\u611f",
        "H1-H15 \u6e05\u5355\u9010\u6761\u8fc7\uff0c\u7ea2/\u9ec4/\u7eff\u4e09\u6863\u6807\u6ce8",
        "\u53ea\u7ed9\u610f\u89c1\u4e0d\u6539\u7a3f\u2014\u2014\u6539\u7a3f\u662f\u4e3b\u7b14\u7684\u4e8b",
        "BLOCK \u9879\u5fc5\u987b\u4fee\u590d\u624d\u80fd\u53d1\u5e03\uff0cWARN \u9879\u5efa\u8bae\u4f18\u5316",
    ],
    "publish": [
        "\u5143\u6570\u636e\u6bb5\uff08\u5e73\u53f0/\u5b57\u6570/\u8c03\u6027\uff09\u5df2\u6e05\u6d17\u5417\uff1f\uff08gate-check H-\u5143\u6570\u636e\uff09",
        "\u6ce8\u5165\u6b8b\u7559\u626b\u63cf\uff1asystem-reminder/</result>/</system> \u7b49",
        "\u5360\u4f4d\u7b26\u7edf\u4e00\u7528 [\u5f85\u586b\u5199]\uff0c\u6587\u672b\u987b\u6709 ## \u4fe1\u606f\u7f3a\u53e3\u58f0\u660e",
        "\u5b57\u6570\u6863\u4f4d\uff1a\u957f\u7a3f\u22651200/\u6807\u51c6800-1200/\u77ed\u7a3f500-800/\u901f\u8bc4300-500",
        "H8 \u5b57\u6570 <200 = BLOCK \u786c\u62e6\uff08\u7591\u4f3c\u6f0f\u5199\uff09",
    ],
    "strategy": [
        "\u9009\u9898\u5fc5\u987b\u5e263\u4e2a\u6765\u6e90\uff08\u22652\u4e2a\u53ef\u94fe\u63a5\uff09+1\u4e2a\u771f\u53cd\u4f8b",
        "\u70ed\u5ea6\u2260\u9700\u6c42\uff1a\u8bfb\u8005\u8bfb\u5b8c\u80fd\u5e26\u8d70\u4e00\u4e2a\u5177\u4f53\u52a8\u4f5c\u624d\u7b97\u6210\u7acb",
        "\u5148\u5b9a\u4e0d\u505a\u6e05\u5355\uff08\u8fb9\u754c\uff09\uff0c\u518d\u505a\u5199\u4ec0\u4e48\uff08\u7a7a\u95f4\uff09",
        "\u51b3\u7b56\u4f9d\u636e\u5fc5\u987b\u6307\u5411\u5177\u4f53\u95e8\u7981\u6216\u5b9e\u6d4b\u6570\u636e\uff0c\u7ed9\u4e0d\u51fa\u4f9d\u636e\u53eb\u731c",
    ],
    "structure": [
        "\u5148\u5b9a\u6838\u5fc3\u95ee\u9898\uff08\u8bfb\u8005\u5e26\u8d70\u7684\u90a3\u53e5\u8bdd\uff09\uff0c\u518d\u5206\u8282",
        "\u6bcf\u8282\u56de\u7b54'\u8bfb\u8005\u8bfb\u5b8c\u80fd\u5e72\u4ec0\u4e48'\u2014\u2014\u7b54\u4e0d\u51fa\u5c31\u5220",
        "\u5b81\u53ef3\u8282\u6253\u900f\u4e0d\u89816\u8282\u5404\u8bb2\u4e00\u534a",
        "\u5b57\u6570\u9884\u7b97\u5408\u8ba1\u5fc5\u987b\u843d\u5728800-1200",
        "\u6bcf\u5220\u6389\u4e00\u8282\u8bba\u8bc1\u90fd\u8fd8\u6210\u7acb\uff0c\u90a3\u5b83\u672c\u6765\u5c31\u4e0d\u8be5\u5728",
    ],
}

STEP_ALIASES = {
    "write": "writing", "\u7b14": "writing", "\u4e3b\u7b14": "writing",
    "review": "review", "\u5ba1": "review", "\u5ba1\u6838": "review",
    "publish": "publish", "\u53d1": "publish", "\u53d1\u5e03": "publish",
    "strategy": "strategy", "\u7b56": "strategy", "\u9009\u9898": "strategy",
    "structure": "structure", "\u7ed3\u6784": "structure", "\u68b3\u7406": "structure",
}


def normalize_step(step):
    s = step.strip().lower()
    return STEP_ALIASES.get(s, s)


def _lookup(step):
    step = normalize_step(step)
    items = REMINDERS.get(step)
    if not items:
        print("\u672a\u77e5\u6b65\u9aa4: %s\uff0c\u53ef\u7528: %s"
              % (step, ", ".join(REMINDERS.keys())), file=sys.stderr)
        return None, None
    return step, items


def cmd_show(args):
    print("=== \u6bcf\u8f6e\u884c\u4e3a\u63d0\u9192 ===\n")
    for step, items in REMINDERS.items():
        print("\u3010%s\u3011(%d \u6761)" % (step, len(items)))
        for i, item in enumerate(items, 1):
            print("  %d. %s" % (i, item))
        print()
    return 0


def cmd_get(args):
    step, items = _lookup(args.step)
    if items is None:
        return 2
    print("=== %s \u63d0\u9192 ===" % step)
    for i, item in enumerate(items, 1):
        print("  %d. %s" % (i, item))
    return 0


def cmd_inject(args):
    step, items = _lookup(args.step)
    if items is None:
        return 2
    prompt = "## \u672c\u8f6e\u884c\u4e3a\u63d0\u9192\uff08%s\uff09\n" % step
    prompt += "\n".join("  - %s" % item for item in items)
    if args.task:
        prompt += "\n\n## \u4efb\u52a1\n%s" % args.task
    print(prompt)
    return 0


def cmd_rotate(args):
    turn = args.turn
    all_steps = list(REMINDERS.keys())
    step = all_steps[turn % len(all_steps)]
    items = REMINDERS[step]
    half = len(items) // 2
    subset = items[:half] if turn % 2 == 0 else items[half:]
    print("[\u8f6e %d \u2192 %s \u7b2c %d \u7ec4]" % (turn, step, turn % 2 + 1))
    for item in subset:
        print("  - %s" % item)
    return 0


def main():
    parser = gzh_cli.build_parser("turn-reminders.py", "\u6bcf\u8f6e\u884c\u4e3a\u63d0\u9192\uff085\u6b65\u9aa4+\u8f6e\u8f6c\uff09")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="list all reminders")
    p_get = sub.add_parser("get", help="reminders for a step")
    p_get.add_argument("step", help="step name")
    p_inj = sub.add_parser("inject", help="inject reminders+task")
    p_inj.add_argument("--step", required=True, help="step name")
    p_inj.add_argument("--task", default=None, help="task description")
    p_rot = sub.add_parser("rotate", help="rotate reminders")
    p_rot.add_argument("--turn", type=int, required=True, help="round number")
    args = parser.parse_args()
    return {"show": cmd_show, "get": cmd_get, "inject": cmd_inject,
            "rotate": cmd_rotate}[args.cmd](args)


if __name__ == "__main__":
    gzh_cli.run_main(main)
