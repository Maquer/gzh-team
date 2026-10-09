---
id: tools-design
title: "12.3 排版层（排版岗职责）"
tokens: 1654
source: "TEAM.md.bak-pre-split"
source_lines: "779-794,876-893"
---

### 12.3 排版层（排版岗职责）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `gzh-typeset.py` | Python | ✅ | `gzh-typeset.py` | Markdown → HTML 排版。5 主题预设 + 荧光笔 + 首尾模板 + 表格转义 |
| `minis-browser-use` | CLI | ✅ | `minis-browser-use` | 可选：navigate → inject HTML → formatContent() → screenshot 验证（原 gzh-typeset.py 流程） |


### 12.9 角色→工具速查

| 角色 | 工具组合 | 关键操作 |
|------|---------|---------|
| **负责人** | `apple-reminders` + `gongzhonghao-publish` | 排期存 Reminders；选题定稿走 G1 门禁 |
| **信息收集** | `re-souo-ju-he` → `anysearch`/`exa-search` → `web-content-extractor` | 热搜找题 → 搜索找料 → 提取正文 |
| **结构梳理** | 无工具（靠 §3.3 结构模板库） | 5 种模板：教程拆解/观点文/对比测评/复盘/盘点 |
| **主笔** | `bao-kuai-xie-zuo` → `humanizer-check.py` | 写完跑去味检测，≤5 分进审核 |
| **审核** | `yuwen-publish-precheck` + `gate-check.py` + `apple-vision` + `REVIEW.md` | 词面预检 → 结构门禁 → OCR 抽检 → 规范对照 |
| **排版** | `hai-bao-she-ji`(即梦) / `minis-model-use`(sensenova) + `gzh-typeset.py` | 生图 → 排版 → 截图验证 |
| **发布** | `gongzhonghao-publish` + `gzh-api-push.py` | 检查清单 → API 推草稿箱 → 后台确认 |
| **读者互动官** | `nei-rong-zhuan-hua` | 一鱼多吃 6 平台拆分 |

> ✅ 15 个工具 + 7 个文档/配置（§12.1-12.8 共 22 行，逐行验证存在）（09-17）。4 个已实测执行（gate-check.py / yuwen-publish-precheck / hai-bao-she-ji / minis-model-use），9 个已读文档未执行。
> ⚠️ 结构梳理无对应工具——靠模板库是现状，不是遗漏。模板库的 5 种结构覆盖 AI 自媒体 90% 的选题类型。

---

