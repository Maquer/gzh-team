# P1 借鉴 Easel 7 工具测试报告

> 日期：2026-10-03 19:30
> 测试文章：`outputs/test-article/article.md`（1239字，AI内容工作流主题）
> 测试方法：流水线全流程执行，逐项验证
> 修复记录：3 个 CLI 接口问题已全部修复（gate-check argparse / persona-layers --topic / skill-layers 文件参数）

---

## 测试结果总览

| # | 工具 | 对标 Easel | 测试项 | 结果 | 关键发现 |
|---|------|-----------|--------|------|---------|
| 1 | **gate-check.py** | content_guard | BLOCK/WARN 两级 | ✅ | BLOCK→exit7 硬拦，WARN→exit1 提醒；已加 argparse + --verbose |
| 2 | **persona-layers.py** | 画像分层 | 7层注入 | ✅ | `inject --layer writing --topic "AI内容工作流"` 带任务上下文 |
| 3 | **turn-reminders.py** | 轮间提醒 | 5步骤+轮转 | ✅ | `rotate --turn 3` 正确分组 |
| 4 | **skill-layers.py** | 三层加载 | 检查清单 | ✅ | `checklist <tool.py>` 分析具体工具覆盖度 |
| 5 | **manifest.py** | 薄索引编排 | record/list | ✅ | 原子写，topic/step 索引正常 |
| 6 | **output_paths.py** | 产物路径门禁 | validate+36 selftest | ✅ | 泛名/穿越/系统目录全检测 |
| 7 | **assertion-check.py** | argparse漂移 | 漂移检测 | ✅ | 63条声明，零漂移 |

---

## 修复记录（2026-10-03 19:15-19:30）

### 修复 1: gate-check.py 加 argparse

**问题：** 使用位置参数 `sys.argv[1]`，与团队其他工具 argparse 风格不一致。

**修复：** 加 `argparse`，支持：
- `gate-check.py <file>`（位置参数，向后兼容）
- `gate-check.py --file <path>`（可选参数）
- `gate-check.py --file <path> --verbose`（详细模式）

**验证：** 3 种用法 exit code 一致（0=WARN）。

### 修复 2: persona-layers.py 加 --topic

**问题：** `inject --layer writing` 不能指定具体任务主题。

**修复：** 加 `--topic` 参数，输出格式：
```
你是矩尺（写作层（结构+主笔））
你是管城（写作层（结构+主笔））

---
当前任务：AI内容工作流
请基于以上角色定位，完成当前任务。
```

**验证：** 向后兼容（不传 --topic 时输出不变）。

### 修复 3: skill-layers.py checklist 加文件参数

**问题：** `checklist` 只能输出框架说明，不能分析具体工具文件。

**修复：** 加可选位置参数 `<tool.py>`，输出格式：
```
=== 三层覆盖分析：gate-check ===
文件：gate-check.py  （188 行）

Layer 1 元数据： ❌
  - docstring: ❌ (6行)
  - 做什么: ✅
  - 什么时候用: ❌
  - 关键约束: ✅

Layer 2 指令： ✅
  - argparse: ✅
  - 用法说明: ✅

Layer 3 约束： ✅
  - exit code: ✅ (发现: 0,2,7)
  - 错误处理: ✅
  - 边界条件: ✅

覆盖度：7/9
```

**验证：** 向后兼容（不传参数时输出框架）。

---

## 详细测试记录

### Test 1: gate-check.py — 两级安全门禁

**测试用例：** 含元数据残留的文章

**第一次运行（BLOCK）：**
```
❌ BLOCK: H-元数据 3 处残留: 字数：约,调性：,平台：公众号
   → exit 7，硬拦发布，必须修复后复检
EXIT: 7
```

**修复后运行（WARN）：**
```
⚠️  WARN: H9 1 段超 3 句
   → 只提醒不阻断，建议优化后发布
EXIT: 0
```

**--verbose 模式：**
```
**② WARN 优化建议（只提醒，建议优化）**
- **H9**：将超 3 句段落拆为短句段落（每段 1-3 句，参见 TEAM.md §3.4）

**③ 未跑的检查**（本脚本未覆盖，需人工或其他脚本）
- 未跑 `train-check.py`（C1-C7 风格维度）
- 未跑 `link-check.py`（外链可访问性）
- 未跑 `verify-all.py`（H11/H12/H13 合规层）
- 未过 05 审核岗**人工通读**

**审核建议**：⚠️ 1 项 WARN 只提醒，建议优化后发布
**自检覆盖**：10/10 项已跑，9 PASS / 0 BLOCK / 1 WARN
```

**验证项：**
- ✅ BLOCK 级（exit 7）：元数据残留、注入残留、非标占位符、字数<200
- ✅ WARN 级（exit 0）：超3句段落、禁用词、元话语、标题策略不足
- ✅ argparse：位置参数 + --file + --verbose
- ✅ 两级独立：BLOCK 硬拦，WARN 不阻断

---

### Test 2: persona-layers.py — 画像分层读取

**测试用例：** `inject --layer writing --topic "AI内容工作流"`

**输出：**
```
你是矩尺（写作层（结构+主笔））
你是管城（写作层（结构+主笔））

---
当前任务：AI内容工作流
请基于以上角色定位，完成当前任务。
```

**验证项：**
- ✅ 7 层映射：strategy / writing / review / design / publish / data / creative
- ✅ 层间不跨读：writing 层只注入结构师+主笔，review 层只注入审核
- ✅ 多角色注入：同一层可注入多个角色
- ✅ --topic 参数：追加任务上下文

---

### Test 3: turn-reminders.py — 每轮行为提醒

**测试用例：** `rotate --turn 3`

**输出：**
```
[轮 3 → strategy 第 2 组]
  - 先定不做清单（边界），再做写什么（空间）
  - 决策依据必须指向具体门禁或实测数据，给不出依据叫猜
```

**验证项：**
- ✅ 5 步骤分类：writing / review / publish / strategy / structure
- ✅ 轮转功能：`rotate --turn N` 正确分组
- ✅ 注入功能：`inject --step writing --task "..."` 正常

---

### Test 4: skill-layers.py — SKILL 三层加载

**测试用例 1：** `checklist`（向后兼容）
```
=== SKILL 三层加载框架 ===

【Layer 1：元数据】
  目的：告诉用户这个工具做什么、什么时候用、关键约束
  行数上限：5
  检查项：一句话定位, 触发条件, 关键约束
  示例：gate-check.py：检查文章质量门禁，写入后必跑，<200字=BLOCK
```

**测试用例 2：** `checklist <tool.py>`（文件分析）
```
=== 三层覆盖分析：gate-check ===
文件：gate-check.py  （188 行）

Layer 1 元数据： ❌
  - docstring: ❌ (6行)
  - 做什么: ✅
  - 什么时候用: ❌
  - 关键约束: ✅

Layer 2 指令： ✅
  - argparse: ✅
  - 用法说明: ✅

Layer 3 约束： ✅
  - exit code: ✅ (发现: 0,2,7)
  - 错误处理: ✅
  - 边界条件: ✅

覆盖度：7/9
```

**验证项：**
- ✅ Layer 1 元数据：≤5 行（做什么、什么时候用、关键约束）
- ✅ Layer 2 指令：≤15 行（操作步骤、输入输出）
- ✅ Layer 3 约束：≤10 行（BLOCK/WARN、反模式、失败模式）
- ✅ 文件分析：`checklist <tool.py>` 分析具体工具覆盖度

---

### Test 5: manifest.py — 薄索引编排

**测试用例：** `record --topic "AI内容工作流" --layer produce ...`

**输出：**
```
[record] topic='AI内容工作流' layer='produce' skill='writing-skill' -> done
```

**list 输出：**
```json
[
  {
    "topic": "AI内容工作流",
    "step_count": 1,
    "status": "draft"
  },
  {
    "topic": "test-article",
    "step_count": 0,
    "status": "draft"
  }
]
```

**验证项：**
- ✅ 原子写：`.tmp` + `os.replace`
- ✅ 薄索引：只传路径+结论，不复制内容
- ✅ 全流程：record / latest / read / meta / list / selftest

---

### Test 6: output_paths.py — 产物路径门禁

**测试用例：** validate + selftest

**validate 合法：**
```
OK: outputs/test-article/article.md
exit: 0
```

**validate 泛名：**
```
ERROR: 禁止泛名项目 'test'
exit: 1
```

**validate 目录穿越：**
```
ERROR: 路径不存在于 base-dir 内（疑似目录穿越）
exit: 1
```

**validate 系统目录（allow-system）：**
```
OK: 系统目录 _publish
exit: 0
```

**selftest：**
```
=== results: 36 passed, 0 failed ===
```

**验证项：**
- ✅ 泛名黑名单：24 个（test/tmp/draft 等）
- ✅ 系统目录白名单：6 个（`_login/_publish/_analytics/_scratch/_inbox/_review`）
- ✅ 目录穿越检测：`Path.resolve()` + `relative_to()`
- ✅ 符号链接逃逸：resolve() 展开 symlink
- ✅ 隐藏目录拒绝：`.ssh` 等
- ✅ 泛名大小写不敏感：`TEST` / `TeMp` 均拒

---

### Test 7: assertion-check.py — argparse 漂移检测

**测试用例：** 扫描 26 个 Skill，63 条工具声明

**输出：**
```
扫描 26 个 Skill，共 63 条工具声明
全部 ✓ 已实现
零漂移
```

**验证项：**
- ✅ 扫描所有 SKILL.md 中的工具声明
- ✅ 对照脚本 argparse 定义
- ✅ 检测 DRIFT（SKILL 用了但脚本没定义）
- ✅ 检测 MISSING_REQUIRED（缺少必需参数）
- ✅ required 限定根 parser（子命令不产生假阳性）

---

## 流水线集成测试

### 完整流程

```
1. 写文章 → outputs/test-article/article.md
2. gate-check → BLOCK（元数据残留）→ exit 7
3. 修复文章 → 移除元数据
4. gate-check → WARN（1段超3句）→ exit 0（可发布）
5. gate-check --verbose → 显示详细检查项
6. manifest record → 登记产出
7. output_paths validate → 验证路径合法
8. persona-layers inject --topic → 注入审核层画像+任务
9. turn-reminders inject → 注入步骤提醒
10. skill-layers checklist <tool> → 检查三层覆盖
11. assertion-check → 验证零漂移
```

**结果：全链路通过**

---

## 工具改进建议

### 已完成
- ✅ gate-check.py 加 argparse（位置参数 + --file + --verbose）
- ✅ persona-layers.py 加 --topic 参数
- ✅ skill-layers.py checklist 加文件参数

### 待改进（P2）
| 工具 | 问题 | 建议 |
|------|------|------|
| gate-check.py | docstring 6行（超限5行） | 精简 docstring |
| gate-check.py | 缺"什么时候用" | 在 docstring 加触发条件 |
| output_paths.py | docstring 7行（超限5行） | 精简 docstring |
| skill-layers.py | 不能批量分析 | 加 `--dir <path>` 批量扫描 |
| manifest.py | 缺 --verbose | 加详细输出模式 |

---

## 结论

**7/7 工具全部测试通过，3 个 CLI 问题已修复。**

**核心价值：**
- gate-check 两级安全：BLOCK 硬拦 + WARN 提醒，比一刀切更实用
- output_paths 门禁：泛名/穿越/系统目录三重防护，36/36 selftest
- manifest 薄索引：只传路径+结论，不复制内容，数据不膨胀
- assertion-check 漂移检测：63 条声明零漂移，工具声明与实现一致
- persona-layers 分层：层间不跨读，避免上下文污染
- turn-reminders 轮转：每轮不同提醒，避免重复疲劳
- skill-layers 覆盖分析：检查工具三层结构完整性

**文件路径：**
```
gate-check.py      (修复: argparse + --verbose)
persona-layers.py  (修复: --topic)
../manifest.py                  (无改动)
../output_paths.py              (无改动)
../assertion-check.py           (无改动)
turn-reminders.py   (无改动)
../skill-layers.py              (修复: checklist <tool>)
```

---

> 测试文章：[article.md](outputs/test-article/article.md)
> 报告作者：gzh-team P1 测试流程
> 更新时间：2026-10-03 19:30