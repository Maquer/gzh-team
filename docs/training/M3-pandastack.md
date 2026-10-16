# M3: PandaStack API 培训

**掌握标准**: 能创建/清理 sandbox，理解配额管理

---

## 1. API 端点

### 创建 Sandbox
```bash
curl -X POST https://api.pandastack.ai/v1/sandboxes \
  -H "Authorization: Bearer $PANDASTACK_API_KEY" \
  -d '{"template":"browser","ttl_seconds":1800}'
```

### 删除 Sandbox
```bash
curl -X DELETE https://api.pandastack.ai/v1/sandboxes/{id} \
  -H "Authorization: Bearer $PANDASTACK_API_KEY"
```

---

## 2. 配额管理

**Free Tier**: 40 CPU / 10GB RAM

**关键纪律**:
- ⚠️ 每次渲染后必须立即清理 sandbox
- ⚠️ 避免长时间保留闲置 sandbox
