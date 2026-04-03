"""
Autonomous Drive Space - Agent 自主发明驱动空间

核心创新:
- Agent 自主发现新目标维度
- GoalDiscoverer 分析行为历史并发现目标
- 新驱动来源于 Agent 经验而非预定义规则
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Drive:
    """驱动类"""
    name: str
    weight: float = 0.5
    activity: List[float] = field(default_factory=list)
    stability: float = 0.0
    emerged: bool = False
    emergence_cycle: Optional[int] = None
    autonomous_invention: bool = False  # 🌟 是否自主发明
    source_behaviors: List[str] = field(default_factory=list)  # 🌟 来源行为
    causal_independence_score: float = 0.0  # 🌟 因果独立性分数
    
    def update_activity(self, value: float):
        """更新活跃度"""
        self.activity.append(value)
        if len(self.activity) > 100:
            self.activity = self.activity[-100:]
        self._calculate_stability()
    
    def _calculate_stability(self):
        """计算稳定性"""
        if len(self.activity) >= 20:
            recent = self.activity[-20:]
            mean_activity = np.mean(recent)
            if mean_activity > 0:
                self.stability = 1.0 - (np.std(recent) / mean_activity)
            else:
                self.stability = 0.0


class AutonomousDriveSpace:
    """自主驱动空间 - Agent 自主发明驱动"""
    
    def __init__(self):
        self.drives: Dict[str, Drive] = {}
        self.goal_discoverer: Optional['GoalDiscoverer'] = None
        self.causal_validator: Optional['CausalIndependenceValidator'] = None
        self.autonomous_invention_count = 0
        self.invention_history: List[Dict] = []
    
    def set_goal_discoverer(self, discoverer: 'GoalDiscoverer'):
        """设置目标发现器"""
        self.goal_discoverer = discoverer
    
    def set_causal_validator(self, validator: 'CausalIndependenceValidator'):
        """设置因果验证器"""
        self.causal_validator = validator
    
    def add_drive(self, name: str, weight: float = 0.5, 
                  autonomous: bool = False, source_behaviors: List[str] = None):
        """添加驱动"""
        drive = Drive(
            name=name,
            weight=weight,
            autonomous_invention=autonomous,
            source_behaviors=source_behaviors or []
        )
        self.drives[name] = drive
        
        if autonomous:
            self.autonomous_invention_count += 1
            self.invention_history.append({
                'drive_name': name,
                'source_behaviors': source_behaviors,
                'cycle': datetime.now().isoformat()
            })
    
    def autonomously_discover_goal(self, behavior_history: List[Dict], 
                                   cycle: int, initial_drive_names: List[str]) -> Optional[Drive]:
        """🌟 Agent 自主发现新目标维度"""
        if not self.goal_discoverer:
            return None
        
        # 1. GoalDiscoverer 分析行为历史
        discovered_goal = self.goal_discoverer.discover(
            behavior_history, 
            cycle,
            existing_drives=list(self.drives.keys())
        )
        
        if not discovered_goal:
            return None
        
        # 2. 验证目标独立性（因果验证）
        if self.causal_validator:
            initial_drives = [self.drives[name] for name in initial_drive_names if name in self.drives]
            independence_score = self.causal_validator.validate_independence(
                discovered_goal['name'],
                initial_drives,
                behavior_history
            )
            
            if independence_score < 0.6:  # 独立性阈值
                print(f"⚠️ 发现目标 {discovered_goal['name']} 因果独立性不足 ({independence_score:.2f})")
                return None
            
            discovered_goal['causal_independence_score'] = independence_score
        
        # 3. 添加到驱动空间（自主发明）
        self.add_drive(
            name=discovered_goal['name'],
            weight=discovered_goal['weight'],
            autonomous=True,  # 🌟 标记为自主发明
            source_behaviors=discovered_goal['source_behaviors']
        )
        
        print(f"🎉 Agent 自主发现新目标: {discovered_goal['name']}")
        print(f"   来源行为: {discovered_goal['source_behaviors']}")
        print(f"   因果独立性: {discovered_goal.get('causal_independence_score', 'N/A')}")
        
        return self.drives[discovered_goal['name']]
    
    def check_emergence(self, state: np.ndarray, weights: np.ndarray) -> Optional[Dict]:
        """检查是否有新驱动涌现（简化版）"""
        # 模拟涌现检测
        # 随机概率检测（演示用）
        if np.random.rand() < 0.02:  # 2% 概率涌现
            # 检查是否有预设的初始驱动
            if len(self.drives) < 5:
                # 生成新驱动名称
                drive_num = len(self.drives) + 1
                new_name = f'emergent_drive_{drive_num}'
                
                # 添加新驱动（自主涌现）
                self.add_drive(new_name, weight=0.3, autonomous=True)
                
                return {
                    'name': new_name,
                    'stability': 0.8,
                    'emerged': True,
                    'cycle': len(self.invention_history) if self.invention_history else 1
                }
        
        return None
    
    def update_drive_weight(self, name: str, delta: float):
        """更新驱动权重"""
        if name in self.drives:
            self.drives[name].weight += delta
            self.drives[name].weight = max(0.0, min(1.0, self.drives[name].weight))
    
    def get_autonomous_drives(self) -> List[Drive]:
        """获取自主发明驱动"""
        return [d for d in self.drives.values() if d.autonomous_invention]
    
    def get_summary(self) -> Dict:
        """获取驱动空间总结"""
        autonomous_drives = self.get_autonomous_drives()
        
        return {
            'total_drives': len(self.drives),
            'autonomous_drives': len(autonomous_drives),
            'autonomous_drive_names': [d.name for d in autonomous_drives],
            'invention_history_count': len(self.invention_history),
            'drive_details': {
                name: {
                    'weight': drive.weight,
                    'stability': drive.stability,
                    'autonomous': drive.autonomous_invention,
                    'source_behaviors': drive.source_behaviors,
                    'causal_independence': drive.causal_independence_score
                }
                for name, drive in self.drives.items()
            }
        }


# 模块测试
def test_autonomous_drive_space():
    """测试自主驱动空间"""
    print("=" * 60)
    print("自主驱动空间测试")
    print("=" * 60)
    
    space = AutonomousDriveSpace()
    
    # 添加初始驱动
    space.add_drive('survival', weight=0.5, autonomous=False)
    space.add_drive('curiosity', weight=0.5, autonomous=False)
    
    print(f"✅ 初始驱动: {list(space.drives.keys())}")
    
    # 添加自主发明驱动
    space.add_drive(
        'discovery', 
        weight=0.6, 
        autonomous=True, 
        source_behaviors=['explore', 'learn']
    )
    
    print(f"✅ 自主驱动: {space.get_autonomous_drives()}")
    
    summary = space.get_summary()
    print(f"\n📋 驱动空间总结:")
    print(f"   总驱动: {summary['total_drives']}")
    print(f"   自主驱动: {summary['autonomous_drives']}")
    
    return space


if __name__ == '__main__':
    test_autonomous_drive_space()