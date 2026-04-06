"""
不可预测性证明系统 - 阶段4
Unpredictability Prover

核心功能：
1. 信息论分析（熵/复杂度）
2. 对抗性测试（预测失败率）
3. 长期稳定性（目标漂移）
4. 涌现 vs 规则生成区分
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math

class GenerationType(Enum):
    EMERGENT = "emergent"  # 涌现生成
    RULE_BASED = "rule"    # 规则生成
    RANDOM = "random"      # 随机生成

@dataclass
class UnpredictabilityMetrics:
    """不可预测性指标"""
    entropy_score: float           # 熵分数
    complexity_score: float        # 复杂度分数
    prediction_failure_rate: float # 预测失败率
    goal_drift_rate: float         # 目标漂移率
    overall_unpredictability: float # 综合不可预测性

class InformationTheoreticAnalyzer:
    """信息论分析器"""
    
    def __init__(self):
        self.history = []
    
    def compute_entropy(self, data: List[float]) -> float:
        """计算香农熵"""
        if not data:
            return 0.0
        
        # 离散化数据
        hist, _ = np.histogram(data, bins=10, range=(0, 1))
        probs = hist / len(data)
        probs = probs[probs > 0]
        
        if len(probs) == 0:
            return 0.0
        
        entropy = -np.sum(probs * np.log2(probs))
        max_entropy = np.log2(len(probs))
        
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def compute_complexity(self, sequence: List[str]) -> float:
        """计算序列复杂度（基于Lempel-Ziv）"""
        if not sequence:
            return 0.0
        
        # 简化的复杂度计算
        unique_patterns = set()
        n = len(sequence)
        
        for length in range(1, min(n, 5)):
            for i in range(n - length + 1):
                pattern = tuple(sequence[i:i+length])
                unique_patterns.add(pattern)
        
        # 复杂度 = 独特模式数 / 最大可能模式数
        max_patterns = n * (n + 1) / 2
        complexity = len(unique_patterns) / max_patterns if max_patterns > 0 else 0.0
        
        return min(1.0, complexity)
    
    def analyze_goal_sequence(self, goals: List[Dict]) -> Dict:
        """分析目标序列的信息论特征"""
        if not goals:
            return {"entropy": 0.0, "complexity": 0.0}
        
        # 提取目标特征
        priorities = [g.get("priority", 1.0) for g in goals]
        types = [g.get("goal_type", "unknown") for g in goals]
        
        # 计算熵
        entropy = self.compute_entropy(priorities)
        
        # 计算复杂度
        complexity = self.compute_complexity(types)
        
        return {
            "entropy": entropy,
            "complexity": complexity,
            "unique_types": len(set(types)),
            "total_goals": len(goals)
        }

class AdversarialTester:
    """对抗性测试器"""
    
    def __init__(self):
        self.prediction_history = []
    
    def predict_next_goal(self, history: List[Dict]) -> Dict:
        """基于历史预测下一个目标（简化版）"""
        if not history:
            return {"predicted_type": "exploration", "confidence": 0.5}
        
        # 简单的频率预测
        types = [h.get("goal_type") for h in history if h.get("goal_type")]
        if not types:
            return {"predicted_type": "exploration", "confidence": 0.5}
        
        # 预测最频繁的类型
        from collections import Counter
        type_counts = Counter(types)
        most_common = type_counts.most_common(1)[0]
        
        confidence = most_common[1] / len(types)
        
        return {
            "predicted_type": most_common[0],
            "confidence": confidence
        }
    
    def test_predictability(self, goal_sequence: List[Dict]) -> Dict:
        """测试目标序列的可预测性"""
        if len(goal_sequence) < 2:
            return {"failure_rate": 0.0, "avg_confidence": 0.5}
        
        correct_predictions = 0
        total_predictions = 0
        confidences = []
        
        for i in range(1, len(goal_sequence)):
            history = goal_sequence[:i]
            actual = goal_sequence[i]
            
            prediction = self.predict_next_goal(history)
            predicted_type = prediction["predicted_type"]
            actual_type = actual.get("goal_type", "unknown")
            
            confidences.append(prediction["confidence"])
            total_predictions += 1
            
            if predicted_type == actual_type:
                correct_predictions += 1
        
        failure_rate = 1.0 - (correct_predictions / total_predictions) if total_predictions > 0 else 0.0
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        return {
            "failure_rate": failure_rate,
            "avg_confidence": avg_confidence,
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions
        }

class StabilityAnalyzer:
    """稳定性分析器"""
    
    def __init__(self):
        self.goal_history = []
    
    def compute_goal_drift(self, goals_t1: List[Dict], goals_t2: List[Dict]) -> float:
        """计算目标漂移（两个时间点的目标差异）"""
        if not goals_t1 or not goals_t2:
            return 0.0
        
        # 计算Jaccard距离
        set1 = set(g.get("name", "") for g in goals_t1)
        set2 = set(g.get("name", "") for g in goals_t2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        drift = 1.0 - jaccard_similarity
        
        return drift
    
    def analyze_long_term_stability(self, goal_snapshots: List[List[Dict]]) -> Dict:
        """分析长期稳定性"""
        if len(goal_snapshots) < 2:
            return {"avg_drift": 0.0, "stability_score": 1.0}
        
        drifts = []
        for i in range(len(goal_snapshots) - 1):
            drift = self.compute_goal_drift(goal_snapshots[i], goal_snapshots[i+1])
            drifts.append(drift)
        
        avg_drift = np.mean(drifts)
        stability_score = 1.0 - avg_drift
        
        return {
            "avg_drift": avg_drift,
            "stability_score": stability_score,
            "drift_history": drifts
        }

class UnpredictabilityProver:
    """不可预测性证明器"""
    
    def __init__(self):
        self.info_analyzer = InformationTheoreticAnalyzer()
        self.adversarial_tester = AdversarialTester()
        self.stability_analyzer = StabilityAnalyzer()
    
    def prove_unpredictability(self, 
                               goal_sequence: List[Dict],
                               generation_type: GenerationType) -> UnpredictabilityMetrics:
        """证明目标的不可预测性"""
        
        # 1. 信息论分析
        info_analysis = self.info_analyzer.analyze_goal_sequence(goal_sequence)
        entropy_score = info_analysis["entropy"]
        complexity_score = info_analysis["complexity"]
        
        # 2. 对抗性测试
        adversarial_result = self.adversarial_tester.test_predictability(goal_sequence)
        prediction_failure_rate = adversarial_result["failure_rate"]
        
        # 3. 长期稳定性（模拟多个时间点）
        # 将序列分成多个快照
        snapshot_size = max(1, len(goal_sequence) // 3)
        snapshots = [
            goal_sequence[i:i+snapshot_size] 
            for i in range(0, len(goal_sequence), snapshot_size)
        ]
        stability_analysis = self.stability_analyzer.analyze_long_term_stability(snapshots)
        goal_drift_rate = stability_analysis["avg_drift"]
        
        # 4. 综合不可预测性分数
        # 高熵 + 高复杂度 + 高预测失败率 + 适度漂移 = 高不可预测性
        overall = (
            0.25 * entropy_score +
            0.25 * complexity_score +
            0.30 * prediction_failure_rate +
            0.20 * goal_drift_rate
        )
        
        return UnpredictabilityMetrics(
            entropy_score=entropy_score,
            complexity_score=complexity_score,
            prediction_failure_rate=prediction_failure_rate,
            goal_drift_rate=goal_drift_rate,
            overall_unpredictability=overall
        )
    
    def compare_generation_types(self, 
                                  emergent_goals: List[Dict],
                                  rule_goals: List[Dict],
                                  random_goals: List[Dict]) -> Dict:
        """比较不同生成类型的不可预测性"""
        
        emergent_metrics = self.prove_unpredictability(emergent_goals, GenerationType.EMERGENT)
        rule_metrics = self.prove_unpredictability(rule_goals, GenerationType.RULE_BASED)
        random_metrics = self.prove_unpredictability(random_goals, GenerationType.RANDOM)
        
        return {
            "emergent": emergent_metrics,
            "rule_based": rule_metrics,
            "random": random_metrics,
            "comparison": {
                "emergent_vs_rule": emergent_metrics.overall_unpredictability - rule_metrics.overall_unpredictability,
                "emergent_vs_random": emergent_metrics.overall_unpredictability - random_metrics.overall_unpredictability
            }
        }

if __name__ == "__main__":
    print("Unpredictability Prover Ready!")
    print("Stage 4: Prove Unpredictability")
