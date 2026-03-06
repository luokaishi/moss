"""
MOSS框架测试
"""

import sys
sys.path.insert(0, '/workspace/projects')

from moss.agents.moss_agent import MOSSAgent
from moss.core.objectives import SystemState
import json


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 50)
    print("MOSS Framework Test")
    print("=" * 50)
    
    # 创建Agent
    agent = MOSSAgent(agent_id="test_001")
    print(f"\n[1] Agent created: {agent.agent_id}")
    
    # 运行决策循环
    print("\n[2] Running 5 decision steps...")
    for i in range(5):
        result = agent.step()
        decision = result['decision']
        print(f"\n  Step {i+1}:")
        print(f"    State: {decision['system_state']}")
        print(f"    Weights: {json.dumps(decision['weights'], indent=6)}")
        print(f"    Selected: {decision['selected_action']['action'] if decision['selected_action'] else 'None'}")
    
    # 生成报告
    print("\n[3] Generating report...")
    report = agent.get_report()
    print(f"\n  Agent ID: {report['agent_id']}")
    print(f"  Uptime: {report['uptime_hours']:.2f} hours")
    print(f"  Total decisions: {report['stats']['total_decisions']}")
    print(f"  Current state: {report['allocator_stats']['current_state']}")
    print(f"  Current weights: {json.dumps(report['current_weights'], indent=4)}")
    
    # 目标趋势
    print("\n[4] Objective trends:")
    for name, trend in report['objective_trends'].items():
        avg_str = f"{trend['average']:.3f}" if trend['average'] is not None else 'N/A'
        print(f"    {name}: latest={trend['latest']:.3f}, avg={avg_str}")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    test_basic_functionality()
