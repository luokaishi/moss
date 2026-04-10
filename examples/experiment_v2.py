#!/usr/bin/env python3
"""
MOSS 长时间运行实验 v2
增强：内存监控、自适应检查点、速度追踪、心跳检测
"""

import os
import sys
import time
import json
import signal
import logging
import resource
import gc
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('experiment-v2')


class GracefulExiter:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info(f"收到信号 {signum}，优雅退出中...")
        self.shutdown = True


def get_memory_mb():
    """获取当前进程RSS内存(MB)"""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def save_checkpoint(run_dir, agent, cycle, start_time, extra=None):
    """保存检查点，含内存和性能数据"""
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
            'gc_collections': gc.collect(),
        },
    }
    report_file = os.path.join(run_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(final, f, indent=2, default=str)
    return report_file


def main():
    exiter = GracefulExiter()

    config_path = str(
        Path(__file__).resolve().parent.parent / 'config' / 'agent_config.yaml'
    )

    # ========== 参数配置 ==========
    MAX_CYCLES = 500000
    CHECKPOINT_INTERVAL = 1000       # 1000周期(从500提升，减少IO)
    REPORT_INTERVAL = 5000           # 5000周期报告
    MONITOR_INTERVAL = 10000         # 10000周期详细监控+GC
    HEARTBEAT_INTERVAL = 20000       # 20000周期心跳文件

    # ========== 实验目录 ==========
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = str(
        Path(__file__).resolve().parent.parent /
        'logs' / f'experiment_v2_{run_id}'
    )
    os.makedirs(run_dir, exist_ok=True)

    # 日志
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(fh)

    logger.info("=" * 60)
    logger.info("  MOSS 长时间运行实验 v2")
    logger.info("=" * 60)
    logger.info(f"实验 ID: {run_id}")
    logger.info(f"最大周期: {MAX_CYCLES:,}")
    logger.info(f"检查点间隔: {CHECKPOINT_INTERVAL:,}")
    logger.info(f"报告间隔: {REPORT_INTERVAL:,}")
    logger.info(f"监控间隔: {MONITOR_INTERVAL:,}")
    logger.info(f"心跳间隔: {HEARTBEAT_INTERVAL:,}")
    logger.info(f"日志目录: {run_dir}")

    # ========== 创建 Agent ==========
    agent = AGIAgent(config_path)
    start_time = time.time()
    emerged_log = []
    initial_drives = list(agent.drive_manager.get_all_drive_names())
    checkpoint_count = 0
    speed_log = []  # 每100周期采样速度
    mem_log = []
    last_speed_check = time.time()

    logger.info(f"初始驱动力: {initial_drives}")
    logger.info(f"初始内存: {get_memory_mb():.1f} MB")

    # ========== 主循环 ==========
    try:
        for cycle in range(1, MAX_CYCLES + 1):
            if exiter.shutdown:
                logger.info("收到终止信号，保存最终状态...")
                break

            agent.cycle = cycle

            # 执行周期
            try:
                agent._one_cycle()
            except Exception as e:
                logger.error(f"周期 {cycle} 执行错误: {e}")
                continue

            # 速度采样(每100周期)
            if cycle % 100 == 0:
                now = time.time()
                dt = now - last_speed_check
                speed_log.append(100.0 / max(dt, 0.001))
                last_speed_check = now

            # 检查点(每1000周期)
            if cycle % CHECKPOINT_INTERVAL == 0:
                save_checkpoint(run_dir, agent, cycle, start_time)
                checkpoint_count += 1
                if cycle % REPORT_INTERVAL == 0:
                    logger.info(
                        f"[CP] 周期 {cycle:,} | "
                        f"内存 {get_memory_mb():.0f}MB | "
                        f"速度 {speed_log[-1]:.1f}c/s"
                    )

            # 报告(每5000周期)
            if cycle % REPORT_INTERVAL == 0 and cycle % CHECKPOINT_INTERVAL != 0:
                elapsed = (time.time() - start_time) / 3600.0
                logger.info(f"--- 报告 周期 {cycle:,} ---")
                logger.info(f"  运行时间: {elapsed:.1f}h")
                logger.info(f"  驱动力: {len(agent.drive_manager.drives)} 个")
                logger.info(f"  涌现: {agent._emerged_drives}")
                logger.info(f"  记忆: {agent.memory.get_stats()['total_records']:,} 条")
                logger.info(f"  命令: {agent.env.get_stats()['total_actions']:,} 次")
                logger.info(f"  错误: {agent.env.get_stats()['error_count']} 次")
                logger.info(f"  内存: {get_memory_mb():.1f} MB")
                avg_speed = sum(speed_log[-500:]) / len(speed_log[-500:]) if speed_log else 0
                logger.info(f"  平均速度: {avg_speed:.1f} 周期/秒")

            # 详细监控(每10000周期) + GC
            if cycle % MONITOR_INTERVAL == 0:
                mem_mb = get_memory_mb()
                mem_log.append(mem_mb)
                gc.collect()
                mem_after = get_memory_mb()
                avg_speed = sum(speed_log[-500:]) / len(speed_log[-500:]) if speed_log else 0
                elapsed = (time.time() - start_time) / 3600.0
                logger.info(f"[MONITOR] 周期 {cycle:,}")
                logger.info(f"  内存: {mem_mb:.1f}MB → GC后 {mem_after:.1f}MB")
                logger.info(f"  检查点数: {checkpoint_count}")
                logger.info(f"  平均速度: {avg_speed:.1f}c/s")
                # 保存监控快照
                save_checkpoint(run_dir, agent, cycle, start_time, extra={
                    'monitor': {
                        'memory_before_gc_mb': round(mem_mb, 1),
                        'memory_after_gc_mb': round(mem_after, 1),
                        'avg_speed': round(avg_speed, 2),
                        'checkpoint_count': checkpoint_count,
                    }
                })

            # 心跳文件(每20000周期) - 证明进程存活
            if cycle % HEARTBEAT_INTERVAL == 0:
                hb = {
                    'cycle': cycle,
                    'timestamp': datetime.now().isoformat(),
                    'alive': True,
                    'memory_mb': round(get_memory_mb(), 1),
                }
                hb_file = os.path.join(run_dir, 'heartbeat.json')
                with open(hb_file, 'w') as f:
                    json.dump(hb, f)

            # 涌现事件记录
            if len(agent._emerged_drives) > len(emerged_log):
                new_emerged = set(agent._emerged_drives) - set(emerged_log)
                elapsed_now = (time.time() - start_time) / 3600.0
                for name in new_emerged:
                    logger.info(
                        f"  ★ 新驱动力涌现: {name} "
                        f"(周期 {cycle:,}, {elapsed_now:.1f}h)"
                    )
                    emerged_log.append(name)
                    # 涌现时立即保存检查点
                    save_checkpoint(run_dir, agent, cycle, start_time, extra={
                        'emergence_event': {
                            'drive_name': name,
                            'all_emerged': list(agent._emerged_drives),
                        }
                    })

    except Exception as e:
        logger.critical(f"实验异常终止: {e}", exc_info=True)

    # ========== 最终报告 ==========
    logger.info("正在生成最终报告...")
    report_file = save_final_report(
        run_dir, agent, run_id, start_time, initial_drives,
        speed_log, mem_log, checkpoint_count
    )

    elapsed = (time.time() - start_time) / 3600.0
    logger.info("=" * 60)
    logger.info("  实验结束")
    logger.info(f"  总周期: {agent.cycle:,}")
    logger.info(f"  运行时间: {elapsed:.1f} 小时")
    logger.info(f"  涌现驱动力: {agent._emerged_drives}")
    logger.info(f"  检查点数: {checkpoint_count}")
    logger.info(f"  最终内存: {get_memory_mb():.1f} MB")
    logger.info(f"  最终报告: {report_file}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
