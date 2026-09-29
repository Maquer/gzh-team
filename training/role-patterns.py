#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
role-patterns.py —— 公众号团队角色卡的增长型 pattern 存储

设计依据（ProfSynapse 借鉴，机制自实现）：
  1. pattern 长进角色卡文件本身 → gzh-dispatch.py 逐字注入卡片，自动带出，派发链路零改动
  2. 每角色两张卡：成功模式 / 失败模式（ProfSynapse 的 Effective / Anti-Patterns）
  3. agent-tagged memory 的"agent"维度 = role 维度 → recall 可按角色过滤，不被其他角色噪声稀释

用法:
  python3 role-patterns.py add --role 02-主笔 --type effective --text "标题必须有正文支撑，无支撑被判 R5"
  python3 role-patterns.py add --role 02-主笔 --type anti --text "只写带策略名不写括号分隔符，门禁数到 0"
  python3 role-patterns.py list --role 02-主笔
  python3 role-patterns.py list --all
  python3 role-patterns.py recall --query "标题策略"
  python3 role-patterns.py recall --query "AI味" --role 02-主笔
  python3 role-patterns.py prune --days 90

pattern 条目格式: - [YYYY-MM-DD] 内容
上限: 每角色每类 12 条，超了 FIFO 淘汰最旧
去重: 归一化（strip+去标点空白）后完全相同则跳过
"""
import sys, re, argparse, json
from pathlib import Path
from datetime import datetime, timedelta

CARD_DIR = Path("/var/minis/shared/gzh-team/training/skills")
ROLES = ["01-选题规划师", "02-主笔", "03-审核", "04-排版",
         "05-发布", "06-负责人", "07-读者互动官", "08-数据分析师"]
ROLE_FILES = {r: CARD_DIR / (r + ".md") for r in ROLES}
MAX_PER_SECTION = 12
PATTERN_LINE = re.compile(r'^- \[(\d{4}-\d{2}-\d{2})\] (.+)$')


def section_bounds(text, heading):
    """找 heading 段：返回 (start_idx_of_first_line, end_idx_of_last_line, 或 None)。
    段 = 从该 heading 行起，到下一个 ## 开头行或文件尾。"""
    lines = text.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == heading:
            start = i
            break
    if start is None:
        return None
    end = len(lines) - 1
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j - 1
            break
    return (start, end, lines)


def norm(s):
    """归一化用于去重：去首尾空白，删所有非文字字符"""
    return re.sub(r'[^\w\u4e00-\u9fff]+', '', s)


def collapse_blanks(lines):
    """合并连续空行（最多保留 1 行）"""
    out = []
    for ln in lines:
        if not ln.strip() and out and not out[-1].strip():
            continue
        out.append(ln)
    return out


def cmd_add(args):
    p = ROLE_FILES[args.role]
    if not p.exists():
        print("❌ 角色卡不存在: %s" % p, file=sys.stderr)
        return 1
    txt = p.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")
    entry = "- [%s] %s" % (today, args.text.strip())
    heading = "## 成功模式" if args.type == "effective" else "## 失败模式"

    b = section_bounds(txt, heading)
    if b is None:
        print("❌ %s 缺「%s」段，先跑 init 子命令" % (args.role, heading), file=sys.stderr)
        return 1
    _, end, lines = b

    # 去重
    for ln in lines:
        m = PATTERN_LINE.match(ln)
        if m and norm(m.group(2)) == norm(args.text):
            print("⏭️  已存在（去重跳过）: %s" % args.text[:40])
            return 0

    # 写入：段尾插新条目（段内空行占位符删掉）
    insert_at = end
    for k in range(end, start_i(lines, heading), -1):
        if lines[k].strip() == "（空）":
            lines[k] = ""
            break
    lines.insert(insert_at + 1, entry)
    # 上限淘汰
    pat_idx = [i for i, ln in enumerate(lines) if PATTERN_LINE.match(ln)]
    while len(pat_idx) > MAX_PER_SECTION:
        oldest = pat_idx[0]
        removed = lines.pop(oldest)
        print("♻️  淘汰最旧: %s" % removed[:50])
        pat_idx = [i for i, ln in enumerate(lines) if PATTERN_LINE.match(ln)]

    # 写入前合并多余空行
    lines = collapse_blanks(lines)
    p.write_text("\n".join(lines), encoding="utf-8")
    print("✅ 已追加到 %s / %s（%s）" % (args.role, heading, today))
    return 0


def start_i(lines, heading):
    for i, ln in enumerate(lines):
        if ln.strip() == heading:
            return i
    return 0


def cmd_list(args):
    for role in (ROLES if args.all else [args.role]):
        p = ROLE_FILES[role]
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        pats = []
        for h, label in (("## 成功模式", "🟢"), ("## 失败模式", "🔴")):
            b = section_bounds(txt, h)
            if not b:
                continue
            _, end, lines = b
            for ln in lines[start_i(lines, h):end + 1]:
                m = PATTERN_LINE.match(ln)
                if m:
                    pats.append((role, label, m.group(1), m.group(2)))
        if not pats and not args.all:
            print("（%s 无 pattern）" % role)
        for role2, label, dt, content in pats:
            if args.all:
                print("%s %s [%s] %s" % (role2, label, dt, content))
            else:
                print("%s [%s] %s" % (label, dt, content))
    return 0


def cmd_recall(args):
    """跨角色关键词召回（agent-tagged memory 的查询路径）
    多词匹配：任一关键词命中即入选，命中数多的排前"""
    kws = [k.strip() for k in args.query.split() if k.strip()]
    if not kws:
        print("❌ --query 为空", file=sys.stderr)
        return 1
    hits = []
    for role in ROLES:
        if args.role and role != args.role:
            continue
        p = ROLE_FILES[role]
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        for h, label in (("## 成功模式", "🟢"), ("## 失败模式", "🔴")):
            b = section_bounds(txt, h)
            if not b:
                continue
            _, end, lines = b
            for ln in lines[start_i(lines, h):end + 1]:
                m = PATTERN_LINE.match(ln)
                if not m:
                    continue
                score = sum(1 for k in kws if k in m.group(2))
                if score > 0:
                    hits.append((score, role, label, m.group(1), m.group(2)))
    hits.sort(key=lambda x: (-x[0], x[3]))
    if not hits:
        print("（无命中：%s）" % " ".join(kws))
        return 0
    print("命中 %d 条（关键词: %s）" % (len(hits), " ".join(kws)))
    for score, role, label, dt, content in hits:
        print("  %s [%s] %s [%s] %s" % (label, role, dt, score, content))
    return 0


def cmd_prune(args):
    cutoff = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    removed = 0
    for role in ROLES:
        p = ROLE_FILES[role]
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        lines = txt.split("\n")
        keep = []
        for ln in lines:
            m = PATTERN_LINE.match(ln)
            if m and m.group(1) < cutoff:
                removed += 1
                continue
            keep.append(ln)
        if removed:
            p.write_text("\n".join(keep), encoding="utf-8")
    print("♻️  淘汰 %d 条（早于 %s）" % (removed, cutoff))
    return 0


def cmd_init(args):
    """给缺段的角色卡补两个 pattern 段（幂等）"""
    for role in ROLES:
        p = ROLE_FILES[role]
        if not p.exists():
            print("⚠️  跳过（文件不存在）: %s" % p)
            continue
        txt = p.read_text(encoding="utf-8")
        add = []
        for h in ("## 成功模式", "## 失败模式"):
            if section_bounds(txt, h) is None:
                add.append("\n%s\n（空）" % h)
        if not add:
            print("✅ %s 已有两个段" % role)
            continue
        tail = "\n".join(add)
        txt = txt.rstrip("\n") + "\n" + tail + "\n"
        p.write_text(txt, encoding="utf-8")
        print("➕ %s 补了 %d 个段" % (role, len(add)))
    return 0


def main():
    ap = argparse.ArgumentParser(description="公众号团队角色卡 pattern 管理")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add", help="追加一条 pattern")
    s.add_argument("--role", required=True, choices=ROLES)
    s.add_argument("--type", required=True, choices=["effective", "anti"])
    s.add_argument("--text", required=True)
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("list", help="查看 pattern")
    s.add_argument("--role", choices=ROLES)
    s.add_argument("--all", action="store_true")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("recall", help="跨角色关键词召回")
    s.add_argument("--query", required=True)
    s.add_argument("--role", choices=ROLES)
    s.set_defaults(func=cmd_recall)

    s = sub.add_parser("prune", help="淘汰旧 pattern")
    s.add_argument("--days", type=int, default=90)
    s.set_defaults(func=cmd_prune)

    s = sub.add_parser("init", help="初始化角色卡的 pattern 段")
    s.set_defaults(func=cmd_init)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
