#!/usr/bin/env python3
# gate-H14-check.py —— 正文 H14 门禁脚本（AI 味检测）
# 判据：AI 味评分三档硬判定
#   ≤5 分 → PASS（放行）
#   6-15 分 → WARN（重写≥50%）
#   16-25 分 → WARN（明显 AI 味，建议重写）
#   >25 分 → FAIL（推倒重写）
# 来源：REVIEW.md H14 + 09-18 双模式说明
# 用法：
#   python3 gate-H14-check.py <正文.md> [--mode solo|strict] [--json]
# 退出码：
#   solo 模式：始终 0（H14 只给参考分数，不卡关产出）
#   strict 模式：0=PASS / 1=FAIL / 2=输入错误
import argparse, json, subprocess, sys, re, os

HUMANIZER = '/var/minis/shared/humanizer-check/humanizer-check.py'

# H14 判定阈值
THRESHOLD_PASS = 5
THRESHOLD_WARN_LOW = 15
THRESHOLD_WARN_HIGH = 25


def check_ai_tone(text):
    """调用 humanizer-check.py 检测 AI 味，返回 (score, raw_output)。"""
    try:
        r = subprocess.run(
            ['python3', HUMANIZER],
            input=text, capture_output=True, text=True, timeout=60)
        output = r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return None, str(e)

    # 提取分数：格式 "📊 综合评分: N 分"
    m = re.search(r'综合评分[:：]\s*(\d+)\s*分', output)
    if not m:
        return None, output

    score = int(m.group(1))
    return score, output


def judge(score, mode='strict'):
    """三档判定 + 双模式。"""
    if score is None:
        return 'FAIL', '检测失败'

    # 判定档位
    if score <= THRESHOLD_PASS:
        level, action = 'PASS', '放行'
    elif score <= THRESHOLD_WARN_LOW:
        level, action = 'WARN', '重写≥50%'
    elif score <= THRESHOLD_WARN_HIGH:
        level, action = 'WARN', '明显 AI 味，建议重写'
    else:
        level, action = 'FAIL', '推倒重写'

    # 双模式
    if mode == 'solo':
        # solo：只给参考分数，不卡关产出（对齐 REVIEW.md H14 双模式说明 09-18）
        return 'SKIP', f'{level}（solo 模式，仅参考）→ {action}'

    return level, action


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--mode', choices=['solo', 'strict'], default='solo',
                    help='solo=默认参考分不卡关；strict=三档硬判定')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    results = []
    any_fail = False

    for path in a.files:
        if not os.path.isfile(path):
            results.append({'path': path, 'score': None, 'level': 'FAIL',
                            'action': f'文件不存在: {path}'})
            any_fail = True
            continue

        text = open(path).read()
        score, raw = check_ai_tone(text)
        level, action = judge(score, a.mode)

        results.append({
            'path': path,
            'score': score,
            'level': level,
            'action': action,
        })

        if level == 'FAIL':
            any_fail = True

    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f'=== H14 门禁实测（AI 味检测，mode={a.mode}）===')
        for r in results:
            score_str = f'{r["score"]} 分' if r['score'] is not None else 'N/A'
            print(f'\n[{r["path"]}]')
            print(f'  AI 味评分: {score_str}')
            print(f'  判定: {r["level"]} → {r["action"]}')
        print(f'\n=== 门禁判定 ===')
        if any_fail:
            print('FAIL: 至少一篇正文未通过 H14 门禁（AI 味 >25 分，需推倒重写）')
        else:
            if a.mode == 'solo':
                print('SKIP: solo 模式不卡关产出（人工看分数决定是否改稿）')
            else:
                print('PASS: 全部正文通过 H14 门禁（AI 味 ≤25 分）')

    # solo 模式始终退出 0；strict 模式 FAIL 时退出 1
    if a.mode == 'solo':
        sys.exit(0)
    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
