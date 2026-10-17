# 归档封面脚本

归档日期：2026-10-17
原因：功能重叠，已合并到 cover-pipeline.py / cover-card.py / cover-brief.py

| 归档脚本 | 替代脚本 | 归档原因 |
|----------|----------|----------|
| cover-dynamic.py | cover-brief.py | 动态提取与摘要型功能重叠 |
| cover-new-style.py | cover-pipeline.py | 品牌区实现不一致（不调 draw_brand_block） |
| cover-summary.py | cover-brief.py | 摘要型功能重叠 |
| cover_styles.py | gzhkit/visual/styles.py | v3→v4 垫片，逻辑已迁入 gzhkit |
