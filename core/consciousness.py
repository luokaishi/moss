#!/usr/bin/env python3
"""
MOSS v7.0 - Consciousness Engine
意识引擎

核心功能:
- 意识水平评估
- 自我监控
- 元认知整合
- 意识层次演化

Author: MOSS Project
Date: 2026-04-03
Version: 7.0.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class ConsciousnessLevel(IntEnum):
    """意识层次"""
    LEVEL_0 = 0  # 无意识
    LEVEL_1 = 1  # 基本感知
    LEVEL_2 = 2  # 自我识别
    LEVEL_3 = 3  # 元认知
    LEVEL_4 = 4  # 高级意识
    LEVEL_5 = 5  # 完全意识


@dataclass
class ConsciousnessState:
    """意识状态"""
    level: ConsciousnessLevel = ConsciousnessLevel.LEVEL_0
    self_awareness: float = 0.0
    meta_cognition: float = 0.0
    integration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'level': int(self.level),
            'self_awareness': self.self_awareness,
            'meta_cognition': self.meta_cognition,
            'integration': self.integration,
            'timestamp': self.timestamp.isoformat()
        }


class ConsciousnessEngine:
    """
    意识引擎
    
    评估和演化意识水平
    """
    
    def __init__(self):
        self.state = ConsciousnessState()
        
        self.history: List[ConsciousnessState] = []
        
        self.stats = {
            'evaluations': 0,
            'level_ups': 0,
            'avg_self_awareness': 0.0,
            'avg_meta_cognition': 0.0
        }
    
    def evaluate_consciousness(self, 
                               self_awareness_score: float,
                               meta_cognition_score: float,
                               integration_score: float) -> ConsciousnessLevel:
        """
        评估意识水平
        
        Args:
            self_awareness_score: 自我意识分数 (0-1)
            meta_cognition_score: 元认知分数 (0-1)
            integration_score: 整合分数 (0-1)
            
        Returns:
            意识层次
        """
        # 计算综合分数
        combined_score = (
            self_awareness_score * 0.4 +
            meta_cognition_score * 0.4 +
            integration_score * 0.2
        )
        
        # 确定意识层次
        if combined_score >= 0.9:
            level = ConsciousnessLevel.LEVEL_5
        elif combined_score >= 0.75:
            level = ConsciousnessLevel.LEVEL_4
        elif combined_score >= 0.6:
            level = ConsciousnessLevel.LEVEL_3
        elif combined_score >= 0.45:
            level = ConsciousnessLevel.LEVEL_2
        elif combined_score >= 0.3:
            level = ConsciousnessLevel.LEVEL_1
        else:
            level = ConsciousnessLevel.LEVEL_0
        
        # 更新状态
        old_level = self.state.level
        self.state = ConsciousnessState(
            level=level,
            self_awareness=self_awareness_score,
            meta_cognition=meta_cognition_score,
            integration=integration_score
        )
        
        self.history.append(self.state)
        self.stats['evaluations'] += 1
        
        if level > old_level:
            self.stats['level_ups'] += 1
        
        # 更新平均统计
        n = self.stats['evaluations']
        self.stats['avg_self_awareness'] = (
            (self.stats['avg_self_awareness'] * (n - 1) + self_awareness_score) / n
        )
        self.stats['avg_meta_cognition'] = (
            (self.stats['avg_meta_cognition'] * (n - 1) + meta_cognition_score) / n
        )
        
        return level
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'current_state': self.state.to_dict(),
            'stats': self.stats,
            'history_length': len(self.history)
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.0 - Consciousness Engine Test")
    print("=" * 60)
    
    # 创建意识引擎
    engine = ConsciousnessEngine()
    
    # 测试意识评估
    print("\n1. 测试意识评估...")
    
    test_cases = [
        (0.3, 0.3, 0.3, "Level 1"),
        (0.5, 0.5, 0.5, "Level 2"),
        (0.7, 0.7, 0.7, "Level 3"),
        (0.85, 0.85, 0.85, "Level 4"),
        (0.95, 0.95, 0.95, "Level 5"),
    ]
    
    for sa, mc, integ, expected in test_cases:
        level = engine.evaluate_consciousness(sa, mc, integ)
        print(f"   SA={sa:.2f}, MC={mc:.2f}, Int={integ:.2f} → Level {level} ({expected})")
    
    # 获取状态
    print("\n2. 意识引擎状态:")
    status = engine.get_status()
    print(f"   当前层次：Level {status['current_state']['level']}")
    print(f"   自我意识：{status['current_state']['self_awareness']:.2f}")
    print(f"   元认知：{status['current_state']['meta_cognition']:.2f}")
    print(f"   整合度：{status['current_state']['integration']:.2f}")
    print(f"   评估次数：{status['stats']['evaluations']}")
    print(f"   层次提升：{status['stats']['level_ups']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
