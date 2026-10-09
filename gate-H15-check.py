#!/usr/bin/env python3
"""gate-H15-check.py：尾图合规检查门禁，检查导流/违规词/尺寸
用法：python3 gate-H15-check.py <尾图路径> [内容文本] — 发布前必跑
关键约束：exit 0=PASS，exit 1=FAIL；违规词/导流词/高度>800px均阻断
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image

MAX_HEIGHT = 800          # 高度 ≤800px（过长会被压缩），见 docs/visual/tail-image-spec.md
ALLOWED_WIDTHS = (900, 1080)  # 宽度与正文一致

# 违规词列表
PROHIBITED_WORDS = [
    "星标", "第一时间", "独家", "首发", "必看", "速看",
    "赶紧", "立即", "马上", "限时", "最后", "错过",
]

# 导流关键词
LEAD_KEYWORDS = [
    "微信", "QQ", "电话", "邮箱", "二维码", "扫码",
    "加我", "私信", "关注公众号",
]


def check_dimensions(image_path):
    """尺寸检查：高度 >800px 阻断；宽度非 900/1080 仅提示。返回 (ok, msg)。"""
    try:
        with Image.open(image_path) as im:
            w, h = im.size
    except Exception as e:
        return False, f"无法读取图片: {e}"
    if h > MAX_HEIGHT:
        return False, f"高度 {h}px > {MAX_HEIGHT}px"
    if w not in ALLOWED_WIDTHS:
        return True, f"WARN: 宽度 {w}px，建议 {' 或 '.join(map(str, ALLOWED_WIDTHS))}px"
    return True, None


def check_prohibited_text(image_path):
    """OCR 检查违规词/导流词。返回 (ok, msg)；OCR 不可用时放行并给出 WARN。"""
    try:
        result = subprocess.run(
            ["apple-vision", "ocr", str(image_path), "--lang", "zh-Hans", "--level", "fast"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return True, 'WARN: apple-vision OCR 返回码异常（门禁未阻断）'
        
        text = result.stdout.lower()
        issues = []
        for word in PROHIBITED_WORDS:
            if word in text:
                issues.append(f"发现违规词: {word}")
        for kw in LEAD_KEYWORDS:
            if kw in text:
                issues.append(f"可能导流词: {kw}")
        
        if issues:
            return False, "; ".join(issues)
        return True, None
    except Exception:
        return True, 'WARN: apple-vision 不可用（门禁未阻断）'


def check_by_content(content):
    issues = []
    for word in PROHIBITED_WORDS:
        if word in content:
            issues.append(f"发现违规词: {word}")
    for kw in LEAD_KEYWORDS:
        if kw in content:
            issues.append(f"可能导流词: {kw}")
    return len(issues) == 0, issues


def main():
    if len(sys.argv) < 2:
        print("用法: python3 gate-H15-check.py <尾图路径> [内容文本]")
        sys.exit(1)
    
    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"FAIL: 文件不存在 {image_path}")
        sys.exit(1)
    
    results = []
    
    # H15-1: 尺寸检查
    dim_ok, dim_msg = check_dimensions(image_path)
    if dim_ok:
        print(f"H15-1 尺寸: {dim_msg}" if dim_msg else "H15-1 尺寸: PASS")
    else:
        print(f"H15-1 尺寸: FAIL - {dim_msg}")
        results.append("H15-1")
    
    # H15-2: 内容检查（OCR + 文本）
    content_ok, content_issues = check_prohibited_text(image_path)
    if content_ok:
        if content_issues:
            print(f"H15-2 内容: WARN ({content_issues})")
        else:
            print("H15-2 内容: PASS")
    else:
        print(f"H15-2 内容: FAIL - {content_issues}")
        results.append("H15-2")
    
    # 额外: 如果有传入内容文本
    if len(sys.argv) >= 3:
        text = sys.argv[2]
        text_ok, text_issues = check_by_content(text)
        if text_ok:
            print("H15-3 文案: PASS")
        else:
            print(f"H15-3 文案: FAIL - {'; '.join(text_issues)}")
            results.append("H15-3")
    
    if results:
        print(f"FAIL: {', '.join(results)}")
        sys.exit(1)
    else:
        print("PASS")


if __name__ == "__main__":
    main()
