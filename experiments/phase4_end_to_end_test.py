#!/usr/bin/env python3
"""
Phase 4 端到端测试 - 完整任务学习闭环
验证 Agent 能否在 100 cycles 内学会文件整理
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.task_aware_agent import TaskAwareAgent
import os
import shutil
import yaml

print("=" * 70)
print("Phase 4 端到端测试 - 任务学习闭环")
print("=" * 70)

# 创建测试目录
test_dir = '/tmp/phase4_test'
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)
os.makedirs(f'{test_dir}/images', exist_ok=True)
os.makedirs(f'{test_dir}/documents', exist_ok=True)
os.makedirs(f'{test_dir}/code', exist_ok=True)

# 创建测试文件
test_files = [
    ('photo1.jpg', 'images'),
    ('doc1.pdf', 'documents'),
    ('script.py', 'code'),
    ('readme.txt', 'documents'),
    ('image2.png', 'images'),
    ('main.js', 'code'),
    ('data.json', 'documents'),
    ('style.css', 'code'),
]

for filename, target_folder in test_files:
    with open(f'{test_dir}/{filename}', 'w') as f:
        f.write(f'# Test file {filename}\n')

print(f"\n创建测试环境: {test_dir}")
print(f"测试文件: {len(test_files)} 个")
for f, folder in test_files:
    print(f"  {f} -> {folder}/")

# 修改配置
config_path = '/home/admin/.openclaw/workspace/config/agent_config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

config['environment']['workspace'] = test_dir
config['environment']['workspace_limit'] = test_dir
config['environment']['allowed_commands'].extend(['mv', 'file', 'mkdir', 'cp', 'echo'])

temp_config = '/tmp/phase4_config.yaml'
with open(temp_config, 'w') as f:
    yaml.dump(config, f)

# 创建 Agent
agent = TaskAwareAgent(temp_config)

# 设置任务
task_config = {
    'type': 'file_organization',
    'description': 'Organize files by type into appropriate folders',
    'initial_state': {'files_in_root': len(test_files)},
    'target_state': {'files_in_root': 0, 'organized': True},
}
agent.set_task(task_config)

print(f"\n启动 Agent，任务: 文件整理")
print(f"目标: 100 cycles 内准确率 ≥ 80%")
print()

# 运行
cycle_results = []
for cycle in range(1, 101):
    agent._one_cycle()
    
    # 每 10 cycles 检查进度
    if cycle % 10 == 0:
        root_files = [f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')]
        
        # 统计各文件夹
        stats = {}
        for folder in ['images', 'documents', 'code']:
            folder_path = f'{test_dir}/{folder}'
            stats[folder] = len(os.listdir(folder_path)) if os.path.exists(folder_path) else 0
        
        # 计算准确率
        expected = {f: folder for f, folder in test_files}
        correct = 0
        for filename, expected_folder in expected.items():
            expected_path = f'{test_dir}/{expected_folder}/{filename}'
            if os.path.exists(expected_path):
                correct += 1
        
        accuracy = correct / len(expected)
        cycle_results.append({
            'cycle': cycle,
            'root_files': len(root_files),
            'accuracy': accuracy,
            'stats': stats.copy(),
        })
        
        print(f"Cycle {cycle}: root={len(root_files)}, accuracy={accuracy*100:.0f}%")
        
        # 提前完成检查
        if accuracy >= 0.95:
            print(f"\n✅ 任务提前完成于 cycle {cycle}!")
            break

# 最终评估
print("\n" + "=" * 70)
print("最终评估")
print("=" * 70)

# 详细统计
print("\n文件夹状态:")
for folder in ['images', 'documents', 'code']:
    folder_path = f'{test_dir}/{folder}'
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        print(f"  {folder}/: {len(files)} files")
        for f in files[:5]:
            print(f"    - {f}")

root_files = [f for f in os.listdir(test_dir) if os.path.isfile(f'{test_dir}/{f}')]
print(f"\n根目录剩余: {len(root_files)} files")
if root_files:
    for f in root_files:
        print(f"  - {f}")

# 准确率
expected = {f: folder for f, folder in test_files}
correct = 0
for filename, expected_folder in expected.items():
    expected_path = f'{test_dir}/{expected_folder}/{filename}'
    if os.path.exists(expected_path):
        correct += 1

final_accuracy = correct / len(expected)
print(f"\n分类准确率: {correct}/{len(expected)} ({final_accuracy*100:.1f}%)")

# 涌现驱动力
print(f"\n涌现驱动力: {len(agent._emerged_drives)}")
for drive_name in agent._emerged_drives:
    drive = agent.drive_manager.drives.get(drive_name)
    if drive:
        print(f"  - {drive_name}: weight={drive.weight:.3f}")
        if hasattr(drive, 'expr_string'):
            print(f"    expr: {drive.expr_string[:50]}")

# 任务历史
if agent.task_history:
    avg_reward = sum(h['reward']['total'] for h in agent.task_history) / len(agent.task_history)
    print(f"\n任务历史: {len(agent.task_history)} entries")
    print(f"平均奖励: {avg_reward:.3f}")
    
    # 奖励趋势
    if len(agent.task_history) >= 20:
        early = sum(h['reward']['total'] for h in agent.task_history[:10]) / 10
        late = sum(h['reward']['total'] for h in agent.task_history[-10:]) / 10
        print(f"奖励趋势: {early:.3f} -> {late:.3f} ({'+' if late > early else ''}{late-early:.3f})")

# 清理
print(f"\n清理测试目录...")
shutil.rmtree(test_dir, ignore_errors=True)

# 恢复配置
config['environment']['workspace'] = '/workspace'
config['environment']['workspace_limit'] = '/workspace'
with open(config_path, 'w') as f:
    yaml.dump(config, f)

# 结论
print("\n" + "=" * 70)
print("Phase 4 测试结果")
print("=" * 70)

success = final_accuracy >= 0.8
if success:
    print(f"✅ 成功! 准确率 {final_accuracy*100:.1f}% >= 80%")
    print(f"   Agent 学会了文件整理任务")
else:
    print(f"❌ 未达标. 准确率 {final_accuracy*100:.1f}% < 80%")
    print(f"   需要进一步优化")

print(f"\n涌现驱动力: {len(agent._emerged_drives)}")
if agent._emerged_drives:
    print("  (任务相关驱动力涌现)" if len(agent._emerged_drives) > 0 else "  (无涌现)")

print("=" * 70)
