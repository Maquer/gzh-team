#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
persona-layers.py：画像分层读取工具（层间不跨读）
用法：python3 persona-layers.py <参数>
关键约束：需指定层名，不跨层读取
"""
import sys, re
from pathlib import Path

ROLES_DIR = Path("/var/minis/shared/gzh-team/docs/roles")

# 层→角色映射（角色文件名）
LAYER_MAP = {
    "strategy":  ["01-lead.md", "02-research.md"],
    "writing":   ["03-structure.md", "04-writer.md"],
    "review":    ["05-review.md"],
    "design":    ["06-design.md"],
    "publish":   ["07-publish.md", "08-return.md"],
    "data":      ["09-photo.md"],
    "creative":  ["10-creative.md"],
}

# 层名称中文映射
LAYER_NAMES = {
    "strategy":  "策略层（负责人+选题）",
    "writing":   "写作层（结构+主笔）",
    "review":    "审核层",
    "design":    "视觉层",
    "publish":   "发布层（发布+互动）",
    "data":      "数据层",
    "creative":  "创意层",
}


def parse_frontmatter(text):
    fpath = ROLES_DIR / fname
    if not fpath.exists():
        return None
    text = fpath.read_text(encoding="utf-8")
    name, soul, catchphrase = parse_frontmatter(text)
    # 提取定位段（role card 的**定位**段）
    m = re.search(r'\*\*定位[：:]\s*(.+?)(?:\n\n|\*\*)', text, re.DOTALL)
    positioning = m.group(1).strip() if m else ""
    return {
        "file": fname,
        "name": name,
        "soul": soul,
        "catchphrase": catchphrase,
        "positioning": positioning,
        "full_text": text,
    }


def get_layer_roles(layer):
    roles = get_layer_roles(layer)
    if not roles:
        print(f"❌ 未知层: {layer}，可用: {', '.join(LAYER_MAP.keys())}")
        sys.exit(1)
    print(f"=== {LAYER_NAMES.get(layer, layer)} ===\n")
    for r in roles:
        print(f"--- {r['file']} ---")
        if r['name']:
            print(f"  名字: {r['name']}")
        if r['soul']:
            print(f"  灵魂: {r['soul']}")
        if r['catchphrase']:
            print(f"  口头禅: {r['catchphrase']}")
        if r['positioning']:
            print(f"  定位: {r['positioning'][:100]}...")
        print()


def cmd_inject(layer, text, task=None, topic=None):
    roles = get_layer_roles(layer)
    if not roles:
        print(f"❌ 未知层: {layer}，可用: {', '.join(LAYER_MAP.keys())}")
        sys.exit(1)
    
    # 构建画像注入段
    segments = []
    for r in roles:
        seg = f"你是{r['name'] or r['file'].split('.')[0]}（{LAYER_NAMES.get(layer, layer)}）"
        if r['soul']:
            seg += f"，灵魂：{r['soul']}"
        if r['catchphrase']:
            seg += f"，口头禅：{r['catchphrase']}"
        segments.append(seg)
    
    prompt = "\n".join(segments)
    
    task_text = text or task or ""
    if task_text:
        prompt += f"\n\n## 任务\n{task_text}"

    topic_text = (topic or "").strip()
    if topic_text:
        prompt += (
            "\n\n---\n"
            f"当前任务：{topic_text}\n"
            "请基于以上角色定位，完成当前任务。"
        )

    print(prompt)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="画像分层读取")
    sub = ap.add_subparsers(dest="cmd")
    
    sub.add_parser("layers", help="列出所有层")
    
    p_show = sub.add_parser("show", help="显示层画像")
    p_show.add_argument("--layer", required=True)
    
    p_inj = sub.add_parser("inject", help="注入层画像+任务")
    p_inj.add_argument("--layer", required=True)
    p_inj.add_argument("--text", default=None, help="任务描述")
    p_inj.add_argument("--topic", default=None, help="当前任务主题（追加到画像之后）")
    
    args = ap.parse_args()
    if args.cmd == "layers":
        cmd_layers()
    elif args.cmd == "show":
        cmd_show(args.layer)
    elif args.cmd == "inject":
        cmd_inject(args.layer, args.text, topic=args.topic)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
