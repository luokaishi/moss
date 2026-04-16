#!/usr/bin/env python3
"""
MOSS 涌现驱动效用优化实验 v5.5.0-P1
验证涌现驱动权重可达 0.20+

使用:
    python experiment_v5_utility.py --cycles 5000 --label utility_v1
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
from agi.genetic_programmer_v2 import GeneticProgrammerV2, DriveManagerV2

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('experiment-utility')


def main():
    parser = argparse.ArgumentParser(description='MOSS 涌现驱动效用优化实验 v5.5.0-P1')
    parser.add_argument('--cycles', type=int, default=5000, help='运行周期')
    parser.add_argument('--label', type=str, default='', help='实验标签')
    args = parser.parse_args()

    moss_root = Path(__file__).resolve().parent.parent
    config_path = str(moss_root / 'config' / 'agent_config.yaml')
    
    # 创建实验目录
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = f"_{args.label}" if args.label else ""
    run_dir = str(moss_root / 'logs' / f'experiment_v5_utility_{run_id}{label}')
    os.makedirs(run_dir, exist_ok=True)
    
    # 日志
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    logger.info("=" * 70)
    logger.info("  MOSS 涌现驱动效用优化实验 v5.5.0-P1")
    logger.info("=" * 70)
    logger.info(f"目标: 涌现驱动权重 >= 0.20")
    logger.info(f"周期: {args.cycles:,}")
    logger.info(f"目录: {run_dir}")
    
    # 创建 Agent
    agent = AGIAgent(config_path)
    
    # V2: 使用增强版 GP
    gp_v2 = GeneticProgrammerV2({
        'population_size': 100,
        'generations': 50,
        'practicality_weight': 0.25,  # 新增实用性权重
        'practicality_threshold': 0.30,
        'min_weight_target': 0.20,
    })
    
    # V2: 使用增强版 DriveManager
    drive_manager_v2 = DriveManagerV2({
        'utility_threshold': 0.15,
        'min_weight_threshold': 0.05,
        'max_emerged_drives': 5,
    })
    
    start_time = time.time()
    
    logger.info(f"初始驱动力: {agent.drive_manager.get_all_drive_names()}")
    logger.info("=" * 70)
    
    # 统计
    emerged_count = 0
    high_weight_drives = []  # 权重 >= 0.20 的驱动
    
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
                    
                    logger.info(f"★★★ 涌现: {new_emerged} (周期 {cycle}, 权重 {weight:.3f})")
                    
                    # V2: 检查是否达到目标权重
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
                emerged_weights = {k: v.get('weight', 0) for k, v in drive_summary.items() 
                                 if k in agent._emerged_drives}
                
                logger.info(
                    f"[{cycle:>5,}] "
                    f"涌现: {agent._emerged_drives} | "
                    f"权重: {emerged_weights}"
                )
                
                # V2: 统计高权重驱动
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
        'experiment': 'utility_optimization',
        'total_cycles': agent.cycle,
        'emerged_drives': list(agent._emerged_drives),
        'drive_weights': {k: v.get('weight', 0) for k, v in drive_summary.items()},
        'high_weight_drives': high_weight_drives,
        'target_achieved': len(high_weight_drives) > 0,
        'target_count': len(high_weight_drives),
    }
    
    report_file = os.path.join(run_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    elapsed = (time.time() - start_time) / 3600.0
    logger.info(f"✓ 完成: {agent.cycle:,} 周期, {elapsed:.1f}h")
    logger.info(f"✓ 涌现: {agent._emerged_drives}")
    logger.info(f"✓ 高权重(>=0.20): {len(high_weight_drives)}个")
    logger.info(f"✓ 报告: {report_file}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
