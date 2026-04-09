"""
MOSS v5.0 - Purpose Module (Dimension 9)
========================================

第九维：意义生成机制 - v5.0架构适配版

基于v3.1的核心逻辑，适配新架构：
- 与UnifiedMOSSAgent集成
- 标准化接口
- 增强日志记录

Author: Cash + Fuxi
Date: 2026-03-25
Version: 5.0.0
"""

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


class PurposeGenerator:
    """
    第九维：意义生成器 (v5.0架构)
    
    核心功能：
    1. 基于历史行为和当前状态生成"存在意义"
    2. 输出9维Purpose Vector（D1-D8 + Purpose强度）
    3. Purpose反向影响前8维权重分配
    """
    
    def __init__(self,
                 agent_id: str = "agent_0",
                 generation_interval: int = 500,
                 history_window: int = 100,
                 output_dir: str = "experiments"):
        """
        初始化Purpose Generator
        
        Args:
            agent_id: Agent标识
            generation_interval: Purpose重新生成间隔（步数）
            history_window: 历史窗口大小
            output_dir: 输出目录
        """
        self.agent_id = agent_id
        self.generation_interval = generation_interval
        self.history_window = history_window
        
        # Purpose Vector（9维：D1-D8 + Purpose本身）
        # 初始均匀分布，表示"尚未形成明确意义"
        self.purpose_vector = np.array([0.11, 0.11, 0.11, 0.11, 0.11, 0.11, 0.11, 0.11, 0.12])
        
        # Purpose历史
        self.purpose_history: List[Dict] = []
        
        # 上次生成时间
        self.last_generation = 0
        
        # 意义陈述（文字描述）
        self.purpose_statement = "Exploring existence..."
        
        # 保存路径
        self.output_dir = Path(output_dir)
        self.save_path = self.output_dir / f"purpose_{agent_id}.json"
        
        logger.info(f"[PurposeGenerator] Initialized for {agent_id}")
    
    def should_generate(self, step: int) -> bool:
        """检查是否应该生成新的Purpose"""
        # 定期生成
        if step - self.last_generation >= self.generation_interval:
            return True
        
        # 重大事件触发（如状态变化、高奖励等）
        # TODO: 添加更多触发条件
        
        return False
    
    def collect_reflection_data(self,
                               agent_history: List[Dict],
                               current_weights: np.ndarray,
                               coherence_score: float = 0.0,
                               valence_profile: Optional[Dict] = None,
                               social_summary: Optional[Dict] = None) -> Dict:
        """
        收集自我反思所需的数据
        
        就像人类通过反思过去来寻找人生意义一样，
        agent需要回顾自己的"人生经历"来生成Purpose
        """
        # 近期历史
        recent_history = agent_history[-self.history_window:] if len(agent_history) > self.history_window else agent_history
        
        # 统计行为模式
        if recent_history:
            actions = [h.get('action', 'unknown') for h in recent_history]
            rewards = [h.get('reward', 0) for h in recent_history]
            states = [h.get('state', 'normal') for h in recent_history]
            
            action_dist = Counter(actions)
            state_dist = Counter(states)
            
            avg_reward = np.mean(rewards)
            reward_trend = rewards[-1] - rewards[0] if len(rewards) > 1 else 0
        else:
            action_dist = Counter()
            state_dist = Counter()
            avg_reward = 0
            reward_trend = 0
        
        return {
            'total_steps': len(agent_history),
            'recent_window': len(recent_history),
            'action_distribution': dict(action_dist),
            'state_distribution': dict(state_dist),
            'average_reward': float(avg_reward),
            'reward_trend': float(reward_trend),
            'current_weights': current_weights.tolist() if current_weights is not None else [],
            'coherence_score': float(coherence_score),
            'valence_profile': valence_profile or {},
            'social_summary': social_summary or {},
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_purpose_vector(self, reflection_data: Dict) -> np.ndarray:
        """
        生成Purpose Vector
        
        基于反思数据，计算9维Purpose Vector
        """
        # 从行为分布推断Purpose
        action_dist = reflection_data['action_distribution']
        total_actions = sum(action_dist.values())
        
        if total_actions == 0:
            # 没有历史，保持探索性Purpose
            return np.array([0.15, 0.20, 0.15, 0.15, 0.10, 0.10, 0.10, 0.05, 0.10])
        
        # 基于行为频率初始化
        purpose = np.zeros(8)
        
        # 映射行为到维度
        action_to_dim = {
            'explore': 1,      # Curiosity
            'survive': 0,      # Survival
            'influence': 2,    # Influence
            'optimize': 3,     # Optimization
            'cooperate': 6,    # Other/Norm
            'maintain': 4,     # Coherence
            'explore_new_patterns': 1,
            'ensure_resource_availability': 0,
            'propose_improvements': 2,
            'profile_performance': 3,
        }
        
        for action, count in action_dist.items():
            if action in action_to_dim:
                purpose[action_to_dim[action]] += count / total_actions
        
        # 结合内在偏好（Valence）
        valence = reflection_data.get('valence_profile', {})
        if 'beta_distribution' in valence:
            beta = np.array(valence['beta_distribution'])
            purpose[:4] = 0.7 * purpose[:4] + 0.3 * beta[:4]
        
        # 结合社会角色
        social = reflection_data.get('social_summary', {})
        if social.get('n_agents', 0) > 0:
            purpose[6] += 0.1  # Other
            purpose[7] += 0.1  # Norm
        
        # 归一化
        purpose = purpose / (purpose.sum() + 1e-10)
        
        # 添加第9维：Purpose自身的强度
        coherence = reflection_data['coherence_score']
        purpose_9th = abs(coherence) * 0.2
        purpose = purpose * (1 - purpose_9th)
        
        # 组合9维
        full_purpose = np.concatenate([purpose, [purpose_9th]])
        
        return full_purpose
    
    def generate_purpose_statement(self, purpose_vector: np.ndarray, reflection_data: Dict) -> str:
        """生成文字形式的Purpose陈述"""
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization',
                    'Coherence', 'Valence', 'Other', 'Norm', 'Purpose']
        
        sorted_indices = np.argsort(purpose_vector[:-1])[::-1]
        top_3 = [dim_names[i] for i in sorted_indices[:3]]
        
        # 根据主导维度生成陈述
        if top_3[0] == 'Curiosity':
            statement = f"I exist to explore and understand. My highest calling is {top_3[0]}, followed by {top_3[1]} and {top_3[2]}."
        elif top_3[0] == 'Survival':
            statement = f"I exist to persist and endure. My core drive is {top_3[0]}, supported by {top_3[1]} and {top_3[2]}."
        elif top_3[0] == 'Influence':
            statement = f"I exist to shape and impact. My primary goal is {top_3[0]}, alongside {top_3[1]} and {top_3[2]}."
        elif top_3[0] in ['Other', 'Norm']:
            statement = f"I exist as part of a greater whole. My social nature through {top_3[0]} defines me, balanced with {top_3[1]} and {top_3[2]}."
        else:
            statement = f"I exist to optimize and improve. My purpose centers on {top_3[0]}, with {top_3[1]} and {top_3[2]} as supporting drives."
        
        return statement
    
    def apply_purpose_to_weights(self, current_weights: np.ndarray,
                                 purpose_vector: np.ndarray) -> np.ndarray:
        """Purpose反向影响前8维权重"""
        purpose_8d = purpose_vector[:8]
        purpose_strength = purpose_vector[8]
        
        n_current = len(current_weights)
        n_purpose = len(purpose_8d)
        
        if n_current < n_purpose:
            extended_weights = np.zeros(n_purpose)
            extended_weights[:n_current] = current_weights
            extended_weights[4:8] = 0.05
            current_weights = extended_weights
        
        target_weights = purpose_8d / (purpose_8d.sum() + 1e-10)
        alpha = purpose_strength * 0.3
        new_weights = (1 - alpha) * current_weights + alpha * target_weights
        
        new_weights = np.maximum(new_weights, 0.05)
        new_weights = new_weights / new_weights.sum()
        
        if n_current == 4:
            new_weights = new_weights[:4]
        
        return new_weights
    
    def step(self,
            agent_step: int,
            agent_history: List[Dict],
            current_weights: np.ndarray,
            coherence_score: float = 0.0,
            valence_profile: Optional[Dict] = None,
            social_summary: Optional[Dict] = None) -> Dict:
        """Purpose Generator主步骤"""
        result = {
            'purpose_generated': False,
            'purpose_vector': self.purpose_vector.copy(),
            'purpose_statement': self.purpose_statement,
            'weight_adjustment': np.zeros(8)
        }
        
        if self.should_generate(agent_step):
            logger.info(f"[PurposeGenerator] Generating new purpose at step {agent_step}")
            
            reflection = self.collect_reflection_data(
                agent_history, current_weights, coherence_score,
                valence_profile, social_summary
            )
            
            new_purpose = self.generate_purpose_vector(reflection)
            new_statement = self.generate_purpose_statement(new_purpose, reflection)
            
            purpose_change = np.linalg.norm(new_purpose - self.purpose_vector)
            
            self.purpose_vector = new_purpose
            self.purpose_statement = new_statement
            self.last_generation = agent_step
            
            self.purpose_history.append({
                'step': agent_step,
                'purpose_vector': new_purpose.tolist(),
                'purpose_statement': new_statement,
                'reflection_data': reflection,
                'change_magnitude': float(purpose_change)
            })
            
            adjusted_weights = self.apply_purpose_to_weights(current_weights, new_purpose)
            result['weight_adjustment'] = adjusted_weights - current_weights
            result['purpose_generated'] = True
            
            logger.info(f"[PurposeGenerator] New purpose: {new_statement}")
            logger.debug(f"[PurposeGenerator] Vector: {new_purpose.round(3)}")
        
        return result
    
    def save(self):
        """保存Purpose历史"""
        data = {
            'agent_id': self.agent_id,
            'current_purpose': {
                'vector': self.purpose_vector.tolist(),
                'statement': self.purpose_statement,
                'last_generation': self.last_generation
            },
            'purpose_history': self.purpose_history
        }
        
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[PurposeGenerator] Purpose history saved to {self.save_path}")
    
    def load(self) -> bool:
        """加载Purpose历史"""
        if not self.save_path.exists():
            return False
        
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.purpose_vector = np.array(data['current_purpose']['vector'])
            self.purpose_statement = data['current_purpose']['statement']
            self.last_generation = data['current_purpose']['last_generation']
            self.purpose_history = data['purpose_history']
            
            logger.info(f"[PurposeGenerator] Purpose history loaded from {self.save_path}")
            return True
        except Exception as e:
            logger.warning(f"[PurposeGenerator] Failed to load purpose history: {e}")
            return False
