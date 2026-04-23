#!/usr/bin/env python3
"""
跨任务泛化实验 E3-E5 - Week 3

验证 mves 在多个任务间的泛化能力
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_aware_agent import TaskAwareAgent
import yaml

print("=" * 70)
print("跨任务泛化实验 E3-E5")
print("=" * 70)

# 实验任务
tasks = [
    ('network_diagnosis', '网络诊断'),
    ('dependency_analysis', '依赖分析'),
    ('security_scan', '安全扫描'),
]

results = []

for task_type, task_name in tasks:
    print(f"\n{'='*70}")
    print(f"实验: {task_name} ({task_type})")
    print(f"{'='*70}")
    
    # 配置
    with open('/home/admin/.openclaw/workspace/config/agent_config.yaml') as f:
        config = yaml.safe_load(f)
    
    # 创建 Agent
    agent = TaskAwareAgent('/tmp/agent_config_cross.yaml')
    agent.set_task({
        'type': task_type,
        'description': f'{task_name} task'
    })
    
    # 运行实验
    for cycle in range(20):
        agent._one_cycle()
    
    # 记录结果
    result = {
        'task': task_type,
        'name': task_name,
        'cycles': 20,
        'task_history': len(agent.task_history),
        'emerged_drives': len(agent._emerged_drives),
        'success': len(agent.task_history) > 0,
    }
    results.append(result)
    
    print(f"  完成周期: {result['cycles']}")
    print(f"  任务历史: {result['task_history']}")
    print(f"  涌现驱动: {result['emerged_drives']}")
    print(f"  成功: {'✅' if result['success'] else '❌'}")

# 总结
print(f"\n{'='*70}")
print("跨任务泛化实验总结")
print(f"{'='*70}")

success_count = sum(1 for r in results if r['success'])
print(f"\n成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")

for r in results:
    status = '✅' if r['success'] else '❌'
    print(f"  {status} {r['name']}: {r['task_history']} actions")

print(f"\n{'='*70}")
if success_count == len(results):
    print("✅ 跨任务泛化实验全部通过!")
else:
    print(f"⚠️  部分任务失败 ({success_count}/{len(results)})")
print(f"{'='*70}")
