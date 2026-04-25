"""
MemoryEngine - 向量记忆引擎
使用numpy实现embedding存储、相似度检索和重要性衰减
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class MemoryRecord:
    """记忆条目"""
    content: str
    embedding: np.ndarray
    memory_type: str = "experience"  # fact / experience / reflection
    importance: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self):
        self.access_count += 1


def simple_hash_embedding(text: str, dim: int = 128) -> np.ndarray:
    """
    简单hash embedding：不依赖外部模型
    将文本通过hash映射到固定维度向量
    """
    vec = np.zeros(dim, dtype=np.float32)
    # 多轮hash填充
    text_bytes = text.encode('utf-8')
    for i in range(dim):
        h = hashlib.md5(f"{text_bytes}_{i}".encode()).hexdigest()
        vec[i] = int(h[:8], 16) / 0xFFFFFFFF
    # 归一化
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """余弦相似度"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


class MemoryEngine:
    """
    向量记忆引擎

    功能：
    1. 存储带embedding的记忆条目
    2. 基于余弦相似度的语义检索
    3. 重要性衰减机制
    4. 初始记忆加载
    """

    def __init__(self, config: Dict):
        self.dimension: int = config.get('dimension', 128)
        self.engine_type: str = config.get('engine', 'numpy')
        self.decay_rate: float = config.get('decay_rate', 0.001)

        # 存储结构
        self.records: List[MemoryRecord] = []
        self._embedding_matrix: Optional[np.ndarray] = None
        self._dirty = True  # matrix需要重建

        # 加载初始记忆
        for mem_cfg in config.get('initial_memories', []):
            self._load_initial_memory(mem_cfg)

    def _load_initial_memory(self, cfg: Dict):
        """加载初始记忆"""
        content = cfg['content']
        embedding = simple_hash_embedding(content, self.dimension)
        record = MemoryRecord(
            content=content,
            embedding=embedding,
            memory_type=cfg.get('type', 'fact'),
            importance=cfg.get('importance', 0.5),
            tags=cfg.get('tags', [])
        )
        self.records.append(record)
        self._dirty = True

    def _rebuild_matrix(self):
        """重建embedding矩阵"""
        if self.records:
            self._embedding_matrix = np.array([r.embedding for r in self.records])
        else:
            self._embedding_matrix = np.empty((0, self.dimension))
        self._dirty = False

    def store(self, content: str, memory_type: str = "experience",
              importance: float = 0.5, tags: Optional[List[str]] = None,
              metadata: Optional[Dict] = None) -> int:
        """存储新记忆"""
        embedding = simple_hash_embedding(content, self.dimension)
        record = MemoryRecord(
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        self.records.append(record)
        self._dirty = True
        return len(self.records) - 1

    def recall(self, query: str, top_k: int = 5,
               min_similarity: float = 0.3) -> List[MemoryRecord]:
        """基于语义相似度检索记忆"""
        if not self.records:
            return []

        if self._dirty:
            self._rebuild_matrix()

        query_embedding = simple_hash_embedding(query, self.dimension)

        # 计算相似度
        similarities = self._embedding_matrix @ query_embedding

        # 衰减权重
        now = datetime.now()
        hours_aged = np.array([
            (now - r.timestamp).total_seconds() / 3600.0 for r in self.records
        ])
        decay_factors = np.exp(-self.decay_rate * hours_aged)
        access_boosts = np.array([1.0 + 0.1 * r.access_count for r in self.records])

        # 综合排序分数 = 相似度 * 衰减 * 重要性 * 访问加成
        importance = np.array([r.importance for r in self.records])
        final_scores = similarities * decay_factors * importance * access_boosts

        # 排序
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            sim = float(similarities[idx])
            if sim >= min_similarity:
                self.records[idx].touch()
                results.append(self.records[idx])

        return results

    def decay_all(self):
        """对所有记忆执行重要性衰减"""
        for record in self.records:
            hours = (datetime.now() - record.timestamp).total_seconds() / 3600.0
            record.importance *= np.exp(-self.decay_rate * hours)

    def get_stats(self) -> Dict:
        return {
            'total_records': len(self.records),
            'by_type': dict(
                (t, sum(1 for r in self.records if r.memory_type == t))
                for t in set(r.memory_type for r in self.records)
            ),
            'avg_importance': float(np.mean([r.importance for r in self.records])) if self.records else 0.0
        }
