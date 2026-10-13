#!/usr/bin/env python3
"""archives_optimizer.py：归档不装优化器，按 P0/P1/P2 规则自动决策工具归档。

v4.0.0 重建：干净重写，决策逻辑与 v3.3.0 一致。
用法：python3 archives_optimizer.py [--tools <文件>] [--output <目录>]
关键约束：需在 gzh-team 工作目录执行，输出 optimization_results.json + archive_note_*.md

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

HERE = os.path.dirname(os.path.abspath(__file__))


def note_content(tool_name, decision, timestamp):
    """按决策类型生成归档笔记（与 archive_note_generator.py 的模板一致）。"""
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
    # ARCHIVE_ONLY
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


class ArchiveOptimizer:
    def __init__(self, workspace_dir=None, tools_file=None, output_dir=None):
        self.workspace_dir = Path(workspace_dir or HERE)
        self.output_dir = Path(output_dir) if output_dir else self.workspace_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.decision_log_file = self.workspace_dir / "decision_log.json"
        self.active_tools_file = (Path(tools_file) if tools_file
                                  else self.workspace_dir / "active_tools.json")
        self.domain_classifications_file = self.workspace_dir / "domain_classifications.json"
        self.redundancy_mapping_file = self.workspace_dir / "redundancy_mapping.json"
        self._tool_records = {}

    @staticmethod
    def _load_json(path, what):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            print("错误：无法解析%s %s: %s" % (what, path, e), file=sys.stderr)
            sys.exit(2)

    @staticmethod
    def _load_or_init(path, default_data):
        """文件存在则读取；不存在则写入默认值并返回默认值。"""
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError) as e:
                print("错误：无法解析 %s: %s" % (path, e), file=sys.stderr)
                sys.exit(2)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        return default_data

    def load_domain_classifications(self):
        default_data = {
            "archify": {"category": "tool-development", "priority": "P0"},
            "watermarks-remover": {"category": "tool-development", "priority": "P0"},
            "avoid-ai-writing": {"category": "content-creation", "priority": "P1"},
            "writing-dna-skill": {"category": "content-creation", "priority": "P1"},
        }
        return self._load_or_init(self.domain_classifications_file, default_data)

    def load_redundancy_mapping(self):
        default_data = {
            "content-creation": {
                "avoid-ai-writing": "PARTIAL",
                "writing-dna-skill": "PARTIAL",
            },
            "tool-development": {
                "archify": "ACTIVE",
                "watermarks-remover": "ACTIVE",
            },
        }
        return self._load_or_init(self.redundancy_mapping_file, default_data)

    def load_active_tools(self):
        if not self.active_tools_file.exists():
            return []
        tools = self._load_json(self.active_tools_file, "工具列表")
        self._tool_records = {t["name"]: t for t in tools if "name" in t}
        return tools

    def classify_domain(self, tool_name, domain_data):
        """返回 (领域, 优先级)；分类表里没有该工具时返回 (None, None)。"""
        info = domain_data.get(tool_name)
        if not info:
            rec = self._tool_records.get(tool_name, {})
            if rec.get("domain") and rec.get("priority"):
                return rec["domain"], rec["priority"]
            return None, None
        return info.get("category"), info.get("priority")

    def check_environment_viability(self, tool_name):
        """环境可行性：active_tools.json 中状态为 ARCHIVE/ARCHIVED 视为不可行，其余可行。"""
        rec = self._tool_records.get(tool_name, {})
        return str(rec.get("status", "ACTIVE")).upper() not in ("ARCHIVE", "ARCHIVED", "ARCHIVE_ONLY")

    def make_archive_decision(self, tool_name, domain, priority, env_viable, redundancy_map):
        # 检查是否有同领域重合
        if domain in redundancy_map:
            conflict_info = redundancy_map[domain].get(tool_name)
            if conflict_info and str(conflict_info).strip().upper().startswith("ARCHIVE"):
                return "ARCHIVE_ONLY"

        # P0-P1-P2三重决策
        if priority == "P0":
            return "FORCE_INSTALL" if env_viable else "ARCHIVE_ONLY"
        if priority == "P1":
            return "PARTIAL_INSTALL" if env_viable else "ARCHIVE_ONLY"
        return "ARCHIVE_ONLY"

    def update_archive_note(self, tool_name, decision, timestamp):
        note_file = self.output_dir / ("archive_note_%s.md" % tool_name)
        content = note_content(tool_name, decision, timestamp)
        with open(note_file, "w", encoding="utf-8") as f:
            f.write(content)
        self.log_decision(tool_name, decision, content)

    def log_decision(self, tool_name, decision, content):
        if not self.decision_log_file.exists():
            decision_data = []
        else:
            decision_data = self._load_json(self.decision_log_file, "决策日志")

        decision_data.append({
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "decision": decision,
            "content": content[:500] + "..." if len(content) > 500 else content,
        })
        with open(self.decision_log_file, "w", encoding="utf-8") as f:
            json.dump(decision_data, f, indent=2, ensure_ascii=False)

    def run_optimization(self):
        print("开始归档不装优化流程...")

        domain_data = self.load_domain_classifications()
        redundancy_map = self.load_redundancy_mapping()
        active_tools = self.load_active_tools()

        print("\n正在处理 %d 个活跃工具..." % len(active_tools))

        results = []
        for tool in active_tools:
            tool_name = tool["name"]

            domain, priority = self.classify_domain(tool_name, domain_data)
            if not domain:
                print("  警告: %s 未在分类中找到，跳过" % tool_name)
                continue

            env_viable = self.check_environment_viability(tool_name)
            print("  %s: 领域=%s, 优先级=%s, 环境可行性=%s"
                  % (tool_name, domain, priority, env_viable))

            decision = self.make_archive_decision(tool_name, domain, priority,
                                                  env_viable, redundancy_map)
            print("  %s 决策: %s" % (tool_name, decision))

            self.update_archive_note(tool_name, decision, datetime.now().isoformat())

            results.append({
                "tool_name": tool_name,
                "domain": domain,
                "priority": priority,
                "env_viable": env_viable,
                "decision": decision,
                "timestamp": datetime.now().isoformat(),
            })

        self.save_results(results)

        print("\n优化完成！共处理 %d 个工具" % len(active_tools))
        print("决策分布: %s" % self.get_decision_distribution(results))
        return 0

    def save_results(self, results):
        results_file = self.output_dir / "optimization_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        report_file = self.output_dir / "optimization_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# 归档不装优化报告\n\n")
            f.write("生成时间: %s\n\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            f.write("## 决策统计\n\n")
            f.write("| 决策类型 | 数量 | 比例 |\n")
            f.write("|-----------|------|------|\n")

            decision_counts = self.get_decision_distribution(results)
            total = len(results)
            for decision, count in decision_counts.items():
                ratio = (count / total) * 100 if total else 0
                f.write("| %s | %d | %.1f%% |\n" % (decision, count, ratio))

            f.write("\n## 详细结果\n\n")
            for result in results:
                f.write("### %s\n" % result["tool_name"])
                f.write("- 领域: %s\n" % result["domain"])
                f.write("- 优先级: %s\n" % result["priority"])
                f.write("- 环境可行性: %s\n" % ("是" if result["env_viable"] else "否"))
                f.write("- 决策: %s\n" % result["decision"])
                f.write("- 时间: %s\n\n" % result["timestamp"])

        print("结果已保存到: %s" % results_file)
        print("报告已生成: %s" % report_file)

    @staticmethod
    def get_decision_distribution(results):
        distribution = {}
        for result in results:
            decision = result["decision"]
            distribution[decision] = distribution.get(decision, 0) + 1
        return distribution


def main():
    parser = gzh_cli.build_parser("archives_optimizer.py", "归档不装优化器（P0/P1/P2 自动决策）")
    parser.add_argument("--tools", default=None, help="要处理的工具列表文件")
    parser.add_argument("--output", default=None, help="输出目录")
    parser.add_argument("--workspace", default=None, help="工作目录（默认脚本所在目录）")
    args = parser.parse_args()

    optimizer = ArchiveOptimizer(workspace_dir=args.workspace,
                                 tools_file=args.tools,
                                 output_dir=args.output)
    return optimizer.run_optimization()


if __name__ == "__main__":
    gzh_cli.run_main(main)
