#!/usr/bin/env python3
"""
分析长时间运行测试的检查点数据
"""

import json
import os
import glob
import matplotlib.pyplot as plt

def analyze_checkpoints():
    checkpoint_dir = "logs/long_run_test/checkpoints"
    checkpoint_files = sorted(glob.glob(os.path.join(checkpoint_dir, "checkpoint_*.json")))
    
    if not checkpoint_files:
        print("未找到检查点文件")
        return
    
    print(f"找到 {len(checkpoint_files)} 个检查点文件")
    
    # 提取关键指标
    cycles = []
    drive_counts = []
    emergent_counts = []
    memory_sizes = []
    success_rates = []
    action_counts = []
    
    for file_path in checkpoint_files:
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            cycle = data.get('cycle', 0)
            cycles.append(cycle)
            
            drives = data.get('drives', {})
            drive_counts.append(len(drives))
            
            emergent_drives = data.get('emerged_drives', [])
            emergent_counts.append(len(emergent_drives))
            
            memory = data.get('memory', {})
            memory_sizes.append(memory.get('total_records', 0))
            
            behavior = data.get('behavior', {})
            success_rates.append(behavior.get('success_rate', 0.0))
            
            env = data.get('env', {})
            action_counts.append(env.get('total_actions', 0))
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    # 打印摘要
    print("\n=== 检查点分析报告 ===")
    print(f"周期范围: {min(cycles)} - {max(cycles)}")
    print(f"最大驱动力数量: {max(drive_counts)}")
    print(f"最大涌现驱动力数量: {max(emergent_counts)}")
    print(f"最大记忆记录数: {max(memory_sizes)}")
    print(f"平均成功率: {sum(success_rates)/len(success_rates):.2%}")
    
    # 找到有驱动力的检查点
    drives_present = [i for i, count in enumerate(drive_counts) if count > 0]
    if drives_present:
        print(f"\n有驱动力的检查点: {len(drives_present)} 个")
        last_with_drives = drives_present[-1]
        print(f"最后一个有驱动力的检查点: 周期 {cycles[last_with_drives]}")
    
    # 打印每个检查点的驱动力数量
    print("\n周期 vs 驱动力数量:")
    for i in range(0, len(cycles), max(1, len(cycles)//10)):
        if i < len(cycles):
            print(f"  周期 {cycles[i]:5d}: {drive_counts[i]} 个驱动力, {emergent_counts[i]} 个涌现驱动力")
    
    # 生成简单的文本图表
    print("\n驱动力数量趋势:")
    for i in range(0, len(cycles), max(1, len(cycles)//20)):
        if i < len(cycles):
            bar = "█" * min(10, drive_counts[i])
            print(f"  周期 {cycles[i]:5d}: {bar} ({drive_counts[i]})")
    
    return {
        'cycles': cycles,
        'drive_counts': drive_counts,
        'emergent_counts': emergent_counts,
        'memory_sizes': memory_sizes,
        'success_rates': success_rates,
        'action_counts': action_counts
    }

if __name__ == '__main__':
    analyze_checkpoints()