#!/usr/bin/env python3
"""
实际应用场景 - 展示 Agent 在真实环境中的应用
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_aware_agent import TaskAwareAgent
import os
import shutil
import yaml

print("=" * 70)
print("MOSS v8.3.0 - 实际应用场景演示")
print("=" * 70)

# 场景 1: 开发环境整理
print(f"\n{'='*70}")
print("🛠️  场景 1: 开发环境整理")
print(f"{'='*70}")

test_dir = '/tmp/dev_project'
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

# 创建混乱的开发项目文件
files = [
    'main.py', 'utils.py', 'README.md', 'requirements.txt',
    'test_main.py', 'test_utils.py', 'logo.png', 'docs/guide.md',
    'config.json', '.gitignore', 'setup.py', 'LICENSE.txt'
]

for f in files:
    open(f'{test_dir}/{f}', 'w').write(f'# {f}\n')

print(f"初始文件: {len(files)} 个")
for f in files:
    print(f"  - {f}")

# 配置
config_path = '/home/admin/.openclaw/workspace/config/agent_config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

config['environment']['workspace'] = test_dir
config['environment']['workspace_limit'] = test_dir
config['environment']['allowed_commands'].extend(['mv', 'mkdir'])

temp_config = '/tmp/real_world_config.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

# 运行 Agent
agent = TaskAwareAgent(temp_config)
agent.set_task({
    'type': 'file_organization',
    'description': 'Organize development project files'
})

print(f"\n🤖 Agent 开始整理...")
for cycle in range(1, 41):
    agent._one_cycle()
    if cycle % 10 == 0:
        print(f"  Cycle {cycle}...")

# 检查结果
print(f"\n✅ 整理完成!")
for folder in ['images', 'documents', 'code']:
    folder_path = f'{test_dir}/{folder}'
    if os.path.exists(folder_path):
        folder_files = os.listdir(folder_path)
        if folder_files:
            print(f"  {folder}/: {', '.join(folder_files)}")

root_files = [f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')]
print(f"  根目录: {len(root_files)} 个文件")

shutil.rmtree(test_dir)

# 场景 2: 日志监控
print(f"\n{'='*70}")
print("📊 场景 2: 服务器日志监控")
print(f"{'='*70}")

test_dir = '/tmp/server_logs'
os.makedirs(test_dir, exist_ok=True)

# 创建模拟服务器日志
with open(f'{test_dir}/app.log', 'w') as f:
    f.write("2026-04-23 08:00:00 INFO Server started\n")
    f.write("2026-04-23 08:05:23 ERROR Database connection failed\n")
    f.write("2026-04-23 08:10:45 WARNING High memory usage: 85%\n")
    f.write("2026-04-23 08:15:12 ERROR Timeout after 30s\n")
    f.write("2026-04-23 08:20:00 INFO Server restarted\n")

config['environment']['workspace'] = test_dir
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

agent2 = TaskAwareAgent(temp_config)
agent2.set_task({
    'type': 'log_analysis',
    'description': 'Analyze server logs for errors'
})

print(f"🤖 Agent 开始分析日志...")
for cycle in range(1, 6):
    agent2._one_cycle()
    print(f"  Cycle {cycle}...")

print(f"\n✅ 分析完成!")
print(f"  执行了 {len(agent2.task_history)} 个分析动作")

shutil.rmtree(test_dir)

# 场景 3: 代码审查
print(f"\n{'='*70}")
print("🔍 场景 3: 代码质量检查")
print(f"{'='*70}")

test_dir = '/tmp/code_review'
os.makedirs(test_dir, exist_ok=True)

# 创建模拟代码文件
with open(f'{test_dir}/main.py', 'w') as f:
    f.write("# TODO: Refactor this function\n")
    f.write("def process_data(data):\n")
    f.write("    # FIXME: Handle edge cases\n")
    f.write("    return data\n")

with open(f'{test_dir}/utils.py', 'w') as f:
    f.write("import os\n")
    f.write("import sys\n")
    f.write("# TODO: Add error handling\n")

config['environment']['workspace'] = test_dir
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

agent3 = TaskAwareAgent(temp_config)
agent3.set_task({
    'type': 'code_review',
    'description': 'Review code for TODOs and quality'
})

print(f"🤖 Agent 开始代码审查...")
for cycle in range(1, 6):
    agent3._one_cycle()
    print(f"  Cycle {cycle}...")

print(f"\n✅ 审查完成!")
print(f"  执行了 {len(agent3.task_history)} 个审查动作")

shutil.rmtree(test_dir)

# 总结
print(f"\n{'='*70}")
print("🎉 实际应用场景演示完成!")
print(f"{'='*70}")

print(f"\n✅ MOSS v8.3.0 在实际场景中的应用:")
print(f"  1. 开发环境整理 - 自动分类项目文件")
print(f"  2. 服务器日志监控 - 分析错误和警告")
print(f"  3. 代码质量检查 - 发现 TODO 和 FIXME")

print(f"\n📊 核心能力:")
print(f"  - 任务感知: 根据任务类型选择动作")
print(f"  - 自动执行: 无需人工干预完成任务")
print(f"  - 多场景支持: 适应不同应用场景")

print(f"\n{'='*70}")
