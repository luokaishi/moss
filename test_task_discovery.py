#!/usr/bin/env python3
"""
测试任务发现功能
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_discovery import TaskDiscovery

print("=" * 70)
print("任务发现功能测试")
print("=" * 70)

# 创建任务发现器
discovery = TaskDiscovery({
    'min_pattern_frequency': 3,
    'min_task_value': 0.5,
    'pattern_window': 100,
})

# 模拟 Agent 行为历史
action_history = [
    {'action': {'command': 'ls -la'}, 'result': {'success': True}},
    {'action': {'command': 'find . -name "*.py"'}, 'result': {'success': True}},
    {'action': {'command': 'find . -name "*.log"'}, 'result': {'success': True}},
    {'action': {'command': 'cat app.log'}, 'result': {'success': True}},
    {'action': {'command': 'grep "error" app.log'}, 'result': {'success': True}},
    {'action': {'command': 'ls -la'}, 'result': {'success': True}},
    {'action': {'command': 'find . -name "*.py"'}, 'result': {'success': True}},
    {'action': {'command': 'find . -name "*.txt"'}, 'result': {'success': True}},
    {'action': {'command': 'cat README.txt'}, 'result': {'success': True}},
    {'action': {'command': 'ls -la'}, 'result': {'success': True}},
    {'action': {'command': 'find . -name "*.py"'}, 'result': {'success': True}},
    {'action': {'command': 'grep "TODO" *.py'}, 'result': {'success': True}},
    {'action': {'command': 'ls -la'}, 'result': {'success': True}},
    {'action': {'command': 'find . -name "*.json"'}, 'result': {'success': True}},
    {'action': {'command': 'cat config.json'}, 'result': {'success': True}},
]

print(f"\n输入历史: {len(action_history)} 个动作")
print("动作列表:")
for i, h in enumerate(action_history, 1):
    cmd = h['action'].get('command', '')
    print(f"  {i}. {cmd}")

# 发现任务
print(f"\n{'='*70}")
print("开始任务发现...")
print(f"{'='*70}")

discovered_tasks = discovery.discover_from_history(action_history)

print(f"\n发现任务: {len(discovered_tasks)} 个")

for i, task in enumerate(discovered_tasks, 1):
    print(f"\n{i}. {task['name']}")
    print(f"   类型: {task['type']}")
    print(f"   描述: {task['description']}")
    print(f"   价值: {task['value']:.2f}")
    print(f"   模式: {task['pattern']['pattern']}")
    print(f"   频率: {task['pattern']['frequency']}")

# 验证
print(f"\n{'='*70}")
print("验证结果")
print(f"{'='*70}")

expected_patterns = ['ls', 'find', 'py', 'log']
found_patterns = [task['pattern']['pattern'] for task in discovered_tasks]

for pattern in expected_patterns:
    if pattern in found_patterns:
        print(f"✅ 发现预期模式: {pattern}")
    else:
        print(f"⚠️  未找到模式: {pattern}")

# 总结
print(f"\n{'='*70}")
if len(discovered_tasks) >= 3:
    print(f"✅ 任务发现成功! 发现 {len(discovered_tasks)} 个任务")
else:
    print(f"⚠️  发现任务较少 ({len(discovered_tasks)} 个)")
print(f"{'='*70}")
