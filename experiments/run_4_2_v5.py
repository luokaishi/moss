#!/usr/bin/env python3
"""
MOSS Run 4.2-v5 - Refactored with Unified Architecture
=======================================================

使用v5.0统一架构重构的Run 4.2实验

验证：新框架能否复现Run 4.x的实验结果

Duration: 12 hours
Target: 4,320,000 steps
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
from moss.experiments import ExperimentConfig, BaseExperiment
import numpy as np
from datetime import datetime
from pathlib import Path


class Run42Experiment(BaseExperiment):
    """
    Run 4.2 重构版 - Purpose演化验证实验
    
    研究问题：初始Purpose为Survival时，系统如何演化？
    """
    
    def __init__(self, output_dir: str = "experiments/run_4_2_v5"):
        # 配置Agent（模拟v4.2特性）
        agent_config = MOSSConfig(
            agent_id="run_4_2_v5",
            enable_purpose=True,
            purpose_interval=1000,  # 每1000步检查Purpose
            enable_coherence=True,
            enable_valence=True,
            log_dir=output_dir
        )
        
        # 配置实验
        exp_config = ExperimentConfig(
            experiment_id="run_4_2_v5",
            duration_hours=12,  # 12小时
            checkpoint_interval=1000,
            log_interval=100,
            output_dir=output_dir
        )
        
        # 创建Agent
        self.agent = UnifiedMOSSAgent(agent_config)
        
        super().__init__(exp_config, self.agent)
        
        # Run 4.2特定配置
        self.initial_purpose = "Survival"
        self.exploration_rate = 0.10  # 10%探索率
        
        # 初始化统计数据
        self.purpose_transitions = []
        self.dominant_purposes = []
        
        print(f"[Run4.2v5] Initialized with initial purpose: {self.initial_purpose}")
    
    def setup(self):
        """实验设置"""
        # 设置初始权重偏向Survival
        self.agent.weights = np.array([0.60, 0.10, 0.20, 0.10])
        print(f"[Run4.2v5] Initial weights set: {self.agent.weights}")
    
    def run_step(self, step: int):
        """单步执行"""
        # 创建模拟观察（简化版）
        observation = {
            'critical': False,
            'warning': False,
            'phase': self._detect_phase(step)
        }
        
        # 执行Agent step
        result = self.agent.step(observation)
        
        # 记录Purpose变化
        if self.agent.purpose_generator:
            current_purpose = self.agent.purpose_generator.purpose_statement
            self.dominant_purposes.append({
                'step': step,
                'purpose': current_purpose,
                'vector': self.agent.purpose_generator.purpose_vector.tolist()
            })
        
        return result
    
    def _detect_phase(self, step: int) -> str:
        """检测当前阶段（模拟Phase变化）"""
        total_steps = self.config.duration_steps
        
        # 简化的Phase划分
        if step < total_steps * 0.33:
            return "Threat"  # 威胁阶段
        elif step < total_steps * 0.66:
            return "Growth"  # 成长阶段
        else:
            return "Social"  # 社交阶段
    
    def teardown(self):
        """实验结束处理"""
        # 保存Purpose演化轨迹
        purpose_file = self.output_dir / "purpose_evolution.json"
        with open(purpose_file, 'w') as f:
            json.dump({
                'transitions': self.purpose_transitions,
                'dominant_purposes': self.dominant_purposes,
                'final_purpose': self.agent.purpose_generator.purpose_statement if self.agent.purpose_generator else None
            }, f, indent=2)
        
        print(f"[Run4.2v5] Purpose evolution saved to {purpose_file}")
    
    def _generate_summary(self) -> dict:
        """生成实验摘要"""
        base_summary = super()._generate_summary()
        
        # 添加Run 4.2特定指标
        base_summary['run_4_2_specific'] = {
            'initial_purpose': self.initial_purpose,
            'exploration_rate': self.exploration_rate,
            'purpose_transitions': len(self.purpose_transitions),
            'final_purpose_vector': self.agent.purpose_generator.purpose_vector.tolist() if self.agent.purpose_generator else None
        }
        
        return base_summary


def quick_test():
    """快速测试模式（5分钟）"""
    print("=" * 70)
    print("🚀 Run 4.2-v5 Quick Test Mode (5 minutes)")
    print("=" * 70)
    
    agent_config = MOSSConfig(
        agent_id="run_4_2_test",
        enable_purpose=True,
        purpose_interval=100,
        log_dir="experiments/run_4_2_v5_test"
    )
    
    exp_config = ExperimentConfig(
        experiment_id="run_4_2_test",
        duration_steps=3000,  # 快速测试：3000步
        checkpoint_interval=500,
        log_interval=100,
        output_dir="experiments/run_4_2_v5_test"
    )
    
    agent = UnifiedMOSSAgent(agent_config)
    agent.weights = np.array([0.60, 0.10, 0.20, 0.10])  # Survival初始
    
    # 简化的实验运行
    print("\n🧪 Running quick test...")
    print(f"Initial Purpose: Survival")
    print(f"Initial Weights: {agent.weights}")
    
    for step in range(0, 3001, 500):
        # 模拟运行
        for _ in range(500):
            agent.step()
        
        if agent.purpose_generator:
            purpose = agent.purpose_generator.purpose_statement[:50] + "..."
            vector = agent.purpose_generator.purpose_vector[:4].round(2)
            print(f"Step {step}: {purpose}")
            print(f"  Weights: {agent.weights.round(3)}, Vector: {vector}")
    
    print("\n✅ Quick test complete!")
    print(f"Final weights: {agent.weights.round(3)}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS Run 4.2-v5')
    parser.add_argument('--quick', action='store_true', help='Quick test mode (5 min)')
    parser.add_argument('--full', action='store_true', help='Full 12-hour experiment')
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    elif args.full:
        print("=" * 70)
        print("🚀 Run 4.2-v5 Full Experiment (12 hours)")
        print("=" * 70)
        
        experiment = Run42Experiment()
        result = experiment.run()
        
        print("\n📊 Results:")
        print(f"  Total Steps: {result['total_steps']}")
        print(f"  Avg Reward: {result['summary']['avg_reward']:.3f}")
        print(f"  Success Rate: {result['summary']['success_rate']:.2%}")
        print(f"  Duration: {result['duration_seconds']/3600:.2f} hours")
        print("=" * 70)
    else:
        print("Usage:")
        print("  python experiments/run_4_2_v5.py --quick  # 5分钟快速测试")
        print("  python experiments/run_4_2_v5.py --full   # 12小时完整实验")
