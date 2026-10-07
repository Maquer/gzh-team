# 提醒任务提案模板

> 岗位提新提案时，复制下面代码块到 `pending.md`，改字段，然后通知 01 负责人。

```yaml
- id: REM-YYYYMMDD-NN           # 唯一 ID，例：REM-20260922-01
  title: 一句话说明要提醒什么     # ≤30 字，动词开头
  created_at: 2026-09-22T22:30+08:00
  created_by: 07-publish        # 提出岗位 ID
  trigger_kind: role            # auto | role | cross
  event_at: 2026-09-25T20:00+08:00  # 关联事件时间（可选）
                                  # 有值时 fire_at = event_at + offset（偏移量从 --countdown 推导）
                                  # 无值时 fire_at = created_at + countdown（默认行为，已有）
                                  # 示例：稿件 09-25 晚间发布 → 72h 后查阅读 → event_at=09-25T20:00, countdown=259200
  fire_at: 2026-09-28T20:00+08:00  # 绝对时间戳，不允许相对时间
  reason: 为什么建这条提醒      # 必填，不允许"待定""待办"
  action: 触发后要做什么        # 动词开头，具体到可执行
  related_task: 稿件/项目 ID    # 如有
  status: pending               # pending | active | done | rejected
  confirmed_by: ""              # pending 时空
  confirmed_at: ""              # pending 时空
  result: ""                    # done 时填
```

## 档位速查

| trigger_kind | 含义 | 谁确认 |
|---|---|---|
| `auto` | 规则内置（如 09 数据岗 10 篇复盘） | 自动通过，只登记 |
| `role` | 单岗位自主衍生 | 01 负责人 |
| `cross` | 跨岗位协作 | 01 + 相关岗位 |

## 校验清单（提出岗位自检）

- [ ] `fire_at` 是绝对时间戳，不是"3 天后"这种相对时间
- [ ] `action` 是动词开头，具体到"检查 XX 并 YY"
- [ ] `reason` 说清"为什么不能现在做"
- [ ] `event_at`（如有）≤ `fire_at`，且 `fire_at - event_at` ≈ `countdown` 偏移量
- [ ] 查过 `active.md` / `done.md`，没有重复提案
- [ ] `created_at` 与 `fire_at` 差 ≤90 天（超过需要 01+09 双确认）

### event_at 规则（新增）
- **有事件锚点的任务**（如"稿件发布后 N 小时查数据"）必须填 `event_at`，让 fire_at 基于事件而非创建时间
- **无事件锚点的任务**（如"每周复盘"）留空，用默认行为（fire_at = created_at + countdown）
- 01 审批时若发现"稿件发布后 72h 查阅读"类提案未填 `event_at`，必须退回重写
