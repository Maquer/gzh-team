#!/usr/bin/env python3
"""
gzh-typeset.py：公众号排版工具（Markdown→微信HTML）
用法：python3 gzh-typeset.py <input.md> [output.html]
关键约束：需指定输入Markdown文件
"""
# gzh-typeset.py — 兼容 shim

# 本文件是 shared/gzh-team/gzh-typeset.py 的旧路径兼容层。
# 真正的实现已迁移到 shared/gzh-typeset/gzh-typeset.py（融合版 v2）。

# 融合版相比团队版增加了：
#   - 5 主题预设（authoritative/friendly/analytical/urgent/elegant）+ 关键词加权打分
#   - 5 色荧光笔（yellow/green/blue/pink/purple）
#   - 首尾模板（--template / --save-template）
#   - --plain 纯文本输出
#   - 密度门控（金句卡封顶，超量降级加粗）
#   - **markdown 表格 → HTML <table>**（团队版直接把 `| --- |` 塞进 <p>，微信渲染为裸字符）
#   - **H1 剥离时先剥 `（策略：XXX）` 尾部标记**
#   - **`### 结尾/结束/小结` 特殊跳过**（不渲染标题行）
#   - 默认输出名规则（-正文.md → -排版稿.html）

# 用法完全兼容团队版：
#   python3 gzh-typeset.py IN.md [--title "标题"] [--out OUT.html]

# 新增参数（只有融合版支持）：
#   --only-body / --tone / --max-pull / --hl / --highlight-color / --template / --save-template / --list-tones / --plain

# 历史事故：2026-09-20 16:00 推送 AI 写作副业稿时，团队版排版稿的报价表还是 `| --- |` 裸 markdown，
# 微信渲染为裸文字 → 用手工"修复版.html"临时绕过。本次融合后，表格自动转 HTML <table>，bug 根治。


import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get('GZH_TYPESET_IMPL', ''),
    os.path.join(_HERE, '..', 'gzh-typeset', 'gzh-typeset.py'),
]


def main():
    for impl in _CANDIDATES:
        if impl and os.path.isfile(impl) and os.path.abspath(impl) != os.path.abspath(__file__):
            sys.exit(subprocess.call([sys.executable, impl] + sys.argv[1:]))
    print('gzh-typeset.py: 未找到融合版实现（../gzh-typeset/gzh-typeset.py），'
          '可用环境变量 GZH_TYPESET_IMPL 指定路径。', file=sys.stderr)
    sys.exit(2)


if __name__ == '__main__':
    main()
