"""
MOSS v3.0.0 - Multi-Objective Self-Driven System
=================================================

从4维到8维：自驱力系统的维度扩展

核心维度：
1. Survival (S)     - 生存
2. Curiosity (C)    - 探索  
3. Influence (I)    - 影响
4. Optimization (O) - 优化
5. Coherence (V)    - 自我连续性 [NEW in v3.0]
6. Valence (V)      - 主观偏好 [NEW in v3.0]
7. Other (Oth)      - 他者建模 [NEW in v3.0]
8. Norm (N)         - 规范内化 [NEW in v3.0]

版本关系：
- v2.0.0: 论文版本，4维系统，NeurIPS投稿
- v3.0.0: 扩展版本，8维系统，理论探索

作者: Cash
创建: 2026-03-19
"""

__version__ = "3.0.0-dev"
__author__ = "Cash"

# v3.0 - 8D Agent
# v3.1 - 9D Agent (with Purpose)
# Import specific agents from submodules as needed
# from .core.agent_8d import MOSSv3Agent8D
# from .core.agent_9d import MOSSv3Agent9D

__all__ = []
