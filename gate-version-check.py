#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate-version-check.py — 版本与变更管理门禁（TEAM.md §2 执行载体）

校验两件事：
  1. 版本号一致性：CHANGELOG 最新条目 = TEAM.md frontmatter = TEAM.md 头部行
     = README 标题 = README 版本历史表最新行 = README 尾注
  2. CHANGELOG 最新条目四要素齐全：触发 / 决策(变更内容) / 修改文件 / 影响面

退出码：0 全绿 / 1 红灯（阻断提交）
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
VER = r"v?(\d+\.\d+(?:\.\d+)?)"

def read(name):
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()

def find(pattern, text, group=1, last=False):
    if not text:
        return None
    ms = re.findall(pattern, text, flags=re.M)
    if not ms:
        return None
    return ms[-1] if last else ms[0]

results = []

def check(label, value, expect):
    ok = value is not None and value == expect
    results.append((ok, label, value if value is not None else "缺失"))
    return ok

# ---- CHANGELOG 最新条目 = SSOT ----
chlog = read("CHANGELOG.md")
heads = re.findall(r"^## .*", chlog or "", flags=re.M)
ssot = None
entry_body = ""
if heads:
    last = heads[-1]
    m = re.search(VER, last)
    ssot = m.group(1) if m else None
    idx = chlog.rfind(last)
    entry_body = chlog[idx:]
    results.append((ssot is not None, "CHANGELOG 最新条目含版本号", last))
    for kw, desc in [("触发", "触发"), ("修改文件", "修改文件"),
                     ("影响面", "影响面")]:
        results.append((("**" + kw) in entry_body, "条目四要素: " + desc,
                        "✅" if ("**" + kw) in entry_body else "❌ 缺 **%s**" % kw))
    decided = any(("**" + k) in entry_body for k in ["决策", "变更内容", "最终裁定"])
    results.append((decided, "条目四要素: 决策/变更内容",
                    "✅" if decided else "❌ 缺 **决策** 或 **变更内容**"))
else:
    results.append((False, "CHANGELOG 无任何条目", "❌"))

# ---- 各处版本号 ----
team = read("TEAM.md")
team_ver = find(r'^version:\s*"([^"]+)"', team)
team_hdr = find(r"^>\s*v" + VER, team)

rd = read("README.md")
rd_title = find(r"^#\s+公众号写作团队\s+v" + VER, rd)
rd_table = find(r"^\|\s*\*{0,2}v" + VER + r"\*{0,2}\s*\|", rd, last=True)
rd_foot = find(r"\*版本：v" + VER + r"\*", rd)

if ssot:
    check("TEAM.md frontmatter version", team_ver, ssot)
    check("TEAM.md 头部行 > vX.Y.Z", team_hdr, ssot)
    check("README 标题", rd_title, ssot)
    check("README 版本历史表最新行", rd_table, ssot)
    check("README 尾注", rd_foot, ssot)
else:
    results.append((False, "无法确定 SSOT 版本，跳过比对", "❌"))

fails = [r for r in results if not r[0]]
for ok, label, val in results:
    print("%s %s: %s" % ("✅" if ok else "🔴", label, val))
print("---")
if fails:
    print("FAIL: %d 项不通过。SSOT=CHANGELOG 最新版本 %s" % (len(fails), ssot))
    print("按 TEAM.md §2 提交前五步：补 CHANGELOG 条目 / 同步三处版本号后重跑。")
    sys.exit(1)
print("PASS: 版本号全链一致 = v%s，最新条目四要素齐全。" % ssot)
