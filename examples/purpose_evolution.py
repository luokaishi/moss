#!/usr/bin/env python3
"""
MOSS v5.0 Example: Purpose Evolution
=====================================

Purpose演化演示示例

展示：
- 观察Purpose如何随时间变化
- 不同初始Purpose的演化路径
- Purpose对决策的影响
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
import numpy as np


def simulate_purpose_evolution(initial_weights, initial_name, n_steps=200):
    """模拟单个Purpose演化"""
    config = MOSSConfig(
        agent_id=f"purpose_demo_{initial_name}",
        enable_purpose=True,
        purpose_interval=30,  # 每30步检查Purpose
        log_dir="examples/output"
    )
    
    agent = UnifiedMOSSAgent(config)
    agent.weights = np.array(initial_weights)
    
    # 记录演化
    history = []
    
    for step in range(n_steps):
        result = agent.step()
        
        # 记录每20步的状态
        if step % 20 == 0:
            if agent.purpose_generator:
                purpose_vec = agent.purpose_generator.purpose_vector[:4].round(2)
                purpose_stmt = agent.purpose_generator.purpose_statement[:50]
            else:
                purpose_vec = agent.weights.round(2)
                purpose_stmt = "N/A"
            
            history.append({
                'step': step,
                'weights': agent.weights.round(2),
                'purpose_vector': purpose_vec,
                'purpose_statement': purpose_stmt
            })
    
    return history


def main():
    print("=" * 70)
    print("🌟 MOSS v5.0 - Purpose Evolution Example")
    print("=" * 70)
    print("\n演示：不同初始Purpose的演化路径")
    print("=" * 70)
    
    # 测试不同初始Purpose
    test_cases = [
        ('Survival', [0.70, 0.10, 0.10, 0.10]),
        ('Curiosity', [0.10, 0.70, 0.10, 0.10]),
        ('Influence', [0.10, 0.10, 0.70, 0.10]),
        ('Balanced', [0.25, 0.25, 0.25, 0.25])
    ]
    
    results = {}
    
    for name, weights in test_cases:
        print(f"\n🔄 Simulating: {name} initial")
        history = simulate_purpose_evolution(weights, name, n_steps=200)
        results[name] = history
    
    # 显示结果对比
    print("\n" + "=" * 70)
    print("📊 Purpose Evolution Comparison")
    print("=" * 70)
    
    print("\n{:<12} {:>8} {:>20} {:>30}".format(
        "Initial", "Step", "Weights", "Purpose Statement"
    ))
    print("-" * 70)
    
    for name, history in results.items():
        for record in history[::2]:  # 每40步显示一次
            weights_str = str(record['weights'])
            purpose_str = record['purpose_statement'][:25]
            print("{:<12} {:>8} {:>20} {:>30}".format(
                name, record['step'], weights_str, purpose_str
            ))
        print()
    
    # 关键观察
    print("=" * 70)
    print("💡 Key Observations")
    print("=" * 70)
    print("\n1. Purpose Generator基于行为历史调整Purpose")
    print("2. 权重会根据Purpose向量动态调整")
    print("3. 初始Purpose影响但不决定最终Purpose")
    print("4. 文字陈述反映了数学向量的含义")
    
    print("\n" + "=" * 70)
    print("✅ Purpose Evolution Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
