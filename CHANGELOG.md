

## 35. v4.1.1：门禁冲突修复（2026-10-16）

**根因**：v4.1.0 角色卡/培训卡滞后于 gate-check.py 变更，导致门禁判定与岗位要求不一致

**P0 修复**：
- H14 默认降级为 solo 模式（只给参考分数，不卡关），与角色卡"仅供参考不卡关"对齐；strict 需显式 `--h14-strict`
- 金句密度：WARN → BLOCK（与 G7 发布前清单对齐）
- 互动钩子 EX3：WARN → BLOCK（与 G7 发布前清单对齐）

**P1 修复**：
- EX1-EX5 全部升级为 BLOCK（与角色卡"必填"对齐）
- 新增 EX6：标题字数检查（15-30字，G7 BLOCK 项）
- 新增 EX7：防盗链检查（HTML `<img>` 必须有 `referrerpolicy`，G7 BLOCK 项）

**角色卡同步**：
- 03-structure：补充 G3 结构门禁培训
- 04-writer：H14 solo 说明 + G8/EX1-EX6 检查说明
- 06-design：G7 防盗链检查培训
- 07-publish：账号健康/评论群发开关培训

**修改文件**：`gate-check.py` / `docs/roles/03-structure.md` / `docs/roles/04-writer.md` / `docs/roles/06-design.md` / `docs/roles/07-publish.md`

**影响面**：gate-check.py 输出判定级别与角色卡要求完全对齐，防止"WARN 通过了但 G7 BLOCK 了"的流程断裂

**触发**：用户指令"对所有岗位进行定岗定位定责培训，所有岗位技能只能通过外部调用"

**决策内容**：
将 10 个岗位从"内嵌执行逻辑"重构为"薄岗位 + 厚工具"架构：
- 岗位只负责调度、交接、决策，不包含执行逻辑
- 所有执行技能外部化到 skill / 工具调用
- 培训重点从"教执行方法"转为"教调用协议 + 交接演练"

**修改文件**：
- `docs/roles/01-lead.md` — 新增外部调用表（minis-cli company/agent/apple-reminders）
- `docs/roles/02-research.md` — 新增外部调用表（re-souo-ju-he/anysearch/exa-search/web-content-extractor）
- `docs/roles/03-structure.md` — 删除结构模板库表格，新增外部调用表（bao-kuai-xie-zuo/wu-ceng-jue-ce）
- `docs/roles/04-writer.md` — 移除11洞见维度列举，新增外部调用表（bao-kuai-xie-zuo/gzh-chuang-gao/gate-check）
- `docs/roles/05-review.md` — 新增外部调用表（yuwen-publish-precheck/gate-check strict/H11/H12/H15）
- `docs/roles/06-design.md` — 新增外部调用表（gzh-pai-ban/gzh-cover-gen/H11/H12/H15/cover-pipeline）
- `docs/roles/07-publish.md` — 新增外部调用表（gzh-api-tui-song/gongzhonghao-publish/H11）
- `docs/roles/08-return.md` — 新增外部调用表（research/second-brain-guide/memory-l2-rollup）
- `docs/roles/09-photo.md` — 新增外部调用表（photo-shotlist/apple-vision/ai-detection-signals）
- `docs/roles/10-creative.md` — 修正正文残留3.11→3.10，新增外部调用表（hai-bao-she-ji/gzh-cover-gen/gzh-brand）
- `training/skills/*.md`（10个）— 重构为调用协议训练 + 交接演练 + 量化考核标准
- `docs/00-architecture/role-external-call-design-20261016.md` — 新增架构设计文档
- `TEAM.md` — frontmatter version 4.0.0→4.1.0

**影响面**：
- 角色卡 token 大幅精简（04-writer 7729B→4183B，-46%）
- 培训卡 token 从 1500-3500 降至 300-420，缩减约 75-85%
- 岗位执行逻辑全部沉淀到外部 skill，交更成本从"改角色卡"变为"改 skill"
- 交接契约、产出物标准、灵魂描述全部保留
