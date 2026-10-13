#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gzh-call.py —— 公众号流水线模型调用 wrapper。

v4.0.0 重建：结构清理（argparse 统一 CLI / 退出码 0/1/2 / 缺依赖提示），
调用与净化逻辑与 v3.3.0 一致。

作用：minis-model-use → 取 output_text → sanitize 净化 → 落盘。
把"模型返回 → 落盘"的注入清洗固化成一步，不靠手动过净化。

配合 gate-check.py 的 H-注入 断言形成双重保险：
  wrapper 主动清洗（防污染）+ gate-check 被动检查（兜底防漏网）

用法:
  python3 gzh-call.py <model> <prompt> <out_file>

输出: 清洗后正文写入 out_file；检测到注入时 stderr 警告。
退出码: 0 正常 / 1 模型调用失败 / 2 参数错误 / 输出全是注入（拒落盘）/ 缺依赖
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gzhkit import cli as gzh_cli

# 仓库根目录（原为 /var/minis/shared/gzh-team）与共享工具目录（仓库的上一级）
GZH_TEAM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.environ.get('GZH_SHARED_DIR', os.path.dirname(GZH_TEAM))

SANITIZE = os.path.join(SHARED_DIR, "sanitize-model-output.py")
TMP = "/tmp/_gzh_raw.md"


def check_deps():
    """检查外部依赖。缺失打印提示并返回 False（调用方 exit 2）。"""
    if shutil.which("minis-model-use") is None:
        print("错误：缺少依赖 minis-model-use（模型调用 CLI，未在 PATH 中找到）。",
              file=sys.stderr)
        return False
    if not os.path.isfile(SANITIZE):
        print("错误：缺少依赖 sanitize 工具 %s。" % SANITIZE, file=sys.stderr)
        return False
    return True


def call_model(model: str, prompt: str) -> str:
    """调 minis-model-use，返回输出文本。

    响应内容在 data.output_text（不在顶层 content），见 09-18 daily log。
    """
    r = subprocess.run(
        ["minis-model-use", "run", "--model", model, "--prompt", prompt],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError("minis-model-use 调用失败: %s" % (r.stderr or r.stdout)[:200])
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.stdout  # 非 JSON（超时/错误输出），原样返回交由 sanitize 兜底
    return (data.get("data", {}).get("output_text")
            or data.get("content")
            or data.get("output", ""))


def sanitize_text(text: str):
    """过净化工具，返回 (清洗后文本, stderr 警告)；全是注入时返回 (None, 原因)。"""
    Path(TMP).write_text(text, encoding="utf-8")
    r = subprocess.run(
        ["python3", SANITIZE, "--file", TMP, "--out", TMP + ".clean"],
        capture_output=True, text=True,
    )
    if r.returncode == 2:
        Path(TMP).unlink(missing_ok=True)
        Path(TMP + ".clean").unlink(missing_ok=True)
        return None, "输出全部是注入内容，拒绝落盘"
    cleaned = Path(TMP + ".clean").read_text(encoding="utf-8")
    Path(TMP).unlink(missing_ok=True)
    Path(TMP + ".clean").unlink(missing_ok=True)
    return cleaned, r.stderr


def main() -> int:
    parser = gzh_cli.build_parser(
        "training/gzh-call.py",
        "公众号流水线模型调用 wrapper（调用 → 净化 → 落盘）")
    parser.add_argument("model", help="模型 ID")
    parser.add_argument("prompt", help="提示词")
    parser.add_argument("out_file", help="清洗后正文落盘路径")
    args = parser.parse_args()

    if not check_deps():
        return 2

    try:
        raw = call_model(args.model, args.prompt)
    except Exception as e:
        print("[ERROR] %s" % e, file=sys.stderr)
        return 1

    cleaned, warn = sanitize_text(raw)
    if cleaned is None:
        print("[ERROR] %s" % warn, file=sys.stderr)
        return 2

    try:
        Path(args.out_file).write_text(cleaned, encoding="utf-8")
    except OSError as e:
        print("[ERROR] 无法写入 %s: %s" % (args.out_file, e), file=sys.stderr)
        return 2

    if warn.strip():
        print("[WARN] " + warn.strip(), file=sys.stderr)
    print("OK %d chars → %s" % (len(cleaned), args.out_file))
    return 0


if __name__ == "__main__":
    gzh_cli.run_main(main)
