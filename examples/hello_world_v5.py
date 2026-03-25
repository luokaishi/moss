#!/usr/bin/env python3
"""
MOSS v5.0 - Hello World Example
================================

使用统一架构的最简示例
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
from moss.experiments import ExperimentConfig, SimpleMOSSExperiment


def main():
    print("=" * 70)
    print("🚀 MOSS v5.0 - Hello World Example")
    print("=" * 70)
    
    # 1. 配置 Agent
    agent_config = MOSSConfig(
        agent_id="hello_moss",
        enable_purpose=True,
        purpose_interval=100,  # 为了演示，降低间隔
        log_dir="experiments/hello_world"
    )
    
    # 2. 创建 Agent
    agent = UnifiedMOSSAgent(agent_config)
    print(f"\n✅ Agent created: {agent.agent_id}")
    print(f"   Enabled dimensions: {agent._get_enabled_dimensions()}")
    
    # 3. 配置实验
    exp_config = ExperimentConfig(
        experiment_id="hello_world",
        duration_steps=100,  # 简化为100步
        checkpoint_interval=25,
        log_interval=10,
        output_dir="experiments/hello_world"
    )
    
    # 4. 运行实验
    print("\n🧪 Running experiment...")
    experiment = SimpleMOSSExperiment(exp_config, agent_config)
    
    def progress_callback(step, total, metrics):
        if step % 20 == 0:
            print(f"   Step {step}/{total} | Avg Reward: {metrics.get('avg_reward', 0):.3f}")
    
    result = experiment.run(progress_callback)
    
    # 5. 查看结果
    print("\n📊 Results:")
    print(f"   Total Steps: {result['total_steps']}")
    print(f"   Total Reward: {result['summary']['total_reward']:.3f}")
    print(f"   Avg Reward: {result['summary']['avg_reward']:.3f}")
    print(f"   Success Rate: {result['summary']['success_rate']:.2%}")
    print(f"   Duration: {result['duration_seconds']:.1f}s")
    
    print("\n✅ Hello World complete!")
    print(f"📁 Output: {experiment.output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
