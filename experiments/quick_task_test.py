#!/usr/bin/env python3
"""
快速任务测试 - 强制任务动作执行
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.agent import AGIAgent
from agi.environment import RealEnvironment, EnvState
import os
import shutil
import yaml
import random

print("=" * 70)
print("快速任务测试 - 强制任务动作")
print("=" * 70)

# 创建测试目录
test_dir = '/tmp/quick_test'
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

# 创建测试文件
files = ['a.jpg', 'b.pdf', 'c.py']
for f in files:
    open(f'{test_dir}/{f}', 'w').close()

print(f"\n测试文件: {files}")

# 创建目标文件夹
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

temp_config = '/tmp/quick_config.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

# 创建 Agent
agent = AGIAgent(temp_config)

# 手动执行整理动作
print("\n执行整理动作...")

# 定义任务动作
task_actions = [
    {'type': 'shell', 'command': 'mv *.jpg images/ 2>/dev/null; echo done', 'description': 'Move images'},
    {'type': 'shell', 'command': 'mv *.pdf documents/ 2>/dev/null; echo done', 'description': 'Move documents'},
    {'type': 'shell', 'command': 'mv *.py code/ 2>/dev/null; echo done', 'description': 'Move code'},
]

success_count = 0
for action in task_actions:
    result = agent.env.execute(action)
    if result.get('success'):
        success_count += 1
        print(f"  ✅ {action['description']}: success")
    else:
        print(f"  ❌ {action['description']}: {result.get('error', 'failed')}")

# 检查结果
print("\n检查结果:")
for folder in ['images', 'documents', 'code']:
    path = f'{test_dir}/{folder}'
    if os.path.exists(path):
        files = os.listdir(path)
        print(f"  {folder}/: {files}")

root_files = [f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')]
print(f"  root: {root_files}")

# 准确率
expected = {'a.jpg': 'images', 'b.pdf': 'documents', 'c.py': 'code'}
correct = sum(1 for f, folder in expected.items() if os.path.exists(f'{test_dir}/{folder}/{f}'))
accuracy = correct / len(expected)

print(f"\n准确率: {correct}/{len(expected)} ({accuracy*100:.0f}%)")

# 清理
shutil.rmtree(test_dir)

print("\n" + "=" * 70)
if accuracy >= 0.8:
    print("✅ 任务完成!")
else:
    print(f"⚠️ 部分完成 ({accuracy*100:.0f}%)")
print("=" * 70)
