#!/usr/bin/env python3
"""
MOSS v7.0 - Creative Thinking Module
创造性思维模块

核心功能:
- 发散思维
- 联想能力
- 创新问题解决
- 创造性评估

Author: MOSS Project
Date: 2026-04-03
Version: 7.0.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random


@dataclass
class CreativeSolution:
    """创造性解决方案"""
    problem: str
    solution: str
    originality: float = 0.5
    usefulness: float = 0.5
    creativity_score: float = 0.5
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'problem': self.problem,
            'solution': self.solution,
            'originality': self.originality,
            'usefulness': self.usefulness,
            'creativity_score': self.creativity_score,
            'generated_at': self.generated_at.isoformat()
        }


class CreativeThinking:
    """
    创造性思维模块
    
    生成和评估创造性解决方案
    """
    
    def __init__(self):
        self.solutions: List[CreativeSolution] = []
        
        self.stats = {
            'solutions_generated': 0,
            'avg_creativity': 0.0,
            'high_creativity_count': 0
        }
    
    def generate_solution(self, problem: str, 
                         context: Dict) -> CreativeSolution:
        """
        生成创造性解决方案
        
        Args:
            problem: 问题描述
            context: 上下文
            
        Returns:
            创造性解决方案
        """
        # 发散思维：生成多个想法
        ideas = self._divergent_thinking(problem, context)
        
        # 联想能力：连接不相关概念
        associations = self._associative_thinking(ideas)
        
        # 生成解决方案
        solution_text = self._synthesize_solution(problem, associations)
        
        # 评估创造性
        originality = self._assess_originality(associations)
        usefulness = self._assess_usefulness(solution_text, context)
        creativity_score = (originality * 0.6 + usefulness * 0.4)
        
        solution = CreativeSolution(
            problem=problem,
            solution=solution_text,
            originality=originality,
            usefulness=usefulness,
            creativity_score=creativity_score
        )
        
        self.solutions.append(solution)
        self.stats['solutions_generated'] += 1
        
        if creativity_score > 0.7:
            self.stats['high_creativity_count'] += 1
        
        # 更新平均创造性
        n = self.stats['solutions_generated']
        self.stats['avg_creativity'] = (
            (self.stats['avg_creativity'] * (n - 1) + creativity_score) / n
        )
        
        return solution
    
    def _divergent_thinking(self, problem: str, 
                           context: Dict) -> List[str]:
        """发散思维：生成多个想法"""
        # 简化实现：基于问题生成变体
        ideas = [
            f"Approach 1: {problem}",
            f"Approach 2: Alternative {problem}",
            f"Approach 3: Creative {problem}",
        ]
        return ideas
    
    def _associative_thinking(self, ideas: List[str]) -> List[str]:
        """联想思维：连接不相关概念"""
        # 简化实现：添加随机关联
        concepts = ['innovation', 'optimization', 'automation', 'intelligence']
        associations = []
        
        for idea in ideas:
            concept = random.choice(concepts)
            associations.append(f"{idea} via {concept}")
        
        return associations
    
    def _synthesize_solution(self, problem: str, 
                            associations: List[str]) -> str:
        """综合解决方案"""
        # 简化实现：组合关联
        solution = f"Solution to {problem}: " + " + ".join(associations[:2])
        return solution
    
    def _assess_originality(self, associations: List[str]) -> float:
        """评估原创性"""
        # 简化实现：基于关联多样性
        unique_concepts = len(set(associations))
        return min(1.0, unique_concepts / 5)
    
    def _assess_usefulness(self, solution: str, 
                          context: Dict) -> float:
        """评估实用性"""
        # 简化实现：基于上下文匹配
        base_score = 0.7
        
        if context.get('feasible', True):
            base_score += 0.1
        if context.get('relevant', True):
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'total_solutions': len(self.solutions),
            'high_creativity_ratio': (
                self.stats['high_creativity_count'] / 
                max(self.stats['solutions_generated'], 1)
            )
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.0 - Creative Thinking Test")
    print("=" * 60)
    
    # 创建创造性思维模块
    creative = CreativeThinking()
    
    # 测试创造性解决方案生成
    print("\n1. 测试创造性解决方案...")
    
    problem = "Improve system performance"
    context = {'feasible': True, 'relevant': True}
    
    solution = creative.generate_solution(problem, context)
    
    print(f"   问题：{solution.problem}")
    print(f"   方案：{solution.solution[:80]}...")
    print(f"   原创性：{solution.originality:.2f}")
    print(f"   实用性：{solution.usefulness:.2f}")
    print(f"   创造性：{solution.creativity_score:.2f}")
    
    # 获取状态
    print("\n2. 创造性思维状态:")
    status = creative.get_status()
    print(f"   总方案数：{status['total_solutions']}")
    print(f"   平均创造性：{status['stats']['avg_creativity']:.2f}")
    print(f"   高创造性比例：{status['high_creativity_ratio']:.1%}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
