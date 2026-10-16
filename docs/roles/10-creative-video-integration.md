# 视频生成集成方案：10-丹青岗位扩展

**版本**: v0.1.0  
**日期**: 2026-10-16  
**状态**: 设计阶段

---

## 1. 集成定位

### 为什么是 10-丹青？

| 现有职责 | 视频扩展 |
|---------|---------|
| 图文翻译官（文字→图） | 文字→视频（新增） |
| 视觉创意决策 | 动效创意决策 |
| 首图/尾图生成 | 封面视频/片头生成 |
| 品牌视觉统一 | 动态品牌规范统一 |

**核心逻辑**：视频是"会动的图"，丹青的视觉翻译职能天然覆盖视频创意层。

---

## 2. 能力矩阵

### 2.1 三级视频能力

| 级别 | 能力 | 触发条件 | 工具链 |
|------|------|---------|--------|
| **L1** | 图片轮播+水印 | 基础需求、快速交付 | `video-lite.py` (iSH) |
| **L2** | 简单动画+字幕 | 数据可视化、转场效果 | `hyperframes` + PandaStack |
| **L3** | 复杂动效+多轨音频 | 产品发布、高级演示 | `hyperframes` + PandaStack + 外部素材 |

### 2.2 工具链映射

```
视频需求
    ↓
L1: video-lite.py (iSH 本地)
    ├── 图片序列 → MP4
    ├── fade 转场
    ├── PIL 水印烧入
    └── mov_text 软字幕轨
    
L2: HyperFrames + PandaStack
    ├── HTML composition 编写
    ├── GSAP/CSS 动画
    ├── 动态图表/转场
    └── 30.4KB ~ 5MB 输出
    
L3: 混合方案
    ├── HyperFrames 基础动效
    ├── 外部素材（实拍/AI 生成）
    ├── 音频混音（TTS/BGM）
    └── 多轨合成
```

---

## 3. 工作流程集成

### 3.1 与现有流程对接

```
[02-衡度] 素材包
    ↓
[03-矩尺] 结构案（新增：是否需要视频？）
    ↓
[10-丹青] 视觉创意（新增：视频创意方案）
    ↓
[04-管城] 撰写（新增：视频脚本）
    ↓
[10-丹青] 视频生成（新增执行层）
    ↓
[06-法度] 排版（新增：视频嵌入 HTML）
    ↓
[07-维缆] 发布（新增：视频上传检查）
```

### 3.2 新增交接契约

| 上游 | 下游 | 新增产出物 |
|------|------|-----------|
| 03-矩尺 | 10-丹青 | `视频需求说明.md`（时长/风格/用途） |
| 04-管城 | 10-丹青 | `视频脚本.md`（分镜/字幕/音效） |
| 10-丹青 | 06-法度 | `视频文件.mp4` + `嵌入代码.md` |
| 06-法度 | 07-维缆 | `视频上传检查清单.md` |

---

## 4. 培训要求扩展

### 4.1 新增技能模块

| 模块 | 内容 | 掌握标准 |
|------|------|---------|
| **M1** | `video-lite.py` 使用 | 能独立生成图片轮播视频 |
| **M2** | HyperFrames 基础 | 能编写简单 HTML composition |
| **M3** | PandaStack API | 能创建/清理 sandbox，下载渲染结果 |
| **M4** | 视频嵌入公众号 | 能正确嵌入 `<video>` 标签并测试 |
| **M5** | 视频门禁检查 | 能运行 H16-H18 视频相关门禁 |

### 4.2 实操考核

**L1 考核**：
```bash
# 给定 5 张封面图，生成带水印的 15 秒视频
python3 /var/minis/shared/video-lite.py \
  --images /path/to/covers/ \
  --out video.mp4 \
  --duration 3 \
  --watermark "@弎水野记"
```
验收标准：视频时长准确、水印位置正确、MP4 可播放

**L2 考核**：
```bash
# 使用 HyperFrames 创建 10 秒产品介绍视频
npx hyperframes init product-demo
# 编写 HTML composition（含 GSAP 动画）
# 通过 PandaStack 渲染
# 下载并验证输出
```
验收标准：HTML 结构正确、动画流畅、视频无黑帧

---

## 5. 门禁扩展

### 5.1 新增视频门禁（H16-H18）

| 编号 | 名称 | 检查项 | 阻断条件 |
|------|------|--------|---------|
| **H16** | 视频格式校验 | MP4/WebM、h264 编码、分辨率合规 | 格式错误/编码不支持 |
| **H17** | 视频时长检查 | ≤60 秒（公众号限制） | 超时 |
| **H18** | 文件大小检查 | ≤50MB（上传限制） | 超限 |

### 5.2 修改现有门禁

| 编号 | 修改内容 |
|------|---------|
| **G6** | 新增"含视频文章排版验证"步骤 |
| **H15** | 扩展为"首尾图/视频合规验收" |
| **G7** | 新增视频防盗链检查（如适用） |

---

## 6. 技术实现

### 6.1 工具封装

**文件**: `/var/minis/shared/gzh-video.py`

```python
#!/usr/bin/env python3
"""
gzh-video.py — 公众号视频生成工具

功能：
1. L1: 图片轮播视频（video-lite.py 封装）
2. L2: HyperFrames + PandaStack 渲染
3. 门禁检查（H16-H18）
4. 嵌入代码生成
"""

import argparse
import subprocess
import json
import base64
from pathlib import Path

def create_sandbox(ttl=1800):
    """创建 PandaStack sandbox"""
    pass

def render_hyperframes(project_dir, output_path):
    """使用 PandaStack 渲染 HyperFrames 项目"""
    pass

def download_video(sandbox_id, remote_path, local_path):
    """从 sandbox 下载视频（base64）"""
    pass

def cleanup_sandbox(sandbox_id):
    """清理 sandbox"""
    pass

def check_video(video_path):
    """H16-H18 门禁检查"""
    pass
```

### 6.2 集成到 minis-cli

```bash
# 生成视频
minis-cli gzh video create --type l1 --images covers/ --out out.mp4

# 检查视频
minis-cli gzh video check --file out.mp4

# 生成嵌入代码
minis-cli gzh video embed --file out.mp4 --type hosted
```

---

## 7. 成本与资源

### 7.1 PandaStack 配额管理

| 指标 | 限制 | 建议策略 |
|------|------|---------|
| CPU | 40 vCPU | 单 sandbox 8 vCPU，最多 5 并发 |
| 内存 | 10 GB | 单 sandbox 4 GB，避免超配 |
| TTL | 30 min | 渲染后立即下载，超时清理 |

**关键**：每次渲染后必须清理 sandbox，避免配额积压。

### 7.2 成本估算

| 场景 | 单次成本 | 月成本（假设 20 篇）|
|------|---------|-------------------|
| L1 (video-lite.py) | ¥0 | ¥0 |
| L2 (PandaStack) | ¥0.03-0.1 | ¥0.6-2 |
| L3 (混合) | ¥0.1-0.5 | ¥2-10 |

---

## 8. 实施计划

### Phase 1: 基础能力（本周）
- [ ] 创建 `gzh-video.py` 封装脚本
- [ ] 集成到 10-丹青 培训模块
- [ ] 跑通 L1 流程（图片→视频）

### Phase 2: 高级能力（下周）
- [ ] 集成 PandaStack 渲染流程
- [ ] 实现 H16-H18 门禁
- [ ] 测试 L2 流程（HTML→MP4）

### Phase 3: 流程整合（下下周）
- [ ] 更新 TEAM.md 角色手册
- [ ] 集成到发布流水线
- [ ] 实盘验证（真实选题）

---

## 9. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| PandaStack 配额耗尽 | 高 | 中 | L1 降级方案；监控配额使用 |
| 渲染超时 | 中 | 低 | timeout=300s；失败重试机制 |
| 视频文件过大 | 低 | 中 | H18 门禁前置；压缩优化 |
| 培训成本高 | 中 | 中 | 分阶段培训；实操考核 |

---

## 10. 成功指标

- **采用率**: 30% 文章使用视频（首月）→ 50%（季度）
- **质量**: H16-H18 通过率 ≥95%
- **效率**: 视频生成 ≤10 分钟（L1）/ ≤15 分钟（L2）
- **成本**: 月视频渲染成本 ≤¥50

---

**决策**: 待 01-定规 审批后实施
