"""
测试驱动力竞争机制
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.drive_manager import DriveManager
import numpy as np

print("=" * 60)
print("测试驱动力竞争机制")
print("=" * 60)

# 创建 DriveManager
dm = DriveManager([
    {'name': 'survival', 'weight': 0.30, 'evaluator': 'builtin:survival'},
    {'name': 'curiosity', 'weight': 0.25, 'evaluator': 'builtin:curiosity'},
])

print("\n初始状态:")
for name, drive in dm.drives.items():
    print(f"  {name}: weight={drive.weight:.3f}, emergent={drive.is_emergent}")

# 模拟添加一个涌现驱动
print("\n添加涌现驱动 'test_emergent'...")
dm.add_emergent_drive(
    name='test_emergent',
    weight=0.15,
    description='测试涌现驱动',
    source_behaviors=['ls', 'cat'],
    novelty_score=0.7,
    causal_independence=0.5,
    eval_fn=lambda s: 0.5
)

print("\n添加后状态:")
for name, drive in dm.drives.items():
    print(f"  {name}: weight={drive.weight:.3f}, emergent={drive.is_emergent}")

# 模拟历史数据 - 让 test_emergent 表现很好
dm.drives['test_emergent'].history = [0.8] * 150  # 150 cycles 高表现

# 模拟 survival 表现一般
dm.drives['survival'].history = [0.4] * 200

# 模拟 curiosity 表现差
dm.drives['curiosity'].history = [0.2] * 200

print("\n模拟历史数据:")
print(f"  test_emergent: avg=0.8 (150 cycles)")
print(f"  survival: avg=0.4 (200 cycles)")
print(f"  curiosity: avg=0.2 (200 cycles)")

# 运行竞争机制
print("\n运行竞争机制...")
dm.update_drive_weights_competitive(performance_window=50)

print("\n竞争后状态:")
for name, drive in dm.drives.items():
    print(f"  {name}: weight={drive.weight:.3f}, emergent={drive.is_emergent}")

# 测试淘汰 - 让一个驱动权重极低
dm.drives['curiosity'].weight = 0.015
dm.drives['curiosity'].history = [0.1] * 50  # 差表现

print("\n模拟 curiosity 权重降至 0.015 (低于淘汰线 0.02)...")
dm.update_drive_weights_competitive(performance_window=50)

print("\n再次运行竞争后:")
if 'curiosity' in dm.drives:
    print(f"  curiosity: weight={dm.drives['curiosity'].weight:.3f} (存活)")
else:
    print("  curiosity: 已被淘汰 ✓")

for name, drive in dm.drives.items():
    print(f"  {name}: weight={drive.weight:.3f}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
