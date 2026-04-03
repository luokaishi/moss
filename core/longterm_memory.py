#!/usr/bin/env python3
"""
MOSS v5.4 - Long-term Memory System
长期记忆系统

核心功能:
- 经验存储与压缩
- 情境化检索
- 记忆驱动决策
- 遗忘机制

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class Memory:
    """记忆单元"""
    id: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5  # 0-1
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None  # 向量表示
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'importance': self.importance,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'tags': self.tags,
            'embedding': self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        return cls(
            id=data['id'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            importance=data['importance'],
            access_count=data['access_count'],
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None,
            tags=data.get('tags', []),
            embedding=data.get('embedding')
        )


class MemoryStorage:
    """
    记忆存储器
    
    提供记忆的持久化存储
    """
    
    def __init__(self, storage_dir: str = "./memory_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.memories: Dict[str, Memory] = {}
        self.stats = {
            'total_memories': 0,
            'total_size_bytes': 0,
            'reads': 0,
            'writes': 0
        }
    
    def store(self, memory: Memory) -> bool:
        """存储记忆"""
        try:
            # 保存到内存
            self.memories[memory.id] = memory
            
            # 保存到磁盘
            filepath = self.storage_dir / f"{memory.id}.json"
            with open(filepath, 'w') as f:
                json.dump(memory.to_dict(), f, indent=2)
            
            self.stats['total_memories'] += 1
            self.stats['writes'] += 1
            self.stats['total_size_bytes'] += filepath.stat().st_size
            
            return True
        except Exception as e:
            return False
    
    def retrieve(self, memory_id: str) -> Optional[Memory]:
        """检索记忆"""
        try:
            # 先从内存查找
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                self.stats['reads'] += 1
                return memory
            
            # 从磁盘加载
            filepath = self.storage_dir / f"{memory_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                memory = Memory.from_dict(data)
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                
                self.memories[memory_id] = memory
                self.stats['reads'] += 1
                return memory
            
            return None
        except Exception:
            return None
    
    def search(self, tags: Optional[List[str]] = None,
               min_importance: float = 0.0,
               limit: int = 100) -> List[Memory]:
        """搜索记忆"""
        results = []
        
        for memory in self.memories.values():
            # 标签过滤
            if tags and not any(tag in memory.tags for tag in tags):
                continue
            
            # 重要性过滤
            if memory.importance < min_importance:
                continue
            
            results.append(memory)
        
        # 按重要性排序
        results.sort(key=lambda m: m.importance, reverse=True)
        return results[:limit]
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            if memory_id in self.memories:
                # 删除磁盘文件
                filepath = self.storage_dir / f"{memory_id}.json"
                if filepath.exists():
                    self.stats['total_size_bytes'] -= filepath.stat().st_size
                    filepath.unlink()
                
                # 从内存移除
                del self.memories[memory_id]
                self.stats['total_memories'] -= 1
                return True
            return False
        except Exception:
            return False
    
    def get_status(self) -> Dict:
        """获取存储状态"""
        return {
            'stats': self.stats,
            'memory_count': len(self.memories),
            'storage_path': str(self.storage_dir)
        }


class MemoryRetrieval:
    """
    记忆检索系统
    
    提供情境化检索和相似度匹配
    """
    
    def __init__(self, storage: MemoryStorage):
        self.storage = storage
        self.stats = {
            'queries': 0,
            'successful_retrievals': 0,
            'failed_retrievals': 0
        }
    
    def retrieve_by_context(self, context: Dict, 
                           top_k: int = 5) -> List[Memory]:
        """
        根据情境检索记忆
        
        Args:
            context: 当前情境（包含 tags、goal 等）
            top_k: 返回数量
            
        Returns:
            相关记忆列表
        """
        self.stats['queries'] += 1
        
        # 提取情境标签
        context_tags = context.get('tags', [])
        context_goal = context.get('goal', '')
        
        # 标签匹配
        tagged_memories = self.storage.search(tags=context_tags, limit=top_k * 2)
        
        if not tagged_memories and context_goal:
            # 如果没有标签匹配，尝试关键词匹配
            keyword_matches = self._keyword_search(context_goal, limit=top_k)
            self.stats['successful_retrievals'] += len(keyword_matches)
            return keyword_matches
        
        self.stats['successful_retrievals'] += len(tagged_memories)
        return tagged_memories[:top_k]
    
    def _keyword_search(self, keyword: str, limit: int = 10) -> List[Memory]:
        """关键词搜索"""
        matches = []
        keyword_lower = keyword.lower()
        
        for memory in self.storage.memories.values():
            # 在内容中搜索关键词
            content_str = json.dumps(memory.content).lower()
            if keyword_lower in content_str:
                matches.append(memory)
        
        matches.sort(key=lambda m: m.importance, reverse=True)
        return matches[:limit]
    
    def get_similar_memories(self, memory: Memory, 
                            top_k: int = 5) -> List[Memory]:
        """获取相似记忆"""
        if memory.embedding is None:
            # 如果没有向量表示，使用标签相似度
            return self.storage.search(tags=memory.tags, limit=top_k)
        
        # 计算余弦相似度
        similarities = []
        query_vec = np.array(memory.embedding)
        
        for other in self.storage.memories.values():
            if other.id == memory.id or other.embedding is None:
                continue
            
            other_vec = np.array(other.embedding)
            similarity = self._cosine_similarity(query_vec, other_vec)
            similarities.append((similarity, other))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in similarities[:top_k]]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def get_status(self) -> Dict:
        """获取检索状态"""
        return {
            'stats': self.stats,
            'success_rate': (
                self.stats['successful_retrievals'] /
                max(self.stats['queries'], 1)
            )
        }


class LongTermMemory:
    """
    长期记忆系统主类
    
    统一管理记忆存储、检索和遗忘
    """
    
    def __init__(self, storage_dir: str = "./longterm_memory"):
        self.storage = MemoryStorage(storage_dir)
        self.retrieval = MemoryRetrieval(self.storage)
        
        self.stats = {
            'memories_created': 0,
            'memories_forgotten': 0,
            'total_retrievals': 0
        }
    
    def add_memory(self, content: Dict, tags: Optional[List[str]] = None,
                   importance: float = 0.5) -> str:
        """添加记忆"""
        memory_id = hashlib.md5(
            f"{datetime.now().isoformat()}{json.dumps(content)}".encode()
        ).hexdigest()[:16]
        
        memory = Memory(
            id=memory_id,
            content=content,
            importance=importance,
            tags=tags or []
        )
        
        self.storage.store(memory)
        self.stats['memories_created'] += 1
        
        return memory_id
    
    def retrieve(self, context: Dict, top_k: int = 5) -> List[Dict]:
        """检索记忆"""
        self.stats['total_retrievals'] += 1
        memories = self.retrieval.retrieve_by_context(context, top_k)
        return [m.to_dict() for m in memories]
    
    def forget_old_memories(self, days: int = 30, 
                           min_importance: float = 0.3) -> int:
        """
        遗忘旧记忆
        
        Args:
            days: 保留天数
            min_importance: 最低重要性阈值
            
        Returns:
            删除的记忆数量
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted = 0
        
        for memory in list(self.storage.memories.values()):
            # 保留高重要性记忆
            if memory.importance >= min_importance:
                continue
            
            # 删除旧且未访问的记忆
            if memory.timestamp.timestamp() < cutoff:
                if not memory.last_accessed or memory.last_accessed.timestamp() < cutoff:
                    if self.storage.delete(memory.id):
                        deleted += 1
                        self.stats['memories_forgotten'] += 1
        
        return deleted
    
    def compress_memories(self, similarity_threshold: float = 0.9) -> int:
        """
        压缩相似记忆
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            合并的记忆组数
        """
        # TODO: 实现基于向量相似度的记忆压缩
        return 0
    
    def get_status(self) -> Dict:
        """获取记忆系统状态"""
        return {
            'stats': self.stats,
            'storage': self.storage.get_status(),
            'retrieval': self.retrieval.get_status()
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.4 - Long-term Memory System Test")
    print("=" * 60)
    
    # 创建记忆系统
    memory = LongTermMemory(storage_dir="./test_memory")
    
    # 添加记忆
    print("\n1. 添加记忆...")
    id1 = memory.add_memory(
        content={'lesson': 'Use caching for performance', 'context': 'optimization'},
        tags=['optimization', 'performance', 'coding'],
        importance=0.8
    )
    print(f"   记忆 1: {id1}")
    
    id2 = memory.add_memory(
        content={'lesson': 'Test early, test often', 'context': 'testing'},
        tags=['testing', 'coding', 'best-practice'],
        importance=0.7
    )
    print(f"   记忆 2: {id2}")
    
    id3 = memory.add_memory(
        content={'lesson': 'Document as you go', 'context': 'documentation'},
        tags=['documentation', 'best-practice'],
        importance=0.6
    )
    print(f"   记忆 3: {id3}")
    
    # 检索记忆
    print("\n2. 情境检索...")
    context = {'tags': ['coding'], 'goal': 'improve code quality'}
    results = memory.retrieve(context, top_k=2)
    print(f"   找到 {len(results)} 条相关记忆:")
    for r in results:
        print(f"     - {r['content'].get('lesson', 'N/A')} (重要性：{r['importance']:.2f})")
    
    # 获取状态
    print("\n3. 系统状态:")
    status = memory.get_status()
    print(f"   总记忆数：{status['storage']['memory_count']}")
    print(f"   创建数：{status['stats']['memories_created']}")
    print(f"   检索次数：{status['stats']['total_retrievals']}")
    print(f"   检索成功率：{status['retrieval']['success_rate']:.1%}")
    
    # 测试遗忘
    print("\n4. 测试遗忘机制...")
    deleted = memory.forget_old_memories(days=30, min_importance=0.7)
    print(f"   删除低重要性记忆：{deleted} 条")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
