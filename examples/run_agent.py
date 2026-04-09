#!/usr/bin/env python3
"""
AGI Agent 运行示例
演示Agent从配置启动、自主运行、涌现新驱动力
"""

import sys
import os

# 确保可以导入moss包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent


def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')

    # 创建Agent
    print("=" * 60)
    print("  MOSS AGI Agent - 自主涌现驱动力演示")
    print("=" * 60)
    print()

    agent = AGIAgent(config_path)

    # 运行Agent
    agent.run(max_cycles=100, verbose=True)


if __name__ == '__main__':
    main()
