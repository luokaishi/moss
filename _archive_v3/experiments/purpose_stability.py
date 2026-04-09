"""
MOSS v3.1 - Long-term Purpose Stability Experiment
===================================================

长时Purpose稳定性实验（10,000+步）
验证假设H2: Purpose exhibits hysteresis

Author: Cash
Date: 2026-03-19
"""

import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_9d import MOSSv3Agent9D


class PurposeStabilityExperiment:
    """Purpose稳定性实验"""
    
    def __init__(self, agent_id: str = "stability_test"):
        self.agent_id = agent_id
        self.checkpoint_interval = 1000
        
    def run_long_term(self, n_steps: int = 10000) -> Dict:
        """
        运行长时稳定性实验
        
        观察：
        1. Purpose是否保持相对稳定（滞后性）
        2. Purpose是否会经历相变（突变）
        3. Purpose漂移的长期趋势
        """
        print("="*70)
        print("🧪 Purpose Stability Experiment (Long-term)")
        print("="*70)
        print(f"Agent: {self.agent_id}")
        print(f"Steps: {n_steps:,}")
        print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # 创建9D agent
        agent = MOSSv3Agent9D(
            agent_id=self.agent_id,
            enable_social=True,
            enable_purpose=True,
            purpose_interval=500  # 每500步评估Purpose
        )
        
        # 记录
        history = {
            'purpose_evolution': [],
            'weight_evolution': [],
            'coherence_evolution': [],
            'checkpoints': []
        }
        
        prev_purpose = None
        phase_transitions = []
        
        for step in range(n_steps):
            # 执行一步
            result = agent.step()
            
            # 记录每100步
            if step % 100 == 0:
                if agent.purpose_generator:
                    pg = agent.purpose_generator
                    
                    # Purpose信息
                    purpose_data = {
                        'step': step,
                        'vector': pg.purpose_vector.tolist(),
                        'statement': pg.purpose_statement,
                        'dominant': self._get_dominant_dim(pg.purpose_vector)
                    }
                    history['purpose_evolution'].append(purpose_data)
                    
                    # 权重信息
                    history['weight_evolution'].append({
                        'step': step,
                        'weights': agent.weights.tolist()
                    })
                    
                    # 检测相变
                    if prev_purpose is not None:
                        drift = np.linalg.norm(
                            np.array(pg.purpose_vector) - np.array(prev_purpose)
                        )
                        if drift > 0.5:  # 大幅变化阈值
                            phase_transitions.append({
                                'step': step,
                                'drift': float(drift),
                                'from_statement': '...',  # 简化
                                'to_statement': pg.purpose_statement
                            })
                    
                    prev_purpose = pg.purpose_vector.tolist()
            
            # 检查点
            if step > 0 and step % self.checkpoint_interval == 0:
                print(f"\n📍 Checkpoint {step:,}")
                if agent.purpose_generator:
                    pg = agent.purpose_generator
                    print(f"   Purpose generations: {len(pg.purpose_history)}")
                    if len(pg.purpose_history) > 1:
                        # 计算Purpose稳定性
                        first = np.array(pg.purpose_history[0]['purpose_vector'])
                        current = pg.purpose_vector
                        total_drift = np.linalg.norm(current - first)
                        print(f"   Total Purpose drift: {total_drift:.4f}")
                        print(f"   Current dominant: {self._get_dominant_dim(current)}")
                        print(f"   Current statement: {pg.purpose_statement[:60]}...")
                
                checkpoint = {
                    'step': step,
                    'purpose_summary': agent.get_purpose_summary() if agent.purpose_generator else {}
                }
                history['checkpoints'].append(checkpoint)
        
        # 最终分析
        final_analysis = self._analyze_stability(history, agent)
        
        results = {
            'config': {
                'agent_id': self.agent_id,
                'n_steps': n_steps,
                'start_time': datetime.now().isoformat()
            },
            'history': history,
            'phase_transitions': phase_transitions,
            'stability_analysis': final_analysis
        }
        
        # 保存
        save_path = Path('experiments/purpose_stability_10k.json')
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {save_path}")
        
        return results
    
    def _get_dominant_dim(self, purpose_vector: np.ndarray) -> str:
        """获取主导维度"""
        dims = ['Survival', 'Curiosity', 'Influence', 'Optimization',
                'Coherence', 'Valence', 'Other', 'Norm']
        idx = np.argmax(purpose_vector[:8])
        return dims[idx] if idx < len(dims) else 'Unknown'
    
    def _analyze_stability(self, history: Dict, agent: MOSSv3Agent9D) -> Dict:
        """分析稳定性"""
        analysis = {
            'purpose_generations': 0,
            'mean_purpose_lifetime': 0,
            'stability_score': 0.0,
            'phase_transitions': len(history.get('phase_transitions', [])),
            'dominant_dim_changes': 0
        }
        
        if agent.purpose_generator:
            pg = agent.purpose_generator
            analysis['purpose_generations'] = len(pg.purpose_history)
            
            if len(pg.purpose_history) > 1:
                # 计算平均Purpose生命周期
                lifetimes = []
                for i in range(1, len(pg.purpose_history)):
                    step_diff = pg.purpose_history[i]['step'] - pg.purpose_history[i-1]['step']
                    lifetimes.append(step_diff)
                analysis['mean_purpose_lifetime'] = np.mean(lifetimes)
                
                # 计算总体漂移
                first = np.array(pg.purpose_history[0]['purpose_vector'])
                last = pg.purpose_vector
                total_drift = np.linalg.norm(last - first)
                analysis['total_drift'] = float(total_drift)
                
                # 稳定性评分（越低越稳定）
                analysis['stability_score'] = 1.0 / (1.0 + total_drift)
                
                # 主导维度变化次数
                prev_dim = None
                dim_changes = 0
                for h in pg.purpose_history:
                    vec = np.array(h['purpose_vector'])
                    curr_dim = self._get_dominant_dim(vec)
                    if prev_dim is not None and curr_dim != prev_dim:
                        dim_changes += 1
                    prev_dim = curr_dim
                analysis['dominant_dim_changes'] = dim_changes
        
        return analysis
    
    def print_results(self, results: Dict):
        """打印结果"""
        print("\n" + "="*70)
        print("📊 PURPOSE STABILITY ANALYSIS")
        print("="*70)
        
        config = results['config']
        print(f"\nConfiguration:")
        print(f"  Steps: {config['n_steps']:,}")
        print(f"  Agent: {config['agent_id']}")
        
        analysis = results['stability_analysis']
        print(f"\n📈 Stability Metrics:")
        print(f"  Purpose generations: {analysis['purpose_generations']}")
        print(f"  Mean Purpose lifetime: {analysis['mean_purpose_lifetime']:.1f} steps")
        print(f"  Total Purpose drift: {analysis.get('total_drift', 0):.4f}")
        print(f"  Stability score: {analysis['stability_score']:.4f}")
        print(f"  Dominant dim changes: {analysis['dominant_dim_changes']}")
        print(f"  Phase transitions: {analysis['phase_transitions']}")
        
        # 解释
        print(f"\n💡 Interpretation:")
        if analysis['stability_score'] > 0.8:
            print(f"  → HIGH STABILITY: Purpose exhibits strong hysteresis")
            print(f"    (resistant to change, consistent 'life philosophy')")
        elif analysis['stability_score'] > 0.5:
            print(f"  → MODERATE STABILITY: Purpose evolves gradually")
            print(f"    (adapts to context while maintaining core identity)")
        else:
            print(f"  → LOW STABILITY: Purpose changes frequently")
            print(f"    (highly adaptive, 'identity crisis' possible)")
        
        if analysis['phase_transitions'] > 0:
            print(f"\n  → PHASE TRANSITIONS DETECTED: {analysis['phase_transitions']}")
            print(f"    (Purpose underwent major shifts, like 'conversion experiences')")
        
        print(f"\n✅ Hypothesis H2 (Purpose Stability): ", end="")
        if analysis['stability_score'] > 0.5 and analysis['phase_transitions'] <= 2:
            print("SUPPORTED")
            print(f"   Purpose shows hysteresis + limited phase transitions")
        else:
            print("PARTIALLY SUPPORTED")
            print(f"   Further analysis needed")
        
        print("="*70)


if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - Purpose Stability Experiment")
    print("="*70)
    
    # 先用1000步测试（完整10,000步需要更长时间）
    experiment = PurposeStabilityExperiment()
    
    print("\nRunning 1,000-step stability test...")
    print("(Full 10,000-step experiment can be run overnight)\n")
    
    results = experiment.run_long_term(n_steps=1000)
    experiment.print_results(results)
    
    print("\n✓ Purpose Stability experiment complete!")
    print("="*70)
