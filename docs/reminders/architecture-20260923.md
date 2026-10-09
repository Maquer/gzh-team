# 提醒系统架构说明（2026-09-23）

## 问题：Minis 被杀后台，Bark 审批怎么办？

### 核心设计

**Bark 通知携带 Worker URL，不依赖 Minis 存活。**

当 01-lead 提交提案后，Bark 通知包含两个链接：
- ✅ 批：`https://daily-cron.lovemaquer.workers.dev/remind/approve?rem_id=REM-XXXX`
- ❌ 驳：`https://daily-cron.lovemaquer.workers.dev/remind/reject?rem_id=REM-XXXX&reason=...`

用户点击 Bark 通知 → 打开浏览器 → 访问 Worker 端点 → Worker 记录审批决定到 KV。

**整个过程不需要 Minis 运行。**

---

## 完整流程

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  角色提交    │ ──→ │ pending.md   │ ──→ │ Bark 通知   │ ──→ │ Worker KV    │
│  (本地)      │     │              │     │ (带 URL)    │     │ (云端存储)   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  sync-from  │ ←── │ active/done  │ ←── │ 调度器注册  │ ←── │  Minis 恢复  │
│  -worker    │     │  队列更新     │     │  (本地)     │     │  (用户操作)  │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

### 关键节点

| 阶段 | 依赖 Minis | 依赖网络 | 说明 |
|------|-----------|---------|------|
| 提交提案 | ✅ | ❌ | 写入 pending.md |
| Bark 通知 | ✅ | ✅ | 发送通知（含 Worker URL） |
| 用户点击审批 | ❌ | ✅ | 打开浏览器访问 Worker |
| Worker 记录决定 | ❌ | ✅ | KV 存储，Minis 随时可同步 |
| sync-from-worker | ✅ | ✅ | 拉取决定并应用到本地队列 |
| 调度器执行 | ✅ | ❌ | 按 fire_at 触发 |

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `../remind-action.py` | 主脚本：submit/approve/reject/list/run/status/sync-from-worker |
| `../worker-daily-cron.js` | Worker：health/tasks/dryrun/test + remind/approve/reject/decisions/delete-decisions |
| `docs/reminders/pending.md` | 待审批队列 |
| `docs/reminders/active.md` | 已审批队列 |
| `docs/reminders/done.md` | 已完成队列 |
| `../.scheduler/countdown-tasks.json` | 调度器状态 |

---

## 使用方式

### 常规流程（Minis 存活）
```bash
# 提交提案
python3 ../remind-action.py submit "复查上周三篇稿子的读者反馈数据" --role 01-lead

# 审批（手动）
python3 ../remind-action.py approve REM-20260923-XX

# 驳回
python3 ../remind-action.py reject REM-20260923-XX --reason "理由"
```

### Minis 被杀后台后的恢复流程
```bash
# 1. 用户通过 Bark 点击审批链接（无需 Minis 运行）
# 2. Worker 记录决定到 KV

# 3. Minis 恢复后，运行同步
python3 ../remind-action.py sync-from-worker

# 4. 验证状态
python3 ../remind-action.py status
```

---

## 环境变量要求

| 变量 | 用途 | 必填 |
|------|------|------|
| `BARK_KEY` | Bark 推送密钥 | ✅ |
| `WORKER_URL` | Cloudflare Worker 地址 | 推荐（用于审批 URL） |

---

## 技术细节

### Worker 端点
- `GET /remind/approve?rem_id=XXX` — 记录审批决定
- `GET /remind/reject?rem_id=XXX&reason=XXX` — 记录驳回决定
- `GET /remind/decisions` — 拉取所有待处理决定
- `POST /remind/delete-decisions` — 清空已处理决定

### KV Key 结构
- `remind_decisions` → JSON array of `{rem_id, status, decided_at, decided_by, reason?}`
