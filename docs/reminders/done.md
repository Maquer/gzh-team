# 提醒任务 · 完成归档

> 触发跑完后的归档记录
> 满 20 条 → 压缩到 `done-YYYYMM.md` 月度卷

## 已完成

<!-- 无 -->

### REM-20260923-02 · 07-publish 提案（已顺延）

- **created_at**: 2026-09-23T06:38:22+08:00
- **created_by**: 07-publish
- **fire_at（原）**: 2026-09-26T06:38:22+08:00
- **fire_at（新）**: 2026-09-28T20:00:00+08:00（已顺延）
- **confirmed_by**: 01-lead
- **trigger_kind**: role
- **reason**: 3天后检查这篇稿子的72h阅读量
- **action**: 检查 wanganzhou 首发稿 72h 阅读量
- **status**: active（延期重排，非 done）
- **related_task**: wanganzhou《框架 3.0 那 4 个动作》（09-25 晚间发布，1 阅读/0 互动，已降级储备）
- ⚠️ **本次误触发**：今日 13:48 catchup 按 created_at+259183s 计算 fire_at，早于首发时间。当时仅 1 阅读，数据无意义，已作废。修正：next_fire_at 改为 09-28 20:00，fired_count 重置为 0。根因：prompt 类任务 fire_at 应基于事件时间（文章发布）而非创建时间，当前设计缺陷 → 已修复：proposals.md 加 `event_at` 字段，countdown-scheduler.py 加 `--event-at` 参数。

- **created_at**: 2026-09-23T06:53:44+08:00（依调度器记录 01c5a123 推断）
- **created_by**: 未追溯——proposals.md 无此提案记录，登记簿缺失时调度器已注册
- **fire_at**: 2026-09-24T06:53:44+08:00（实例 1，调度器 id `01c5a123`，countdown 24h）
- **confirmed_by**: —（补登记，创建时审批记录缺失，缺项按 reminders.md §4 规则不予追认，仅如实入账）
- **trigger_kind**: role（推断）
- **reason**: 复查上周三篇稿子的读者反馈数据
- **action**: 复查上周三篇稿子的读者反馈数据（"上周" = 09-14 ~ 09-20）
- **status**: done
- **result**: 09-24T22:00 手动触发（超期约 15h）。完整复查见 `复盘档案/数据回收-20260924-三篇稿子复查.md`。核心结论：(1) 09-17《4 部门 14 条新规》阅读 16→36→51，搜一搜 91.7%→94.1%，零互动；(2) 09-18 AI Skill 稿 D+3 仅 3 阅读、搜一搜 0%，判为本人点开；(3) 09-19 稿台账无记录，不补登记。跨篇判断：账号仍处标签压制期，无外部推荐流量。不下的结论：不说 09-17 表现好（n=51 无横向基线），不说 09-18/19 表现差（样本太小）。
- **related_task**: 阶段 2 首发（09-25 · AI 学术诚信）。前置输入：渠道结构未变、取数流程必须先修（T+1/T+7 定点）、完读率口径需统一、结尾加 1 个可回答的具体提问（04 主笔，需下一篇验证）、不改变 09-25〜09-27 排期
- ⚠️ **重复实例已撤销**：同 prompt 于 06:55:18 创建第二实例（调度器 id `f6f7ccae`，countdown 604789s = 7 天，触发 09-30T06:55）。两条创建仅隔 94 秒。**01 建议保留 09-24 实例、撤销 09-30 实例（与 REM-20260923-03 重叠）——已于 09-24T22:00 经用户确认执行撤销**。撤销命令：`python3 /var/minis/shared/countdown-scheduler.py remove --id f6f7ccae`

### REM-20260923-01 · 01-lead 提案

- **created_at**: 2026-09-23T06:18:32+08:00
- **created_by**: 01-lead
- **fire_at**: 2026-09-24T06:18:32+08:00
- **confirmed_by**: 01-lead
- **trigger_kind**: role
- **reason**: 明天复盘这篇稿子的选题方向和受众匹配度
- **action**: 明天复盘这篇稿子的选题方向和受众匹配度
- **status**: done
- **result**: 手动触发，明天复盘这篇稿子的选题方向和受众匹配度
- **related_task**: （待填）


### REM-20260922-01 · 07-publish 提案

- **created_at**: 2026-09-22T23:46:31+08:00
- **created_by**: 07-publish
- **fire_at**: 2026-09-25T23:46:31+08:00
- **confirmed_by**: 01-lead
- **confirmed_at**: 2026-09-23T06:37:07+08:00
- **trigger_kind**: role
- **reason**: 3天后检查这篇稿子的72h阅读量
- **action**: 3天后检查这篇稿子的72h阅读量
- **status**: done
- **result**: 手动触发，3天后检查这篇稿子的72h阅读量
- **related_task**: （待填）



