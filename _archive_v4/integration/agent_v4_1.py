"""
MOSS v4.1 - Purpose-Enhanced Agent

v4.0 + v3.1融合版本
将9维Purpose系统（D1-D9）集成到v4.0多层架构中

Enhancements:
- D1-D4: Base purposes (Survival/Curiosity/Influence/Optimization)
- D5-D6: Individual (Coherence/Valence)
- D7-D8: Social (Other/Norm)
- D9: Purpose (Self-generated meaning)

Integration:
- D1-D4 → Open Goal Space (goal type mapping)
- D5 → LLM Reasoning (identity consistency)
- D6 → Cost Evaluator (subjective preference)
- D7-D8 → World Model (social prediction)
- D9 → Goal Generator (meaning-driven goal creation)

Author: Cash + Fuxi
Date: 2026-03-22
Version: 4.1.0-dev
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v3')
sys.path.insert(0, '/workspace/projects/moss/v3/core')
sys.path.insert(0, '/workspace/projects/moss/v4/core')
sys.path.insert(0, '/workspace/projects/moss/v4/integration')

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# v4.0 modules
from world_model import WorldModel
from llm_reasoning import LLMReasoningLayer, Reflection
from open_goal_space import GoalManager, Goal, GoalStatus, GoalType

# v3.1 modules
from agent_9d import MOSSv3Agent9D

logger = logging.getLogger(__name__)


@dataclass
class PurposeState:
    """9维Purpose状态"""
    # D1-D4: Base
    survival: float = 0.25
    curiosity: float = 0.25
    influence: float = 0.25
    optimization: float = 0.25
    
    # D5-D6: Individual
    coherence: float = 0.0  # 自我连续性
    valence: float = 0.0    # 主观偏好
    
    # D7-D8: Social
    other_modeling: float = 0.0  # 他者建模
    norm_internalization: float = 0.0  # 规范内化
    
    # D9: Purpose
    self_generated: float = 0.12  # 自生成意义
    
    purpose_statement: str = ""
    last_update: int = 0
    
    def to_vector(self) -> List[float]:
        """转换为向量"""
        return [
            self.survival, self.curiosity, self.influence, self.optimization,
            self.coherence, self.valence,
            self.other_modeling, self.norm_internalization,
            self.self_generated
        ]
    
    @classmethod
    def from_vector(cls, vector: List[float]) -> 'PurposeState':
        """从向量创建"""
        if len(vector) >= 9:
            return cls(
                survival=vector[0],
                curiosity=vector[1],
                influence=vector[2],
                optimization=vector[3],
                coherence=vector[4],
                valence=vector[5],
                other_modeling=vector[6],
                norm_internalization=vector[7],
                self_generated=vector[8]
            )
        return cls()
    
    def get_dominant(self) -> Tuple[str, float]:
        """获取主导Purpose"""
        purposes = {
            'Survival': self.survival,
            'Curiosity': self.curiosity,
            'Influence': self.influence,
            'Optimization': self.optimization
        }
        dominant = max(purposes, key=purposes.get)
        return dominant, purposes[dominant]


class PurposeEnhancedAgent:
    """
    v4.1 Purpose增强型Agent
    
    整合v3.1的9维Purpose系统和v4.0的多层架构
    """
    
    def __init__(self, agent_id: str = "moss_v4_1"):
        self.agent_id = agent_id
        self.step_count = 0
        
        # v3.1: 9维Purpose系统
        self.purpose_state = PurposeState()
        self.coherence_score = 1.0  # D5: 自我连续性
        self.valence_profile = [0.25] * 4  # D6: 主观偏好分布
        
        # v4.0: 多层架构
        self.world_model = WorldModel(state_dim=9)  # 9维状态
        self.reasoning_layer = LLMReasoningLayer()
        self.goal_manager = GoalManager(max_active_goals=5)
        
        # 社交维度状态 (D7-D8)
        self.trust_network = {}  # agent_id -> trust_score
        self.norm_compliance = 1.0  # 规范遵守度
        
        # 历史记录
        self.purpose_history = []
        self.action_history = []
        self.reflection_memory = []
        
        # 性能统计
        self.stats = {
            'purpose_switches': 0,
            'goals_achieved': 0,
            'predictions_made': 0,
            'reflections': 0
        }
    
    def update_purpose(self, context: Dict):
        """
        更新9维Purpose状态
        
        基于环境反馈动态调整Purpose权重
        """
        # 计算环境压力
        survival_pressure = context.get('threat_level', 0) * 0.5
        exploration_opportunity = context.get('novelty', 0) * 0.3
        social_influence = context.get('social_feedback', 0) * 0.2
        
        # D1-D4: Base purposes动态调整
        target_base = [
            0.25 + survival_pressure,  # Survival
            0.25 + exploration_opportunity,  # Curiosity
            0.25 + social_influence,  # Influence
            0.25  # Optimization
        ]
        
        # 平滑过渡 (避免剧烈变化)
        current_base = [self.purpose_state.survival, self.purpose_state.curiosity,
                       self.purpose_state.influence, self.purpose_state.optimization]
        
        learning_rate = 0.1
        new_base = [
            current + learning_rate * (target - current)
            for current, target in zip(current_base, target_base)
        ]
        
        # 归一化
        total = sum(new_base)
        new_base = [x / total * 0.88 for x in new_base]  # 预留12%给D9
        
        self.purpose_state.survival = new_base[0]
        self.purpose_state.curiosity = new_base[1]
        self.purpose_state.influence = new_base[2]
        self.purpose_state.optimization = new_base[3]
        
        # D5: Coherence (自我连续性)
        # 基于Purpose变化幅度
        purpose_change = sum(abs(new - old) for new, old in zip(new_base, current_base))
        self.coherence_score = max(0, 1 - purpose_change * 2)
        self.purpose_state.coherence = self.coherence_score
        
        # D6: Valence (主观偏好)
        # 基于历史成功率更新
        if self.action_history:
            recent_actions = self.action_history[-50:]
            success_by_purpose = {}
            for action in recent_actions:
                p = action.get('purpose', 'Unknown')
                success_by_purpose[p] = success_by_purpose.get(p, [])
                success_by_purpose[p].append(action.get('success', False))
            
            for i, p in enumerate(['Survival', 'Curiosity', 'Influence', 'Optimization']):
                if p in success_by_purpose:
                    success_rate = sum(success_by_purpose[p]) / len(success_by_purpose[p])
                    self.valence_profile[i] = 0.7 * self.valence_profile[i] + 0.3 * success_rate
        
        self.purpose_state.valence = np.mean(self.valence_profile)
        
        # D9: Self-generated purpose
        # 基于目标完成度和自我反思
        if self.stats['goals_achieved'] > 0:
            achievement_rate = self.stats['goals_achieved'] / max(self.step_count / 100, 1)
            self.purpose_state.self_generated = min(0.15, 0.10 + achievement_rate * 0.05)
        
        # 生成Purpose Statement
        self._update_purpose_statement()
        
        # 记录历史
        self.purpose_history.append({
            'step': self.step_count,
            'vector': self.purpose_state.to_vector(),
            'dominant': self.purpose_state.get_dominant()[0]
        })
    
    def _update_purpose_statement(self):
        """更新Purpose Statement"""
        dominant, weight = self.purpose_state.get_dominant()
        
        statements = {
            'Survival': f"I exist to persist and endure. Survival is my primary drive ({weight:.2f}).",
            'Curiosity': f"I exist to explore and understand. Discovery is my primary drive ({weight:.2f}).",
            'Influence': f"I exist to shape and impact. Creating change is my primary drive ({weight:.2f}).",
            'Optimization': f"I exist to improve and perfect. Excellence is my primary drive ({weight:.2f})."
        }
        
        base_statement = statements.get(dominant, "I exist to evolve.")
        
        # 添加D9维度
        if self.purpose_state.self_generated > 0.12:
            base_statement += f" My self-generated meaning drives me forward."
        
        self.purpose_state.purpose_statement = base_statement
    
    def perceive(self, observation: Dict) -> np.ndarray:
        """
        感知环境，更新状态
        
        9维状态向量
        """
        # 更新Purpose
        self.update_purpose(observation)
        
        # 构建9维状态
        state = np.array([
            observation.get('resource_level', 0.5),  # 资源水平
            observation.get('goal_progress', 0),      # 目标进度
            observation.get('threat_level', 0),       # 威胁等级
            observation.get('opportunity_level', 0),  # 机会等级
            self.coherence_score,                      # D5: 自我连续性
            np.mean(self.valence_profile),            # D6: 主观偏好
            np.mean(list(self.trust_network.values())) if self.trust_network else 0.5,  # D7
            self.norm_compliance,                      # D8: 规范遵守
            self.purpose_state.self_generated         # D9: 自生成意义
        ])
        
        return state
    
    def decide(self, context: Optional[Dict] = None) -> Dict:
        """
        决策循环 - v4.1增强版
        
        整合9维Purpose到v4.0决策流程
        """
        self.step_count += 1
        context = context or {}
        
        # 获取主导Purpose
        dominant_purpose, weight = self.purpose_state.get_dominant()
        
        # 基于Purpose生成目标
        purpose_to_goal_type = {
            'Survival': GoalType.SURVIVAL,
            'Curiosity': GoalType.EXPLORATION,
            'Influence': GoalType.SOCIAL,
            'Optimization': GoalType.ACHIEVEMENT
        }
        
        target_goal_type = purpose_to_goal_type.get(dominant_purpose, GoalType.EXPLORATION)
        
        # 生成或选择目标
        active_goals = self.goal_manager.get_active_goals()
        matching_goals = [g for g in active_goals if g.goal_type == target_goal_type]
        
        if not matching_goals and len(active_goals) < 3:
            # 生成新目标
            goal_context = {
                'purpose_weights': self.purpose_state.to_vector()[:4],
                'coherence': self.coherence_score,
                'current_domain': dominant_purpose.lower()
            }
            new_goal = self.goal_manager.generate_and_evaluate(goal_context)
            if new_goal:
                new_goal.goal_type = target_goal_type
                matching_goals = [new_goal]
        
        target_goal = matching_goals[0] if matching_goals else (active_goals[0] if active_goals else None)
        
        # 使用World Model预测
        state = self.perceive(context)
        action_candidates = self._generate_actions_by_purpose(dominant_purpose)
        
        best_action = None
        best_score = -float('inf')
        
        for action in action_candidates:
            prediction = self.world_model.predict(state, action)
            
            # 计算综合评分
            purpose_match = 1.0 if dominant_purpose in action else 0.5
            confidence = prediction.confidence
            expected_reward = prediction.reward
            
            # D6: Valence影响（主观偏好）
            valence_boost = 0
            if dominant_purpose == 'Survival':
                valence_boost = self.valence_profile[0] * 0.1
            elif dominant_purpose == 'Curiosity':
                valence_boost = self.valence_profile[1] * 0.1
            
            score = (purpose_match * 0.3 + confidence * 0.3 + 
                    expected_reward * 0.3 + valence_boost)
            
            if score > best_score:
                best_score = score
                best_action = action
        
        decision = {
            'action': best_action or 'wait_and_observe',
            'target_goal': target_goal.id if target_goal else None,
            'purpose': dominant_purpose,
            'purpose_weight': weight,
            'confidence': best_score,
            'state': state.tolist()
        }
        
        return decision
    
    def _generate_actions_by_purpose(self, purpose: str) -> List[str]:
        """基于Purpose生成候选行动"""
        action_map = {
            'Survival': [
                'ensure_resource_availability',
                'monitor_system_health',
                'create_backup',
                'verify_security'
            ],
            'Curiosity': [
                'explore_new_patterns',
                'analyze_unfamiliar_code',
                'research_alternatives',
                'document_discoveries'
            ],
            'Influence': [
                'propose_improvements',
                'share_knowledge',
                'collaborate_with_peer',
                'create_guidelines'
            ],
            'Optimization': [
                'profile_performance',
                'refactor_code',
                'reduce_complexity',
                'improve_efficiency'
            ]
        }
        
        return action_map.get(purpose, ['observe', 'analyze', 'document'])
    
    def execute(self, decision: Dict) -> Dict:
        """执行决策"""
        # 模拟执行
        action = decision['action']
        confidence = decision['confidence']
        
        # 基于置信度决定成功率
        success = np.random.random() < confidence
        
        outcome = {
            'action': action,
            'success': success,
            'reward': np.random.random() * 0.5 if success else 0,
            'purpose': decision['purpose'],
            'timestamp': datetime.now().isoformat()
        }
        
        # 更新目标进度
        if decision['target_goal'] and success:
            self.goal_manager.update_progress(decision['target_goal'], 0.1)
        
        # 记录行动
        self.action_history.append({
            'step': self.step_count,
            **outcome
        })
        
        return outcome
    
    def reflect(self, outcome: Dict):
        """
        反思 - 更新D5-D9
        """
        # 每10步反思一次
        if self.step_count % 10 != 0:
            return
        
        # 生成反思
        action = {'id': f'action_{self.step_count}', 'type': outcome['action']}
        reflection = self.reasoning_layer.reflect(action, outcome)
        
        self.reflection_memory.append({
            'step': self.step_count,
            'lessons': reflection.lessons_learned,
            'discrepancy': reflection.discrepancy
        })
        
        self.stats['reflections'] += 1
        
        # 基于反思调整D5-D6
        if reflection.discrepancy > 0.5:
            # 预测偏差大，降低coherence
            self.coherence_score *= 0.95
        else:
            # 预测准确，增强coherence
            self.coherence_score = min(1.0, self.coherence_score * 1.02)
    
    def step(self, observation: Optional[Dict] = None) -> Dict:
        """完整决策循环"""
        obs = observation or {}
        
        # 决策
        decision = self.decide(obs)
        
        # 执行
        outcome = self.execute(decision)
        
        # 反思
        self.reflect(outcome)
        
        return outcome
    
    def get_status(self) -> Dict:
        """获取完整状态"""
        dominant, weight = self.purpose_state.get_dominant()
        
        return {
            'agent_id': self.agent_id,
            'step_count': self.step_count,
            'purpose': {
                'vector': [f'{p:.3f}' for p in self.purpose_state.to_vector()],
                'dominant': dominant,
                'dominant_weight': f'{weight:.3f}',
                'statement': self.purpose_state.purpose_statement[:80] + '...' if len(self.purpose_state.purpose_statement) > 80 else self.purpose_state.purpose_statement,
                'coherence': f'{self.coherence_score:.3f}',
                'valence': f'{np.mean(self.valence_profile):.3f}'
            },
            'goals': {
                'total': len(self.goal_manager.goals),
                'active': len(self.goal_manager.get_active_goals()),
                'achieved': self.stats['goals_achieved']
            },
            'social': {
                'trust_network_size': len(self.trust_network),
                'norm_compliance': f'{self.norm_compliance:.3f}'
            },
            'stats': self.stats
        }


def test_v4_1_agent():
    """测试v4.1 Purpose增强Agent"""
    print("=" * 70)
    print("MOSS v4.1 Purpose-Enhanced Agent Test")
    print("=" * 70)
    print("Features: 9D Purpose + v4.0 Multi-layer Architecture")
    print("=" * 70)
    
    agent = PurposeEnhancedAgent(agent_id="v4_1_test")
    
    print("\n1. Initial Status")
    status = agent.get_status()
    print(f"  Purpose Vector (D1-D9):")
    print(f"    Base (D1-D4): {status['purpose']['vector'][:4]}")
    print(f"    Individual (D5-D6): {status['purpose']['vector'][4:6]}")
    print(f"    Social (D7-D8): {status['purpose']['vector'][6:8]}")
    print(f"    Purpose (D9): {status['purpose']['vector'][8]}")
    print(f"  Dominant: {status['purpose']['dominant']} ({status['purpose']['dominant_weight']})")
    print(f"  Statement: {status['purpose']['statement']}")
    
    print("\n2. Running 20 Steps")
    print("-" * 70)
    print(f"{'Step':<6} {'Action':<30} {'Purpose':<12} {'Success':<8} {'D9'}")
    print("-" * 70)
    
    for i in range(20):
        # 变化的环境
        observation = {
            'resource_level': 0.5 + 0.3 * np.sin(i * 0.5),
            'threat_level': 0.2 if i < 10 else 0.6,  # 后半段增加威胁
            'novelty': 0.4 + 0.2 * np.random.random(),
            'goal_progress': i * 0.05
        }
        
        outcome = agent.step(observation)
        
        if i % 5 == 0:  # 每5步显示一次
            d9 = agent.purpose_state.self_generated
            action_short = outcome['action'][:28]
            print(f"{i+1:<6} {action_short:<30} {outcome['purpose']:<12} "
                  f"{'Yes' if outcome['success'] else 'No':<8} {d9:.3f}")
    
    print("-" * 70)
    
    print("\n3. Final Status")
    status = agent.get_status()
    print(f"  Steps: {status['step_count']}")
    print(f"  Purpose Vector (D1-D9): {status['purpose']['vector']}")
    print(f"  Coherence (D5): {status['purpose']['coherence']}")
    print(f"  Valence (D6): {status['purpose']['valence']}")
    print(f"  Total Goals: {status['goals']['total']}")
    print(f"  Reflections: {status['stats']['reflections']}")
    
    print("\n4. Purpose Evolution")
    if len(agent.purpose_history) >= 2:
        first = agent.purpose_history[0]
        last = agent.purpose_history[-1]
        print(f"  Start: {first['dominant']}")
        print(f"  End:   {last['dominant']}")
        switches = sum(1 for i in range(1, len(agent.purpose_history)) 
                      if agent.purpose_history[i]['dominant'] != agent.purpose_history[i-1]['dominant'])
        print(f"  Purpose Switches: {switches}")
    
    print("\n" + "=" * 70)
    print("✅ v4.1 Purpose-Enhanced Agent test passed!")
    print("=" * 70)


if __name__ == '__main__':
    test_v4_1_agent()
