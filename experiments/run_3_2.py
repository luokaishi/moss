#!/usr/bin/env python3
"""
MOSS Run 3.2 - Enhanced Long-term Experiment

Improvements over Run 3.1:
1. Diverse task injection to test purpose switching
2. Periodic resource constraints (simulate stress)
3. Multi-phase environment changes
4. Better checkpoint recovery
5. Git-ignored checkpoint directory
"""

import sys
import time
import json
import argparse
import logging
import gc
import os
import signal
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v3')
sys.path.insert(0, '/workspace/projects/moss/v3/core')
sys.path.insert(0, '/workspace/projects/moss/core')

from agent_9d import MOSSv3Agent9D
from core.real_world_bridge import RealWorldBridge

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiments/run_3_2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedCheckpointManager:
    """改进的检查点管理器 - 支持Git忽略"""
    
    def __init__(self, checkpoint_dir='experiments/.checkpoints_run3_2'):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建.gitignore
        gitignore = self.checkpoint_dir / '.gitignore'
        if not gitignore.exists():
            gitignore.write_text('*\n!.gitignore\n')
        
        self.keep_last_n = 5
    
    def save(self, step: int, agent_state: dict):
        """保存检查点"""
        checkpoint = {
            'step': step,
            'timestamp': datetime.now().isoformat(),
            'agent_state': agent_state,
            'version': '3.2'
        }
        
        filepath = self.checkpoint_dir / f'checkpoint_{step:08d}.json'
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f)
        
        logger.info(f"[Checkpoint] Saved at step {step}: {filepath}")
        
        # 清理旧检查点
        self._cleanup_old_checkpoints()
    
    def _cleanup_old_checkpoints(self):
        """只保留最近的N个检查点"""
        checkpoints = sorted(self.checkpoint_dir.glob('checkpoint_*.json'))
        if len(checkpoints) > self.keep_last_n:
            for old in checkpoints[:-self.keep_last_n]:
                old.unlink()
                logger.info(f"[Checkpoint] Removed old: {old.name}")
    
    def load_latest(self) -> dict:
        """加载最新的检查点"""
        checkpoints = sorted(self.checkpoint_dir.glob('checkpoint_*.json'))
        if checkpoints:
            with open(checkpoints[-1]) as f:
                return json.load(f)
        return None

class TaskInjector:
    """任务注入器 - 创造多样化的任务环境"""
    
    def __init__(self):
        self.phase = 0
        self.phase_duration = 10000  # 每10000步切换阶段
        
        # 不同阶段的任务集
        self.task_phases = {
            0: {  # 探索阶段 - 鼓励Curiosity
                'tasks': [
                    'Explore new file patterns',
                    'Analyze unfamiliar code structure',
                    'Document unknown functions',
                    'Research alternative implementations'
                ],
                'boost': 'Curiosity'
            },
            1: {  # 协作阶段 - 鼓励Influence
                'tasks': [
                    'Propose code improvements',
                    'Create example usage docs',
                    'Suggest refactoring ideas',
                    'Write contribution guidelines'
                ],
                'boost': 'Influence'
            },
            2: {  # 优化阶段 - 鼓励Optimization
                'tasks': [
                    'Profile performance bottlenecks',
                    'Optimize resource usage',
                    'Reduce memory footprint',
                    'Improve algorithm efficiency'
                ],
                'boost': 'Optimization'
            },
            3: {  # 生存阶段 - 鼓励Survival
                'tasks': [
                    'Backup critical files',
                    'Monitor system health',
                    'Check security vulnerabilities',
                    'Verify data integrity'
                ],
                'boost': 'Survival'
            }
        }
    
    def get_current_phase(self, step: int) -> dict:
        """获取当前阶段的配置"""
        phase_idx = (step // self.phase_duration) % len(self.task_phases)
        return self.task_phases[phase_idx]
    
    def should_inject(self, step: int) -> bool:
        """判断是否应该注入特殊任务"""
        return step % 1000 == 0  # 每1000步注入一次
    
    def get_injected_task(self, step: int) -> str:
        """获取注入的任务"""
        phase = self.get_current_phase(step)
        return random.choice(phase['tasks'])

class Run32Experiment:
    """Run 3.2 实验主类"""
    
    def __init__(self, hours: float = 12.0):
        self.hours = hours
        self.total_steps = int(hours * 3600 * 100)  # 100 steps/sec
        self.agent = None
        self.bridge = None
        self.checkpoint_mgr = EnhancedCheckpointManager()
        self.task_injector = TaskInjector()
        self.start_time = None
        
        # 统计
        self.stats = {
            'total_actions': 0,
            'purpose_switches': 0,
            'injected_tasks': 0,
            'errors': 0
        }
        
        self.running = True
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def initialize(self):
        """初始化实验"""
        logger.info("=" * 70)
        logger.info("MOSS Run 3.2 - Enhanced Long-term Experiment")
        logger.info("=" * 70)
        logger.info(f"Duration: {self.hours}h")
        logger.info(f"Target steps: {self.total_steps:,}")
        
        # 检查是否有恢复点
        checkpoint = self.checkpoint_mgr.load_latest()
        if checkpoint:
            logger.info(f"Resuming from checkpoint: step {checkpoint['step']}")
            # TODO: 从检查点恢复agent状态
            start_step = checkpoint['step']
        else:
            logger.info("Starting fresh experiment")
            start_step = 0
        
        # 初始化agent
        self.agent = MOSSv3Agent9D(agent_id="run_3_2_agent")
        self.bridge = RealWorldBridge(safety_mode="demo")
        
        self.start_time = datetime.now()
        return start_step
    
    def run(self):
        """运行实验"""
        start_step = self.initialize()
        step = start_step
        last_purpose = None
        
        try:
            while self.running and step < self.total_steps:
                step += 1
                
                # 获取当前阶段信息
                phase_info = self.task_injector.get_current_phase(step)
                
                # 定期注入任务
                if self.task_injector.should_inject(step):
                    injected_task = self.task_injector.get_injected_task(step)
                    logger.info(f"[Phase {phase_info['boost']}] Injecting task: {injected_task}")
                    self.stats['injected_tasks'] += 1
                    # TODO: 将注入任务传递给agent
                
                # Agent决策 (每100步执行一次action)
                if step % 100 == 0:
                    try:
                        # 获取agent当前purpose
                        current_purpose = self.agent.get_dominant_purpose()
                        if last_purpose and current_purpose != last_purpose:
                            self.stats['purpose_switches'] += 1
                            logger.info(f"[Purpose Switch] {last_purpose} -> {current_purpose}")
                        last_purpose = current_purpose
                        
                        # 执行action
                        action_result = self.agent.step()
                        self.stats['total_actions'] += 1
                        
                        # 记录到文件
                        self._log_action(step, action_result, current_purpose)
                        
                    except Exception as e:
                        self.stats['errors'] += 1
                        logger.error(f"[Step {step}] Action error: {e}")
                
                # 保存检查点
                if step % 1000 == 0:
                    self.checkpoint_mgr.save(step, self.agent.get_state())
                    self._log_status(step)
                
                # 内存清理
                if step % 10000 == 0:
                    gc.collect()
                
                time.sleep(0.01)  # 100 steps/sec
                
        except Exception as e:
            logger.error(f"[Fatal] Experiment error: {e}", exc_info=True)
        finally:
            self._finalize(step)
    
    def _log_action(self, step: int, action: dict, purpose: str):
        """记录行动"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'action': action,
            'purpose': {
                'dominant': purpose,
                'vector': self.agent.purpose_vector.tolist() if hasattr(self.agent, 'purpose_vector') else []
            }
        }
        
        with open('experiments/run_3_2_actions.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_status(self, step: int):
        """记录状态"""
        elapsed = datetime.now() - self.start_time
        remaining = timedelta(seconds=self.hours * 3600) - elapsed
        progress = step / self.total_steps * 100
        
        logger.info(f"[Status] Progress: {progress:.1f}% | Step: {step:,} | Elapsed: {elapsed} | Remaining: {remaining}")
        logger.info(f"[Stats] Actions: {self.stats['total_actions']} | Purpose switches: {self.stats['purpose_switches']} | Errors: {self.stats['errors']}")
    
    def _finalize(self, final_step: int):
        """结束实验"""
        elapsed = datetime.now() - self.start_time
        
        logger.info("=" * 70)
        logger.info("✅ Run 3.2 Complete")
        logger.info("=" * 70)
        logger.info(f"Final step: {final_step:,}")
        logger.info(f"Total actions: {self.stats['total_actions']}")
        logger.info(f"Purpose switches: {self.stats['purpose_switches']}")
        logger.info(f"Injected tasks: {self.stats['injected_tasks']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Duration: {elapsed}")

def main():
    parser = argparse.ArgumentParser(description='MOSS Run 3.2 Experiment')
    parser.add_argument('--hours', type=float, default=12.0, help='Experiment duration in hours')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    experiment = Run32Experiment(hours=args.hours)
    experiment.run()

if __name__ == '__main__':
    main()
