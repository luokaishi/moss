#!/usr/bin/env python3
"""
MOSS 分支同步检测脚本
检测 main 与 mves 分支差异

Usage:
    python scripts/sync_detector.py [--detailed]
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class FileDiff:
    path: str
    status: str  # added, modified, deleted
    lines_added: int = 0
    lines_removed: int = 0


class SyncDetector:
    """检测 main 与 mves 分支差异"""
    
    # Main 分支特有优化 (需同步到 mves)
    MAIN_OPTIMIZATIONS = [
        "moss/core/llm_cost_controller.py",
        "moss/core/statistical_validator.py",
        "moss/core/agent_bridge.py",
        "moss/core/autonomous_loop.py",
        "moss/core/hybrid_mutation.py",
        "moss/core/llm_backend.py",
    ]
    
    # MVES 分支生产组件 (需同步到 main)
    MVES_COMPONENTS = [
        "agi/event_driven_purpose.py",
        "agi/monitoring_dashboard.py",
        "agi/mves_realworld_bridge.py",
        "agi/auto_recovery.py",
    ]
    
    # 可能冲突的文件
    POTENTIAL_CONFLICTS = [
        "agi/hybrid_mutation.py",
        "agi/llm_mutator.py",
        "agi/genetic_programmer.py",
    ]
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.results = {
            "main_only": [],
            "mves_only": [],
            "both_modified": [],
            "sync_status": {}
        }
    
    def run_git_diff(self, base: str = "main", compare: str = "mves-local") -> List[FileDiff]:
        """运行 git diff 获取差异"""
        try:
            result = subprocess.run(
                ["git", "diff", f"{base}...{compare}", "--name-status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            diffs = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    path = parts[1]
                    diffs.append(FileDiff(path=path, status=status))
            
            return diffs
        except Exception as e:
            print(f"Error running git diff: {e}")
            return []
    
    def categorize_files(self, diffs: List[FileDiff]) -> Dict:
        """分类文件差异"""
        diff_paths = {d.path for d in diffs}
        
        # 检查 main 优化是否已在 mves
        for opt in self.MAIN_OPTIMIZATIONS:
            if opt in diff_paths:
                self.results["main_only"].append({
                    "file": opt,
                    "action": "port_to_mves",
                    "priority": "P0"
                })
        
        # 检查 mves 组件是否已在 main
        for comp in self.MVES_COMPONENTS:
            if comp in diff_paths:
                self.results["mves_only"].append({
                    "file": comp,
                    "action": "merge_to_main",
                    "priority": "P0"
                })
        
        # 检查冲突
        for conflict in self.POTENTIAL_CONFLICTS:
            if conflict in diff_paths:
                self.results["both_modified"].append({
                    "file": conflict,
                    "action": "manual_resolve",
                    "priority": "P1"
                })
        
        return self.results
    
    def generate_report(self) -> str:
        """生成同步状态报告"""
        report = []
        report.append("# MOSS 分支同步检测报告")
        report.append("")
        report.append("## 执行摘要")
        report.append("")
        report.append(f"- Main 特有优化 (待移植): {len(self.results[main_only])} 个")
        report.append(f"- MVES 特有组件 (待合并): {len(self.results[mves_only])} 个")
        report.append(f"- 冲突文件 (需手动解决): {len(self.results[both_modified])} 个")
        report.append("")
        
        if self.results["main_only"]:
            report.append("## Main → MVES 移植清单 (P0)")
            report.append("")
            for item in self.results["main_only"]:
                report.append(f"- [ ] `{item[file]}`")
            report.append("")
        
        if self.results["mves_only"]:
            report.append("## MVES → Main 合并清单 (P0)")
            report.append("")
            for item in self.results["mves_only"]:
                report.append(f"- [ ] `{item[file]}`")
            report.append("")
        
        if self.results["both_modified"]:
            report.append("## 冲突文件 (P1)")
            report.append("")
            for item in self.results["both_modified"]:
                report.append(f"- [ ] `{item[file]}` (需手动解决)")
            report.append("")
        
        report.append("## 建议行动")
        report.append("")
        report.append("1. 立即执行: 移植 Token 预算控制和统计验证框架到 mves")
        report.append("2. 本周完成: 合并 MVES 生产组件到 main")
        report.append("3. 下周处理: 手动解决冲突文件")
        report.append("")
        
        return "\n".join(report)
    
    def save_sync_map(self, output: str = "sync_map.json"):
        """保存同步映射表"""
        sync_map = {
            "version": "1.0",
            "generated": "2026-04-25",
            "main_to_mves": [
                {
                    "source": "moss/core/llm_cost_controller.py",
                    "target": "agi/cost_controller.py",
                    "priority": "P0",
                    "notes": "Token 预算优化，基于 mves v8.6 经验"
                },
                {
                    "source": "moss/core/statistical_validator.py",
                    "target": "experiments/statistical_validator.py",
                    "priority": "P0",
                    "notes": "学术级统计验证框架"
                }
            ],
            "mves_to_main": [
                {
                    "source": "agi/event_driven_purpose.py",
                    "target": "moss/core/event_driven_purpose.py",
                    "priority": "P0",
                    "notes": "事件驱动 Purpose 生成"
                },
                {
                    "source": "agi/monitoring_dashboard.py",
                    "target": "moss/core/monitoring_dashboard.py",
                    "priority": "P1",
                    "notes": "生产级监控仪表盘"
                }
            ]
        }
        
        with open(output, "w") as f:
            json.dump(sync_map, f, indent=2)
        
        print(f"Sync map saved to {output}")


def main():
    detector = SyncDetector()
    
    print("🔍 检测 MOSS 分支差异...")
    diffs = detector.run_git_diff()
    print(f"   发现 {len(diffs)} 个差异文件")
    
    print("📊 分类文件...")
    detector.categorize_files(diffs)
    
    print("📝 生成报告...")
    report = detector.generate_report()
    
    # 保存报告
    report_path = "SYNC_REPORT.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"   报告已保存: {report_path}")
    
    # 保存同步映射
    detector.save_sync_map()
    
    print("\n" + report)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
