# M2: HyperFrames 基础培训

**掌握标准**: 能编写简单 HTML composition

---

## 1. 核心概念

**Composition = HTML + data 属性**

```html
<div data-composition-id="my-video" 
     data-start="0" 
     data-width="1920" 
     data-height="1080">
  <h1 class="clip" data-start="0" data-duration="10">Hello World</h1>
</div>
```

---

## 2. 关键属性

| 属性 | 说明 | 示例 |
|------|------|------|
| `data-composition-id` | 根容器 ID（必须唯一） | `my-video` |
| `data-start` | 开始时间（秒） | `0`, `1.5` |
| `data-duration` | 持续时间（秒） | `5`, `10` |
| `data-track-index` | 轨道索引 | `0`, `1`, `2` |
| `class="clip"` | 标记为可动画元素 | `clip` |

---

## 3. 实操练习

```bash
# 初始化项目
npx hyperframes init demo
cd demo

# 编辑 index.html
# 检查语法
npx hyperframes lint
```

---

## 4. 验收标准

- [ ] 能创建 HyperFrames 项目
- [ ] 能编写 basic composition HTML
- [ ] 能通过 lint 检查
