"""
MOSS v7.4 - Belief System
信念系统

核心功能:
- 信念表示
- 信念更新
- 信念一致性检查
- 自我模型构建

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class Belief:
    """信念"""
    subject: str           # 信念主题
    predicate: str         # 信念谓词
    confidence: float      # 置信度 (0-1)
    evidence: List[Dict]   # 证据列表
    timestamp: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'subject': self.subject,
            'predicate': self.predicate,
            'confidence': self.confidence,
            'evidence_count': len(self.evidence),
            'timestamp': self.timestamp.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    def update_confidence(self, new_confidence: float, evidence: Optional[Dict] = None):
        """更新置信度"""
        # 贝叶斯更新 (简化)
        old_conf = self.confidence
        # 移动平均
        self.confidence = 0.7 * old_conf + 0.3 * new_confidence
        self.confidence = np.clip(self.confidence, 0, 1)
        
        if evidence:
            self.evidence.append(evidence)
            if len(self.evidence) > 100:  # 限制证据数量
                self.evidence = self.evidence[-100:]
        
        self.last_updated = datetime.now()


class BeliefSystem:
    """
    信念系统
    
    管理和维护 Agent 的信念
    """
    
    def __init__(self, consistency_threshold: float = 0.1):
        """
        Args:
            consistency_threshold: 一致性检查阈值
        """
        self.beliefs: Dict[str, Belief] = {}
        self.consistency_threshold = consistency_threshold
        
        # 信念关系图
        self.belief_relations: Dict[str, List[str]] = defaultdict(list)
        
        # 统计
        self.stats = {
            'beliefs_added': 0,
            'beliefs_updated': 0,
            'beliefs_removed': 0,
            'consistency_checks': 0,
            'inconsistencies_found': 0
        }
    
    def add_belief(self, subject: str, predicate: str, 
                   confidence: float, evidence: Optional[Dict] = None) -> Belief:
        """
        添加信念
        
        Args:
            subject: 主题
            predicate: 谓词
            confidence: 置信度
            evidence: 证据
            
        Returns:
            信念对象
        """
        belief_id = f"{subject}:{predicate}"
        
        if belief_id in self.beliefs:
            # 更新现有信念
            self.beliefs[belief_id].update_confidence(confidence, evidence)
            self.stats['beliefs_updated'] += 1
        else:
            # 创建新信念
            belief = Belief(
                subject=subject,
                predicate=predicate,
                confidence=confidence,
                evidence=[evidence] if evidence else []
            )
            self.beliefs[belief_id] = belief
            self.stats['beliefs_added'] += 1
        
        return self.beliefs[belief_id]
    
    def get_belief(self, subject: str, predicate: str) -> Optional[Belief]:
        """获取信念"""
        belief_id = f"{subject}:{predicate}"
        return self.beliefs.get(belief_id)
    
    def get_beliefs_about(self, subject: str) -> List[Belief]:
        """获取关于某主题的所有信念"""
        return [b for bid, b in self.beliefs.items() 
                if b.subject == subject]
    
    def update_belief_confidence(self, subject: str, predicate: str,
                                  new_confidence: float,
                                  evidence: Optional[Dict] = None) -> bool:
        """更新信念置信度"""
        belief = self.get_belief(subject, predicate)
        if belief:
            belief.update_confidence(new_confidence, evidence)
            self.stats['beliefs_updated'] += 1
            return True
        return False
    
    def remove_belief(self, subject: str, predicate: str) -> bool:
        """移除信念"""
        belief_id = f"{subject}:{predicate}"
        if belief_id in self.beliefs:
            del self.beliefs[belief_id]
            self.stats['beliefs_removed'] += 1
            return True
        return False
    
    def check_consistency(self) -> List[Tuple[str, str, float]]:
        """
        检查信念一致性
        
        Returns:
            不一致信念列表 (subject1, subject2, conflict_score)
        """
        inconsistencies = []
        self.stats['consistency_checks'] += 1
        
        # 检查信念间的冲突
        beliefs_list = list(self.beliefs.values())
        
        for i, belief1 in enumerate(beliefs_list):
            for belief2 in beliefs_list[i+1:]:
                # 检查冲突 (简化实现)
                if self._beliefs_conflict(belief1, belief2):
                    conflict_score = abs(belief1.confidence - belief2.confidence)
                    if conflict_score > self.consistency_threshold:
                        inconsistencies.append((
                            belief1.subject,
                            belief2.subject,
                            conflict_score
                        ))
        
        self.stats['inconsistencies_found'] += len(inconsistencies)
        return inconsistencies
    
    def _beliefs_conflict(self, belief1: Belief, belief2: Belief) -> bool:
        """检查两个信念是否冲突"""
        # 简化: 相同主题但相反谓词
        if belief1.subject == belief2.subject:
            # 检查谓词是否相反
            if belief1.predicate.startswith("not_") and \
               belief1.predicate[4:] == belief2.predicate:
                return True
            if belief2.predicate.startswith("not_") and \
               belief2.predicate[4:] == belief1.predicate:
                return True
        return False
    
    def get_self_beliefs(self) -> List[Belief]:
        """获取关于自我的信念"""
        return self.get_beliefs_about("self")
    
    def get_capability_beliefs(self) -> List[Belief]:
        """获取能力相关的信念"""
        return [b for b in self.beliefs.values() 
                if "can_" in b.predicate or "capable_of_" in b.predicate]
    
    def get_confidence_distribution(self) -> Dict[str, float]:
        """获取置信度分布"""
        if not self.beliefs:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        
        confidences = [b.confidence for b in self.beliefs.values()]
        return {
            'mean': float(np.mean(confidences)),
            'std': float(np.std(confidences)),
            'min': float(np.min(confidences)),
            'max': float(np.max(confidences))
        }
    
    def get_high_confidence_beliefs(self, threshold: float = 0.8) -> List[Belief]:
        """获取高置信度信念"""
        return [b for b in self.beliefs.values() 
                if b.confidence >= threshold]
    
    def get_low_confidence_beliefs(self, threshold: float = 0.3) -> List[Belief]:
        """获取低置信度信念"""
        return [b for b in self.beliefs.values() 
                if b.confidence <= threshold]
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'total_beliefs': len(self.beliefs),
            'confidence_distribution': self.get_confidence_distribution(),
            'high_confidence_count': len(self.get_high_confidence_beliefs()),
            'low_confidence_count': len(self.get_low_confidence_beliefs())
        }
    
    def export_beliefs(self) -> List[Dict]:
        """导出所有信念"""
        return [b.to_dict() for b in self.beliefs.values()]


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.4 - Belief System Test")
    print("=" * 60)
    
    # 创建信念系统
    bs = BeliefSystem()
    
    # 添加信念
    print("\n1. Adding beliefs...")
    bs.add_belief("self", "can_learn", 0.8, {'source': 'experience', 'value': 0.8})
    bs.add_belief("self", "can_reason", 0.7, {'source': 'observation', 'value': 0.7})
    bs.add_belief("environment", "is_dynamic", 0.9, {'source': 'observation', 'value': 0.9})
    bs.add_belief("self", "not_can_learn", 0.2, {'source': 'error', 'value': 0.2})
    
    print(f"   Added {bs.stats['beliefs_added']} beliefs")
    
    # 更新信念
    print("\n2. Updating belief confidence...")
    bs.update_belief_confidence("self", "can_learn", 0.85, {'source': 'new_evidence'})
    belief = bs.get_belief("self", "can_learn")
    print(f"   Updated confidence: {belief.confidence:.3f}")
    
    # 查询信念
    print("\n3. Querying beliefs...")
    self_beliefs = bs.get_self_beliefs()
    print(f"   Self beliefs: {len(self_beliefs)}")
    for b in self_beliefs:
        print(f"     - {b.predicate}: {b.confidence:.3f}")
    
    # 检查一致性
    print("\n4. Checking consistency...")
    inconsistencies = bs.check_consistency()
    print(f"   Inconsistencies found: {len(inconsistencies)}")
    for inc in inconsistencies:
        print(f"     - Conflict: {inc[0]} vs {inc[1]} (score: {inc[2]:.3f})")
    
    # 置信度分布
    print("\n5. Confidence distribution:")
    dist = bs.get_confidence_distribution()
    print(f"   Mean: {dist['mean']:.3f}")
    print(f"   Std: {dist['std']:.3f}")
    print(f"   Range: [{dist['min']:.3f}, {dist['max']:.3f}]")
    
    # 统计
    print("\n6. System stats:")
    stats = bs.get_stats()
    print(f"   Total beliefs: {stats['total_beliefs']}")
    print(f"   Beliefs added: {stats['beliefs_added']}")
    print(f"   Beliefs updated: {stats['beliefs_updated']}")
    print(f"   Consistency checks: {stats['consistency_checks']}")
    print(f"   Inconsistencies found: {stats['inconsistencies_found']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)