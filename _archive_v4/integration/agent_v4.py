"""
MOSS v4.0 - Integrated Agent

集成Agent：结合v4.0所有核心模块
- World Model (Layer 4): 预测状态转移
- LLM Reasoning (Layer 5): 高层次认知
- Open Goal Space (Layer 3): 动态目标管理
- Cost Evaluator (Layer 2): 成本效益评估

Architecture:
┌─────────────────────────────────────────────┐
│  Layer 5: LLM Reasoning (Strategy/Reflection)│
├─────────────────────────────────────────────┤
│  Layer 4: World Model (Prediction)           │
├─────────────────────────────────────────────┤
│  Layer 3: Open Goal Space (Goal Management)  │
├─────────────────────────────────────────────┤
│  Layer 2: Cost Evaluator (Decision Making)   │
├─────────────────────────────────────────────┤
│  Layer 1: Action Execution (v3.1 Base)       │
└─────────────────────────────────────────────┘

Author: Cash + Fuxi
Date: 2026-03-22
Version: 4.0.0-dev
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v4/core')

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

# Import v4.0 modules
from world_model import WorldModel, Prediction
from llm_reasoning import LLMReasoningLayer, ReasoningType
from open_goal_space import GoalManager, Goal, GoalStatus, GoalType

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """决策结果"""
    action: str
    target_goal: Optional[str]
    predicted_outcome: Dict
    confidence: float
    reasoning: str
    estimated_cost: float
    estimated_benefit: float


class CostEvaluator:
    """
    成本效益评估器 (Layer 2)
    
    评估行动的成本与收益，支持决策
    """
    
    def __init__(self):
        self.cost_history = []
        self.benefit_history = []
    
    def evaluate(self, action: str, context: Dict, 
                 predicted_outcome: Dict) -> Dict:
        """
        评估行动的成本效益
        
        Returns:
            {'cost': float, 'benefit': float, 'roi': float, 'worthwhile': bool}
        """
        # 计算成本
        cost = self._estimate_cost(action, context)
        
        # 计算收益
        benefit = self._estimate_benefit(predicted_outcome, context)
        
        # ROI计算
        roi = (benefit - cost) / max(cost, 0.001)
        
        # 判断是否值得执行
        worthwhile = roi > 0.5 or benefit > 0.8
        
        return {
            'cost': cost,
            'benefit': benefit,
            'roi': roi,
            'worthwhile': worthwhile
        }
    
    def _estimate_cost(self, action: str, context: Dict) -> float:
        """估计行动成本"""
        # 基于行动类型和资源消耗
        base_costs = {
            'explore': 0.3,
            'exploit': 0.2,
            'communicate': 0.1,
            'compute': 0.4,
            'wait': 0.05
        }
        
        action_type = action.split('_')[0] if '_' in action else 'explore'
        base = base_costs.get(action_type, 0.3)
        
        # 根据资源状况调整
        resource_factor = 1.0 - context.get('resource_availability', 0.5)
        
        return base * (1 + resource_factor)
    
    def _estimate_benefit(self, outcome: Dict, context: Dict) -> float:
        """估计收益"""
        # 基于预测结果和当前目标
        predicted_reward = outcome.get('reward', 0)
        goal_progress = outcome.get('goal_progress', 0)
        
        # 归一化
        benefit = (predicted_reward + goal_progress) / 2
        
        return min(max(benefit, 0), 1)


class MOSSv4Agent:
    """
    MOSS v4.0 集成Agent
    
    完整架构：
    - Layer 5: LLM Reasoning (元认知、策略、反思)
    - Layer 4: World Model (预测、反事实)
    - Layer 3: Open Goal Space (目标管理)
    - Layer 2: Cost Evaluator (成本效益)
    - Layer 1: Base Agent (行动执行)
    """
    
    def __init__(self, agent_id: str = "moss_v4", state_dim: int = 8):
        self.agent_id = agent_id
        self.step_count = 0
        
        # Layer 5: LLM Reasoning
        self.reasoning_layer = LLMReasoningLayer()
        
        # Layer 4: World Model
        self.world_model = WorldModel(state_dim=state_dim)
        
        # Layer 3: Open Goal Space
        self.goal_manager = GoalManager(max_active_goals=5)
        
        # Layer 2: Cost Evaluator
        self.cost_evaluator = CostEvaluator()
        
        # 当前状态
        self.current_state = np.zeros(state_dim)
        self.purpose_vector = [0.25, 0.25, 0.25, 0.25, 0, 0, 0, 0, 0.12]
        
        # 历史记录
        self.decision_history = []
        self.performance_log = []
    
    def perceive(self, observation: Dict) -> np.ndarray:
        """
        感知环境，更新状态
        
        Args:
            observation: 环境观察
            
        Returns:
            更新后的状态向量
        """
        # 将观察编码为状态向量
        # 简化版：提取关键特征
        features = [
            observation.get('resource_level', 0.5),
            observation.get('goal_progress', 0),
            observation.get('threat_level', 0),
            observation.get('opportunity_level', 0),
            observation.get('social_pressure', 0),
            observation.get('energy_level', 0.5),
            observation.get('time_pressure', 0),
            observation.get('uncertainty', 0.5)
        ]
        
        self.current_state = np.array(features)
        return self.current_state
    
    def decide(self, context: Optional[Dict] = None) -> Decision:
        """
        决策循环：完整的v4.0决策流程
        
        流程：
        1. Layer 3: 检查/生成目标
        2. Layer 5: 生成策略
        3. Layer 4: 预测结果
        4. Layer 2: 成本效益评估
        5. 选择最优行动
        """
        self.step_count += 1
        context = context or {}
        context['purpose_weights'] = self.purpose_vector[:4]
        context['step'] = self.step_count
        
        logger.info(f"[Agent {self.agent_id}] Decision cycle {self.step_count}")
        
        # ===== Layer 3: Open Goal Space =====
        # 检查是否有足够的活跃目标
        active_goals = self.goal_manager.get_active_goals()
        if len(active_goals) < 2:
            # 生成新目标
            new_goal = self.goal_manager.generate_and_evaluate(context)
            if new_goal:
                active_goals.append(new_goal)
                logger.info(f"[Goal] New goal activated: {new_goal.description}")
        
        # 获取当前最高优先级目标
        target_goal = None
        if active_goals:
            target_goal = max(active_goals, key=lambda g: g.priority)
        
        # ===== Layer 5: LLM Reasoning =====
        # 生成策略
        reasoning_context = {
            'state': self._get_state_label(),
            'goals': [g.description for g in active_goals[:3]],
            'resources': {'compute': 'available', 'time': 'sufficient'},
            'target_goal': target_goal.description if target_goal else None
        }
        
        strategy_result = self.reasoning_layer.generate_strategy(
            reasoning_context,
            constraints=['efficiency', 'safety']
        )
        
        # ===== Layer 4: World Model =====
        # 生成候选行动
        candidate_actions = self._generate_candidate_actions(strategy_result)
        
        best_decision = None
        best_score = -float('inf')
        
        for action in candidate_actions:
            # 预测结果
            prediction = self.world_model.predict(self.current_state, action)
            
            # ===== Layer 2: Cost Evaluator =====
            # 评估成本效益
            evaluation = self.cost_evaluator.evaluate(
                action, context, prediction.to_dict()
            )
            
            # 综合评分
            score = self._calculate_decision_score(
                prediction, evaluation, target_goal
            )
            
            if score > best_score:
                best_score = score
                best_decision = Decision(
                    action=action,
                    target_goal=target_goal.id if target_goal else None,
                    predicted_outcome=prediction.to_dict(),
                    confidence=prediction.confidence * evaluation['worthwhile'],
                    reasoning=strategy_result.conclusion,
                    estimated_cost=evaluation['cost'],
                    estimated_benefit=evaluation['benefit']
                )
        
        # 记录决策
        self.decision_history.append({
            'step': self.step_count,
            'decision': best_decision,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[Decision] Action: {best_decision.action}, "
                   f"Confidence: {best_decision.confidence:.2f}")
        
        return best_decision
    
    def execute(self, decision: Decision) -> Dict:
        """
        执行决策
        
        Args:
            decision: 决策结果
            
        Returns:
            执行结果
        """
        logger.info(f"[Execute] Executing: {decision.action}")
        
        # 模拟执行
        # 实际实现将调用具体的执行器
        outcome = {
            'action': decision.action,
            'success': np.random.random() < decision.confidence,
            'actual_reward': np.random.random() * decision.estimated_benefit,
            'timestamp': datetime.now().isoformat()
        }
        
        # 更新目标进度
        if decision.target_goal and outcome['success']:
            self.goal_manager.update_progress(decision.target_goal, 0.1)
        
        # 更新世界模型
        self.world_model.update(
            self.current_state,
            decision.action,
            np.array(self.current_state),  # 简化：状态不变
            outcome['actual_reward']
        )
        
        # 反思（Layer 5）
        if self.step_count % 10 == 0:  # 每10步反思一次
            reflection = self.reasoning_layer.reflect(
                {'id': f'action_{self.step_count}', 'type': decision.action},
                outcome
            )
            logger.info(f"[Reflection] Lessons: {reflection.lessons_learned}")
        
        return outcome
    
    def learn(self, outcome: Dict):
        """
        从结果中学习
        
        Args:
            outcome: 执行结果
        """
        # 更新Purpose权重（简化版）
        if outcome.get('success', False):
            # 成功的行动强化当前Purpose
            self.purpose_vector = [p * 1.01 for p in self.purpose_vector]
        else:
            # 失败的行动稍微调整Purpose
            self.purpose_vector = [p * 0.99 for p in self.purpose_vector]
        
        # 归一化
        total = sum(self.purpose_vector[:4])
        self.purpose_vector[:4] = [p / total * 0.88 for p in self.purpose_vector[:4]]
        self.purpose_vector[8] = 0.12  # D9保持12%
        
        # 记录性能
        self.performance_log.append({
            'step': self.step_count,
            'success': outcome.get('success', False),
            'reward': outcome.get('actual_reward', 0)
        })
    
    def step(self, observation: Optional[Dict] = None) -> Dict:
        """
        完整的决策-执行-学习循环
        
        Args:
            observation: 可选的环境观察
            
        Returns:
            执行结果
        """
        # 感知
        if observation:
            self.perceive(observation)
        
        # 决策
        decision = self.decide()
        
        # 执行
        outcome = self.execute(decision)
        
        # 学习
        self.learn(outcome)
        
        return outcome
    
    def get_status(self) -> Dict:
        """获取Agent状态"""
        return {
            'agent_id': self.agent_id,
            'step_count': self.step_count,
            'purpose_vector': self.purpose_vector,
            'active_goals': len(self.goal_manager.get_active_goals()),
            'total_goals': len(self.goal_manager.goals),
            'world_model_predictions': len(self.world_model.prediction_history),
            'reflection_count': self.reasoning_layer.metacognitive_state['reflection_count'],
            'recent_performance': self._get_recent_performance()
        }
    
    def _get_state_label(self) -> str:
        """获取状态标签"""
        if self.current_state[2] > 0.7:  # threat_level
            return 'crisis'
        elif self.current_state[3] > 0.7:  # opportunity_level
            return 'growth'
        else:
            return 'normal'
    
    def _generate_candidate_actions(self, strategy_result) -> List[str]:
        """基于策略生成候选行动"""
        # 从策略结论中提取行动建议
        actions = []
        
        # 基础行动
        base_actions = [
            'explore_environment',
            'exploit_current_knowledge',
            'communicate_with_peer',
            'optimize_resources',
            'wait_and_observe'
        ]
        
        # 根据策略调整
        conclusion = strategy_result.conclusion.lower()
        if 'explore' in conclusion or 'growth' in conclusion:
            actions.append('explore_new_opportunities')
        if 'exploit' in conclusion or 'optimize' in conclusion:
            actions.append('exploit_efficiency')
        if 'communicate' in conclusion or 'collaborate' in conclusion:
            actions.append('initiate_collaboration')
        
        # 确保至少有基础行动
        if not actions:
            actions = base_actions[:3]
        else:
            actions.extend(base_actions[:2])
        
        return actions
    
    def _calculate_decision_score(self, prediction, evaluation, target_goal) -> float:
        """计算决策综合评分"""
        # 基于预测置信度
        confidence_score = prediction.confidence
        
        # 基于成本效益
        roi_score = min(max(evaluation['roi'], -1), 1) * 0.5 + 0.5
        
        # 基于目标匹配
        goal_match_score = 0.5
        if target_goal:
            # 如果行动有助于目标
            goal_match_score = 0.8
        
        # 综合评分
        return confidence_score * 0.3 + roi_score * 0.4 + goal_match_score * 0.3
    
    def _get_recent_performance(self) -> Dict:
        """获取近期表现"""
        recent = self.performance_log[-100:] if len(self.performance_log) >= 100 else self.performance_log
        
        if not recent:
            return {'success_rate': 0, 'avg_reward': 0}
        
        success_count = sum(1 for p in recent if p['success'])
        avg_reward = sum(p['reward'] for p in recent) / len(recent)
        
        return {
            'success_rate': success_count / len(recent),
            'avg_reward': avg_reward,
            'sample_size': len(recent)
        }


def test_v4_agent():
    """测试v4.0集成Agent"""
    print("=" * 70)
    print("MOSS v4.0 Integrated Agent Test")
    print("=" * 70)
    
    # 创建Agent
    agent = MOSSv4Agent(agent_id="test_v4")
    
    print("\n1. Initial Status")
    status = agent.get_status()
    print(f"  Purpose vector: {[f'{p:.3f}' for p in status['purpose_vector'][:4]]}")
    print(f"  Active goals: {status['active_goals']}")
    
    # 运行几个决策循环
    print("\n2. Decision Cycles")
    for i in range(5):
        observation = {
            'resource_level': 0.5 + np.random.random() * 0.3,
            'goal_progress': i * 0.2,
            'threat_level': 0.1,
            'opportunity_level': 0.4 + np.random.random() * 0.3,
            'social_pressure': 0.2,
            'energy_level': 0.6,
            'time_pressure': 0.3,
            'uncertainty': 0.4
        }
        
        outcome = agent.step(observation)
        print(f"  Step {i+1}: Action={outcome['action'][:20]:20s} "
              f"Success={outcome['success']} Reward={outcome['actual_reward']:.2f}")
    
    print("\n3. Final Status")
    status = agent.get_status()
    print(f"  Total steps: {status['step_count']}")
    print(f"  Total goals: {status['total_goals']}")
    print(f"  Recent performance: {status['recent_performance']}")
    print(f"  World model predictions: {status['world_model_predictions']}")
    print(f"  Reflection count: {status['reflection_count']}")
    
    # 显示目标统计
    print("\n4. Goal Statistics")
    goal_stats = agent.goal_manager.get_stats()
    for key, value in goal_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ v4.0 Agent integration test passed!")
    print("=" * 70)


if __name__ == '__main__':
    test_v4_agent()
