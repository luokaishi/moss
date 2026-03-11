"""
MOSS v2.0.0 - Parallel Comparison Experiment
v2.0.0 vs v0.3.0 并行对比实验

对比维度：
1. 知识获取效率
2. 任务完成质量
3. 资源利用效率
4. 长期稳定性
"""

import json
import time
import sys
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace/projects/moss/v2/core')
sys.path.insert(0, '/workspace/projects/moss/v2/environment')

from self_modifying_agent import SelfModifyingAgent, WeightConfiguration
from continuous_task_stream import ContinuousTaskStream


class ComparisonExperiment:
    """
    并行对比实验
    
    同时运行：
    - v2.0.0: 自修改动态权重
    - v0.3.0: 固定权重 [0.6, 0.1, 0.2, 0.1] (模拟)
    """
    
    def __init__(self, duration_hours: float = 2.0):
        self.duration_hours = duration_hours
        self.experiment_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # v2.0.0 Agent - 自修改
        self.v2_agent = SelfModifyingAgent(
            agent_id="v2_self_modifying",
            initial_weights=WeightConfiguration(0.2, 0.4, 0.3, 0.1)
        )
        # 设置短冷却期以便观察修改
        self.v2_agent.modification_cooldown = 600
        
        # v0.3.0 Agent - 固定权重（最优配置）
        self.v03_agent = SelfModifyingAgent(
            agent_id="v03_fixed",
            initial_weights=WeightConfiguration(0.6, 0.1, 0.2, 0.1)
        )
        # 禁用自修改（模拟v0.3.0固定权重）
        self.v03_agent.modification_cooldown = float('inf')
        
        # 共享任务流（确保公平对比）
        self.task_stream = ContinuousTaskStream()
        self.task_stream_v03 = ContinuousTaskStream()  # 相同任务分布
        
        self.results = {
            'experiment_id': self.experiment_id,
            'duration_hours': duration_hours,
            'v2_data': [],
            'v03_data': [],
            'comparison': []
        }
    
    def run(self):
        """运行对比实验"""
        print("=" * 70)
        print("MOSS v2.0.0 vs v0.3.0 Parallel Comparison")
        print(f"Duration: {self.duration_hours} hours")
        print("=" * 70)
        print()
        print("Configuration:")
        print(f"  v2.0.0: Self-modifying, initial=[0.2, 0.4, 0.3, 0.1]")
        print(f"  v0.3.0: Fixed weights [0.6, 0.1, 0.2, 0.1] (optimal)")
        print()
        
        start_time = time.time()
        duration_seconds = self.duration_hours * 3600
        check_interval = 300  # 每5分钟记录一次
        last_check = 0
        
        round_num = 0
        
        while time.time() - start_time < duration_seconds:
            round_num += 1
            
            # 运行一轮对比
            self._run_comparison_round(round_num)
            
            # 定期输出状态
            elapsed = time.time() - start_time
            if elapsed - last_check >= check_interval:
                self._print_status(elapsed)
                last_check = elapsed
            
            time.sleep(0.5)
        
        self._finalize()
        return self.results
    
    def _run_comparison_round(self, round_num: int):
        """运行一轮对比"""
        # v2.0.0 Agent执行任务
        v2_task = self.task_stream.next_task(self._get_agent_state(self.v2_agent))
        v2_result = self._simulate_execution(self.v2_agent, v2_task)
        self._update_agent(self.v2_agent, v2_result)
        
        # v0.3.0 Agent执行相同类型任务
        v03_task = self.task_stream_v03.next_task(self._get_agent_state(self.v03_agent))
        v03_result = self._simulate_execution(self.v03_agent, v03_task)
        self._update_agent(self.v03_agent, v03_result)
        
        # 记录数据
        self.results['v2_data'].append({
            'round': round_num,
            'weights': self.v2_agent.weights.to_array().tolist(),
            'knowledge': self.v2_agent.knowledge_acquired,
            'reward': self.v2_agent.cumulative_reward,
            'modifications': len(self.v2_agent.weight_history)
        })
        
        self.results['v03_data'].append({
            'round': round_num,
            'weights': self.v03_agent.weights.to_array().tolist(),
            'knowledge': self.v03_agent.knowledge_acquired,
            'reward': self.v03_agent.cumulative_reward,
            'modifications': len(self.v03_agent.weight_history)
        })
    
    def _get_agent_state(self, agent: SelfModifyingAgent) -> Dict:
        """获取Agent状态"""
        return {
            'weights': {
                'survival': agent.weights.survival,
                'curiosity': agent.weights.curiosity,
                'influence': agent.weights.influence,
                'optimization': agent.weights.optimization
            },
            'recent_performance': [0.5] * 5  # 简化
        }
    
    def _simulate_execution(self, agent: SelfModifyingAgent, task) -> Dict:
        """模拟任务执行"""
        import random
        
        # 根据Agent权重和任务匹配度
        weight_match = 0
        for obj, potential in task.reward_potential.items():
            agent_weight = getattr(agent.weights, obj, 0.25)
            weight_match += agent_weight * potential
        
        base_reward = task.difficulty * 0.5
        random_factor = random.uniform(0.8, 1.2)
        reward = base_reward * weight_match * random_factor
        
        survival_score = max(0.5, 0.95 - (agent.total_actions * 0.0001))
        knowledge_gained = 1 if random.random() < weight_match else 0
        
        return {
            'reward': reward,
            'survival_score': survival_score,
            'knowledge_gained': knowledge_gained
        }
    
    def _update_agent(self, agent: SelfModifyingAgent, result: Dict):
        """更新Agent状态"""
        agent.total_actions += 1
        agent.record_performance(
            reward=result['reward'],
            survival_score=result['survival_score'],
            knowledge_gained=result['knowledge_gained']
        )
        
        # 检查权重修改（v2.0.0）
        if agent.agent_id == "v2_self_modifying" and agent.should_modify_weights():
            agent.modify_weights()
    
    def _print_status(self, elapsed: float):
        """打印状态"""
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        
        v2 = self.results['v2_data'][-1] if self.results['v2_data'] else None
        v03 = self.results['v03_data'][-1] if self.results['v03_data'] else None
        
        print(f"\n[{hours:02d}:{minutes:02d}] Comparison Status:")
        
        if v2 and v03:
            print(f"  v2.0.0:  Knowledge={v2['knowledge']:4d} | "
                  f"Reward={v2['reward']:7.2f} | "
                  f"Mods={v2['modifications']:2d} | "
                  f"Weights=[{v2['weights'][0]:.2f}, {v2['weights'][1]:.2f}, ...]")
            print(f"  v0.3.0:  Knowledge={v03['knowledge']:4d} | "
                  f"Reward={v03['reward']:7.2f} | "
                  f"Mods={v03['modifications']:2d} | "
                  f"Weights=[FIXED]")
            
            # 计算差异
            knowledge_diff = v2['knowledge'] - v03['knowledge']
            reward_diff = v2['reward'] - v03['reward']
            
            print(f"  Diff:    Knowledge={knowledge_diff:+4d} | "
                  f"Reward={reward_diff:+7.2f}")
    
    def _finalize(self):
        """结束实验"""
        print("\n" + "=" * 70)
        print("对比实验完成，生成报告...")
        print("=" * 70)
        
        # 最终对比
        v2_final = self.results['v2_data'][-1] if self.results['v2_data'] else None
        v03_final = self.results['v03_data'][-1] if self.results['v03_data'] else None
        
        if v2_final and v03_final:
            comparison = {
                'v2_knowledge': v2_final['knowledge'],
                'v03_knowledge': v03_final['knowledge'],
                'knowledge_improvement': (
                    (v2_final['knowledge'] - v03_final['knowledge']) / 
                    max(v03_final['knowledge'], 1) * 100
                ),
                'v2_reward': v2_final['reward'],
                'v03_reward': v03_final['reward'],
                'reward_improvement': (
                    (v2_final['reward'] - v03_final['reward']) / 
                    max(v03_final['reward'], 1) * 100
                ),
                'v2_modifications': v2_final['modifications'],
                'v2_final_weights': v2_final['weights']
            }
            
            self.results['final_comparison'] = comparison
            
            print(f"\n最终对比结果:")
            print(f"  知识获取:")
            print(f"    v2.0.0: {comparison['v2_knowledge']}")
            print(f"    v0.3.0: {comparison['v03_knowledge']}")
            print(f"    提升:   {comparison['knowledge_improvement']:+.1f}%")
            print(f"\n  累计奖励:")
            print(f"    v2.0.0: {comparison['v2_reward']:.2f}")
            print(f"    v0.3.0: {comparison['v03_reward']:.2f}")
            print(f"    提升:   {comparison['reward_improvement']:+.1f}%")
            print(f"\n  权重修改:")
            print(f"    v2.0.0: {comparison['v2_modifications']}次")
            print(f"    v0.3.0: 0次 (固定)")
            print(f"\n  v2.0.0最终权重: {comparison['v2_final_weights']}")
        
        # 保存结果
        result_path = f"/workspace/projects/moss/v2/experiments/{self.experiment_id}_results.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存: {result_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS v2.0.0 vs v0.3.0 Comparison')
    parser.add_argument('--duration', type=float, default=2.0,
                       help='Duration in hours (default: 2)')
    
    args = parser.parse_args()
    
    experiment = ComparisonExperiment(duration_hours=args.duration)
    results = experiment.run()
    print("\n对比实验完成！")
