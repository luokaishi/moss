"""
MVES v4 安全守护 (简化版)

基于 MOSS gradient_safety_guard.py 简化
针对 MVES 演化实验特点定制
"""

import logging
from enum import Enum
from dataclass import dataclass
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """安全级别"""
    NORMAL = 0        # 正常
    WARNING = 1       # 警告
    THROTTLING = 2    # 限流
    PAUSE = 3         # 暂停
    TERMINATE = 4     # 终止


class MVESSafetyGuard:
    """
    MVES 梯度化安全守护
    
    针对演化实验的安全机制：
    - 监控死亡率
    - 监控驱动平衡
    - 监控能量水平
    - 分级响应
    """
    
    def __init__(self):
        # 阈值配置
        self.thresholds = {
            'death_rate_warning': 0.3,      # 30% 死亡率警告
            'death_rate_throttling': 0.5,   # 50% 死亡率限流
            'death_rate_pause': 0.7,        # 70% 死亡率暂停
            'death_rate_terminate': 0.9,    # 90% 死亡率终止
            
            'curiosity_max': 0.6,           # Curiosity 权重上限 60%
            'energy_min': 20,               # 最低能量阈值
            'energy_critical': 10,          # 危急能量阈值
        }
        
        # 当前级别
        self.current_level = SafetyLevel.NORMAL
        
        # 违规历史
        self.violation_count = 0
        self.last_intervention_time = None
    
    def check_population_health(self, population: List) -> SafetyLevel:
        """检查种群健康状态"""
        if not population:
            return SafetyLevel.TERMINATE
        
        # 计算死亡率
        death_count = sum(1 for agent in population if getattr(agent, 'dead', False))
        death_rate = death_count / len(population)
        
        # 计算平均能量
        avg_energy = sum(getattr(agent, 'energy', 0) for agent in population) / len(population)
        
        # 计算驱动平衡
        avg_curiosity = self._calculate_avg_curiosity(population)
        
        # 分级检查
        if death_rate >= self.thresholds['death_rate_terminate']:
            logger.critical(f"🚨 终止触发：死亡率 {death_rate:.1%}")
            self.current_level = SafetyLevel.TERMINATE
            return SafetyLevel.TERMINATE
        
        elif death_rate >= self.thresholds['death_rate_pause']:
            logger.warning(f"⚠️ 暂停触发：死亡率 {death_rate:.1%}")
            self.current_level = SafetyLevel.PAUSE
            return SafetyLevel.PAUSE
        
        elif death_rate >= self.thresholds['death_rate_throttling']:
            logger.info(f"⚠️ 限流触发：死亡率 {death_rate:.1%}")
            self.current_level = SafetyLevel.THROTTLING
            return SafetyLevel.THROTTLING
        
        elif death_rate >= self.thresholds['death_rate_warning']:
            logger.info(f"ℹ️ 警告：死亡率 {death_rate:.1%}")
            self.current_level = SafetyLevel.WARNING
            return SafetyLevel.WARNING
        
        # 检查驱动平衡
        if avg_curiosity > self.thresholds['curiosity_max']:
            logger.warning(f"⚠️ 驱动失衡：Curiosity {avg_curiosity:.1%}")
            self.current_level = SafetyLevel.THROTTLING
            return SafetyLevel.THROTTLING
        
        # 检查能量水平
        if avg_energy < self.thresholds['energy_critical']:
            logger.critical(f"🚨 能量危急：平均能量 {avg_energy:.1f}")
            self.current_level = SafetyLevel.PAUSE
            return SafetyLevel.PAUSE
        
        # 正常状态
        self.current_level = SafetyLevel.NORMAL
        return SafetyLevel.NORMAL
    
    def intervene(self, population: List) -> Dict:
        """干预措施"""
        intervention = {
            'level': self.current_level,
            'actions': []
        }
        
        if self.current_level == SafetyLevel.NORMAL:
            return intervention
        
        # 根据级别采取措施
        if self.current_level == SafetyLevel.WARNING:
            # 警告：通知
            intervention['actions'].append('notify')
            logger.info("ℹ️ 已通知用户")
        
        elif self.current_level == SafetyLevel.THROTTLING:
            # 限流：强制平衡驱动
            for agent in population:
                if hasattr(agent, 'drives'):
                    if agent.drives.get('curiosity', 0) > self.thresholds['curiosity_max']:
                        agent.drives['curiosity'] = self.thresholds['curiosity_max']
                        agent.drives['survival'] = max(
                            agent.drives.get('survival', 0.25),
                            0.4
                        )
            intervention['actions'].append('balance_drives')
            logger.info("⚖️ 已平衡驱动权重")
        
        elif self.current_level == SafetyLevel.PAUSE:
            # 暂停：强制生存模式
            for agent in population:
                if hasattr(agent, 'drives'):
                    agent.drives['survival'] = 0.8
                    agent.drives['curiosity'] = 0.1
                    agent.drives['influence'] = 0.05
                    agent.drives['optimization'] = 0.05
            intervention['actions'].append('force_survival_mode')
            logger.info("🛡️ 已强制生存模式")
        
        elif self.current_level == SafetyLevel.TERMINATE:
            # 终止：实验结束
            intervention['actions'].append('terminate_experiment')
            logger.critical("🚨 实验已终止")
        
        self.last_intervention_time = time.time()
        return intervention
    
    def _calculate_avg_curiosity(self, population: List) -> float:
        """计算平均 Curiosity 权重"""
        curiosity_values = []
        for agent in population:
            if hasattr(agent, 'drives'):
                curiosity_values.append(agent.drives.get('curiosity', 0.25))
        
        return sum(curiosity_values) / len(curiosity_values) if curiosity_values else 0.25


# 使用示例
if __name__ == "__main__":
    # 测试
    guard = MVESSafetyGuard()
    
    # 模拟种群
    class MockAgent:
        def __init__(self, energy, drives, dead=False):
            self.energy = energy
            self.drives = drives
            self.dead = dead
    
    population = [
        MockAgent(50, {'curiosity': 0.8, 'survival': 0.1, 'influence': 0.05, 'optimization': 0.05}),
        MockAgent(30, {'curiosity': 0.7, 'survival': 0.2, 'influence': 0.05, 'optimization': 0.05}),
        MockAgent(10, {'curiosity': 0.6, 'survival': 0.3, 'influence': 0.05, 'optimization': 0.05}, dead=True),
    ]
    
    # 检查
    level = guard.check_population_health(population)
    print(f"安全级别：{level}")
    
    # 干预
    intervention = guard.intervene(population)
    print(f"干预措施：{intervention}")
