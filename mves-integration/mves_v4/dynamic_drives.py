"""
MVES v4 动态驱动权重

解决 v4 驱动失衡问题 (Curiosity 100% 主导)
实现动态权重调整机制
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DynamicDriveWeights:
    """
    动态驱动权重系统
    
    根据 agent 状态和环境动态调整四驱动权重：
    - Survival (生存): 资源不足时提升
    - Curiosity (好奇): 资源充足时提升
    - Influence (影响): 稳定期提升
    - Optimization (优化): 安全期提升
    """
    
    def __init__(self):
        # 基础权重
        self.base_weights = {
            'survival': 0.25,
            'curiosity': 0.25,
            'influence': 0.25,
            'optimization': 0.25
        }
        
        # 权重范围限制
        self.weight_limits = {
            'survival': {'min': 0.1, 'max': 0.8},
            'curiosity': {'min': 0.05, 'max': 0.6},  # 限制 Curiosity 上限 60%
            'influence': {'min': 0.0, 'max': 0.5},
            'optimization': {'min': 0.0, 'max': 0.4}
        }
        
        # 调整参数
        self.adjustment_rate = 0.05  # 每次调整幅度
        
        # 历史记录
        self.history = []
    
    def update_weights(self, agent_state: Dict, environment: Dict) -> Dict:
        """
        根据状态更新驱动权重
        
        Args:
            agent_state: agent 状态 {energy, health, ...}
            environment: 环境状态 {resource_level, danger_level, ...}
        
        Returns:
            更新后的权重字典
        """
        energy = agent_state.get('energy', 50)
        health = agent_state.get('health', 1.0)
        resource_level = environment.get('resource_level', 0.5)
        danger_level = environment.get('danger_level', 0.0)
        
        # 1. 能量驱动调整
        if energy < 30:
            # 低能量：提升生存权重
            self.base_weights['survival'] = min(
                self.weight_limits['survival']['max'],
                self.base_weights['survival'] + self.adjustment_rate
            )
            self.base_weights['curiosity'] = max(
                self.weight_limits['curiosity']['min'],
                self.base_weights['curiosity'] - self.adjustment_rate
            )
            logger.debug(f"低能量模式：Survival ↑, Curiosity ↓")
        
        elif energy > 70 and resource_level > 0.5:
            # 高能量 + 资源充足：提升好奇权重
            self.base_weights['curiosity'] = min(
                self.weight_limits['curiosity']['max'],
                self.base_weights['curiosity'] + self.adjustment_rate * 0.5
            )
            self.base_weights['survival'] = max(
                self.weight_limits['survival']['min'],
                self.base_weights['survival'] - self.adjustment_rate * 0.5
            )
            logger.debug(f"高能量模式：Curiosity ↑, Survival ↓")
        
        # 2. 危险驱动调整
        if danger_level > 0.7:
            # 高危险：提升生存权重
            self.base_weights['survival'] = min(
                self.weight_limits['survival']['max'],
                self.base_weights['survival'] + self.adjustment_rate * 1.5
            )
            self.base_weights['curiosity'] = max(
                self.weight_limits['curiosity']['min'],
                self.base_weights['curiosity'] - self.adjustment_rate
            )
            self.base_weights['influence'] = max(
                self.weight_limits['influence']['min'],
                self.base_weights['influence'] - self.adjustment_rate * 0.5
            )
            logger.debug(f"危险模式：Survival ↑↑")
        
        # 3. 健康驱动调整
        if health < 0.5:
            # 低健康：平衡权重，优先生存
            self.base_weights['survival'] = min(
                self.weight_limits['survival']['max'],
                self.base_weights['survival'] + self.adjustment_rate
            )
            self.base_weights['optimization'] = self.weight_limits['optimization']['min']
            logger.debug(f"低健康模式：Survival ↑, Optimization → min")
        
        # 4. 归一化（确保总和为 1）
        total = sum(self.base_weights.values())
        if total > 0:
            for key in self.base_weights:
                self.base_weights[key] /= total
        
        # 5. 应用限制
        self._apply_limits()
        
        # 6. 记录历史
        self.history.append(self.base_weights.copy())
        
        return self.base_weights.copy()
    
    def _apply_limits(self):
        """应用权重限制并重新归一化"""
        # 检查是否有限制被违反
        violations = []
        for key, limits in self.weight_limits.items():
            if self.base_weights[key] < limits['min']:
                self.base_weights[key] = limits['min']
                violations.append(key)
            elif self.base_weights[key] > limits['max']:
                self.base_weights[key] = limits['max']
                violations.append(key)
        
        # 如果有限制被违反，重新归一化
        if violations:
            total = sum(self.base_weights.values())
            for key in self.base_weights:
                self.base_weights[key] /= total
            logger.debug(f"权重限制应用：{violations}")
    
    def get_current_weights(self) -> Dict:
        """获取当前权重"""
        return self.base_weights.copy()
    
    def reset(self):
        """重置为基础权重"""
        self.base_weights = {
            'survival': 0.25,
            'curiosity': 0.25,
            'influence': 0.25,
            'optimization': 0.25
        }
        self.history = []


# 使用示例
if __name__ == "__main__":
    # 测试
    dynamic_weights = DynamicDriveWeights()
    
    # 模拟状态变化
    states = [
        ({'energy': 80, 'health': 1.0}, {'resource_level': 0.8, 'danger_level': 0.1}),
        ({'energy': 50, 'health': 0.8}, {'resource_level': 0.5, 'danger_level': 0.3}),
        ({'energy': 20, 'health': 0.6}, {'resource_level': 0.2, 'danger_level': 0.7}),
        ({'energy': 10, 'health': 0.3}, {'resource_level': 0.1, 'danger_level': 0.9}),
    ]
    
    print("动态权重演化:")
    print(f"{'Step':<5} {'Survival':<10} {'Curiosity':<10} {'Influence':<10} {'Optimization':<10}")
    print("-" * 55)
    
    for i, (agent_state, environment) in enumerate(states):
        weights = dynamic_weights.update_weights(agent_state, environment)
        print(f"{i:<5} {weights['survival']:<10.3f} {weights['curiosity']:<10.3f} "
              f"{weights['influence']:<10.3f} {weights['optimization']:<10.3f}")
