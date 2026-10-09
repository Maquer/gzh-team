#!/usr/bin/env python3
"""
gate-H12-check.py：H12 合规检查门禁（prompt 元数据/主体描述入图检测）
用法：发布前调用 python3 gate-H12-check.py <图片1> [图片2 ...] [--prompt "原始 prompt"]
关键约束：exit 0=PASS, 1=FAIL, 2=输入错误；prompt 关键词硬拦截
"""
# gate-H12-check.py —— 图片 H12 门禁独立检查脚本
# 判据：图上出现 prompt 参数（如 `ultrawide 21:9`、`no text`）或主体描述文字 → FAIL
# 来源：REVIEW.md H12 + TEAM.md §3.6 五条硬约束 #2（元数据会被画进图）
# 用法：
#   python3 gate-H12-check.py <图片1> [图片2 ...] [--title "标题" --sub "副标题"]
#          [--prompt "原始 prompt 文本"] [--json]
# 退出码：0=全绿 / 1=FAIL / 2=输入错误
import argparse, json, subprocess, sys, os
from PIL import Image

# prompt 元数据关键词（硬判据）
# 依据：TEAM.md §3.6 五条硬约束 #2 实测案例
PROMPT_META_KEYWORDS = [
    'ultrawide', 'no text', 'no watermark', 'no lettering', 'no text, no watermark',
    'aspect ratio', 'aspect-ratio', 'poster', 'image quality', 'high quality',
    'masterpiece', 'best quality', '8k', '4k', 'cinematic', 'photorealistic',
    'ultra detailed', 'hyper detailed', 'detailed', 'style', 'prompt', 'text, no',
    'watermark', 'lettering', 'subtitle', 'caption',
]

# 主体描述常见模式（软判据，WARN 而非 FAIL）
# 中文词组 ≥ 4 字 且不在标题白名单里 → WARN
SUBJECT_CN_THRESHOLD = 4


def check_ocr(path, level='fast'):
    """调用 apple-vision OCR，返回 blocks 列表；调用失败返回 None。"""
    try:
        r = subprocess.run(
            ['apple-vision', 'ocr', path, '--lang', 'zh-Hans,en', '--level', level, '-q'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout).get('blocks', []) if r.stdout.strip() else []
    except ValueError:
        return None


def check_ocr_dual(path):
    """fast 为主；accurate 只做兜底补充（accurate 在纯色区会造字，不能直接全收）。"""
    fast = check_ocr(path, 'fast')
    accurate = check_ocr(path, 'accurate')
    if fast is None and accurate is None:
        return None
    blocks = list(fast or [])
    for b in (accurate or []):
        t = b.get('text', '').strip()
        if not t:
            continue
        # accurate 兜底：prompt 关键词 + 中文主体描述（≥4 字）
        is_prompt_kw = any(kw.lower() in t.lower() for kw in PROMPT_META_KEYWORDS)
        cn_chars = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
        is_subject = cn_chars >= 4
        if is_prompt_kw or is_subject:
            blocks.append(b)
    return blocks


def is_flat(path, box, max_colors=2):
    try:
        px = list(Image.open(path).convert('RGB').crop(box).getdata())
        return len(set(px)) <= max_colors, len(set(px)), len(px)
    except Exception:
        return False, 0, 0


def check_image(path, titles=frozenset(), subs=frozenset(), prompt_text=''):
    if not os.path.isfile(path):
        return True, False, [f'文件不存在: {path}']

    blocks = check_ocr_dual(path)
    if blocks is None:
        return True, False, [f'OCR 调用失败: {path}']

    # 从 prompt 文本提取用户自定义关键词（补充 PROMPT_META_KEYWORDS）
    extra_keywords = []
    if prompt_text:
        # 提取 prompt 里的英文关键词（≥4 字符）
        import re
        extra_keywords = [w.lower() for w in re.findall(r'\b[a-z]{4,}\b', prompt_text.lower())
                          if w.lower() not in PROMPT_META_KEYWORDS]

    all_keywords = PROMPT_META_KEYWORDS + extra_keywords

    fail = False
    warn = False
    details = []

    for b in blocks:
        t = b.get('text', '').strip()
        t_lower = t.lower()
        if not t:
            continue

        # 白名单：完整匹配或子串匹配（OCR 常检出片段如 "Skill" 来自完整标题）
        all_titles = list(titles | subs)
        if any(t in full or full in t for full in all_titles):
            details.append(f'✓ [{t}] 自加文字（白名单）')
            continue

        # 幻觉放行（conf < 0.5 + flat 区域）
        x, y, w, h = b.get('bbox', (0, 0, 0, 0))
        img = Image.open(path)
        W, H = img.size
        box = (int(x * W), int(y * H), int((x + w) * W), int((y + h) * H))
        flat, ncol, npx = is_flat(path, box)
        conf = b.get('confidence', 1.0)

        if conf < 0.5 and flat:
            details.append(f'⚠ [{t}] conf={conf:.2f} 纯色区 {ncol} 色/{npx}px → OCR 幻觉')
            continue

        # 硬判据：prompt 关键词
        kw_hit = [kw for kw in all_keywords if kw in t_lower]
        if kw_hit:
            fail = True
            details.append(f'✗ [{t}] 命中 prompt 关键词 {kw_hit} → 元数据被画进图')
            continue

        # 软判据：中文主体描述（≥4 字，非幻觉、非白名单）
        cn_chars = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
        if cn_chars >= SUBJECT_CN_THRESHOLD:
            warn = True
            details.append(f'⚠ [{t}] {cn_chars} 个中文字 → 可能是主体描述被画进图，人工确认')

    return fail, warn, details


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('images', nargs='+')
    ap.add_argument('--title', default='')
    ap.add_argument('--sub', default='')
    ap.add_argument('--prompt', default='', help='原始 prompt 文本（自动提取关键词）')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    titles = {a.title} if a.title else set()
    subs = {a.sub} if a.sub else set()

    results = []
    any_fail = False
    any_warn = False
    for p in a.images:
        fail, warn, details = check_image(p, titles, subs, a.prompt)
        results.append({'path': p, 'fail': fail, 'warn': warn, 'details': details})
        if fail:
            any_fail = True
        if warn:
            any_warn = True

    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print('=== H12 门禁实测（prompt 元数据/主体描述入图）===')
        for r in results:
            print(f'\n[{r["path"]}]')
            for d in r['details']:
                print(f'  {d}')
            if not r['details']:
                print('  （空）')
            status = 'FAIL' if r['fail'] else ('PASS_WITH_WARN' if r['warn'] else 'PASS')
            print(f'  → {status}')
        print('\n=== 门禁判定 ===')
        if any_fail:
            print('FAIL: 至少一张图片命中 prompt 关键词（元数据被画进图）')
        elif any_warn:
            print('PASS_WITH_WARN: 检出可能的主題描述入图，人工确认')
        else:
            print('PASS: 全部图片通过 H12 门禁')

    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
