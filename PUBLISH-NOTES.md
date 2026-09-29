# CHANGELOG · 公众号写作团队 v2.5.1

> 发布说明：2026-09-29 | 仓库：https://github.com/Maquer/gzh-team

---

## v2.5.1 · 2026-09-29 团队净化 + 推送说明

**本次变更**：在 v2.5.0 修复基础上，清理团队文档中的外部硬引用，明确自有资产边界，准备对外发布。

### 🔧 本轮改动

| 类别 | 改动 |
|------|------|
| **文档净化** | 移除直接引用 `/var/minis/shared/` 路径，统一改为 skill 调用 |
| **依赖标注** | `humanizer-check` 标注为共享工具（非团队自有） |
| **版本统一** | TEAM.md / README / CHANGELOG 版本号一致性验证通过 |

### 📦 团队自有资产清单（git tracked）

**门禁脚本（11 个）**：
- `gate-check.py` — 综合门禁（事实/逻辑/读者/合规层）
- `gate-G0-check.py` ~ `gate-G8-check.py` — G 系列流程门禁
- `gate-H11-check.py` ~ `gate-H15-check.py` — H 系列质量门禁
- `gate-G7-check.py` — G7 发布前检查（**v2.5.0 新增群发开关 + 账号健康前置门禁**）
- `gate-version-check.py` — 版本一致性门禁（**v2.4.0 新增，防纸面完成事故**）

**工具脚本（15 个）**：
- `gzh-typeset.py` — 排版引擎（兼容层，实现在 shared/gzh-typeset/）
- `gzh-brand.py` — 品牌色生成
- `cover-*.py` / `follow-cards.py` — 封面/首尾图生成
- `link-check.py` / `verify-all.py` — 链接校验 + 全量验证

**文档资产**：
- `TEAM.md` — 核心职责手册（10 岗 × 12 项 G7 清单）
- `CHANGELOG.md` — 变更记录（§1-§27，含补记的 v2.3/v2.3.1）
- `REVIEW.md` — 门禁清单（R1-R6 致命 / H1-H14 高频 / §3 一般规范）
- `SELF-STATEMENT.md` — 岗位自诉（第一人称入职材料）
- `docs/roles/*.md` — 10 张角色卡
- `docs/发布台账.md` — 公共资产 #11（**v2.5.0 新增，回填 8 篇历史数据**）
- `docs/account-health-label.md` — 账号健康追踪（**v2.5.0 回填三轮误判线**）
- `选题库/README.md` — 选题库占位（**v2.5.0 重建**）

### ⚠️ 外部依赖（共享，非团队自有）

| 工具 | 用途 | 归属 |
|------|------|------|
| `humanizer-check` | AI 味检测（H14） | `/var/minis/shared/` 共享 |
| `gzh-api-tui-song` skill | API 直推草稿箱 | 已封装，不直接引用路径 |
| `gzh-pai-ban` skill | 排版组件 | 已封装 |

### 📝 使用方式

```bash
# 克隆
git clone https://github.com/Maquer/gzh-team.git

# 查看团队手册
cat TEAM.md

# 运行门禁
python3 gate-check.py 稿件.md
python3 gate-G7-check.py 稿件.md --strict --broadcast-ok

# 版本一致性检查
python3 gate-version-check.py
```

---

## v2.5.0 · 2026-09-29 BUG 修复批次

> 详见 [本仓库 CHANGELOG.md](CHANGELOG.md) §27

**核心修复**：
1. G7 清单 10 项 → 12 项（新增群发开关 + 账号健康前置门禁）
2. 发布台账 #11 补建（回填 8 篇历史数据）
3. account-health-label.md 回填 09-21 三轮误判线
4. gzh-api-push.py `--thumb` 支持图片路径自动 upload

---

## v2.4.0 · 2026-09-28 版本纪律

> 详见 CHANGELOG.md §26

**核心修复**：v2.3.1 纸面完成事故 → 新增 §2 版本与变更管理全队纪律 + `gate-version-check.py` 门禁

---

## v2.3.1 · 2026-09-28 脱敏上传

> 详见 docs/README-v2.3.1.md

**核心变更**：删除选题库/复盘档案/会议记录，保留职责手册 + 门禁脚本 + 角色卡

---

*本文档由团队自动生成，最后更新：2026-09-29*
