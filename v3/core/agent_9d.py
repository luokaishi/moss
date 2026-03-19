"""
MOSS v3.1 - 9D Agent (D1-D8 + D9 Purpose)
=========================================

集成Purpose维度的完整Agent

Author: Cash
Date: 2026-03-19
Version: 3.1.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent_8d import MOSSv3Agent8D, MOSSv3State8D
from purpose import PurposeGenerator


@dataclass
class MOSSv3State9D(MOSSv3State8D):
    """MOSS v3.1 9维状态（继承8维 + Purpose）"""
    purpose: float = 0.0           # D9: Purpose强度
    purpose_statement: str = ""    # Purpose文字陈述
    
    def to_vector_9d(self) -> np.ndarray:
        """转换为9维向量"""
        base = self.to_vector()  # 8维
        return np.concatenate([base, [self.purpose]])


class MOSSv3Agent9D(MOSSv3Agent8D):
    """
    MOSS v3.1 Agent - 完整9维系统
    
    在8维基础上集成Purpose Generator（D9）
    """
    
    def __init__(self,
                 agent_id: str,
                 enable_purpose: bool = True,
                 purpose_interval: int = 500,
                 **kwargs):
        """
        初始化9维Agent
        
        Args:
            agent_id: Agent标识
            enable_purpose: 是否启用D9
            purpose_interval: Purpose重新生成间隔
            **kwargs: 传递给父类(8D)的参数
        """
        # 初始化8维父类
        super().__init__(agent_id=agent_id, **kwargs)
        
        self.enable_purpose = enable_purpose
        
        # 初始化Purpose Generator
        if enable_purpose:
            self.purpose_generator = PurposeGenerator(
                agent_id=agent_id,
                generation_interval=purpose_interval
            )
            # 尝试加载之前的Purpose历史
            self.purpose_generator.load()
        else:
            self.purpose_generator = None
        
        # 9维历史记录
        self.history_9d: List[MOSSv3State9D] = []
        
        # Purpose统计
        self.purpose_generation_count = 0
        
    def step(self, 
            observed_behaviors: Optional[Dict] = None,
            interaction: Optional[Dict] = None) -> Dict:
        """
        执行一步决策循环（9维）
        
        流程：
        1. 执行8维step
        2. 更新Purpose Generator
        3. 应用Purpose影响
        4. 构建9维状态
        """
        # 1. 执行8维step（继承）
        result_8d = super().step(observed_behaviors, interaction)
        
        # 2. 更新Purpose（如果启用）
        purpose_result = None
        if self.enable_purpose and self.purpose_generator:
            # 构建历史数据（简化版本）
            agent_history = [
                {
                    'action': result_8d.get('action', 'unknown'),
                    'reward': np.mean(result_8d['M'][:4]),  # 简化为平均reward
                    'state': result_8d['state']
                }
            ] * 10  # 模拟历史
            
            # 获取coherence和valence信息
            coherence_score = result_8d['M'][4]  # D5
            valence_profile = {
                'beta_distribution': self.valence_module.beta.tolist() 
                if self.valence_module else [0.25, 0.25, 0.25, 0.25]
            }
            
            social_summary = None
            if self.other_module:
                social_summary = {
                    'n_agents': len(self.other_module.other_models),
                    'avg_trust': np.mean([m.trust_score for m in self.other_module.other_models.values()])
                                if self.other_module.other_models else 0.0
                }
            
            # 调用Purpose Generator
            purpose_result = self.purpose_generator.step(
                agent_step=self.step_count,
                agent_history=agent_history,
                current_weights=self.weights.copy(),
                coherence_score=coherence_score,
                valence_profile=valence_profile,
                social_summary=social_summary
            )
            
            # 如果生成了新Purpose，应用影响
            if purpose_result['purpose_generated']:
                self.purpose_generation_count += 1
                
                # 应用Purpose到权重
                weight_adjustment = purpose_result['weight_adjustment']
                self.weights = self.weights + weight_adjustment
                self.weights = np.maximum(self.weights, 0.05)
                self.weights = self.weights / self.weights.sum()
                
                # 保存Purpose历史
                self.purpose_generator.save()
        
        # 3. 构建9维状态
        purpose_value = 0.0
        purpose_statement = ""
        
        if self.purpose_generator:
            purpose_value = self.purpose_generator.purpose_vector[8]  # D9值
            purpose_statement = self.purpose_generator.purpose_statement
        
        state_9d = MOSSv3State9D(
            survival=result_8d['M'][0],
            curiosity=result_8d['M'][1],
            influence=result_8d['M'][2],
            optimization=result_8d['M'][3],
            coherence=result_8d['M'][4],
            valence=result_8d['M'][5],
            other=result_8d['M'][6],
            norm=result_8d['M'][7],
            purpose=purpose_value,
            weights=self.weights.copy(),
            state_label=result_8d['state'],
            purpose_statement=purpose_statement
        )
        
        self.history_9d.append(state_9d)
        
        # 4. 返回9维结果
        result_9d = {
            **result_8d,
            'purpose': purpose_value,
            'purpose_statement': purpose_statement,
            'purpose_generated': purpose_result['purpose_generated'] if purpose_result else False,
            'purpose_vector': self.purpose_generator.purpose_vector.tolist() 
                            if self.purpose_generator else [0] * 9,
            'weights_after_purpose': self.weights.copy()
        }
        
        return result_9d
    
    def get_full_report_9d(self) -> Dict:
        """生成完整9维报告"""
        # 基础8维报告
        report_8d = self.get_full_report()
        
        # 添加9维信息
        report_9d = {
            **report_8d,
            'dimension': 9,
            'purpose': {
                'enabled': self.enable_purpose,
                'current_purpose_vector': self.purpose_generator.purpose_vector.tolist() 
                                        if self.purpose_generator else None,
                'current_statement': self.purpose_generator.purpose_statement 
                                   if self.purpose_generator else None,
                'generation_count': self.purpose_generation_count,
                'history_length': len(self.purpose_generator.purpose_history) 
                                if self.purpose_generator else 0
            }
        }
        
        return report_9d
    
    def get_purpose_summary(self) -> Dict:
        """获取Purpose摘要"""
        if not self.purpose_generator:
            return {'enabled': False}
        
        pg = self.purpose_generator
        
        # 分析Purpose历史变化
        if len(pg.purpose_history) > 1:
            first = np.array(pg.purpose_history[0]['purpose_vector'])
            last = np.array(pg.purpose_history[-1]['purpose_vector'])
            drift = np.linalg.norm(last - first)
        else:
            drift = 0.0
        
        # 找出主导维度
        purpose_8d = pg.purpose_vector[:8]
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization',
                    'Coherence', 'Valence', 'Other', 'Norm']
        top_idx = np.argmax(purpose_8d)
        
        return {
            'enabled': True,
            'dominant_dimension': dim_names[top_idx],
            'dominant_weight': float(purpose_8d[top_idx]),
            'purpose_strength': float(pg.purpose_vector[8]),
            'total_generations': len(pg.purpose_history),
            'purpose_drift': float(drift),
            'current_statement': pg.purpose_statement
        }


# 测试
if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - 9D Agent Test")
    print("="*70)
    
    np.random.seed(42)
    
    # 创建9维agent
    print("\nCreating 9D agent...")
    agent = MOSSv3Agent9D(
        agent_id="test_9d",
        enable_social=True,
        enable_purpose=True,
        purpose_interval=100  # 每100步生成Purpose（测试用）
    )
    
    print(f"✓ Agent created: {agent.agent_id}")
    print(f"✓ Dimensions: D1-D9 (Full)")
    print(f"✓ Purpose enabled: {agent.enable_purpose}")
    
    # 运行200步
    print(f"\nRunning 200 steps...")
    purpose_generations = []
    
    for i in range(200):
        result = agent.step()
        
        if result['purpose_generated']:
            purpose_generations.append({
                'step': i,
                'statement': result['purpose_statement'],
                'vector': result['purpose_vector']
            })
            print(f"\n🌟 Step {i}: Purpose Generated!")
            print(f"   Statement: {result['purpose_statement'][:80]}...")
            print(f"   Weights adjusted: {np.array(result['weights_after_purpose']).round(3)}")
    
    # 报告
    print("\n" + "="*70)
    print("📊 9D AGENT REPORT")
    print("="*70)
    
    purpose_summary = agent.get_purpose_summary()
    if purpose_summary['enabled']:
        print(f"\n🎯 Purpose Summary:")
        print(f"   Dominant dimension: {purpose_summary['dominant_dimension']}")
        print(f"   Purpose strength: {purpose_summary['purpose_strength']:.4f}")
        print(f"   Total generations: {purpose_summary['total_generations']}")
        print(f"   Purpose drift: {purpose_summary['purpose_drift']:.4f}")
        print(f"   Current statement: {purpose_summary['current_statement'][:100]}...")
    
    print(f"\n✓ 9D Agent test complete!")
    print("="*70)
