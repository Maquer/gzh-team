---
id: tools-release
title: "12.5 审核层（审核岗职责）"
tokens: 1946
source: "TEAM.md.bak-pre-split"
source_lines: "827-867"
---

### 12.5 审核层（审核岗职责）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `yuwen-publish-precheck` | Skill | ✅ | `skills/yuwen-publish-precheck/scripts/scan.py` | 敏感词/限流词面预检。`python3 scan.py <稿件.md>`。词面扫描，不做语义判断 |
| `gate-check.py` | 脚本 | ✅ | `/var/minis/shared/gzh-team/gate-check.py` | 结构门禁实测。`python3 gate-check.py <稿件.md>`。输出：字数/段落数/超3句明细/禁用词/元话语/标题策略数/AI标注 → PASS 或 FAIL |
| `apple-vision` | CLI | 🔶 | `apple-vision ocr <图> --lang zh-Hans,en` | OCR 检查：H11 中文错字 / H12 元数据入图 / H13 AI 标识 |
| `REVIEW.md` | 清单 | — | `/var/minis/shared/gzh-team/REVIEW.md` | 26 条推荐规范审核清单（R1-R6 致命红线 / H1-H14 高频雷区 / G1-G6 一般规范；编号与 §3 门禁 G1-G8 是两套体系）。每月复查 |

**审核分工**：
- `yuwen-publish-precheck` → **词面预检**（敏感词、限流词、发布前合规扫描）
- `gate-check.py` → **结构门禁**（字数 H8、句数 H9、格式 H10——**不采信模型自报，脚本实测**）
- `apple-vision` → **生图抽检**（H11-H13，即梦/sensenova 出图后跑 OCR）
- `REVIEW.md` → **规范对照**（R1-R6 + H1-H14 + G1-G6，人工逐条勾）

> ⚠️ 实测教训：LLM **不能做精确计数**（字数、句数），但会自信报错误结果——自报 1560 字实为 1131。**精确计数类约束必须脚本实测。**

### 12.6 发布层（发布/负责人职责）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `gongzhonghao-publish` | Skill | 🔶 | `skills/gongzhonghao-publish/SKILL.md` | 创→排→发→推四段式流水线。含爆款写作标准 + 本地排版 + 发布检查 + API 直推 |
| `gzh-api-push.py` | 脚本 | 🔶 | `/var/minis/shared/gzh-api-push.py` | 公众号 Web API 直推草稿箱。需 `WX_APPID` + `WX_APPSECRET` 环境变量。`push`/`get-draft`/`update`/`upload` |
| `apple-reminders` | CLI | 🔶 | `apple-reminders` | 选题排期表存为 Reminders 清单，提醒到点 |

**API 推送 6 个卡点**（大鸭实录）：
1. AppSecret 只显示一次 → 当场复制存环境变量，不截图不传群
2. 40164 = IP 不在白名单 → 去「基本配置 → IP 白名单」添加
3. 48001 = 公众号未认证 → 个人订阅号不行，需先认证
4. CRLF 换行符报错 → 工具自动转换
5. 读草稿必须 POST（GET 报 43002）→ 工具统一 POST
6. 改草稿整篇覆盖 → 必须先 get-draft 读全量，再 update 整篇写回

> ⚠️ 推送草稿箱 ≠ 发布。推完仍需在公众号后台预览确认后再点「发布」。

### 12.7 分发层（读者互动官职责）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `nei-rong-zhuan-hua` | Skill | 🔶 | `skills/nei-rong-zhuan-hua/SKILL.md` | 一鱼多吃：一篇文章自动拆分为 6 个平台专业内容（含小红书配图方案） |

