"""
长期运行实验 - 验证 GP v8.2.1 改进效果
目标: 500 cycles，观察涌现质量
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.agent import AGIAgent
import logging
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)

print("=" * 60)
print("MOSS GP v8.2.1 长期运行实验")
print("=" * 60)
print(f"开始时间: {datetime.now().isoformat()}")
print("目标: 500 cycles")
print("改进: 自适应阈值 + 方差正则化 + 单终端惩罚")
print("=" * 60)

# 创建 Agent
agent = AGIAgent('/home/admin/.openclaw/workspace/config/agent_config.yaml')

# 运行
results = agent.run(max_cycles=500)

# 输出结果
print("\n" + "=" * 60)
print("实验完成!")
print("=" * 60)

print(f"\n总周期: {results['cycles']}")
print(f"运行时间: {results['duration']:.1f}s")
print(f"最终驱动力数量: {len(results['final_drives'])}")

print("\n驱动力详情:")
for drive in results['final_drives']:
    print(f"  - {drive['name']}: weight={drive['weight']:.3f}")
    if 'expr_string' in drive:
        print(f"    表达式: {drive['expr_string']}")
    if 'behavioral_gain' in drive:
        print(f"    behavioral_gain: {drive['behavioral_gain']:.3f}")

# 保存结果
output = {
    'version': 'v8.2.1',
    'timestamp': datetime.now().isoformat(),
    'config': 'improved_gp',
    'results': results
}

output_path = '/home/admin/.openclaw/workspace/experiments/longrun_v8.2.1_results.json'
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2, default=str)

print(f"\n结果已保存: {output_path}")
