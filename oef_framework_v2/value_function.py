"""
显式价值函数 - Day 1-3

为驱动力添加统一的价值-成本-风险评分
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValueAssessment:
    """价值评估"""
    drive_name: str
    
    # 三维度评分 (0-1)
    value_score: float = 0.0  # 价值：能带来多少收益
    cost_score: float = 0.0   # 成本：需要多少资源
    risk_score: float = 0.0   # 风险：失败概率
    
    # 综合评分
    net_value: float = 0.0    # 净价值 = value - cost - risk
    priority: int = 0         # 优先级排序
    
    def calculate_net_value(self):
        """计算净价值"""
        self.net_value = self.value_score - self.cost_score - self.risk_score
        return self.net_value


class ExplicitValueFunction:
    """
    显式价值函数
    
    为每个驱动力计算统一的价值评分
    """
    
    def __init__(self):
        # 历史数据用于学习
        self.success_history: Dict[str, List[float]] = {}
        self.failure_history: Dict[str, List[float]] = {}
        self.cost_history: Dict[str, List[float]] = {}
    
    def assess_drive(self, drive_name: str, 
                     success_rate: float,
                     avg_reward: float,
                     resource_cost: float,
                     failure_rate: float) -> ValueAssessment:
        """
        评估驱动力价值
        
        Args:
            drive_name: 驱动力名称
            success_rate: 成功率 (0-1)
            avg_reward: 平均奖励
            resource_cost: 资源消耗 (0-1)
            failure_rate: 失败率 (0-1)
        
        Returns:
            ValueAssessment
        """
        # 价值评分：成功率和奖励的函数
        value_score = success_rate * min(avg_reward * 2, 1.0)
        
        # 成本评分：资源消耗
        cost_score = resource_cost
        
        # 风险评分：失败率
        risk_score = failure_rate
        
        assessment = ValueAssessment(
            drive_name=drive_name,
            value_score=value_score,
            cost_score=cost_score,
            risk_score=risk_score
        )
        
        assessment.calculate_net_value()
        
        return assessment
    
    def update_from_experience(self, drive_name: str, 
                               success: bool,
                               reward: float,
                               cost: float):
        """从经验更新历史"""
        if drive_name not in self.success_history:
            self.success_history[drive_name] = []
            self.failure_history[drive_name] = []
            self.cost_history[drive_name] = []
        
        if success:
            self.success_history[drive_name].append(1.0)
        else:
            self.failure_history[drive_name].append(1.0)
        
        self.cost_history[drive_name].append(cost)
    
    def get_drive_statistics(self, drive_name: str) -> Dict:
        """获取驱动力统计"""
        success_rate = np.mean(self.success_history.get(drive_name, [0.5]))
        failure_rate = np.mean(self.failure_history.get(drive_name, [0.5]))
        avg_cost = np.mean(self.cost_history.get(drive_name, [0.5]))
        
        return {
            'success_rate': success_rate,
            'failure_rate': failure_rate,
            'avg_cost': avg_cost,
            'n_trials': len(self.success_history.get(drive_name, []))
        }
    
    def rank_drives(self, drives: List[str]) -> List[ValueAssessment]:
        """对驱动力进行优先级排序"""
        assessments = []
        
        for drive_name in drives:
            stats = self.get_drive_statistics(drive_name)
            
            # 从历史计算当前评分
            assessment = self.assess_drive(
                drive_name=drive_name,
                success_rate=1 - stats['failure_rate'],
                avg_reward=0.5,  # 默认值
                resource_cost=stats['avg_cost'],
                failure_rate=stats['failure_rate']
            )
            
            assessments.append(assessment)
        
        # 按净价值排序
        assessments.sort(key=lambda x: x.net_value, reverse=True)
        
        # 分配优先级
        for i, assessment in enumerate(assessments):
            assessment.priority = i + 1
        
        return assessments


# 测试
if __name__ == "__main__":
    print("=" * 70)
    print("显式价值函数测试")
    print("=" * 70)
    
    vf = ExplicitValueFunction()
    
    # 模拟一些经验数据
    drives = ['survival', 'curiosity', 'emergent_0']
    
    print("\n📊 模拟经验数据...")
    
    # survival: 高成功率，中等成本
    for _ in range(10):
        vf.update_from_experience('survival', success=True, reward=0.7, cost=0.3)
    vf.update_from_experience('survival', success=False, reward=0.0, cost=0.3)
    
    # curiosity: 中等成功率，低成本
    for _ in range(5):
        vf.update_from_experience('curiosity', success=True, reward=0.6, cost=0.2)
    for _ in range(5):
        vf.update_from_experience('curiosity', success=False, reward=0.0, cost=0.2)
    
    # emergent_0: 新驱动，数据少
    vf.update_from_experience('emergent_0', success=True, reward=0.8, cost=0.4)
    vf.update_from_experience('emergent_0', success=True, reward=0.7, cost=0.3)
    
    print("\n📈 驱动力评估:")
    
    for drive in drives:
        stats = vf.get_drive_statistics(drive)
        print(f"\n   {drive}:")
        print(f"      成功率: {1-stats['failure_rate']:.2f}")
        print(f"      失败率: {stats['failure_rate']:.2f}")
        print(f"      平均成本: {stats['avg_cost']:.2f}")
        print(f"      尝试次数: {stats['n_trials']}")
    
    print("\n📊 价值排序:")
    
    ranked = vf.rank_drives(drives)
    
    for assessment in ranked:
        print(f"\n   [{assessment.priority}] {assessment.drive_name}")
        print(f"      价值: {assessment.value_score:.2f}")
        print(f"      成本: {assessment.cost_score:.2f}")
        print(f"      风险: {assessment.risk_score:.2f}")
        print(f"      净价值: {assessment.net_value:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ 显式价值函数测试完成")
    print("=" * 70)
