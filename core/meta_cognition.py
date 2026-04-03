#!/usr/bin/env python3
"""
MOSS v6.0 - Meta Cognition Engine
元认知引擎

核心功能:
- 思考监控
- 学习监控
- 决策监控
- 元认知评估

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MetaCognitiveState:
    """元认知状态"""
    # 思考监控
    thinking_awareness: float = 0.5
    
    # 学习监控
    learning_awareness: float = 0.5
    
    # 决策监控
    decision_awareness: float = 0.5
    
    # 整体元认知水平
    overall_level: float = 0.5
    
    # 更新时间
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'thinking_awareness': self.thinking_awareness,
            'learning_awareness': self.learning_awareness,
            'decision_awareness': self.decision_awareness,
            'overall_level': self.overall_level,
            'timestamp': self.timestamp.isoformat()
        }


class MetaCognition:
    """
    元认知引擎
    
    监控和评估认知过程
    """
    
    def __init__(self):
        self.state = MetaCognitiveState()
        
        self.thought_history: List[Dict] = []
        self.learning_history: List[Dict] = []
        self.decision_history: List[Dict] = []
        
        self.stats = {
            'thoughts_monitored': 0,
            'learnings_tracked': 0,
            'decisions_monitored': 0,
            'meta_updates': 0
        }
    
    def monitor_thinking(self, thought_content: str,
                        confidence: float,
                        outcome: Optional[float] = None):
        """
        监控思考过程
        
        Args:
            thought_content: 思考内容
            confidence: 思考置信度
            outcome: 结果 (如果有)
        """
        thought = {
            'content': thought_content,
            'confidence': confidence,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat()
        }
        self.thought_history.append(thought)
        self.stats['thoughts_monitored'] += 1
        
        # 更新思考意识
        if outcome is not None:
            # 根据结果调整
            accuracy = abs(outcome - confidence)
            self.state.thinking_awareness = 1.0 - min(accuracy, 1.0)
        else:
            self.state.thinking_awareness = confidence
        
        self._update_overall()
    
    def monitor_learning(self, topic: str,
                        progress: float,
                        difficulty: float):
        """
        监控学习过程
        
        Args:
            topic: 学习主题
            progress: 进度 (0-1)
            difficulty: 难度 (0-1)
        """
        learning = {
            'topic': topic,
            'progress': progress,
            'difficulty': difficulty,
            'timestamp': datetime.now().isoformat()
        }
        self.learning_history.append(learning)
        self.stats['learnings_tracked'] += 1
        
        # 更新学习意识
        self.state.learning_awareness = progress * (1.0 - difficulty * 0.5)
        
        self._update_overall()
    
    def monitor_decision(self, decision: str,
                        alternatives: List[str],
                        outcome: Optional[float] = None):
        """
        监控决策过程
        
        Args:
            decision: 决策内容
            alternatives: 备选方案
            outcome: 结果 (如果有)
        """
        decision_record = {
            'decision': decision,
            'alternatives': alternatives,
            'outcome': outcome,
            'timestamp': datetime.now().isoformat()
        }
        self.decision_history.append(decision_record)
        self.stats['decisions_monitored'] += 1
        
        # 更新决策意识
        if outcome is not None:
            self.state.decision_awareness = outcome
        else:
            self.state.decision_awareness = 0.7  # 默认
        
        self._update_overall()
    
    def _update_overall(self):
        """更新整体元认知水平"""
        self.state.overall_level = (
            self.state.thinking_awareness * 0.4 +
            self.state.learning_awareness * 0.3 +
            self.state.decision_awareness * 0.3
        )
        self.state.timestamp = datetime.now()
        self.stats['meta_updates'] += 1
    
    def evaluate_meta_cognition(self) -> Tuple[float, Dict]:
        """
        评估元认知水平
        
        Returns:
            (整体分数，详细评估)
        """
        evaluation = {
            'thinking': {
                'level': self.state.thinking_awareness,
                'history_length': len(self.thought_history),
                'avg_confidence': np.mean([t['confidence'] for t in self.thought_history]) if self.thought_history else 0
            },
            'learning': {
                'level': self.state.learning_awareness,
                'history_length': len(self.learning_history),
                'avg_progress': np.mean([l['progress'] for l in self.learning_history]) if self.learning_history else 0
            },
            'decision': {
                'level': self.state.decision_awareness,
                'history_length': len(self.decision_history),
                'success_rate': np.mean([1.0 if d.get('outcome', 0) > 0.5 else 0.0 for d in self.decision_history]) if self.decision_history else 0
            },
            'overall': self.state.overall_level
        }
        
        return self.state.overall_level, evaluation
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'state': self.state.to_dict(),
            'stats': self.stats,
            'history_lengths': {
                'thoughts': len(self.thought_history),
                'learnings': len(self.learning_history),
                'decisions': len(self.decision_history)
            }
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.0 - Meta Cognition Test")
    print("=" * 60)
    
    # 创建元认知
    meta = MetaCognition()
    
    # 监控思考
    print("\n1. 监控思考...")
    meta.monitor_thinking("Solving math problem", 0.8, outcome=0.9)
    meta.monitor_thinking("Writing code", 0.7, outcome=0.6)
    print(f"   思考记录：{len(meta.thought_history)}")
    
    # 监控学习
    print("\n2. 监控学习...")
    meta.monitor_learning("Python", 0.8, 0.5)
    meta.monitor_learning("Machine Learning", 0.6, 0.7)
    print(f"   学习记录：{len(meta.learning_history)}")
    
    # 监控决策
    print("\n3. 监控决策...")
    meta.monitor_decision(
        "Choose algorithm A",
        ["algorithm A", "algorithm B", "algorithm C"],
        outcome=0.85
    )
    print(f"   决策记录：{len(meta.decision_history)}")
    
    # 评估元认知
    print("\n4. 评估元认知...")
    overall, evaluation = meta.evaluate_meta_cognition()
    print(f"   整体水平：{overall:.3f}")
    print(f"   思考水平：{evaluation['thinking']['level']:.3f}")
    print(f"   学习水平：{evaluation['learning']['level']:.3f}")
    print(f"   决策水平：{evaluation['decision']['level']:.3f}")
    
    # 获取状态
    print("\n5. 元认知状态:")
    status = meta.get_status()
    print(f"   监控更新：{status['stats']['meta_updates']}")
    print(f"   思考监控：{status['stats']['thoughts_monitored']}")
    print(f"   学习跟踪：{status['stats']['learnings_tracked']}")
    print(f"   决策监控：{status['stats']['decisions_monitored']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
