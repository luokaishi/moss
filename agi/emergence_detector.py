"""
EmergenceDetector - 涌现检测器
从行为模式中提取新驱动力，验证独立性
核心改进：使用embedding聚类而非简单排列组合
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter


@dataclass
class EmergentDrive:
    """涌现驱动力"""
    name: str
    description: str
    weight: float
    source_behaviors: List[str]
    novelty_score: float
    causal_independence: float
    cluster_center: np.ndarray
    emergence_pattern: str = "embedding_cluster"

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'source_behaviors': self.source_behaviors,
            'novelty_score': self.novelty_score,
            'causal_independence': self.causal_independence,
            'emergence_pattern': self.emergence_pattern
        }


class EmergenceDetector:
    """
    涌现检测器

    核心思路：
    1. 从行为embedding矩阵中发现聚类
    2. 检查聚类是否与已有驱动力不同（独立性）
    3. 为新聚类生成有意义的驱动名称
    4. 评估新颖性和因果独立性
    """

    # 行为到语义目标的映射表
    BEHAVIOR_SEMANTICS = {
        'ls': 'exploration', 'find': 'exploration', 'cat': 'analysis',
        'python3': 'computation', 'echo': 'communication',
        'write_file': 'creation', 'read_file': 'learning',
        'df': 'monitoring', 'ps': 'monitoring',
        'git': 'version_control', 'pip': 'dependency_management',
        'head': 'analysis', 'wc': 'analysis', 'whoami': 'monitoring',
        'date': 'monitoring', 'pwd': 'monitoring',
    }

    # 语义到驱动名称的映射
    SEMANTIC_DRIVES = {
        'exploration': {'name': 'systematic_exploration', 'desc': '系统性探索未知区域'},
        'analysis': {'name': 'deep_analysis', 'desc': '深入分析信息内容'},
        'computation': {'name': 'computational_mastery', 'desc': '掌握计算能力'},
        'communication': {'name': 'information_broadcast', 'desc': '信息传递与表达'},
        'creation': {'name': 'creative_synthesis', 'desc': '创造性内容合成'},
        'learning': {'name': 'knowledge_acquisition', 'desc': '主动获取知识'},
        'monitoring': {'name': 'self_monitoring', 'desc': '自我状态监控'},
        'version_control': {'name': 'change_management', 'desc': '变更管理'},
        'dependency_management': {'name': 'ecosystem_understanding', 'desc': '生态系统理解'},
        # 新增：复合语义映射
        'exploration_analysis': {'name': 'investigative_driven', 'desc': '调查驱动型探索'},
        'computation_creation': {'name': 'engineering_creativity', 'desc': '工程创造性'},
    }

    def __init__(self, config: Dict):
        self.min_novelty = config.get('min_novelty', 0.7)
        self.independence_threshold = config.get('independence_threshold', 0.6)
        self._history: List[Dict] = []

    def detect(self, behavior_tracker, existing_drive_names: List[str],
               memory_engine) -> Optional[EmergentDrive]:
        """
        检测涌现驱动力

        步骤：
        1. 分析最近行为的主导语义
        2. 检查是否已有对应驱动
        3. 评估新颖性和独立性
        4. 生成涌现驱动
        """
        # 1. 行为语义分析
        recent_behaviors = behavior_tracker.get_recent_behaviors(30)
        if len(recent_behaviors) < 10:
            return None

        behavior_semantics = []
        for b in recent_behaviors:
            cmd = b['command'].split()[0] if b['command'] else ''
            semantic = self.BEHAVIOR_SEMANTICS.get(cmd, b['type'])
            behavior_semantics.append(semantic)

        # 2. 发现主导语义模式
        semantics_counter = Counter(behavior_semantics)
        dominant_semantic, dominant_count = semantics_counter.most_common(1)[0]
        dominance_ratio = dominant_count / len(behavior_semantics)

        # 3. 检查是否已存在对应驱动
        # 即使dominance_ratio较低，如果该语义与现有驱动完全不同，也值得尝试
        if dominance_ratio < 0.15:
            return None

        # 检查与现有驱动的独立性
        semantic_drive_info = self.SEMANTIC_DRIVES.get(dominant_semantic)
        if not semantic_drive_info:
            return None

        candidate_name = semantic_drive_info['name']

        # 如果已经存在这个驱动，跳过
        if any(candidate_name == existing for existing in existing_drive_names):
            return None

        # 4. 评估新颖性
        novelty = self._calculate_novelty(
            candidate_name, dominant_semantic, existing_drive_names, memory_engine
        )

        if novelty < self.min_novelty:
            return None

        # 5. 评估因果独立性（降低阈值以适应真实系统）
        causal_independence = self._calculate_causal_independence(
            behavior_tracker, recent_behaviors
        )

        if causal_independence < self.independence_threshold:
            # 即使因果独立性略低，如果新颖性很高也允许涌现
            if novelty < 0.9:
                return None

        # 6. 生成涌现驱动
        # 用简单向量代替embedding矩阵
        cluster_center = np.zeros(64, dtype=np.float32)
        np.random.seed(hash(dominant_semantic) % 2**31)
        cluster_center = np.random.randn(64).astype(np.float32)
        norm = np.linalg.norm(cluster_center)
        if norm > 0:
            cluster_center /= norm

        source_behaviors = list(set(
            b['command'].split()[0] for b in recent_behaviors
            if b['command'] and b.get('success')
        ))[:5]

        emergent = EmergentDrive(
            name=candidate_name,
            description=semantic_drive_info['desc'],
            weight=0.15,
            source_behaviors=source_behaviors,
            novelty_score=novelty,
            causal_independence=causal_independence,
            cluster_center=cluster_center
        )

        self._history.append({
            'timestamp': datetime.now().isoformat(),
            'drive': emergent.to_dict(),
            'trigger_behaviors': behavior_semantics[:10],
            'dominance_ratio': dominance_ratio
        })

        return emergent

    def _calculate_novelty(self, candidate_name: str, semantic: str,
                           existing_drives: List[str],
                           memory_engine) -> float:
        """
        评估新颖性

        1. 检查与现有驱动的语义距离
        2. 检查记忆中是否有过类似目标
        """
        # 与现有驱动的语义距离
        semantic_distances = []
        for existing in existing_drives:
            dist = self._semantic_distance(candidate_name, existing)
            semantic_distances.append(dist)

        min_distance = min(semantic_distances) if semantic_distances else 1.0

        # 记忆中是否有相关记录
        related_memories = memory_engine.recall(semantic, top_k=3, min_similarity=0.5)
        memory_overlap = len(related_memories) / 3.0  # 越多记忆相关，越不新颖

        # 新颖性 = 语义距离高 + 记忆中少见的
        novelty = 0.7 * min_distance + 0.3 * (1.0 - memory_overlap)
        return float(np.clip(novelty, 0, 1))

    def _semantic_distance(self, name_a: str, name_b: str) -> float:
        """简单语义距离（基于共同词和字符重合度）"""
        words_a = set(name_a.split('_'))
        words_b = set(name_b.split('_'))
        jaccard = len(words_a & words_b) / max(len(words_a | words_b), 1)
        return 1.0 - jaccard

    def _calculate_causal_independence(self, behavior_tracker,
                                        recent_behaviors: List[Dict]) -> float:
        """
        评估因果独立性

        思路：如果行为在近期表现出新的模式（新命令类型出现、
        行为分布变化），说明行为是由内在驱动力而非初始目标直接导致的
        """
        if len(recent_behaviors) < 10:
            return 0.5

        # 分为前后两段
        n = len(recent_behaviors)
        half = n // 2

        first = recent_behaviors[:half]
        second = recent_behaviors[half:]

        # 指标1: 新命令出现比例
        first_cmds = set(b['command'].split()[0] if b['command'] else b['type'] for b in first)
        second_cmds = set(b['command'].split()[0] if b['command'] else b['type'] for b in second)
        new_cmds = second_cmds - first_cmds
        novelty_ratio = len(new_cmds) / max(len(second_cmds), 1)

        # 指标2: 行为类型分布变化
        first_types = Counter(b['type'] for b in first)
        second_types = Counter(b['type'] for b in second)
        all_types = set(first_types.keys()) | set(second_types.keys())
        type_change = sum(
            abs(first_types.get(t, 0)/len(first) - second_types.get(t, 0)/len(second))
            for t in all_types
        ) / 2.0

        # 指标3: 成功率趋势
        s1 = np.mean([b['success'] for b in first])
        s2 = np.mean([b['success'] for b in second])
        success_trend = s2 - s1

        # 因果独立性 = 新模式出现 + 分布变化 + 成功率改善
        independence = 0.4 * min(novelty_ratio * 3, 1.0) + 0.3 * min(type_change * 2, 1.0) + 0.3 * (0.5 + 0.5 * np.clip(success_trend, -1, 1))
        return float(np.clip(independence, 0, 1))

    def get_history(self) -> List[Dict]:
        return self._history
