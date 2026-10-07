# 提醒任务 · 活跃队列

> 已批准的提醒任务，在 countdown-scheduler 里已注册
> 触发后按 `action` 执行，完成后转 `done.md`

## 活跃任务

### REM-20261002-01 · 08-data 提案
- **created_at**: 2026-10-02T15:30+08:00
- **created_by**: 08-data
- **fire_at**: 2026-10-05T15:30+08:00
- **trigger_kind**: role
- **reason**: 投稿「测试了 5 款 AI 写作工具，我发现一个反直觉结论」3天后检查72h阅读量
- **action**: 3天后检查这篇稿子的72h阅读量，填数据回收表
- **status**: active
- **related_task**: #9 测试了 5 款 AI 写作工具

### REM-20261002-02 · 08-data 提案
- **created_at**: 2026-10-02T15:30+08:00
- **created_by**: 08-data
- **fire_at**: 2026-10-02T15:30+08:00 + 30天
- **trigger_kind**: role
- **reason**: 投稿「测试了 5 款 AI 写作工具，我发现一个反直觉结论」30天后收集完整数据
- **action**: 30天后收集完整30天数据，回填数据回收表，对比基线
- **status**: active
- **related_task**: #9 测试了 5 款 AI 写作工具




## 撤销审计（30 天）

- REM-20260922-01 · 07-publish → 01-lead 审批通过 → 注册调度器 ID `67f9e85c` → **01:48 撤销**（用户决策：仅作演示，不让其真触发）。撤销命令：`python3 /var/minis/shared/countdown-scheduler.py remove --id 67f9e85c`。调度器恢复到干净 6 任务状态。
