"""
动态目标发现与集成 - Phase 5.3

将在线聚类发现的驱动力动态集成到Agent驱动空间
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import time

from edd_online_clustering import OnlineHDBSCAN, OptimizedRuntimeDiscoverer


@dataclass
class DynamicDrive:
    """动态驱动力"""
    name: str
    cluster_id: int
    centroid: np.ndarray
    stability: float
    persistence: float
    robustness: float = 0.0
    
    # 运行时状态
    is_active: bool = True
    weight: float = 0.5
    activation_count: int = 0
    last_activation: int = 0
    created_at: int = 0
    
    # 行为特征
    preferred_actions: List[str] = field(default_factory=list)
    action_weights: Dict[str, float] = field(default_factory=dict)
    
    def activate(self, cycle: int):
        """激活"""
        self.activation_count += 1
        self.last_activation = cycle
    
    def update_weight(self, delta: float):
        """更新权重"""
        self.weight = np.clip(self.weight + delta, 0.1, 1.0)
    
    def get_confidence(self) -> float:
        """获取置信度"""
        return (self.stability + self.persistence + self.robustness) / 3


class DynamicDriveSpace:
    """
    动态驱动空间
    
    支持运行时动态添加、更新、淘汰驱动力
    """
    
    def __init__(self, 
                 max_drives: int = 10,
                 min_confidence: float = 0.4,
                 decay_rate: float = 0.95):
        self.max_drives = max_drives
        self.min_confidence = min_confidence
        self.decay_rate = decay_rate
        
        # 驱动力集合
        self.drives: Dict[str, DynamicDrive] = {}
        self.cycle = 0
        
        # 初始驱动
        self.initial_drives = ['survival', 'curiosity']
        for drive in self.initial_drives:
            self._add_initial_drive(drive)
    
    def _add_initial_drive(self, name: str):
        """添加初始驱动"""
        self.drives[name] = DynamicDrive(
            name=name,
            cluster_id=-1,
            centroid=np.zeros(64),
            stability=1.0,
            persistence=1.0,
            robustness=1.0,
            weight=0.25,
            created_at=0
        )
    
    def add_emergent_drive(self, cluster_info: Dict) -> Optional[DynamicDrive]:
        """
        添加涌现驱动力
        
        Args:
            cluster_info: 聚类信息
        
        Returns:
            新添加的驱动力
        """
        drive_name = f"emergent_{cluster_info['id']}"
        
        # 检查是否已存在
        if drive_name in self.drives:
            return None
        
        # 检查空间是否已满
        if len(self.drives) >= self.max_drives:
            # 淘汰最低置信度的驱动力
            self._remove_weakest_drive()
        
        # 创建新驱动力
        drive = DynamicDrive(
            name=drive_name,
            cluster_id=cluster_info['id'],
            centroid=cluster_info.get('centroid', np.zeros(64)),
            stability=cluster_info['stability'],
            persistence=cluster_info['persistence'],
            robustness=cluster_info.get('robustness', 0.0),
            weight=0.5,
            created_at=self.cycle
        )
        
        self.drives[drive_name] = drive
        
        print(f"🌟 动态添加驱动力: {drive_name}")
        print(f"   Confidence: {drive.get_confidence():.2f}")
        print(f"   Weight: {drive.weight:.2f}")
        
        return drive
    
    def _remove_weakest_drive(self):
        """淘汰最弱的驱动力"""
        # 只淘汰涌现驱动，不淘汰初始驱动
        emergent_drives = [
            (name, drive) for name, drive in self.drives.items()
            if name not in self.initial_drives
        ]
        
        if not emergent_drives:
            return
        
        # 找到置信度最低的
        weakest = min(emergent_drives, key=lambda x: x[1].get_confidence())
        
        if weakest[1].get_confidence() < self.min_confidence:
            print(f"⚠️ 淘汰弱驱动力: {weakest[0]} (confidence={weakest[1].get_confidence():.2f})")
            del self.drives[weakest[0]]
    
    def update_drives(self, action: str, reward: float):
        """更新所有驱动力"""
        self.cycle += 1
        
        # 更新每个驱动力的权重
        for drive in self.drives.values():
            if drive.is_active:
                # 根据action匹配度更新
                if action in drive.preferred_actions:
                    drive.activate(self.cycle)
                    drive.update_weight(0.05)
                else:
                    # 衰减
                    drive.update_weight(-0.02)
    
    def select_action(self, available_actions: List[str]) -> str:
        """基于驱动力选择action"""
        if not self.drives:
            return np.random.choice(available_actions)
        
        # 计算每个action的加权得分
        action_scores = {}
        for action in available_actions:
            score = 0
            for drive in self.drives.values():
                if drive.is_active:
                    if action in drive.preferred_actions:
                        score += drive.weight * drive.get_confidence()
                    else:
                        score += drive.weight * 0.1
            action_scores[action] = score
        
        # 选择得分最高的
        if action_scores:
            return max(action_scores, key=action_scores.get)
        
        return np.random.choice(available_actions)
    
    def get_active_drives(self) -> List[DynamicDrive]:
        """获取活跃驱动力"""
        return [d for d in self.drives.values() if d.is_active]
    
    def get_summary(self) -> Dict:
        """获取摘要"""
        return {
            'cycle': self.cycle,
            'total_drives': len(self.drives),
            'active_drives': len(self.get_active_drives()),
            'initial_drives': len(self.initial_drives),
            'emergent_drives': len(self.drives) - len(self.initial_drives),
            'drives': [
                {
                    'name': d.name,
                    'weight': d.weight,
                    'confidence': d.get_confidence(),
                    'activations': d.activation_count,
                    'is_initial': d.name in self.initial_drives
                }
                for d in self.drives.values()
            ]
        }


class SelfDrivenAgent:
    """
    自驱动Agent
    
    集成EDD运行时发现的完整Agent
    """
    
    def __init__(self, 
                 embedding_dim: int = 64,
                 min_cluster_size: int = 5):
        
        # EDD运行时发现器
        self.discoverer = OptimizedRuntimeDiscoverer(
            embedding_dim=embedding_dim,
            min_cluster_size=min_cluster_size
        )
        
        # 动态驱动空间
        self.drive_space = DynamicDriveSpace(
            max_drives=8,
            min_confidence=0.4
        )
        
        # 状态
        self.cycle = 0
        self.action_history = []
        self.reward_history = []
    
    def step(self, observation: Dict) -> str:
        """
        Agent每cycle的决策
        
        Args:
            observation: 环境观察
        
        Returns:
            选择的action
        """
        self.cycle += 1
        
        # 1. 感知环境（简化版）
        available_actions = ['explore', 'gather', 'rest', 'communicate']
        
        # 2. 基于当前驱动力选择action
        action = self.drive_space.select_action(available_actions)
        
        # 3. 执行action（模拟）
        reward = self._simulate_reward(action)
        
        # 4. EDD运行时发现
        new_drive = self.discoverer.step(action, observation, reward)
        
        # 5. 如果有新发现的聚类，添加到驱动空间
        if new_drive:
            self.drive_space.add_emergent_drive(new_drive)
        
        # 6. 更新驱动空间
        self.drive_space.update_drives(action, reward)
        
        # 记录
        self.action_history.append(action)
        self.reward_history.append(reward)
        
        return action
    
    def _simulate_reward(self, action: str) -> float:
        """模拟奖励"""
        # 根据action返回基础奖励
        rewards = {
            'explore': 0.6,
            'gather': 0.75,
            'rest': 0.3,
            'communicate': 0.7
        }
        base = rewards.get(action, 0.5)
        return base + np.random.uniform(-0.1, 0.1)
    
    def get_summary(self) -> Dict:
        """获取Agent摘要"""
        return {
            'cycle': self.cycle,
            'edd_summary': self.discoverer.get_summary(),
            'drive_space_summary': self.drive_space.get_summary(),
            'recent_actions': self.action_history[-10:],
            'recent_rewards': self.reward_history[-10:]
        }


# 测试
if __name__ == "__main__":
    print("=" * 70)
    print("自驱动Agent测试 - Phase 5.3")
    print("=" * 70)
    
    # 创建自驱动Agent
    agent = SelfDrivenAgent(
        embedding_dim=64,
        min_cluster_size=5
    )
    
    print("\n🤖 Agent启动...")
    print(f"   初始驱动: {agent.drive_space.initial_drives}")
    
    # 模拟运行
    print("\n" + "=" * 70)
    print("模拟运行")
    print("=" * 70)
    
    # 阶段1: Exploration
    print("\n📍 阶段1: Exploration (0-99)")
    for i in range(100):
        action = agent.step({'phase': 'exploration'})
        if i % 25 == 0:
            print(f"   Cycle {i}: action={action}")
    
    # 阶段2: Gathering
    print("\n📍 阶段2: Gathering (100-199)")
    for i in range(100, 200):
        action = agent.step({'phase': 'gathering'})
        if i % 25 == 0:
            print(f"   Cycle {i}: action={action}")
    
    # 阶段3: Communication
    print("\n📍 阶段3: Communication (200-299)")
    for i in range(200, 300):
        action = agent.step({'phase': 'communication'})
        if i % 25 == 0:
            print(f"   Cycle {i}: action={action}")
    
    # 最终摘要
    print("\n" + "=" * 70)
    print("最终摘要")
    print("=" * 70)
    
    summary = agent.get_summary()
    
    print(f"\n总周期: {summary['cycle']}")
    print(f"发现聚类: {summary['edd_summary']['n_discovered']}")
    print(f"驱动力总数: {summary['drive_space_summary']['total_drives']}")
    print(f"  - 初始驱动: {summary['drive_space_summary']['initial_drives']}")
    print(f"  - 涌现驱动: {summary['drive_space_summary']['emergent_drives']}")
    
    print(f"\n驱动力详情:")
    for drive in summary['drive_space_summary']['drives']:
        print(f"   {drive['name']}:")
        print(f"      Weight: {drive['weight']:.2f}")
        print(f"      Confidence: {drive['confidence']:.2f}")
        print(f"      Activations: {drive['activations']}")
        print(f"      Is Initial: {drive['is_initial']}")
    
    print(f"\n最近行为: {summary['recent_actions']}")
    print(f"最近奖励: {[f'{r:.2f}' for r in summary['recent_rewards']]}")
    
    print("\n" + "=" * 70)
    print("✅ 自驱动Agent运行完成")
    print("=" * 70)
