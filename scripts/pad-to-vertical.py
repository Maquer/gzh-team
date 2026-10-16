#!/usr/bin/env python3
"""把 1080×1440 视觉卡填充到 1080×1920（视频号 9:16 竖屏）。

上下用品牌纸面色填充，居中放置原卡。
"""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, '/var/minis/shared/gzh-team')
from gzhkit.visual import canvas as C

SRC = '/var/minis/shared/gzh-team/选题库/deepseek-fault-compensation-20261015/视觉卡'
DST = '/var/minis/shared/gzh-team/选题库/deepseek-fault-compensation-20261015/视觉卡-竖屏'
os.makedirs(DST, exist_ok=True)

W, H = 1080, 1920
PAD_TOP = (H - 1440) // 2  # 240

for f in sorted(os.listdir(SRC)):
    if not f.endswith('.png'):
        continue
    img = Image.open(os.path.join(SRC, f)).convert('RGB')
    canvas = Image.new('RGB', (W, H), C.PAPER)
    d = ImageDraw.Draw(canvas)
    # 上下填充区加一条品牌红细线作视觉过渡
    d.rectangle([0, PAD_TOP - 3, W, PAD_TOP], fill=C.RED)
    d.rectangle([0, PAD_TOP + 1440, W, PAD_TOP + 1440 + 3], fill=C.RED)
    canvas.paste(img, (0, PAD_TOP))
    out = os.path.join(DST, f)
    canvas.save(out, quality=95)
    print(f'[OK] {out}')

print(f'\n→ {len(os.listdir(DST))} 张竖屏卡 → {DST}')
