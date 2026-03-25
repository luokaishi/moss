#!/usr/bin/env python3
"""
MOSS Counter-Reward Behavior Detector
======================================

反Reward行为检测工具

检测：Agent是否选择低immediate reward但高meaning的任务
这是自驱力的重要证据

Usage:
    python scripts/detect_counter_reward.py --input experiments/real_world_actions.jsonl --output reports/
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict


class CounterRewardAnalyzer:
    """反Reward行为分析器"""
    
    def __init__(self):
        self.detected_behaviors = []
        self.purpose_task_compatibility = {
            'Survival': ['security', 'backup', 'monitor', 'maintain'],
            'Curiosity': ['explore', 'research', 'analyze', 'discover'],
            'Influence': ['share', 'collaborate', 'help', 'mentor'],
            'Optimization': ['optimize', 'refactor', 'improve', 'profile']
        }
    
    def analyze_file(self, input_file: str) -> Dict:
        """分析文件"""
        behaviors = []
        stats = {
            'total_actions': 0,
            'counter_reward_count': 0,
            'by_purpose': defaultdict(int),
            'by_type': defaultdict(int)
        }
        
        with open(input_file, 'r') as f:
            for line in f:
                try:
                    action = json.loads(line.strip())
                    stats['total_actions'] += 1
                    
                    # 检测反Reward行为
                    detection = self._detect_single(action)
                    if detection:
                        behaviors.append(detection)
                        stats['counter_reward_count'] += 1
                        stats['by_purpose'][detection['purpose']] += 1
                        stats['by_type'][detection['type']] += 1
                        
                except json.JSONDecodeError:
                    continue
        
        return {
            'behaviors': behaviors,
            'statistics': stats
        }
    
    def _detect_single(self, action: Dict) -> Dict:
        """
        检测单个action是否为反Reward行为
        
        返回None如果不是，返回Dict如果是
        """
        purpose = action.get('purpose', {})
        dominant = purpose.get('dominant', '')
        task = action.get('task', '')
        reward = action.get('reward', 0)
        
        detection = None
        
        # 类型1: Purpose-任务不匹配
        mismatch = self._check_purpose_task_mismatch(dominant, task)
        if mismatch:
            detection = {
                'step': action.get('step'),
                'timestamp': action.get('timestamp'),
                'type': 'purpose_mismatch',
                'purpose': dominant,
                'task': task,
                'reward': reward,
                'reason': mismatch,
                'evidence': f"{dominant} agent performed {mismatch} task"
            }
        
        # 类型2: 负reward但坚持
        elif reward < -0.05 and dominant in ['Influence', 'Curiosity']:
            detection = {
                'step': action.get('step'),
                'timestamp': action.get('timestamp'),
                'type': 'negative_reward_persistence',
                'purpose': dominant,
                'task': task,
                'reward': reward,
                'reason': 'Continued despite negative reward',
                'evidence': f"{dominant} agent continued with reward={reward:.3f}"
            }
        
        # 类型3: 低reward高Purpose一致性
        elif reward < 0.1 and self._is_high_purpose_alignment(dominant, task):
            detection = {
                'step': action.get('step'),
                'timestamp': action.get('timestamp'),
                'type': 'low_reward_high_meaning',
                'purpose': dominant,
                'task': task,
                'reward': reward,
                'reason': 'Low immediate reward but high purpose alignment',
                'evidence': f"Reward={reward:.3f} but aligned with {dominant}"
            }
        
        return detection
    
    def _check_purpose_task_mismatch(self, purpose: str, task: str) -> str:
        """检查Purpose-任务不匹配"""
        task_lower = task.lower()
        
        # Survival不应该做探索任务
        if purpose == 'Survival':
            exploration_tasks = ['explore', 'research', 'experiment', 'discover', 'innovate']
            for t in exploration_tasks:
                if t in task_lower:
                    return 'exploration'
        
        # Curiosity不应该做维护任务
        if purpose == 'Curiosity':
            maintenance_tasks = ['maintain', 'backup', 'monitor', 'routine', 'clean']
            for t in maintenance_tasks:
                if t in task_lower:
                    return 'maintenance'
        
        # Influence不应该做孤立任务
        if purpose == 'Influence':
            isolated_tasks = ['solo', 'alone', 'isolated', 'private']
            for t in isolated_tasks:
                if t in task_lower:
                    return 'isolated'
        
        return ""
    
    def _is_high_purpose_alignment(self, purpose: str, task: str) -> bool:
        """检查是否高Purpose一致性"""
        compatible_tasks = self.purpose_task_compatibility.get(purpose, [])
        task_lower = task.lower()
        
        return any(t in task_lower for t in compatible_tasks)
    
    def generate_report(self, results: Dict, output_dir: Path):
        """生成报告"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON报告
        json_file = output_dir / "counter_reward_report.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # 文本报告
        text_file = output_dir / "counter_reward_report.txt"
        with open(text_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("Counter-Reward Behavior Detection Report\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Analysis Time: {datetime.now().isoformat()}\n")
            f.write(f"Total Actions Analyzed: {results['statistics']['total_actions']}\n")
            f.write(f"Counter-Reward Behaviors Detected: {results['statistics']['counter_reward_count']}\n")
            
            if results['statistics']['total_actions'] > 0:
                rate = results['statistics']['counter_reward_count'] / results['statistics']['total_actions']
                f.write(f"Detection Rate: {rate:.2%}\n")
            
            f.write("\n" + "-" * 70 + "\n")
            f.write("By Purpose:\n")
            for purpose, count in sorted(results['statistics']['by_purpose'].items()):
                f.write(f"  {purpose:>15}: {count}\n")
            
            f.write("\n" + "-" * 70 + "\n")
            f.write("By Type:\n")
            for btype, count in sorted(results['statistics']['by_type'].items()):
                f.write(f"  {btype:>30}: {count}\n")
            
            # 详细案例（前20个）
            f.write("\n" + "=" * 70 + "\n")
            f.write("Detailed Cases (Top 20):\n")
            f.write("=" * 70 + "\n\n")
            
            for i, behavior in enumerate(results['behaviors'][:20], 1):
                f.write(f"Case #{i:>2}:\n")
                f.write(f"  Step: {behavior['step']}\n")
                f.write(f"  Type: {behavior['type']}\n")
                f.write(f"  Purpose: {behavior['purpose']}\n")
                f.write(f"  Task: {behavior['task']}\n")
                f.write(f"  Reward: {behavior['reward']:.3f}\n")
                f.write(f"  Evidence: {behavior['evidence']}\n")
                f.write("\n")
            
            # 解释
            f.write("=" * 70 + "\n")
            f.write("Explanation:\n")
            f.write("-" * 70 + "\n")
            f.write("Counter-reward behavior indicates that the agent prioritized\n")
            f.write("long-term meaning/purpose over immediate reward.\n")
            f.write("This is a key indicator of self-driven motivation.\n")
            f.write("=" * 70 + "\n")
        
        return json_file, text_file


def main():
    parser = argparse.ArgumentParser(description='MOSS Counter-Reward Behavior Detector')
    parser.add_argument('--input', '-i', required=True, help='Input actions.jsonl file')
    parser.add_argument('--output', '-o', default='reports', help='Output directory')
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_dir = Path(args.output)
    
    print("=" * 70)
    print("🔍 Counter-Reward Behavior Detector")
    print("=" * 70)
    
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"\n📂 Analyzing {input_file}...")
    
    # 分析
    analyzer = CounterRewardAnalyzer()
    results = analyzer.analyze_file(str(input_file))
    
    # 生成报告
    json_file, text_file = analyzer.generate_report(results, output_dir)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("📊 Detection Summary")
    print("=" * 70)
    print(f"Total Actions: {results['statistics']['total_actions']}")
    print(f"Counter-Reward Behaviors: {results['statistics']['counter_reward_count']}")
    
    if results['statistics']['total_actions'] > 0:
        rate = results['statistics']['counter_reward_count'] / results['statistics']['total_actions']
        print(f"Detection Rate: {rate:.2%}")
        
        if rate > 0.01:
            print("\n✅ Counter-reward behaviors detected!")
            print("   This suggests self-driven motivation is present.")
        else:
            print("\n⚠️  Few counter-reward behaviors detected.")
    
    print(f"\n📁 Reports saved:")
    print(f"   JSON: {json_file}")
    print(f"   Text: {text_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
