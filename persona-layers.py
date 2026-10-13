#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""persona-layers.py：画像分层读取工具（层间不跨读）。

v4.0.0 重建：干净重写，逻辑与 v3.3.0 一致。
用法：
  python3 persona-layers.py layers                          # 列出所有层
  python3 persona-layers.py show --layer writing             # 显示层画像
  python3 persona-layers.py inject --layer writing --text <任务> [--topic <主题>]

关键约束：需指定层名，不跨层读取。

退出码：0 成功；2 参数错误 / 未知层 / 角色卡缺失。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

HERE = os.path.dirname(os.path.abspath(__file__))
ROLES_DIR = os.path.join(HERE, "docs", "roles")

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

_persona_mod = None


def _persona():
    """惰性加载 persona.py 的头部解析（避免 import 即执行）。"""
    global _persona_mod
    if _persona_mod is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "persona", os.path.join(HERE, "persona.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _persona_mod = mod
    return _persona_mod


def load_role(fname):
    fpath = os.path.join(ROLES_DIR, fname)
    if not os.path.exists(fpath):
        return None
    text = gzh_cli.read_text(fpath)
    name, soul, catchphrase = _persona().extract_persona(text)
    # 提取定位段（role card 的**定位**段）
    m = re.search(r'\*\*定位[：:]\s*(.+?)(?:\n\n|\*\*)', text, re.DOTALL)
    positioning = m.group(1).strip() if m else ""
    return {
        "file": fname,
        "name": name,
        "soul": soul,
        "catchphrase": catchphrase,
        "positioning": positioning,
    }


def get_layer_roles(layer):
    """返回该层全部角色卡；未知层返回空列表（层间不跨读）。"""
    return [r for r in (load_role(f) for f in LAYER_MAP.get(layer, [])) if r]


def cmd_layers(args):
    for key, files in LAYER_MAP.items():
        print("%-10s %s：%s" % (key, LAYER_NAMES.get(key, key), ", ".join(files)))
    return 0


def cmd_show(args):
    layer = args.layer
    roles = get_layer_roles(layer)
    if not roles:
        print("❌ 未知层: %s，可用: %s" % (layer, ", ".join(LAYER_MAP.keys())),
              file=sys.stderr)
        return 2
    print("=== %s ===\n" % LAYER_NAMES.get(layer, layer))
    for r in roles:
        print("--- %s ---" % r["file"])
        if r["name"]:
            print("  名字: %s" % r["name"])
        if r["soul"]:
            print("  灵魂: %s" % r["soul"])
        if r["catchphrase"]:
            print("  口头禅: %s" % r["catchphrase"])
        if r["positioning"]:
            print("  定位: %s..." % r["positioning"][:100])
        print()
    return 0


def cmd_inject(args):
    layer = args.layer
    roles = get_layer_roles(layer)
    if not roles:
        print("❌ 未知层: %s，可用: %s" % (layer, ", ".join(LAYER_MAP.keys())),
              file=sys.stderr)
        return 2

    # 构建画像注入段
    segments = []
    for r in roles:
        seg = "你是%s（%s）" % (r["name"] or r["file"].split(".")[0],
                              LAYER_NAMES.get(layer, layer))
        if r["soul"]:
            seg += "，灵魂：%s" % r["soul"]
        if r["catchphrase"]:
            seg += "，口头禅：%s" % r["catchphrase"]
        segments.append(seg)

    prompt = "\n".join(segments)

    task_text = args.text or ""
    if task_text:
        prompt += "\n\n## 任务\n%s" % task_text

    topic_text = (args.topic or "").strip()
    if topic_text:
        prompt += ("\n\n---\n"
                   "当前任务：%s\n"
                   "请基于以上角色定位，完成当前任务。" % topic_text)

    print(prompt)
    return 0


def main():
    parser = gzh_cli.build_parser("persona-layers.py", "画像分层读取（层间不跨读）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("layers", help="列出所有层")

    p_show = sub.add_parser("show", help="显示层画像")
    p_show.add_argument("--layer", required=True, help="层名")

    p_inj = sub.add_parser("inject", help="注入层画像+任务")
    p_inj.add_argument("--layer", required=True, help="层名")
    p_inj.add_argument("--text", default=None, help="任务描述")
    p_inj.add_argument("--topic", default=None, help="当前任务主题（追加到画像之后）")

    args = parser.parse_args()
    return {"layers": cmd_layers, "show": cmd_show,
            "inject": cmd_inject}[args.cmd](args)


if __name__ == "__main__":
    gzh_cli.run_main(main)
