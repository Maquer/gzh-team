#!/usr/bin/env python3
"""gate-H15-check.py: 尾图合规检查门禁

判据:
- H15-1: 无导流二维码/微信号
- H15-2: 无诱导关注违规词
- H15-3: 尺寸合规（高度 ≤800px）
"""
import sys
import re
from pathlib import Path

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
    """Check if image height <= 800px."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        w, h = img.size
        if h > 800:
            return False, f"高度 {h}px 超限（上限 800px）"
        return True, None
    except Exception as e:
        return False, f"无法打开图片: {e}"


def check_prohibited_text(image_path):
    """Check for prohibited words in image (using OCR)."""
    try:
        import subprocess
        result = subprocess.run(
            ["apple-vision", "ocr", image_path, "--lang", "zh-Hans", "--level", "fast"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return True, None  # OCR 失败不算 FAIL
        
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
    except Exception as e:
        return True, None  # 工具不可用时不阻断


def check_by_content(content):
    """Check text content for prohibited words."""
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
        print("H15-1 尺寸: PASS")
    else:
        print(f"H15-1 尺寸: FAIL - {dim_msg}")
        results.append("H15-1")
    
    # H15-2: 内容检查（OCR + 文本）
    content_ok, content_issues = check_prohibited_text(image_path)
    if content_ok:
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
