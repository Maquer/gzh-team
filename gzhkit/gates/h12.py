#!/usr/bin/env python3
"""gzhkit.gates.h12: H12 prompt 元数据检查（prompt 关键词/主体描述入图）。

判据：图上出现 prompt 参数（如 ultrawide 21:9、no text）或主体描述文字。
prompt 关键词命中 → BLOCK；中文主体描述（≥4 字）→ WARN。
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
    parser.add_argument('--prompt', default='',
                        help='原始 prompt 文本（自动提取关键词）')


def _ocr(path, level='fast'):
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
    fast = _ocr(path, 'fast')
    accurate = _ocr(path, 'accurate')
    if fast is None and accurate is None:
        return None
    blocks = list(fast or [])
    for b in (accurate or []):
        txt = b.get('text', '').strip()
        if not txt:
            continue
        is_kw = any(kw.lower() in txt.lower()
                    for kw in C.H12_PROMPT_META_KEYWORDS)
        cn = sum(1 for ch in txt if '\u4e00' <= ch <= '\u9fff')
        if is_kw or cn >= C.H12_SUBJECT_CN_MIN:
            blocks.append(b)
    return blocks


def _check_image(path, titles, subs, keywords):
    if not os.path.isfile(path):
        return True, False, ['✗ 文件不存在: %s' % path]

    blocks = _ocr_dual(path)
    if blocks is None:
        # v3.3.0 口径：OCR 失败 → FAIL（与 h11 的 WARN 降级不同）
        return True, False, ['✗ OCR 调用失败: %s' % path]

    fail, warn, details = False, False, []
    whitelist = list(titles | subs)
    for b in blocks:
        txt = b.get('text', '').strip()
        low = txt.lower()
        if not txt:
            continue
        # 白名单
        if any(txt in full or full in txt for full in whitelist):
            details.append('✓ [%s] 自加文字（白名单）' % txt)
            continue
        # 幻觉放行：低置信度中文检出不单独计（简化 v3.3.0 纯色区判断）
        conf = b.get('confidence', 1.0)
        # 硬判据：prompt 关键词
        hits = [kw for kw in keywords if kw in low]
        if hits:
            fail = True
            details.append('✗ [%s] 命中 prompt 关键词 %s → 元数据被画进图'
                           % (txt, hits))
            continue
        # 软判据：中文主体描述 ≥4 字
        cn = sum(1 for ch in txt if '\u4e00' <= ch <= '\u9fff')
        if cn >= C.H12_SUBJECT_CN_MIN and conf >= C.H12_HALLUC_CONF:
            warn = True
            details.append('⚠ [%s] %d 个中文字 → 可能是主体描述入图，人工确认'
                           % (txt, cn))
    return fail, warn, details


def check(args, ctx):
    """执行 H12 检查。args: images/title/sub/prompt。"""
    out = GateOutcome('h12')
    images = getattr(args, 'images', []) or []
    if not images:
        out.info('H12', '未提供图片，跳过')
        return out

    # prompt 文本补充关键词
    prompt = getattr(args, 'prompt', '') or ''
    extra = [w for w in re.findall(r'\b[a-z]{4,}\b', prompt.lower())
             if w not in C.H12_PROMPT_META_KEYWORDS]
    keywords = C.H12_PROMPT_META_KEYWORDS + extra

    titles = {getattr(args, 'title', '')} if getattr(args, 'title', '') else set()
    subs = {getattr(args, 'sub', '')} if getattr(args, 'sub', '') else set()

    for path in images:
        fail, warn, details = _check_image(path, titles, subs, keywords)
        for d in details:
            if d.startswith('✗'):
                out.block('H12', '[%s] %s' % (os.path.basename(path), d[2:]))
            elif d.startswith('⚠'):
                out.warn('H12', '[%s] %s' % (os.path.basename(path), d[2:]))
            else:
                out.info('H12', '[%s] %s' % (os.path.basename(path), d[2:]))
        out.stat('H12 %s' % os.path.basename(path),
                 'FAIL' if fail else ('WARN' if warn else 'PASS'))
    return out


register('h12', 'prompt 元数据检查')(check)
