#!/usr/bin/env python3
"""
MOSS v5.0 Example: Custom Experiment
=====================================

自定义实验示例

展示：
- 使用v5.0实验框架
- 自定义实验逻辑
- 数据收集和分析
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
from moss.experiments import ExperimentConfig, BaseExperiment
import numpy as np
from datetime import datetime
from typing import Dict


class MyCustomExperiment(BaseExperiment):
    """
    自定义实验：Purpose演化速度测试
    
    研究问题：不同purpose_interval对Purpose稳定性的影响
    """
    
    def __init__(self, purpose_interval: int = 100):
        self.purpose_interval = purpose_interval
        
        # Agent配置
        agent_config = MOSSConfig(
            agent_id=f"custom_exp_p{purpose_interval}",
            enable_purpose=True,
            purpose_interval=purpose_interval,
            log_dir="examples/output"
        )
        
        # 实验配置
        exp_config = ExperimentConfig(
            experiment_id=f"purpose_stability_p{purpose_interval}",
            duration_steps=500,
            checkpoint_interval=50,
            log_interval=50,
            output_dir="examples/output"
        )
        
        # 创建Agent
        self.agent = UnifiedMOSSAgent(agent_config)
        
        super().__init__(exp_config, self.agent)
        
        # 自定义指标
        self.purpose_changes = 0
        self.prev_purpose = None
        self.weight_variance = []
    
    def setup(self):
        """实验设置"""
        print(f"[CustomExperiment] Setup with purpose_interval={self.purpose_interval}")
        # 设置初始权重
        self.agent.weights = np.array([0.4, 0.3, 0.2, 0.1])
    
    def run_step(self, step: int):
        """单步执行"""
        # 创建观察
        observation = {
            'phase': 'test',
            'step': step
        }
        
        # 执行
        result = self.agent.step(observation)
        
        # 记录Purpose变化
        if self.agent.purpose_generator:
            current_purpose = self.agent.purpose_generator.purpose_statement
            if current_purpose != self.prev_purpose:
                self.purpose_changes += 1
                self.prev_purpose = current_purpose
        
        # 记录权重方差
        self.weight_variance.append(np.var(self.agent.weights))
        
        return result
    
    def teardown(self):
        """实验结束"""
        print(f"[CustomExperiment] Complete: {self.purpose_changes} purpose changes")
    
    def _generate_summary(self) -> Dict:
        """生成自定义摘要"""
        base_summary = super()._generate_summary()
        
        # 添加自定义指标
        base_summary['custom_metrics'] = {
            'purpose_interval': self.purpose_interval,
            'purpose_changes': self.purpose_changes,
            'avg_weight_variance': float(np.mean(self.weight_variance)),
            'final_weights': self.agent.weights.tolist(),
            'stability_score': 1.0 - (self.purpose_changes / self.config.duration_steps)
        }
        
        return base_summary


def compare_purpose_intervals():
    """比较不同的purpose_interval"""
    print("=" * 70)
    print("🔬 Custom Experiment: Purpose Interval Comparison")
    print("=" * 70)
    
    intervals = [50, 100, 200]
    results = []
    
    for interval in intervals:
        print(f"\n🧪 Testing purpose_interval={interval}")
        print("-" * 70)
        
        exp = MyCustomExperiment(purpose_interval=interval)
        result = exp.run()
        results.append(result)
        
        custom = result.get('custom_metrics', {})
        print(f"   Purpose Changes: {custom.get('purpose_changes', 0)}")
        print(f"   Stability Score: {custom.get('stability_score', 0):.3f}")
        print(f"   Avg Weight Variance: {custom.get('avg_weight_variance', 0):.3f}")
    
    # 比较结果
    print("\n" + "=" * 70)
    print("📊 Comparison Results")
    print("=" * 70)
    print("\n{:<12} {:>15} {:>15} {:>15}".format(
        "Interval", "Changes", "Stability", "Variance"
    ))
    print("-" * 70)
    
    for interval, result in zip(intervals, results):
        custom = result.get('custom_metrics', {})
        print("{:<12} {:>15} {:>15.3f} {:>15.3f}".format(
            interval,
            custom.get('purpose_changes', 0),
            custom.get('stability_score', 0),
            custom.get('avg_weight_variance', 0)
        ))
    
    print("\n💡 Finding:")
    print("   Longer intervals → More stable Purpose but slower adaptation")
    print("   Shorter intervals → Faster adaptation but more fluctuation")


def demo_callback_usage():
    """演示回调函数使用"""
    print("\n" + "=" * 70)
    print("🔔 Custom Experiment: Using Callbacks")
    print("=" * 70)
    
    exp = MyCustomExperiment(purpose_interval=100)
    
    # 自定义进度回调
    def my_callback(step, total, metrics):
        if step % 100 == 0:
            progress = (step / total) * 100
            print(f"   Progress: {progress:.0f}% (step {step}/{total})")
    
    print("\nRunning with custom callback...")
    result = exp.run(progress_callback=my_callback)
    
    print(f"\n✅ Experiment complete!")
    print(f"   Total reward: {result['summary']['total_reward']:.3f}")
    print(f"   Duration: {result['duration_seconds']:.1f}s")


def main():
    print("=" * 70)
    print("🧪 MOSS v5.0 - Custom Experiment Example")
    print("=" * 70)
    print("\n展示：如何使用v5.0实验框架创建自定义实验")
    
    # 演示1: 比较不同参数
    compare_purpose_intervals()
    
    # 演示2: 使用回调
    demo_callback_usage()
    
    print("\n" + "=" * 70)
    print("💡 Custom Experiment Features")
    print("=" * 70)
    print("\n1. Inherit from BaseExperiment")
    print("2. Implement setup(), run_step(), teardown()")
    print("3. Add custom metrics in _generate_summary()")
    print("4. Use callbacks for real-time monitoring")
    print("5. Automatic checkpoint and report generation")
    
    print("\n" + "=" * 70)
    print("✅ Custom Experiment Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
