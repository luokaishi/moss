#!/usr/bin/env python3
"""
稳定性验证 - 运行 5 次端到端测试
验证 Agent 能稳定达到 80%+ 准确率
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_aware_agent import TaskAwareAgent
import os
import shutil
import yaml
import random

print("=" * 70)
print("稳定性验证 - 5 次重复测试")
print("=" * 70)

results = []

for run in range(1, 6):
    print(f"\n{'='*70}")
    print(f"运行 {run}/5")
    print(f"{'='*70}")
    
    # 创建测试目录
    test_dir = f'/tmp/stability_test_{run}'
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # 随机生成测试文件
    random.seed(run * 100)
    file_types = {
        'images': ['.jpg', '.png', '.gif'],
        'documents': ['.pdf', '.txt', '.md', '.json'],
        'code': ['.py', '.js', '.sh', '.css', '.html']
    }
    
    test_files = []
    for folder, exts in file_types.items():
        for ext in exts:
            filename = f'file_{random.randint(1,999)}{ext}'
            test_files.append((filename, folder))
            open(f'{test_dir}/{filename}', 'w').close()
    
    print(f"测试文件: {len(test_files)} 个")
    
    # 配置
    config_path = '/home/admin/.openclaw/workspace/config/agent_config.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    config['environment']['workspace'] = test_dir
    config['environment']['workspace_limit'] = test_dir
    config['environment']['allowed_commands'].extend(['mv', 'mkdir'])
    
    temp_config = f'/tmp/stability_config_{run}.yaml'
    with open(temp_config, 'w') as f:
        yaml.dump(config, f)
    
    # 创建 Agent
    agent = TaskAwareAgent(temp_config)
    
    # 设置任务
    task_config = {
        'type': 'file_organization',
        'description': 'Organize files by type',
    }
    agent.set_task(task_config)
    
    # 运行
    max_cycles = 50
    for cycle in range(1, max_cycles + 1):
        agent._one_cycle()
        
        # 每 10 cycles 检查
        if cycle % 10 == 0:
            # 计算准确率
            expected = {f: folder for f, folder in test_files}
            correct = sum(1 for f, folder in expected.items() 
                         if os.path.exists(f'{test_dir}/{folder}/{f}'))
            accuracy = correct / len(expected)
            
            if accuracy >= 0.95:
                print(f"  Cycle {cycle}: 完成! 准确率 {accuracy*100:.0f}%")
                break
    else:
        # 最终检查
        expected = {f: folder for f, folder in test_files}
        correct = sum(1 for f, folder in expected.items() 
                     if os.path.exists(f'{test_dir}/{folder}/{f}'))
        accuracy = correct / len(expected)
        print(f"  最终: 准确率 {accuracy*100:.0f}%")
    
    results.append({
        'run': run,
        'accuracy': accuracy,
        'cycles': cycle if accuracy >= 0.95 else max_cycles,
        'success': accuracy >= 0.8
    })
    
    # 清理
    shutil.rmtree(test_dir)

# 统计
print(f"\n{'='*70}")
print("稳定性验证结果")
print(f"{'='*70}")

success_count = sum(1 for r in results if r['success'])
success_rate = success_count / len(results)

print(f"\n成功率: {success_count}/{len(results)} ({success_rate*100:.0f}%)")

accuracies = [r['accuracy'] for r in results]
import numpy as np
print(f"平均准确率: {np.mean(accuracies)*100:.1f}%")
print(f"最小准确率: {min(accuracies)*100:.1f}%")
print(f"最大准确率: {max(accuracies)*100:.1f}%")

cycles = [r['cycles'] for r in results]
print(f"平均完成周期: {np.mean(cycles):.1f}")

print(f"\n详细结果:")
for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"  {status} 运行 {r['run']}: {r['accuracy']*100:.0f}% ({r['cycles']} cycles)")

print(f"\n{'='*70}")
if success_rate >= 0.8:
    print(f"✅ 稳定性验证通过! ({success_rate*100:.0f}% >= 80%)")
else:
    print(f"❌ 稳定性验证失败 ({success_rate*100:.0f}% < 80%)")
print(f"{'='*70}")
