#!/usr/bin/env python3
"""
7层架构长期运行测试 (1000周期)

验证目标：
1. 概念系统稳定性 - 概念是否收敛，预测质量是否提升
2. 目标涌现 - 是否在1000周期内形成稳定目标
3. 元驱动激活 - 元驱动是否被触发，是否产生自我修改
4. 自我意识演化 - 自我模型准确率是否提升
5. 系统整体稳定性 - 是否出现崩溃或异常
"""

import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')

from agi.concept import ConceptSystem
from agi.goal import GoalSystem
from agi.meta_drive import SelfModel, MetaController
from agi.ecology import World


def run_concept_system_test(n_cycles=1000):
    """测试概念系统长期稳定性"""
    print("\n" + "="*60)
    print("[测试1] 概念系统长期稳定性")
    print("="*60)
    
    state_dim = 16
    concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)
    
    # 记录指标
    errors = []
    stabilities = []
    qualities = []
    split_events = []
    
    for i in range(n_cycles):
        # 模拟状态转移（带有一些模式）
        state = np.random.rand(state_dim)
        # 添加周期性模式
        state[0] = 0.5 + 0.3 * np.sin(i * 0.1)
        state[1] = 0.5 + 0.3 * np.cos(i * 0.05)
        
        next_state = np.random.rand(state_dim)
        next_state[0] = 0.5 + 0.3 * np.sin((i+1) * 0.1)
        next_state[1] = 0.5 + 0.3 * np.cos((i+1) * 0.05)
        
        action = f"action_{i % 5}"
        
        concept, error, info = concept_system.step(state, next_state, action)
        
        errors.append(error)
        stabilities.append(info['concept_stability'])
        qualities.append(info['prediction_quality'])
        
        if info.get('split_triggered'):
            split_events.append(i)
        
        # 每100周期输出进度
        if (i + 1) % 100 == 0:
            recent_error = np.mean(errors[-100:])
            recent_quality = np.mean(qualities[-100:])
            print(f"  Cycle {i+1:4d}: Error={recent_error:.4f}, Quality={recent_quality:.4f}, Concepts={concept_system.concept_dim}")
    
    # 总结
    print(f"\n  总结:")
    print(f"    总周期: {n_cycles}")
    print(f"    最终概念数: {concept_system.concept_dim}")
    print(f"    概念分裂次数: {concept_system.split_count}")
    print(f"    平均预测误差: {np.mean(errors):.4f} → {np.mean(errors[-100:]):.4f} (改进: {(1-np.mean(errors[-100:])/(np.mean(errors[:100])+0.001))*100:.1f}%)")
    print(f"    平均预测质量: {np.mean(qualities):.4f} → {np.mean(qualities[-100:]):.4f}")
    print(f"    平均稳定性: {np.mean(stabilities):.4f}")
    
    return {
        'concept_dim': concept_system.concept_dim,
        'split_count': concept_system.split_count,
        'error_trend': 'decreasing' if np.mean(errors[-100:]) < np.mean(errors[:100]) else 'stable',
        'final_quality': float(np.mean(qualities[-100:]))
    }


def run_goal_system_test(n_cycles=1000):
    """测试目标涌现"""
    print("\n" + "="*60)
    print("[测试2] 目标涌现测试")
    print("="*60)
    
    state_dim = 16
    goal_system = GoalSystem(state_dim=state_dim)
    
    # 模拟运行
    for i in range(n_cycles):
        state = np.random.rand(state_dim)
        # 添加模式：某些状态更常见
        if i % 10 < 7:  # 70%时间在一个区域
            state[:4] = [0.8, 0.2, 0.5, 0.3]
            action = "explore"
        else:
            action = "exploit"
        
        reward = 0.5 + 0.3 * np.sin(i * 0.05)
        
        goal_system.step(state, action, reward, i)
    
    stats = goal_system.get_stats()
    
    print(f"\n  总结:")
    print(f"    总周期: {n_cycles}")
    print(f"    轨迹缓冲区: {stats['trajectory_buffer_size']}")
    print(f"    活跃目标数: {stats['num_active_goals']}")
    
    if stats['goals']:
        print(f"    目标列表:")
        for g in stats['goals']:
            print(f"      - {g['name']}: consistency={g['consistency']:.3f}, stability={g['stability']:.3f}")
    else:
        print(f"    注意: 尚未形成稳定目标（需要更多周期或更强的行为模式）")
    
    return {
        'num_goals': stats['num_active_goals'],
        'trajectory_count': stats['trajectory_buffer_size'],
        'goals': stats['goals']
    }


def run_meta_drive_test(n_cycles=1000):
    """测试元驱动和自我模型"""
    print("\n" + "="*60)
    print("[测试3] 元驱动与自我模型测试")
    print("="*60)
    
    state_dim = 16
    action_dim = 10
    
    self_model = SelfModel(state_dim=state_dim, action_dim=action_dim, drive_dim=4)
    meta_controller = MetaController(self_model=self_model)
    
    # 记录
    awareness_history = []
    modification_history = []
    
    for i in range(n_cycles):
        state = np.random.rand(state_dim)
        
        # 模拟行动（带有一些可预测的模式）
        action = np.zeros(action_dim)
        action[i % action_dim] = 1.0
        
        # 更新自我模型
        self_model.update(state, action)
        
        # 模拟性能波动
        performance = 0.5 + 0.3 * np.sin(i * 0.02) + 0.1 * np.random.randn()
        performance = np.clip(performance, 0, 1)
        
        # 元控制步骤
        prev_mods = len(meta_controller.modification_history)
        meta_controller.step(state, performance)
        
        if len(meta_controller.modification_history) > prev_mods:
            modification_history.append({
                'cycle': i,
                'mod': meta_controller.modification_history[-1]
            })
        
        awareness = self_model.get_self_awareness_score()
        awareness_history.append(awareness)
        
        if (i + 1) % 200 == 0:
            print(f"  Cycle {i+1:4d}: Self-Awareness={awareness:.4f}, Modifications={len(modification_history)}")
    
    print(f"\n  总结:")
    print(f"    总周期: {n_cycles}")
    print(f"    自我意识趋势: {np.mean(awareness_history[:100]):.4f} → {np.mean(awareness_history[-100:]):.4f}")
    print(f"    自我修改次数: {len(modification_history)}")
    
    if modification_history:
        print(f"    修改记录:")
        for m in modification_history[:5]:
            print(f"      - Cycle {m['cycle']}: {m['mod']['type']} - {m['mod']['description']}")
    
    return {
        'final_awareness': float(np.mean(awareness_history[-100:])),
        'awareness_trend': 'increasing' if np.mean(awareness_history[-100:]) > np.mean(awareness_history[:100]) else 'stable',
        'modifications': len(modification_history)
    }


def run_ecology_test(n_cycles=1000):
    """测试生态系统"""
    print("\n" + "="*60)
    print("[测试4] 生态系统长期测试")
    print("="*60)
    
    world = World(size=10, n_agents=3)
    
    stats_history = []
    
    for i in range(n_cycles):
        stats = world.step()
        stats_history.append(stats)
        
        if (i + 1) % 200 == 0:
            print(f"  Cycle {i+1:4d}: Agents={stats['alive_agents']}, AvgEnergy={stats['avg_energy']:.1f}, Births={stats['birth_count']}, Deaths={stats['death_count']}")
    
    final_stats = stats_history[-1]
    
    print(f"\n  总结:")
    print(f"    总周期: {n_cycles}")
    print(f"    最终存活: {final_stats['alive_agents']} 智能体")
    print(f"    总出生: {final_stats['birth_count']}")
    print(f"    总死亡: {final_stats['death_count']}")
    print(f"    平均能量: {final_stats['avg_energy']:.1f}")
    print(f"    平均适应度: {final_stats['avg_fitness']:.1f}")
    print(f"    驱动多样性:")
    for key, div in final_stats['drive_diversity'].items():
        print(f"      - {key}: mean={div['mean']:.3f}, std={div['std']:.3f}")
    
    return {
        'final_agents': final_stats['alive_agents'],
        'total_births': final_stats['birth_count'],
        'total_deaths': final_stats['death_count'],
        'drive_diversity': final_stats['drive_diversity']
    }


def main():
    print("="*60)
    print("7层架构长期运行测试 (1000周期)")
    print("="*60)
    print(f"开始时间: {datetime.now().isoformat()}")
    
    results = {}
    
    # 运行各组件测试
    results['concept_system'] = run_concept_system_test(1000)
    results['goal_system'] = run_goal_system_test(1000)
    results['meta_drive'] = run_meta_drive_test(1000)
    results['ecology'] = run_ecology_test(1000)
    
    # 保存