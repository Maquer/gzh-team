#!/usr/bin/env python3
"""
归档笔记精简生成器 - 根据"归档不装"决策生成精简归档笔记
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

class ArchiveNoteGenerator:
    def __init__(self, workspace_dir="/var/minis/shared/gzh-team"):
        self.workspace_dir = Path(workspace_dir)
        self.decision_log_file = self.workspace_dir / "decision_log.json"
        self.active_tools_file = self.workspace_dir / "active_tools.json"
        
    def load_decisions(self):
        """加载决策日志"""
        if not self.decision_log_file.exists():
            return []
        
        with open(self.decision_log_file, 'r') as f:
            return json.load(f)
    
    def load_active_tools(self):
        """加载活跃工具列表"""
        if not self.active_tools_file.exists():
            return []
        
        with open(self.active_tools_file, 'r') as f:
            return json.load(f)
    
    def generate_note_content(self, tool_name, decision, timestamp):
        """生成归档笔记内容"""
        if decision == "FORCE_INSTALL":
            content = f"""# {tool_name}
> 核心价值：P0 强制执行工具
> 决策边界：环境不可用则归档
> P1 借鉴：架构设计与执行流程
> 域内边界：iSH 环境限制

## 核心定位
{tool_name} 是 P0 级工具，在当前环境中强制执行。

## 核心差异
与同类工具不同之处在于自动化执行能力。

## P1 借鉴
从[工具名]中借鉴执行流程和架构设计。[借鉴细节]

## 域内边界
{tool_name} 的应用受限于[环境限制]。

生成时间：{timestamp}
"""
        elif decision == "PARTIAL_INSTALL":
            content = f"""# {tool_name}
> 核心价值：P1 部分执行工具
> 决策边界：环境可用性与领域重合度
> P1 借鉴：边界管理和工具池管理
> 域内边界：特定领域工具

## 核心定位
{tool_name} 是 P1 级工具，在特定领域有限执行。

## 核心差异
与同类工具不同之处在于边界管理和部分执行能力。[具体差异]

## P1 借鉴
从[工具名]中借鉴边界管理和工具池管理。[借鉴细节]

## 域内边界
{tool_name} 的应用受限于[特定领域]。

生成时间：{timestamp}
"""
        else:  # ARCHIVE_ONLY
            content = f"""# {tool_name}
> 核心价值：P2/P3 仅归档工具
> 决策边界：环境不可用 + 领域错位
> P1 借鉴：无直接借鉴
> 域内边界：完全归档工具

## 核心定位
{tool_name} 归档仅供参考，无实际执行能力。

## 核心差异
与同类工具不同之处在于完全归档且无实际应用。[具体差异]

## P1 借鉴
无直接借鉴。

## 域内边界
{tool_name} 完全归档，不具备实际应用条件。

生成时间：{timestamp}
"""
        return content
    
    def generate_all_notes(self):
        """生成所有归档笔记"""
        print("开始生成归档笔记...")
        
        # 加载数据
        decisions = self.load_decisions()
        active_tools = self.load_active_tools()
        
        # 创建归档笔记目录
        notes_dir = self.workspace_dir / "archive_notes"
        notes_dir.mkdir(exist_ok=True)
        
        # 生成每个活跃工具的归档笔记
        generated_notes = []
        for tool in active_tools:
            tool_name = tool['name']
            
            # 查找对应的决策
            tool_decision = None
            tool_timestamp = None
            for decision in decisions:
                if decision['tool_name'] == tool_name:
                    tool_decision = decision['decision']
                    tool_timestamp = decision['timestamp']
                    break
            
            if not tool_decision:
                print(f"  警告: {tool_name} 没有对应的决策，跳过")
                continue
            
            # 生成归档笔记
            note_content = self.generate_note_content(tool_name, tool_decision, tool_timestamp)
            
            # 保存归档笔记
            note_file = notes_dir / f"archive_note_{tool_name}.md"
            with open(note_file, 'w') as f:
                f.write(note_content)
            
            generated_notes.append({
                "tool_name": tool_name,
                "decision": tool_decision,
                "note_file": str(note_file)
            })
            
            print(f"  已生成归档笔记: {tool_name} ({tool_decision})")
        
        # 生成汇总报告
        self.generate_summary_report(generated_notes)
        
        print(f"\n归档笔记生成完成！共生成 {len(generated_notes)} 个归档笔记")
        return generated_notes
    
    def generate_summary_report(self, generated_notes):
        """生成汇总报告"""
        report_file = self.workspace_dir / "archive_generation_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# 归档笔记生成报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 统计信息
            f.write("## 统计信息\n\n")
            f.write(f"总归档笔记数: {len(generated_notes)}\n\n")
            
            # 按决策类型统计
            decision_counts = {}
            for note in generated_notes:
                decision = note['decision']
                decision_counts[decision] = decision_counts.get(decision, 0) + 1
            
            f.write("决策类型分布:\n\n")
            f.write("| 决策类型 | 数量 | 比例 |\n")
            f.write("|-----------|------|------|\n")
            
            total = len(generated_notes)
            for decision, count in decision_counts.items():
                ratio = (count / total) * 100
                f.write(f"| {decision} | {count} | {ratio:.1f}% |\n")
            
            f.write("\n")
            
            # 详细列表
            f.write("## 归档笔记列表\n\n")
            for note in generated_notes:
                f.write(f"### {note['tool_name']}\n")
                f.write(f"- 决策: {note['decision']}\n")
                f.write(f"- 文件: {note['note_file']}\n\n")
        
        print(f"汇总报告已生成: {report_file}")
    
    def run(self):
        """运行归档笔记生成器"""
        self.generate_all_notes()

def main():
    parser = argparse.ArgumentParser(description="归档笔记生成器")
    parser.add_argument("--tools", help="要生成的工具列表文件")
    
    args = parser.parse_args()
    
    generator = ArchiveNoteGenerator()
    generator.run()

if __name__ == "__main__":
    main()