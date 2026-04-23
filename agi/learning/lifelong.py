"""
MOSS v8.0 - Lifelong Learning System
终身学习系统

核心功能:
- 记忆巩固
- 知识整合
- 遗忘管理
- 持续学习

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json


@dataclass
class KnowledgeUnit:
    """知识单元"""
    knowledge_id: str
    content: str
    knowledge_type: str       # 'fact', 'skill', 'pattern', 'concept'
    importance: float         # 重要性 (0-1)
    confidence: float         # 置信度 (0-1)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    forgetting_curve: float = 1.0  # 遗忘曲线值
    
    def to_dict(self) -> Dict:
        return {
            'knowledge_id': self.knowledge_id,
            'content': self.content,
            'knowledge_type': self.knowledge_type,
            'importance': self.importance,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'access_count': self.access_count,
            'forgetting_curve': self.forgetting_curve
        }
    
    def access(self):
        """访问知识"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        # 强化记忆
        self.forgetting_curve = min(self.forgetting_curve + 0.1, 1.0)


class LifelongLearner:
    """
    终身学习器
    
    实现持续学习不遗忘
    """
    
    def __init__(self, 
                 max_knowledge_units: int = 1000,
                 consolidation_threshold: int = 5,
                 forgetting_rate: float = 0.01):
        """
        Args:
            max_knowledge_units: 最大知识单元数
            consolidation_threshold: 巩固阈值 (访问次数)
            forgetting_rate: 遗忘率
        """
        self.max_knowledge_units = max_knowledge_units
        self.consolidation_threshold = consolidation_threshold
        self.forgetting_rate = forgetting_rate
        
        # 知识库
        self.knowledge: Dict[str, KnowledgeUnit] = {}
        self.short_term_memory: deque = deque(maxlen=100)
        self.long_term_memory: Dict[str, KnowledgeUnit] = {}
        
        # 知识关联
        self.knowledge_links: Dict[str, List[str]] = {}
        
        # 统计
        self.stats = {
            'knowledge_acquired': 0,
            'knowledge_consolidated': 0,
            'knowledge_forgotten': 0,
            'knowledge_accessed': 0
        }
    
    def learn(self, content: str, knowledge_type: str = 'fact',
             importance: float = 0.5, confidence: float = 0.7) -> KnowledgeUnit:
        """
        学习新知识
        
        Args:
            content: 知识内容
            knowledge_type: 知识类型
            importance: 重要性
            confidence: 置信度
            
        Returns:
            知识单元
        """
        # 生成知识 ID
        knowledge_id = f"KNOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.knowledge)}"
        
        unit = KnowledgeUnit(
            knowledge_id=knowledge_id,
            content=content,
            knowledge_type=knowledge_type,
            importance=importance,
            confidence=confidence
        )
        
        # 存入短期记忆
        self.short_term_memory.append(unit)
        self.knowledge[knowledge_id] = unit
        
        self.stats['knowledge_acquired'] += 1
        
        # 检查是否需要遗忘
        if len(self.knowledge) > self.max_knowledge_units:
            self._forget_least_important()
        
        return unit
    
    def consolidate_memory(self):
        """记忆巩固"""
        consolidated = []
        
        for unit in list(self.short_term_memory):
            if unit.access_count >= self.consolidation_threshold:
                # 巩固到长期记忆
                self.long_term_memory[unit.knowledge_id] = unit
                consolidated.append(unit.knowledge_id)
                self.stats['knowledge_consolidated'] += 1
        
        return consolidated
    
    def access_knowledge(self, knowledge_id: str) -> Optional[KnowledgeUnit]:
        """
        访问知识
        
        Args:
            knowledge_id: 知识 ID
            
        Returns:
            知识单元
        """
        if knowledge_id in self.knowledge:
            unit = self.knowledge[knowledge_id]
            unit.access()
            self.stats['knowledge_accessed'] += 1
            return unit
        return None
    
    def search_knowledge(self, query: str, threshold: float = 0.5) -> List[KnowledgeUnit]:
        """
        搜索知识
        
        Args:
            query: 查询
            threshold: 相似度阈值
            
        Returns:
            相关知识列表
        """
        results = []
        query_lower = query.lower()
        
        for unit in self.knowledge.values():
            # 简单字符串匹配
            if query_lower in unit.content.lower():
                results.append(unit)
            elif self._calculate_similarity(query_lower, unit.content.lower()) > threshold:
                results.append(unit)
        
        # 按重要性和遗忘曲线排序
        results.sort(key=lambda u: (u.importance * u.forgetting_curve), reverse=True)
        return results
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度 (简化)"""
        # 使用 Jaccard 相似度
        set1 = set(s1.split())
        set2 = set(s2.split())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def update_forgetting_curve(self):
        """更新遗忘曲线"""
        now = datetime.now()
        
        for unit in self.knowledge.values():
            # 计算时间差
            time_diff = (now - unit.last_accessed).total_seconds() / 3600  # 小时
            
            # 应用遗忘曲线 (简化 Ebbinghaus)
            decay = np.exp(-self.forgetting_rate * time_diff)
            unit.forgetting_curve *= decay
            
            # 确保不低于最小值
            unit.forgetting_curve = max(unit.forgetting_curve, 0.1)
    
    def _forget_least_important(self):
        """遗忘最不重要的知识"""
        if not self.knowledge:
            return
        
        # 找到重要性最低且遗忘曲线最低的知识
        least_important = min(
            self.knowledge.values(),
            key=lambda u: u.importance * u.forgetting_curve
        )
        
        del self.knowledge[least_important.knowledge_id]
        if least_important.knowledge_id in self.long_term_memory:
            del self.long_term_memory[least_important.knowledge_id]
        
        self.stats['knowledge_forgotten'] += 1
    
    def integrate_knowledge(self, knowledge_ids: List[str]) -> Dict:
        """
        知识整合
        
        Args:
            knowledge_ids: 知识 ID 列表
            
        Returns:
            整合后的知识
        """
        integrated = {
            'sources': knowledge_ids,
            'content': '',
            'confidence': 0.0
        }
        
        contents = []
        confidences = []
        
        for kid in knowledge_ids:
            if kid in self.knowledge:
                unit = self.knowledge[kid]
                contents.append(unit.content)
                confidences.append(unit.confidence)
                unit.access()  # 访问强化
        
        if contents:
            # 简单整合：连接内容
            integrated['content'] = ' | '.join(contents)
            integrated['confidence'] = np.mean(confidences)
        
        return integrated
    
    def get_knowledge_stats(self) -> Dict:
        """获取知识统计"""
        if not self.knowledge:
            return {
                'total_knowledge': 0,
                'short_term': 0,
                'long_term': 0,
                'avg_importance': 0.0,
                'avg_confidence': 0.0,
                'avg_forgetting_curve': 0.0
            }
        
        return {
            'total_knowledge': len(self.knowledge),
            'short_term': len(self.short_term_memory),
            'long_term': len(self.long_term_memory),
            'avg_importance': float(np.mean([u.importance for u in self.knowledge.values()])),
            'avg_confidence': float(np.mean([u.confidence for u in self.knowledge.values()])),
            'avg_forgetting_curve': float(np.mean([u.forgetting_curve for u in self.knowledge.values()]))
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            **self.get_knowledge_stats()
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v8.0 - Lifelong Learning System Test")
    print("=" * 60)
    
    # 创建终身学习器
    learner = LifelongLearner(max_knowledge_units=10)
    
    # 学习新知识
    print("\n1. Learning new knowledge...")
    knowledge_items = [
        ('Action A leads to high reward', 'fact', 0.8, 0.9),
        ('State S is dangerous', 'fact', 0.9, 0.8),
        ('Pattern P indicates success', 'pattern', 0.7, 0.6),
        ('Strategy X is optimal', 'skill', 0.85, 0.75),
        ('Environment E is dynamic', 'concept', 0.6, 0.7)
    ]
    
    learned = []
    for content, ktype, importance, confidence in knowledge_items:
        unit = learner.learn(content, ktype, importance, confidence)
        learned.append(unit)
        print(f"   Learned: {unit.knowledge_id} - {content[:30]}...")
    
    # 访问知识
    print("\n2. Accessing knowledge...")
    for i in range(3):
        unit = learned[i]
        for _ in range(5):  # 多次访问
            learner.access_knowledge(unit.knowledge_id)
        print(f"   Accessed {unit.knowledge_id} 5 times")
    
    # 巩固记忆
    print("\n3. Consolidating memory...")
    consolidated = learner.consolidate_memory()
    print(f"   Consolidated {len(consolidated)} items to long-term memory")
    
    # 搜索知识
    print("\n4. Searching knowledge...")
    results = learner.search_knowledge('reward')
    print(f"   Found {len(results)} results for 'reward':")
    for r in results:
        print(f"     - {r.content}")
    
    # 更新遗忘曲线
    print("\n5. Updating forgetting curve...")
    learner.update_forgetting_curve()
    stats = learner.get_knowledge_stats()
    print(f"   Average forgetting curve: {stats['avg_forgetting_curve']:.3f}")
    
    # 知识整合
    print("\n6. Integrating knowledge...")
    integrated = learner.integrate_knowledge([learned[0].knowledge_id, learned[2].knowledge_id])
    print(f"   Integrated content: {integrated['content'][:50]}...")
    print(f"   Confidence: {integrated['confidence']:.3f}")
    
    # 统计
    print("\n7. Learning stats:")
    stats = learner.get_stats()
    print(f"   Knowledge acquired: {stats['knowledge_acquired']}")
    print(f"   Knowledge consolidated: {stats['knowledge_consolidated']}")
    print(f"   Knowledge accessed: {stats['knowledge_accessed']}")
    print(f"   Total knowledge: {stats['total_knowledge']}")
    print(f"   Long-term memory: {stats['long_term']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)