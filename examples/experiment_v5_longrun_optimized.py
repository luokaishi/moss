#!/usr/bin/env python3
"""
MOSS 长周期实验运行器 v5.5.1 - 优化版
支持 100,000+ 周期连续运行 - 增强GC和内存管理

优化点:
- 更激进的GC策略 (间隔250周期)
- 检查点文件压缩
- 内存使用上限控制
- 速度优化

使用:
    python experiment_v5_longrun_optimized.py --cycles 100000 --label longrun_opt
"""

import os
import sys
import json
import time
import signal
import logging
import resource
import gc
import gzip
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('experiment-v5-opt')


class MemoryOptimizer:
    """内存优化器 - 增强版"""
    
    def __init__(self, gc_threshold_mb: float = 30.0, gc_interval_cycles: int = 250, 
                 mem_limit_mb: float = 800.0):
        self.gc_threshold_mb = gc_threshold_mb
        self.gc_interval_cycles = gc_interval_cycles
        self.mem_limit_mb = mem_limit_mb
        self.last_gc_cycle = 0
        self.mem_log: list = []
        self.leak_detected = False
        self.gc_count = 0
        
    def check_and_gc(self, cycle: int, current_mem_mb: float) -> Dict[str, Any]:
        """检查内存并执行 GC 如果需要"""
        result = {'gc_triggered': False, 'mem_before': current_mem_mb, 'mem_after': current_mem_mb}
        
        self.mem_log.append((cycle, current_mem_mb))
        
        # 保留最近 500 个采样点
        if len(self.mem_log) > 500:
            self.mem_log = self.mem_log[-500:]
        
        # 触发条件 1: 按周期 (更频繁)
        if cycle - self.last_gc_cycle >= self.gc_interval_cycles:
            result['gc_triggered'] = True
            result['reason'] = 'interval'
        
        # 触发条件 2: 内存增长超过阈值 (更敏感)
        if len(self.mem_log) >= 50:
            recent = self.mem_log[-50:]
            avg_recent = sum(m for _, m in recent) / len(recent)
            older = self.mem_log[:25]
            avg_older = sum(m for _, m in older) / len(older)
            
            if avg_recent - avg_older > self.gc_threshold_mb:
                result['gc_triggered'] = True
                result['reason'] = 'growth'
                result['growth_mb'] = avg_recent - avg_older
        
        # 触发条件 3: 内存接近上限
        if current_mem_mb > self.mem_limit_mb * 0.8:
            result['gc_triggered'] = True
            result['reason'] = 'limit'
        
        if result['gc_triggered']:
            gc.collect()
            gc.collect()  # 双重GC确保清理
            result['mem_after'] = get_memory_mb()
            result['freed_mb'] = result['mem_before'] - result['mem_after']
            self.last_gc_cycle = cycle
            self.gc_count += 1
            
            if result.get('freed_mb', 0) > 10:
                logger.debug(f"GC at cycle {cycle}: freed {result.get('freed_mb', 0):.1f}MB")
        
        return result
    
    def detect_leak(self, window_cycles: int = 3000) -> Optional[Dict]:
        """检测内存泄漏 - 更快检测"""
        if len(self.mem_log) < window_cycles // 20:
            return None
        
        recent = self.mem_log[-window_cycles//20:]
        if len(recent) < 10:
            return None
        
        cycles = [c for c, _ in recent]
        mems = [m for _, m in recent]
        
        n = len(cycles)
        sum_x = sum(cycles)
        sum_y = sum(mems)
        sum_xy = sum(c * m for c, m in recent)
        sum_x2 = sum(c * c for c in cycles)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.005:  # 更低的阈值
            return {
                'leak_detected': True,
                'slope_mb_per_cycle': slope,
                'projected_100k_mb': slope * 100000,
                'severity': 'high' if slope > 0.03 else 'medium'
            }
        
        return {'leak_detected': False, 'slope_mb_per_cycle': slope}


class CheckpointManager:
    """智能检查点管理器 - 支持压缩"""
    
    def __init__(self, run_dir: str, cycle_interval: int = 1000, time_interval_min: int = 30):
        self.run_dir = run_dir
        self.cycle_interval = cycle_interval
        self.time_interval_min = time_interval_min
        self.last_checkpoint_cycle = 0
        self.last_checkpoint_time = time.time()
        self.checkpoint_count = 0
        
    def should_save(self, cycle: int) -> bool:
        if cycle - self.last_checkpoint_cycle >= self.cycle_interval:
            return True
        
        elapsed_min = (time.time() - self.last_checkpoint_time) / 60
        if elapsed_min >= self.time_interval_min:
            return True
        
        return False
    
    def mark_saved(self, cycle: int):
        self.last_checkpoint_cycle = cycle
        self.last_checkpoint_time = time.time()
        self.checkpoint_count += 1


class GracefulExiter:
    def __init__(self):
        self.shutdown = False
        self.signal_received = None
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info(f"收到信号 {signum}，优雅退出中...")
        self.shutdown = True
        self.signal_received = signum


def get_memory_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def save_checkpoint(run_dir: str, agent: AGIAgent, cycle: int, start_time: float,
                   mem_optimizer: MemoryOptimizer, extra: Optional[Dict] = None,
                   compress: bool = True) -> str:
    """保存检查点 - 支持压缩"""
    try:
        cp = {
            'version': 'v5.5.1-opt',
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': round((time.time() - start_time) / 3600.0, 3),
            'memory_mb': round(get_memory_mb(), 1),
            'drives': agent.drive_manager.get_drive_summary(),
            'behavior': agent.behavior_tracker.get_behavior_summary(),
            'memory_stats': agent.memory.get_stats(),
            'env': agent.env.get_stats(),
            'emerged_drives': list(agent._emerged_drives),
            'mem_optimizer': {
                'leak_status': mem_optimizer.detect_leak(),
                'last_gc_cycle': mem_optimizer.last_gc_cycle,
                'gc_count': mem_optimizer.gc_count,
            }
        }
        if extra:
            cp.update(extra)
        
        cp_file = os.path.join(run_dir, f"checkpoint_{cycle:08d}.json")
        
        if compress and cp['memory_mb'] > 200:
            # 大内存时使用压缩
            cp_file += '.gz'
            with gzip.open(cp_file, 'wt') as f:
                json.dump(cp, f, indent=2, default=str)
        else:
            with open(cp_file, 'w') as f:
                json.dump(cp, f, indent=2, default=str)
        
        size_mb = os.path.getsize(cp_file) / (1024 * 1024)
        logger.info(f"✓ 检查点: {cp_file} ({cp['memory_mb']:.0f}MB, 文件{size_mb:.1f}MB)")
        return cp_file
    except Exception as e:
        logger.error(f"检查点保存失败: {e}")
        raise


def save_final_report(run_dir: str, agent: AGIAgent, run_id: str, start_time: float,
                     initial_drives: list, mem_optimizer: MemoryOptimizer,
                     performance_stats: Dict) -> str:
    elapsed = (time.time() - start_time) / 3600.0
    
    mem_log = mem_optimizer.mem_log
    mem_stats = {
        'peak_mb': round(max(m for _, m in mem_log), 1) if mem_log else 0,
        'final_mb': round(get_memory_mb(), 1),
        'avg_mb': round(sum(m for _, m in mem_log) / len(mem_log), 1) if mem_log else 0,
        'growth_rate_mb_per_1k': round((mem_log[-1][1] - mem_log[0][1]) / (mem_log[-1][0] - mem_log[0][0]) * 1000, 2) if len(mem_log) > 1 else 0,
        'gc_count': mem_optimizer.gc_count,
    }
    
    final = {
        'version': 'v5.5.1-opt',
        'experiment_id': run_id,
        'total_cycles': agent.cycle,
        'elapsed_hours': round(elapsed, 2),
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'end_time': datetime.now().isoformat(),
        'initial_drives': initial_drives,
        'final_drives': agent.drive_manager.get_drive_summary(),
        'emerged_drives': list(agent._emerged_drives),
        'behavior': agent.behavior_tracker.get_behavior_summary(),
        'memory_stats': agent.memory.get_stats(),
        'env_stats': agent.env.get_stats(),
        'performance': performance_stats,
        'memory_analysis': mem_stats,
        'leak_detection': mem_optimizer.detect_leak(),
    }
    
    report_file = os.path.join(run_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(final, f, indent=2, default=str)
    return report_file


def find_latest_checkpoint(run_dir: str) -> Optional[str]:
    cps = sorted(Path(run_dir).glob('checkpoint_*.json*'))
    if not cps:
        return None
    return str(cps[-1])


def find_latest_experiment_dir(moss_root: Path) -> Optional[Path]:
    exp_dirs = []
    for pattern in ['experiment_v5_*', 'experiment_v3_*', 'experiment_v2_*']:
        exp_dirs.extend(moss_root.glob(f'logs/{pattern}'))
    
    if not exp_dirs:
        return None
    return sorted(exp_dirs)[-1]


def main():
    parser = argparse.ArgumentParser(description='MOSS 长周期实验运行器 v5.5.1-优化版')
    parser.add_argument('--cycles', type=int, default=100000, help='最大运行周期')
    parser.add_argument('--label', type=str, default='', help='实验标签')
    parser.add_argument('--resume', type=str, default=None, help='从检查点恢复')
    parser.add_argument('--cp-cycle', type=int, default=1000, help='检查点周期间隔')
    parser.add_argument('--cp-time', type=int, default=30, help='检查点时间间隔分钟')
    parser.add_argument('--gc-threshold', type=float, default=30.0, help='GC触发阈值MB')
    parser.add_argument('--gc-interval', type=int, default=250, help='GC周期间隔')
    parser.add_argument('--report-interval', type=int, default=5000, help='报告输出间隔')
    args = parser.parse_args()

    exiter = GracefulExiter()
    moss_root = Path(__file__).resolve().parent.parent
    config_path = str(moss_root / 'config' / 'agent_config.yaml')

    resume_cycle = 0
    run_dir = None
    
    if args.resume:
        if args.resume == 'latest':
            latest_dir = find_latest_experiment_dir(moss_root)
            if not latest_dir:
                logger.error("找不到已有的实验目录")
                sys.exit(1)
            run_dir = str(latest_dir)
            cp_path = find_latest_checkpoint(run_dir)
            if not cp_path:
                logger.error(f"在 {run_dir} 中找不到检查点")
                sys.exit(1)
            args.resume = cp_path
        else:
            run_dir = str(Path(args.resume).resolve().parent)
        
        logger.info(f"从检查点恢复: {args.resume}")
        with open(args.resume, 'rb') as f:
            if args.resume.endswith('.gz'):
                import gzip
                checkpoint = json.loads(gzip.open(f).read().decode())
            else:
                checkpoint = json.load(f)
        resume_cycle = checkpoint['cycle']
        logger.info(f"恢复周期: {resume_cycle:,}")
    else:
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        label = f"_{args.label}" if args.label else ""
        run_dir = str(moss_root / 'logs' / f'experiment_v5_{run_id}{label}')
        os.makedirs(run_dir, exist_ok=True)

    MAX_CYCLES = args.cycles
    cp_manager = CheckpointManager(run_dir, args.cp_cycle, args.cp_time)
    mem_optimizer = MemoryOptimizer(args.gc_threshold, args.gc_interval)
    
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    logger.info("=" * 70)
    logger.info("  MOSS 长周期实验运行器 v5.5.1 - 优化版")
    logger.info("=" * 70)
    logger.info(f"目录: {run_dir}")
    logger.info(f"最大周期: {MAX_CYCLES:,}")
    logger.info(f"起始周期: {resume_cycle:,}")
    logger.info(f"检查点间隔: {args.cp_cycle} 周期 / {args.cp_time} 分钟")
    logger.info(f"GC策略: 阈值{args.gc_threshold}MB / 间隔{args.gc_interval}周期")
    
    agent = AGIAgent(config_path)
    start_time = time.time()
    initial_drives = ['survival', 'curiosity', 'influence', 'optimization']
    
    speed_log = []
    last_report_time = time.time()
    
    logger.info(f"初始驱动力: {agent.drive_manager.get_all_drive_names()}")
    logger.info(f"初始内存: {get_memory_mb():.1f} MB")
    logger.info("=" * 70)
    
    emerged_log = list(agent._emerged_drives)
    
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
            
            current_mem = get_memory_mb()
            gc_result = mem_optimizer.check_and_gc(cycle, current_mem)
            
            if cp_manager.should_save(cycle):
                save_checkpoint(run_dir, agent, cycle, start_time, mem_optimizer)
                cp_manager.mark_saved(cycle)
            
            if cycle % args.report_interval == 0:
                elapsed = (time.time() - start_time) / 3600.0
                avg_speed = (cycle - resume_cycle) / max(elapsed * 3600, 1)
                leak_status = mem_optimizer.detect_leak()
                
                logger.info(
                    f"[{cycle:>8,}/{MAX_CYCLES:,}] "
                    f"{elapsed:>5.1f}h | "
                    f"{current_mem:>6.1f}MB | "
                    f"{avg_speed:>6.1f}c/s | "
                    f"GC:{mem_optimizer.gc_count} | "
                    f"涌现:{agent._emerged_drives}"
                )
                
                if leak_status and leak_status.get('leak_detected'):
                    logger.warning(f"⚠️ 内存泄漏检测: {leak_status}")
            
            if len(agent._emerged_drives) > len(emerged_log):
                new_emerged = set(agent._emerged_drives) - set(emerged_log)
                for name in new_emerged:
                    logger.info(f"★★★ 涌现: {name} (周期 {cycle:,})")
                    emerged_log.append(name)
                    save_checkpoint(run_dir, agent, cycle, start_time, mem_optimizer, extra={
                        'emergence_event': {'drive_name': name}
                    })
    
    except Exception as e:
        logger.critical(f"实验异常: {e}", exc_info=True)
        try:
            save_checkpoint(run_dir, agent, agent.cycle, start_time, mem_optimizer,
                          extra={'emergency': True, 'error': str(e)})
        except:
            pass
        raise
    
    logger.info("=" * 70)
    logger.info("生成最终报告...")
    
    performance_stats = {
        'avg_cycles_per_sec': round((agent.cycle - resume_cycle) / max((time.time() - start_time), 1), 2),
        'checkpoint_count': cp_manager.checkpoint_count,
        'gc_count': mem_optimizer.gc_count,
    }
    
    report_file = save_final_report(
        run_dir, agent, '', start_time, initial_drives,
        mem_optimizer, performance_stats
    )
    
    elapsed = (time.time() - start_time) / 3600.0
    logger.info(f"✓ 完成: {agent.cycle:,} 周期, {elapsed:.1f}h")
    logger.info(f"✓ 涌现: {agent._emerged_drives}")
    logger.info(f"✓ 报告: {report_file}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
