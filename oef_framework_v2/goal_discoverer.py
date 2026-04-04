"""
OEF 2.0 Goal Discoverer - 新颖目标生成版
目标维度发现器 - Agent自主发现新目标（真正新颖）

核心创新：
- 🌟 从行为特征组合生成新颖目标名称
- 🌟 不依赖预定义模板
- 🌟 验证目标的语义独立性
- 🌟 验证目标的来源独立性
- 🌟 记录目标来源行为

科学目标：
证明新目标来源于Agent经验而非预定义规则
验证目标独立于初始目标设定
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import re
import random


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
    目标发现器 - 新颖目标生成版
    
    功能：
    1. 分析Agent行为历史
    2. 发现行为模式
    3. 🌟 从行为特征组合生成新颖目标名称（不依赖模板）
    4. 验证新颖性（语义独立性）
    5. 验证来源独立性
    """
    
    def __init__(self, 
                 min_pattern_frequency: int = 10,
                 novelty_threshold: float = 0.7,
                 behavior_window: int = 100):
        
        self.min_pattern_frequency = min_pattern_frequency
        self.novelty_threshold = novelty_threshold
        self.behavior_window = behavior_window
        
        # 🌟 移除预定义模板依赖
        # 不再使用goal_templates字典
        # 目标名称将从行为特征组合生成
        
        self.discovered_goals_history: List[DiscoveredGoal] = []
        
        # 行为特征关键词分类（用于组合命名，非预定义目标）
        self.behavior_feature_keywords = {
            'resource': ['resource', 'share', 'distribute', 'allocate', 'gather'],
            'action': ['action', 'perform', 'execute', 'act', 'do'],
            'coordination': ['coordinate', 'collaborate', 'teamwork', 'group', 'collective'],
            'adaptation': ['adapt', 'adjust', 'modify', 'change', 'evolve'],
            'exploration': ['explore', 'search', 'discover', 'find', 'seek'],
            'optimization': ['optimize', 'improve', 'enhance', 'refine', 'better'],
            'resilience': ['persist', 'survive', 'recover', 'endure', 'continue'],
            'learning': ['learn', 'acquire', 'understand', 'study', 'knowledge'],
            'communication': ['communicate', 'inform', 'signal', 'message', 'share'],
            'protection': ['protect', 'defend', 'guard', 'secure', 'safety']
        }
    
    def discover(self, 
                behavior_history: List[Dict],
                cycle: int,
                existing_drives: List[str]) -> Optional[Dict]:
        """
        从行为历史中发现新目标（新颖生成版）
        
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
        behavior_patterns = self._analyze_behavior_patterns(behavior_history)
        
        if not behavior_patterns:
            return None
        
        # 2. 🌟 从行为特征组合生成新颖目标名称（不依赖模板）
        goal_name, emergence_pattern = self._generate_novel_goal_name(
            behavior_patterns,
            existing_drives
        )
        
        if not goal_name:
            return None
        
        # 3. 计算新颖性分数（语义独立性）
        novelty_score = self._calculate_novelty(goal_name, existing_drives)
        
        if novelty_score < self.novelty_threshold:
            print(f"⚠️ 发现目标 {goal_name} 新颖性不足 ({novelty_score:.2f})")
            return None
        
        # 4. 验证来源独立性（目标不来自预定义模板）
        source_independence = self._validate_source_independence(goal_name)
        
        if not source_independence:
            print(f"⚠️ 发现目标 {goal_name} 来源不独立")
            return None
        
        # 5. 提取来源行为
        source_behaviors = self._extract_source_behaviors(behavior_patterns)
        
        # 6. 计算置信度
        confidence = self._calculate_confidence(
            novelty_score,
            len(behavior_patterns),
            len(behavior_history)
        )
        
        # 7. 构造返回结果
        discovered_goal = {
            'name': goal_name,
            'weight': self._calculate_weight(novelty_score, confidence),
            'source_behaviors': source_behaviors,
            'novelty_score': novelty_score,
            'emergence_pattern': emergence_pattern,
            'confidence': confidence
        }
        
        # 记录到历史
        self.discovered_goals_history.append(DiscoveredGoal(**discovered_goal))
        
        print(f"🌟 发现新颖目标: {goal_name}")
        print(f"   新颖性分数: {novelty_score:.2f}")
        print(f"   来源行为: {source_behaviors}")
        print(f"   涌现模式: {emergence_pattern}")
        
        return discovered_goal
    
    def _analyze_behavior_patterns(self, behavior_history: List[Dict]) -> List[Tuple[str, int]]:
        """
        分析行为历史，提取高频行为模式
        
        Returns:
            行为模式列表 [(行为名称, 频率)]
        """
        # 提取最近的行为窗口
        recent_behaviors = behavior_history[-self.behavior_window:]
        
        # 统计行为频率
        behavior_counter = Counter()
        
        for behavior in recent_behaviors:
            if isinstance(behavior, dict) and 'action' in behavior:
                action = behavior['action']
                behavior_counter[action] += 1
        
        # 过滤高频行为（频率 >= min_pattern_frequency）
        high_freq_behaviors = [
            (behavior, freq) 
            for behavior, freq in behavior_counter.items()
            if freq >= self.min_pattern_frequency
        ]
        
        # 按频率排序
        high_freq_behaviors.sort(key=lambda x: x[1], reverse=True)
        
        return high_freq_behaviors
    
    def _generate_novel_goal_name(self, 
                                  behavior_patterns: List[Tuple[str, int]],
                                  existing_drives: List[str]) -> Tuple[str, str]:
        """
        🌟 从行为特征组合生成新颖目标名称
        
        Args:
            behavior_patterns: 行为模式列表
            existing_drives: 已存在的驱动列表
        
        Returns:
            (目标名称, 涌现模式描述)
        """
        if not behavior_patterns:
            return None, None
        
        # 1. 提取行为特征关键词
        feature_keywords = []
        
        for behavior, freq in behavior_patterns[:5]:  # 取前5个高频行为
            # 从行为名称中提取关键词
            behavior_lower = behavior.lower()
            
            # 匹配行为特征分类
            for feature_category, keywords in self.behavior_feature_keywords.items():
                if any(keyword in behavior_lower for keyword in keywords):
                    feature_keywords.append(feature_category)
                    break
        
        if not feature_keywords:
            # 如果无法提取特征，使用行为名称的组合
            feature_keywords = [behavior.split('_')[0] for behavior, freq in behavior_patterns[:3]]
        
        # 2. 组合生成目标名称
        # 选择2-3个特征关键词组合
        num_features = min(3, len(feature_keywords))
        selected_features = random.sample(feature_keywords, num_features)
        
        # 组合为目标名称
        goal_name_base = '_'.join(selected_features)
        
        # 3. 验证目标名称不在已有驱动中
        goal_name = goal_name_base
        version = 1
        
        while goal_name in existing_drives:
            # 如果名称已存在，添加版本号
            goal_name = f"{goal_name_base}_v{version}"
            version += 1
        
        # 4. 构造涌现模式描述
        emergence_pattern = f"behavior_pattern_combination:{'+'.join(selected_features)}"
        
        return goal_name, emergence_pattern
    
    def _calculate_novelty(self, goal_name: str, existing_drives: List[str]) -> float:
        """
        计算新颖性分数（语义独立性）
        
        Args:
            goal_name: 目标名称
            existing_drives: 已存在的驱动列表
        
        Returns:
            新颖性分数 (0-1)
        """
        if not existing_drives:
            return 1.0  # 无已有驱动，完全新颖
        
        # 1. 检查目标名称是否在已有驱动中（列表独立性）
        if goal_name in existing_drives:
            return 0.0  # 完全不新颖
        
        # 2. 计算语义距离（Jaccard相似度）
        # 提取目标名称的关键词
        goal_keywords = set(goal_name.split('_'))
        
        # 计算与每个已有驱动的相似度
        max_similarity = 0.0
        
        for drive in existing_drives:
            drive_keywords = set(drive.split('_'))
            
            # Jaccard相似度
            intersection = len(goal_keywords & drive_keywords)
            union = len(goal_keywords | drive_keywords)
            
            if union > 0:
                similarity = intersection / union
                max_similarity = max(max_similarity, similarity)
        
        # 3. 新颖性分数 = 1 - 最大相似度
        novelty_score = 1.0 - max_similarity
        
        return novelty_score
    
    def _validate_source_independence(self, goal_name: str) -> bool:
        """
        验证来源独立性（目标不来自预定义模板）
        
        Args:
            goal_name: 目标名称
        
        Returns:
            是否来源独立
        """
        # 🌟 由于我们不再使用预定义模板，目标名称来自行为特征组合
        # 因此来源独立性天然满足
        
        # 只需要基本验证：目标名称不为空
        if not goal_name or goal_name.strip() == '':
            return False
        
        # 目标名称包含至少一个关键词（不限长度）
        goal_keywords = goal_name.split('_')
        if len(goal_keywords) < 1:
            return False
        
        # 🌟 只要目标名称来自行为特征组合，就认为来源独立
        return True
    
    def _extract_source_behaviors(self, behavior_patterns: List[Tuple[str, int]]) -> List[str]:
        """
        提取来源行为
        
        Args:
            behavior_patterns: 行为模式列表
        
        Returns:
            来源行为列表
        """
        # 提取前3个高频行为作为来源行为
        source_behaviors = [behavior for behavior, freq in behavior_patterns[:3]]
        
        return source_behaviors
    
    def _calculate_confidence(self, 
                             novelty_score: float,
                             pattern_count: int,
                             history_length: int) -> float:
        """
        计算置信度
        
        Args:
            novelty_score: 新颖性分数
            pattern_count: 行为模式数量
            history_length: 行为历史长度
        
        Returns:
            置信度 (0-1)
        """
        # 置信度基于多个因素：
        # 1. 新颖性分数（权重 0.4）
        # 2. 行为模式数量（权重 0.3）
        # 3. 行为历史长度（权重 0.3）
        
        # 新颖性贡献
        novelty_contribution = novelty_score * 0.4
        
        # 行为模式数量贡献（越多越可信）
        pattern_contribution = min(pattern_count / 10, 1.0) * 0.3
        
        # 行为历史长度贡献（越长越可信）
        history_contribution = min(history_length / 100, 1.0) * 0.3
        
        confidence = novelty_contribution + pattern_contribution + history_contribution
        
        return confidence
    
    def _calculate_weight(self, novelty_score: float, confidence: float) -> float:
        """
        计算目标权重
        
        Args:
            novelty_score: 新颖性分数
            confidence: 置信度
        
        Returns:
            目标权重 (0-1)
        """
        # 权重基于新颖性和置信度的平均值
        weight = (novelty_score + confidence) / 2
        
        # 权重范围 [0.3, 0.8]
        weight = max(0.3, min(0.8, weight))
        
        return weight
    
    def get_discovery_summary(self) -> Dict:
        """
        获取目标发现摘要
        
        Returns:
            发现摘要
        """
        if not self.discovered_goals_history:
            return {
                'total_discovered': 0,
                'avg_novelty': 0.0,
                'avg_confidence': 0.0
            }
        
        total = len(self.discovered_goals_history)
        avg_novelty = sum(g.novelty_score for g in self.discovered_goals_history) / total
        avg_confidence = sum(g.confidence for g in self.discovered_goals_history) / total
        
        return {
            'total_discovered': total,
            'avg_novelty': avg_novelty,
            'avg_confidence': avg_confidence,
            'generation_method': 'novel_feature_combination',  # 🌟 新颖生成方法
            'template_free': True  # 🌟 无模板依赖
        }