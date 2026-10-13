#!/usr/bin/env python3
"""gzhkit.gates.h11: H11 图片 OCR 门禁（图片中文残留/水印检测）。

apple-vision CLI 缺失时记 WARN Finding，不抛异常。
水印关键词命中 → BLOCK；低置信度中文检出 → WARN（疑似幻觉）。
"""
import json
import os
import re
import subprocess

from . import register
from .. import config as C
from ..report import GateOutcome


def add_arguments(parser):
    parser.add_argument('images', nargs='*', metavar='IMG',
                        help='待检查的图片路径（可多张）')
    parser.add_argument('--title', default='', help='标题白名单')
    parser.add_argument('--sub', default='', help='副标题白名单')


def _ocr(path, level='fast'):
    """apple-vision OCR；CLI 缺失/超时/解析失败返回 None。"""
    try:
        r = subprocess.run(
            ['apple-vision', 'ocr', path, '--lang', 'zh-Hans,en',
             '--level', level, '-q'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get('blocks', []) if r.stdout.strip() else []
    except ValueError:
        return None


def _ocr_dual(path):
    """fast 为主；accurate 只做水印关键词兜底补充。"""
    fast = _ocr(path, 'fast')
    accurate = _ocr(path, 'accurate')
    if fast is None and accurate is None:
        return None
    blocks = list(fast or [])
    seen = {b.get('text', '').strip() for b in blocks}
    for b in (accurate or []):
        txt = b.get('text', '').strip()
        if txt and txt not in seen and any(
                kw.lower() in txt.lower() for kw in C.H11_WATERMARK_KEYWORDS):
            blocks.append(b)
    return blocks


def _check_image(path, titles, subs):
    """返回 (blocks 可用?, fail, warn, details)。"""
    if not os.path.isfile(path):
        return True, True, False, ['文件不存在: %s' % path]

    blocks = _ocr_dual(path)
    if blocks is None:
        # apple-vision CLI 缺失 → WARN，不抛异常（v4 降级，不再硬 FAIL）
        return False, False, True, ['apple-vision 不可用或 OCR 失败：跳过（WARN，不阻断）']

    fail, warn, details = False, False, []
    whitelist = list(titles | subs)
    for b in blocks:
        txt = b.get('text', '').strip()
        if not txt:
            continue
        # 白名单：自加标题文字放行
        if any(txt in full or full in txt for full in whitelist):
            details.append('✓ [%s] 自加文字（白名单）' % txt)
            continue
        # 水印关键词硬拦截
        wm = [kw for kw in C.H11_WATERMARK_KEYWORDS if kw.lower() in txt.lower()]
        if wm:
            fail = True
            details.append('✗ [%s] 命中水印关键词 %s → 去水印不彻底' % (txt, wm))
            continue
        # 置信度分级
        conf = b.get('confidence', 1.0)
        if conf < C.H11_CONF_THRESHOLD:
            warn = True
            details.append('⚠ [%s] conf=%.2f <%.2f → 疑似 OCR 幻觉，人工确认'
                           % (txt, conf, C.H11_CONF_THRESHOLD))
        else:
            fail = True
            details.append('✗ [%s] conf=%.2f ≥%.2f → 真实中文残留'
                           % (txt, conf, C.H11_CONF_THRESHOLD))
    return True, fail, warn, details


def check(args, ctx):
    """执行 H11 图片 OCR 检查。args: images/title/sub。"""
    out = GateOutcome('h11')
    images = getattr(args, 'images', []) or []
    if not images:
        out.info('H11', '未提供图片，跳过')
        return out

    titles = {getattr(args, 'title', '')} if getattr(args, 'title', '') else set()
    subs = {getattr(args, 'sub', '')} if getattr(args, 'sub', '') else set()

    for path in images:
        ok, fail, warn, details = _check_image(path, titles, subs)
        for d in details:
            if d.startswith('✗'):
                out.block('H11', '[%s] %s' % (os.path.basename(path), d[2:]))
            elif d.startswith('⚠'):
                out.warn('H11', '[%s] %s' % (os.path.basename(path), d[2:]))
            else:
                out.info('H11', '[%s] %s' % (os.path.basename(path), d[2:]))
        out.stat('H11 %s' % os.path.basename(path),
                 'FAIL' if fail else ('WARN' if warn else 'PASS'))
    return out


register('h11', '图片 OCR（中文残留/水印）')(check)
