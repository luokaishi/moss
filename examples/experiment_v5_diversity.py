#!/usr/bin/env python3
"""
MOSS 行为多样性实验 v5.5.0
使用增强版环境 (RealEnvironmentV2)

目标: 将 shell 占比从 86% 降至 60% 以下
新增 action 类型: edit_file, exec_python, analyze_data, generate_report

使用:
    python experiment_v5_diversity.py --cycles 10000 --label diversity_test
"""

import os
import sys
import json
import time
import signal
import logging
import resource
import gc
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent
from agi.environment_v2 import RealEnvironmentV2, EnvState

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('experiment-diversity')


class DiversityAgent(AGIAgent):
    """使用 V2 环境的 Agent"""
    
    def __init__(self, config_path: str):
        # 先调用父类初始化
        super().__init__(config_path)
        
        # 替换环境为 V2
        from agi.environment_v2 import RealEnvironmentV2
        self.env = RealEnvironmentV2(self.config.get('environment', {}))
        logger.info("使用 RealEnvironmentV2 (行为多样性增强)")


def get_memory_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def save_diversity_report(run_dir: str, agent: DiversityAgent, cycle: int) -> str:
    """保存多样性分析报告"""
    stats = agent.env.get_stats()
    
    report = {
        'cycle': cycle,
        'timestamp': datetime.now().isoformat(),
        'action_distribution': stats['action_type_distribution'],
        'shell_ratio': stats['shell_ratio'],
        'diversity_metrics': {
            'total_types_used': len([v for v in stats['action_type_distribution'].values() if v > 0]),
            'shell_percentage': round(stats['shell_ratio'] * 100, 1),
            'non_shell_percentage': round((1 - stats['shell_ratio']) * 100, 1),
            'unique_commands': stats['unique_commands'],
            'analysis_count': stats['analysis_count'],
            'report_count': stats['report_count'],
        }
    }
    
    report_file = os.path.join(run_dir, f'diversity_report_{cycle:06d}.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_file


def main():
    parser = argparse.ArgumentParser(description='MOSS 行为多样性实验 v5.5.0')
    parser.add_argument('--cycles', type=int, default=10000, help='最大运行周期')
    parser.add_argument('--label', type=str, default='', help='实验标签')
    parser.add_argument('--report-interval', type=int, default=1000, help='多样性报告间隔')
    args = parser.parse_args()

    moss_root = Path(__file__).resolve().parent.parent
    config_path = str(moss_root / 'config' / 'agent_config.yaml')
    
    # 创建实验目录
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = f"_{args.label}" if args.label else ""
    run_dir = str(moss_root / 'logs' / f'experiment_v5_diversity_{run_id}{label}')
    os.makedirs(run_dir, exist_ok=True)
    
    # 日志
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    logger.info("=" * 70)
    logger.info("  MOSS 行为多样性实验 v5.5.0")
    logger.info("=" * 70)
    logger.info(f"目标: shell 占比 < 60%")
    logger.info(f"新增: edit_file, exec_python, analyze_data, generate_report")
    logger.info(f"目录: {run_dir}")
    
    # 创建 Agent
    agent = DiversityAgent(config_path)
    start_time = time.time()
    
    logger.info(f"初始驱动力: {agent.drive_manager.get_all_drive_names()}")
    logger.info(f"初始内存: {get_memory_mb():.1f} MB")
    logger.info("=" * 70)
    
    # 主循环
    emerged_log = list(agent._emerged_drives)
    
    try:
        for cycle in range(1, args.cycles + 1):
            agent.cycle = cycle
            
            try:
                agent._one_cycle()
            except Exception as e:
                logger.error(f"周期 {cycle} 执行错误: {e}")
                continue
            
            # 多样性报告
            if cycle % args.report_interval == 0:
                report_file = save_diversity_report(run_dir, agent, cycle)
                stats = agent.env.get_stats()
                shell_pct = stats['shell_ratio'] * 100
                
                logger.info(
                    f"[{cycle:>6,}] shell={shell_pct:.1f}% | "
                    f"types={len([v for v in stats['action_type_distribution'].values() if v > 0])} | "
                    f"unique={stats['unique_commands']} | "
                    f"analysis={stats['analysis_count']} | "
                    f"reports={stats['report_count']}"
                )
                
                # 目标检查
                if shell_pct < 60:
                    logger.info(f"✅ 目标达成: shell 占比 {shell_pct:.1f}% < 60%")
            
            # 涌现事件
            if len(agent._emerged_drives) > len(emerged_log):
                new_emerged = set(agent._emerged_drives) - set(emerged_log)
                for name in new_emerged:
                    logger.info(f"★★★ 涌现: {name} (周期 {cycle:,})")
                    emerged_log.append(name)
    
    except KeyboardInterrupt:
        logger.info("收到中断信号，保存状态...")
    
    # 最终报告
    logger.info("=" * 70)
    logger.info("生成最终多样性报告...")
    
    final_report = save_diversity_report(run_dir, agent, agent.cycle)
    stats = agent.env.get_stats()
    
    elapsed = (time.time() - start_time) / 3600.0
    logger.info(f"✓ 完成: {agent.cycle:,} 周期, {elapsed:.1f}h")
    logger.info(f"✓ shell 占比: {stats['shell_ratio']*100:.1f}%")
    logger.info(f"✓ 行动类型: {stats['action_type_distribution']}")
    logger.info(f"✓ 涌现: {agent._emerged_drives}")
    logger.info(f"✓ 报告: {final_report}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
