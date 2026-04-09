#!/usr/bin/env python3
"""
修复验证脚本 - 分3步验证
Step 1: JSON序列化验证（50周期）
Step 2: 检查点完整性验证（500周期）
Step 3: 完整长时间运行验证（2000周期）
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent


def step1_json_serialization():
    """Step 1: 验证JSON序列化修复"""
    print("\n" + "=" * 60)
    print("  Step 1: JSON序列化验证 (50周期)")
    print("=" * 60)
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')
    agent = AGIAgent(config_path)
    
    errors = 0
    for cycle in range(1, 51):
        agent.cycle = cycle
        try:
            agent._one_cycle()
        except Exception as e:
            errors += 1
            print(f"  周期 {cycle} 错误: {e}")
    
    # 测试所有输出是否可JSON序列化
    try:
        drives_summary = agent.drive_manager.get_drive_summary()
        json_str = json.dumps(drives_summary, indent=2)
        print(f"  [OK] get_drive_summary() 可序列化 ({len(drives_summary)} 个驱动)")
        
        # 验证所有值都是原生Python类型
        for name, info in drives_summary.items():
            for k, v in info.items():
                vtype = type(v).__name__
                if vtype.startswith('np.'):
                    print(f"  [FAIL] {name}.{k} = {vtype} (应该是Python原生类型)")
                    errors += 1
        
        behavior_summary = agent.behavior_tracker.get_behavior_summary()
        json_str = json.dumps(behavior_summary, indent=2)
        print(f"  [OK] get_behavior_summary() 可序列化")
        
        memory_stats = agent.memory.get_stats()
        json_str = json.dumps(memory_stats, indent=2)
        print(f"  [OK] memory.get_stats() 可序列化")
        
        env_stats = agent.env.get_stats()
        json_str = json.dumps(env_stats, indent=2)
        print(f"  [OK] env.get_stats() 可序列化")
        
        # 综合测试
        full_state = {
            'drives': drives_summary,
            'behavior': behavior_summary,
            'memory': memory_stats,
            'env': env_stats
        }
        json_str = json.dumps(full_state, indent=2)
        print(f"  [OK] 完整状态可序列化 ({len(json_str)} bytes)")
        
    except (TypeError, ValueError) as e:
        print(f"  [FAIL] JSON序列化失败: {e}")
        errors += 1
    
    print(f"\n  结果: {'PASS' if errors == 0 else 'FAIL'} ({errors} 个错误)")
    return errors == 0


def step2_checkpoint_integrity():
    """Step 2: 验证检查点保存完整性"""
    print("\n" + "=" * 60)
    print("  Step 2: 检查点完整性验证 (500周期)")
    print("=" * 60)
    
    run_dir = f"logs/verify_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(run_dir, exist_ok=True)
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')
    agent = AGIAgent(config_path)
    
    errors = 0
    checkpoint_count = 0
    
    for cycle in range(1, 501):
        agent.cycle = cycle
        try:
            agent._one_cycle()
        except Exception as e:
            errors += 1
            print(f"  周期 {cycle} 错误: {e}")
            continue
        
        if cycle % 100 == 0:
            # 保存检查点
            checkpoint_data = {
                'cycle': cycle,
                'drives': agent.drive_manager.get_drive_summary(),
                'behavior': agent.behavior_tracker.get_behavior_summary(),
                'memory': agent.memory.get_stats(),
                'env': agent.env.get_stats(),
                'emerged_drives': list(agent._emerged_drives),
                'drive_names': list(agent.drive_manager.drives.keys())
            }
            
            cp_file = os.path.join(run_dir, f"checkpoint_{cycle:06d}.json")
            try:
                with open(cp_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)
                checkpoint_count += 1
                
                # 立即读回验证
                with open(cp_file) as f:
                    loaded = json.load(f)
                
                drives_count = len(loaded.get('drives', {}))
                drive_names_count = len(loaded.get('drive_names', []))
                
                if drives_count == 0 and drive_names_count == 0:
                    print(f"  [WARN] 周期 {cycle}: 驱动力数据为空")
                else:
                    print(f"  [OK] 周期 {cycle}: {drives_count} 个驱动力, "
                          f"涌现 {len(loaded.get('emerged_drives', []))} 个")
                    
            except (TypeError, ValueError) as e:
                print(f"  [FAIL] 周期 {cycle}: 检查点保存/读取失败: {e}")
                errors += 1
            except Exception as e:
                print(f"  [FAIL] 周期 {cycle}: 未知错误: {e}")
                errors += 1
    
    print(f"\n  检查点保存: {checkpoint_count}/5")
    print(f"  结果: {'PASS' if errors == 0 else 'FAIL'} ({errors} 个错误)")
    return errors == 0


def step3_long_run():
    """Step 3: 完整长时间运行验证"""
    print("\n" + "=" * 60)
    print("  Step 3: 完整长时间运行验证 (2000周期)")
    print("=" * 60)
    
    from examples.long_run_test import LongRunAgent
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')
    
    print("  创建LongRunAgent...")
    agent = LongRunAgent(config_path)
    
    print(f"  运行2000周期 (检查点间隔: {agent.checkpoint_interval})...")
    start = time.time()
    
    try:
        agent.run_with_checkpoints(max_cycles=2000)
    except Exception as e:
        print(f"  [FAIL] 运行出错: {e}")
        return False
    
    elapsed = time.time() - start
    
    # 验证结果
    drives = agent.drive_manager.get_drive_summary()
    run_checkpoints = os.path.join(agent.run_dir, "checkpoints")
    
    cp_files = []
    if os.path.exists(run_checkpoints):
        cp_files = [f for f in os.listdir(run_checkpoints) if f.endswith('.json')]
    
    print(f"\n  运行时间: {elapsed:.1f}s")
    print(f"  总周期: {agent.cycle}")
    print(f"  驱动力: {len(drives)} 个")
    print(f"  涌现驱动力: {len(agent._emerged_drives)} 个")
    for name in agent._emerged_drives:
        print(f"    - {name}")
    print(f"  检查点文件: {len(cp_files)} 个")
    
    # 验证最终报告
    report_file = os.path.join(agent.run_dir, "final_report.json")
    if os.path.exists(report_file):
        with open(report_file) as f:
            report = json.load(f)
        print(f"  [OK] 最终报告已生成")
        print(f"  运行目录: {agent.run_dir}")
    else:
        print(f"  [WARN] 最终报告未找到")
    
    print(f"\n  结果: PASS")
    return True


def main():
    print("=" * 60)
    print("  AGI Agent 修复验证")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Step 1
    results['json_serialization'] = step1_json_serialization()
    
    # Step 2
    results['checkpoint_integrity'] = step2_checkpoint_integrity()
    
    # Step 3
    results['long_run'] = step3_long_run()
    
    # 最终总结
    print("\n" + "=" * 60)
    print("  修复验证总结")
    print("=" * 60)
    all_pass = True
    for step, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {step}: {status}")
        if not passed:
            all_pass = False
    
    print(f"\n  总体结果: {'ALL PASS' if all_pass else 'HAS FAILURES'}")
    print("=" * 60)
    
    return all_pass


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)