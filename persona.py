#!/usr/bin/env python3
"""
persona.py：团队画像管理工具（角色卡加载/注入）
用法：
  python3 persona.py show                          # 显示全部人设摘要
  python3 persona.py verify                        # 验证每张角色卡都有名字
  python3 persona.py inject --role 01 <任务描述>    # 输出带人设的 prompt
关键约束：角色卡位于 docs/roles/，头部格式为
  > **名字：XXX** | **性别**：X | **灵魂**：XXX [| **口头禅**：XXX]
"""
import argparse
import re
import sys
from pathlib import Path

ROLES_DIR = Path(__file__).resolve().parent / "docs" / "roles"

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


def extract_persona(content: str) -> tuple:
    """返回 (名字, 灵魂, 口头禅)，缺失项为 None。"""
    for line in content.splitlines():
        line = line.strip()
        if "名字" not in line or "|" not in line:
            continue
        fields = {}
        for part in line.split("|"):
            m = re.match(r"^>?\s*\*\*([^*：:]+)(?:[：:]\s*\**|\*\*[：:])\s*(.*?)\**\s*$", part.strip())
            if m:
                fields[m.group(1).strip()] = m.group(2).strip()
        name = fields.get("名字")
        if name:
            return name, fields.get("灵魂"), fields.get("口头禅")
    return None, None, None


def get_persona(role_id: str) -> dict:
    if role_id not in ROLE_FILES:
        return {"error": f"未知编号: {role_id}，有效值: {list(ROLE_FILES.keys())}"}
    fpath = ROLES_DIR / ROLE_FILES[role_id]
    if not fpath.exists():
        return {"error": f"角色卡不存在: {fpath}"}
    content = fpath.read_text(encoding="utf-8")
    name, soul, catchphrase = extract_persona(content)
    # 提取岗位标题
    title_m = re.search(r"###\s+(.+)", content)
    title = title_m.group(1).strip() if title_m else role_id
    return {"id": role_id, "file": fpath.name, "title": title,
            "name": name, "soul": soul, "catchphrase": catchphrase}


def inject_prompt(role_id: str, task_desc: str) -> str:
    info = get_persona(role_id)
    if "error" in info:
        return f"[错误] {info['error']}\n\n## 任务\n{task_desc}"
    head = f"你是 {info['name'] or info['title']}（{info['title']}）。"
    if info["soul"]:
        head += f"灵魂：{info['soul']}。"
    if info["catchphrase"]:
        head += f"口头禅：{info['catchphrase']}。"
    return f"{head}\n\n## 任务\n{task_desc}"


def cmd_show(args):
    print("=== <YOUR_BRAND> · 团队人设 ===\n")
    for role_id in sorted(ROLE_FILES.keys()):
        info = get_persona(role_id)
        if "error" in info:
            print(f"  {role_id}: ⚠️ {info['error']}")
            continue
        print(f"  {role_id} {info['name']}（{info['title']}）")
        if info["soul"]:
            print(f"          灵魂：{info['soul']}")
        if info["catchphrase"]:
            print(f"          口头禅：{info['catchphrase']}")
        print()


def cmd_inject(args):
    print(inject_prompt(args.role, " ".join(args.task)))


def cmd_verify(args):
    results = []
    for role_id, fname in ROLE_FILES.items():
        fpath = ROLES_DIR / fname
        content = fpath.read_text(encoding="utf-8") if fpath.exists() else ""
        has_name = bool(re.search(r"\*\*名字[：:]", content))
        results.append((role_id, fname, has_name))
    ok = sum(1 for _, _, h in results if h)
    total = len(results)
    print(f"名字注入验证: {ok}/{total}")
    for role_id, fname, has_name in results:
        status = "✅" if has_name else "❌"
        print(f"  {status} {role_id} {fname}")
    return 0 if ok == total else 1


def main():
    ap = argparse.ArgumentParser(description="公众号团队人设注入工具")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("show", help="显示全部人设摘要")
    sub.add_parser("verify", help="验证角色卡名字注入状态")
    p = sub.add_parser("inject", help="给任务注入人设")
    p.add_argument("--role", required=True, help="角色编号 (01-10)")
    p.add_argument("task", nargs=argparse.REMAINDER, help="任务描述")
    args = ap.parse_args()
    if args.cmd == "show":
        cmd_show(args)
    elif args.cmd == "verify":
        sys.exit(cmd_verify(args))
    elif args.cmd == "inject":
        cmd_inject(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
