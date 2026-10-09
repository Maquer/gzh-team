# 提醒任务登记与流程

> **位置**：`docs/rules/reminders.md`
> **建立日期**：2026-09-21
> **上位规则**：`docs/rules/gate-mapping.md`（门禁归属表）
> **底层工具**：`countdown-scheduler.py`（`../`）
> **触发场景**：任何岗位在执行任务过程中，识别出"这事过 N 小时/天/周后再看更合适"时，不能靠人肉记忆，必须走登记流程。

---

## 1. 目的

- **不丢事**：任务中衍生出的后续动作，落到调度器而不是脑内 TODO
- **可审计**：谁提的、谁确认的、什么时候执行、为什么提，全部有痕
- **可归因**：数据岗复盘时，能区分"主动衍生的复盘"和"临时想到的复盘"

## 2. 触发权限矩阵（3 档）

| 档位 | 场景 | 确认人 | 阻塞 |
|---|---|---|---|
| **A. 规则内置** | 已在 TEAM.md 明写的固定周期任务（如 09 数据岗"10 篇一组复盘"） | 自动通过（登记即可） | 否 |
| **B. 岗位自主** | 单岗位衍生、不涉及他人协作（如 07 发布岗"3 天后看阅读量"） | 01 负责人 1 人 | 是（等确认） |
| **C. 跨岗位协作** | 需要 ≥2 个岗位共同参与（如"下周同 09 数据一起复盘 07 的发布"） | 01 负责人 + 相关岗位 1 人 | 是（等双方） |

**判据**：如果这条提醒跑起来的时候，只有一个岗位会动 → B；如果会有 ≥2 个岗位交接 → C。

## 3. 时间戳 4 字段（强制）

每个提醒任务必须带完整 4 个时间戳，缺一不可：

| 字段 | 含义 | 填写时机 |
|---|---|---|
| `created_at` | 衍生时间（提案提出时刻） | 提出岗位填写，格式 `YYYY-MM-DDTHH:MM+08:00` |
| `fire_at` | 计划触发时间 | 提出岗位填写，格式同上 |
| `created_by` | 提出岗位 ID（01/02/.../09） | 提出岗位填写 |
| `confirmed_by` | 确认人（岗位 ID 或 `auto:rule-10-articles` 等规则标识） | 审批人填写 |
| `confirmed_at` | 审批完成时间 | 审批人填写 |

**空字段 = 无效提案**：`pending.md` 里出现空 `fire_at` 或空 `created_by` 的条目，05 审核岗下次巡检时必须退回。

## 4. 3 态登记簿

路径：`docs/reminders/`

| 文件 | 状态 | 内容 |
|---|---|---|
| `pending.md` | 待审批 | 提案刚提出、等待签核 |
| `active.md` | 已批准、待触发 | countdown-scheduler 里已注册的任务 |
| `done.md` | 已完成、归档 | 触发跑完，写回结果 |
| `proposals.md` | 提案模板 | 岗位提新提案时的填空模板 |

**生命周期**：`proposals` → `pending` → `active` → `done`（不允许多跳；如从 active 回 pending 视为流程违规）。

## 5. 提案模板

新提案必须按 `docs/reminders/proposals.md` 模板填写。核心字段：

```yaml
- id: REM-YYYYMMDD-NN       # 唯一 ID
  title: 一句话说明要提醒什么
  created_at: 2026-09-21T22:30+08:00
  created_by: 07-publish    # 提出岗位
  trigger_kind: auto | role | cross  # 对应 §2 档位
  event_at: 2026-09-25T20:00+08:00  # 关联事件时间（可选）
                                   # 有值时 fire_at = event_at + offset（偏移量从 --countdown 推导）
                                   # 无值时 fire_at = created_at + countdown（默认行为）
                                   # 适用：稿件发布后 N 小时查数据、上线后 X 天复盘等
  fire_at: 2026-09-28T20:00+08:00  # 绝对时间戳，不允许相对时间
  reason: 为什么建这条提醒（不允许填"待办""待定"）
  action: 触发后要执行的具体动作（动词开头）
  related_task: 关联的稿件/项目 ID（如有）
  status: pending | active | done | rejected
  confirmed_by: ""           # pending 时空
  confirmed_at: ""           # pending 时空
  result: ""                 # done 时填结果摘要
```

### event_at 使用规则

- **有事件锚点**（如"稿件发布后 72h 查阅读"）：**必须填** `event_at`，让 fire_at 基于事件而非创建时间
- **无事件锚点**（如"每周固定复盘"）：留空，走默认行为（fire_at = created_at + countdown）
- 审批时若发现该填 `event_at` 却没填 → 退回重填，避免同类误触发
- 注册任务时用 `--event-at <ISO时间>` 代替手动调 `next_fire_at`

## 6. 确认流程

### 6.1 提出（任意有权限岗位）

1. 在 `docs/reminders/proposals.md` 复制模板，填好必填字段
2. 追加到 `docs/reminders/pending.md`
3. 通知 01 负责人（B/C 档必须通知）

### 6.2 审批（01 负责人）

1. 逐条读 `pending.md`
2. 判断是否符合 §2 权限档判据
3. 决策：
   - **通过**：填 `confirmed_by` / `confirmed_at`，改 `status: active`，从 `pending.md` 移到 `active.md`
   - **驳回**：填 `status: rejected` + `reject_reason`，留在 `pending.md` 底部供审计
4. 审批后调用：`python3 ../countdown-scheduler.py add --name <REM-ID> --countdown <X> --kind prompt --prompt "<action>"`

### 6.3 触发

- `countdown-scheduler` 到点触发 → 相关岗位收到 prompt
- 岗位执行完毕后，把条目从 `active.md` 移到 `done.md`，填 `result`

### 6.4 归档

- `done.md` 满 20 条 → 压缩归档到 `done-YYYYMM.md`（月度卷）
- 归档后清空 `done.md`，重新开始计数

## 7. 岗位触发权（谁可以提）

| 岗位 | 可提档位 | 典型场景 |
|---|---|---|
| 01 负责人 | A / B / C | 选题方向复核、策略调整回看 |
| 02 信息收集 | A / B | 素材有效期到期、外部事件跟踪 |
| 03 结构梳理 | B | 结构方案后续 A/B 对比 |
| 04 主笔 | B | 稿件改写后的效果追踪 |
| 05 审核 | B / C | 复核类、发布后修订 |
| 06 排版 | B | 排版方案在不同设备的效果回看 |
| 07 发布 | A / B / C | 阅读量 24h/72h、封面 A/B |
| 08 互动 | A / B | 留言转化跟踪、再触点设计 |
| 09 数据 | A / B / C | **10 篇复盘（规则内置）**、异常追踪 |

**越权提案**：02 提 A 档自动通过是可以的（规则内置）；但 02 提 C 档跨岗位协作，需 01 判定是否合理。

## 8. 越界红线（什么时候不能建提醒）

- **无明确 action**：`action` 字段只写"复盘一下""再看一看"→ 拒绝
- **无明确 `fire_at`**：不填"3 天后"（相对时间），必须写绝对时间戳
- **重复提案**：同一 `related_task` + 同一 `action` 类型已存在 → 拒绝
- **规避复盘**：不能用"3 天后看"来拖延当期的复盘义务（09 数据的 10 篇复盘有独立触发权）
- **单点确认滥用**：跨岗位任务不能只让 01 一个人确认，必须拉相关岗位
- **超过 90 天**：`fire_at - created_at > 90 天` 的提醒必须经 01 + 09 双确认（长期提醒容易失效）

## 9. 常见反例（拒绝示例）

**反例 1**（缺 action）：
```yaml
title: 3 天后看看
action: 看一下        # ❌ 什么是"看一下"
fire_at: 2026-09-24T22:00+08:00
```
→ 应改为：`action: 检查 REM-20260921-01 稿件 72h 阅读量，若低于基线 20% 通知 01 负责人`

**反例 2**（相对时间）：
```yaml
fire_at: 3 天后       # ❌ 不写绝对时间戳
```
→ 应改为：`fire_at: 2026-09-24T22:00+08:00`

**反例 3**（规避复盘）：
```yaml
title: 等数据多了再复盘
fire_at: 2027-01-15T00:00+08:00   # ❌ 用"以后复盘"推迟当前义务
```
→ 违反 09 数据岗"10 篇一组复盘"规则，01 必须驳回

## 10. 关联规则

- `TEAM.md §13`：变更流程（本流程与变更流程互补，不重叠）
- `docs/rules/gate-mapping.md`：门禁脚本归属表（提醒任务是"时间维"，门禁是"内容维"）
- `countdown-scheduler.py`：底层调度器（跨会话存活，minis 死亡后启动补跑）

## 11. 未做（已知空白）

- 未写脚本自动校验 `pending.md` / `active.md` 的字段完整性（当前靠 05 审核岗人肉巡检）
- 未定义"确认超时"机制（如 pending 超过 7 天无人确认怎么办，暂按超时驳回处理）
- 未做跨任务去重（同 `related_task` + 同 action 靠人判断）
- 未接入 Bark push 通道（minis-scheduled 是 best-effort，minis 死亡后靠 `check --catchup` 补跑）
- **已修复（2026-09-26）**：添加 `event_at` 字段支持，prompt 类任务可用 `--event-at` 指定事件锚定时间，避免 fire_at 基于 created_at 导致提前触发
