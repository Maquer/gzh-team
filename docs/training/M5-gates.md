# M5: 视频门禁检查培训

**掌握标准**: 能运行 H16-H18 门禁并处理 FAIL

---

## 1. 新增门禁

| 编号 | 名称 | 检查项 | 阻断条件 |
|------|------|--------|---------|
| H16 | 视频格式校验 | MP4/WebM、h264 | 格式错误 |
| H17 | 视频时长检查 | ≤60 秒 | 超时 |
| H18 | 文件大小检查 | ≤50MB | 超限 |

---

## 2. 使用方法

```bash
python3 /var/minis/shared/gzh-video.py check --file video.mp4
```

---

## 3. 故障处理

### H17 FAIL: 时长超限
```bash
ffmpeg -i input.mp4 -t 60 -c copy output.mp4
```

### H18 FAIL: 文件过大
```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 output.mp4
```
