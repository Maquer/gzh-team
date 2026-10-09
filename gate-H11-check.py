#!/usr/bin/env python3
"""
gate-H11-check.py：H11 合规检查门禁（图片中文残留/水印检测）
用法：发布前调用 python3 gate-H11-check.py <图片1> [图片2 ...] [--title "标题"]
关键约束：exit 0=PASS, 1=FAIL, 2=输入错误；水印关键词硬拦截
"""
# gate-H11-check.py —— 图片 H11 门禁独立检查脚本
# 判据：封面/配图含可读中文（除标题白名单外）或水印关键词残留 → FAIL
# 来源：REVIEW.md H11 + TEAM.md §3.6 五条硬约束 #1（图上中文必错字）
# 用法：
#   python3 gate-H11-check.py <图片1> [图片2 ...] [--title "标题" --sub "副标题"] [--json]
# 退出码：0=全绿 / 1=FAIL / 2=输入错误
import argparse, json, subprocess, sys, os
from PIL import Image

# 水印关键词硬拦截（对齐 cover-pipeline.py 常量）
WATERMARK_KEYWORDS = ['AI生成', 'AI 生成', '日日新', 'sensenova', '即梦', 'jimeng', 'SENSENOVA']

# 幻觉放行阈值（对齐 cover-pipeline.py 但调高到 0.6）
# 单字符 OCR 噪声 conf 通常 0.3-0.5，真实中文残留 conf 通常 >0.7
# 0.6 阈值让边界样本走 WARN（人工确认），不误拦真实水印关键词（水印已前置硬拦截）
CONF_THRESHOLD = 0.6
FLAT_MAX_COLORS = 2


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
    accurate_wm = []
    seen = {b.get('text', '').strip() for b in blocks}
    for b in (accurate or []):
        t = b.get('text', '').strip()
        if t and t not in seen and any(kw.lower() in t.lower() for kw in WATERMARK_KEYWORDS):
            accurate_wm.append(b)
    blocks.extend(accurate_wm)
    return blocks


def is_flat(path, box, max_colors=FLAT_MAX_COLORS):
    """区域颜色数 ≤ max_colors 视为纯色区（OCR 在纯色区的检出多为幻觉）。"""
    try:
        px = list(Image.open(path).convert('RGB').crop(box).getdata())
        return len(set(px)) <= max_colors, len(set(px)), len(px)
    except Exception:
        return False, 0, 0


def check_image(path, titles=frozenset(), subs=frozenset()):
    """返回 (fail, warn, details)。"""
    if not os.path.isfile(path):
        return True, False, [f'文件不存在: {path}']

    blocks = check_ocr_dual(path)
    if blocks is None:
        return True, False, [f'OCR 调用失败: {path}']

    fail = False
    warn = False
    details = []

    # 标题白名单：OCR 检出文字是标题子串或标题包含它 → 放行
    all_titles = list(titles | subs)

    for b in blocks:
        t = b.get('text', '').strip()
        if not t:
            continue

        # 白名单：完整匹配或子串匹配（OCR 常检出片段如 "Skill" 来自完整标题）
        if any(t in full or full in t for full in all_titles):
            details.append(f'✓ [{t}] 自加文字（白名单）')
            continue

        # 水印关键词硬拦截（绕过幻觉放行）
        wm_hit = [kw for kw in WATERMARK_KEYWORDS if kw.lower() in t.lower()]
        if wm_hit:
            fail = True
            details.append(f'✗ [{t}] 命中水印关键词 {wm_hit} → 去水印不彻底')
            continue

        # 置信度判断（对齐 REVIEW.md H11 硬约束）
        conf = b.get('confidence', 1.0)
        if conf < CONF_THRESHOLD:
            # conf < CONF_THRESHOLD → WARN（可能是幻觉，人工确认；水印关键词已前置拦截）
            warn = True
            details.append(f'⚠ [{t}] conf={conf:.2f} <{CONF_THRESHOLD} → 疑似 OCR 幻觉，人工确认')
        else:
            fail = True
            details.append(f'✗ [{t}] conf={conf:.2f} ≥{CONF_THRESHOLD} → 真实中文残留，H11 未过')

    return fail, warn, details


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('images', nargs='+')
    ap.add_argument('--title', default='', help='标题白名单')
    ap.add_argument('--sub', default='', help='副标题白名单')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    titles = {a.title} if a.title else set()
    subs = {a.sub} if a.sub else set()

    results = []
    any_fail = False
    for p in a.images:
        fail, warn, details = check_image(p, titles, subs)
        results.append({'path': p, 'fail': fail, 'warn': warn, 'details': details})
        if fail:
            any_fail = True

    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print('=== H11 门禁实测（图片中文/水印残留）===')
        for r in results:
            print(f'\n[{r["path"]}]')
            for d in r['details']:
                print(f'  {d}')
            if not r['details']:
                print('  （空）')
            print(f'  → {"FAIL" if r["fail"] else "PASS"}')
        print('\n=== 门禁判定 ===')
        print('FAIL: 至少一张图片未通过 H11 门禁（中文残留或水印关键词残留）' if any_fail
              else 'PASS: 全部图片通过 H11 门禁')

    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
