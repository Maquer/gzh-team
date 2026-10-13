#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G5 岗位能力考核脚本 —— 公众号团队培训体系度量层。

v4.0.0 重建：结构清理（argparse 统一 CLI / 退出码 0/1/2 / 缺依赖提示），
判定逻辑与 v3.3.0 逐字保留。

用法:
  python3 train-check.py <稿件.md>                  # 文本报告
  python3 train-check.py <稿件.md> --json            # JSON（供 train-verify 消费）
  python3 train-check.py <稿件.md> --track 速评      # 速评轨：豁免 H8 字数门槛
  python3 train-check.py <稿件.md> --no-humanizer     # 跳过 AI 味外部调用
  python3 train-check.py <稿件.md> --mode strict      # 审核岗/发布前：H14 三档硬判定
  python3 train-check.py <排期表.md> --role 06-负责人   # 负责人产出考核

退出码：0 全部达标（--json 恒为 0）；1 有未达标项；2 参数错误 / 文件不可读。
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gzhkit import cli as gzh_cli

GZH_TEAM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.environ.get('GZH_SHARED_DIR', os.path.dirname(GZH_TEAM))

HUMANIZER = os.path.join(SHARED_DIR, "humanizer-check", "humanizer-check.py")

BODY_RE = re.compile(r'##\s*正文(.*?)(?=\n#{2,3}\s*(配图|缺口判断|AI 参与|自检|结尾|发布))', re.S)
ZH_RE = re.compile(r'[\u4e00-\u9fff]')
BANNED = ['首先', '其次', '此外', '总而言之', '不可否认', '需要关注的是', '接下来',
          '需要注意的是', '换句话说']
URGENCY = ['速看', '马上删', '惊呆了', '震惊', '必看', '全网首个', '全网第一']
URGENCY_SOFT = ['立即', '紧急', '限时']
META = ['这里多余', '刚才说', '删掉。', '多余，删']
TITLE_STRATEGY_RE = re.compile(
    r'(?:\uff08|\u3010|——\s*|-{2,}\s*|：\s*)([^\u3011\n（（：,，]*?(?:缺口|冲击|共鸣|反常识|货币)[^\u3011\n（（：,，]*?)(?:\uff09|\u3011|$)', re.M)

REQUIRED_SECTIONS = ['备选标题', '正文', '结尾', 'AI 参与']
PACKAGE_MARKERS = ['备选标题', 'AI 参与', '交付前自检', '配图指导', '已选标题']
DEFAULT_MIN_WORDS = 800
EXPRESS_MIN_WORDS = 500

HUMANIZER_LIMITS = {"放行": 5, "重写": 15}


def detect_kind(text):
    """完整稿件含包装节；正文片段（clean 版）只有内容小节，不该判包装节结构"""
    return "完整稿件" if any(m in text for m in PACKAGE_MARKERS) else "正文片段"


def _extract_body(text):
    m = BODY_RE.search(text)
    return m.group(1) if m else text


def _sentences(p):
    return len([x for x in re.split(r'[。！？；]',
                 re.sub(r'\*\*|【金句】', '', p)) if x.strip()])


def check_structure(text, expected=None):
    """H10 输出结构漂移：任一必需节缺失，或整篇无 markdown 标题（纯文本输出）"""
    expected = expected or REQUIRED_SECTIONS
    heads = [h.strip() for h in
             re.findall(r'^\s{0,3}#{1,4}\s*(.+?)\s*$', text, re.M)]
    hit = {kw: any(kw in h for h in heads) for kw in expected}
    missing = [k for k, v in hit.items() if not v]
    return {
        "必需节": expected, "命中": hit, "缺失节": missing,
        "标题总数": len(heads),
        "结构漂移": bool(missing) or not heads,
    }


def check_humanizer(body):
    """H14 AI 味：调 humanizer-check.py v2（lieflat 11 条实证规则）"""
    if not os.path.exists(HUMANIZER):
        return {"可用": False, "说明": "humanizer-check.py 不存在"}
    try:
        p = subprocess.run([sys.executable, HUMANIZER], input=body,
                           capture_output=True, text=True, timeout=60)
        out = (p.stdout or "") + (p.stderr or "")
        m = re.search(r'(\d+)\s*分', out)
        if not m:
            return {"可用": True, "分数": None, "说明": "解析失败: " + out[:120]}
        score = int(m.group(1))
        if score <= HUMANIZER_LIMITS["放行"]:
            verdict = "放行"
        elif score <= HUMANIZER_LIMITS["重写"]:
            verdict = "重写>=50%"
        else:
            verdict = "推倒重写"
        return {"可用": True, "分数": score, "判定": verdict}
    except Exception as e:
        return {"可用": True, "分数": None, "说明": "调用异常: %s" % e}


def assess_lead(text):
    """负责人产出考核：选题排期表字段完整性 + G0门禁 + 决策依据 + 通用规则"""
    n_cand = len(re.findall(r'^##\s*候选\s*\d', text, re.M))
    BASE_FIELDS = ['选题', '目标读者', '读者痛点', '预期收益', '素材可得性',
                   '风险', '优先级', '状态']
    sections = re.split(r'^##\s*候选', text, flags=re.M)[1:]
    field_gaps = {}
    for i, sec in enumerate(sections):
        missing = [f for f in BASE_FIELDS if f not in sec]
        published = any(kw in sec for kw in ['已发布', '已发表', '已完成'])
        if not published and '落选理由' not in sec:
            missing.append('落选理由')
        if missing:
            field_gaps[i + 1] = missing
    all_ok = not field_gaps
    INTERNAL_RE = re.compile(r'(?:H[1-9]|[GH]\d{2}|TEAM\.md|gate-check\.py|REVIEW\.md|VALIDATION\.md|train-check\.py)')
    g0_hits = []
    for i, sec in enumerate(sections):
        m = re.search(r'\|\s*选题\s*\|\s*([^|]+?)\s*\|', sec)
        if m and INTERNAL_RE.search(m.group(1)):
            g0_hits.append(i + 1)
    has_basis = bool(re.search(r'依据|门禁|实测数据|排期表|不做清单', text))
    hits = [w for w in BANNED if w in text]
    urg_hits = [w for w in URGENCY if w in text]
    meta = [w for w in META if w in text]
    return {
        "候选数>=3": {"实测": n_cand, "标准": ">=3", "达标": n_cand >= 3, "判定方式": "脚本"},
        "9字段齐全": {"实测": ("缺失 %s" % field_gaps) if field_gaps else "全部齐全",
                   "标准": "0 字段缺失", "达标": all_ok, "判定方式": "脚本"},
        "G0无内部编号": {"实测": ("选题标题命中候选 %s" % g0_hits) if g0_hits else "无",
                     "标准": "0 命中", "达标": not g0_hits, "判定方式": "脚本"},
        "决策有依据": {"实测": has_basis, "标准": True,
                    "达标": has_basis, "判定方式": "布尔"},
        "禁用词": {"实测": hits or "无", "标准": "0 命中", "达标": not hits, "判定方式": "脚本"},
        "元话语污染": {"实测": meta or "无", "标准": "0 命中", "达标": not meta, "判定方式": "布尔"},
        "紧迫诱导词": {"实测": urg_hits or "无", "标准": "0 命中", "达标": not urg_hits, "判定方式": "脚本"},
    }


def assess(text, track="深评", expected=None, do_humanizer=True, mode="solo"):
    """返回能力项 dict。每项: {实测, 标准, 达标} —— 可判定，不留主观项"""
    body = _extract_body(text)
    zh = len(ZH_RE.findall(body))
    min_words = EXPRESS_MIN_WORDS if track == "速评" else DEFAULT_MIN_WORDS

    paras = [p.strip() for p in re.split(r'\n\s*\n', body)
             if p.strip() and not p.strip().startswith(('**', '##', '【'))]
    over = [(i + 1, _sentences(p), p[:18]) for i, p in enumerate(paras)
            if _sentences(p) > 3]

    hits = [w for w in BANNED if w in body]
    urg_hits = [w for w in URGENCY if w in body]
    meta = [w for w in META if w in body]
    titles = TITLE_STRATEGY_RE.findall(text)
    title_min = 1 if '已选标题' in text else 5
    hum = check_humanizer(body) if do_humanizer else {"可用": False, "跳过": True}
    ai_label = bool(re.search(r'AI\s*参与(程度|占比)', text)) or 'AI 参与' in text
    gold = len(re.findall(r'\*\*[^*\n]{4,80}\*\*', body))
    kind = detect_kind(text)
    struct = check_structure(text, expected)

    items = {
        "H8 正文字数": {"实测": zh, "标准": ">= %d (%s轨)" % (min_words, track),
                     "达标": zh >= min_words, "判定方式": "脚本"},
        "H9 段落<=3句": {"实测": "%d/%d 段超标" % (len(over), len(paras)),
                     "标准": "0 段超标", "达标": not over, "判定方式": "脚本",
                     "超标明细": over},
        "H10 输出结构": {"实测": ("正文片段，跳过" if kind == "正文片段"
                              else "缺失 %s" % (struct["缺失节"] or "无")),
                     "标准": "四节齐全" if kind == "完整稿件" else "不适用",
                     "达标": (None if kind == "正文片段"
                             else not struct["结构漂移"]),
                     "判定方式": "脚本", "文件类型": kind, "明细": struct},
        "H14 AI味": {"实测": hum.get("分数"),
                  "标准": "<=%d 放行 / 6-%d 重写 / >25 推倒"
                          % (HUMANIZER_LIMITS["放行"], HUMANIZER_LIMITS["重写"])
                          + (" | solo=参考分，strict=硬判定" if mode == "solo" else ""),
                  "达标": (hum.get("分数") is not None and hum.get("分数") <= HUMANIZER_LIMITS["放行"]),
                  "判定方式": "外部脚本", "模式": mode, "明细": hum},
        "禁用词": {"实测": hits or "无", "标准": "0 命中", "达标": not hits,
                "判定方式": "脚本"},
        "元话语污染": {"实测": meta or "无", "标准": "0 命中", "达标": not meta,
                  "判定方式": "布尔"},
        "标题策略标注": {"实测": ("正文片段，跳过" if kind == "正文片段"
                              else "%d/%d" % (len(titles), title_min)),
                    "标准": ">= %d" % title_min,
                    "达标": (None if kind == "正文片段"
                            else len(titles) >= title_min),
                    "判定方式": "脚本"},
        "AI 参与声明": {"实测": ("正文片段，跳过" if kind == "正文片段" else ai_label),
                   "标准": True,
                   "达标": (None if kind == "正文片段" else ai_label),
                   "判定方式": "布尔"},
        "金句密度": {"实测": "%d 处加粗 / %d 字" % (gold, zh),
                 "标准": ">=1 处且每 1000 字 1 处",
                 "达标": zh == 0 or (gold >= 1 and gold >= zh // 1000),
                 "判定方式": "脚本"},
        "紧迫诱导词": {"实测": urg_hits or "无", "标准": "0 命中", "达标": not urg_hits,
                   "判定方式": "脚本"},
    }
    return items


def main():
    parser = gzh_cli.build_parser("training/train-check.py", "G5 岗位能力考核（培训体系度量层）")
    parser.add_argument("file", help="稿件或排期表文件路径")
    parser.add_argument("--json", dest="json_mode", action="store_true",
                        help="JSON 输出（供 train-verify 消费）")
    parser.add_argument("--track", default="深评",
                        help="考核轨道：速评（豁免 H8 字数门槛，500 字）/ 深评（默认，800 字）")
    parser.add_argument("--no-humanizer", dest="no_humanizer", action="store_true",
                        help="跳过 AI 味外部调用")
    parser.add_argument("--mode", default="solo", choices=["solo", "strict"],
                        help="solo=单人模式 H14 只给参考分（默认）；strict=审核岗/发布前三档硬判定")
    parser.add_argument("--role", default=None, help="按岗位路由考核（06-负责人=排期表考核）")
    args = parser.parse_args()

    # v3.3.0 的 "--track 速评" 因 argv 切分 bug 从未生效；argparse 下按文档语义正确解析
    track = "速评" if args.track == "速评" else "深评"

    text = gzh_cli.read_text(args.file)

    if args.role == "06-负责人":
        items = assess_lead(text)
        track = "负责人"
    else:
        items = assess(text, track=track, do_humanizer=not args.no_humanizer,
                       mode=args.mode)

    if args.json_mode:
        ft = "选题排期表" if args.role == "06-负责人" else detect_kind(text)
        print(json.dumps({"文件": args.file, "轨道": track,
                          "文件类型": ft, "能力项": items},
                         ensure_ascii=False, indent=2))
        return 0

    # 三态判定：SKIP（达标=None）不计入分母。否则正文片段会被算成 FAIL，
    # 产生假阳性能力缺口（实测命中过 2 例）。
    scored = {k: v for k, v in items.items() if v["达标"] is not None}
    skipped = {k: v for k, v in items.items() if v["达标"] is None}
    passed = sum(1 for v in scored.values() if v["达标"])
    print("=" * 60)
    print("岗位能力考核  %s" % os.path.basename(args.file))
    print("轨道: %s | 文件类型: %s"
          % (track, "选题排期表" if args.role == "06-负责人" else detect_kind(text)))
    print("=" * 60)
    for k, v in items.items():
        d = v["达标"]
        mark = "PASS" if d is True else ("FAIL" if d is False else "SKIP")
        print("[%s] %-14s 实测=%s  标准=%s" % (mark, k, v["实测"], v["标准"]))
        if "超标明细" in v and v["超标明细"]:
            for n, c, s in v["超标明细"]:
                print("        段%d %d句: %s..." % (n, c, s))
        if k == "H10 输出结构" and v["明细"]["缺失节"]:
            print("        缺失: %s" % "、".join(v["明细"]["缺失节"]))
        if k == "H14 AI味" and v["明细"].get("判定"):
            print("        %s 分 → %s" % (v["明细"]["分数"], v["明细"]["判定"]))
    print("-" * 60)
    print("能力项通过率: %d/%d = %.0f%%" % (passed, len(scored),
          passed / len(scored) * 100))
    if skipped:
        print("不适用(SKIP): %s —— 文件类型不匹配，不计入分母"
              % "、".join(skipped))
    return 0 if passed == len(scored) else 1


if __name__ == "__main__":
    gzh_cli.run_main(main)
