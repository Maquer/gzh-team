#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gzh-typeset.py — 兼容 shim（2026-09-20 融合）

本文件是 shared/gzh-team/gzh-typeset.py 的旧路径兼容层。
真正的实现已迁移到 shared/gzh-typeset/gzh-typeset.py（融合版 v2）。

融合版相比团队版增加了：
  - 5 主题预设（authoritative/friendly/analytical/urgent/elegant）+ 关键词加权打分
  - 5 色荧光笔（yellow/green/blue/pink/purple）
  - 首尾模板（--template / --save-template）
  - --plain 纯文本输出
  - 密度门控（金句卡封顶，超量降级加粗）
  - **markdown 表格 → HTML <table>**（团队版直接把 `| --- |` 塞进 <p>，微信渲染为裸字符）
  - **H1 剥离时先剥 `（策略：XXX）` 尾部标记**
  - **`### 结尾/结束/小结` 特殊跳过**（不渲染标题行）
  - 默认输出名规则（-正文.md → -排版稿.html）

用法完全兼容团队版：
  python3 gzh-typeset.py IN.md [--title "标题"] [--out OUT.html]

新增参数（只有融合版支持）：
  --only-body / --tone / --max-pull / --hl / --highlight-color / --template / --save-template / --list-tones / --plain

历史事故：2026-09-20 16:00 推送 AI 写作副业稿时，团队版排版稿的报价表还是 `| --- |` 裸 markdown，
微信渲染为裸文字 → 用手工"修复版.html"临时绕过。本次融合后，表格自动转 HTML <table>，bug 根治。
"""
import sys, os

FUSION = '/var/minis/shared/gzh-typeset/gzh-typeset.py'

if __name__ == '__main__':
    if not os.path.exists(FUSION):
        print(f'FATAL: 融合版不存在 {FUSION}，请先恢复 shared/gzh-typeset/gzh-typeset.py', file=sys.stderr)
        sys.exit(1)
    # 用 runpy 执行融合版脚本，保留 __main__ 上下文（让 argparse 能读 sys.argv）
    import runpy
    runpy.run_path(FUSION, run_name='__main__')
