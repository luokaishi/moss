"""
OEF 2.0 Goal Discoverer
目标维度发现器 - Agent自主发现新目标

核心创新：
- 分析Agent行为历史
- 发现新目标维度
- 验证目标新颖性
- 记录目标来源行为

科学目标：
证明新目标来源于Agent经验而非预定义规则
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import re


@dataclass
class DiscoveredGoal:
    """发现的目标"""
    name: str
    weight: float
    source_behaviors: List[str]
    novelty_score: float
    emergence_pattern: str
    confidence: float


class GoalDiscoverer:
    """
    目标发现器
    
    功能：
    1. 分析Agent行为历史
    2. 发现行为模式
    3. 提取目标维度
    4. 验证新颖性
    """
    
    def __init__(self, 
                 min_pattern_frequency: int = 10,
                 novelty_threshold: float = 0.7,
                 behavior_window: int = 100):
        
        self.min_pattern_frequency = min_pattern_frequency
        self.novelty_threshold = novelty_threshold
        self.behavior_window = behavior_window
        
        # 目标命名模板
        self.goal_templates = {
            'collaboration': ['help', 'share', 'coordinate', 'collaborate', 'teamwork'],
            'exploration': ['explore', 'discover', 'search', 'investigate', 'curiosity'],
            'optimization': ['optimize', 'improve', 'enhance', 'refine', 'efficiency'],
            'influence': ['influence', 'lead', 'guide', 'inspire', 'persuade'],
            'resilience': ['adapt', 'recover', 'persist', 'survive', 'resilience'],
            'creativity': ['create', 'innovate', 'design', 'invent', 'novel'],
            'learning': ['learn', 'study', 'acquire', 'understand', 'knowledge'],
            'autonomy': ['autonomous', 'self-driven', 'independent', 'freedom', 'choice']
        }
        
        self.discovered_goals_history: List[DiscoveredGoal] = []
    
    def discover(self, 
                behavior_history: List[Dict],
                cycle: int,
                existing_drives: List[str]) -> Optional[Dict]:
        """
        从行为历史中发现新目标
        
        Args:
            behavior_history: Agent行为历史
            cycle: 当前周期
            existing_drives: 已存在的驱动列表
        
        Returns:
            发现的新目标（如果存在）
        """
        
        if len(behavior_history) < self.min_pattern_frequency:
            return None
        
        # 1. 分析行为模式
        patterns = self._analyze_behavior_patterns(behavior_history)
        
        if not patterns:
            return None
        
        # 2. 提取候选目标
        candidate_goals = self._extract_candidate_goals(patterns, existing_drives)
        
        if not candidate_goals:
            return None
        
        # 3. 选择最佳候选
        best_goal = self._select_best_goal(candidate_goals)
        
        # 4. 验证新颖性
        novelty_score = self._calculate_novelty(best_goal['name'], existing_drives)
        
        if novelty_score < self.novelty_threshold:
            return None
        
        # 5. 创建发现目标
        discovered = DiscoveredGoal(
            name=best_goal['name'],
            weight=best_goal['weight'],
            source_behaviors=best_goal['source_behaviors'],
            novelty_score=novelty_score,
            emergence_pattern=best_goal['pattern'],
            confidence=best_goal['confidence']
        )
        
        self.discovered_goals_history.append(discovered)
        
        return {
            'name': discovered.name,
            'weight': discovered.weight,
            'source_behaviors': discovered.source_behaviors,
            'novelty_score': discovered.novelty_score,
            'emergence_pattern': discovered.emergence_pattern,
            'confidence': discovered.confidence
        }
    
    def _analyze_behavior_patterns(self, behavior_history: List[Dict]) -> List[Dict]:
        """分析行为模式"""
        
        # 提取行为名称
        behavior_names = [b.get('action', b.get('behavior', 'unknown')) for b in behavior_history]
        
        # 计算行为频率
        behavior_freq = Counter(behavior_names)
        
        # 找出高频行为
        high_freq_behaviors = {
            beh: freq for beh, freq in behavior_freq.items()
            if freq >= self.min_pattern_frequency
        }
        
        if not high_freq_behaviors:
            return []
        
        # 分析行为组合模式
        patterns = []
        
        # 使用滑动窗口分析行为序列
        window_size = min(self.behavior_window, len(behavior_history))
        
        for i in range(len(behavior_history) - window_size + 1):
            window_behaviors = behavior_names[i:i+window_size]
            
            # 检测重复模式
            pattern_signature = self._detect_pattern_signature(window_behaviors)
            
            if pattern_signature:
                patterns.append({
                    'behaviors': window_behaviors[:10],  # 只保留前10个
                    'signature': pattern_signature,
                    'frequency': len([p for p in patterns if p['signature'] == pattern_signature]) + 1
                })
        
        return patterns
    
    def _detect_pattern_signature(self, behaviors: List[str]) -> Optional[str]:
        """检测模式签名"""
        
        # 检查是否匹配已知目标模板
        for goal_type, keywords in self.goal_templates.items():
            matched_keywords = [kw for kw in keywords if any(kw in beh for beh in behaviors)]
            
            if len(matched_keywords) >= 2:  # 至少匹配2个关键词
                return f"{goal_type}_pattern"
        
        # 检查行为重复模式
        unique_behaviors = set(behaviors)
        
        if len(unique_behaviors) < len(behaviors) * 0.5:  # 重复率>50%
            return "repetition_pattern"
        
        # 检查行为多样性模式
        if len(unique_behaviors) > len(behaviors) * 0.8:  # 多样性>80%
            return "exploration_pattern"
        
        return None
    
    def _extract_candidate_goals(self, 
                                patterns: List[Dict],
                                existing_drives: List[str]) -> List[Dict]:
        """提取候选目标"""
        
        candidates = []
        
        for pattern in patterns:
            signature = pattern['signature']
            behaviors = pattern['behaviors']
            frequency = pattern['frequency']
            
            # 从签名提取目标类型
            goal_type = signature.replace('_pattern', '')
            
            # 检查是否为新目标（不在已存在驱动中）
            if goal_type in existing_drives:
                continue
            
            # 检查是否与已存在驱动相似
            is_novel = self._check_novelty(goal_type, existing_drives)
            
            if not is_novel:
                continue
            
            # 计算目标权重（基于频率）
            weight = min(1.0, frequency / 20.0)  # 最大权重为1.0
            
            # 计算置信度
            confidence = min(1.0, len(behaviors) / 10.0 * frequency / 5.0)
            
            candidates.append({
                'name': goal_type,
                'weight': weight,
                'source_behaviors': behaviors[:5],  # 最多记录5个来源行为
                'pattern': signature,
                'frequency': frequency,
                'confidence': confidence
            })
        
        return candidates
    
    def _check_novelty(self, goal_type: str, existing_drives: List[str]) -> bool:
        """检查目标新颖性"""
        
        # 直接匹配检查
        if goal_type in existing_drives:
            return False
        
        # 语义相似性检查（简化版）
        for existing in existing_drives:
            # 检查是否包含相同关键词
            goal_keywords = self.goal_templates.get(goal_type, [])
            existing_keywords = self.goal_templates.get(existing, [])
            
            overlap = len(set(goal_keywords) & set(existing_keywords))
            
            if overlap >= 3:  # 重叠超过3个关键词视为相似
                return False
        
        return True
    
    def _select_best_goal(self, candidates: List[Dict]) -> Dict:
        """选择最佳候选目标"""
        
        if not candidates:
            return None
        
        # 综合评分：频率 + 置信度
        scored_candidates = []
        
        for candidate in candidates:
            score = candidate['frequency'] * 0.5 + candidate['confidence'] * 0.5
            scored_candidates.append((score, candidate))
        
        # 按评分排序
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        return scored_candidates[0][1]
    
    def _calculate_novelty(self, goal_name: str, existing_drives: List[str]) -> float:
        """计算新颖性分数"""
        
        # 直接匹配检查
        if goal_name in existing_drives:
            return 0.0
        
        # 语义距离计算（简化版）
        goal_keywords = set(self.goal_templates.get(goal_name, [goal_name]))
        
        max_similarity = 0.0
        
        for existing in existing_drives:
            existing_keywords = set(self.goal_templates.get(existing, [existing]))
            
            # Jaccard相似度
            intersection = len(goal_keywords & existing_keywords)
            union = len(goal_keywords | existing_keywords)
            
            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)
        
        # 新颖性 = 1 - 最大相似度
        novelty = 1.0 - max_similarity
        
        return novelty
    
    def get_discovery_summary(self) -> Dict:
        """获取发现摘要"""
        
        return {
            'total_discovered': len(self.discovered_goals_history),
            'goal_names': [g.name for g in self.discovered_goals_history],
            'avg_novelty': np.mean([g.novelty_score for g in self.discovered_goals_history]) if self.discovered_goals_history else 0.0,
            'avg_confidence': np.mean([g.confidence for g in self.discovered_goals_history]) if self.discovered_goals_history else 0.0
        }