#!/usr/bin/env python3
"""
gate-G7-check.py：发布前检查门禁（十项清单脚本化）
用法：发布前调用 python3 gate-G7-check.py <稿件.md> [--cover 封面.jpg]
关键约束：exit 0=PASS, 1=FAIL, 2=输入错误；strict 模式须 --broadcast-ok
"""
# gate-G7-check.py —— G7 发布门禁自动检查脚本
# 判据来源：TEAM.md §3.7 发布岗 G7 十项清单
# 可自动判定：标题字数/封面尺寸/金句数量/防盗链/互动钩子/AI味分数/OCR
# 人工项：后台预览/AI声明开关/24h pre-mortem
# 用法：python3 gate-G7-check.py <稿件.md> [--cover 封面.jpg] [--html 排版稿.html] [--review 审核结论.md] [--json] [--strict]
# 退出码：0=全绿 / 1=FAIL / 2=输入错误
import sys, re, os, json, argparse, subprocess

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('markdown', help='稿件 Markdown 路径')
    ap.add_argument('--cover', help='封面图路径')
    ap.add_argument('--html', help='排版稿 HTML 路径')
    ap.add_argument('--review', help='05 审核结论路径（含 AI 味分数）')
    ap.add_argument('--json', action='store_true', help='JSON 输出')
    ap.add_argument('--strict', action='store_true', help='全部 PASS 才退出 0')
    ap.add_argument('--broadcast-ok', action='store_true',
                   help='v2.5.0 G7-11：显式确认「群发开关已开启」。strict 模式下缺省即 FAIL')
    ap.add_argument('--comment-enabled', action='store_true',
                   help='v2.5.2 G7-5b：显式确认「评论功能已开启」。strict 模式下缺省即 FAIL')
    ap.add_argument('--label', default='',
                   help='v2.5.0 G7-12：账号健康追踪文件路径（默认 docs/account-health-label.md）')
    args = ap.parse_args()

    if not os.path.isfile(args.markdown):
        print(f'ERROR: 文件不存在 {args.markdown}', file=sys.stderr)
        sys.exit(2)

    t = open(args.markdown).read()
    html = open(args.html).read() if args.html and os.path.isfile(args.html) else ''
    review = open(args.review).read() if args.review and os.path.isfile(args.review) else ''

    results = []
    fails = []

    # ── 1. 标题字数（15-30 字）──
    title_match = re.search(r'^#\s+(.+)$', t, re.M)
    if title_match:
        title = title_match.group(1).strip()
        zh_count = len(re.findall(r'[\u4e00-\u9fff]', title))
        status = 'PASS' if 15 <= zh_count <= 30 else 'FAIL'
        detail = f'{zh_count} 字（要求 15-30）'
        results.append({'项': '标题字数', '状态': status, '依据': detail})
        if status == 'FAIL':
            fails.append(f'标题 {zh_count} 字，要求 15-30')
    else:
        results.append({'项': '标题字数', '状态': 'FAIL', '依据': '无标题'})
        fails.append('无标题')

    # ── 2. 封面尺寸（900×383）──
    if args.cover:
        if os.path.isfile(args.cover):
            try:
                r = subprocess.run(['identify', args.cover], capture_output=True, text=True, timeout=10)
                dims = r.stdout.strip()
                w, h = 0, 0
                for d in dims.split():
                    m = re.match(r'(\d+)x(\d+)', d)
                    if m:
                        w, h = int(m.group(1)), int(m.group(2))
                        break
                status = 'PASS' if w == 900 and h == 383 else 'FAIL'
                detail = f'{w}x{h}（要求 900x383）'
                results.append({'项': '封面尺寸', '状态': status, '依据': detail})
                if status == 'FAIL':
                    fails.append(f'封面 {w}x{h}，要求 900x383')
            except Exception as e:
                results.append({'项': '封面尺寸', '状态': 'FAIL', '依据': f'检测失败: {e}'})
                fails.append('封面检测失败')
        else:
            results.append({'项': '封面尺寸', '状态': 'FAIL', '依据': f'文件不存在 {args.cover}'})
            fails.append('封面文件不存在')
    else:
        results.append({'项': '封面尺寸', '状态': 'SKIP', '依据': '未提供 --cover'})

    # ── 3. 金句数量（≥1 加粗）──
    bold_count = len(re.findall(r'\*\*[^*]+\*\*', t))
    status = 'PASS' if bold_count >= 1 else 'FAIL'
    detail = f'{bold_count} 处加粗（要求 ≥1）'
    results.append({'项': '金句数量', '状态': status, '依据': detail})
    if status == 'FAIL':
        fails.append(f'金句 {bold_count} 处，要求 ≥1')

    # ── 4. 防盗链注入 ──
    if html:
        has_referrer = 'referrerpolicy' in html.lower() or 'referrer' in html.lower()
        has_img = '<img' in html.lower()
        if has_img and not has_referrer:
            status = 'FAIL'
            detail = 'HTML 中有 <img> 但无 referrerpolicy'
        elif has_referrer:
            status = 'PASS'
            detail = '已注入 referrerpolicy'
        else:
            status = 'SKIP'
            detail = 'HTML 中无 <img>'
        results.append({'项': '防盗链注入', '状态': status, '依据': detail})
        if status == 'FAIL':
            fails.append('防盗链未注入')
    else:
        results.append({'项': '防盗链注入', '状态': 'SKIP', '依据': '未提供 --html'})

    # ── 5. 互动钩子 ──
    hook_keywords = ['你', '评论', '留言', '怎么', '如何', '你觉得', '分享', '投票', '填']
    has_hook = any(kw in t for kw in hook_keywords)
    status = 'PASS' if has_hook else 'FAIL'
    detail = '找到互动关键词' if has_hook else '未找到互动钩子'
    results.append({'项': '互动钩子', '状态': status, '依据': detail})
    if status == 'FAIL':
        fails.append('无互动钩子')

    # ── 5b. 评论功能开启状态（v2.5.2 新增 · 09-25 评论开关未开→互动=0 事故）──
    has_comment = getattr(args, 'comment_enabled', False)
    if args.strict and not has_comment:
        results.append({'项': '评论功能', '状态': 'FAIL',
                       '依据': '须传 --comment-enabled 显式确认（后台评论功能是否已开启）'})
        fails.append('未提供 --comment-enabled 确认（评论功能是否已开启）')
    else:
        results.append({'项': '评论功能', '状态': 'PASS' if args.strict else 'SKIP',
                       '依据': '已显式确认 --comment-enabled' if args.strict else '非 strict 模式默认跳过'})

    # ── 6. AI 味分数 ──
    if review:
        ai_match = re.search(r'AI\s*味[^\d]*(\d+)', review, re.I)
        if ai_match:
            score = int(ai_match.group(1))
            if score <= 5:
                status = 'PASS'
                detail = f'{score} 分（≤5 放行）'
            elif score <= 15:
                status = 'WARN'
                detail = f'{score} 分（6-15 需重写≥50%）'
            elif score <= 25:
                status = 'WARN'
                detail = f'{score} 分（16-25 需重写≥50%）'
            else:
                status = 'FAIL'
                detail = f'{score} 分（>25 需推倒重写）'
        else:
            status = 'SKIP'
            detail = '审核结论中无 AI 味分数'
    else:
        status = 'SKIP'
        detail = '未提供 --review'
    results.append({'项': 'AI 味分数', '状态': status, '依据': detail})
    if status == 'FAIL':
        fails.append(f'AI 味 {score} 分 >25，需推倒重写')

    # ── 7. OCR 检查（封面）──
    if args.cover and os.path.isfile(args.cover):
        try:
            r = subprocess.run(
                ['apple-vision', 'ocr', args.cover, '--lang', 'zh-Hans,en', '--level', 'fast', '-q'],
                capture_output=True, text=True, timeout=60)
            blocks = json.loads(r.stdout).get('blocks', []) if r.stdout else []
            chinese_texts = [b.get('text','') for b in blocks if re.search(r'[\u4e00-\u9fff]', b.get('text',''))]
            if chinese_texts:
                status = 'FAIL'
                detail = f'检测到 {len(chinese_texts)} 处中文: {" / ".join(chinese_texts[:3])}'
            else:
                status = 'PASS'
                detail = '无中文残留'
            results.append({'项': 'OCR 中文检查', '状态': status, '依据': detail})
            if status == 'FAIL':
                fails.append('封面有中文残留')
        except Exception as e:
            results.append({'项': 'OCR 中文检查', '状态': 'SKIP', '依据': f'检测失败: {e}'})
    else:
        results.append({'项': 'OCR 中文检查', '状态': 'SKIP', '依据': '未提供 --cover'})

    # ── 8-10. 人工项 ──
    for name, desc in [
        ('后台预览', '人工确认'),
        ('AI 声明开关', '人工确认'),
        ('24h pre-mortem', '人工确认')
    ]:
        results.append({'项': name, '状态': 'SKIP', '依据': desc})

    # ── 11. 群发开关（v2.5.0 新增 · 09-25 三篇全绿但阅读=0 的根因）──
    has_broadcast = getattr(args, 'broadcast_ok', False)
    if args.strict and not has_broadcast:
        results.append({'项': '群发开关', '状态': 'FAIL', '依据': '须传 --broadcast-ok 显式确认（v2.5.0 起 G7 第 11 项）'})
        fails.append('未提供 --broadcast-ok 确认（群发开关是否已开启）')
    else:
        results.append({'项': '群发开关', '状态': 'PASS' if args.strict else 'SKIP',
                       '依据': '已显式确认 --broadcast-ok' if args.strict else '非 strict 模式默认跳过'})

    # ── 12. 账号健康状态（v2.5.0 新增 · 读 docs/account-health-label.md）──
    _dir = os.path.dirname(os.path.abspath(__file__))
    label_path = args.label or os.path.join(_dir, 'docs', 'account-health-label.md')
    label_rel = args.label or 'docs/account-health-label.md'
    if os.path.isfile(label_path):
        label = open(label_path, encoding='utf-8').read()
        has_red = '🔴' in label
        has_pending = ('⏳ 待查' in label) or ('⏳ 待用户' in label)
        if has_red and has_pending:
            results.append({'项': '账号健康状态', '状态': 'FAIL',
                           '依据': f'读 {label_rel}：标签未解除（🔴 + ⏳ 待查）→ 常规发布暂停'})
            fails.append(f'账号健康状态 FAIL：{label_rel} 显示 🔴 + 待查，常规发布不放行')
        elif has_red:
            results.append({'项': '账号健康状态', '状态': 'FAIL',
                           '依据': f'读 {label_rel}：🔴 标签仍在，常规发布暂停'})
            fails.append('账号健康状态 FAIL：🔴 标签仍在，常规发布不走此门禁')
        else:
            results.append({'项': '账号健康状态', '状态': 'PASS',
                           '依据': f'读 {label_rel}：无 🔴 且无待查，标签已解除或无记录'})
    else:
        results.append({'项': '账号健康状态', '状态': 'SKIP',
                       '依据': f'{label_path} 不存在（新团队首次跑可忽略）'})

    # ── 输出 ──
    pass_count = sum(1 for r in results if r['状态'] == 'PASS')
    fail_count = sum(1 for r in results if r['状态'] == 'FAIL')
    skip_count = sum(1 for r in results if r['状态'] == 'SKIP')
    warn_count = sum(1 for r in results if r['状态'] == 'WARN')

    if args.json:
        print(json.dumps({'pass': pass_count, 'fail': fail_count, 'warn': warn_count, 'skip': skip_count, 'results': results}, ensure_ascii=False, indent=2))
    else:
        print('G7 发布门禁检查')
        print(f'{"─"*50}')
        for r in results:
            icon = {'PASS': '✅', 'FAIL': '❌', 'WARN': '⚠️', 'SKIP': '⏭️'}.get(r['状态'], '❓')
            print(f'{icon} {r["项"]}: {r["依据"]}')
        print(f'{"─"*50}')
        print(f'PASS: {pass_count} | FAIL: {fail_count} | WARN: {warn_count} | SKIP: {skip_count}')
        if fails:
            print('\n❌ FAIL 项:')
            for f in fails:
                print(f'  - {f}')

    sys.exit(1 if (fail_count > 0 or (args.strict and warn_count > 0)) else 0)

if __name__ == '__main__':
    main()