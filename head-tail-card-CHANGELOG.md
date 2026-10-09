# head-tail-card.py 更新记录

> 2026-09-25 | v1.5

---

## 变更

| 字段 | 旧值 | 新值 |
|------|------|------|
| SLOGAN 常量 | `山野水系 · 行走笔记` | `野路实测，笔记为证：留下能用的` |
| 尾图副文案 | `野路实测，笔记为证：留下能用的 · AI 做内容，动作讲清楚` | `野路实测，笔记为证：留下能用的` |

---

## 用法

```bash
cd gzh-team

# 生成首图 + 尾图
python3 head-tail-card.py --title "标题" --sub "副标题" --date 2026.09.28

# 只生成尾图
python3 head-tail-card.py --only tail

# 带下一篇预告
python3 head-tail-card.py --only tail --next "AI 学术诚信：学生该知道什么"

# 不带印章
python3 head-tail-card.py --no-seal
```

---

## 输出

| 文件 | 尺寸 | 用途 |
|------|------|------|
| `assets/out/首图-<标题>.png` | 900×383 | 头条封面 |
| `assets/out/尾图-关注型.png` | 900×400 | 文章结尾引导关注 |

---

## 待办

- [ ] 更新 `head-cover-spec.md` v1.5 记录
- [ ] 更新 `brand-colors.md` v1.5 记录（如需要）