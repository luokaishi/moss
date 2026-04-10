#!/usr/bin/env python3
"""
MOSS 快速 Demo
用法: python -m moss.demo
或安装后: moss-demo
"""

import os
import sys
import json
import time
from pathlib import Path

# 确保 moss 包可导入
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from moss.agi.agent import AGIAgent


def main():
    cycles = 200
    config_path = str(
        Path(__file__).resolve().parent / 'config' / 'agent_config.yaml'
    )
    if not os.path.exists(config_path):
        # 尝试从安装路径找到配置
        for candidate in [
            Path(__file__).resolve().parent / 'config' / 'agent_config.yaml',
            Path('/workspace') / 'config' / 'agent_config.yaml',
        ]:
            if candidate.exists():
                config_path = str(candidate)
                break
        else:
            print("ERROR: 找不到 config/agent_config.yaml")
            sys.exit(1)

    print("=" * 56)
    print("  MOSS — 自主涌现驱动力 AGI Agent Demo")
    print("=" * 56)
    print(f"配置: {config_path}")
    print(f"周期: {cycles}")
    print()

    # 创建 Agent
    agent = AGIAgent(config_path)
    print(f"初始驱动力: {agent.drive_manager.get_all_drive_names()}")
    print()

    # 运行
    start = time.time()
    errors = 0
    for i in range(1, cycles + 1):
        agent.cycle = i
        try:
            agent._one_cycle()
        except Exception:
            errors += 1

    elapsed = time.time() - start

    # 输出结果
    drives = agent.drive_manager.get_drive_summary()
    behavior = agent.behavior_tracker.get_behavior_summary()
    memory = agent.memory.get_stats()
    env = agent.env.get_stats()

    print(f"运行完成: {cycles} 周期, {elapsed:.1f}s, {errors} 错误")
    print()
    print("--- 驱动力状态 ---")
    for name, info in drives.items():
        tag = " [涌现]" if info['is_emergent'] else ""
        print(f"  {name}{tag}")
        print(f"    权重={info['weight']:.3f}  得分={info['score']:.3f}  "
              f"稳定性={info['stability']:.3f}")

    print()
    print("--- 涌现事件 ---")
    if agent._emerged_drives:
        for name in agent._emerged_drives:
            print(f"  ★ {name}")
    else:
        print("  (200 周期内未检测到涌现)")

    print()
    print("--- 行为统计 ---")
    print(f"  命令执行: {env['total_actions']} 次")
    print(f"  成功率:   {behavior['success_rate']:.1%}")
    print(f"  唯一命令: {behavior['unique_commands_ever']} 种")
    print(f"  记忆条目: {memory['total_records']} 条")

    # JSON 输出
    result = {
        'cycles': cycles,
        'elapsed_sec': round(elapsed, 2),
        'errors': errors,
        'drives': drives,
        'emerged': agent._emerged_drives,
        'behavior': behavior,
        'memory': memory,
    }
    out_file = Path(__file__).resolve().parent / 'demo_result.json'
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print()
    print(f"结果已保存: {out_file}")

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
