---
id: tools-media
title: "12.4 生图层（排版岗职责）"
tokens: 1704
source: "TEAM.md.bak-pre-split"
source_lines: "795-826"
---

### 12.4 生图层（排版岗职责）

| 工具 | 类型 | 状态 | 路径/入口 | 用法 |
|------|------|------|-----------|------|
| `hai-bao-she-ji` | Skill+脚本 | ✅ | `skills/hai-bao-she-ji/scripts/generate_mondo_enhanced.py` | 37 设计师风格 + 6 维原子组合 + 8 混色预设 + 7 种比例 |
| `jimeng_provider.py` | 后端脚本 | ✅ | `skills/hai-bao-she-ji/scripts/jimeng_provider.py` | 即梦后端，68 积分/天免费。cookie 从浏览器 offload 自动取最新 |
| `minis-model-use` | CLI | ✅ | `minis-model-use run --model sensenova-u1-fast` | 模型生图，2048×2048 PNG，~40s/张。size 只吃 13 种固定值，连跑需 sleep 20s+ |
| **`cover-pipeline.py`** | 脚本 | ✅ 黄金测试 3/3 | `cover-pipeline.py` | **封面一条命令流水线**：去水印（纯色覆盖）→ 裁 2.35:1 → 叠标题 → OCR 门禁自检（自动区分幻觉/真实文字）。退出码 0=全绿 / 1=H11 未过。见下方「封面流水线」 |
| `apple-vision ocr` | CLI | ✅ | `apple-vision ocr <图> --lang zh-Hans,en --level fast` | H11 门禁执行器。**只用 fast 级**；accurate 在纯色区造字 |

 **即梦用法**：
```bash
python3 <SKILLS_DIR>/hai-bao-she-ji/scripts/generate_mondo_enhanced.py \
  "<subject>" poster --style saul-bass --provider jimeng --aspect-ratio 21:9
```

**封面流水线（推荐，一步到位）**：
```bash
python3 cover-pipeline.py \
  --src <出图路径> --wm "<x1,y1,x2,y2>" \
  --title "你的 AI 文章标注了吗？" --sub "副标题" \
  --out attachments/cover.png
# 想保留水印（自动满足 AI 标识）改加 --keep-wm，并去掉 --wm
```

**生图五条硬约束**（两轮实测 09-17）：
1. ⚠️ 中文错字（自→客）→ **标题文字后期叠加**（Pillow + Noto Sans CJK），不在 prompt 里写中文
2. ⚠️ prompt 元数据被画进图 → prompt 末尾必须加 `no text, no watermark, no lettering`
3. ⚠️ **两通道都自带水印且不可关**：即梦左下角"AI生成"、sensenova 右上角"日日新+sensenova"。要干净封面须 Pillow 纯色覆盖，**覆盖区 ≥ OCR bbox + 40px**；裁切 2.35:1 去不掉即梦水印（y=0.922 在裁切范围内）
4. ⚠️ 去水印后标识责任转到发布 → 图上无"AI生成"字样即不满足显式标识，发布必须开后台「AI 生成内容」声明开关
5. ⚠️ OCR 抽检**必须 `--level fast`** → accurate 级在纯色覆盖区会产生 conf=0.30 幻觉文字（实测"中貝新"，像素验证 1 色）

