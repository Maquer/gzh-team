# 提醒任务 · 活跃队列

> 已批准的提醒任务，在 countdown-scheduler 里已注册
> 触发后按 `action` 执行，完成后转 `done.md`

## 活跃任务

### REM-20260923-02 · 07-publish 提案

- **created_at**: 2026-09-23T06:38:22+08:00
- **created_by**: 07-publish
- **fire_at**: 2026-09-28T20:00:00+08:00（已顺延）
- **result**: ⚠️ 今日 13:48 误触发（稿件刚发布几小时，1阅读），数据作废。已顺延至 09-28 20:00 重新触发（首发后 ~72h）。根因：prompt 类任务 fire_at 用 created_at 而非 event_time 计算 → **已修复**：proposals.md 加 `event_at` 字段，countdown-scheduler.py 加 `--event-at` 参数，后续同类提案必须填 `event_at`。
- **补录 13:57（另一会话）**：13:52 我误建的手动提醒 `17EFCA4D` 已 fire，同样取不到数——**公众号数据中心 API 这条路在 iSH 走不通**：`gzh-api-push.py token` 返回 **40164 IP 不在白名单**（出口 IP `223.160.187.182`，iSH 出口 IP 会变，加白名单不实用）；且阅读数据接口另需认证主体。与 09 岗定位一致：**09-data 工具链就是「后台手动录入」，不上 API**。
- 调度器已按 event_at 重建：旧 `51534c06` → 新 `f7f5bdb7`（first fire 09-28 20:00，event_at 09-25 20:00）。**待确认**：首发日期两处记录冲突（09-24 22:50 vs 09-26），72h 时点相应落在 09-28 或 09-29，需 07 岗按后台实际时间核。


### REM-20260923-03 · 09-data 提案

- **created_at**: 2026-09-23T06:38:23+08:00
- **created_by**: 09-data
- **fire_at**: 2026-09-30T06:38:23+08:00
- **confirmed_by**: 01-lead
- **trigger_kind**: role
- **reason**: 下周复盘这篇稿子的选题方向和受众匹配度
- **action**: 下周复盘这篇稿子的选题方向和受众匹配度
- **status**: active
- **result**: （待触发）
- **related_task**: 阶段 2 三篇组复盘（09-24 wanganzhou 已发 / 09-27 ai-writing / 09-28 AI 学术诚信首发）。"这篇稿子"按三篇整组执行：选题方向 × 搜一搜占比 × 受众匹配，输出进阶段 3 判据（见 选题库/PLAN-phase2-recovery.md §3）


## 撤销审计（30 天）

- REM-20260922-01 · 07-publish → 01-lead 审批通过 → 注册调度器 ID `67f9e85c` → **01:48 撤销**（用户决策：仅作演示，不让其真触发）。撤销命令：`python3 /var/minis/shared/countdown-scheduler.py remove --id 67f9e85c`。调度器恢复到干净 6 任务状态。
