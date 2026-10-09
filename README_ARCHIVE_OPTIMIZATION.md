# 归档不装优化体系 README

## 概述

本项目旨在优化"归档不装"决策体系，使其更高效、更智能、更可维护。

## 核心优化目标

1. **减少重复决策**：通过自动化决策树，90% 的决策由脚本自动完成
2. **精简归档笔记**：采用四段式精简格式，每个笔记 50-80 行
3. **建立活档案系统**：动态更新归档状态和决策
4. **应用强制执行机制**：P0 级工具强制执行，P1 级工具部分执行，P2 级工具归档
5. **创建一站式管理工具**：所有工具通过统一入口管理

## 目录结构

```
gzh-team/
├── archives-rules.md                 # 归档不装优化体系规则
├── archives_optimizer.py             # 优化主脚本：分类 → 环境检查 → P0/P1/P2 决策 → 写笔记
├── archive_note_generator.py         # 按 decision_log.json 批量生成归档笔记
├── active_tools.json                 # 输入：待处理工具（name / priority / domain / status）
├── domain_classifications.json       # 输入：工具 → 领域/优先级（缺失时自动写入默认值）
├── redundancy_mapping.json           # 输入：领域内重合关系（值以 archive 开头即强制归档）
├── decision_log.json                 # 输出：决策日志（追加写入）
├── optimization_results.json         # 输出：本次决策结果
├── optimization_report.md            # 输出：决策统计报告
├── archive_note_<工具名>.md          # 输出：优化器生成的归档笔记
├── archive_notes/                    # 输出：笔记生成器生成的归档笔记
├── archive_generation_report.md      # 输出：笔记生成汇总
└── README_ARCHIVE_OPTIMIZATION.md    # 本文件
```

## 快速开始

### 1. 环境

只用 Python 3 标准库，无额外依赖。在仓库根目录执行即可（脚本会自动以自身所在目录为工作目录）。

### 2. 运行优化流程

```bash
# 运行归档不装优化器（默认读取 active_tools.json，结果写在仓库根目录）
python3 archives_optimizer.py

# 指定工具列表文件和输出目录
python3 archives_optimizer.py --tools my_tools.json --output out/

# 按决策日志生成精简归档笔记（输出到 archive_notes/）
python3 archive_note_generator.py
python3 archive_note_generator.py --tools my_tools.json
```

### 3. 查看结果

```bash
cat optimization_results.json      # 优化结果
cat optimization_report.md         # 决策统计
cat decision_log.json              # 决策日志
cat archive_notes/archive_note_*.md
cat archive_generation_report.md
```

## 技术细节

### 决策流程

1. **领域分类**：先查 `domain_classifications.json`，查不到再用 `active_tools.json` 里的 domain/priority；都没有则跳过
2. **领域重合检查**：`redundancy_mapping.json` 中该工具在本领域标记为 archive → 直接归档
3. **环境可行性检查**：`active_tools.json` 中 status 为 ARCHIVE / ARCHIVED 视为不可用，其余视为可用
4. **P0-P1-P2 三级决策**：
   - **P0 级**：环境可用则强制执行，否则归档
   - **P1 级**：环境可用则部分执行，否则归档
   - **P2 级**：直接归档

### 文件格式

#### 归档笔记格式

```markdown
# 工具名称
> 核心价值：[P0/P1/P2 级]
> 决策边界：[决策边界说明]
> P1 借鉴：[P1 级借鉴内容]
> 域内边界：[域内边界说明]

## 核心定位
[工具定位说明]

## 核心差异
与同类工具不同之处在于[差异]。

## P1 借鉴
从[来源]中借鉴[内容]。

## 域内边界
[边界说明]
```

### 决策日志格式

```json
{
  "timestamp": "2026-09-22T10:00:00",
  "tool_name": "tool1",
  "decision": "FORCE_INSTALL",
  "content": "[决策内容摘要...]"
}
```

## 使用示例

### 示例1：P0 强制执行工具

假设有一个名为 "archify" 的工具，根据分类属于 "tool-development" 领域，优先级为 P0，环境可用性为 True。

```bash
# 运行优化器
python3 archives_optimizer.py

# 结果
{
  "tool_name": "archify",
  "domain": "tool-development",
  "priority": "P0",
  "env_viable": true,
  "decision": "FORCE_INSTALL",
  "timestamp": "2026-09-22T10:00:00"
}

# 生成的归档笔记
# archify
> 核心价值：P0 强制执行工具
> 决策边界：环境不可用则归档
> P1 借鉴：架构设计与执行流程
> 域内边界：iSH 环境限制

## 核心定位
archify 是 P0 级工具，在当前环境中强制执行。

## 核心差异
与同类工具不同之处在于自动化执行能力。

## P1 借鉴
从 archify 中借鉴执行流程和架构设计。

## 域内边界
archify 的应用受限于 iSH 环境限制。
```

### 示例2：归档工具

假设有一个名为 "higgsfield" 的工具，根据分类属于 "data-analysis" 领域，优先级为 P2，环境可用性为 False。

```bash
# 运行优化器
python3 archives_optimizer.py

# 结果
{
  "tool_name": "higgsfield",
  "domain": "data-analysis",
  "priority": "P2",
  "env_viable": false,
  "decision": "ARCHIVE_ONLY",
  "timestamp": "2026-09-22T10:05:00"
}

# 生成的归档笔记
# higgsfield
> 核心价值：P2/P3 仅归档工具
> 决策边界：环境不可用 + 领域错位
> P1 借鉴：无直接借鉴
> 域内边界：完全归档工具

## 核心定位
higgsfield 归档仅供参考，无实际执行能力。

## 核心差异
与同类工具不同之处在于完全归档且无实际应用。

## P1 借鉴
无直接借鉴。

## 域内边界
higgsfield 完全归档，不具备实际应用条件。
```

## 维护指南

### 更新工具分类

1. 编辑 `domain_classifications.json` 文件
2. 更新工具到新的领域或调整优先级
3. 重新运行优化器

### 添加新工具

1. 在 `domain_classifications.json` 中添加新工具
2. 设置正确的领域和优先级
3. 运行优化器生成归档笔记

### 手动覆盖

如果需要手动覆盖自动化决策，可以在工具名称旁边添加前缀：

```bash
# 强制归档强制工具
cat >> priority_overrides.yaml << EOF
tool_name:
  override_decision: "ARCHIVE_ONLY"
EOF
```

## 常见问题

### 为什么优化器会失败？

1. 检查 `domain_classifications.json` 是否存在且格式正确
2. 确保所有必需的 Python 模块都已安装
3. 检查输出目录的权限

### 如何查看生成的归档笔记？

```bash
cat archive_notes/archive_note_*.md | less
```

或者查看汇总报告：

```bash
cat archive_generation_report.md
```

### 如何处理环境不可用的工具？

如果工具的环境不可用，优化器会将其标记为 "ARCHIVE_ONLY"。
如果需要强制执行，可以手动编辑生成的归档笔记，或者更新 `domain_classifications.json` 中工具的优先级。

## 未来计划

### 1. 添加更多自动化功能

- 自动检测工具之间的重合性
- 建议合并或保留的策略
- 自动生成对比分析报告

### 2. 增强可视化功能

- 图表化决策分布
- 可交互式决策树
- 热力图显示工具关系

### 3. 集成 CI/CD

- 将优化流程集成到 CI/CD 管道
- 自动验证生成的归档笔记
- 提供 CI 反馈和报告

## 许可

MIT License

## 联系方式

如有任何问题或建议，请联系项目负责人。

---

*本 README 文件由归档不装优化器自动生成*