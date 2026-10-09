# 发布说明 · 公众号写作团队 v3.1.0

> 最后更新：2026-10-10 | 仓库：https://github.com/Maquer/gzh-team

---

## v3.1.0 · 2026-10-10 全量脚本修复 + 文档重写

**本次变更**：修复 v3.0.0 整理时被破坏的脚本，并按修复结果重写仓库说明。详见 [CHANGELOG.md](CHANGELOG.md) §30。

### 🔧 修复

| 类别 | 改动 |
|------|------|
| **被注释 / 错位的代码** | `split.py` `recover.py` `persona.py` `turn-reminders.py` `cover_styles.py` 等恢复可运行；多处「函数头与函数体错位」已拆回正确的函数 |
| **缺失函数与 import** | 补回 `check_ocr` / `check_ocr_dual` / `check_image`（H11/H12）、`check_dimensions` / `check_prohibited_text`（H15）、`make_radial_gradient` / `check_text_dual` / `in_excl_zone`（cover-pipeline）、`tw` / `wrap`（follow-cards）、`make_follow_cover`（brand-font-schemes）、归档工具的加载/分类/决策逻辑 |
| **逻辑 bug** | cover-pipeline 标题区豁免：OCR 归一化坐标与像素坐标混比；gzh-dispatch 组装命令从未执行；train-check 紧迫诱导词算了不判；H11 提示阈值与代码不一致 |
| **路径** | 环境专属绝对路径全部改为相对仓库；共享工具用 `GZH_SHARED_DIR` 指定 |
| **说明更正** | `link-check.py` = 拆分结构审计、`verify-all.py` = 拆分一致性验证（原说明写成外链检查 / H11-H13 合规） |
| **代码检查** | pyflakes 由 149 处未定义名称降到 0 报错 |

### 📦 删除

- `desensitize-v1.py`：一次性内容清理脚本，已无用途且会直接覆写文件
- `docs/README-v2.3.1.md`：过时的仓库说明，内容并入新 README

### 📝 使用方式

见 [README.md](README.md)「快速开始」。

---

## v2.5.1 · 2026-09-29 团队净化 + 推送说明

**本次变更**：在 v2.5.0 修复基础上，清理团队文档中的外部硬引用，明确自有资产边界，准备对外发布。

### 🔧 本轮改动

| 类别 | 改动 |
|------|------|
| **文档净化** | 移除直接引用 `../` 路径，统一改为 skill 调用 |
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
- `gzh-typeset.py` — 排版引擎（兼容层，实现在 ../gzh-typeset/）
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
| `humanizer-check` | AI 味检测（H14） | `../` 共享 |
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

## v2.3.1 · 2026-09-28 首次开源发布

**核心变更**：公开职责手册 + 门禁脚本 + 角色卡；选题库、复盘档案、会议记录等团队内部资料不在仓库内

---

*最后更新：2026-10-10*
