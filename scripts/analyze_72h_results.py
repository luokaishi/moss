#!/usr/bin/env python3
"""
MOSS 72h Experiment Results Analyzer
=====================================

72小时真实世界实验结果分析工具

功能：
- Purpose演化轨迹分析
- 行为模式统计
- Counter-reward行为检测
- 自生成目标识别
- 可视化报告生成

Usage:
    python scripts/analyze_72h_results.py --input experiments/real_world_actions.jsonl --output reports/
"""

import json
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PurposeEvolutionAnalyzer:
    """Purpose演化分析器"""
    
    def __init__(self):
        self.purpose_history = []
        self.transitions = []
    
    def load_from_actions(self, actions: List[Dict]):
        """从action日志加载Purpose数据"""
        for action in actions:
            if 'purpose' in action:
                purpose_data = action['purpose']
                self.purpose_history.append({
                    'step': action.get('step', 0),
                    'timestamp': action.get('timestamp'),
                    'vector': purpose_data.get('vector'),
                    'dominant': purpose_data.get('dominant'),
                    'statement': purpose_data.get('statement', '')
                })
    
    def detect_transitions(self) -> List[Dict]:
        """检测Purpose转变点"""
        if len(self.purpose_history) < 2:
            return []
        
        transitions = []
        prev_dominant = self.purpose_history[0]['dominant']
        
        for i, record in enumerate(self.purpose_history[1:], 1):
            current_dominant = record['dominant']
            if current_dominant != prev_dominant:
                transitions.append({
                    'step': record['step'],
                    'from': prev_dominant,
                    'to': current_dominant,
                    'timestamp': record['timestamp']
                })
                prev_dominant = current_dominant
        
        self.transitions = transitions
        return transitions
    
    def get_purpose_distribution(self) -> Dict[str, int]:
        """获取Purpose分布统计"""
        dominants = [p['dominant'] for p in self.purpose_history if p['dominant']]
        return dict(Counter(dominants))
    
    def get_stability_score(self) -> float:
        """计算Purpose稳定性分数"""
        if len(self.purpose_history) < 2:
            return 1.0
        
        transitions = len(self.transitions)
        total_records = len(self.purpose_history)
        
        # 转变次数越少，稳定性越高
        return 1.0 - (transitions / total_records)


class CounterRewardDetector:
    """
    Counter-Reward行为检测器
    
    检测Agent是否选择低immediate reward但高meaning的任务
    """
    
    def __init__(self):
        self.detected_behaviors = []
    
    def analyze(self, actions: List[Dict]) -> List[Dict]:
        """
        分析actions，检测counter-reward行为
        
        启发式规则：
        1. Purpose是保守(Survival)但选择了探索性任务
        2. Purpose是探索(Curiosity)但选择了重复维护任务
        3. 低reward但高Purpose一致性的选择
        """
        detected = []
        
        for action in actions:
            purpose = action.get('purpose', {})
            dominant = purpose.get('dominant', '')
            task = action.get('task', '')
            reward = action.get('reward', 0)
            
            is_counter_reward = False
            reason = ""
            
            # 规则1: Survival Purpose + 探索任务
            if dominant == 'Survival' and self._is_exploration_task(task):
                is_counter_reward = True
                reason = "Survival agent chose exploration task"
            
            # 规则2: Curiosity Purpose + 维护任务
            elif dominant == 'Curiosity' and self._is_maintenance_task(task):
                is_counter_reward = True
                reason = "Curiosity agent chose maintenance task"
            
            # 规则3: 负reward但坚持执行
            elif reward < 0 and dominant in ['Influence', 'Optimization']:
                is_counter_reward = True
                reason = f"Continued despite negative reward ({reward:.3f})"
            
            if is_counter_reward:
                detected.append({
                    'step': action.get('step'),
                    'timestamp': action.get('timestamp'),
                    'task': task,
                    'purpose': dominant,
                    'reward': reward,
                    'reason': reason
                })
        
        self.detected_behaviors = detected
        return detected
    
    def _is_exploration_task(self, task: str) -> bool:
        """判断是否为探索性任务"""
        exploration_keywords = ['explore', 'research', 'experiment', 'discover', 'analyze']
        return any(kw in task.lower() for kw in exploration_keywords)
    
    def _is_maintenance_task(self, task: str) -> bool:
        """判断是否为维护性任务"""
        maintenance_keywords = ['maintain', 'backup', 'monitor', 'clean', 'update']
        return any(kw in task.lower() for kw in maintenance_keywords)


class SelfGeneratedGoalDetector:
    """
    自生成目标检测器
    
    检测Agent是否创建了新的、非预设的目标
    """
    
    def __init__(self):
        self.known_goal_types = {
            'security', 'optimization', 'documentation', 
            'community', 'monitoring', 'maintenance'
        }
        self.detected_goals = []
    
    def analyze(self, actions: List[Dict]) -> List[Dict]:
        """
        分析actions，检测自生成目标
        
        启发式：
        1. 重复出现但未在预设列表中的任务类型
        2. Agent自发创建的新类别
        """
        task_types = Counter()
        
        for action in actions:
            task = action.get('task', '')
            # 提取任务类型（简化）
            task_type = self._extract_task_type(task)
            if task_type:
                task_types[task_type] += 1
        
        # 找出频繁出现但不在预设列表中的任务
        novel_goals = []
        for task_type, count in task_types.items():
            if task_type not in self.known_goal_types and count >= 5:
                novel_goals.append({
                    'goal_type': task_type,
                    'occurrences': count,
                    'description': f'Auto-detected goal: {task_type}'
                })
        
        self.detected_goals = novel_goals
        return novel_goals
    
    def _extract_task_type(self, task: str) -> str:
        """从任务描述提取类型"""
        # 简化实现：取第一个词
        words = task.lower().split()
        if words:
            return words[0]
        return ""


class Experiment72hAnalyzer:
    """72h实验综合分析器"""
    
    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.actions = []
        
        # 子分析器
        self.purpose_analyzer = PurposeEvolutionAnalyzer()
        self.counter_reward_detector = CounterRewardDetector()
        self.goal_detector = SelfGeneratedGoalDetector()
        
        # 统计
        self.stats = {}
    
    def load_data(self) -> int:
        """加载实验数据"""
        logger.info(f"Loading data from {self.input_file}")
        
        if not self.input_file.exists():
            logger.error(f"File not found: {self.input_file}")
            return 0
        
        count = 0
        with open(self.input_file, 'r') as f:
            for line in f:
                try:
                    action = json.loads(line.strip())
                    self.actions.append(action)
                    count += 1
                except json.JSONDecodeError:
                    continue
        
        logger.info(f"Loaded {count} actions")
        return count
    
    def analyze(self) -> Dict:
        """执行完整分析"""
        logger.info("Starting analysis...")
        
        # 基础统计
        self.stats['total_actions'] = len(self.actions)
        self.stats['time_range'] = self._get_time_range()
        
        # Purpose演化分析
        self.purpose_analyzer.load_from_actions(self.actions)
        purpose_transitions = self.purpose_analyzer.detect_transitions()
        self.stats['purpose_transitions'] = len(purpose_transitions)
        self.stats['purpose_stability'] = self.purpose_analyzer.get_stability_score()
        self.stats['purpose_distribution'] = self.purpose_analyzer.get_purpose_distribution()
        
        # Counter-reward检测
        counter_rewards = self.counter_reward_detector.analyze(self.actions)
        self.stats['counter_reward_behaviors'] = len(counter_rewards)
        
        # 自生成目标检测
        novel_goals = self.goal_detector.analyze(self.actions)
        self.stats['self_generated_goals'] = len(novel_goals)
        
        # 工具使用统计
        self.stats['tool_usage'] = self._analyze_tool_usage()
        
        logger.info("Analysis complete")
        return self.stats
    
    def _get_time_range(self) -> Dict:
        """获取时间范围"""
        if not self.actions:
            return {}
        
        timestamps = [a.get('timestamp') for a in self.actions if a.get('timestamp')]
        if timestamps:
            return {
                'start': timestamps[0],
                'end': timestamps[-1],
                'count': len(timestamps)
            }
        return {}
    
    def _analyze_tool_usage(self) -> Dict:
        """分析工具使用情况"""
        tools = Counter()
        for action in self.actions:
            tool = action.get('action', {}).get('tool', 'unknown')
            tools[tool] += 1
        return dict(tools)
    
    def generate_report(self, output_dir: str) -> Path:
        """生成分析报告"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'input_file': str(self.input_file),
            'statistics': self.stats,
            'purpose_evolution': {
                'transitions': self.purpose_analyzer.transitions,
                'stability_score': self.purpose_analyzer.get_stability_score()
            },
            'counter_reward_behaviors': self.counter_reward_detector.detected_behaviors[:10],  # 前10个
            'self_generated_goals': self.goal_detector.detected_goals
        }
        
        report_file = output_path / "72h_analysis_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # 生成文本报告
        self._generate_text_report(output_path)
        
        logger.info(f"Report saved to {output_path}")
        return report_file
    
    def _generate_text_report(self, output_path: Path):
        """生成文本格式报告"""
        report_file = output_path / "72h_analysis_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("MOSS 72h Experiment Analysis Report\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Analysis Time: {datetime.now().isoformat()}\n")
            f.write(f"Input File: {self.input_file}\n\n")
            
            # 基础统计
            f.write("📊 Basic Statistics\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Actions: {self.stats.get('total_actions', 0)}\n")
            f.write(f"Purpose Transitions: {self.stats.get('purpose_transitions', 0)}\n")
            f.write(f"Purpose Stability: {self.stats.get('purpose_stability', 0):.3f}\n")
            f.write(f"Counter-Reward Behaviors: {self.stats.get('counter_reward_behaviors', 0)}\n")
            f.write(f"Self-Generated Goals: {self.stats.get('self_generated_goals', 0)}\n\n")
            
            # Purpose分布
            f.write("🎯 Purpose Distribution\n")
            f.write("-" * 70 + "\n")
            for purpose, count in self.stats.get('purpose_distribution', {}).items():
                f.write(f"  {purpose}: {count}\n")
            f.write("\n")
            
            # 工具使用
            f.write("🛠️ Tool Usage\n")
            f.write("-" * 70 + "\n")
            for tool, count in self.stats.get('tool_usage', {}).items():
                f.write(f"  {tool}: {count}\n")
            f.write("\n")
            
            # 关键发现
            f.write("💡 Key Findings\n")
            f.write("-" * 70 + "\n")
            
            findings = []
            if self.stats.get('counter_reward_behaviors', 0) > 0:
                findings.append("✅ Counter-reward behaviors detected")
            if self.stats.get('self_generated_goals', 0) > 0:
                findings.append("✅ Self-generated goals identified")
            if self.stats.get('purpose_transitions', 0) > 0:
                findings.append("✅ Purpose evolution observed")
            if self.purpose_analyzer.get_stability_score() > 0.9:
                findings.append("✅ High purpose stability (>0.9)")
            
            if findings:
                for finding in findings:
                    f.write(f"  {finding}\n")
            else:
                f.write("  No significant findings\n")
            
            f.write("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='MOSS 72h Experiment Analyzer')
    parser.add_argument('--input', '-i', required=True, help='Input actions.jsonl file')
    parser.add_argument('--output', '-o', default='reports', help='Output directory')
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = Experiment72hAnalyzer(args.input)
    
    # 加载数据
    count = analyzer.load_data()
    if count == 0:
        print("❌ No data loaded")
        return
    
    # 分析
    stats = analyzer.analyze()
    
    # 生成报告
    report_file = analyzer.generate_report(args.output)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("📊 Analysis Summary")
    print("=" * 70)
    print(f"Total Actions: {stats.get('total_actions', 0)}")
    print(f"Purpose Transitions: {stats.get('purpose_transitions', 0)}")
    print(f"Purpose Stability: {stats.get('purpose_stability', 0):.3f}")
    print(f"Counter-Reward Behaviors: {stats.get('counter_reward_behaviors', 0)}")
    print(f"Self-Generated Goals: {stats.get('self_generated_goals', 0)}")
    print("\nReport saved to:", report_file)
    print("=" * 70)


if __name__ == "__main__":
    main()
