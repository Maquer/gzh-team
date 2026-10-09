#!/usr/bin/env python3
"""archives_optimizer.py：归档不装优化器，按 P0/P1/P2 规则自动决策工具归档
用法：python3 archives_optimizer.py — 定期运行时自动处理 active_tools.json 中所有工具
关键约束：需在 gzh-team 工作目录执行，输出 optimization_results.json + archive_note_*.md
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

class ArchiveOptimizer:
    def __init__(self, workspace_dir=None, tools_file=None, output_dir=None):
        self.workspace_dir = Path(workspace_dir or Path(__file__).resolve().parent)
        self.output_dir = Path(output_dir) if output_dir else self.workspace_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.decision_log_file = self.workspace_dir / "decision_log.json"
        self.active_tools_file = Path(tools_file) if tools_file else self.workspace_dir / "active_tools.json"
        self.domain_classifications_file = self.workspace_dir / "domain_classifications.json"
        self.redundancy_mapping_file = self.workspace_dir / "redundancy_mapping.json"
        
    def load_domain_classifications(self):
        default_data = {
            "archify": {
                "category": "tool-development",
                "priority": "P0"
            },
            "watermarks-remover": {
                "category": "tool-development",
                "priority": "P0"
            },
            "avoid-ai-writing": {
                "category": "content-creation",
                "priority": "P1"
            },
            "writing-dna-skill": {
                "category": "content-creation",
                "priority": "P1"
            }
        }
        
        return self._load_or_init(self.domain_classifications_file, default_data)
    
    def load_redundancy_mapping(self):
        default_data = {
            "content-creation": {
                "avoid-ai-writing": "PARTIAL",
                "writing-dna-skill": "PARTIAL"
            },
            "tool-development": {
                "archify": "ACTIVE",
                "watermarks-remover": "ACTIVE"
            }
        }
        
        return self._load_or_init(self.redundancy_mapping_file, default_data)
    
    @staticmethod
    def _load_or_init(path, default_data):
        """文件存在则读取；不存在则写入默认值并返回默认值。"""
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        return default_data

    def load_active_tools(self):
        if not self.active_tools_file.exists():
            return []
        with open(self.active_tools_file, 'r', encoding='utf-8') as f:
            tools = json.load(f)
        self._tool_records = {t['name']: t for t in tools if 'name' in t}
        return tools

    def classify_domain(self, tool_name, domain_data):
        """返回 (领域, 优先级)；分类表里没有该工具时返回 (None, None)。"""
        info = domain_data.get(tool_name)
        if not info:
            rec = getattr(self, '_tool_records', {}).get(tool_name, {})
            if rec.get('domain') and rec.get('priority'):
                return rec['domain'], rec['priority']
            return None, None
        return info.get('category'), info.get('priority')

    def check_environment_viability(self, tool_name):
        """环境可行性：active_tools.json 中状态为 ARCHIVE/ARCHIVED 视为不可行，其余可行。"""
        rec = getattr(self, '_tool_records', {}).get(tool_name, {})
        return str(rec.get('status', 'ACTIVE')).upper() not in ('ARCHIVE', 'ARCHIVED', 'ARCHIVE_ONLY')

    def make_archive_decision(self, tool_name, domain, priority, env_viable, redundancy_map):
        # 检查是否有同领域重合
        if domain in redundancy_map:
            conflict_info = redundancy_map[domain].get(tool_name)
            if conflict_info and str(conflict_info).strip().upper().startswith("ARCHIVE"):
                return "ARCHIVE_ONLY"
        
        # P0-P1-P2三重决策
        if priority == "P0":
            if env_viable:
                return "FORCE_INSTALL"
            else:
                return "ARCHIVE_ONLY"
        elif priority == "P1":
            if env_viable:
                return "PARTIAL_INSTALL"
            else:
                return "ARCHIVE_ONLY"
        elif priority == "P2":
            return "ARCHIVE_ONLY"
        else:
            return "ARCHIVE_ONLY"
    
    def update_archive_note(self, tool_name, decision, timestamp):
        note_file = self.output_dir / f"archive_note_{tool_name}.md"
        # FORCE_INSTALL（P0）
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
从其他工具中借鉴执行流程和架构设计。

## 域内边界
{tool_name} 的应用受限于 iSH 环境限制。

生成时间：{timestamp}
"""
        if decision == "PARTIAL_INSTALL":
            content = f"""# {tool_name}
> 核心价值：P1 部分执行工具
> 决策边界：环境可用性与领域重合度
> P1 借鉴：边界管理和工具池管理
> 域内边界：特定领域工具

## 核心定位
{tool_name} 是 P1 级工具，在特定领域有限执行。

## 核心差异
与同类工具不同之处在于边界管理和部分执行能力。

## P1 借鉴
从其他工具中借鉴边界管理和工具池管理。

## 域内边界
{tool_name} 的应用受限于特定领域。

生成时间：{timestamp}
"""
        elif decision == "ARCHIVE_ONLY":
            content = f"""# {tool_name}
> 核心价值：P2/P3 仅归档工具
> 决策边界：环境不可用 + 领域错位
> P1 借鉴：无直接借鉴
> 域内边界：完全归档工具

## 核心定位
{tool_name} 归档仅供参考，无实际执行能力。

## 核心差异
与同类工具不同之处在于完全归档且无实际应用。

## P1 借鉴
无直接借鉴。

## 域内边界
{tool_name} 完全归档，不具备实际应用条件。

生成时间：{timestamp}
"""
        
        with open(note_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 记录决策日志
        self.log_decision(tool_name, decision, content)
    
    def log_decision(self, tool_name, decision, content):
        if not self.decision_log_file.exists():
            decision_data = []
        else:
            with open(self.decision_log_file, 'r') as f:
                decision_data = json.load(f)
        
        decision_record = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "decision": decision,
            "content": content[:500] + "..." if len(content) > 500 else content
        }
        
        decision_data.append(decision_record)
        
        with open(self.decision_log_file, 'w') as f:
            json.dump(decision_data, f, indent=2, ensure_ascii=False)
    
    def run_optimization(self):
        print("开始归档不装优化流程...")
        
        # 加载数据
        domain_data = self.load_domain_classifications()
        redundancy_map = self.load_redundancy_mapping()
        active_tools = self.load_active_tools()
        
        print(f"\n正在处理 {len(active_tools)} 个活跃工具...")
        
        # 处理每个工具
        results = []
        for tool in active_tools:
            tool_name = tool['name']
            
            # 获取工具信息
            domain, priority = self.classify_domain(tool_name, domain_data)
            if not domain:
                print(f"  警告: {tool_name} 未在分类中找到，跳过")
                continue
            
            # 检查环境可行性
            env_viable = self.check_environment_viability(tool_name)
            print(f"  {tool_name}: 领域={domain}, 优先级={priority}, 环境可行性={env_viable}")
            
            # 做出决策
            decision = self.make_archive_decision(tool_name, domain, priority, env_viable, redundancy_map)
            print(f"  {tool_name} 决策: {decision}")
            
            # 更新归档笔记
            self.update_archive_note(tool_name, decision, datetime.now().isoformat())
            
            # 记录结果
            results.append({
                "tool_name": tool_name,
                "domain": domain,
                "priority": priority,
                "env_viable": env_viable,
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            })
        
        # 保存结果
        self.save_results(results)
        
        print(f"\n优化完成！共处理 {len(active_tools)} 个工具")
        print(f"决策分布: {self.get_decision_distribution(results)}")
    
    def save_results(self, results):
        results_file = self.output_dir / "optimization_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 生成统计报告
        report_file = self.output_dir / "optimization_report.md"
        with open(report_file, 'w') as f:
            f.write("# 归档不装优化报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 决策统计\n\n")
            f.write("| 决策类型 | 数量 | 比例 |\n")
            f.write("|-----------|------|------|\n")
            
            decision_counts = self.get_decision_distribution(results)
            total = len(results)
            
            for decision, count in decision_counts.items():
                ratio = (count / total) * 100 if total else 0
                f.write(f"| {decision} | {count} | {ratio:.1f}% |\n")
            
            f.write("\n## 详细结果\n\n")
            for result in results:
                f.write(f"### {result['tool_name']}\n")
                f.write(f"- 领域: {result['domain']}\n")
                f.write(f"- 优先级: {result['priority']}\n")
                f.write(f"- 环境可行性: {'是' if result['env_viable'] else '否'}\n")
                f.write(f"- 决策: {result['decision']}\n")
                f.write(f"- 时间: {result['timestamp']}\n\n")
        
        print(f"结果已保存到: {results_file}")
        print(f"报告已生成: {report_file}")
    
    def get_decision_distribution(self, results):
        distribution = {}
        for result in results:
            decision = result['decision']
            distribution[decision] = distribution.get(decision, 0) + 1
        return distribution

def main():
    parser = argparse.ArgumentParser(description="归档不装优化器")
    parser.add_argument("--tools", help="要处理的工具列表文件")
    parser.add_argument("--output", help="输出目录")
    
    args = parser.parse_args()
    
    optimizer = ArchiveOptimizer(tools_file=args.tools, output_dir=args.output)
    optimizer.run_optimization()

if __name__ == "__main__":
    main()