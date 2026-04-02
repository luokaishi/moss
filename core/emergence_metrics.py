# v5/core/emergence_metrics.py
"""
涌现指标模块 - v5.3 新增
独立量化系统涌现行为，不依赖复合驱力机制
"""

import numpy as np
from typing import List, Dict, Any, Set
from collections import Counter


class EmergenceMetrics:
    """
    涌现指标量化模块
    
    核心指标:
    1. 行为多样性 (Behavioral Diversity)
    2. 世界结构复杂度 (World Structure Complexity)
    3. 群体协调性 (Group Coordination)
    4. 创新涌现 (Innovation Emergence)
    """
    
    def __init__(self):
        self.behavior_history: List[Dict] = []
        self.structure_snapshots: List[np.ndarray] = []
        self.innovation_log: List[Dict] = []
        
    def calc_behavioral_diversity(self, agents: List) -> float:
        """
        计算行为多样性
        
        基于 agent 行为分布的熵值
        
        Returns:
            float: 多样性得分 [0, 1]
        """
        if not agents:
            return 0.0
        
        # 收集所有 agent 的行为模式
        behavior_patterns = []
        for agent in agents:
            if hasattr(agent, 'get_behavior_pattern'):
                pattern = agent.get_behavior_pattern()
                behavior_patterns.append(pattern)
            else:
                # 简化：使用探索率作为行为代理
                if hasattr(agent, 'exploration_rate'):
                    behavior_patterns.append(agent.exploration_rate)
        
        if not behavior_patterns:
            return 0.5  # 默认中等多样性
        
        # 计算熵值
        behavior_array = np.array(behavior_patterns)
        if len(behavior_array.shape) == 1:
            # 一维行为：离散化后计算熵
            bins = np.histogram_bin_edges(behavior_array, bins='auto')
            hist, _ = np.histogram(behavior_array, bins=bins)
            hist = hist[hist > 0]  # 移除空 bin
            probs = hist / len(behavior_array)
            entropy = -np.sum(probs * np.log2(probs))
            max_entropy = np.log2(len(bins) - 1)
        else:
            # 多维行为：使用协方差行列式
            cov_matrix = np.cov(behavior_array.T)
            entropy = np.log2(np.abs(np.linalg.det(cov_matrix)) + 1e-10)
            max_entropy = 10.0  # 归一化因子
        
        return np.clip(entropy / max_entropy if max_entropy > 0 else 0.5, 0.0, 1.0)
    
    def calc_world_structure_complexity(self, world_state: Any) -> float:
        """
        计算世界结构复杂度
        
        基于:
        - 资源分布的不均匀性
        - agent 聚集程度
        - 连接网络密度
        
        Returns:
            float: 复杂度得分 [0, 1]
        """
        # 简化实现 (需要接入真实世界状态)
        if world_state is None:
            return 0.5
        
        complexity = 0.5
        
        # 如果有资源分布信息
        if hasattr(world_state, 'resource_distribution'):
            resources = world_state.resource_distribution
            if len(resources) > 1:
                # 计算资源分布的标准差 (越高越复杂)
                std = np.std(resources)
                complexity += 0.2 * np.clip(std, 0.0, 1.0)
        
        # 如果有网络连接信息
        if hasattr(world_state, 'network_density'):
            density = world_state.network_density
            # 中等密度最复杂 (太高太低都简单)
            optimal_density = 0.3
            distance = abs(density - optimal_density)
            complexity += 0.3 * (1.0 - distance)
        
        return np.clip(complexity, 0.0, 1.0)
    
    def calc_group_coordination(self, agents: List) -> float:
        """
        计算群体协调性
        
        基于:
        - 行为同步率
        - 目标一致性
        - 资源共享效率
        
        Returns:
            float: 协调性得分 [0, 1]
        """
        if len(agents) < 2:
            return 0.0
        
        # 计算目标一致性
        purposes = []
        for agent in agents:
            if hasattr(agent, 'purpose'):
                purposes.append(agent.purpose)
        
        if purposes:
            purpose_array = np.array(purposes)
            purpose_std = np.mean(np.std(purpose_array, axis=0))
            goal_alignment = 1.0 - np.clip(purpose_std, 0.0, 1.0)
        else:
            goal_alignment = 0.5
        
        # 计算行为同步率
        actions = []
        for agent in agents:
            if hasattr(agent, 'last_action'):
                actions.append(agent.last_action)
        
        if actions:
            action_counter = Counter(actions)
            most_common_ratio = action_counter.most_common(1)[0][1] / len(actions)
            sync_rate = most_common_ratio
        else:
            sync_rate = 0.5
        
        # 综合协调性
        coordination = 0.6 * goal_alignment + 0.4 * sync_rate
        return np.clip(coordination, 0.0, 1.0)
    
    def detect_innovation(self, agents: List, step: int) -> List[Dict]:
        """
        检测创新涌现
        
        创新定义:
        - 首次出现的行为模式
        - 突破性的策略组合
        - 新的协作形式
        
        Returns:
            List[Dict]: 检测到的创新事件列表
        """
        innovations = []
        
        for agent in agents:
            if hasattr(agent, 'get_novel_behavior'):
                novel = agent.get_novel_behavior()
                if novel:
                    innovation = {
                        'step': step,
                        'agent_id': agent.id,
                        'type': 'novel_behavior',
                        'description': novel
                    }
                    innovations.append(innovation)
                    self.innovation_log.append(innovation)
        
        return innovations
    
    def get_emergence_score(self, agents: List, world_state: Any = None) -> float:
        """
        综合涌现得分
        
        加权组合:
        - 行为多样性: 0.35
        - 结构复杂度：0.25
        - 群体协调性：0.25
        - 创新频率：0.15
        
        Returns:
            float: 综合涌现得分 [0, 1]
        """
        diversity = self.calc_behavioral_diversity(agents)
        complexity = self.calc_world_structure_complexity(world_state) if world_state else 0.5
        coordination = self.calc_group_coordination(agents)
        
        # 创新频率 (基于历史)
        innovation_rate = min(1.0, len(self.innovation_log) / 100) if self.innovation_log else 0.0
        
        emergence_score = (
            0.35 * diversity +
            0.25 * complexity +
            0.25 * coordination +
            0.15 * innovation_rate
        )
        
        return np.clip(emergence_score, 0.0, 1.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_innovations': len(self.innovation_log),
            'innovation_by_type': self._count_innovations_by_type(),
            'recent_behavior_diversity': self._calc_recent_diversity_trend()
        }
    
    def _count_innovations_by_type(self) -> Dict[str, int]:
        """统计各类型创新数量"""
        counts = {}
        for innovation in self.innovation_log:
            innovation_type = innovation.get('type', 'unknown')
            counts[innovation_type] = counts.get(innovation_type, 0) + 1
        return counts
    
    def _calc_recent_diversity_trend(self) -> float:
        """计算最近多样性趋势"""
        # 简化实现
        return 0.5
