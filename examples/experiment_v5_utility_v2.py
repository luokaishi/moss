#!/usr/bin/env python3
"""
MOSS 涌现驱动效用优化实验 V2 v5.5.1
优化参数，目标: 涌现驱动权重 >= 0.20

改进:
- survival初始权重: 0.20 (降低)
- practicality_weight: 0.30 (增加)
- 目标周期: 10,000 (增加)

使用:
    python experiment_v5_utility_v2.py --cycles 10000 --label utility_v2
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('experiment-utility-v2')


def main():
    parser = argparse.ArgumentParser(description='MOSS 涌现驱动效用优化实验 V2 v5.5.1')
    parser.add_argument('--cycles', type=int, default=10000, help='运行周期')
    parser.add_argument('--label', type=str, default='', help='实验标签')
    args = parser.parse_args()

    moss_root = Path(__file__).resolve().parent.parent
    
    # V2: 使用优化配置
    config_path = str(moss_root / 'config' / 'agent_config_v2.yaml')
    
    # 创建实验目录
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = f"_{args.label}" if args.label else ""
    run_dir = str(moss_root / 'logs' / f'experiment_v5_utility_v2_{run_id}{label}')
    os.makedirs(run_dir, exist_ok=True)
    
    # 日志
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    logger.info("=" * 70)
    logger.info("  MOSS 涌现驱动效用优化实验 V2 v5.5.1")
    logger.info("=" * 70)
    logger.info(f"改进:")
    logger.info(f"  - survival初始权重: 0.20 (降低)")
    logger.info(f"  - practicality_weight: 0.30 (增加)")
    logger.info(f"  - 目标周期: {args.cycles:,}")
    logger.info(f"目标: 涌现驱动权重 >= 0.20")
    logger.info(f"目录: {run_dir}")
    
    # 创建 Agent (使用V2配置)
    agent = AGIAgent(config_path)
    
    start_time = time.time()
    
    logger.info(f"初始驱动力: {agent.drive_manager.get_all_drive_names()}")
    logger.info(f"初始权重: {agent.drive_manager.get_drive_summary()}")
    logger.info("=" * 70)
    
    # 统计
    emerged_count = 0
    high_weight_drives = []
    max_weight_seen = 0.0
    
    # 主循环
    try:
        for cycle in range(1, args.cycles + 1):
            agent.cycle = cycle
            
            try:
                agent._one_cycle()
            except Exception as e:
                logger.error(f"周期 {cycle} 执行错误: {e}")
                continue
            
            # 检查涌现
            if len(agent._emerged_drives) > emerged_count:
                new_emerged = agent._emerged_drives[-1]
                emerged_count = len(agent._emerged_drives)
                
                # 获取驱动权重
                drive_summary = agent.drive_manager.get_drive_summary()
                if new_emerged in drive_summary:
                    weight = drive_summary[new_emerged].get('weight', 0)
                    max_weight_seen = max(max_weight_seen, weight)
                    
                    logger.info(f"★★★ 涌现: {new_emerged} (周期 {cycle}, 权重 {weight:.3f})")
                    
                    if weight >= 0.20:
                        logger.info(f"✅ 目标达成: 涌现驱动权重 {weight:.3f} >= 0.20")
                        high_weight_drives.append({
                            'name': new_emerged,
                            'cycle': cycle,
                            'weight': weight
                        })
            
            # 定期报告
            if cycle % 1000 == 0:
                drive_summary = agent.drive_manager.get_drive_summary()
                
                # V2: 获取所有权重
                all_weights = {k: v.get('weight', 0) for k, v in drive_summary.items()}
                emerged_weights = {k: v for k, v in all_weights.items() 
                                 if k in agent._emerged_drives}
                
                logger.info(
                    f"[{cycle:>5,}] "
                    f"涌现: {agent._emerged_drives} | "
                    f"权重: {emerged_weights} | "
                    f"最大: {max_weight_seen:.3f}"
                )
                
                # V2: 统计
                high_count = sum(1 for w in emerged_weights.values() if w >= 0.20)
                if high_count > 0:
                    logger.info(f"✅ 高权重涌现驱动: {high_count}个 (>=0.20)")
    
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    
    # 最终报告
    logger.info("=" * 70)
    logger.info("生成最终报告...")
    
    drive_summary = agent.drive_manager.get_drive_summary()
    final_report = {
        'experiment': 'utility_optimization_v2',
        'config': 'agent_config_v2.yaml',
        'improvements': {
            'survival_weight': 0.20,
            'practicality_weight': 0.30,
            'target_cycles': args.cycles,
        },
        'total_cycles': agent.cycle,
        'emerged_drives': list(agent._emerged_drives),
        'drive_weights': {k: v.get('weight', 0) for k, v in drive_summary.items()},
        'high_weight_drives': high_weight_drives,
        'max_weight_seen': max_weight_seen,
        'target_achieved': len(high_weight_drives) > 0,
        'target_count': len(high_weight_drives),
    }
    
    report_file = os.path.join(run_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    elapsed = (time.time() - start_time) / 3600.0
    logger.info(f"✓ 完成: {agent.cycle:,} 周期, {elapsed:.1f}h")
    logger.info(f"✓ 涌现: {agent._emerged_drives}")
    logger.info(f"✓ 最大权重: {max_weight_seen:.3f}")
    logger.info(f"✓ 高权重(>=0.20): {len(high_weight_drives)}个")
    logger.info(f"✓ 报告: {report_file}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
