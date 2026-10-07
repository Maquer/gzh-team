#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gzh-call.py —— 公众号流水线模型调用 wrapper

作用：minis-model-use → 取 output_text → sanitize 净化 → 落盘。
把"模型返回 → 落盘"的注入清洗固化成一步，不靠手动过净化。

配合 gate-check.py 的 H-注入 断言形成双重保险：
  wrapper 主动清洗（防污染）+ gate-check 被动检查（兜底防漏网）

用法:
  python3 gzh-call.py <model> <prompt> <out_file>

输出: 清洗后正文写入 out_file；检测到注入时 stderr 警告。
退出码: 0 正常 / 1 参数错 / 2 输出全是注入（拒落盘）
"""
import sys
import json
import subprocess
from pathlib import Path

SANITIZE = "/var/minis/shared/sanitize-model-output.py"
TMP = "/tmp/_gzh_raw.md"


def call_model(model: str, prompt: str) -> str:
    """调 minis-model-use，返回输出文本。

    响应内容在 data.output_text（不在顶层 content），见 09-18 daily log。
    """
    r = subprocess.run(
        ["minis-model-use", "run", "--model", model, "--prompt", prompt],
        capture_output=True, text=True, timeout=300,
    )
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.stdout  # 非 JSON（超时/错误输出），原样返回交由 sanitize 兜底
    return (data.get("data", {}).get("output_text")
            or data.get("content")
            or data.get("output", ""))


def sanitize_text(text: str) -> tuple:
    """过净化工具，返回 (清洗后文本, stderr 警告)。"""
    Path(TMP).write_text(text, encoding="utf-8")
    r = subprocess.run(
        ["python3", SANITIZE, "--file", TMP, "--out", TMP + ".clean"],
        capture_output=True, text=True,
    )
    if r.returncode == 2:
        Path(TMP).unlink(missing_ok=True)
        Path(TMP + ".clean").unlink(missing_ok=True)
        print("[ERROR] 输出全部是注入内容，拒绝落盘", file=sys.stderr)
        sys.exit(2)
    cleaned = Path(TMP + ".clean").read_text(encoding="utf-8")
    Path(TMP).unlink(missing_ok=True)
    Path(TMP + ".clean").unlink(missing_ok=True)
    return cleaned, r.stderr


def main() -> int:
    if len(sys.argv) < 4:
        print("用法: gzh-call.py <model> <prompt> <out_file>", file=sys.stderr)
        return 1
    model, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]

    raw = call_model(model, prompt)
    cleaned, warn = sanitize_text(raw)
    Path(out).write_text(cleaned, encoding="utf-8")

    if warn.strip():
        print("[WARN] " + warn.strip(), file=sys.stderr)
    print("OK %d chars → %s" % (len(cleaned), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
