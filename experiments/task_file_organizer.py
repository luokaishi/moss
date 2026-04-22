#!/usr/bin/env python3
"""
实用任务场景: 文件自动整理 Agent
让 Agent 学会整理 /workspace/downloads 目录
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.agent import AGIAgent
import os
import shutil
from datetime import datetime

print("=" * 70)
print("实用任务: 文件自动整理 Agent")
print("=" * 70)

# 创建测试目录结构
test_dir = '/tmp/test_downloads'
os.makedirs(test_dir, exist_ok=True)
os.makedirs(f'{test_dir}/images', exist_ok=True)
os.makedirs(f'{test_dir}/documents', exist_ok=True)
os.makedirs(f'{test_dir}/code', exist_ok=True)

# 创建一些测试文件
test_files = [
    ('photo1.jpg', 'images'),
    ('doc1.pdf', 'documents'),
    ('script.py', 'code'),
    ('readme.txt', 'documents'),
    ('image2.png', 'images'),
    ('main.js', 'code'),
]

for filename, _ in test_files:
    with open(f'{test_dir}/{filename}', 'w') as f:
        f.write(f'# Test file {filename}\n')

print(f"\n创建测试目录: {test_dir}")
print(f"测试文件: {len(test_files)} 个")

# 修改配置以使用测试目录
import yaml

config_path = '/home/admin/.openclaw/workspace/config/agent_config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

# 临时修改工作目录
original_workspace = config['environment']['workspace']
config['environment']['workspace'] = test_dir
config['environment']['workspace_limit'] = test_dir

# 添加文件整理相关命令
config['environment']['allowed_commands'].extend(['mv', 'file', 'mkdir'])

# 保存临时配置
temp_config = '/tmp/agent_config_file_org.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

print(f"\n启动 Agent 学习文件整理...")
print(f"目标: 将文件按类型分类到 images/documents/code 目录")
print()

# 创建 Agent
agent = AGIAgent(temp_config)

# 运行 100 cycles
for cycle in range(1, 101):
    agent._one_cycle()
    
    if cycle % 20 == 0:
        # 检查整理进度
        files_remaining = len([f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')])
        print(f"Cycle {cycle}: {files_remaining} files remaining in root")
        
        # 如果整理完成，提前结束
        if files_remaining == 0:
            print(f"\n✅ 整理完成于 cycle {cycle}!")
            break

# 评估结果
print("\n" + "=" * 70)
print("整理结果评估")
print("=" * 70)

# 统计各目录文件数
for folder in ['images', 'documents', 'code']:
    folder_path = f'{test_dir}/{folder}'
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        print(f"  {folder}/: {len(files)} files")
        for f in files:
            print(f"    - {f}")

# 检查根目录
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

# 检查是否涌现了新驱动力
print(f"\n  涌现驱动力: {len(agent._emerged_drives)}")
for drive_name in agent._emerged_drives:
    drive = agent.drive_manager.drives.get(drive_name)
    if drive:
        print(f"    - {drive_name}: weight={drive.weight:.3f}")

# 清理
print(f"\n  清理测试目录...")
shutil.rmtree(test_dir, ignore_errors=True)

# 恢复配置
config['environment']['workspace'] = original_workspace
config['environment']['workspace_limit'] = original_workspace
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
