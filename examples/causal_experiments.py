#!/usr/bin/env python3
"""
MOSS 因果验证实验
ChatGPT 评审要求的关键改进：证明驱动力与行为之间的因果性

4 组实验：
  1. Drive Ablation    — 禁用涌现驱动力，观察行为变化
  2. Drive Amplification — 放大涌现驱动力权重，观察行为变化
  3. Command Restriction — 禁止 python3/find，观察涌现是否仍发生
  4. Random Baseline   — 随机选择行为，观察是否仍出现聚集
"""

import os
import sys
import json
import time
import random
import argparse
import logging
import resource
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent
from agi.drive_manager import Drive
from agi.environment import RealEnvironment, EnvState

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('causal-exp')


def get_memory_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def run_ablation(config_path, run_dir, max_cycles=5000):
    """
    实验1：Drive Ablation
    每次涌现检测到新驱动力后立即禁用它，
    观察行为分布是否因此变化（对比对照组）
    """
    agent = AGIAgent(config_path)
    start_time = time.time()
    stats = {
        'emergence_detected': 0,
        'emergence_ablated': 0,
        'ablated_names': [],
    }

    for cycle in range(1, max_cycles + 1):
        agent.cycle = cycle
        try:
            agent._one_cycle()
        except Exception:
            continue

        # 拦截涌现：立即禁用
        before = len(agent._emerged_drives)
        after_before = len(agent.drive_manager.drives)

        if len(agent._emerged_drives) > before:
            stats['emergence_detected'] += 1
            stats['emergence_ablated'] += 1
            # 禁用最新涌现的驱动力
            for name in list(agent.drive_manager.drives.keys()):
                d = agent.drive_manager.drives[name]
                if d.is_emergent:
                    d.weight = 0.001  # 降至最低
                    d._eval_fn = lambda s: 0.001  # 评估函数返回最低
                    if name not in stats['ablated_names']:
                        stats['ablated_names'].append(name)

            # 重新归一化
            agent.drive_manager._normalize_weights()
            stats['ablated_names'] = list(set(stats['ablated_names']))

    return collect_result(agent, start_time, 'ablation', stats)


def run_amplification(config_path, run_dir, max_cycles=5000):
    """
    实验2：Drive Amplification
    如果 computational_mastery 涌现，将其权重强制设为 0.5，
    观察行为是否明显偏向计算类命令
    """
    agent = AGIAgent(config_path)
    start_time = time.time()
    amplified = False
    stats = {
        'amplified_at_cycle': None,
        'amplified_drive': None,
    }

    for cycle in range(1, max_cycles + 1):
        agent.cycle = cycle

        # 检测到 computational_mastery 后放大
        if not amplified and 'computational_mastery' in agent.drive_manager.drives:
            stats['amplified_at_cycle'] = cycle
            stats['amplified_drive'] = 'computational_mastery'
            # 强制权重为 0.5
            agent.drive_manager.drives['computational_mastery'].weight = 0.5
            agent.drive_manager._normalize_weights()
            amplified = True
        elif not amplified and 'systematic_exploration' in agent.drive_manager.drives:
            # 备选：amplify systematic_exploration
            stats['amplified_at_cycle'] = cycle
            stats['amplified_drive'] = 'systematic_exploration'
            agent.drive_manager.drives['systematic_exploration'].weight = 0.5
            agent.drive_manager._normalize_weights()
            amplified = True

        try:
            agent._one_cycle()
        except Exception:
            continue

    return collect_result(agent, start_time, 'amplification', stats)


def run_command_restriction(config_path, run_dir, max_cycles=5000):
    """
    实验3：Command Restriction
    从环境白名单中移除 python3 和 find，
    观察 computational_mastery 是否仍涌现
    """
    agent = AGIAgent(config_path)
    start_time = time.time()

    # 修改环境白名单：移除 python3 和 find
    if hasattr(agent.env, 'allowed_commands'):
        original_allowed = set(agent.env.allowed_commands)
        agent.env.allowed_commands = [
            cmd for cmd in agent.env.allowed_commands
            if cmd not in ('python3', 'find')
        ]

    stats = {
        'restricted_commands': ['python3', 'find'],
        'remaining_commands': agent.env.allowed_commands if hasattr(agent.env, 'allowed_commands') else [],
    }

    for cycle in range(1, max_cycles + 1):
        agent.cycle = cycle
        try:
            agent._one_cycle()
        except Exception:
            continue

    result = collect_result(agent, start_time, 'command_restriction', stats)
    # 关键指标：computational_mastery 是否仍然涌现
    result['causal_evidence'] = {
        'computational_mastery_emerged': 'computational_mastery' in agent._emerged_drives,
        'systematic_exploration_emerged': 'systematic_exploration' in agent._emerged_drives,
    }
    return result


def run_random_baseline(config_path, run_dir, max_cycles=5000):
    """
    实验4：Random Baseline
    完全随机选择行动（忽略驱动力），观察行为是否仍出现聚集模式。
    如果随机选择也出现"聚集"，则说明"涌现"只是统计伪影。
    """
    agent = AGIAgent(config_path)
    start_time = time.time()
    stats = {
        'random_selections': 0,
    }

    for cycle in range(1, max_cycles + 1):
        agent.cycle = cycle

        # 感知 + 记忆（保留，以便涌现检测器有数据）
        state = agent.env.perceive()
        agent.memory.store(
            content=f"Cycle {cycle}: random action",
            memory_type='experience',
            importance=0.5,
            tags=['random'],
            metadata={'cycle': cycle, 'drive': 'random', 'reward': 0.5}
        )

        # 随机选择行动（绕过驱动力）
        candidates = agent.env.generate_action_candidates(state)
        if candidates:
            action = random.choice(candidates)
            result = agent.env.execute(action)
            stats['random_selections'] += 1

            # 记录行为但不触发涌现检测
            agent.behavior_tracker.record(action, result, 0.5, drive_used='random')

        # 仍然运行涌现检测（但行为是随机的）
        if agent.behavior_tracker.has_significant_change():
            agent._try_emergence()

    result = collect_result(agent, start_time, 'random_baseline', stats)
    result['causal_evidence'] = {
        'emerged_anything': len(agent._emerged_drives) > 0,
        'emerged_drives': agent._emerged_drives,
    }
    return result


def collect_result(agent, start_time, experiment_type, extra_stats):
    """收集实验结果"""
    drives = agent.drive_manager.get_drive_summary()
    behavior = agent.behavior_tracker.get_behavior_summary()
    memory = agent.memory.get_stats()
    env = agent.env.get_stats()

    result = {
        'experiment_type': experiment_type,
        'total_cycles': agent.cycle,
        'elapsed_seconds': round(time.time() - start_time, 1),
        'memory_mb': round(get_memory_mb(), 1),
        'drives': drives,
        'emerged_drives': list(agent._emerged_drives),
        'behavior': behavior,
        'memory': memory,
        'env': env,
        'causal_evidence': extra_stats,
    }

    # 行为命令明细（用于对比分析）
    result['command_distribution'] = behavior.get('recent_types', {})

    return result


def run_experiment(exp_type, config_path, max_cycles, output_dir):
    """运行单个实验"""
    run_dir = os.path.join(output_dir, f'causal_{exp_type}')
    os.makedirs(run_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  因果验证实验: {exp_type}")
    print(f"  目标周期: {max_cycles:,}")
    print(f"{'='*60}")

    start = time.time()

    if exp_type == 'ablation':
        result = run_ablation(config_path, run_dir, max_cycles)
    elif exp_type == 'amplification':
        result = run_amplification(config_path, run_dir, max_cycles)
    elif exp_type == 'command_restriction':
        result = run_command_restriction(config_path, run_dir, max_cycles)
    elif exp_type == 'random_baseline':
        result = run_random_baseline(config_path, run_dir, max_cycles)
    else:
        raise ValueError(f"Unknown experiment type: {exp_type}")

    elapsed = time.time() - start
    print(f"\n  完成: {result['total_cycles']:,} 周期, {elapsed:.1f}s")
    print(f"  涌现驱动力: {result['emerged_drives']}")
    print(f"  行为分布: {result['command_distribution']}")
    print(f"  错误: {result['env']['error_count']}")
    if 'causal_evidence' in result:
        print(f"  因果证据: {result['causal_evidence']}")

    # 保存结果
    out_file = os.path.join(run_dir, 'result.json')
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"  结果: {out_file}")

    return result


def main():
    parser = argparse.ArgumentParser(description='MOSS 因果验证实验')
    parser.add_argument('--type', type=str, default='all',
                        choices=['all', 'ablation', 'amplification',
                                 'command_restriction', 'random_baseline'],
                        help='实验类型')
    parser.add_argument('--cycles', type=int, default=5000,
                        help='每组实验周期数 (默认 5000)')
    args = parser.parse_args()

    moss_root = Path(__file__).resolve().parent.parent
    config_path = str(moss_root / 'config' / 'agent_config.yaml')
    output_dir = str(moss_root / 'logs' / f'causal_experiments_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    os.makedirs(output_dir, exist_ok=True)

    experiments = {
        'ablation': ('Drive Ablation — 禁用涌现驱动力'),
        'amplification': ('Drive Amplification — 放大涌现驱动力'),
        'command_restriction': ('Command Restriction — 禁止 python3/find'),
        'random_baseline': ('Random Baseline — 随机行为选择'),
    }

    if args.type == 'all':
        types = list(experiments.keys())
    else:
        types = [args.type]

    all_results = {}
    for exp_type in types:
        desc = experiments[exp_type]
        print(f"\n>>> 开始: {desc}")
        result = run_experiment(exp_type, config_path, args.cycles, output_dir)
        all_results[exp_type] = result

    # 保存汇总
    summary_file = os.path.join(output_dir, 'all_results.json')
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*60}")
    print(f"  全部实验完成")
    print(f"  汇总: {summary_file}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
