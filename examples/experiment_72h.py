#!/usr/bin/env python3
"""
72h 真实长时间运行实验
目标：验证 AGI Agent 在真实环境中的长期演化稳定性
"""

import os
import sys
import time
import json
import signal
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('72h-experiment')


class GracefulExiter:
    """优雅退出处理"""
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info(f"收到信号 {signum}，准备优雅退出...")
        self.shutdown = True


def main():
    exiter = GracefulExiter()

    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.yaml')

    # 实验配置
    MAX_CYCLES = 100000  # 72h 约 100K+ 周期
    CHECKPOINT_INTERVAL = 500  # 每 500 周期保存
    REPORT_INTERVAL = 5000  # 每 5000 周期输出报告

    # 实验目录
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', f'experiment_72h_{run_id}')
    os.makedirs(run_dir, exist_ok=True)

    # 日志文件
    log_file = os.path.join(run_dir, 'experiment.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(fh)

    logger.info("=" * 60)
    logger.info("  MOSS 72h 真实长时间运行实验")
    logger.info("=" * 60)
    logger.info(f"实验 ID: {run_id}")
    logger.info(f"最大周期: {MAX_CYCLES}")
    logger.info(f"检查点间隔: {CHECKPOINT_INTERVAL}")
    logger.info(f"报告间隔: {REPORT_INTERVAL}")
    logger.info(f"日志目录: {run_dir}")

    # 创建 Agent
    agent = AGIAgent(config_path)
    start_time = time.time()
    emerged_log = []

    # 记录初始状态
    initial_drives = list(agent.drive_manager.get_all_drive_names())
    logger.info(f"初始驱动力: {initial_drives}")

    try:
        for cycle in range(1, MAX_CYCLES + 1):
            if exiter.shutdown:
                logger.info("收到终止信号，保存最终状态并退出")
                break

            agent.cycle = cycle

            # 执行一个周期
            try:
                agent._one_cycle()
            except Exception as e:
                logger.error(f"周期 {cycle} 执行错误: {e}")
                continue

            # 检查点保存
            if cycle % CHECKPOINT_INTERVAL == 0:
                try:
                    cp = {
                        'cycle': cycle,
                        'timestamp': datetime.now().isoformat(),
                        'elapsed_hours': (time.time() - start_time) / 3600.0,
                        'drives': agent.drive_manager.get_drive_summary(),
                        'behavior': agent.behavior_tracker.get_behavior_summary(),
                        'memory': agent.memory.get_stats(),
                        'env': agent.env.get_stats(),
                        'emerged_drives': list(agent._emerged_drives),
                    }
                    cp_file = os.path.join(run_dir, f"checkpoint_{cycle:06d}.json")
                    with open(cp_file, 'w') as f:
                        json.dump(cp, f, indent=2)
                    logger.info(f"[CP] 周期 {cycle} 检查点已保存")
                except Exception as e:
                    logger.error(f"检查点保存失败: {e}")

            # 周期性报告
            if cycle % REPORT_INTERVAL == 0:
                elapsed = (time.time() - start_time) / 3600.0
                drives_summary = agent.drive_manager.get_drive_summary()
                logger.info(f"--- 报告 周期 {cycle} ---")
                logger.info(f"  运行时间: {elapsed:.1f}h")
                logger.info(f"  驱动力: {len(drives_summary)} 个")
                logger.info(f"  涌现: {agent._emerged_drives}")
                logger.info(f"  记忆: {agent.memory.get_stats()['total_records']} 条")
                logger.info(f"  命令: {agent.env.get_stats()['total_actions']} 次")
                logger.info(f"  错误: {agent.env.get_stats()['error_count']} 次")

            # 涌现事件记录
            if len(agent._emerged_drives) > len(emerged_log):
                new_emerged = set(agent._emerged_drives) - set(emerged_log)
                elapsed_now = (time.time() - start_time) / 3600.0
                for name in new_emerged:
                    logger.info(f"  ★ 新驱动力涌现: {name} (周期 {cycle}, {elapsed_now:.1f}h)")
                    emerged_log.append(name)

    except Exception as e:
        logger.critical(f"实验异常终止: {e}")

    # 保存最终报告
    elapsed = (time.time() - start_time) / 3600.0
    final = {
        'experiment_id': run_id,
        'total_cycles': agent.cycle,
        'elapsed_hours': round(elapsed, 2),
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'end_time': datetime.now().isoformat(),
        'initial_drives': initial_drives,
        'final_drives': agent.drive_manager.get_drive_summary(),
        'emerged_drives': list(agent._emerged_drives),
        'behavior': agent.behavior_tracker.get_behavior_summary(),
        'memory': agent.memory.get_stats(),
        'env': agent.env.get_stats(),
    }
    report_file = os.path.join(run_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(final, f, indent=2, default=str)

    logger.info("=" * 60)
    logger.info("  实验结束")
    logger.info(f"  总周期: {agent.cycle}")
    logger.info(f"  运行时间: {elapsed:.1f} 小时")
    logger.info(f"  涌现驱动力: {agent._emerged_drives}")
    logger.info(f"  最终报告: {report_file}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
