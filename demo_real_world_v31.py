"""
MOSS v3.1 with RealWorld Bridge Integration
============================================

将RealWorldBridge集成到v3.1 agent主循环的示例

Usage:
    python demo_real_world_v31.py
"""

import sys
import time
sys.path.insert(0, 'v3')
sys.path.insert(0, 'core')

from core.real_world_bridge import RealWorldBridge

# 模拟一个带Purpose Generator的Agent
class MockV3Agent:
    """模拟v3.1 agent的结构"""
    
    def __init__(self):
        # 模拟purpose generator
        self.purpose_generator = MockPurposeGenerator()
        self.step_count = 0
        self.weights = [0.25, 0.25, 0.25, 0.25]
    
    def step(self):
        """模拟agent step"""
        self.step_count += 1
        
        # 每500步生成新的purpose
        if self.step_count % 500 == 0:
            self.purpose_generator.generate()
    
    def get_state(self):
        """获取当前状态"""
        return {
            'step': self.step_count,
            'weights': self.weights,
            'purpose': self.purpose_generator.current_purpose
        }


class MockPurposeGenerator:
    """模拟Purpose Generator"""
    
    def __init__(self):
        import numpy as np
        self.purpose_vector = np.array([0.25, 0.25, 0.25, 0.25, 0, 0, 0, 0, 0.5])
        self.current_statement = "Initial purpose"
        self.current_purpose = "Exploration"
        self.purpose_history = []
    
    def generate(self):
        """生成新purpose"""
        import numpy as np
        import random
        
        # 随机选择主导维度
        dims = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        self.current_purpose = random.choice(dims)
        
        # 更新purpose vector
        idx = dims.index(self.current_purpose)
        self.purpose_vector = np.array([0.2] * 8 + [0.5])
        self.purpose_vector[idx] = 0.35
        
        self.current_statement = f"I exist to {self.current_purpose.lower()}."
        
        print(f"\n🌟 [D9 Purpose] Generated at step: {self.current_purpose}")
        print(f"   Statement: {self.current_statement}")


def demo_with_real_world():
    """演示带RealWorldBridge的agent运行"""
    
    print("=" * 70)
    print("🚀 MOSS v3.1 + RealWorldBridge Demo")
    print("=" * 70)
    
    # 创建agent
    agent = MockV3Agent()
    
    # 创建RealWorldBridge
    bridge = RealWorldBridge(agent)
    
    print(f"\nAgent initialized")
    print(f"RealWorldBridge tools: {list(bridge.tools.keys())}")
    print(f"GitHub enabled: {bridge.tools['github']['enabled']}")
    
    # 模拟运行600步
    print("\n" + "=" * 70)
    print("Running 600 steps with real-world actions...")
    print("=" * 70)
    
    real_world_tasks = [
        "git status",
        "Check GitHub issues",
        "Review recent commits",
        "Update documentation",
        "Run tests",
        "git log --oneline -5"
    ]
    
    task_idx = 0
    
    for step in range(600):
        # Agent正常step
        agent.step()
        
        # 每100步执行一个真实世界任务
        if step > 0 and step % 100 == 0:
            task = real_world_tasks[task_idx % len(real_world_tasks)]
            print(f"\n--- Step {step}: Real-world task ---")
            print(f"Task: {task}")
            
            result = bridge.execute_real_action(task, step)
            
            if result.get('success'):
                output = result.get('result', {}).get('output', '')
                if output:
                    print(f"Output: {output[:150]}...")
                else:
                    print(f"Executed: {result.get('result', {}).get('executed', False)}")
            else:
                print(f"Failed: {result.get('error', 'Unknown error')}")
            
            task_idx += 1
        
        # 显示进度
        if step % 200 == 0:
            print(f"  Progress: {step}/600 steps")
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete")
    print("=" * 70)
    
    # 显示行为日志摘要
    print("\nRecent Real-World Actions:")
    actions = bridge.get_action_summary(n_recent=5)
    for action in actions:
        print(f"  Step {action['step']}: {action['action']['tool']} - {action['task'][:40]}...")
    
    print(f"\nFull log saved to: {bridge.action_log_path}")
    print("\nNext steps:")
    print("  - Run 72-hour experiment: python experiments/real_world_72h.py")
    print("  - Analyze Purpose impact on real actions")
    print("  - Integrate with actual v3.1 agent_9d.py")


if __name__ == "__main__":
    demo_with_real_world()
