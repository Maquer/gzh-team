# 公众号写作团队 · 开源脱敏版

> 10 岗图文生产全流程：选题 → 素材 → 结构 → 撰写 → 审核 → 排版 → 发布 → 回访
> 📚 **开源脱敏版**：已移除所有项目内容（具体选题、文章、账号数据、图片），仅保留团队核心能力（工具代码、SOP、方法论、门禁规则、模板）。

---

## ⚙️ 使用方式

**Fork 后必做**：全局搜索替换占位符为你的账号信息：

```bash
# 替换品牌名
grep -r "<YOUR_BRAND>" .   # 定位所有需要改的地方
grep -r "<YOUR_BRAND_EN>" .
```

**代码里的品牌常量**（需要手动改）：
- `follow-cards.py`：`ACCOUNT = '<YOUR_BRAND>'`
- `cover-brief.py` / `cover-card.py` / `cover-dynamic.py` / `brand-font-schemes.py`：`BRAND = '<YOUR_BRAND>'`
- `cover-summary.py`：`"＜YOUR_BRAND＞ · ＜YOUR_BRAND_EN＞"`（注意是 U+FF1C 全角）
- `persona.py`、`cover-new-style.py` 等：搜索 `YOUR_BRAND` 替换

---

## 📁 保留资产

```
├── TEAM.md                    # 10 岗架构 + G7 12 项清单（最终版 v2.6.0）
├── CHANGELOG.md               # §1-§29 完整变更历史
├── gate-*.py                  # 11 个门禁脚本
├── docs/
│   ├── roles/                 # 10 张角色卡
│   ├── 发布台账.md            # 8+ 篇历史数据
│   └── account-health-label.md  # 三轮误判线
├── 选题库/
│   └── v2.5.2自审复盘-正文.md  # 最后一篇定稿文章
└── training/                  # 培训框架
```

---

## 相关 Skill（仍可用）

- [`gzh-team-perspective`](/var/minis/skills/gzh-team-perspective/SKILL.md) — 7 心智模型 + 8 启发式，用于流程治理视角评审

---

*最后更新：2026-10-02 · 版本 v2.6.0 · 废弃状态*
*版本：v2.6.0*
