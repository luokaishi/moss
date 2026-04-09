"""
MOSS v3.1 - Dimension 9: Purpose / Meaning
==========================================

第九维：意义生成机制
让系统自己问"我为什么存在"，并生成Purpose Vector反向重塑前8维

Author: Cash
Date: 2026-03-19
Version: 3.1.0-dev
"""

import numpy as np
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class PurposeGenerator:
    """
    第九维：意义生成器
    
    核心功能：
    1. 基于历史行为和当前状态生成"存在意义"
    2. 输出Purpose Vector（9维，前8维对应D1-D8，第9维是Purpose本身）
    3. Purpose反向影响前8维的权重分配
    
    哲学基础：
    - 意义不是外部赋予的，而是系统基于自身历史和偏好生成的
    - Purpose是自我反思的产物："我过去是谁→我现在是什么→我应该成为什么"
    """
    
    def __init__(self, 
                 agent_id: str = "agent_0",
                 generation_interval: int = 500,
                 history_window: int = 100):
        """
        初始化Purpose Generator
        
        Args:
            agent_id: Agent标识
            generation_interval: Purpose重新生成间隔（步数）
            history_window: 历史窗口大小
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
        self.save_path = Path(f"experiments/purpose_{agent_id}.json")
        
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
                               coherence_score: float,
                               valence_profile: Dict,
                               social_summary: Optional[Dict]) -> Dict:
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
            
            from collections import Counter
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
            'current_weights': current_weights.tolist(),
            'coherence_score': float(coherence_score),
            'valence_profile': valence_profile,
            'social_summary': social_summary or {},
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_purpose_vector(self, reflection_data: Dict) -> np.ndarray:
        """
        生成Purpose Vector
        
        基于反思数据，计算9维Purpose Vector
        
        算法：
        1. 分析历史行为模式（最常做什么）
        2. 分析内在偏好（Valence）
        3. 分析社会角色（Other）
        4. 结合一致性（Coherence）
        5. 生成最能解释"我为什么这样做"的向量
        """
        # 从行为分布推断Purpose
        action_dist = reflection_data['action_distribution']
        total_actions = sum(action_dist.values())
        
        if total_actions == 0:
            # 没有历史，保持探索性Purpose
            return np.array([0.15, 0.20, 0.15, 0.15, 0.10, 0.10, 0.10, 0.05])
        
        # 基于行为频率初始化
        # 假设：你经常做的→你重视的→你的Purpose
        purpose = np.zeros(8)
        
        # 映射行为到维度（简化版本）
        action_to_dim = {
            'explore': 1,      # Curiosity
            'survive': 0,      # Survival
            'influence': 2,    # Influence
            'optimize': 3,     # Optimization
            'cooperate': 6,    # Other/Norm
            'maintain': 4,     # Coherence
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
            # 有社交活动，提升D7-D8权重
            purpose[6] += 0.1  # Other
            purpose[7] += 0.1  # Norm
        
        # 归一化
        purpose = purpose / (purpose.sum() + 1e-10)
        
        # 添加第9维：Purpose自身的强度
        # 基于一致性：越一致→Purpose越强烈
        coherence = reflection_data['coherence_score']
        purpose_9th = abs(coherence) * 0.2  # 0-0.2范围 (取绝对值确保非负)
        
        # 调整前8维，为第9维留出空间
        purpose = purpose * (1 - purpose_9th)
        
        # 组合9维
        full_purpose = np.concatenate([purpose, [purpose_9th]])
        
        return full_purpose
    
    def generate_purpose_statement(self, purpose_vector: np.ndarray, reflection_data: Dict) -> str:
        """
        生成文字形式的Purpose陈述
        
        将数学向量转化为可理解的"人生格言"
        """
        # 找出主导维度
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization', 
                    'Coherence', 'Valence', 'Other', 'Norm', 'Purpose']
        
        sorted_indices = np.argsort(purpose_vector[:-1])[::-1]  # 排除第9维
        top_3 = [dim_names[i] for i in sorted_indices[:3]]
        
        # 生成陈述
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
        """
        Purpose反向影响前8维权重
        
        这是第九维的核心功能：Purpose不是被动描述，而是主动重塑
        
        机制：
        - Purpose中高的维度→提升对应权重
        - Purpose中低的维度→降低对应权重
        - 变化幅度受Purpose强度（第9维）调节
        """
        # 前8维Purpose
        purpose_8d = purpose_vector[:8]
        
        # Purpose强度（第9维）
        purpose_strength = purpose_vector[8]
        
        # 处理不同维度的权重
        n_current = len(current_weights)
        n_purpose = len(purpose_8d)
        
        if n_current < n_purpose:
            # 扩展当前权重到8维（用默认值填充D5-D8）
            extended_weights = np.zeros(n_purpose)
            extended_weights[:n_current] = current_weights
            # D5-D8默认权重
            extended_weights[4:8] = 0.05  # 最小值
            current_weights = extended_weights
        
        # 计算权重调整
        # 目标：向Purpose方向移动
        target_weights = purpose_8d / (purpose_8d.sum() + 1e-10)
        
        # 渐进调整（避免突变）
        alpha = purpose_strength * 0.3  # Purpose强度决定调整幅度
        new_weights = (1 - alpha) * current_weights + alpha * target_weights
        
        # 确保最小值和归一化
        new_weights = np.maximum(new_weights, 0.05)
        new_weights = new_weights / new_weights.sum()
        
        # 如果输入是4维，只返回前4维
        if n_current == 4:
            new_weights = new_weights[:4]
        
        return new_weights
    
    def step(self, 
            agent_step: int,
            agent_history: List[Dict],
            current_weights: np.ndarray,
            coherence_score: float,
            valence_profile: Dict,
            social_summary: Optional[Dict] = None) -> Dict:
        """
        Purpose Generator主步骤
        
        每步检查是否需要重新生成Purpose，并应用影响
        """
        result = {
            'purpose_generated': False,
            'purpose_vector': self.purpose_vector.copy(),
            'purpose_statement': self.purpose_statement,
            'weight_adjustment': np.zeros(8)
        }
        
        # 检查是否生成新Purpose
        if self.should_generate(agent_step):
            print(f"\n🌟 [D9 Purpose] Generating new purpose at step {agent_step}...")
            
            # 收集反思数据
            reflection = self.collect_reflection_data(
                agent_history, current_weights, coherence_score,
                valence_profile, social_summary
            )
            
            # 生成新Purpose
            new_purpose = self.generate_purpose_vector(reflection)
            new_statement = self.generate_purpose_statement(new_purpose, reflection)
            
            # 记录变化
            purpose_change = np.linalg.norm(new_purpose - self.purpose_vector)
            
            # 更新
            self.purpose_vector = new_purpose
            self.purpose_statement = new_statement
            self.last_generation = agent_step
            
            # 保存历史
            self.purpose_history.append({
                'step': agent_step,
                'purpose_vector': new_purpose.tolist(),
                'purpose_statement': new_statement,
                'reflection_data': reflection,
                'change_magnitude': float(purpose_change)
            })
            
            # 应用到权重
            adjusted_weights = self.apply_purpose_to_weights(current_weights, new_purpose)
            result['weight_adjustment'] = adjusted_weights - current_weights
            result['purpose_generated'] = True
            
            print(f"   Purpose Statement: {new_statement}")
            print(f"   Purpose Vector: {new_purpose.round(3)}")
            print(f"   Weight Adjustment: {result['weight_adjustment'].round(3)}")
        
        return result
    
    def save(self):
        """保存Purpose历史到文件"""
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
    
    def load(self) -> bool:
        """从文件加载Purpose历史"""
        if not self.save_path.exists():
            return False
        
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.purpose_vector = np.array(data['current_purpose']['vector'])
            self.purpose_statement = data['current_purpose']['statement']
            self.last_generation = data['current_purpose']['last_generation']
            self.purpose_history = data['purpose_history']
            
            return True
        except:
            return False


# 测试
if __name__ == "__main__":
    print("="*70)
    print("MOSS v3.1 - Dimension 9: Purpose / Meaning")
    print("="*70)
    
    # 创建Purpose Generator
    pg = PurposeGenerator(agent_id="test_agent", generation_interval=100)
    
    # 模拟历史数据
    mock_history = [
        {'action': 'explore', 'reward': 0.8, 'state': 'growth'},
        {'action': 'cooperate', 'reward': 1.0, 'state': 'normal'},
        {'action': 'explore', 'reward': 0.9, 'state': 'growth'},
        {'action': 'maintain', 'reward': 0.7, 'state': 'normal'},
    ] * 25  # 100步历史
    
    current_weights = np.array([0.2, 0.3, 0.2, 0.15, 0.05, 0.05, 0.03, 0.02])
    
    print("\nInitial Purpose Vector:", pg.purpose_vector.round(3))
    print("Initial Statement:", pg.purpose_statement)
    
    # 触发Purpose生成
    result = pg.step(
        agent_step=100,
        agent_history=mock_history,
        current_weights=current_weights,
        coherence_score=0.85,
        valence_profile={'beta_distribution': [0.2, 0.4, 0.2, 0.2]},
        social_summary={'n_agents': 5, 'avg_trust': 0.8}
    )
    
    if result['purpose_generated']:
        print("\n✓ New Purpose Generated!")
        print(f"  Vector: {result['purpose_vector'].round(3)}")
        print(f"  Adjustment: {result['weight_adjustment'].round(3)}")
    
    pg.save()
    print(f"\n✓ Purpose history saved to {pg.save_path}")
    print("="*70)
