"""
Ecology System - 生态系统 (第3层)

多智能体生态系统，支持驱动的传播与竞争

三种传播机制：
1. 接触传播 (Proximity Transmission)
2. 观察传播 (Imitation)
3. 繁殖传播 (Reproduction)

关键现象：
- Drive扩散（Memetic Spread）
- Drive灭绝（淘汰无效驱动）
- 策略分化（生态位形成）
- "文化"出现（行为模式被复制）
"""

from .world import World, Agent
__all__ = ['World', 'Agent']
