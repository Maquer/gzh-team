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


def find_meta_leak(text):
    """H-元数据泄漏。"""
    return C.META_LEAK_RE.findall(text)


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
