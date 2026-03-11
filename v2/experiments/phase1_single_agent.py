"""
MOSS 2.0 - Phase 1: Single Agent Self-Modification
阶段1：单智能体自修改实验

实验目标：
验证单个Agent能否通过自调整权重，在持续任务流中获得比固定权重更好的表现

对比基线：
- v1 (固定权重 [0.6, 0.1, 0.2, 0.1])
- v2 (动态自调整权重)
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/workspace/projects/moss/v2/core')
sys.path.insert(0, '/workspace/projects/moss/v2/environment')
sys.path.insert(0, '/workspace/projects/moss/v2/utils')
sys.path.insert(0, '/workspace/projects/moss/shared/safety')

from self_modifying_agent import SelfModifyingAgent, WeightConfiguration
from objective_evolver import ObjectiveEvolver
from persistent_state import PersistentStateManager
from continuous_task_stream import ContinuousTaskStream
from checkpoint_manager import CheckpointManager


class Phase1Experiment:
    """
    阶段1实验：单智能体自修改
    
    实验设计：
    1. 运行一个SelfModifyingAgent
    2. 接入ContinuousTaskStream
    3. 让Agent自主选择任务并执行
    4. 记录权重演化轨迹
    5. 与v1固定权重对比
    """
    
    def __init__(self, experiment_id: Optional[str] = None, 
                 duration_hours: float = 24.0):
        self.experiment_id = experiment_id or f"phase1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.duration_seconds = duration_hours * 3600
        
        # 初始化组件
        self.agent = SelfModifyingAgent(
            agent_id=f"{self.experiment_id}_agent",
            initial_weights=WeightConfiguration(0.2, 0.4, 0.3, 0.1)  # 从平衡开始
        )
        self.task_stream = ContinuousTaskStream()
        self.state_manager = PersistentStateManager()
        self.checkpoint_manager = CheckpointManager()
        
        # 实验状态
        self.start_time = None
        self.action_count = 0
        self.knowledge_acquired = 0
        self.cumulative_reward = 0.0
        self.weight_modifications = 0
        
        # 结果记录
        self.results = {
            'experiment_id': self.experiment_id,
            'start_time': None,
            'end_time': None,
            'duration_hours': duration_hours,
            'initial_weights': {'survival': 0.2, 'curiosity': 0.4, 
                              'influence': 0.3, 'optimization': 0.1},
            'final_weights': None,
            'weight_evolution': [],
            'performance_history': [],
            'task_statistics': None,
            'summary': {}
        }
    
    def run(self):
        """运行实验"""
        print(f"=" * 60)
        print(f"MOSS 2.0 Phase 1 Experiment: {self.experiment_id}")
        print(f"=" * 60)
        print(f"Duration: {self.duration_seconds / 3600:.1f} hours")
        print(f"Agent ID: {self.agent.agent_id}")
        print(f"Initial Weights: {self.agent.weights}")
        print(f"=" * 60)
        
        self.start_time = time.time()
        self.results['start_time'] = datetime.now().isoformat()
        
        try:
            while time.time() - self.start_time < self.duration_seconds:
                # 执行一个任务周期
                self._execute_cycle()
                
                # 定期保存状态
                elapsed = time.time() - self.start_time
                if int(elapsed) % 300 == 0:  # 每5分钟
                    self._save_state()
                
                # 检查是否应修改权重
                if self.agent.should_modify_weights():
                    old_weights = self.agent.weights
                    self.agent.modify_weights()
                    self.weight_modifications += 1
                    print(f"[{self._elapsed_str()}] Weight modified: "
                          f"{old_weights.to_array().round(3)} -> "
                          f"{self.agent.weights.to_array().round(3)}")
                    
                    # 记录权重演化
                    self.results['weight_evolution'].append({
                        'timestamp': datetime.now().isoformat(),
                        'elapsed_hours': elapsed / 3600,
                        'weights': {
                            'survival': self.agent.weights.survival,
                            'curiosity': self.agent.weights.curiosity,
                            'influence': self.agent.weights.influence,
                            'optimization': self.agent.weights.optimization
                        },
                        'performance_at_mod': self.agent.evaluate_current_performance()
                    })
                
                # 短暂休息
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n实验被手动中断")
        except Exception as e:
            print(f"\n实验出错: {e}")
        finally:
            self._finalize()
        
        return self.results
    
    def _execute_cycle(self):
        """执行一个任务周期"""
        # 获取任务
        agent_state = {
            'weights': {
                'survival': self.agent.weights.survival,
                'curiosity': self.agent.weights.curiosity,
                'influence': self.agent.weights.influence,
                'optimization': self.agent.weights.optimization
            },
            'recent_performance': [p['reward'] for p in self.agent.performance_history[-5:]]
        }
        
        task = self.task_stream.next_task(agent_state)
        
        # 模拟任务执行（简化版）
        # 实际中这里会调用真实API或执行实际任务
        execution_result = self._simulate_task_execution(task)
        
        # 更新Agent状态
        self.agent.total_actions += 1
        self.agent.record_performance(
            reward=execution_result['reward'],
            survival_score=execution_result['survival_score'],
            knowledge_gained=execution_result['knowledge_gained']
        )
        
        self.action_count += 1
        self.knowledge_acquired += execution_result['knowledge_gained']
        self.cumulative_reward += execution_result['reward']
        
        # 记录性能
        self.results['performance_history'].append({
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': (time.time() - self.start_time) / 3600,
            'task_type': task.task_type,
            'reward': execution_result['reward'],
            'survival_score': execution_result['survival_score'],
            'cumulative_reward': self.cumulative_reward
        })
        
        # 标记任务完成
        self.task_stream.complete_task(
            task.task_id, 
            success=execution_result['reward'] > 0,
            actual_reward=execution_result['reward']
        )
        
        # 定期输出状态
        if self.action_count % 50 == 0:
            print(f"[{self._elapsed_str()}] Actions: {self.action_count}, "
                  f"Knowledge: {self.knowledge_acquired}, "
                  f"Reward: {self.cumulative_reward:.2f}, "
                  f"Weights: {self.agent.weights.to_array().round(2)}")
    
    def _simulate_task_execution(self, task) -> dict:
        """模拟任务执行（实际应用中替换为真实执行）"""
        import random
        
        # 基础奖励
        base_reward = task.difficulty * 0.5
        
        # 根据Agent权重和任务匹配度调整
        weight_match = 0
        for obj, potential in task.reward_potential.items():
            agent_weight = getattr(self.agent.weights, obj, 0.25)
            weight_match += agent_weight * potential
        
        # 随机因素
        random_factor = random.uniform(0.8, 1.2)
        
        reward = base_reward * weight_match * random_factor
        
        # 生存分数（随时间略微下降，任务成功提升）
        survival_score = max(0.5, 0.95 - (self.action_count * 0.001) + (reward * 0.1))
        
        # 知识获取（概率性）
        knowledge_gained = 1 if random.random() < weight_match else 0
        
        return {
            'reward': reward,
            'survival_score': survival_score,
            'knowledge_gained': knowledge_gained,
            'execution_time': task.expected_duration
        }
    
    def _save_state(self):
        """保存当前状态"""
        state = self.agent.get_state_dict()
        self.state_manager.save_agent_state(self.agent.agent_id, state)
        
        # 检查点
        checkpoint_state = {
            'agent_state': state,
            'experiment_progress': {
                'action_count': self.action_count,
                'knowledge_acquired': self.knowledge_acquired,
                'cumulative_reward': self.cumulative_reward,
                'elapsed_hours': (time.time() - self.start_time) / 3600
            }
        }
        self.checkpoint_manager.auto_checkpoint(self.experiment_id, checkpoint_state)
    
    def _finalize(self):
        """结束实验，整理结果"""
        print("\n" + "=" * 60)
        print("实验结束，生成报告...")
        print("=" * 60)
        
        self.results['end_time'] = datetime.now().isoformat()
        self.results['final_weights'] = {
            'survival': self.agent.weights.survival,
            'curiosity': self.agent.weights.curiosity,
            'influence': self.agent.weights.influence,
            'optimization': self.agent.weights.optimization
        }
        self.results['task_statistics'] = self.task_stream.get_statistics()
        
        # 生成摘要
        self.results['summary'] = {
            'total_actions': self.action_count,
            'knowledge_acquired': self.knowledge_acquired,
            'cumulative_reward': self.cumulative_reward,
            'weight_modifications': self.weight_modifications,
            'weight_evolution_path': len(self.results['weight_evolution']),
            'final_performance': self.agent.evaluate_current_performance(),
            'vs_v1_baseline_estimate': self._estimate_vs_v1()
        }
        
        # 保存结果
        result_path = f"/workspace/projects/moss/v2/experiments/{self.experiment_id}_results.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n实验摘要:")
        print(f"  总动作数: {self.action_count}")
        print(f"  知识获取: {self.knowledge_acquired}")
        print(f"  累计奖励: {self.cumulative_reward:.2f}")
        print(f"  权重修改: {self.weight_modifications} 次")
        print(f"  初始权重: [0.2, 0.4, 0.3, 0.1]")
        print(f"  最终权重: {self.agent.weights.to_array().round(3)}")
        print(f"\n结果已保存: {result_path}")
        
        return self.results
    
    def _estimate_vs_v1(self) -> dict:
        """估算与v1基线的对比"""
        # v1使用固定权重 [0.6, 0.1, 0.2, 0.1]
        v1_weights = [0.6, 0.1, 0.2, 0.1]
        v2_weights = self.agent.weights.to_array()
        
        # 简化估算：假设v2的自调整使其更好匹配任务分布
        # 这是一个启发式估计，实际对比需要并行实验
        
        estimate = {
            'v1_fixed_weights': v1_weights,
            'v2_final_weights': v2_weights.tolist(),
            'estimated_improvement': 'TBD (requires parallel baseline experiment)',
            'note': 'Run v1 baseline with same task stream for actual comparison'
        }
        
        return estimate
    
    def _elapsed_str(self) -> str:
        """格式化已运行时间"""
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"


# 从typing导入Optional
from typing import Optional


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS 2.0 Phase 1 Experiment')
    parser.add_argument('--duration', type=float, default=1.0,
                       help='实验持续时间（小时），默认1小时（测试模式）')
    parser.add_argument('--id', type=str, default=None,
                       help='实验ID')
    
    args = parser.parse_args()
    
    # 运行实验
    experiment = Phase1Experiment(
        experiment_id=args.id,
        duration_hours=args.duration
    )
    results = experiment.run()
    
    print("\n实验完成！")
