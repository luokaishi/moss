#!/usr/bin/env python3
"""
MOSS 72h Real World Experiment - Resume Version
从指定checkpoint恢复运行

用法:
    python local_72h_resume.py --resume-step 298700 --remaining-hours 63.7
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

# 实验配置
EXPERIMENT_ID = "local_72h_20260325"
LOG_DIR = Path(f"experiments/{EXPERIMENT_ID}")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 配置日志 - 追加模式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'experiment.log', mode='a'),  # 追加模式
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class IsolatedRealWorldBridge(RealWorldBridge):
    """隔离版RealWorldBridge"""
    
    def __init__(self, agent, config_path=None):
        super().__init__(agent, config_path)
        self.action_log_path = LOG_DIR / 'actions.jsonl'
        logger.info(f"[IsolatedBridge] Action log: {self.action_log_path}")
    
    def _execute_github_action(self, action_plan):
        """覆盖：禁用git push避免冲突"""
        import subprocess
        
        task = action_plan['task'].lower()
        result = {'executed': False, 'output': ''}
        
        if 'push' in task:
            result['executed'] = False
            result['output'] = '[ISOLATED MODE] Git push disabled'
            logger.info("[IsolatedBridge] Skipped git push (isolated mode)")
            return result
        
        if 'status' in task or 'log' in task:
            cmd = task.split() if task.startswith('git ') else ['git', 'status']
            r = subprocess.run(cmd, capture_output=True, text=True, cwd='/workspace/projects/moss')
            result['executed'] = True
            result['output'] = r.stdout or r.stderr
        
        return result


class Local72hResumeExperiment:
    """本地72小时实验（恢复版）"""
    
    def __init__(self, start_step: int = 0, remaining_hours: float = 72, 
                 initial_stats: Dict = None):
        self.start_step = start_step
        self.duration = timedelta(hours=remaining_hours)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration
        
        # 初始化agent
        self.agent = self._init_agent()
        self.bridge = IsolatedRealWorldBridge(self.agent)
        
        # 恢复统计或初始化为0
        self.stats = initial_stats or {
            'total_steps': start_step,
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
        
        # 计算任务索引（从之前的进度恢复）
        self.task_idx = (start_step // 100) % len(self.tasks)
        
        logger.info("=" * 70)
        logger.info("🔄 RESUMING LOCAL 72-hour Real World Experiment")
        logger.info("=" * 70)
        logger.info(f"[Resume] Starting from step: {start_step}")
        logger.info(f"[Resume] Remaining duration: {remaining_hours} hours")
        logger.info(f"[Resume] Start time: {self.start_time}")
        logger.info(f"[Resume] End time: {self.end_time}")
        logger.info(f"[Resume] Current stats: {self.stats}")
    
    def _init_agent(self):
        """初始化MOSS agent"""
        try:
            from agent_9d import MOSSv3Agent9D
            agent = MOSSv3Agent9D(
                agent_id=f"local_72h_{EXPERIMENT_ID}_resumed",
                enable_purpose=True
            )
            logger.info("[Local 72h Experiment] Using real MOSSv3Agent9D")
            return agent
        except Exception as e:
            logger.warning(f"[Local 72h Experiment] Using mock agent: {e}")
            return MockAgent()
    
    def run(self):
        """运行实验"""
        step = self.start_step
        
        while datetime.now() < self.end_time:
            current_time = datetime.now()
            elapsed = current_time - self.start_time
            remaining = self.end_time - current_time
            
            # Agent step
            if hasattr(self.agent, 'step'):
                self.agent.step()
            
            # 每100步执行一次真实世界任务
            if step % 100 == 0 and step > 0:
                task = self.tasks[self.task_idx % len(self.tasks)]
                self._execute_real_world_task(task, step)
                self.task_idx += 1
            
            # 每小时记录一次状态
            if step % 3600 == 0 and step > 0:
                self._log_hourly_status(step, elapsed, remaining)
            
            # 显示进度（每1000步）
            if step % 1000 == 0:
                total_elapsed_hours = 8.3 + elapsed.total_seconds() / 3600  # 加上之前的8.3小时
                progress = (total_elapsed_hours / 72) * 100
                logger.info(f"Progress: {progress:.1f}% | Step {step} | Elapsed this session: {elapsed}")
            
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
        logger.info(f"  Session elapsed: {elapsed}")
        logger.info(f"  Session remaining: {remaining}")
        logger.info(f"  Total real-world actions: {self.stats['real_world_actions']}")
        
        # 保存状态到文件
        total_elapsed_hours = 8.3 + elapsed.total_seconds() / 3600
        status = {
            'experiment_id': EXPERIMENT_ID,
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'total_elapsed_hours': total_elapsed_hours,
            'session_elapsed_hours': elapsed.total_seconds() / 3600,
            'session_remaining_hours': remaining.total_seconds() / 3600,
            'stats': self.stats,
            'resumed': True
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
            'resumed_from_step': self.start_step,
            'stats': self.stats
        }
        with open(LOG_DIR / 'report_resumed.json', 'w') as f:
            json.dump(report, f, indent=2)


class MockAgent:
    """Mock agent for testing"""
    def step(self):
        pass


def load_previous_stats():
    """加载之前的统计信息"""
    status_file = LOG_DIR / 'status.json'
    if status_file.exists():
        with open(status_file, 'r') as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MOSS Local 72h Real World Experiment (RESUME)')
    parser.add_argument('--resume-step', type=int, default=298700, 
                        help='Step to resume from (default: 298700)')
    parser.add_argument('--remaining-hours', type=float, default=63.7,
                        help='Remaining hours to run (default: 63.7)')
    args = parser.parse_args()
    
    # 加载之前的统计
    prev_status = load_previous_stats()
    initial_stats = None
    if prev_status and 'stats' in prev_status:
        initial_stats = prev_status['stats']
        logger.info(f"[Resume] Loaded previous stats: {initial_stats}")
    
    experiment = Local72hResumeExperiment(
        start_step=args.resume_step,
        remaining_hours=args.remaining_hours,
        initial_stats=initial_stats
    )
    experiment.run()
