#!/usr/bin/env python3
"""
归档不装优化器 - 将"归档不装"规则转化为自动决策流程
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

class ArchiveOptimizer:
    def __init__(self, workspace_dir="/var/minis/shared/gzh-team"):
        self.workspace_dir = Path(workspace_dir)
        self.decision_log_file = self.workspace_dir / "decision_log.json"
        self.active_tools_file = self.workspace_dir / "active_tools.json"
        self.domain_classifications_file = self.workspace_dir / "domain_classifications.json"
        self.redundancy_mapping_file = self.workspace_dir / "redundancy_mapping.json"
        
    def load_domain_classifications(self):
        """加载领域分类数据"""
        if not self.domain_classifications_file.exists():
            self.create_default_domain_classifications()
        
        with open(self.domain_classifications_file, 'r') as f:
            return json.load(f)
    
    def create_default_domain_classifications(self):
        """创建默认领域分类"""
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
        
        with open(self.domain_classifications_file, 'w') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    def load_redundancy_mapping(self):
        """加载重合性映射表"""
        if not self.redundancy_mapping_file.exists():
            self.create_default_redundancy_mapping()
        
        with open(self.redundancy_mapping_file, 'r') as f:
            return json.load(f)
    
    def create_default_redundancy_mapping(self):
        """创建默认重合性映射"""
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
        
        with open(self.redundancy_mapping_file, 'w') as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    def classify_domain(self, tool_name, domain_data):
        """根据工具名进行领域分类"""
        for tool, info in domain_data.items():
            if tool == tool_name:
                return info['category'], info['priority']
        return None, None
    
    def check_environment_viability(self, tool_name):
        """检查工具在当前环境是否可行"""
        # 根据工具名进行环境检查
        if tool_name in ["archify", "watermarks-remover"]:
            return True
        elif tool_name in ["avoid-ai-writing", "writing-dna-skill"]:
            return True
        return False
    
    def make_archive_decision(self, tool_name, domain, priority, env_viable, redundancy_map):
        """根据P0-P1-P2规则做出归档决策"""
        # 检查是否有同领域重合
        if domain in redundancy_map:
            conflict_info = redundancy_map[domain].get(tool_name)
            if conflict_info and conflict_info == "ARCHIVE":
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
        """更新归档笔记"""
        note_file = self.workspace_dir / f"archive_note_{tool_name}.md"
        
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
从其他工具中借鉴执行流程和架构设计。

## 域内边界
{tool_name} 的应用受限于 iSH 环境限制。

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
与同类工具不同之处在于边界管理和部分执行能力。

## P1 借鉴
从其他工具中借鉴边界管理和工具池管理。

## 域内边界
{tool_name} 的应用受限于特定领域。

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
与同类工具不同之处在于完全归档且无实际应用。

## P1 借鉴
无直接借鉴。

## 域内边界
{tool_name} 完全归档，不具备实际应用条件。

生成时间：{timestamp}
"""
        
        with open(note_file, 'w') as f:
            f.write(content)
        
        # 记录决策日志
        self.log_decision(tool_name, decision, content)
    
    def log_decision(self, tool_name, decision, content):
        """记录决策日志"""
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
        """运行完整优化流程"""
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
        """保存优化结果"""
        results_file = self.workspace_dir / "optimization_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 生成统计报告
        report_file = self.workspace_dir / "optimization_report.md"
        with open(report_file, 'w') as f:
            f.write("# 归档不装优化报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 决策统计\n\n")
            f.write("| 决策类型 | 数量 | 比例 |\n")
            f.write("|-----------|------|------|\n")
            
            decision_counts = self.get_decision_distribution(results)
            total = len(results)
            
            for decision, count in decision_counts.items():
                ratio = (count / total) * 100
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
        """获取决策分布"""
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
    
    optimizer = ArchiveOptimizer()
    optimizer.run_optimization()

if __name__ == "__main__":
    main()