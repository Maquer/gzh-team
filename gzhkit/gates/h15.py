#!/usr/bin/env python3
"""gzhkit.gates.h15: H15 尾图合规检查（尺寸 / 违规词 / 导流词）。

- 尺寸：高度 >800px → BLOCK；宽度非 900/1080 → WARN。
- OCR 违规词/导流词 → BLOCK；OCR 不可用 → WARN（不阻断）。
- 传入文案文本时对文案做同词表检查。
"""
import os
import subprocess

from . import register
from .. import config as C
from ..report import GateOutcome


def add_arguments(parser):
    parser.add_argument('image', nargs='?', metavar='IMG',
                        help='尾图路径')
    parser.add_argument('content', nargs='?', metavar='TEXT',
                        help='可选：伴随文案文本（做词表检查）')


def _dimensions(path):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def _ocr_text(path):
    """apple-vision OCR；CLI 缺失/失败返回 None。"""
    try:
        r = subprocess.run(
            ['apple-vision', 'ocr', str(path), '--lang', 'zh-Hans',
             '--level', 'fast'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.lower()


def _word_issues(text):
    issues = []
    for word in C.H15_PROHIBITED_WORDS:
        if word in text:
            issues.append('发现违规词: %s' % word)
    for kw in C.H15_LEAD_KEYWORDS:
        if kw in text:
            issues.append('可能导流词: %s' % kw)
    return issues


def check(args, ctx):
    """执行 H15 尾图检查。args: image/content；ctx: path 兜底。"""
    out = GateOutcome('h15')
    image = getattr(args, 'image', None) or ctx.get('path', '')

    if not image:
        out.info('H15', '未提供尾图，跳过')
        return out
    if not os.path.isfile(image):
        out.block('H15', '文件不存在: %s' % image)
        return out

    # H15-1 尺寸
    dims = _dimensions(image)
    if dims is None:
        out.warn('H15', 'Pillow 缺失或图片读取失败，尺寸检查跳过')
    else:
        w, h = dims
        out.stat('H15 尺寸', '%dx%d' % (w, h))
        if h > C.H15_MAX_HEIGHT:
            out.block('H15', 'H15-1 高度 %dpx > %dpx' % (h, C.H15_MAX_HEIGHT))
        elif w not in C.H15_ALLOWED_WIDTHS:
            out.warn('H15', 'H15-1 宽度 %dpx，建议 %s' %
                     (w, ' 或 '.join(map(str, C.H15_ALLOWED_WIDTHS))))

    # H15-2 OCR 内容
    ocr = _ocr_text(image)
    if ocr is None:
        out.warn('H15', 'H15-2 apple-vision 不可用（门禁未阻断）')
    else:
        issues = _word_issues(ocr)
        if issues:
            out.block('H15', 'H15-2 %s' % '；'.join(issues))
        else:
            out.stat('H15-2 内容', 'PASS')

    # H15-3 文案文本
    content = getattr(args, 'content', None) or ''
    if content:
        issues = _word_issues(content)
        if issues:
            out.block('H15', 'H15-3 文案 %s' % '；'.join(issues))
        else:
            out.stat('H15-3 文案', 'PASS')
    return out


register('h15', '尾图合规检查')(check)
