"""
Goal System - 目标系统

目标 = 对未来轨迹的压缩表达（compression of trajectories）

核心思想：
- 从长期行为轨迹中提取稳定的行为模式
- 这些模式成为系统的"目标"
- 目标对行为产生持续约束
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque
from .trajectory_embedder import TrajectoryEmbedder


@dataclass
class Goal:
    """目标"""
    name: str
    description: str = ""
    weight: float = 0.5
    stability: float = 0.0  # 稳定性分数
    consistency: float = 0.0  # 跨时间一致性
    resistance: float = 0.0  # 抗干扰性
    self_maintenance: float = 0.0  # 自我维护性
    
    # 目标相关的特征模式
    feature_pattern: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # 历史
    activation_history: List[float] = field(default_factory=list)
    created_at: int = 0
    
    def update_activation(self, activation: float, cycle: int):
        """更新目标激活历史"""
        self.activation_history.append(activation)
        if len(self.activation_history) > 100:
            self.activation_history = self.activation_history[-100:]
        
        # 更新稳定性
        if len(self.activation_history) >= 20:
            recent = self.activation_history[-20:]
            self.stability = 1.0 - np.std(recent) / (np.mean(recent) + 0.01)
            self.stability = float(np.clip(self.stability, 0, 1))


class TrajectoryBuffer:
    """
    轨迹缓冲区 V2
    
    关键改进：
    - 轨迹长度从20延长到100~200
    - 引入轨迹嵌入器
    """
    
    def __init__(self, max_trajectories: int = 50, trajectory_length: int = 100):
        self.max_trajectories = max_trajectories
        self.trajectory_length = trajectory_length
        self.trajectories: deque = deque(maxlen=max_trajectories)
        
    def add(self, states: List[np.ndarray], actions: List[str], rewards: List[float]):
        """添加一条轨迹"""
        if len(states) >= self.trajectory_length:
            trajectory = {
                'states': states[-self.trajectory_length:],
                'actions': actions[-self.trajectory_length:],
                'rewards': rewards[-self.trajectory_length:],
                'summary': self._summarize_trajectory(states, actions, rewards)
            }
            self.trajectories.append(trajectory)
    
    def _summarize_trajectory(self, states, actions, rewards) -> dict:
        """总结轨迹特征"""
        return {
            'mean_state': np.mean(states, axis=0),
            'state_variance': np.var(states, axis=0),
            'action_distribution': self._action_distribution(actions),
            'mean_reward': np.mean(rewards),
            'reward_variance': np.var(rewards)
        }
    
    def _action_distribution(self, actions: List[str]) -> Dict[str, float]:
        """计算动作分布"""
        dist = {}
        for a in actions:
            dist[a] = dist.get(a, 0) + 1
        total = len(actions)
        return {k: v/total for k, v in dist.items()}
    
    def get_similar_trajectories(self, query_summary: dict, top_k: int = 5) -> List[dict]:
        """获取相似的轨迹"""
        if len(self.trajectories) < 5:
            return list(self.trajectories)
        
        similarities = []
        for traj in self.trajectories:
            sim = self._compute_similarity(query_summary, traj['summary'])
            similarities.append((sim, traj))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [traj for _, traj in similarities[:top_k]]
    
    def _compute_similarity(self, s1: dict, s2: dict) -> float:
        """计算两个轨迹总结的相似度"""
        # 状态均值相似度
        state_sim = 1.0 - np.mean(np.abs(s1['mean_state'] - s2['mean_state']))
        
        # 奖励相似度
        reward_sim = 1.0 - abs(s1['mean_reward'] - s2['mean_reward'])
        
        # 动作分布相似度
        action_sim = self._action_distribution_similarity(
            s1['action_distribution'], 
            s2['action_distribution']
        )
        
        return 0.4 * state_sim + 0.3 * reward_sim + 0.3 * action_sim
    
    def _action_distribution_similarity(self, d1: Dict, d2: Dict) -> float:
        """计算动作分布的相似度"""
        all_actions = set(d1.keys()) | set(d2.keys())
        if not all_actions:
            return 0.0
        
        diff = sum(abs(d1.get(a, 0) - d2.get(a, 0)) for a in all_actions)
        return 1.0 - diff / 2.0


class GoalExtractor:
    """
    目标提取器
    
    从轨迹中提取稳定的目标
    """
    
    def __init__(self, min_trajectories: int = 10):
        self.min_trajectories = min_trajectories
        
    def extract(self, trajectories: List[dict]) -> List[Goal]:
        """
        从轨迹中提取目标
        
        策略：
        1. 聚类相似的轨迹
        2. 每个聚类的中心定义一个目标
        3. 计算目标的稳定性指标
        """
        if len(trajectories) < self.min_trajectories:
            return []
        
        goals = []
        
        # 基于动作分布聚类
        action_clusters = self._cluster_by_actions(trajectories)
        
        for cluster_id, cluster_trajs in action_clusters.items():
            if len(cluster_trajs) < 3:  # 至少需要3条轨迹
                continue
            
            # 提取目标
            goal = self._extract_goal_from_cluster(cluster_trajs, cluster_id)
            if goal:
                goals.append(goal)
        
        return goals
    
    def _cluster_by_actions(self, trajectories: List[dict]) -> Dict[int, List[dict]]:
        """基于动作分布聚类轨迹"""
        # 简化：使用主导动作作为聚类标签
        clusters = {}
        for traj in trajectories:
            actions = traj['actions']
            if not actions:
                continue
            
            # 找出主导动作
            action_counts = {}
            for a in actions:
                action_counts[a] = action_counts.get(a, 0) + 1
            dominant_action = max(action_counts.items(), key=lambda x: x[1])[0]
            
            # 使用动作哈希作为聚类ID
            cluster_id = hash(dominant_action) % 1000
            
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(traj)
        
        return clusters
    
    def _extract_goal_from_cluster(self, cluster_trajs: List[dict], cluster_id: int) -> Optional[Goal]:
        """从轨迹聚类中提取目标"""
        # 计算聚类的平均特征
        mean_states = [t['summary']['mean_state'] for t in cluster_trajs]
        avg_state = np.mean(mean_states, axis=0)
        
        # 计算一致性（方差越小越一致）
        state_variance = np.mean([np.var(s) for s in mean_states])
        consistency = np.exp(-state_variance * 5)
        
        # 获取主导动作
        all_actions = []
        for t in cluster_trajs:
            all_actions.extend(t['actions'])
        
        action_counts = {}
        for a in all_actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        dominant_action = max(action_counts.items(), key=lambda x: x[1])[0]
        
        # 创建目标
        goal = Goal(
            name=f"goal_{cluster_id}_{dominant_action[:8]}",
            description=f"Maintain {dominant_action} behavior pattern",
            feature_pattern=avg_state,
            consistency=float(consistency)
        )
        
        return goal


class GoalEvaluator:
    """
    目标评估器
    
    评估目标的三个关键属性：
    1. 跨时间一致性
    2. 抗干扰性
    3. 自我维护性
    """
    
    def evaluate(self, goal: Goal, trajectories: List[dict]) -> float:
        """
        评估目标的质量
        
        Returns:
            综合评分 (0-1)
        """
        # 1. 跨时间一致性
        consistency = self._evaluate_consistency(goal, trajectories)
        
        # 2. 抗干扰性（环境变化后是否仍维持）
        resistance = self._evaluate_resistance(goal, trajectories)
        
        # 3. 自我维护性（系统是否主动维持该目标）
        self_maintenance = self._evaluate_self_maintenance(goal, trajectories)
        
        # 综合评分
        score = 0.4 * consistency + 0.3 * resistance + 0.3 * self_maintenance
        
        # 更新目标属性
        goal.consistency = consistency
        goal.resistance = resistance
        goal.self_maintenance = self_maintenance
        
        return score
    
    def _evaluate_consistency(self, goal: Goal, trajectories: List[dict]) -> float:
        """评估跨时间一致性"""
        if not trajectories:
            return 0.0
        
        # 检查目标相关的轨迹是否持续出现
        related_count = 0
        for traj in trajectories:
            # 计算轨迹与目标模式的相似度
            state_sim = 1.0 - np.mean(np.abs(
                traj['summary']['mean_state'] - goal.feature_pattern
            ))
            if state_sim > 0.7:
                related_count += 1
        
        return related_count / len(trajectories)
    
    def _evaluate_resistance(self, goal: Goal, trajectories: List[dict]) -> float:
        """评估抗干扰性"""
        if len(trajectories) < 10:
            return 0.5
        
        # 检查在环境变化（高方差）时目标是否仍维持
        early = trajectories[:len(trajectories)//2]
        late = trajectories[len(trajectories)//2:]
        
        early_related = sum(1 for t in early if self._is_related(t, goal))
        late_related = sum(1 for t in late if self._is_related(t, goal))
        
        early_ratio = early_related / len(early) if early else 0
        late_ratio = late_related / len(late) if late else 0
        
        # 如果后期仍保持，说明抗干扰
        return late_ratio if late_ratio > 0.3 else late_ratio * 0.5
    
    def _evaluate_self_maintenance(self, goal: Goal, trajectories: List[dict]) -> float:
        """评估自我维护性"""
        # 检查系统是否主动产生维持该目标的行为
        if not goal.activation_history:
            return 0.0
        
        # 激活历史是否有上升趋势
        if len(goal.activation_history) >= 20:
            early = np.mean(goal.activation_history[:10])
            late = np.mean(goal.activation_history[-10:])
            if late > early:
                return min(1.0, (late - early) * 5 + 0.5)
        
        return np.mean(goal.activation_history) if goal.activation_history else 0.0
    
    def _is_related(self, trajectory: dict, goal: Goal) -> bool:
        """判断轨迹是否与目标相关"""
        state_sim = 1.0 - np.mean(np.abs(
            trajectory['summary']['mean_state'] - goal.feature_pattern
        ))
        return state_sim > 0.6


class GoalSystem:
    """
    目标系统主控 V2
    
    关键改进：
    - 使用TrajectoryEmbedder进行轨迹聚类
    - 延长轨迹长度到100
    - 引入"回访奖励"机制
    """
    
    def __init__(self, state_dim: int):
        self.state_dim = state_dim
        
        self.buffer = TrajectoryBuffer(trajectory_length=100)  # 延长到100
        self.extractor = GoalExtractor()
        self.evaluator = GoalEvaluator()
        self.embedder = TrajectoryEmbedder(state_dim=state_dim)
        
        self.active_goals: List[Goal] = []
        self.max_goals = 5
        
        # 高频区域记录（用于回访奖励）
        self.state_frequency: Dict[Tuple[int, ...], int] = {}
        self.frequent_regions: List[np.ndarray] = []
        
        # 临时存储当前轨迹
        self.current_trajectory = {
            'states': [],
            'actions': [],
            'rewards': []
        }
        
    def step(self, state: np.ndarray, action: str, reward: float, cycle: int):
        """
        目标系统的主循环步骤 V2
        
        改进：
        - 延长轨迹到100
        - 记录高频区域
        - 引入回访奖励
        """
        # 记录状态频率（用于回访奖励）
        state_key = tuple((state[:4] * 10).astype(int))  # 离散化
        self.state_frequency[state_key] = self.state_frequency.get(state_key, 0) + 1
        
        # 更新高频区域
        if self.state_frequency[state_key] > 5:
            if len(self.frequent_regions) < 10:
                self.frequent_regions.append(state)
        
        # 积累当前轨迹
        self.current_trajectory['states'].append(state)
        self.current_trajectory['actions'].append(action)
        self.current_trajectory['rewards'].append(reward)
        
        # 每100步完成一条轨迹（延长）
        if len(self.current_trajectory['states']) >= 100:
            self.buffer.add(
                self.current_trajectory['states'],
                self.current_trajectory['actions'],
                self.current_trajectory['rewards']
            )
            
            # 重置当前轨迹
            self.current_trajectory = {
                'states': [],
                'actions': [],
                'rewards': []
            }
        
        # 每100周期提取一次目标
        if cycle % 100 == 0 and len(self.buffer.trajectories) >= 10:
            self._extract_and_update_goals(cycle)
        
        # 更新目标激活
        for goal in self.active_goals:
            activation = self._compute_goal_activation(goal, state)
            goal.update_activation(activation, cycle)
    
    def _extract_and_update_goals(self, cycle: int):
        """提取并更新目标 V2 - 使用轨迹嵌入"""
        # 使用嵌入器聚类轨迹
        trajectories_list = list(self.buffer.trajectories)
        if len(trajectories_list) < 10:
            return
        
        # 聚类
        clusters = self.embedder.cluster_trajectories(trajectories_list, n_clusters=3)
        
        # 从轨迹中提取候选目标
        candidates = self.extractor.extract(trajectories_list)
        
        # 评估并筛选
        scored = []
        for goal in candidates:
            score = self.evaluator.evaluate(goal, list(self.buffer.trajectories))
            scored.append((score, goal))
        
        # 排序并选择前N个
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # 保留高质量目标
        new_goals = []
        for score, goal in scored[:self.max_goals]:
            if score > 0.3:  # 质量阈值
                goal.created_at = cycle
                new_goals.append(goal)
        
        self.active_goals = new_goals
    
    def _compute_goal_activation(self, goal: Goal, state: np.ndarray) -> float:
        """计算目标在当前状态下的激活程度"""
        if len(goal.feature_pattern) != len(state):
            return 0.0
        
        # 计算状态与目标模式的相似度
        similarity = 1.0 - np.mean(np.abs(state - goal.feature_pattern))
        return float(np.clip(similarity, 0, 1))
    
    def get_goal_influence(self, state: np.ndarray) -> float:
        """
        获取目标对当前状态的影响
        
        用于驱动决策时的目标约束
        """
        if not self.active_goals:
            return 0.0
        
        total_influence = 0.0
        for goal in self.active_goals:
            activation = self._compute_goal_activation(goal, state)
            total_influence += activation * goal.weight
        
        return total_influence / len(self.active_goals)
    
    def get_active_goals_summary(self) -> List[dict]:
        """获取活跃目标摘要"""
        return [{
            'name': g.name,
            'description': g.description,
            'weight': g.weight,
            'stability': g.stability,
            'consistency': g.consistency,
            'resistance': g.resistance,
            'self_maintenance': g.self_maintenance
        } for g in self.active_goals]
    
    def get_revisit_bias(self, state: np.ndarray) -> float:
        """
        获取回访奖励
        
        如果状态接近历史高频区域，给予正奖励
        用于强化路径依赖，形成稳定轨迹
        """
        if not self.frequent_regions:
            return 0.0
        
        # 计算与高频区域的相似度
        max_similarity = 0.0
        for region in self.frequent_regions:
            similarity = 1.0 - np.mean(np.abs(state - region))
            max_similarity = max(max_similarity, similarity)
        
        # 如果足够接近，给予小正奖励
        if max_similarity > 0.8:
            return 0.1 * max_similarity
        return 0.0
    
    def get_stats(self) -> dict:
        """获取目标系统统计"""
        return {
            'num_active_goals': len(self.active_goals),
            'trajectory_buffer_size': len(self.buffer.trajectories),
            'frequent_regions': len(self.frequent_regions),
            'goals': self.get_active_goals_summary()
        }