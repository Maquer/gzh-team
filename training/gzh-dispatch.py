#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
培训体系派发入口 —— 岗位技能卡 + 任务 → 可执行 prompt

为什么独立成脚本而不是改 company-mode.py：
company-mode.py 是 6 个通用后端（coding/writing/research/decision/explain/default），
与公众号团队 8 个岗位不对应；且它是共享基础设施，培训体系不应为此改造它。
本脚本自建装配层：任务 → 规划 → 注入技能卡 → 交给指定后端执行。

用法:
  python3 gzh-dispatch.py "写公众号正文" --role-card 02-主笔 --dry-run
  python3 gzh-dispatch.py "写公众号正文" --role-card 02-主笔 --backend writing
"""
import sys, json, re, argparse, subprocess
from pathlib import Path

SKILL_CARD_DIR = Path("/var/minis/shared/gzh-team/training/skills")
# v1.6 (2026-09-20)：编号对齐 docs/roles。见 training/MAPPING.md。
GZH_ROLE_CARDS = {
    "01-负责人": "01-负责人.md",
    "02-选题规划师": "02-选题规划师.md",
    "03-结构梳理": "03-结构梳理.md",
    "04-主笔": "04-主笔.md",
    "05-审核": "05-审核.md",
    "06-排版": "06-排版.md",
    "07-发布": "07-发布.md",
    "08-读者互动官": "08-读者互动官.md",
    "09-数据分析师": "09-数据分析师.md",
}
# 岗位 → 后端映射（company-mode.py 的 6 个后端里没有"审核"这类岗位，
# 所以映射是近似值，已在 TRAINING.md 标注）
ROLE_BACKEND = {
    "01-负责人": "decision", "02-选题规划师": "research", "03-结构梳理": "decision",
    "04-主笔": "writing", "05-审核": "decision", "06-排版": "coding",
    "07-发布": "coding", "08-读者互动官": "writing", "09-数据分析师": "research",
}


def load_skill_card(role_name):
    """加载技能卡全文；找不到返回 (None, 原因)"""
    fname = GZH_ROLE_CARDS.get(role_name)
    if not fname:
        return None, "未知岗位: %s" % role_name
    p = SKILL_CARD_DIR / fname
    if not p.exists():
        return None, "技能卡不存在: %s" % p
    t = p.read_text(encoding="utf-8").strip()
    return (t, None) if t else (None, "技能卡为空: %s" % p)


def load_playbook(task_type):
    """从 .playbooks.json 找匹配 playbook；文件缺失返回 None"""
    pf = Path("/var/minis/shared/.playbooks.json")
    if not pf.exists():
        return None
    try:
        d = json.loads(pf.read_text(encoding="utf-8"))
        for pb in (d if isinstance(d, list) else d.get("playbooks", [])):
            if isinstance(pb, dict) and task_type in pb.get("type", ""):
                return pb.get("content") or pb.get("text")
    except Exception:
        return None
    return None


def build_prompt(task_desc, role_card=None):
    """装配 prompt：任务 + 岗位角色 + 历史经验 + 技能卡"""
    task_type = "内容创作" if role_card else "通用"
    parts = ["## 任务\n%s\n" % task_desc,
             "\n## 任务类型\n%s\n" % task_type]
    pb = load_playbook(task_type)
    if pb:
        parts.append("\n## 相关 Playbook\n%s" % pb)
    if role_card:
        txt, err = load_skill_card(role_card)
        if err:
            print("  ⚠️  %s（跳过注入，不影响执行）" % err)
        else:
            parts.append("\n## 岗位技能卡（培训体系，必须遵守）\n%s\n" % txt)
    return "".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="任务描述")
    ap.add_argument("--role-card", dest="role_card", default=None,
                    help="岗位技能卡 (01-选题规划师 ... 08-数据分析师)")
    ap.add_argument("--backend", default=None, help="后端 (默认按岗位映射)")
    ap.add_argument("--dry-run", action="store_true", help="只打印 prompt 不执行")
    args = ap.parse_args()

    backend = args.backend or (ROLE_BACKEND.get(args.role_card, "writing")
                               if args.role_card else "writing")
    prompt = build_prompt(args.task, args.role_card)

    if args.dry_run:
        print("=" * 60)
        print("后端: %s | 技能卡: %s" % (backend, args.role_card or "无"))
        print("=" * 60)
        print(prompt)
        return 0

    cmd = ["python3", "/var/minis/shared/company-mode.py", "run", args.task,
           "--backend", backend]
    print("（装配完成，执行交给 company-mode.py；技能卡已写入 prompt）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
