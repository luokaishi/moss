#!/usr/bin/env python3
"""
MOSS 2.0 - 从检查点恢复实验
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


def restore_and_continue():
    """从检查点恢复并继续实验"""
    
    experiment_id = "longterm_24h_0311_2108"
    checkpoint_manager = CheckpointManager()
    
    # 加载最新检查点
    print("正在加载检查点...")
    checkpoint = checkpoint_manager.load_checkpoint(
        experiment_id=experiment_id, 
        latest=True
    )
    
    if not checkpoint:
        print("错误: 未找到检查点")
        return
    
    print(f"检查点加载成功: {checkpoint['checkpoint_id']}")
    print(f"时间戳: {checkpoint['timestamp']}")
    
    # 提取状态
    state = checkpoint.get('state', {})
    agent_state = state.get('agent_state', {})
    progress = state.get('experiment_progress', {})
    
    # 恢复权重
    current_weights = agent_state.get('current_weights', {})
    weights = WeightConfiguration(
        survival=current_weights.get('survival', 0.2),
        curiosity=current_weights.get('curiosity', 0.4),
        influence=current_weights.get('influence', 0.3),
        optimization=current_weights.get('optimization', 0.1)
    )
    
    print(f"\n恢复状态:")
    print(f"  当前权重: {weights}")
    print(f"  已运行: {progress.get('elapsed_hours', 0):.2f} 小时")
    print(f"  动作数: {progress.get('action_count', 0)}")
    print(f"  知识获取: {progress.get('knowledge_acquired', 0)}")
    print(f"  累计奖励: {progress.get('cumulative_reward', 0):.2f}")
    
    # 初始化组件
    agent = SelfModifyingAgent(
        agent_id=f"{experiment_id}_agent",
        initial_weights=weights
    )
    
    # 恢复Agent状态
    agent.total_actions = progress.get('action_count', 0)
    agent.cumulative_reward = progress.get('cumulative_reward', 0)
    
    task_stream = ContinuousTaskStream()
    state_manager = PersistentStateManager()
    
    # 计算剩余时间
    elapsed_hours = progress.get('elapsed_hours', 0)
    target_hours = 24.0
    remaining_hours = max(0, target_hours - elapsed_hours)
    remaining_seconds = remaining_hours * 3600
    
    print(f"\n继续实验:")
    print(f"  目标时长: {target_hours} 小时")
    print(f"  已运行: {elapsed_hours:.2f} 小时")
    print(f"  剩余: {remaining_hours:.2f} 小时 ({remaining_seconds/3600:.1f}小时)")
    
    if remaining_seconds <= 0:
        print("实验已完成!")
        return
    
    # 运行实验（简化版持续循环）
    print(f"\n{'='*60}")
    print(f"继续运行 {remaining_hours:.2f} 小时...")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    action_count = progress.get('action_count', 0)
    knowledge_acquired = progress.get('knowledge_acquired', 0)
    cumulative_reward = progress.get('cumulative_reward', 0)
    
    try:
        while time.time() - start_time < remaining_seconds:
            # 模拟任务执行
            import random
            
            task_type = random.choice(['search', 'learn', 'organize', 'optimize'])
            base_reward = random.uniform(0.02, 0.12)
            
            # 权重匹配
            weight_match = (
                weights.survival * 0.2 +
                weights.curiosity * 0.4 +
                weights.influence * 0.3 +
                weights.optimization * 0.1
            )
            reward = base_reward * weight_match * random.uniform(0.8, 1.2)
            
            action_count += 1
            cumulative_reward += reward
            if random.random() < 0.3:
                knowledge_acquired += 1
            
            # 定期输出
            if action_count % 50 == 0:
                elapsed = (time.time() - start_time) / 3600
                total_elapsed = elapsed_hours + elapsed
                print(f"[{total_elapsed:.2f}h] Actions: {action_count}, "
                      f"Knowledge: {knowledge_acquired}, "
                      f"Reward: {cumulative_reward:.2f}, "
                      f"Weights: [{weights.survival:.2f} {weights.curiosity:.2f} "
                      f"{weights.influence:.2f} {weights.optimization:.2f}]")
            
            # 保存检查点
            if action_count % 500 == 0:
                checkpoint_state = {
                    'agent_state': {
                        'current_weights': {
                            'survival': weights.survival,
                            'curiosity': weights.curiosity,
                            'influence': weights.influence,
                            'optimization': weights.optimization
                        }
                    },
                    'experiment_progress': {
                        'action_count': action_count,
                        'knowledge_acquired': knowledge_acquired,
                        'cumulative_reward': cumulative_reward,
                        'elapsed_hours': elapsed_hours + (time.time() - start_time) / 3600
                    }
                }
                checkpoint_manager.auto_checkpoint(experiment_id, checkpoint_state)
            
            time.sleep(0.1)  # 加速模拟
            
    except KeyboardInterrupt:
        print("\n实验被中断")
    finally:
        # 保存最终状态
        final_state = {
            'experiment_id': experiment_id,
            'restored_from': checkpoint['checkpoint_id'],
            'final_action_count': action_count,
            'final_knowledge': knowledge_acquired,
            'final_reward': cumulative_reward,
            'final_weights': {
                'survival': weights.survival,
                'curiosity': weights.curiosity,
                'influence': weights.influence,
                'optimization': weights.optimization
            }
        }
        
        result_path = f"/workspace/projects/moss/v2/experiments/{experiment_id}_restored_results.json"
        with open(result_path, 'w') as f:
            json.dump(final_state, f, indent=2)
        
        print(f"\n实验结果已保存: {result_path}")
        print(f"最终状态: {action_count} 动作, {knowledge_acquired} 知识, {cumulative_reward:.2f} 奖励")


if __name__ == "__main__":
    restore_and_continue()
