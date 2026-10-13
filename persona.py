#!/usr/bin/env python3
"""persona.py：团队画像管理工具（角色卡加载/注入）。

v4.0.0 重建：干净重写，逻辑与 v3.3.0 一致。
用法：
  python3 persona.py show                          # 显示全部人设摘要
  python3 persona.py verify                        # 验证每张角色卡都有名字
  python3 persona.py inject --role 01 <任务描述>    # 输出带人设的 prompt

关键约束：角色卡位于 docs/roles/，头部格式为
  > **名字：XXX** | **性别**：X | **灵魂**：XXX [| **口头禅**：XXX]

退出码：0 成功；1 verify 未通过；2 参数错误 / 角色卡缺失。
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

HERE = os.path.dirname(os.path.abspath(__file__))
ROLES_DIR = os.path.join(HERE, "docs", "roles")

# 编号 → 文件名映射
ROLE_FILES = {
    "01": "01-lead.md",
    "02": "02-research.md",
    "03": "03-structure.md",
    "04": "04-writer.md",
    "05": "05-review.md",
    "06": "06-design.md",
    "07": "07-publish.md",
    "08": "08-return.md",
    "09": "09-photo.md",
    "10": "10-creative.md",
}


def extract_persona(content):
    """返回 (名字, 灵魂, 口头禅)，缺失项为 None。"""
    for line in content.splitlines():
        line = line.strip()
        if "名字" not in line or "|" not in line:
            continue
        fields = {}
        for part in line.split("|"):
            m = re.match(r"^>?\s*\*\*([^*：:]+)(?:[：:]\s*\**|\*\*[：:])\s*(.*?)\**\s*$",
                         part.strip())
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
        name = fields.get("名字")
        if name:
            return name, fields.get("灵魂"), fields.get("口头禅")
    return None, None, None


def get_persona(role_id):
    """读取角色卡；失败返回 {"error": ...}。"""
    if role_id not in ROLE_FILES:
        return {"error": "未知编号: %s，有效值: %s"
                % (role_id, sorted(ROLE_FILES.keys()))}
    fpath = os.path.join(ROLES_DIR, ROLE_FILES[role_id])
    if not os.path.exists(fpath):
        return {"error": "角色卡不存在: %s" % fpath}
    content = gzh_cli.read_text(fpath)
    name, soul, catchphrase = extract_persona(content)
    # 提取岗位标题
    title_m = re.search(r"###\s+(.+)", content)
    title = title_m.group(1).strip() if title_m else role_id
    return {"id": role_id, "file": ROLE_FILES[role_id], "title": title,
            "name": name, "soul": soul, "catchphrase": catchphrase}


def inject_prompt(info, task_desc):
    """由角色卡信息装配带人设的 prompt。"""
    head = "你是 %s（%s）。" % (info["name"] or info["title"], info["title"])
    if info["soul"]:
        head += "灵魂：%s。" % info["soul"]
    if info["catchphrase"]:
        head += "口头禅：%s。" % info["catchphrase"]
    return "%s\n\n## 任务\n%s" % (head, task_desc)


def cmd_show(args):
    print("=== <YOUR_BRAND> · 团队人设 ===\n")
    for role_id in sorted(ROLE_FILES.keys()):
        info = get_persona(role_id)
        if "error" in info:
            print("  %s: ⚠️ %s" % (role_id, info["error"]))
            continue
        print("  %s %s（%s）" % (role_id, info["name"], info["title"]))
        if info["soul"]:
            print("          灵魂：%s" % info["soul"])
        if info["catchphrase"]:
            print("          口头禅：%s" % info["catchphrase"])
        print()
    return 0


def cmd_inject(args):
    info = get_persona(args.role)
    if "error" in info:
        print("[错误] %s" % info["error"], file=sys.stderr)
        return 2
    print(inject_prompt(info, " ".join(args.task)))
    return 0


def cmd_verify(args):
    results = []
    for role_id, fname in ROLE_FILES.items():
        fpath = os.path.join(ROLES_DIR, fname)
        content = gzh_cli.read_text(fpath) if os.path.exists(fpath) else ""
        has_name = bool(re.search(r"\*\*名字[：:]", content))
        results.append((role_id, fname, has_name))
    ok = sum(1 for _, _, h in results if h)
    total = len(results)
    print("名字注入验证: %d/%d" % (ok, total))
    for role_id, fname, has_name in results:
        status = "✅" if has_name else "❌"
        print("  %s %s %s" % (status, role_id, fname))
    return 0 if ok == total else 1


def main():
    parser = gzh_cli.build_parser("persona.py", "公众号团队人设注入工具")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="显示全部人设摘要")
    sub.add_parser("verify", help="验证角色卡名字注入状态")
    p = sub.add_parser("inject", help="给任务注入人设")
    p.add_argument("--role", required=True, help="角色编号 (01-10)")
    p.add_argument("task", nargs=argparse.REMAINDER, help="任务描述")
    args = parser.parse_args()
    return {"show": cmd_show, "verify": cmd_verify,
            "inject": cmd_inject}[args.cmd](args)


if __name__ == "__main__":
    gzh_cli.run_main(main)
