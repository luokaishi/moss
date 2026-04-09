#!/usr/bin/env python3
"""
MOSS v5.0 Example: Basic Agent
===============================

基础Agent使用示例

展示：
- 创建和配置Agent
- 运行多步决策
- 查看结果
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
import numpy as np


def main():
    print("=" * 70)
    print("🤖 MOSS v5.0 - Basic Agent Example")
    print("=" * 70)
    
    # 1. 创建配置
    config = MOSSConfig(
        agent_id="basic_example",
        enable_purpose=True,
        purpose_interval=50,
        log_dir="examples/output"
    )
    
    # 2. 创建Agent
    print("\n1️⃣  Creating Agent...")
    agent = UnifiedMOSSAgent(config)
    print(f"   ✅ Agent created: {agent.agent_id}")
    print(f"   📊 Enabled dimensions: {agent._get_enabled_dimensions()}")
    print(f"   🎯 Initial weights: {agent.weights}")
    
    # 3. 运行多步
    print("\n2️⃣  Running 100 steps...")
    results = []
    
    for step in range(100):
        result = agent.step()
        results.append(result)
        
        # 每20步显示一次状态
        if step % 20 == 0 and step > 0:
            recent_rewards = [r.reward for r in results[-20:]]
            avg_reward = np.mean(recent_rewards)
            success_rate = sum([r.success for r in results[-20:]]) / 20
            
            print(f"   Step {step:>3}: "
                  f"avg_reward={avg_reward:.3f}, "
                  f"success_rate={success_rate:.0%}, "
                  f"weights={agent.weights.round(2)}")
    
    # 4. 汇总统计
    print("\n3️⃣  Summary Statistics")
    print("-" * 70)
    
    total_reward = sum([r.reward for r in results])
    avg_reward = np.mean([r.reward for r in results])
    success_rate = sum([r.success for r in results]) / len(results)
    
    print(f"   Total Steps: {len(results)}")
    print(f"   Total Reward: {total_reward:.3f}")
    print(f"   Average Reward: {avg_reward:.3f}")
    print(f"   Success Rate: {success_rate:.1%}")
    print(f"   Final Weights: {agent.weights.round(3)}")
    
    # 5. 行动分布
    print("\n4️⃣  Action Distribution")
    print("-" * 70)
    
    from collections import Counter
    actions = [r.action_type for r in results]
    action_dist = Counter(actions)
    
    for action, count in action_dist.most_common(5):
        percentage = (count / len(actions)) * 100
        print(f"   {action:>20}: {count:>3} ({percentage:>5.1f}%)")
    
    print("\n" + "=" * 70)
    print("✅ Basic Agent Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
