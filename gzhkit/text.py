#!/usr/bin/env python3
"""gzhkit.text: 文本分析公共函数。

v3.x 各脚本重复实现的正文提取/分句/计数逻辑收敛到此。
"""
import re

from . import config as C


def extract_body(text):
    """提取 ## 正文 … 终止节 之间的正文；无正文节时返回全文。

    终止节缺"结尾"会导致结尾字数算进正文（H8 虚高），v3.3.0 已补齐。
    """
    end_alt = '|'.join(C.BODY_END_MARKERS)
    m = re.search(r'##\s*正文(.*?)(?=\n#{2,3}\s*(?:%s))' % end_alt, text, re.S)
    return m.group(1) if m else text


def count_zh(text):
    """中文字符数。"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def word_tier(zh):
    """字数档位（参考区间，非硬阈值）。"""
    for threshold, name in C.WORD_TIERS:
        if zh >= threshold:
            return name
    return '疑似漏写'


def split_paragraphs(body):
    """分段，排除 **/##/【/``` 开头的非正文块。"""
    return [p.strip() for p in re.split(r'\n\s*\n', body)
            if p.strip() and not p.strip().startswith(('**', '##', '【', '```'))]


def count_sentences(para):
    """段落句数（。！？分句，去 ** 与标记）。"""
    clean = re.sub(r'\*\*|【金句】', '', para)
    return len([x for x in re.split(r'[。！？]', clean) if x.strip()])


def overlong_paragraphs(body, limit=3):
    """超 N 句段落：[(段号, 句数, 前18字)]。"""
    paras = split_paragraphs(body)
    return [(i + 1, count_sentences(p), p[:18])
            for i, p in enumerate(paras) if count_sentences(p) > limit]


def _soft_boundary_find(words, text):
    """中文软边界匹配：前后非中文，避免 URL/代码误报。"""
    hits = []
    for w in words:
        if re.search(r'(?<![\u4e00-\u9fff])%s(?![\u4e00-\u9fff])'
                     % re.escape(w), text):
            hits.append(w)
    return hits


def find_banned(body):
    """H-禁用词命中。"""
    return _soft_boundary_find(C.BANNED_WORDS, body)


def find_meta_words(body):
    """H-元话语命中。"""
    return [w for w in C.META_WORDS if w in body]


def find_titles(text):
    """标题策略数（括号标注）。"""
    return re.findall(r'（[^）]+）', text)


def title_threshold(text):
    """标题策略阈值：已选阶段 ≥1，否则备选阶段 5。"""
    return (C.TITLE_MIN_SELECTED if C.TITLE_SELECTED_MARKER in text
            else C.TITLE_MIN_DRAFT)


def find_inject(text):
    """H-注入残留。"""
    return C.INJECT_RE.findall(text)


def find_placeholders(text):
    """返回 (非标占位符列表, [待填写]计数)。"""
    return C.PLACEHOLDER_RE.findall(text), text.count(C.TODO_MARKER)


def split_meta_block(text):
    """拆出前缀元信息区，返回 (meta_block, rest)。

    元信息区 = H1 行 + 其后连续的元数据行（平台/字数/类型/调性/目标字数/合理性，
    允许空行与斜体标记）。遇到第一个非元数据行或任意 ## 小节即止。

    04-writer 产出物标准里「元信息」是稿件交付件之一（含调性字段），
    而 META_LEAK_RE 提示语是「移到元信息区」——两者要求元信息区必须可容纳这些字段。
    2026-10-18 修复：find_meta_leak 原为全文扫描，元信息区写了调性也会 BLOCK，
    字段无处可放（两篇稿件因此被剥掉元信息块）。现只扫元信息区之外，
    正文/尾注区出现 平台：公众号 / 字数：约 / 调性： 仍 BLOCK 不变。
    """
    lines = text.split('\n')
    end = 0
    seen_h1 = False
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            continue
        if s.startswith('#'):
            if not seen_h1 and s.startswith('# ') and not s.startswith('##'):
                seen_h1 = True
                end = idx + 1
                continue
            break  # 任何 ## 小节 = 前缀区结束
        if seen_h1 and C.META_FIELD_ANY_RE.match(s):
            end = idx + 1
            continue
        break
    return '\n'.join(lines[:end]), '\n'.join(lines[end:])


def find_meta_leak(text):
    """H-元数据泄漏：只扫元信息区之外（正文/尾注区）。"""
    _, rest = split_meta_block(text)
    return C.META_LEAK_RE.findall(rest)


def find_tone(text):
    """取元信息区 `调性：` 字段值（首个，None=未标注）。"""
    meta, _ = split_meta_block(text)
    m = C.TONE_FIELD_RE.search(meta)
    if not m:
        m = C.TONE_FIELD_RE.search(text)
    return m.group(1).strip() if m else None


def check_tone(value):
    """调性取值域。返回 (state, hint)。state: ok / bad / missing。"""
    if value is None:
        return 'missing', ''
    v = value.strip().strip('*').rstrip('。.，,、').strip()
    if v in C.TONE_LEGAL:
        return 'ok', ''
    key = C.TONE_ALIAS.get(v, '')
    if not key:
        for k, lab in C.TONE_LABELS.items():
            if lab == v or k == v.lower():
                key = k
                break
    if key:
        return 'bad', '改为 `调性：%s`（%s）' % (key, C.TONE_LABELS[key])
    return 'bad', '取值须为 5 档之一：%s（词表 docs/rules/tone-structure-map.md）' \
        % '/'.join(C.TONE_KEYS)


def has_ai_credit(text):
    """AI 参与标注是否存在。"""
    return bool(re.search(r'AI\s*参与(程度|占比)', text) or 'AI 参与' in text)


def count_gold(body):
    """金句密度：**加粗** 计数（4-80 字）。"""
    return len(re.findall(r'\*\*[^*\n]{%d,%d}\*\*' % (C.GOLD_MIN_LEN, C.GOLD_MAX_LEN), body))


def gold_needed(zh):
    """金句阈值：每 1000 字 1 处，至少 1 处。"""
    return max(1, zh // 1000)


def find_urgency(body):
    """H-紧迫诱导词命中。"""
    return [w for w in C.URGENCY_WORDS if w in body]


def detect_sections(text):
    """H10 输出结构：返回 (kind, missing)。kind ∈ {完整稿件, 正文片段}。"""
    kind = ('完整稿件' if any(mk in text for mk in C.PACKAGE_MARKERS)
            else '正文片段')
    if kind != '完整稿件':
        return kind, []
    heads = headings(text)
    missing = [kw for kw in C.REQUIRED_SECTIONS
               if not any(kw in h for h in heads)]
    return kind, missing


def headings(text):
    """全部标题行。"""
    return re.findall(r'^\s{0,3}#{1,4}\s*(.+?)\s*$', text, re.M)
