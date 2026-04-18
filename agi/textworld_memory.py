"""
TextWorld Memory - 记忆与学习系统

记录成功经验，避免重复失败，支持相似状态检索
"""

import numpy as np
import hashlib
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
import json


@dataclass
class Episode:
    """回合经验"""
    episode_id: int
    states: List[np.ndarray] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    total_reward: float = 0.0
    success: bool = False
    steps: int = 0
    final_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'episode_id': self.episode_id,
            'states': [s.tolist() for s in self.states],
            'actions': self.actions,
            'rewards': self.rewards,
            'total_reward': self.total_reward,
            'success': self.success,
            'steps': self.steps,
            'final_score': self.final_score,
            'timestamp': self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Episode':
        """从字典创建"""
        ep = cls(
            episode_id=data['episode_id'],
            total_reward=data['total_reward'],
            success=data['success'],
            steps=data['steps'],
            final_score=data['final_score'],
        )
        ep.states = [np.array(s) for s in data['states']]
        ep.actions = data['actions']
        ep.rewards = data['rewards']
        ep.timestamp = datetime.fromisoformat(data['timestamp'])
        return ep


@dataclass
class StateActionPair:
    """状态-动作对"""
    state_hash: str
    state_vector: np.ndarray
    action: str
    value: float = 0.0
    visit_count: int = 0
    success_count: int = 0
    
    @property
    def success_rate(self) -> float:
        return self.success_count / max(self.visit_count, 1)
    
    def update(self, reward: float, success: bool):
        """更新统计"""
        self.visit_count += 1
        if success:
            self.success_count += 1
        # 指数移动平均更新价值
        self.value = 0.95 * self.value + 0.05 * reward


class TextWorldMemory:
    """
    TextWorld 记忆系统
    
    功能：
    1. 存储成功/失败经验
    2. 基于状态相似度检索
    3. 状态-动作价值估计
    4. 经验回放
    """
    
    def __init__(self, capacity: int = 10000, state_dim: int = 12):
        self.capacity = capacity
        self.state_dim = state_dim
        
        # 经验存储
        self.successful_episodes: deque = deque(maxlen=capacity // 2)
        self.failed_episodes: deque = deque(maxlen=capacity // 2)
        
        # 状态-动作价值表
        self.state_action_values: Dict[str, StateActionPair] = {}
        
        # 状态索引 (用于快速相似度检索)
        self.state_index: List[Tuple[str, np.ndarray]] = []
        
        # 统计
        self.stats = {
            'total_episodes': 0,
            'successful_episodes': 0,
            'failed_episodes': 0,
            'state_action_pairs': 0,
        }
        
        # 当前回合
        self.current_episode: Optional[Episode] = None
    
    def _hash_state(self, state: np.ndarray) -> str:
        """计算状态哈希"""
        # 量化状态以减少噪声影响
        quantized = np.round(state * 10).astype(int)
        state_bytes = quantized.tobytes()
        return hashlib.md5(state_bytes).hexdigest()[:16]
    
    def start_episode(self, episode_id: int):
        """开始新回合"""
        self.current_episode = Episode(episode_id=episode_id)
    
    def record_step(self, state: np.ndarray, action: str, reward: float):
        """记录一步"""
        if self.current_episode is None:
            return
        
        self.current_episode.states.append(state.copy())
        self.current_episode.actions.append(action)
        self.current_episode.rewards.append(reward)
        self.current_episode.total_reward += reward
        self.current_episode.steps += 1
        
        # 更新状态-动作价值
        self._update_state_action_value(state, action, reward)
    
    def _update_state_action_value(self, state: np.ndarray, action: str, reward: float):
        """更新状态-动作价值"""
        state_hash = self._hash_state(state)
        key = f"{state_hash}:{action}"
        
        if key not in self.state_action_values:
            self.state_action_values[key] = StateActionPair(
                state_hash=state_hash,
                state_vector=state.copy(),
                action=action,
            )
            self.stats['state_action_pairs'] += 1
        
        # 暂不更新访问计数，在回合结束时统一更新
        pair = self.state_action_values[key]
        pair.value = 0.95 * pair.value + 0.05 * reward
    
    def end_episode(self, success: bool, final_score: float = 0.0):
        """结束回合"""
        if self.current_episode is None:
            return
        
        self.current_episode.success = success
        self.current_episode.final_score = final_score
        
        # 更新状态-动作对的成功计数
        for i, (state, action) in enumerate(zip(self.current_episode.states, self.current_episode.actions)):
            state_hash = self._hash_state(state)
            key = f"{state_hash}:{action}"
            if key in self.state_action_values:
                self.state_action_values[key].update(
                    self.current_episode.rewards[i],
                    success
                )
        
        # 存储回合
        if success:
            self.successful_episodes.append(self.current_episode)
            self.stats['successful_episodes'] += 1
        else:
            self.failed_episodes.append(self.current_episode)
            self.stats['failed_episodes'] += 1
        
        self.stats['total_episodes'] += 1
        
        # 更新状态索引
        for state in self.current_episode.states:
            state_hash = self._hash_state(state)
            self.state_index.append((state_hash, state.copy()))
        
        # 清空当前回合
        episode = self.current_episode
        self.current_episode = None
        
        return episode
    
    def remember_success(self, episode: Episode):
        """记住成功经验"""
        self.successful_episodes.append(episode)
        self.stats['successful_episodes'] += 1
    
    def remember_failure(self, episode: Episode):
        """记住失败经验"""
        self.failed_episodes.append(episode)
        self.stats['failed_episodes'] += 1
    
    def get_similar_success(self, state: np.ndarray, k: int = 3) -> List[Tuple[Episode, float]]:
        """
        获取相似的成功经验
        
        Args:
            state: 查询状态
            k: 返回数量
            
        Returns:
            [(episode, similarity), ...]
        """
        if not self.successful_episodes:
            return []
        
        similarities = []
        
        for episode in self.successful_episodes:
            # 计算与回合中所有状态的相似度，取最大
            max_sim = 0.0
            for ep_state in episode.states:
                sim = self._state_similarity(state, ep_state)
                max_sim = max(max_sim, sim)
            
            similarities.append((episode, max_sim))
        
        # 排序并返回 top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def _state_similarity(self, s1: np.ndarray, s2: np.ndarray) -> float:
        """计算状态相似度 (余弦相似度)"""
        norm1 = np.linalg.norm(s1)
        norm2 = np.linalg.norm(s2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(s1, s2) / (norm1 * norm2))
    
    def get_state_action_value(self, state: np.ndarray, action: str) -> float:
        """获取状态-动作价值"""
        state_hash = self._hash_state(state)
        key = f"{state_hash}:{action}"
        
        if key in self.state_action_values:
            return self.state_action_values[key].value
        
        # 查找相似状态的价值
        similar_value = self._get_similar_state_value(state, action)
        
        return similar_value
    
    def _get_similar_state_value(self, state: np.ndarray, action: str, threshold: float = 0.9) -> float:
        """从相似状态获取价值估计"""
        values = []
        
        for key, pair in self.state_action_values.items():
            if pair.action == action:
                sim = self._state_similarity(state, pair.state_vector)
                if sim >= threshold:
                    values.append(pair.value)
        
        return np.mean(values) if values else 0.0
    
    def get_best_action_from_memory(self, state: np.ndarray, available_actions: List[str]) -> Tuple[str, float]:
        """
        基于记忆选择最佳动作
        
        Returns:
            (best_action, confidence)
        """
        if not available_actions:
            return "look", 0.0
        
        action_values = []
        
        for action in available_actions:
            value = self.get_state_action_value(state, action)
            action_values.append((action, value))
        
        # 排序
        action_values.sort(key=lambda x: x[1], reverse=True)
        best_action, best_value = action_values[0]
        
        # 计算置信度 (基于访问次数)
        state_hash = self._hash_state(state)
        key = f"{state_hash}:{best_action}"
        if key in self.state_action_values:
            visits = self.state_action_values[key].visit_count
            confidence = min(visits / 10.0, 1.0)
        else:
            confidence = 0.0
        
        return best_action, confidence
    
    def sample_experiences(self, batch_size: int = 32, success_only: bool = False) -> List[Tuple[np.ndarray, str, float, np.ndarray, bool]]:
        """
        采样经验用于训练
        
        Returns:
            [(state, action, reward, next_state, done), ...]
        """
        experiences = []
        
        # 选择回合
        if success_only and self.successful_episodes:
            episodes = list(self.successful_episodes)
        else:
            episodes = list(self.successful_episodes) + list(self.failed_episodes)
        
        if not episodes:
            return experiences
        
        # 随机采样
        sampled_episodes = np.random.choice(len(episodes), min(batch_size, len(episodes)), replace=False)
        
        for idx in sampled_episodes:
            episode = episodes[idx]
            if len(episode.states) < 2:
                continue
            
            # 随机选择一步
            step = np.random.randint(0, len(episode.states) - 1)
            
            state = episode.states[step]
            action = episode.actions[step]
            reward = episode.rewards[step]
            next_state = episode.states[step + 1]
            done = (step == len(episode.states) - 2)
            
            experiences.append((state, action, reward, next_state, done))
        
        return experiences
    
    def get_success_patterns(self, min_occurrence: int = 2) -> Dict[str, Dict]:
        """提取成功模式"""
        patterns = {}
        
        for episode in self.successful_episodes:
            # 提取动作序列模式
            action_seq = tuple(episode.actions[:5])  # 前5个动作
            
            if action_seq not in patterns:
                patterns[action_seq] = {
                    'count': 0,
                    'avg_reward': 0.0,
                    'avg_steps': 0.0,
                }
            
            patterns[action_seq]['count'] += 1
            patterns[action_seq]['avg_reward'] += episode.total_reward
            patterns[action_seq]['avg_steps'] += episode.steps
        
        # 计算平均值并过滤
        filtered_patterns = {}
        for seq, data in patterns.items():
            if data['count'] >= min_occurrence:
                data['avg_reward'] /= data['count']
                data['avg_steps'] /= data['count']
                filtered_patterns[seq] = data
        
        return filtered_patterns
    
    def update_value(self, state: np.ndarray, action: str, value: float):
        """更新状态-动作值"""
        state_hash = self._hash_state(state)
        key = f"{state_hash}:{action}"
        
        if key not in self.state_action_values:
            self.state_action_values[key] = StateActionPair(
                state_hash=state_hash,
                state_vector=state.copy(),
                action=action,
            )
        
        self.state_action_values[key].value = value
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'successful_episodes_in_memory': len(self.successful_episodes),
            'failed_episodes_in_memory': len(self.failed_episodes),
            'state_action_pairs': len(self.state_action_values),
            'success_rate': self.stats['successful_episodes'] / max(self.stats['total_episodes'], 1),
            'avg_episode_reward': self._compute_avg_reward(),
        }
    
    def _compute_avg_reward(self) -> float:
        """计算平均回合奖励"""
        all_episodes = list(self.successful_episodes) + list(self.failed_episodes)
        if not all_episodes:
            return 0.0
        return np.mean([ep.total_reward for ep in all_episodes])
    
    def save(self, path: str):
        """保存记忆到文件"""
        data = {
            'stats': self.stats,
            'successful_episodes': [ep.to_dict() for ep in self.successful_episodes],
            'failed_episodes': [ep.to_dict() for ep in self.failed_episodes],
            'state_action_values': {
                k: {
                    'state_hash': v.state_hash,
                    'action': v.action,
                    'value': v.value,
                    'visit_count': v.visit_count,
                    'success_count': v.success_count,
                }
                for k, v in self.state_action_values.items()
            },
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: str):
        """从文件加载记忆"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        self.stats = data['stats']
        
        self.successful_episodes = deque(
            [Episode.from_dict(ep) for ep in data['successful_episodes']],
            maxlen=self.capacity // 2
        )
        
        self.failed_episodes = deque(
            [Episode.from_dict(ep) for ep in data['failed_episodes']],
            maxlen=self.capacity // 2
        )
        
        self.state_action_values = {}
        for k, v in data['state_action_values'].items():
            # 注意：state_vector 在保存时丢失，需要重新构建
            self.state_action_values[k] = StateActionPair(
                state_hash=v['state_hash'],
                state_vector=np.zeros(self.state_dim),
                action=v['action'],
                value=v['value'],
                visit_count=v['visit_count'],
                success_count=v['success_count'],
            )
    
    def reset(self):
        """重置记忆"""
        self.successful_episodes.clear()
        self.failed_episodes.clear()
        self.state_action_values.clear()
        self.state_index.clear()
        self.stats = {
            'total_episodes': 0,
            'successful_episodes': 0,
            'failed_episodes': 0,
            'state_action_pairs': 0,
        }
        self.current_episode = None
