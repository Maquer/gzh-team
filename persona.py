#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
persona.py —— 公众号团队人设注入器

读取 docs/roles/ 9 张角色卡的头部注入段，
在派发 subagent 时自动把名字/灵魂/口头禅追加到 prompt 头部。

用法:
  python3 persona.py inject --role 01 <task_desc>    # 输出带人设的 prompt
  python3 persona.py show                              # 显示全部人设摘要
  python3 persona.py verify                            # 验证 9 个名字都存在
"""
import argparse
import re
import sys
from pathlib import Path

ROLES_DIR = Path("/var/minis/shared/gzh-team/docs/roles")

# 编号 → 文件名映射
ROLE_FILES = {
    "01": "01-lead.md",
    "02": "02-research.md",
    "03": "03-structure.md",
    "04": "04-writer.md",
    "05": "05-review.md",
    "06": "06-design.md",
    "07": "07-publish.md",
    "08": "08-interact.md",
    "09": "09-data.md",
}


def extract_persona(content: str) -> tuple:
    """从角色卡中提取名字/灵魂/口头禅。
    返回 (名字, 灵魂, 口头禅) 或 (None, None, None)。"""
    # 格式：> **名字：XXX** | **灵魂**：XXX | **口头禅**：XXX
    for line in content.splitlines():
        line = line.strip()
        if "名字" not in line or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        name = re.sub(r"^>?\s*\*\*名字[：:]\s*", "", parts[0]).rstrip("*").strip()
        soul = re.sub(r"^\*\*灵魂\*\*[：:]\s*", "", parts[1]).strip()
        catchphrase = re.sub(r"^\*\*口头禅\*\*[：:]\s*", "", parts[2]).strip()
        if name and soul and catchphrase:
            return name, soul, catchphrase
    return None, None, None


def get_persona(role_id: str) -> dict:
    """获取指定角色的完整人设信息。"""
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
    """给任务描述注入人设，返回完整 prompt。"""
    info = get_persona(role_id)
    if "error" in info:
        return f"[错误] {info['error']}\n\n## 任务\n{task_desc}"
    return (f"你是 {info['name']}（{info['title']}）。"
            f"灵魂：{info['soul']}。口头禅：{info['catchphrase']}。\n\n"
            f"## 任务\n{task_desc}")


def cmd_show(args):
    """显示全部人设摘要。"""
    print("=== 弎水野记 · 团队人设 ===\n")
    for role_id in sorted(ROLE_FILES.keys()):
        info = get_persona(role_id)
        if "error" in info:
            print(f"  {role_id}: ⚠️ {info['error']}")
            continue
        print(f"  {role_id} {info['name']}（{info['title']}）")
        print(f"          灵魂：{info['soul']}")
        print(f"          口头禅：{info['catchphrase']}\n")


def cmd_inject(args):
    """注入人设到任务。"""
    prompt = inject_prompt(args.role, args.task)
    print(prompt)


def cmd_verify(args):
    """验证全部 9 个角色卡都有名字。"""
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
    sub.add_parser("verify", help="验证 9 个角色卡名字注入状态")
    
    p = sub.add_parser("inject", help="给任务注入人设")
    p.add_argument("--role", required=True, help="角色编号 (01-09)")
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
