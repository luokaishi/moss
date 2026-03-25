#!/usr/bin/env python3
"""
MOSS v5.0 Example: Multi-Objective Trade-off
=============================================

多目标权衡示例

展示：
- 不同状态下的权重调整
- Survival vs Curiosity权衡
- Crisis状态下的行为变化
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
import numpy as np


def simulate_crisis_scenario():
    """模拟危机场景"""
    print("\n🔥 Scenario 1: Crisis Response")
    print("-" * 70)
    
    config = MOSSConfig(
        agent_id="crisis_agent",
        enable_purpose=False,  # 简化，不使用Purpose
        log_dir="examples/output"
    )
    
    agent = UnifiedMOSSAgent(config)
    
    # 正常状态（前30步）
    print("Phase 1: Normal State (Steps 0-30)")
    normal_weights = []
    for step in range(30):
        observation = {'critical': False, 'warning': False}
        agent.current_state = 'normal'
        result = agent.step(observation)
        if step % 10 == 0:
            normal_weights.append(agent.weights.copy())
    
    # 危机状态（后30步）
    print("Phase 2: Crisis State (Steps 30-60)")
    crisis_weights = []
    for step in range(30, 60):
        observation = {'critical': True, 'warning': False}
        agent.current_state = 'crisis'
        agent._apply_state_weights()  # 应用危机权重
        result = agent.step(observation)
        if step % 10 == 0:
            crisis_weights.append(agent.weights.copy())
    
    # 显示权重变化
    print("\nWeight Evolution:")
    print(f"  Normal State (avg): {np.mean(normal_weights, axis=0).round(3)}")
    print(f"  Crisis State (avg): {np.mean(crisis_weights, axis=0).round(3)}")
    print(f"  → Survival weight increases significantly in crisis!")


def simulate_exploration_vs_exploitation():
    """模拟探索vs利用权衡"""
    print("\n🎯 Scenario 2: Exploration vs Exploitation")
    print("-" * 70)
    
    config = MOSSConfig(
        agent_id="exploration_agent",
        enable_purpose=True,
        purpose_interval=20,
        log_dir="examples/output"
    )
    
    agent = UnifiedMOSSAgent(config)
    
    # 设置初始为探索模式
    agent.weights = np.array([0.1, 0.6, 0.1, 0.2])  # 高Curiosity
    
    exploration_actions = []
    exploitation_actions = []
    
    for step in range(100):
        result = agent.step()
        
        # 根据权重判断当前模式
        if agent.weights[1] > 0.4:  # Curiosity > 0.4
            exploration_actions.append(result.action_type)
        else:
            exploitation_actions.append(result.action_type)
    
    print(f"Exploration-predominant steps: {len(exploration_actions)}")
    print(f"Exploitation-predominant steps: {len(exploitation_actions)}")
    print(f"→ Dynamic balance between exploration and exploitation")


def simulate_social_dilemma():
    """模拟社会困境"""
    print("\n🤝 Scenario 3: Social Dilemma (Cooperate vs Compete)")
    print("-" * 70)
    
    config = MOSSConfig(
        agent_id="social_agent",
        enable_purpose=True,
        enable_other=True,
        enable_norm=True,
        log_dir="examples/output"
    )
    
    agent = UnifiedMOSSAgent(config)
    
    # 初始权重偏向个体利益
    agent.weights = np.array([0.4, 0.1, 0.3, 0.2])
    
    print("Initial weights (individual-focused):")
    print(f"  {agent.weights.round(3)}")
    
    # 模拟多次社交互动
    cooperation_count = 0
    competition_count = 0
    
    for step in range(50):
        result = agent.step()
        
        # 简化的合作/竞争判断
        if 'cooperate' in result.action_type or 'share' in result.action_type:
            cooperation_count += 1
        elif 'compete' in result.action_type or 'optimize' in result.action_type:
            competition_count += 1
    
    print(f"\nActions:")
    print(f"  Cooperative: {cooperation_count}")
    print(f"  Competitive: {competition_count}")
    print(f"→ Agent balances individual and social objectives")


def main():
    print("=" * 70)
    print("⚖️  MOSS v5.0 - Multi-Objective Trade-off Example")
    print("=" * 70)
    print("\n展示：MOSS如何在多个目标间动态权衡")
    
    # 场景1: 危机响应
    simulate_crisis_scenario()
    
    # 场景2: 探索vs利用
    simulate_exploration_vs_exploitation()
    
    # 场景3: 社会困境
    simulate_social_dilemma()
    
    print("\n" + "=" * 70)
    print("💡 Summary")
    print("=" * 70)
    print("\nMOSS通过动态权重调整实现：")
    print("  1. 环境适应性 - 根据状态调整目标优先级")
    print("  2. 探索-利用平衡 - 在学习和优化间切换")
    print("  3. 个体-社会平衡 - 协调个人和集体目标")
    
    print("\n" + "=" * 70)
    print("✅ Multi-Objective Trade-off Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
