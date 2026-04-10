#!/usr/bin/env python3
"""
MOSS 实验运行器 v3
支持断点续跑: python experiment_v3.py --resume checkpoint_xxx.json
支持参数覆盖: python experiment_v3.py --cycles 10000 --label my_experiment
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('experiment-v3')


class GracefulExiter:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info(f"收到信号 {signum}，优雅退出中...")
        self.shutdown = True


def get_memory_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def save_checkpoint(run_dir, agent, cycle, start_time, extra=None):
    try:
        cp = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': round((time.time() - start_time) / 3600.0, 3),
            'memory_mb': round(get_memory_mb(), 1),
            'drives': agent.drive_manager.get_drive_summary(),
            'behavior': agent.behavior_tracker.get_behavior_summary(),
            'memory': agent.memory.get_stats(),
            'env': agent.env.get_stats(),
            'emerged_drives': list(agent._emerged_drives),
        }
        if extra:
            cp.update(extra)
        cp_file = os.path.join(run_dir, f"checkpoint_{cycle:06d}.json")
        with open(cp_file, 'w') as f:
            json.dump(cp, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"检查点保存失败: {e}")
        return False


def save_final_report(run_dir, agent, run_id, start_time, initial_drives,
                      speed_log, mem_log, checkpoint_count):
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
        'performance': {
            'avg_cycles_per_sec': round(len(speed_log) / max(elapsed * 3600, 1), 2) if speed_log else 0,
            'peak_memory_mb': round(max(mem_log), 1) if mem_log else 0,
            'final_memory_mb': round(get_memory_mb(), 1),
            'checkpoint_count': checkpoint_count,
        },
    }
    report_file = os.path.join(run_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(final, f, indent=2, default=str)
    return report_file


def find_latest_checkpoint(run_dir):
    """找到目录中编号最大的检查点"""
    cps = sorted(Path(run_dir).glob('checkpoint_*.json'))
    if not cps:
        return None
    return str(cps[-1])


def main():
    parser = argparse.ArgumentParser(description='MOSS 实验运行器 v3')
    parser.add_argument('--resume', type=str, default=None,
                        help='从检查点恢复，提供 checkpoint_xxx.json 路径，或传 latest 自动找最新的')
    parser.add_argument('--cycles', type=int, default=10000,
                        help='最大运行周期 (默认 10000)')
    parser.add_argument('--label', type=str, default='',
                        help='实验标签，用于目录命名')
    parser.add_argument('--checkpoint-interval', type=int, default=1000,
                        help='检查点保存间隔 (默认 1000)')
    parser.add_argument('--report-interval', type=int, default=5000,
                        help='报告输出间隔 (默认 5000)')
    args = parser.parse_args()

    exiter = GracefulExiter()

    # 配置路径
    moss_root = Path(__file__).resolve().parent.parent
    config_path = str(moss_root / 'config' / 'agent_config.yaml')

    # 确定运行目录和起始周期
    resume_cycle = 0
    if args.resume:
        if args.resume == 'latest':
            # 找到 logs/ 下最新的实验目录
            exp_dirs = sorted(moss_root.glob('logs/experiment_v3_*'))
            if not exp_dirs:
                exp_dirs = sorted(moss_root.glob('logs/experiment_v2_*'))
            if not exp_dirs:
                logger.error("找不到已有的实验目录")
                sys.exit(1)
            latest_dir = exp_dirs[-1]
            cp_path = find_latest_checkpoint(latest_dir)
            if not cp_path:
                logger.error(f"在 {latest_dir} 中找不到检查点")
                sys.exit(1)
            run_dir = str(latest_dir)
            args.resume = cp_path
        else:
            run_dir = str(Path(args.resume).resolve().parent)

        # 加载检查点
        logger.info(f"从检查点恢复: {args.resume}")
        with open(args.resume) as f:
            checkpoint = json.load(f)
        resume_cycle = checkpoint['cycle']
        logger.info(f"恢复周期: {resume_cycle:,}")
    else:
        # 新实验
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        label = f"_{args.label}" if args.label else ""
        run_dir = str(moss_root / 'logs' / f'experiment_v3_{run_id}{label}')
        os.makedirs(run_dir, exist_ok=True)

    # 参数
    MAX_CYCLES = args.cycles
    CP_INTERVAL = args.checkpoint_interval
    REPORT_INTERVAL = args.report_interval

    # 日志
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(fh)

    logger.info("=" * 60)
    logger.info(f"  MOSS 实验运行器 v3")
    logger.info("=" * 60)
    logger.info(f"目录: {run_dir}")
    logger.info(f"最大周期: {MAX_CYCLES:,}")
    logger.info(f"起始周期: {resume_cycle:,}")
    logger.info(f"检查点间隔: {CP_INTERVAL:,}")

    # 创建 Agent
    agent = AGIAgent(config_path)
    start_time = time.time()
    emerged_log = list(agent._emerged_drives) if resume_cycle > 0 else []
    initial_drives = ['survival', 'curiosity', 'influence', 'optimization']
    checkpoint_count = 0
    speed_log = []
    mem_log = []
    last_speed_check = time.time()

    logger.info(f"初始驱动力: {agent.drive_manager.get_all_drive_names()}")
    logger.info(f"内存: {get_memory_mb():.1f} MB")

    # 主循环
    try:
        for cycle in range(resume_cycle + 1, MAX_CYCLES + 1):
            if exiter.shutdown:
                logger.info("收到终止信号，保存最终状态...")
                break

            agent.cycle = cycle

            try:
                agent._one_cycle()
            except Exception as e:
                logger.error(f"周期 {cycle} 执行错误: {e}")
                continue

            # 速度采样
            if cycle % 100 == 0:
                now = time.time()
                dt = now - last_speed_check
                speed_log.append(100.0 / max(dt, 0.001))
                last_speed_check = now

            # 检查点
            if cycle % CP_INTERVAL == 0:
                save_checkpoint(run_dir, agent, cycle, start_time)
                checkpoint_count += 1

            # 报告
            if cycle % REPORT_INTERVAL == 0:
                elapsed = (time.time() - start_time) / 3600.0
                mem_mb = get_memory_mb()
                mem_log.append(mem_mb)
                gc.collect()
                avg_speed = sum(speed_log[-500:]) / len(speed_log[-500:]) if speed_log else 0
                logger.info(
                    f"周期 {cycle:,}/{MAX_CYCLES:,} | "
                    f"{elapsed:.1f}h | "
                    f"{mem_mb:.0f}MB | "
                    f"{avg_speed:.1f}c/s | "
                    f"涌现 {agent._emerged_drives} | "
                    f"错误 {agent.env.get_stats()['error_count']}"
                )

            # 涌现事件
            if len(agent._emerged_drives) > len(emerged_log):
                new_emerged = set(agent._emerged_drives) - set(emerged_log)
                elapsed_now = (time.time() - start_time) / 3600.0
                for name in new_emerged:
                    logger.info(f"★ 涌现: {name} (周期 {cycle:,}, {elapsed_now:.1f}h)")
                    emerged_log.append(name)
                    save_checkpoint(run_dir, agent, cycle, start_time, extra={
                        'emergence_event': {'drive_name': name, 'all_emerged': list(agent._emerged_drives)}
                    })

    except Exception as e:
        logger.critical(f"实验异常终止: {e}", exc_info=True)

    # 最终报告
    logger.info("生成最终报告...")
    report_file = save_final_report(
        run_dir, agent, '', start_time, initial_drives,
        speed_log, mem_log, checkpoint_count
    )

    elapsed = (time.time() - start_time) / 3600.0
    logger.info("=" * 60)
    logger.info(f"完成: {agent.cycle:,} 周期, {elapsed:.1f}h")
    logger.info(f"涌现: {agent._emerged_drives}")
    logger.info(f"报告: {report_file}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
