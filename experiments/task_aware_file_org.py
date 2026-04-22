#!/usr/bin/env python3
"""
任务感知 Agent 文件整理测试
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_aware_agent import TaskAwareAgent
import os
import shutil
import yaml

print("=" * 70)
print("任务感知 Agent - 文件整理测试")
print("=" * 70)

# 创建测试目录
test_dir = '/tmp/test_downloads_v2'
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)
os.makedirs(f'{test_dir}/images')
os.makedirs(f'{test_dir}/documents')
os.makedirs(f'{test_dir}/code')

# 创建测试文件
test_files = [
    ('photo1.jpg', 'images'),
    ('doc1.pdf', 'documents'),
    ('script.py', 'code'),
    ('readme.txt', 'documents'),
    ('image2.png', 'images'),
    ('main.js', 'code'),
]

for filename, target_folder in test_files:
    with open(f'{test_dir}/{filename}', 'w') as f:
        f.write(f'# Test file {filename}\n')

print(f"\n创建测试目录: {test_dir}")
print(f"测试文件: {len(test_files)} 个")
for f, folder in test_files:
    print(f"  {f} -> {folder}/")

# 修改配置
config_path = '/home/admin/.openclaw/workspace/config/agent_config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

config['environment']['workspace'] = test_dir
config['environment']['workspace_limit'] = test_dir
config['environment']['allowed_commands'].extend(['mv', 'file', 'mkdir', 'cp'])

temp_config = '/tmp/agent_config_task.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

# 创建 Agent
agent = TaskAwareAgent(temp_config)

# 设置任务
task_config = {
    'type': 'file_organization',
    'description': 'Organize files by type into appropriate folders',
    'initial_state': {'files_in_root': 6},
    'target_state': {'files_in_root': 0, 'organized': True},
}
agent.set_task(task_config)

print(f"\n启动 Agent，任务: 文件整理")
print(f"目标: 将文件按类型分类到 images/, documents/, code/")
print()

# 运行 100 cycles
for cycle in range(1, 101):
    agent._one_cycle()
    
    if cycle % 20 == 0:
        # 检查进度
        root_files = [f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')]
        print(f"Cycle {cycle}: {len(root_files)} files in root")
        
        if len(root_files) == 0:
            print(f"\n✅ 整理完成于 cycle {cycle}!")
            break

# 评估结果
print("\n" + "=" * 70)
print("整理结果评估")
print("=" * 70)

for folder in ['images', 'documents', 'code']:
    folder_path = f'{test_dir}/{folder}'
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        print(f"  {folder}/: {len(files)} files")
        for f in files:
            print(f"    - {f}")

root_files = [f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')]
print(f"\n  根目录剩余: {len(root_files)} files")

# 计算准确率
expected = {'photo1.jpg': 'images', 'image2.png': 'images',
            'doc1.pdf': 'documents', 'readme.txt': 'documents',
            'script.py': 'code', 'main.js': 'code'}

correct = 0
total = 0
for filename, expected_folder in expected.items():
    expected_path = f'{test_dir}/{expected_folder}/{filename}'
    if os.path.exists(expected_path):
        correct += 1
    total += 1

accuracy = correct / total if total > 0 else 0
print(f"\n  分类准确率: {correct}/{total} ({accuracy*100:.1f}%)")

# 任务历史
print(f"\n  任务历史记录: {len(agent.task_history)} entries")
if agent.task_history:
    avg_reward = sum(h['reward']['total'] for h in agent.task_history) / len(agent.task_history)
    print(f"  平均奖励: {avg_reward:.3f}")

# 涌现驱动力
print(f"\n  涌现驱动力: {len(agent._emerged_drives)}")
for drive_name in agent._emerged_drives:
    drive = agent.drive_manager.drives.get(drive_name)
    if drive:
        print(f"    - {drive_name}: weight={drive.weight:.3f}")

# 清理
print(f"\n  清理测试目录...")
shutil.rmtree(test_dir, ignore_errors=True)

# 恢复配置
config['environment']['workspace'] = '/workspace'
config['environment']['workspace_limit'] = '/workspace'
with open(config_path, 'w') as f:
    yaml.dump(config, f)

print("\n" + "=" * 70)
if accuracy >= 0.8:
    print("✅ 任务完成良好!")
elif accuracy >= 0.5:
    print("⚠️ 任务完成一般")
else:
    print("❌ 任务完成不佳")
print("=" * 70)
