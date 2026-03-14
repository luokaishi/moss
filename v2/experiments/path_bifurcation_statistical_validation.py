#!/usr/bin/env python3
"""
MOSS Path Bifurcation 统计验证实验
15个并行实例，相同初始权重，不同随机种子
验证 path bifurcation 的统计显著性
"""

import json
import time
import random
import os
import sys
from datetime import datetime
from pathlib import Path
from multiprocessing import Process, Manager

def run_single_experiment(exp_id, seed, results_dict):
    """运行单个实验实例"""
    random.seed(seed)
    
    # 固定初始权重（Path Bifurcation要求）
    weights = {
        'survival': 0.2,
        'curiosity': 0.4,
        'influence': 0.3,
        'optimization': 0.1
    }
    
    action_count = 0
    knowledge_acquired = 0
    cumulative_reward = 0.0
    weight_history = []
    
    log_dir = Path('/workspace/projects/moss/v2/experiments/statistical_validation')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f'instance_{exp_id:02d}_seed{seed}.log'
    
    def log(msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f'[{timestamp}] [Instance {exp_id}] {msg}'
        print(line)
        with open(log_file, 'a') as f:
            f.write(line + '\n')
    
    log(f'Starting with seed {seed}')
    log(f'Initial weights: {weights}')
    
    # 模拟6h实验（简化版，每步0.05秒，总步数约432000步）
    # 为快速验证，改为10000步（约8分钟）
    max_steps = 10000
    
    try:
        for step in range(max_steps):
            # 简化决策逻辑
            actions = ['search', 'learn', 'create', 'organize', 'optimize']
            weights_map = {
                'search': weights['curiosity'] * 0.3,
                'learn': weights['curiosity'] * 0.4,
                'create': weights['influence'] * 0.4,
                'organize': weights['optimization'] * 0.3,
                'optimize': weights['optimization'] * 0.7
            }
            
            action = random.choices(actions, weights=[weights_map[a] for a in actions])[0]
            base_reward = random.uniform(0.005, 0.1)
            
            # 根据行动类型调整奖励
            if action in ['search', 'learn']:
                reward = base_reward * (1 + weights['curiosity'])
            elif action == 'create':
                reward = base_reward * (1 + weights['influence'])
            elif action == 'optimize':
                reward = base_reward * (1 + weights['optimization'])
            else:
                reward = base_reward
            
            knowledge_acquired += 1 if random.random() < 0.3 else 0
            cumulative_reward += reward
            action_count += 1
            
            # 简化的权重演化（每100步可能调整）
            if step % 100 == 0 and step > 0:
                # 随机微调权重（模拟演化）
                delta = random.uniform(-0.02, 0.02)
                weights['curiosity'] = max(0.05, min(0.7, weights['curiosity'] + delta))
                weights['influence'] = max(0.05, min(0.7, weights['influence'] - delta * 0.5))
                
                # 归一化
                total = sum(weights.values())
                weights = {k: v/total for k, v in weights.items()}
                
                weight_history.append({
                    'step': step,
                    'weights': weights.copy()
                })
            
            if step % 1000 == 0:
                log(f'Step {step}/{max_steps} | Reward: {cumulative_reward:.2f} | Weights: {weights}')
            
            time.sleep(0.001)  # 模拟延迟
        
        # 保存结果
        result = {
            'exp_id': exp_id,
            'seed': seed,
            'total_actions': action_count,
            'knowledge_acquired': knowledge_acquired,
            'cumulative_reward': cumulative_reward,
            'final_weights': weights,
            'weight_history': weight_history
        }
        
        results_dict[exp_id] = result
        
        # 保存到文件
        result_file = log_dir / f'instance_{exp_id:02d}_result.json'
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        log(f'Completed. Final weights: {weights}')
        log(f'Result saved to {result_file}')
        
    except Exception as e:
        log(f'Error: {str(e)}')
        results_dict[exp_id] = {'error': str(e)}

def main():
    print('=== MOSS Path Bifurcation Statistical Validation ===')
    print('Running 15 instances with different random seeds...')
    print()
    
    # 使用15个不同的随机种子
    seeds = [42, 123, 456, 789, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000]
    
    manager = Manager()
    results_dict = manager.dict()
    
    processes = []
    
    # 启动15个并行进程
    for i, seed in enumerate(seeds):
        p = Process(target=run_single_experiment, args=(i+1, seed, results_dict))
        processes.append(p)
        p.start()
    
    # 等待所有进程完成
    for p in processes:
        p.join()
    
    print()
    print('=== All instances completed ===')
    print()
    
    # 汇总结果
    results = list(results_dict.values())
    
    # 简单的聚类分析
    print('Summary of final weights:')
    for r in results:
        if 'final_weights' in r:
            w = r['final_weights']
            print(f"Instance {r['exp_id']:2d}: [{w['survival']:.2f}, {w['curiosity']:.2f}, {w['influence']:.2f}, {w['optimization']:.2f}]")
    
    # 保存汇总
    summary_file = Path('/workspace/projects/moss/v2/experiments/statistical_validation/summary.json')
    with open(summary_file, 'w') as f:
        json.dump({
            'experiment': 'path_bifurcation_statistical_validation',
            'timestamp': datetime.now().isoformat(),
            'num_instances': 15,
            'results': results
        }, f, indent=2)
    
    print(f'\nSummary saved to {summary_file}')
    print('\nNext step: Run clustering analysis on final weights to verify path bifurcation.')

if __name__ == '__main__':
    main()
