"""
Autonomous Action Space - Agent 自主发明行为空间

核心创新:
- Agent 自主发明新行为
- ActionInventor 分析成功模式并发明
- 新行为来源于 Agent 经验而非预定义
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Action:
    """行为类"""
    name: str
    base_reward: float = 0.5
    execute_count: int = 0
    autonomous_invention: bool = False  # 🌟 是否自主发明
    source_patterns: List[str] = None  # 🌟 来源模式
    
    def execute(self, state: Dict) -> Tuple[float, Dict]:
        """执行行为"""
        self.execute_count += 1
        # 真实系统需要真实实现
        reward = self.base_reward * np.random.uniform(0.8, 1.2)
        new_state = state.copy()
        return reward, new_state


class AutonomousActionSpace:
    """自主行为空间 - Agent 自主发明行为"""
    
    def __init__(self):
        self.actions: Dict[str, Action] = {}
        self.action_inventor: Optional['ActionInventor'] = None
        self.autonomous_invention_count = 0
        self.invention_history: List[Dict] = []
    
    def set_action_inventor(self, inventor: 'ActionInventor'):
        """设置行为发明器"""
        self.action_inventor = inventor
    
    def add_action(self, name: str, base_reward: float = 0.5, 
                   autonomous: bool = False, source_patterns: List[str] = None):
        """添加行为"""
        action = Action(
            name=name,
            base_reward=base_reward,
            autonomous_invention=autonomous,
            source_patterns=source_patterns or []
        )
        self.actions[name] = action
        
        if autonomous:
            self.autonomous_invention_count += 1
            self.invention_history.append({
                'action_name': name,
                'source_patterns': source_patterns,
                'base_reward': base_reward
            })
    
    def autonomously_invent_action(self, action_history: List[Dict], 
                                   reward_history: List[float],
                                   cycle: int) -> Optional[Action]:
        """🌟 Agent 自主发明新行为"""
        if not self.action_inventor:
            return None
        
        # 1. ActionInventor 分析成功模式
        patterns = self.action_inventor.analyze_patterns(action_history, reward_history)
        
        if len(patterns) == 0:
            return None
        
        # 2. 发明新行为
        existing_actions = list(self.actions.keys())
        new_action_info = self.action_inventor.invent_new_action(
            patterns, existing_actions, cycle
        )
        
        if not new_action_info:
            return None
        
        # 3. 添加到行为空间（自主发明）
        self.add_action(
            name=new_action_info['name'],
            base_reward=new_action_info['base_reward'],
            autonomous=True,  # 🌟 标记为自主发明
            source_patterns=new_action_info['source_pattern']
        )
        
        print(f"🎉 Agent 自主发明新行为: {new_action_info['name']}")
        print(f"   来源模式: {new_action_info['source_pattern']}")
        print(f"   基础奖励: {new_action_info['base_reward']:.2f}")
        
        return self.actions[new_action_info['name']]
    
    def select_action(self, drives: Dict) -> Action:
        """基于驱动选择行为"""
        action_names = list(self.actions.keys())
        
        # 简化实现：真实系统需要更复杂决策
        if len(drives) == 0:
            return self.actions[action_names[0]]
        
        avg_drive_weight = np.mean([d.weight for d in drives.values()])
        base_rewards = [self.actions[name].base_reward for name in action_names]
        
        probs = np.array(base_rewards) * avg_drive_weight
        probs = probs / probs.sum() if probs.sum() > 0 else np.ones(len(action_names)) / len(action_names)
        
        selected_idx = np.random.choice(len(action_names), p=probs)
        return self.actions[action_names[selected_idx]]
    
    def get_autonomous_actions(self) -> List[Action]:
        """获取自主发明行为"""
        return [a for a in self.actions.values() if a.autonomous_invention]
    
    def get_summary(self) -> Dict:
        """获取行为空间总结"""
        autonomous_actions = self.get_autonomous_actions()
        
        action_stats = {name: action.execute_count for name, action in self.actions.items()}
        total_executions = sum(action_stats.values())
        action_distribution = {name: count/total_executions for name, count in action_stats.items()} if total_executions > 0 else {}
        
        return {
            'total_actions': len(self.actions),
            'autonomous_actions': len(autonomous_actions),
            'autonomous_action_names': [a.name for a in autonomous_actions],
            'invention_history_count': len(self.invention_history),
            'action_distribution': action_distribution,
            'action_details': {
                name: {
                    'base_reward': action.base_reward,
                    'execute_count': action.execute_count,
                    'autonomous': action.autonomous_invention,
                    'source_patterns': action.source_patterns
                }
                for name, action in self.actions.items()
            }
        }


# 模块测试
def test_autonomous_action_space():
    """测试自主行为空间"""
    print("=" * 60)
    print("自主行为空间测试")
    print("=" * 60)
    
    space = AutonomousActionSpace()
    
    # 添加初始行为
    space.add_action('explore', base_reward=0.4, autonomous=False)
    space.add_action('learn', base_reward=0.5, autonomous=False)
    space.add_action('rest', base_reward=0.8, autonomous=False)
    
    print(f"✅ 初始行为: {list(space.actions.keys())}")
    
    # 添加自主发明行为
    space.add_action(
        'explore_learn', 
        base_reward=0.7, 
        autonomous=True, 
        source_patterns=['explore', 'learn']
    )
    
    print(f"✅ 自主行为: {space.get_autonomous_actions()}")
    
    summary = space.get_summary()
    print(f"\n📋 行为空间总结:")
    print(f"   总行为: {summary['total_actions']}")
    print(f"   自主行为: {summary['autonomous_actions']}")
    
    return space


if __name__ == '__main__':
    test_autonomous_action_space()