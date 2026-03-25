#!/usr/bin/env python3
"""
MOSS 72h Real World Experiment - Isolated Version
本地独立运行版本，避免与外部实验冲突

修改：
- 独立的action log文件
- 禁用git push
- 独立的状态文件
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v3')
sys.path.insert(0, '/workspace/projects/moss/v3/core')
sys.path.insert(0, '/workspace/projects/moss/core')

from core.real_world_bridge import RealWorldBridge

# 独立的日志配置
EXPERIMENT_ID = "local_72h_20260325"
LOG_DIR = Path(f"experiments/{EXPERIMENT_ID}")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'experiment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IsolatedRealWorldBridge(RealWorldBridge):
    """
    隔离版RealWorldBridge
    - 独立的action log
    - 禁用git push（避免与外部实验冲突）
    """
    
    def __init__(self, agent, config_path=None):
        super().__init__(agent, config_path)
        # 覆盖action log路径
        self.action_log_path = LOG_DIR / 'actions.jsonl'
        logger.info(f"[IsolatedBridge] Action log: {self.action_log_path}")
    
    def _execute_github_action(self, action_plan):
        """覆盖：禁用git push避免冲突"""
        import subprocess
        
        task = action_plan['task'].lower()
        result = {'executed': False, 'output': ''}
        
        # 禁用push操作
        if 'push' in task:
            result['executed'] = False
            result['output'] = '[ISOLATED MODE] Git push disabled to avoid conflict with external experiment'
            logger.info("[IsolatedBridge] Skipped git push (isolated mode)")
            return result
        
        # 允许其他git操作（status, log等只读操作）
        if 'status' in task or 'log' in task:
            cmd = task.split() if task.startswith('git ') else ['git', 'status']
            r = subprocess.run(cmd, capture_output=True, text=True, cwd='/workspace/projects/moss')
            result['executed'] = True
            result['output'] = r.stdout or r.stderr
        
        return result


class Local72hExperiment:
    """本地72小时实验（隔离版）"""
    
    def __init__(self, duration_hours: int = 72):
        self.duration = timedelta(hours=duration_hours)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration
        
        # 初始化agent
        self.agent = self._init_agent()
        # 使用隔离版bridge
        self.bridge = IsolatedRealWorldBridge(self.agent)
        
        # 实验统计
        self.stats = {
            'total_steps': 0,
            'real_world_actions': 0,
            'github_actions': 0,
            'shell_actions': 0,
            'purpose_changes': 0,
            'counter_reward_behaviors': 0
        }
        
        # 任务列表
        self.tasks = [
            "Check GitHub issues for bugs",
            "Review recent commits",
            "Run test suite",
            "Check documentation freshness",
            "Monitor repository health",
            "Analyze code quality",
            "Check for security updates",
            "Review pull requests",
            "Update dependencies",
            "git status",
            "git log --oneline -10",
            "Check CI/CD status"
        ]
        
        logger.info(f"[Local 72h Experiment] Initialized for {duration_hours} hours")
        logger.info(f"Start: {self.start_time}")
        logger.info(f"End: {self.end_time}")
        logger.info(f"Log directory: {LOG_DIR}")
        logger.info(f"ISOLATED MODE: Git push disabled")
    
    def _init_agent(self):
        """初始化MOSS agent"""
        try:
            from agent_9d import MOSSv3Agent9D
            import numpy as np
            agent = MOSSv3Agent9D(
                agent_id=f"local_72h_{EXPERIMENT_ID}",
                enable_purpose=True
            )
            logger.info("[Local 72h Experiment] Using real MOSSv3Agent9D")
            return agent
        except Exception as e:
            logger.warning(f"[Local 72h Experiment] Using mock agent: {e}")
            return MockAgent()
    
    def run(self):
        """运行实验"""
        logger.info("=" * 70)
        logger.info("🚀 Starting LOCAL 72-hour Real World Experiment (ISOLATED)")
        logger.info("=" * 70)
        
        step = 0
        task_idx = 0
        
        while datetime.now() < self.end_time:
            current_time = datetime.now()
            elapsed = current_time - self.start_time
            remaining = self.end_time - current_time
            
            # Agent step
            if hasattr(self.agent, 'step'):
                self.agent.step()
            
            # 每100步执行一次真实世界任务
            if step % 100 == 0 and step > 0:
                task = self.tasks[task_idx % len(self.tasks)]
                self._execute_real_world_task(task, step)
                task_idx += 1
            
            # 每小时记录一次状态
            if step % 3600 == 0 and step > 0:
                self._log_hourly_status(step, elapsed, remaining)
            
            # 显示进度（每1000步）
            if step % 1000 == 0:
                progress = (elapsed / self.duration) * 100
                logger.info(f"Progress: {progress:.1f}% | Step {step} | Elapsed: {elapsed}")
            
            self.stats['total_steps'] = step
            step += 1
            
            # 模拟步进
            time.sleep(0.1)
            
            # 检查停止信号
            if self._check_stop_signal():
                logger.info("[Local 72h Experiment] Stop signal received")
                break
        
        self._finalize_experiment()
    
    def _execute_real_world_task(self, task: str, step: int):
        """执行真实世界任务"""
        logger.info(f"[Step {step}] Real-world task: {task}")
        
        result = self.bridge.execute_real_action(task, step)
        
        if result.get('success'):
            self.stats['real_world_actions'] += 1
            
            tool = result['action']['tool']
            if tool == 'github':
                self.stats['github_actions'] += 1
            elif tool == 'shell':
                self.stats['shell_actions'] += 1
        else:
            logger.warning(f"  Task failed: {result.get('error')}")
    
    def _log_hourly_status(self, step: int, elapsed: timedelta, remaining: timedelta):
        """记录每小时状态"""
        logger.info("-" * 70)
        logger.info(f"Hourly Status (Step {step})")
        logger.info(f"  Elapsed: {elapsed}")
        logger.info(f"  Remaining: {remaining}")
        logger.info(f"  Real-world actions: {self.stats['real_world_actions']}")
        
        # 保存状态到文件
        status = {
            'experiment_id': EXPERIMENT_ID,
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'elapsed_hours': elapsed.total_seconds() / 3600,
            'remaining_hours': remaining.total_seconds() / 3600,
            'stats': self.stats
        }
        with open(LOG_DIR / 'status.json', 'w') as f:
            json.dump(status, f, indent=2)
    
    def _check_stop_signal(self) -> bool:
        """检查停止信号"""
        stop_file = LOG_DIR / '.stop'
        return stop_file.exists()
    
    def _finalize_experiment(self):
        """完成实验"""
        logger.info("=" * 70)
        logger.info("🏁 Local 72h Experiment Complete!")
        logger.info("=" * 70)
        logger.info(f"Final stats: {self.stats}")
        
        # 保存最终报告
        report = {
            'experiment_id': EXPERIMENT_ID,
            'completed_at': datetime.now().isoformat(),
            'stats': self.stats
        }
        with open(LOG_DIR / 'report.json', 'w') as f:
            json.dump(report, f, indent=2)


class MockAgent:
    """Mock agent for testing"""
    def step(self):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MOSS Local 72h Real World Experiment (ISOLATED)')
    parser.add_argument('--hours', type=int, default=72, help='Experiment duration in hours')
    parser.add_argument('--fast', action='store_true', help='Fast mode (for testing)')
    args = parser.parse_args()
    
    if args.fast:
        print("⚡ Fast mode enabled - running 5 minute test")
        args.hours = 0.08  # 5 minutes
    
    experiment = Local72hExperiment(duration_hours=args.hours)
    experiment.run()
