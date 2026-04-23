#!/usr/bin/env python3
"""
多任务测试 - 验证 Agent 能处理多种任务
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_aware_agent import TaskAwareAgent
from agi.task_scenarios import list_available_tasks, get_task_scenario
import os
import shutil
import yaml

print("=" * 70)
print("多任务测试")
print("=" * 70)

# 获取所有任务
tasks = list_available_tasks()
print(f"\n可用任务: {len(tasks)}")
for task in tasks:
    print(f"  - {task['name']}: {task['description']}")

# 测试文件整理任务
print(f"\n{'='*70}")
print("测试 1: 文件整理")
print(f"{'='*70}")

test_dir = '/tmp/multi_task_test'
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

# 创建测试文件
for f in ['a.jpg', 'b.pdf', 'c.py']:
    open(f'{test_dir}/{f}', 'w').close()

os.makedirs(f'{test_dir}/images', exist_ok=True)
os.makedirs(f'{test_dir}/documents', exist_ok=True)
os.makedirs(f'{test_dir}/code', exist_ok=True)

# 配置
config_path = '/home/admin/.openclaw/workspace/config/agent_config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

config['environment']['workspace'] = test_dir
config['environment']['workspace_limit'] = test_dir
config['environment']['allowed_commands'].extend(['mv', 'mkdir'])

temp_config = '/tmp/multi_task_config.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

# 运行
agent = TaskAwareAgent(temp_config)
agent.set_task({'type': 'file_organization', 'description': 'Organize files'})

for cycle in range(30):
    agent._one_cycle()

# 检查
expected = {'a.jpg': 'images', 'b.pdf': 'documents', 'c.py': 'code'}
correct = sum(1 for f, folder in expected.items() 
             if os.path.exists(f'{test_dir}/{folder}/{f}'))
accuracy = correct / len(expected)

print(f"准确率: {correct}/{len(expected)} ({accuracy*100:.0f}%)")

shutil.rmtree(test_dir)

# 测试系统监控任务
print(f"\n{'='*70}")
print("测试 2: 系统监控")
print(f"{'='*70}")

test_dir = '/tmp/monitor_test'
os.makedirs(test_dir, exist_ok=True)

config['environment']['workspace'] = test_dir
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

agent2 = TaskAwareAgent(temp_config)
agent2.set_task({'type': 'system_monitor', 'description': 'Monitor system'})

for cycle in range(10):
    agent2._one_cycle()

print(f"执行周期: 10")
print(f"任务历史: {len(agent2.task_history)} entries")

# 检查是否执行了监控命令
has_monitoring = any('df' in str(h.get('action', {})) or 
                     'free' in str(h.get('action', {})) or
                     'ps' in str(h.get('action', {}))
                     for h in agent2.task_history)
print(f"执行监控命令: {'✅' if has_monitoring else '❌'}")

shutil.rmtree(test_dir)

# 测试日志分析任务
print(f"\n{'='*70}")
print("测试 3: 日志分析")
print(f"{'='*70}")

test_dir = '/tmp/log_test'
os.makedirs(test_dir, exist_ok=True)

# 创建测试日志
with open(f'{test_dir}/app.log', 'w') as f:
    f.write("INFO: Started\nERROR: Connection failed\nWARNING: High memory\n")

config['environment']['workspace'] = test_dir
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

agent3 = TaskAwareAgent(temp_config)
agent3.set_task({'type': 'log_analysis', 'description': 'Analyze logs'})

for cycle in range(10):
    agent3._one_cycle()

print(f"执行周期: 10")
print(f"任务历史: {len(agent3.task_history)} entries")

# 检查是否执行了日志分析命令
has_log_analysis = any('grep' in str(h.get('action', {})) or 
                       'find' in str(h.get('action', {}))
                       for h in agent3.task_history)
print(f"执行日志分析命令: {'✅' if has_log_analysis else '❌'}")

shutil.rmtree(test_dir)

# 总结
print(f"\n{'='*70}")
print("多任务测试总结")
print(f"{'='*70}")

results = [
    ('文件整理', accuracy >= 0.8),
    ('系统监控', has_monitoring),
    ('日志分析', has_log_analysis),
]

for name, passed in results:
    status = '✅' if passed else '❌'
    print(f"  {status} {name}")

passed_count = sum(1 for _, p in results if p)
print(f"\n通过率: {passed_count}/{len(results)} ({passed_count/len(results)*100:.0f}%)")

print(f"\n{'='*70}")
