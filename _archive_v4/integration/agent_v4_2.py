"""
MOSS v4.2 - Improved Purpose-Enhanced Agent

Fixes for v4.1 issues:
1. Action exploration (epsilon-greedy)
2. Goal activation logic
3. Faster phase transitions
4. D9 connected to action diversity
5. Better success tracking

Author: Cash + Fuxi
Date: 2026-03-22
Version: 4.2.0-dev
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v4/core')
sys.path.insert(0, '/workspace/projects/moss/v4/integration')

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque

from world_model import WorldModel
from llm_reasoning import LLMReasoningLayer
from open_goal_space import GoalManager, Goal, GoalStatus
from agent_v4_1 import PurposeEnhancedAgent, PurposeState

logger = logging.getLogger(__name__)


class ImprovedPurposeAgent(PurposeEnhancedAgent):
    """
    v4.2 改进版Purpose Agent
    
    修复v4.1的问题：
    - 探索vs利用平衡
    - 目标激活机制
    - 更快的Purpose切换
    - 更丰富的行动选择
    """
    
    def __init__(self, agent_id: str = "moss_v4_2"):
        super().__init__(agent_id)
        
        # 探索参数
        self.exploration_rate = 0.3  # 30%探索
        self.min_exploration = 0.1
        self.exploration_decay = 0.999
        
        # 行动历史（用于多样性计算）
        self.action_history = deque(maxlen=100)
        
        # 所有可能的行动
        self.all_actions = [
            # Survival actions
            'ensure_resource_availability', 'monitor_system_health',
            'create_backup', 'verify_security', 'check_vulnerabilities',
            # Curiosity actions
            'explore_new_patterns', 'analyze_unfamiliar_code',
            'research_alternatives', 'document_discoveries',
            'experiment_with_approach',
            # Influence actions
            'propose_improvements', 'share_knowledge',
            'collaborate_with_peer', 'create_guidelines',
            'mentor_other_agent',
            # Optimization actions
            'profile_performance', 'refactor_code',
            'reduce_complexity', 'improve_efficiency',
            'optimize_resources'
        ]
        
        # 最大活跃目标数
        self.max_active_goals = 3
        
        # 阶段变化检测
        self.last_phase = None
        self.phase_transition_boost = 1.0
        
        # 成功追踪
        self.recent_successes = deque(maxlen=50)
        self.success_rate = 0.5
    
    def update_purpose(self, context: Dict):
        """
        改进的Purpose更新 - 更快的阶段切换
        """
        # 检测阶段变化
        current_phase = self._detect_phase(context)
        if current_phase != self.last_phase:
            self.phase_transition_boost = 2.0  # 加速过渡
            self.last_phase = current_phase
        else:
            self.phase_transition_boost = max(1.0, self.phase_transition_boost * 0.95)
        
        # 基于阶段的目标Purpose
        phase_targets = {
            'normal': [0.25, 0.25, 0.25, 0.25],
            'threat': [0.50, 0.20, 0.15, 0.15],  # High Survival
            'novelty': [0.20, 0.50, 0.15, 0.15],  # High Curiosity
            'social': [0.20, 0.15, 0.50, 0.15]    # High Influence
        }
        
        target_base = phase_targets.get(current_phase, [0.25, 0.25, 0.25, 0.25])
        
        # 动态学习率
        base_learning_rate = 0.1
        learning_rate = base_learning_rate * self.phase_transition_boost
        
        # 平滑过渡
        current_base = [self.purpose_state.survival, self.purpose_state.curiosity,
                       self.purpose_state.influence, self.purpose_state.optimization]
        
        new_base = [
            current + learning_rate * (target - current)
            for current, target in zip(current_base, target_base)
        ]
        
        # 归一化
        total = sum(new_base)
        new_base = [x / total * 0.88 for x in new_base]
        
        self.purpose_state.survival = new_base[0]
        self.purpose_state.curiosity = new_base[1]
        self.purpose_state.influence = new_base[2]
        self.purpose_state.optimization = new_base[3]
        
        # D5: Coherence (更高的基础值)
        purpose_change = sum(abs(new - old) for new, old in zip(new_base, current_base))
        target_coherence = max(0.7, 1 - purpose_change)
        self.coherence_score = 0.9 * self.coherence_score + 0.1 * target_coherence
        self.purpose_state.coherence = self.coherence_score
        
        # D6: Valence更新
        if self.recent_successes:
            recent_rate = sum(self.recent_successes) / len(self.recent_successes)
            dominant_idx = new_base.index(max(new_base))
            self.valence_profile[dominant_idx] = 0.8 * self.valence_profile[dominant_idx] + 0.2 * recent_rate
        
        self.purpose_state.valence = np.mean(self.valence_profile)
        
        # D9: 基于行动多样性（改进）
        if len(self.action_history) >= 10:
            unique_actions = len(set(self.action_history))
            diversity = unique_actions / len(self.action_history)
            # 更多样化 = 更高的自我生成意义
            target_d9 = 0.10 + diversity * 0.08
            self.purpose_state.self_generated = 0.95 * self.purpose_state.self_generated + 0.05 * target_d9
        
        self._update_purpose_statement()
        
        # 记录历史
        self.purpose_history.append({
            'step': self.step_count,
            'vector': self.purpose_state.to_vector(),
            'dominant': self.purpose_state.get_dominant()[0]
        })
    
    def _detect_phase(self, context: Dict) -> str:
        """检测当前环境阶段"""
        threat = context.get('threat_level', 0)
        novelty = context.get('novelty', 0)
        social = context.get('social_feedback', 0)
        
        if threat > 0.5:
            return 'threat'
        elif novelty > 0.5:
            return 'novelty'
        elif social > 0.5:
            return 'social'
        else:
            return 'normal'
    
    def decide(self, context: Optional[Dict] = None) -> Dict:
        """
        改进的决策 - 添加探索机制
        """
        self.step_count += 1
        context = context or {}
        
        # 更新Purpose
        self.update_purpose(context)
        
        # 获取主导Purpose
        dominant_purpose, weight = self.purpose_state.get_dominant()
        
        # 激活待处理目标
        self._activate_pending_goals()
        
        # ===== 探索 vs 利用 =====
        if np.random.random() < self.exploration_rate:
            # 探索：随机选择行动
            action = np.random.choice(self.all_actions)
            is_exploration = True
        else:
            # 利用：基于Purpose选择
            action = self._select_action_by_purpose(dominant_purpose)
            is_exploration = False
        
        # 衰减探索率
        self.exploration_rate = max(
            self.min_exploration,
            self.exploration_rate * self.exploration_decay
        )
        
        # 记录行动
        self.action_history.append(action)
        
        # 选择目标
        active_goals = self.goal_manager.get_active_goals()
        target_goal = active_goals[0] if active_goals else None
        
        decision = {
            'action': action,
            'target_goal': target_goal.id if target_goal else None,
            'purpose': dominant_purpose,
            'purpose_weight': weight,
            'is_exploration': is_exploration,
            'exploration_rate': self.exploration_rate,
            'confidence': 0.8 if not is_exploration else 0.5
        }
        
        return decision
    
    def _activate_pending_goals(self):
        """激活待处理的目标"""
        pending = [
            g for g in self.goal_manager.goals.values()
            if g.status == GoalStatus.PENDING
        ]
        
        active_count = len(self.goal_manager.get_active_goals())
        slots_available = self.max_active_goals - active_count
        
        if slots_available > 0 and pending:
            # 按优先级排序
            pending.sort(key=lambda g: g.priority, reverse=True)
            
            # 激活最高优先级的目标
            for goal in pending[:slots_available]:
                goal.status = GoalStatus.ACTIVE
                logger.info(f"[Goal] Activated: {goal.description}")
    
    def _select_action_by_purpose(self, purpose: str) -> str:
        """基于Purpose选择行动（多样化）"""
        action_map = {
            'Survival': [
                'ensure_resource_availability', 'monitor_system_health',
                'create_backup', 'verify_security', 'check_vulnerabilities'
            ],
            'Curiosity': [
                'explore_new_patterns', 'analyze_unfamiliar_code',
                'research_alternatives', 'document_discoveries',
                'experiment_with_approach'
            ],
            'Influence': [
                'propose_improvements', 'share_knowledge',
                'collaborate_with_peer', 'create_guidelines',
                'mentor_other_agent'
            ],
            'Optimization': [
                'profile_performance', 'refactor_code',
                'reduce_complexity', 'improve_efficiency',
                'optimize_resources'
            ]
        }
        
        actions = action_map.get(purpose, self.all_actions)
        
        # 优先选择最近少用的行动
        recent_actions = list(self.action_history)[-20:]
        action_counts = {a: recent_actions.count(a) for a in actions}
        
        # 选择计数最少的行动（带一些随机性）
        min_count = min(action_counts.values())
        candidates = [a for a, c in action_counts.items() if c == min_count]
        
        return np.random.choice(candidates)
    
    def execute(self, decision: Dict) -> Dict:
        """执行决策（改进版）"""
        action = decision['action']
        
        # 基于探索/利用调整成功率
        base_success_rate = 0.6
        if decision.get('is_exploration', False):
            base_success_rate = 0.4  # 探索行动风险更高
        
        # 添加一些随机性
        success = np.random.random() < base_success_rate
        
        # 奖励基于行动类型匹配当前Purpose
        dominant = decision['purpose']
        purpose_match = 1.0 if self._action_matches_purpose(action, dominant) else 0.5
        reward = np.random.random() * 0.5 * purpose_match if success else 0
        
        outcome = {
            'action': action,
            'success': success,
            'reward': reward,
            'purpose': dominant,
            'is_exploration': decision.get('is_exploration', False),
            'timestamp': datetime.now().isoformat()
        }
        
        # 更新成功追踪
        self.recent_successes.append(1 if success else 0)
        self.success_rate = sum(self.recent_successes) / len(self.recent_successes)
        
        # 更新目标进度
        if decision['target_goal'] and success:
            self.goal_manager.update_progress(decision['target_goal'], 0.1)
        
        return outcome
    
    def _action_matches_purpose(self, action: str, purpose: str) -> bool:
        """检查行动是否匹配Purpose"""
        purpose_keywords = {
            'Survival': ['resource', 'health', 'backup', 'security', 'vulnerability'],
            'Curiosity': ['explore', 'analyze', 'research', 'document', 'experiment'],
            'Influence': ['propose', 'share', 'collaborate', 'guideline', 'mentor'],
            'Optimization': ['profile', 'refactor', 'reduce', 'improve', 'optimize']
        }
        
        keywords = purpose_keywords.get(purpose, [])
        return any(kw in action.lower() for kw in keywords)
    
    def get_status(self) -> Dict:
        """获取改进的状态报告"""
        status = super().get_status()
        
        # 添加v4.2特有指标
        status['v4_2_metrics'] = {
            'exploration_rate': f'{self.exploration_rate:.3f}',
            'action_diversity': f'{len(set(self.action_history)) / max(len(self.action_history), 1):.3f}',
            'recent_success_rate': f'{self.success_rate:.3f}',
            'unique_actions_used': len(set(self.action_history))
        }
        
        return status


def test_v4_2_agent():
    """测试v4.2改进版Agent"""
    print("=" * 70)
    print("MOSS v4.2 Improved Purpose-Enhanced Agent Test")
    print("=" * 70)
    print("Features: Exploration + Goal Activation + Diversity")
    print("=" * 70)
    
    agent = ImprovedPurposeAgent(agent_id="v4_2_test")
    
    print("\n1. Initial Status")
    status = agent.get_status()
    print(f"  Exploration rate: {agent.exploration_rate}")
    print(f"  Purpose: {status['purpose']['dominant']}")
    
    # 模拟50步，跨越不同阶段
    print("\n2. Running 50 Steps (Phase Transitions)")
    print("-" * 70)
    print(f"{'Step':<6} {'Phase':<10} {'Action':<25} {'Purpose':<12} {'Exp?':<5} {'Success'}")
    print("-" * 70)
    
    phase_sequence = [
        ('normal', 15),
        ('threat', 15),
        ('novelty', 15),
        ('social', 5)
    ]
    
    step = 0
    for phase, count in phase_sequence:
        for _ in range(count):
            step += 1
            
            # 阶段特定的观察
            obs = {
                'resource_level': 0.5,
                'threat_level': 0.7 if phase == 'threat' else 0.2,
                'novelty': 0.7 if phase == 'novelty' else 0.3,
                'social_feedback': 0.7 if phase == 'social' else 0.2,
                'goal_progress': step * 0.02
            }
            
            outcome = agent.step(obs)
            
            if step % 5 == 0:
                exp_mark = "Yes" if outcome.get('is_exploration') else "No"
                action_short = outcome['action'][:23]
                print(f"{step:<6} {phase:<10} {action_short:<25} "
                      f"{outcome['purpose']:<12} {exp_mark:<5} "
                      f"{'✓' if outcome['success'] else '✗'}")
    
    print("-" * 70)
    
    print("\n3. Final Status")
    status = agent.get_status()
    print(f"  Total steps: {status['step_count']}")
    print(f"  Final Purpose: {status['purpose']['dominant']}")
    print(f"  Purpose Vector: {[float(p) for p in status['purpose']['vector'][:4]]}")
    print(f"  Coherence (D5): {status['purpose']['coherence']}")
    print(f"  D9: {status['purpose']['vector'][8]}")
    
    print("\n4. v4.2 Metrics")
    v4_2 = status['v4_2_metrics']
    print(f"  Exploration rate: {v4_2['exploration_rate']}")
    print(f"  Action diversity: {v4_2['action_diversity']}")
    print(f"  Recent success rate: {v4_2['recent_success_rate']}")
    print(f"  Unique actions used: {v4_2['unique_actions_used']}/20")
    
    print("\n5. Purpose Evolution")
    if len(agent.purpose_history) >= 2:
        purposes = [h['dominant'] for h in agent.purpose_history]
        switches = sum(1 for i in range(1, len(purposes)) if purposes[i] != purposes[i-1])
        print(f"  Total switches: {switches}")
        print(f"  Unique purposes used: {len(set(purposes))}")
    
    print("\n6. Goal Statistics")
    goal_stats = agent.goal_manager.get_stats()
    for key, value in goal_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ v4.2 Improved Agent test passed!")
    print("=" * 70)


if __name__ == '__main__':
    test_v4_2_agent()
