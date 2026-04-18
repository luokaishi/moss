import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# 读取检查点数据
checkpoint_dir = Path('/home/admin/.openclaw/workspace/logs/experiment_v6_longrun_20260418_113734_seed42')
output_dir = Path('/home/admin/.openclaw/workspace/docs/mves')
output_dir.mkdir(parents=True, exist_ok=True)

# 收集权重历史
weights_history = {
    'survival': [],
    'optimization': [],
    'influence': [],
    'curiosity': [],
    'composite_emergence_v1': [],
    'composite_emergence_v2': [],
    'composite_emergence_v3': [],
}
memory_history = []
cycles = []

for cp_file in sorted(checkpoint_dir.glob('checkpoint_*.json')):
    with open(cp_file, 'r') as f:
        cp = json.load(f)
    
    cycle = cp['cycle']
    cycles.append(cycle)
    
    state = cp.get('experiment_state', {})
    drives = state.get('drive_weights', {})
    
    for name in weights_history.keys():
        weights_history[name].append(drives.get(name, 0))
    
    mem_stats = state.get('memory_stats', {})
    memory_history.append(mem_stats.get('current_memory_mb', 0))

# 创建权重演化图
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 原生驱动权重
ax1 = axes[0, 0]
ax1.plot(cycles, weights_history['survival'], label='survival', linewidth=1.5)
ax1.plot(cycles, weights_history['optimization'], label='optimization', linewidth=1.5)
ax1.plot(cycles, weights_history['influence'], label='influence', linewidth=1.5)
ax1.plot(cycles, weights_history['curiosity'], label='curiosity', linewidth=1.5)
ax1.axvline(x=100, color='gray', linestyle='--', alpha=0.5, label='emergence_v1')
ax1.axvline(x=10000, color='orange', linestyle='--', alpha=0.5, label='emergence_v2')
ax1.axvline(x=30000, color='red', linestyle='--', alpha=0.5, label='emergence_v3')
ax1.set_xlabel('Cycle')
ax1.set_ylabel('Weight')
ax1.set_title('Native Drive Weights Evolution')
ax1.legend(loc='upper right', fontsize=8)
ax1.grid(True, alpha=0.3)

# 涌现驱动权重
ax2 = axes[0, 1]
ax2.plot(cycles, weights_history['composite_emergence_v1'], label='v1', linewidth=1.5, color='gray')
ax2.plot(cycles, weights_history['composite_emergence_v2'], label='v2', linewidth=1.5, color='orange')
ax2.plot(cycles, weights_history['composite_emergence_v3'], label='v3', linewidth=1.5, color='red')
ax2.axvline(x=100, color='gray', linestyle='--', alpha=0.5)
ax2.axvline(x=10000, color='orange', linestyle='--', alpha=0.5)
ax2.axvline(x=30000, color='red', linestyle='--', alpha=0.5)
ax2.set_xlabel('Cycle')
ax2.set_ylabel('Weight')
ax2.set_title('Emergent Drive Weights Evolution')
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.3)

# 内存使用
ax3 = axes[1, 0]
ax3.plot(cycles, memory_history, linewidth=1.5, color='green')
ax3.axhline(y=2048, color='red', linestyle='--', alpha=0.5, label='threshold (2GB)')
ax3.set_xlabel('Cycle')
ax3.set_ylabel('Memory (MB)')
ax3.set_title('Memory Usage Over Time')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 权重稳定性分析 (标准差)
ax4 = axes[1, 1]
window_size = 10
stability_data = {}
for name, weights in weights_history.items():
    if len(weights) >= window_size:
        rolling_std = [np.std(weights[max(0, i-window_size):i+1]) for i in range(len(weights))]
        stability_data[name] = rolling_std
        ax4.plot(cycles, rolling_std, label=name if 'emergence' in name else None, alpha=0.7)

ax4.set_xlabel('Cycle')
ax4.set_ylabel('Weight Std Dev (10-checkpoint window)')
ax4.set_title('Weight Stability (Lower = More Stable)')
ax4.legend(loc='upper right', fontsize=8)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'v6_longterm_analysis.png', dpi=150, bbox_inches='tight')
print(f"Saved visualization to {output_dir / 'v6_longterm_analysis.png'}")

# 计算统计指标
print("\n=== Weight Stability Analysis ===")
for name, weights in weights_history.items():
    if weights and any(w > 0 for w in weights):
        non_zero = [w for w in weights if w > 0.001]
        if non_zero:
            print(f"{name:25s}: mean={np.mean(non_zero):.4f}, std={np.std(non_zero):.4f}, min={np.min(non_zero):.4f}, max={np.max(non_zero):.4f}")

print("\n=== Memory Usage Analysis ===")
print(f"Peak memory: {np.max(memory_history):.2f} MB")
print(f"Mean memory: {np.mean(memory_history):.2f} MB")
print(f"Final memory: {memory_history[-1]:.2f} MB")
print(f"Memory growth rate: {(memory_history[-1] - memory_history[0]) / len(cycles):.4f} MB per 1000 cycles")
