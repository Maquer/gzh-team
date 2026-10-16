# M1: video-lite.py 使用培训

**掌握标准**: 能独立生成图片轮播视频

---

## 1. 工具概述

`video-lite.py` 是 iSH 本地的图片转视频工具，无需外部服务。

**能力**:
- 图片序列 → 1080×1920 竖屏 MP4
- fade 转场效果
- PIL 水印烧入
- mov_text 软字幕轨
- FFmpeg h264 编码

**限制**:
- ❌ 无 drawtext filter → 字幕需预先叠加
- ❌ 无 subtitles filter → 字幕轨可能不保留
- ✅ 适合快速生成图片轮播视频

---

## 2. 基本用法

```bash
# 基础：图片序列 → 视频
python3 /var/minis/shared/video-lite.py \
  --images covers/ \
  --out output.mp4

# 指定参数
python3 /var/minis/shared/video-lite.py \
  --images cover1.png cover2.png cover3.png \
  --out video.mp4 \
  --duration 2.5 \
  --watermark "@弎水野记" \
  --watermark-pos bottom-right
```

---

## 3. 实操练习

### 练习 1：生成 3 张图片轮播
```bash
python3 /var/minis/shared/video-lite.py \
  --images /var/minis/attachments/ \
  --out /tmp/test-l1.mp4 \
  --duration 2 \
  --watermark "@测试"
```

---

## 4. 验收标准

- [ ] 能独立运行 video-lite.py 生成视频
- [ ] 能指定图片路径和输出路径
- [ ] 能设置水印文字和位置
- [ ] 能检查输出文件是否有效

---

## 5. 常见问题

**Q: 提示"未找到任何图片"**
A: 检查图片路径是否正确，支持 .png/.jpg/.jpeg/.webp/.gif/.bmp

**Q: 视频无法播放**
A: 检查 FFmpeg 是否正确安装：`ffmpeg -version`
