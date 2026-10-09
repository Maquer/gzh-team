# 公众号写作团队 v3.1.0

> 10 岗图文生产全流程：选题 → 素材 → 结构 → 撰写 → 出图 → 审核 → 排版 → 发布 → 回访
>
> 一套可以直接拿来用的公众号内容团队方法论与工具链：岗位职责与交接契约、门禁规则、角色卡、培训体系，以及配套的门禁脚本、封面/首尾图生成器和排版工具。核心目标：**任一角色都可以被替换成别人或工具，交接不丢信息、责任不糊。**

---

## 快速开始

```bash
git clone https://github.com/Maquer/gzh-team.git
cd gzh-team
pip install -r requirements.txt     # 只需要 Pillow

cat TEAM.md                          # 团队职责手册（入口）
python3 gate-check.py 稿件.md        # 成稿门禁（H1-H10，<200 字 = BLOCK）
python3 gate-G7-check.py 稿件.md --strict --broadcast-ok   # 发布前 12 项清单
python3 persona.py show              # 查看 10 个岗位人设
python3 gate-version-check.py        # 提交前版本号一致性检查
```

所有脚本都支持 `--help`，缺少外部依赖时会给出明确提示而不是报错退出。

---

## 品牌配置

仓库里的品牌信息使用占位符，使用前全局替换为你的账号信息：

```bash
grep -rn "<YOUR_BRAND>\|<YOUR_BRAND_EN>\|＜YOUR_BRAND" .
```

| 位置 | 需要改的内容 |
|------|------|
| `follow-cards.py` | `ACCOUNT = '<YOUR_BRAND>'`、`SLOGAN` |
| `cover-brief.py` / `cover-card.py` / `cover-dynamic.py` / `brand-font-schemes.py` | `BRAND = '<YOUR_BRAND>'` |
| `cover-summary.py` | `"＜YOUR_BRAND＞ · ＜YOUR_BRAND_EN＞"`（注意是 U+FF1C 全角） |
| `cover-new-style.py` / `persona.py` | 搜索 `YOUR_BRAND` 替换 |
| `assets/brand/qr-code.png` | 放入你的公众号二维码（尾图用） |

---

## 运行环境

| 依赖 | 用途 | 缺失时 |
|------|------|------|
| Python 3.8+、Pillow | 全部脚本 | — |
| Noto CJK 字体（`/usr/share/fonts/noto/`） | 封面、首尾图 | 无法出图 |
| `apple-vision` CLI | H11 / H12 / H15 / G7 的 OCR 检查 | 门禁给出 WARN 或「OCR 调用失败」，人工复核 |
| `humanizer-check` | H14 AI 味检测、培训考核 | 提示缺失 |
| `gzh-typeset`（融合版排版引擎） | `gzh-typeset.py` 转发目标 | 提示缺失，exit 2 |
| `company-mode.py` | `training/gzh-dispatch.py` 实际执行 | 提示缺失，可先用 `--dry-run` |

仓库外的共享工具默认放在仓库的**上一级目录**（如 `../humanizer-check/`、`../gzh-typeset/`），也可以用环境变量 `GZH_SHARED_DIR` 指定；`gzh-typeset.py` 还可以用 `GZH_TYPESET_IMPL` 直接指向实现文件。

---

## 工具一览

### 门禁脚本

| 脚本 | 阶段 | 作用 |
|------|------|------|
| `gate-G0-check.py` | 选题 | 对齐不做清单 + 选题判据 |
| `gate-G3-check.py` | 结构 | 节数 / 字数 / 金句 / 素材引用（按模板参数） |
| `gate-check.py` | 成稿 | H1-H10 质量门禁，<200 字 = BLOCK |
| `gate-H11-check.py` | 出图 | 图片中文残留 / 水印关键词（fast 为主，accurate 只兜底水印） |
| `gate-H12-check.py` | 出图 | prompt 元数据、主体描述被画进图 |
| `gate-H14-check.py` | 审核 | AI 味阈值（审核用 `--mode strict`） |
| `gate-H15-check.py` | 排版 | 尾图：导流词 / 违规词 / 高度 ≤800px |
| `gate-G7-check.py` | 发布 | 发布前 12 项清单（含群发开关、账号健康） |
| `gate-G8-check.py` | 发布 | 发布前检查判据 |
| `gate-version-check.py` | 提交 | CHANGELOG / TEAM.md / README 版本号全链一致 |

退出码统一：`0` = 通过，`1` = 不通过，`2` = 输入错误或缺少依赖。

### 视觉

| 脚本 | 作用 |
|------|------|
| `cover-pipeline.py` | 封面一条命令流水线：去水印 → 裁 2.35:1 → 叠标题 → OCR 自检（`--base pil` 或 `--src` AI 底图，`--layout simple/structured`） |
| `cover_styles.py` | 10 种设计师风格 + 5 档调性映射（被 cover-pipeline / cover-recommend 引用） |
| `cover-recommend.py` | 文章 → 调性打分 → 推荐风格 → 给出可执行命令 |
| `cover-card.py` / `cover-brief.py` / `cover-summary.py` / `cover-dynamic.py` / `cover-new-style.py` | 900×383 标题型 / 摘要型 / 动态提取型封面 |
| `follow-cards.py` | 文首关注提醒卡 + 文末引导卡（`--qr` 嵌入二维码，`--check` OCR 校验） |
| `brand-font-schemes.py` | 品牌字体组合 logo、尾图、首图关注横幅 |
| `gzh-brand.py` | 品牌视觉统一入口 |
| `gzh-typeset.py` | Markdown → 微信 HTML（转发到融合版排版引擎） |

### 团队协作

| 脚本 | 作用 |
|------|------|
| `persona.py` | `show` / `verify` / `inject --role 01 任务`：给派发的任务注入岗位人设 |
| `persona-layers.py` | 按层读取画像（`layers` / `show --layer writing` / `inject`），层间不跨读 |
| `turn-reminders.py` | 每轮行为提醒（`show` / `get 审核` / `inject --step writing` / `rotate --turn N`） |
| `component-registry.py` | 工具链变更同步注册表（改了 A 需要同步哪些 B） |
| `archives_optimizer.py` / `archive_note_generator.py` | 工具「归档不装」决策与归档笔记，见 `README_ARCHIVE_OPTIMIZATION.md` |

### 培训（`training/`）

| 脚本 | 作用 |
|------|------|
| `gzh-dispatch.py` | 岗位技能卡 + 任务 → 可执行 prompt（`--dry-run` 只打印） |
| `train-check.py` | 岗位能力考核（可判定指标，不留主观项） |
| `role-patterns.py` | 角色卡增长型 pattern 存储（每类上限 12 条，FIFO） |
| `run-baselines.py` / `gzh-call.py` | 岗位基线实测与模型调用 |

### 文档结构维护

`TEAM.md` 是由冻结源 `TEAM.md.bak-pre-split` 拆分生成的索引，正文分布在 `docs/` 下。以下工具都需要自备冻结源，缺失时提示后以 exit 2 退出：

| 脚本 | 作用 |
|------|------|
| `split.py` | 按 MAP 从冻结源重新生成 `docs/` 与 `TEAM.md` 索引，逐段 sha256 校验 |
| `verify-all.py` | 拆分一致性验证 V1-V6（冻结源未改、幂等、docs 无漂移、索引完整、frontmatter） |
| `link-check.py` | 拆分结构审计 A1-A6（MAP 覆盖、逐字一致、id 唯一、相对链接、manifest、token 预算） |
| `recover.py` | 由拆分产物反向重建冻结源 |

---

## 目录结构

```
gzh-team/
├── TEAM.md                     # 团队职责手册入口（10 岗 + 门禁 + 版本纪律 + 索引）
├── CHANGELOG.md                # 完整变更历史（最新：§30 v3.1.0）
├── PUBLISH-NOTES.md            # 各版本发布说明
├── REVIEW.md                   # 门禁清单（R1-R6 致命 / H1-H15 高频 / 一般规范）
├── VALIDATION.md               # 规则可执行性验证（实测 + 样本对照）
├── BASELINE.md                 # 视觉基线与验证判据
├── SELF-STATEMENT.md           # 岗位第一人称自诉（入职材料）
├── 不做清单.md                 # 选题边界
├── gate-*.py                   # 门禁脚本
├── cover-*.py / follow-cards.py / brand-font-schemes.py   # 视觉生成
├── persona*.py / turn-reminders.py                        # 人设与提醒
├── docs/
│   ├── 00-architecture/        # 总览、组织、交接契约、最小可行配置、文件清单、培训
│   ├── roles/                  # 10 张角色卡
│   ├── rules/                  # 写作规范、质量标准、门禁映射、交接格式、提醒机制
│   ├── tools/                  # 写作 / 设计 / 媒体 / 发布工具清单
│   ├── visual/                 # 品牌色、首图、尾图规范
│   ├── templates/ sop/         # 标题公式、互动钩子库、每日回访 SOP
│   ├── audit/ decision-log/    # 审计报告与决策记录
│   └── reminders/              # 提醒任务台账
├── training/                   # 培训体系：技能卡、基线、考核脚本
├── assets/                     # 素材、风格库、模板索引
├── media/                      # 媒体素材
└── 金句库/                     # 金句素材
```

---

## 开发约定

- 提交前跑 `python3 gate-version-check.py`：CHANGELOG 最新条目 = 唯一可信版本源，TEAM.md 与 README 需同步（规则见 `TEAM.md` §2）
- 代码检查：`pip install pyflakes && python3 -m pyflakes $(git ls-files '*.py')`，当前 0 报错
- 脚本里的路径一律相对仓库目录，不写环境专属的绝对路径

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.3.1 | 2026-09-28 | 首次开源发布：职责手册 + 门禁脚本 + 角色卡 |
| v2.4.0 | 2026-09-28 | 版本纪律 + `gate-version-check.py` |
| v2.5.0 | 2026-09-29 | G7 清单 10 项 → 12 项（群发开关 + 账号健康） |
| v2.5.2 | 2026-09-29 | 周报数据落地 + 归因口径修正 |
| v2.6.0 | 2026-10-02 | 整理 assets + 更新 SOP |
| v3.0.0 | 2026-10-07 | 仓库整理发布 |
| **v3.1.0** | **2026-10-10** | **全量脚本修复（pyflakes 0 报错）+ 路径改为相对仓库 + 文档重写** |

详细内容见 [CHANGELOG.md](CHANGELOG.md) 与 [PUBLISH-NOTES.md](PUBLISH-NOTES.md)。

---

*最后更新：2026-10-10*
*版本：v3.1.0*
