#!/usr/bin/env python3
"""gzhkit.config: 阈值 / 词表 / 正则集中管理。

D4：此前散落在各脚本硬编码，改一处漏一处是"越修越错"主因之一。
所有门禁插件只从此处读取常量，禁止在插件内硬编码阈值。
值全部取自 v3.3.0 实际行为（以 docs/ 规范为准，冲突处见重建报告）。
"""
import re

# ── H8 字数（2026-09-24 A 级决策：800-1200 降为参考区间，唯一 BLOCK 是 <200） ──
WORD_MIN_BLOCK = 200
# 档位：(下限, 名称)，按从高到低排列
WORD_TIERS = [
    (1200, '长稿'),
    (800, '标准'),
    (500, '短稿'),
    (300, '速评'),
    (0, '疑似漏写'),
]
WORD_TIER_REF = 800  # --verbose 余量计算参照点（非阈值）

# ── H-禁用词（9 词，中文软边界匹配） ──
BANNED_WORDS = ['首先', '其次', '此外', '总而言之', '不可否认',
                '需要关注的是', '接下来', '需要注意的是', '换句话说']

# ── H-元话语（4 词） ──
META_WORDS = ['这里多余', '刚才说', '删掉。', '多余，删']

# ── H-紧迫诱导词（train-check 口径：只留强紧迫词） ──
URGENCY_WORDS = ['速看', '马上删', '惊呆了', '震惊', '必看', '全网首个', '全网第一']

# ── H-占位符 ──
# 非标占位符（内容缺陷 → BLOCK）；[待填写] 须配文末 ## 信息缺口声明
PLACEHOLDER_RE = re.compile(r'XX+|xx+|_{2,}|TBD|tbd|待补')
TODO_MARKER = '[待填写]'
GAP_SECTION_MARKER = '信息缺口声明'

# ── H-注入（8 种行首注入标记 → BLOCK） ──
INJECT_RE = re.compile(
    r'^\s*(?:system[-_ ]?reminder|system\s*prompt|system\s*:|'
    r'</?(?:result|system|minis)\b[^>]*>|<\|im_end\|>|'
    r'ignore\s+(?:all\s+)?previous\s+instructions)', re.I | re.M)

# ── H-元数据泄漏（正文不得含 → BLOCK） ──
META_LEAK_RE = re.compile(r'平台：公众号|字数：约|调性：')

# ── 标题策略数：备选阶段 5 个（5 类策略），已选阶段 ≥1 ──
TITLE_MIN_DRAFT = 5
TITLE_MIN_SELECTED = 1
TITLE_SELECTED_MARKER = '已选标题'

# ── 金句密度：正文 **加粗** 计数，每 1000 字至少 1 处 ──
GOLD_MIN_LEN = 4
GOLD_MAX_LEN = 80

# ── H10 输出结构（完整稿件四节） ──
REQUIRED_SECTIONS = ['备选标题', '正文', '结尾', 'AI 参与']
PACKAGE_MARKERS = ['备选标题', 'AI 参与', '交付前自检', '配图指导', '已选标题']

# ── H14 AI 味（humanizer-check 外部脚本） ──
HUMANIZER_LIMITS = {'放行': 5, '重写': 15}
HUMANIZER_BLOCK_SCORE = 25  # >25 推倒重写 → BLOCK
HUMANIZER_TIMEOUT = 60

# ── G0 选题门禁（TEAM.md §3.1/§3.2 + 不做清单） ──
G0_REQUIRED_FIELDS = ['选题', '目标读者', '读者痛点', '预期收益',
                     '素材可得性', '风险', '优先级', '状态']
G0_MAIN_CLAIM_RE = r'##\s*(?:主论点|核心论点|结论|核心判断|一句话结论)|主论点[：:]'
G0_MATERIAL_MIN = 8
G0_AB_MIN = 3
G0_SOURCE_FIELD_RE = r'\*\*来源\*\*[：:]|^-?\s*来源[：:]'
G0_INTERNAL_HINTS = ['内部文件', '内部手册', '内部编号']
G0_COUNTER_RE = r'反例|反面|失败样本|反证|反对意见'
G0_ALT_RE = r'备选|未选|落选'
G0_REJECT_RE = r'落选理由|否决|放弃理由'
G0_V1_RE = r'与 v1|v1 |v1→'
G0_DIFF_ANGLE_RE = r'差异化角度|角度切换|论证结构不同'
# 样本认知度白名单（账号读者"听说过"的项目）
KNOWN_SAMPLE_HINTS = [
    'Claude Code', 'Cursor', 'Copilot', 'Vercel', 'VSCode', 'GitHub Copilot',
    'ChatGPT', 'Gemini', 'Claude', 'Kimi', 'DeepSeek', 'Doubao', '通义',
    '小红书', '抖音', 'B站', '知乎', '微博', '公众号', '微信',
    'Fiverr', 'Upwork', 'X', 'Twitter', 'YouTube']

# ── G3 结构门禁（模板判据） ──
G3_TEMPLATES = {
    '标准观点': {'sections': (3, 5), 'words_per_section': (200, 350), 'total_words': (800, 1200), 'gold_min': 2},
    '评测横比': {'sections': (5, 7), 'words_per_section': (150, 300), 'total_words': (800, 1500), 'gold_min': 3},
    '教程方法': {'sections': (4, 6), 'words_per_section': (150, 250), 'total_words': (600, 1200), 'gold_min': 2},
    '资讯热点': {'sections': (3, 4), 'words_per_section': (200, 400), 'total_words': (600, 1200), 'gold_min': 2},
    '复盘成长': {'sections': (4, 6), 'words_per_section': (200, 300), 'total_words': (800, 1200), 'gold_min': 2},
}
G3_DEFAULT_TEMPLATE = '标准观点'

# ── G7 发布前清单（TEAM.md §3.7 十项清单） ──
G7_TITLE_ZH_MIN = 15
G7_TITLE_ZH_MAX = 30
G7_COVER_W = 900
G7_COVER_H = 383
G7_HOOK_KEYWORDS = ['你', '评论', '留言', '怎么', '如何', '你觉得', '分享', '投票', '填']
G7_ARTIFICIAL_ITEMS = ['后台预览', 'AI 声明开关', '24h pre-mortem']
G7_ACCOUNT_HEALTH_FILE = 'docs/account-health-label.md'

# ── G8 结构多样性 ──
G8_HISTORY_DIRNAME = '.gzh-structure-history'
G8_HISTORY_FILE = 'structure-log.json'
G8_ORDINAL_MIN = 3  # 序数词小标题 ≥3 个判为 A 型骨架
G8_ORDINAL_RE = r'^#{1,3}\s*[一二三四五六七八九十]+[、.．]'
DISABLED_OPENINGS = ['先说结论', '一句话概括', '这次不一样', '这次值得重视', '先给结论']
DISABLED_CLOSINGS = ['一句话总结', '你的选择', '你怎么看']

# ── H11 图片 OCR（中文残留/水印） ──
H11_WATERMARK_KEYWORDS = ['AI生成', 'AI 生成', '日日新', 'sensenova', '即梦', 'jimeng', 'SENSENOVA']
H11_CONF_THRESHOLD = 0.6  # conf < 0.6 → WARN（疑似幻觉），≥0.6 → 真实中文残留
H11_FLAT_MAX_COLORS = 2

# ── H12 prompt 元数据入图 ──
H12_PROMPT_META_KEYWORDS = [
    'ultrawide', 'no text', 'no watermark', 'no lettering', 'no text, no watermark',
    'aspect ratio', 'aspect-ratio', 'poster', 'image quality', 'high quality',
    'masterpiece', 'best quality', '8k', '4k', 'cinematic', 'photorealistic',
    'ultra detailed', 'hyper detailed', 'detailed', 'style', 'prompt', 'text, no',
    'watermark', 'lettering', 'subtitle', 'caption',
]
H12_SUBJECT_CN_MIN = 4  # 中文词组 ≥4 字 → 可能是主体描述被画进图（WARN）
H12_HALLUC_CONF = 0.5  # conf < 0.5 + 纯色区 → OCR 幻觉，直接放行

# ── H15 尾图合规 ──
H15_MAX_HEIGHT = 800  # 高度 >800px 阻断
H15_ALLOWED_WIDTHS = (900, 1080)  # 宽度非此二值 → 仅提示
H15_PROHIBITED_WORDS = [
    '星标', '第一时间', '独家', '首发', '必看', '速看',
    '赶紧', '立即', '马上', '限时', '最后', '错过',
]
H15_LEAD_KEYWORDS = [
    '微信', 'QQ', '电话', '邮箱', '二维码', '扫码',
    '加我', '私信', '关注公众号',
]

# ── G8 结构多样性 ──
G8_HISTORY_DIRNAME = '.gzh-structure-history'
G8_HISTORY_FILE = 'structure-log.json'
G8_ORDINAL_MIN = 3  # 序数词小标题 ≥3 个判为 A 型骨架
DISABLED_OPENINGS = ['先说结论', '一句话概括', '这次不一样', '这次值得重视', '先给结论']
DISABLED_CLOSINGS = ['一句话总结', '你的选择', '你怎么看']

# ── 正文提取：## 正文 … 终止节（配图/缺口判断/AI 参与/自检/结尾/发布） ──
BODY_END_MARKERS = ['配图', '缺口判断', 'AI 参与', '自检', '结尾', '发布']

# ── 分级放行（v3.3.0 阶段三，保留） ──
RELEASE_LEVELS = {
    'L1': '全量检查',
    'L2': '核心检查',
    'L3': '基础检查',
}

# ── 脱敏占位符（公开版约束，D6） ──
BRAND_PLACEHOLDER = '<YOUR_BRAND>'
BRAND_EN_PLACEHOLDER = '<YOUR_BRAND_EN>'
