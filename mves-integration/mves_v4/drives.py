"""
MVES v4 - 内生驱动系统
核心：不再定义目标函数，而是基础驱动力
"""

class Drives:
    """
    三大基础驱动（可演化）
    """
    
    @staticmethod
    def survival(agent):
        """
        生存驱动：保持能量为正
        返回：0-1 的紧迫度
        """
        energy = agent.state.get("energy", 100)
        # 能量越低，紧迫度越高
        urgency = max(0, 1 - energy / 100)
        return urgency
    
    @staticmethod
    def curiosity(agent):
        """
        好奇驱动：最大化状态新颖性
        返回：0-1 的探索欲望
        """
        # 基于访问过的状态数量
        visited_states = len(agent.memory.get("visited_positions", set()))
        # 访问越少，好奇心越强
        novelty = max(0, 1 - visited_states / 50)
        return novelty
    
    @staticmethod
    def control(agent):
        """
        控制驱动：增加环境影响力
        返回：0-1 的控制欲望
        """
        # 基于已创造的工具/结构数量
        tools_created = len(agent.tools)
        structures_built = agent.state.get("structures_built", 0)
        influence = tools_created + structures_built
        # 影响力越低，欲望越强
        desire = max(0, 1 - influence / 10)
        return desire
    
    @classmethod
    def calculate_scores(cls, agent, weights=None):
        """
        计算各驱动的加权得分
        """
        if weights is None:
            weights = agent.genome.get("drive_weights", {
                "survival": 0.5,
                "curiosity": 0.3,
                "control": 0.2
            })
        
        scores = {
            "survival": cls.survival(agent),
            "curiosity": cls.curiosity(agent),
            "control": cls.control(agent)
        }
        
        weighted = {
            k: scores[k] * weights.get(k, 0.33)
            for k in scores
        }
        
        return {
            "raw": scores,
            "weighted": weighted,
            "total": sum(weighted.values()),
            "dominant": max(scores, key=scores.get)
        }
