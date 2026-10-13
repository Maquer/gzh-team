#!/usr/bin/env python3
"""archive_note_generator.py：生成归档笔记（Markdown 格式）。

v4.0.0 重建：干净重写，笔记模板与 v3.3.0 一致。
用法：归档完成后调用 generate_all_notes() 自动生成。
关键约束：需指定 workspace_dir，输出到 archive_notes/ 目录。

退出码：0 成功；2 参数错误 / 输入文件不可读 / JSON 解析失败。
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli


def note_content(tool_name, decision, timestamp):
    """按决策类型生成归档笔记（与 archives_optimizer.py 的模板一致）。"""
    if decision in ("FORCE_INSTALL", "FULL_INSTALL"):
        return (
            "# %s\n"
            "> 核心价值：P0 强制执行工具\n"
            "> 决策边界：环境不可用则归档\n"
            "> P1 借鉴：架构设计与执行流程\n"
            "> 域内边界：iSH 环境限制\n"
            "\n"
            "## 核心定位\n"
            "%s 是 P0 级工具，在当前环境中强制执行。\n"
            "\n"
            "## 核心差异\n"
            "与同类工具不同之处在于自动化执行能力。\n"
            "\n"
            "## P1 借鉴\n"
            "从其他工具中借鉴执行流程和架构设计。\n"
            "\n"
            "## 域内边界\n"
            "%s 的应用受限于 iSH 环境限制。\n"
            "\n"
            "生成时间：%s\n" % (tool_name, tool_name, tool_name, timestamp)
        )
    if decision == "PARTIAL_INSTALL":
        return (
            "# %s\n"
            "> 核心价值：P1 部分执行工具\n"
            "> 决策边界：环境可用性与领域重合度\n"
            "> P1 借鉴：边界管理和工具池管理\n"
            "> 域内边界：特定领域工具\n"
            "\n"
            "## 核心定位\n"
            "%s 是 P1 级工具，在特定领域有限执行。\n"
            "\n"
            "## 核心差异\n"
            "与同类工具不同之处在于边界管理和部分执行能力。\n"
            "\n"
            "## P1 借鉴\n"
            "从其他工具中借鉴边界管理和工具池管理。\n"
            "\n"
            "## 域内边界\n"
            "%s 的应用受限于特定领域。\n"
            "\n"
            "生成时间：%s\n" % (tool_name, tool_name, tool_name, timestamp)
        )
    # ARCHIVE_ONLY 及其它
    return (
        "# %s\n"
        "> 核心价值：P2/P3 仅归档工具\n"
        "> 决策边界：环境不可用 + 领域错位\n"
        "> P1 借鉴：无直接借鉴\n"
        "> 域内边界：完全归档工具\n"
        "\n"
        "## 核心定位\n"
        "%s 归档仅供参考，无实际执行能力。\n"
        "\n"
        "## 核心差异\n"
        "与同类工具不同之处在于完全归档且无实际应用。\n"
        "\n"
        "## P1 借鉴\n"
        "无直接借鉴。\n"
        "\n"
        "## 域内边界\n"
        "%s 完全归档，不具备实际应用条件。\n"
        "\n"
        "生成时间：%s\n" % (tool_name, tool_name, tool_name, timestamp)
    )


class ArchiveNoteGenerator:
    def __init__(self, workspace_dir=None, tools_file=None):
        self.workspace_dir = Path(workspace_dir or os.path.dirname(os.path.abspath(__file__)))
        self.decision_log_file = self.workspace_dir / "decision_log.json"
        self.active_tools_file = (Path(tools_file) if tools_file
                                  else self.workspace_dir / "active_tools.json")

    def _load_json(self, path):
        if not path.exists():
            return []
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            print("错误：无法解析 %s: %s" % (path, e), file=sys.stderr)
            sys.exit(2)

    def load_decisions(self):
        """读取 decision_log.json；同一工具多条记录时保留最新一条。"""
        data = self._load_json(self.decision_log_file)
        latest = {}
        for d in data:
            if not isinstance(d, dict) or "tool_name" not in d:
                continue
            prev = latest.get(d["tool_name"])
            if prev is None or str(d.get("timestamp", "")) >= str(prev.get("timestamp", "")):
                latest[d["tool_name"]] = d
        return list(latest.values())

    def load_active_tools(self):
        return self._load_json(self.active_tools_file)

    def generate_all_notes(self):
        print("开始生成归档笔记...")

        decisions = self.load_decisions()
        active_tools = self.load_active_tools()

        notes_dir = self.workspace_dir / "archive_notes"
        notes_dir.mkdir(exist_ok=True)

        generated_notes = []
        for tool in active_tools:
            tool_name = tool["name"]

            tool_decision = None
            tool_timestamp = None
            for decision in decisions:
                if decision["tool_name"] == tool_name:
                    tool_decision = decision["decision"]
                    tool_timestamp = decision["timestamp"]
                    break

            if not tool_decision:
                print("  警告: %s 没有对应的决策，跳过" % tool_name)
                continue

            note_file = notes_dir / ("archive_note_%s.md" % tool_name)
            with open(note_file, "w", encoding="utf-8") as f:
                f.write(note_content(tool_name, tool_decision, tool_timestamp))

            generated_notes.append({
                "tool_name": tool_name,
                "decision": tool_decision,
                "note_file": str(note_file),
            })
            print("  已生成归档笔记: %s (%s)" % (tool_name, tool_decision))

        self.generate_summary_report(generated_notes)
        print("\n归档笔记生成完成！共生成 %d 个归档笔记" % len(generated_notes))
        return 0

    def generate_summary_report(self, generated_notes):
        report_file = self.workspace_dir / "archive_generation_report.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# 归档笔记生成报告\n\n")
            f.write("生成时间: %s\n\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            f.write("## 统计信息\n\n")
            f.write("总归档笔记数: %d\n\n" % len(generated_notes))

            decision_counts = {}
            for note in generated_notes:
                decision = note["decision"]
                decision_counts[decision] = decision_counts.get(decision, 0) + 1

            f.write("决策类型分布:\n\n")
            f.write("| 决策类型 | 数量 | 比例 |\n")
            f.write("|-----------|------|------|\n")

            total = len(generated_notes)
            for decision, count in decision_counts.items():
                ratio = (count / total) * 100 if total else 0
                f.write("| %s | %d | %.1f%% |\n" % (decision, count, ratio))

            f.write("\n## 归档笔记列表\n\n")
            for note in generated_notes:
                f.write("### %s\n" % note["tool_name"])
                f.write("- 决策: %s\n" % note["decision"])
                f.write("- 文件: %s\n\n" % note["note_file"])

        print("汇总报告已生成: %s" % report_file)


def main():
    parser = gzh_cli.build_parser("archive_note_generator.py", "归档笔记生成器")
    parser.add_argument("--tools", default=None, help="要生成的工具列表文件")
    parser.add_argument("--workspace", default=None, help="工作目录（默认脚本所在目录）")
    args = parser.parse_args()

    generator = ArchiveNoteGenerator(workspace_dir=args.workspace,
                                     tools_file=args.tools)
    return generator.generate_all_notes()


if __name__ == "__main__":
    gzh_cli.run_main(main)
