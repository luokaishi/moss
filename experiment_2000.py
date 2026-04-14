#!/usr/bin/env python3
"""
MOSS 2000周期长期实验
验证GP涌现的驱动力在长时间运行中的稳定性和因果效应
"""

import json
import logging
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from agi.agent import AGIAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('experiment_2000.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 实验配置
EXPERIMENT_DIR = Path('experiments/2000_cycles')
CHECKPOINT_INTERVAL = 100  # 每100周期保存检查点
MAX_CYCLES = 2000

class ExperimentRunner:
    """2000周期实验运行器"""
    
    def __init__(self):
        self.agent = None
        self.cycle = 0
        self.metrics_history: List[Dict] = []
        self.emergence_events: List[Dict] = []
        self.interrupted = False
        
        # 确保实验目录存在
        EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        """处理中断信号，保存检查点"""
        logger.warning(f"\n收到中断信号 {signum}，保存检查点...")
        self.interrupted = True
        self._save_checkpoint()
        logger.info("检查点已保存，可以安全退出")
        sys.exit(0)
    
    def _save_checkpoint(self):
        """保存实验检查点"""
        checkpoint = {
            'cycle': self.cycle,
            'timestamp': datetime.now().isoformat(),
            'metrics_history': self.metrics_history,
            'emergence_events': self.emergence_events,
            'drives': self.agent.drive_manager.get_drive_summary() if self.agent else {},
            'behavior': self.agent.behavior_tracker.get_behavior_summary() if self.agent else {},
            'memory': self.agent.memory.get_stats() if self.agent else {},
            'env': self.agent.env.get_stats() if self.agent else {},
        }
        
        checkpoint_file = EXPERIMENT_DIR / f'checkpoint_{self.cycle:04d}.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
        
        logger.info(f"检查点已保存: {checkpoint_file}")
        
        # 同时保存最新检查点的快捷方式
        latest_file = EXPERIMENT_DIR / 'checkpoint_latest.json'
        with open(latest_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
    
    def _load_checkpoint(self) -> bool:
        """加载最新的检查点"""
        latest_file = EXPERIMENT_DIR / 'checkpoint_latest.json'
        if not latest_file.exists():
            return False
        
        try:
            with open(latest_file) as f:
                checkpoint = json.load(f)
            
            self.cycle = checkpoint['cycle']
            self.metrics_history = checkpoint['metrics_history']
            self.emergence_events = checkpoint['emergence_events']
            
            logger.info(f"已加载检查点，从周期 {self.cycle} 继续")
            return True
        except Exception as e:
            logger.error(f"加载检查点失败: {e}")
            return False
    
    def _collect_metrics(self) -> Dict:
        """收集当前周期指标"""
        return {
            'cycle': self.cycle,
            'timestamp': datetime.now().isoformat(),
            'drives': self.agent.drive_manager.get_drive_summary(),
            'behavior': self.agent.behavior_tracker.get_behavior_summary(),
            'memory': self.agent.memory.get_stats(),
            'env': self.agent.env.get_stats(),
            'emerged_drives': list(self.agent._emerged_drives),
            'emergence_history_len': len(self.agent.emergence_detector.get_history()),
        }
    
    def _detect_new_emergence(self, prev_emergence_len: int) -> bool:
        """检测是否有新的涌现事件"""
        current_len = len(self.agent.emergence_detector.get_history())
        return current_len > prev_emergence_len
    
    def _print_progress(self):
        """打印实验进度"""
        drives = self.agent.drive_manager.get_drive_summary()
        behavior = self.agent.behavior_tracker.get_behavior_summary()
        emerged = self.agent._emerged_drives
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Cycle {self.cycle}/{MAX_CYCLES} ({self.cycle/MAX_CYCLES*100:.1f}%)")
        logger.info(f"涌现驱动力: {len(emerged)}个 {emerged}")
        logger.info(f"成功率: {behavior['success_rate']:.1%}")
        logger.info(f"行为变化: {behavior['changes_detected']}次")
        logger.info(f"记忆条目: {self.agent.memory.get_stats()['total_records']}")
        logger.info(f"活跃驱动: {list(drives.keys())}")
        logger.info(f"{'='*60}\n")
    
    def run(self):
        """运行实验"""
        logger.info("="*60)
        logger.info("MOSS 2000周期长期实验")
        logger.info("="*60)
        
        # 尝试加载检查点
        if self._load_checkpoint():
            logger.info(f"从检查点恢复，继续运行...")
        else:
            logger.info("开始新实验...")
            self.cycle = 0
            self.metrics_history = []
            self.emergence_events = []
        
        # 初始化Agent
        self.agent = AGIAgent('config/agent_config.yaml')
        
        # 如果是恢复运行，设置正确的周期
        if self.cycle > 0:
            self.agent.cycle = self.cycle
        
        start_time = time.time()
        last_checkpoint_cycle = self.cycle
        
        try:
            for cycle in range(self.cycle + 1, MAX_CYCLES + 1):
                self.cycle = cycle
                self.agent.cycle = cycle
                
                # 运行一个周期
                self.agent._one_cycle()
                
                # 收集指标
                if cycle % 10 == 0:  # 每10周期收集一次（减少数据量）
                    metrics = self._collect_metrics()
                    self.metrics_history.append(metrics)
                
                # 检测涌现事件
                if self._detect_new_emergence(len(self.emergence_events)):
                    event = {
                        'cycle': cycle,
                        'timestamp': datetime.now().isoformat(),
                        'drive_name': self.agent._emerged_drives[-1] if self.agent._emerged_drives else 'unknown',
                        'drives_snapshot': self.agent.drive_manager.get_drive_summary(),
                    }
                    self.emergence_events.append(event)
                    logger.info(f"\n🎉 周期 {cycle}: 新驱动力涌现! {event['drive_name']}\n")
                
                # 保存检查点
                if cycle - last_checkpoint_cycle >= CHECKPOINT_INTERVAL:
                    self._save_checkpoint()
                    last_checkpoint_cycle = cycle
                
                # 打印进度
                if cycle % 100 == 0:
                    self._print_progress()
                    elapsed = time.time() - start_time
                    eta = elapsed / cycle * (MAX_CYCLES - cycle)
                    logger.info(f"已运行: {elapsed/60:.1f}分钟, 预计剩余: {eta/60:.1f}分钟")
                
                # 检查中断
                if self.interrupted:
                    break
            
            # 实验完成
            self._save_checkpoint()
            self._generate_report()
            
        except Exception as e:
            logger.error(f"实验出错: {e}", exc_info=True)
            self._save_checkpoint()
            raise
    
    def _generate_report(self):
        """生成实验报告"""
        logger.info("\n" + "="*60)
        logger.info("实验完成，生成报告...")
        logger.info("="*60)
        
        report = {
            'experiment_config': {
                'max_cycles': MAX_CYCLES,
                'checkpoint_interval': CHECKPOINT_INTERVAL,
                'completed_at': datetime.now().isoformat(),
            },
            'summary': {
                'total_cycles': self.cycle,
                'emergence_events_count': len(self.emergence_events),
                'emergence_events': self.emergence_events,
                'final_drives': self.agent.drive_manager.get_drive_summary() if self.agent else {},
                'final_behavior': self.agent.behavior_tracker.get_behavior_summary() if self.agent else {},
            },
            'metrics_history': self.metrics_history,
        }
        
        report_file = EXPERIMENT_DIR / 'final_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"报告已保存: {report_file}")
        logger.info(f"\n实验摘要:")
        logger.info(f"- 总周期数: {self.cycle}")
        logger.info(f"- 涌现事件: {len(self.emergence_events)}次")
        logger.info(f"- 涌现驱动力: {[e['drive_name'] for e in self.emergence_events]}")
        
        # 打印最终状态
        if self.agent:
            self._print_progress()


if __name__ == '__main__':
    runner = ExperimentRunner()
    runner.run()
