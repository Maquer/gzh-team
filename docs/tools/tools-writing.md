---
id: tools-writing
title: "12.1 创作层（主笔职责）"
tokens: 1281
source: "TEAM.md.bak-pre-split"
source_lines: "758-778"
---

### 12.1 创作层（主笔职责）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `bao-kuai-xie-zuo` | Skill | 🔶 | `skills/bao-kuai-xie-zuo/SKILL.md` | 触发词"写文章/写一篇"。11 洞见维度 + 5 标题策略 + 配图 prompt + 叙事动量自检。产出 Markdown 含备选标题 5 个 + 配图指导 + 互动钩子 |
| `humanizer-check.py` | 脚本 | 🔶 | `../humanizer-check/humanizer-check.py` | `python3 humanizer-check.py < 文章.txt`。11 条实证规则（v2，见 REVIEW H14）。≤5 分可发布，6-15 重写 ≥50% 段落，>25 推倒重写 |
| `humanizer-check/checklist.md` | 清单 | — | `../humanizer-check/checklist.md` | 去 AI 味人工清单，配合脚本使用 |

**主笔交付前必做**：写完稿 → 跑 `humanizer-check.py` → 评分 ≤5 才进审核；>5 必须改写。

### 12.2 调研层（信息收集/结构梳理）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `re-souo-ju-he` | Skill | 🔶 | `skills/re-souo-ju-he/SKILL.md` | 热搜聚合：B站+抖音直连 + 微博/知乎浏览器兜底。赛道词过滤出选题 |
| `anysearch` | Skill | 🔶 | `skills/anysearch/SKILL.md` | 统一实时搜索（17 vertical domains），支持 batch + extract。v3.1.1，Apache-2.0 |
| `exa-search` | Skill | 🔶 | `skills/exa-search/SKILL.md` | Exa MCP 搜索 + 网页抓取，filtered web retrieval |
| `web-content-extractor` | Skill | 🔶 | `skills/web-content-extractor/SKILL.md` | 网页正文提取（Defuddle+Jina AI reader），零依赖 |

**调研分工**：`re-souo-ju-he` 找热点选题 → `anysearch`/`exa-search` 搜具体内容 → `web-content-extractor` 提正文。三件配合用，不要单跑一个。

