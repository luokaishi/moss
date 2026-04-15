"""
Representation Learning - 表征学习模块

实现自编码器和对比学习，用于学习状态表征
替代手工设计的16维特征
"""

from .autoencoder import StateAutoEncoder

__all__ = ['StateAutoEncoder']
