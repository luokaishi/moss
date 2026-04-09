#!/usr/bin/env python3
"""
AGI Agent 中等长度运行测试
运行300周期，观察涌现和演化
"""

import os
import sys
import time
from datetime import datetime

# 确保可以导入moss包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent


def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')
    
    print("=" * 60)
    print("  AGI Agent 中等长度运行测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标周期: 300")
    print(f"配置文件: {config_path}")
    print("=" * 60)
    print()
    
    # 创建Agent
    agent = AGIAgent(config_path)
    
    # 运行300周期
    agent.run(max_cycles=300, verbose=False)
    
    # 手动打印最终报告
    print("\n" + "=" * 60)
    print("  AGI Agent 中等长度测试 - 最终报告")
    print("=" * 60)
    
    drives = agent.drive_manager.get_drive_summary()
    behavior = agent.behavior_tracker.get_behavior_summary()
    env_stats = agent.env.get_stats()
    mem_stats = agent.memory.get_stats()
    
    print(f"总周期数: {agent.cycle}")
    elapsed = (time.time() - agent._start_time) / 60.0
    print(f"运行时间: {elapsed:.1f} 分钟")
    print(f"驱动力总数: {len(drives)}")
    print(f"涌现驱动力: {len(agent._emerged_drives)}")
    for name in agent._emerged_drives:
        print(f"  - {name}")
    
    print("\n最终驱动力权重:")
    for name, info in drives.items():
        marker = ' [EMERGED]' if info['is_emergent'] else ''
        print(f"  {name}: weight={info['weight']:.3f}, score={info['score']:.2f}, stability={info['stability']:.2f}{marker}")
    
    print(f"\n行为统计: {behavior['total']}次行动, 成功率={behavior['success_rate']:.1%}")
    print(f"变化检测: {behavior['changes_detected']}次")
    
    print(f"\n记忆统计: {mem_stats['total_records']}条记录, 平均重要性={mem_stats['avg_importance']:.2f}")
    
    print(f"\n环境统计:")
    print(f"  命令执行: {env_stats['total_actions']}次")
    print(f"  错误数: {env_stats['error_count']}次")
    print(f"  错误率: {env_stats['error_rate']:.1%}")
    
    print("=" * 60)
    print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()