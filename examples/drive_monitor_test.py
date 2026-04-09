#!/usr/bin/env python3
"""
测试驱动力数据丢失问题
运行500周期并观察驱动力状态
"""

import os
import sys
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent


def monitor_drives():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')
    
    print("=" * 60)
    print("  驱动力数据丢失测试")
    print("=" * 60)
    
    agent = AGIAgent(config_path)
    
    # 手动运行多个周期
    for cycle in range(1, 501):
        try:
            # 获取当前驱动力状态
            if cycle % 50 == 0:
                drives = agent.drive_manager.drives
                # 直接访问drives字典来检查
                print(f"\n周期 {cycle}:")
                print(f"  drives字典长度: {len(drives)}")
                
                if drives:
                    for name, drive in drives.items():
                        print(f"    {name}: weight={drive.weight:.3f}, emergent={drive.is_emergent}")
                else:
                    print("  !!! 警告: drives字典为空 !!!")
                
                # 检查get_drive_summary()的输出
                summary = agent.drive_manager.get_drive_summary()
                print(f"  get_drive_summary()输出: {len(summary)} 个驱动力")
            
            # 执行一个周期
            agent.cycle = cycle
            agent._one_cycle()
            
        except Exception as e:
            print(f"周期 {cycle} 出错: {e}")
            break
    
    # 最终报告
    print("\n" + "=" * 60)
    print("  测试完成 - 最终状态")
    print("=" * 60)
    
    drives = agent.drive_manager.drives
    summary = agent.drive_manager.get_drive_summary()
    
    print(f"总周期数: {agent.cycle}")
    print(f"drives字典长度: {len(drives)}")
    print(f"get_drive_summary()输出: {len(summary)} 个驱动力")
    
    if drives:
        print("\n当前驱动力:")
        for name, drive in drives.items():
            print(f"  {name}: weight={drive.weight:.3f}, emergent={drive.is_emergent}")
    else:
        print("\n!!! 严重问题: drives字典为空 !!!")
        print("检查Agent是否异常重置了驱动力")
    
    # 保存当前状态用于分析
    test_dir = "logs/drive_test"
    os.makedirs(test_dir, exist_ok=True)
    state_file = os.path.join(test_dir, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    state = {
        'cycle': agent.cycle,
        'drives': {},
        'summary': summary
    }
    
    for name, drive in drives.items():
        state['drives'][name] = {
            'weight': drive.weight,
            'score': drive.score,
            'history_len': len(drive.history),
            'is_emergent': drive.is_emergent
        }
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\n状态已保存到: {state_file}")
    print("\n测试完成时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


if __name__ == '__main__':
    monitor_drives()