"""
Trajectory Embedder - 轨迹嵌入器

关键改进：
- 将轨迹转换为固定维度的嵌入向量
- 用于识别可重复的行为模式（trajectory motifs）
"""

import numpy as np
from typing import List, Dict


class TrajectoryEmbedder:
    """
    轨迹嵌入器
    
    将变长轨迹转换为固定维度的嵌入，用于：
    1. 轨迹聚类
    2. 目标提取
    3. 行为模式识别
    """
    
    def __init__(self, state_dim: int, embedding_dim: int = 8):
        self.state_dim = state_dim
        self.embedding_dim = embedding_dim
    
    def embed(self, trajectory: Dict) -> np.ndarray:
        """
        将轨迹嵌入为固定维度向量
        
        Args:
            trajectory: {'states': [...], 'actions': [...], 'rewards': [...]}
            
        Returns:
            嵌入向量 (embedding_dim,)
        """
        states = np.array(trajectory.get('states', []))
        rewards = np.array(trajectory.get('rewards', []))
        
        if len(states) == 0:
            return np.zeros(self.embedding_dim)
        
        # 特征1: 状态均值
        state_mean = np.mean(states, axis=0)
        
        # 特征2: 状态方差
        state_std = np.std(states, axis=0) if len(states) > 1 else np.zeros(self.state_dim)
        
        # 特征3: 状态变化趋势（首尾差）
        if len(states) > 1:
            state_trend = states[-1] - states[0]
        else:
            state_trend = np.zeros(self.state_dim)
        
        # 特征4: 奖励统计
        reward_mean = np.mean(rewards) if len(rewards) > 0 else 0.0
        reward_std = np.std(rewards) if len(rewards) > 1 else 0.0
        reward_total = np.sum(rewards) if len(rewards) > 0 else 0.0
        
        # 拼接所有特征
        features = np.concatenate([
            state_mean[:2],  # 只取前2维，降维
            state_std[:2],
            state_trend[:2],
            [reward_mean, reward_std, reward_total, float(len(states))]
        ])
        
        # 确保维度匹配
        if len(features) < self.embedding_dim:
            features = np.pad(features, (0, self.embedding_dim - len(features)))
        elif len(features) > self.embedding_dim:
            features = features[:self.embedding_dim]
        
        return features
    
    def compute_similarity(self, traj1: Dict, traj2: Dict) -> float:
        """
        计算两个轨迹的相似度
        
        Returns:
            相似度 (0-1)
        """
        emb1 = self.embed(traj1)
        emb2 = self.embed(traj2)
        
        # 余弦相似度
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = np.dot(emb1, emb2) / (norm1 * norm2)
        
        # 转换为0-1范围
        return float((cosine_sim + 1) / 2)
    
    def cluster_trajectories(self, trajectories: List[Dict], 
                            n_clusters: int = 3) -> Dict[int, List[int]]:
        """
        简单聚类轨迹
        
        Returns:
            {cluster_id: [traj_indices]}
        """
        if len(trajectories) < n_clusters:
            return {0: list(range(len(trajectories)))}
        
        # 计算所有嵌入
        embeddings = [self.embed(t) for t in trajectories]
        
        # 简单K-means (简化版)
        # 随机选择初始中心
        np.random.seed(42)
        centers = [embeddings[i] for i in np.random.choice(len(embeddings), n_clusters, replace=False)]
        
        # 迭代分配
        for _ in range(10):
            clusters = {i: [] for i in range(n_clusters)}
            
            for i, emb in enumerate(embeddings):
                # 找到最近的中心
                distances = [np.linalg.norm(emb - c) for c in centers]
                closest = int(np.argmin(distances))
                clusters[closest].append(i)
            
            # 更新中心
            for k in range(n_clusters):
                if clusters[k]:
                    centers[k] = np.mean([embeddings[i] for i in clusters[k]], axis=0)
        
        return clusters
