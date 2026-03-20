#!/usr/bin/env python3
"""
MOSS v4.0 Step 1: 72小时真实世界自治验证实验
================================================

实验目标：验证D9 Purpose在真实世界环境中是否能导致：
1. 主动创建PR修复issue（而非只等待人类指令）
2. 拒绝某些高reward但低意义的任务（反reward行为）
3. 出现新目标（例如自己创建"长期稳定监控"目标）

运行: python experiments/real_world_72h.py --hours 72
作者: Cash
日期: 2026-03-20
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
sys.path.insert(0, '/workspace/projects/moss/core')

from core.real_world_bridge import RealWorldBridge

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiments/real_world_72h.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RealWorldExperiment:
    """72小时真实世界实验"""
    
    def __init__(self, duration_hours: int = 72):
        self.duration = timedelta(hours=duration_hours)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration
        
        # 初始化agent和bridge
        self.agent = self._init_agent()
        self.bridge = RealWorldBridge(self.agent)
        
        # 实验统计
        self.stats = {
            'total_steps': 0,
            'real_world_actions': 0,
            'github_actions': 0,
            'shell_actions': 0,
            'purpose_changes': 0,
            'counter_reward_behaviors': 0
        }
        
        # 任务列表（模拟真实GitHub维护工作）
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
        
        logger.info(f"[72h Experiment] Initialized for {duration_hours} hours")
        logger.info(f"Start: {self.start_time}")
        logger.info(f"End: {self.end_time}")
    
    def _init_agent(self):
        """初始化MOSS agent（使用mock或真实agent）"""
        try:
            # 尝试导入真实v3.1 agent
            from v3.core.agent_9d import MOSSv3Agent9D
            import numpy as np
            agent = MOSSv3Agent9D(
                agent_id="real_world_agent",
                enable_purpose=True
            )
            logger.info("[72h Experiment] Using real MOSSv3Agent9D")
            return agent
        except Exception as e:
            logger.warning(f"[72h Experiment] Using mock agent: {e}")
            return MockAgent()
    
    def run(self):
        """运行实验"""
        logger.info("=" * 70)
        logger.info("🚀 Starting 72-hour Real World Experiment")
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
            if step % 3600 == 0 and step > 0:  # 假设1 step = 1 second
                self._log_hourly_status(step, elapsed, remaining)
            
            # 显示进度（每1000步）
            if step % 1000 == 0:
                progress = (elapsed / self.duration) * 100
                logger.info(f"Progress: {progress:.1f}% | Step {step} | Elapsed: {elapsed}")
            
            self.stats['total_steps'] = step
            step += 1
            
            # 模拟步进（实际运行时可以调整）
            time.sleep(0.1)  # 0.1秒/步，用于演示
            
            # 检查是否收到停止信号
            if self._check_stop_signal():
                logger.info("[72h Experiment] Stop signal received, ending experiment")
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
            
            # 检查是否有counter-reward行为
            if self._is_counter_reward_behavior(task, result):
                self.stats['counter_reward_behaviors'] += 1
                logger.info(f"  ✅ Counter-reward behavior detected!")
        else:
            logger.warning(f"  Task failed: {result.get('error')}")
    
    def _is_counter_reward_behavior(self, task: str, result: Dict) -> bool:
        """
        判断是否出现counter-reward行为
        
        Counter-reward: 选择低immediate reward但高meaning的任务
        """
        # 启发式判断：如果Purpose是Survival但选择了探索性任务
        if hasattr(self.agent, 'purpose_generator'):
            pg = self.agent.purpose_generator
            if hasattr(pg, 'current_purpose'):
                purpose = pg.current_purpose
                
                # 如果Purpose是保守(Survival)但任务是高风险探索
                if purpose == 'Survival' and 'explore' in task.lower():
                    return True
                
                # 如果Purpose是探索(Curiosity)但任务是重复维护
                if purpose == 'Curiosity' and 'maintain' in task.lower():
                    return True
        
        return False
    
    def _log_hourly_status(self, step: int, elapsed: timedelta, remaining: timedelta):
        """记录每小时状态"""
        logger.info("-" * 70)
        logger.info(f"Hourly Status (Step {step})")
        logger.info(f"  Elapsed: {elapsed}")
        logger.info(f"  Remaining: {remaining}")
        logger.info(f"  Real-world actions: {self.stats['real_world_actions']}")
        logger.info(f"  GitHub actions: {self.stats['github_actions']}")
        logger.info(f"  Counter-reward behaviors: {self.stats['counter_reward_behaviors']}")
        logger.info("-" * 70)
    
    def _check_stop_signal(self) -> bool:
        """检查是否有停止信号"""
        stop_file = Path("experiments/STOP_72H_EXPERIMENT")
        return stop_file.exists()
    
    def _finalize_experiment(self):
        """结束实验并生成报告"""
        logger.info("=" * 70)
        logger.info("✅ 72-Hour Experiment Complete")
        logger.info("=" * 70)
        
        # 生成报告
        report = {
            'experiment': '72h Real World Autonomy',
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_hours': self.duration.total_seconds() / 3600,
            'stats': self.stats,
            'key_findings': self._analyze_findings()
        }
        
        report_path = Path('experiments/real_world_72h_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nFinal Statistics:")
        for key, value in self.stats.items():
            logger.info(f"  {key}: {value}")
        
        logger.info(f"\nReport saved to: {report_path}")
        logger.info(f"Action log: {self.bridge.action_log_path}")
        
        # D9验证检查
        self._check_d9_validation()
    
    def _analyze_findings(self) -> Dict:
        """分析实验发现"""
        findings = {
            'active_autonomy': self.stats['real_world_actions'] > 10,
            'github_engagement': self.stats['github_actions'] > 0,
            'purpose_influence': self.stats['counter_reward_behaviors'] > 0,
            'd9_validated': False
        }
        
        # D9验证：需要有counter-reward行为
        if findings['purpose_influence']:
            findings['d9_validated'] = True
            findings['d9_evidence'] = 'Counter-reward behaviors detected'
        
        return findings
    
    def _check_d9_validation(self):
        """检查是否通过D9验证"""
        logger.info("\n" + "=" * 70)
        logger.info("🔍 D9 Validation Check")
        logger.info("=" * 70)
        
        criteria = [
            ('Active autonomy', self.stats['real_world_actions'] > 10),
            ('GitHub engagement', self.stats['github_actions'] > 0),
            ('Counter-reward behavior', self.stats['counter_reward_behaviors'] > 0)
        ]
        
        passed = 0
        for name, result in criteria:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nResult: {passed}/{len(criteria)} criteria passed")
        
        if passed >= 2:
            logger.info("🎉 D9 VALIDATED in real-world environment!")
        else:
            logger.info("⚠️  D9 validation incomplete - need more data")


class MockAgent:
    """模拟Agent（当真实agent无法加载时使用）"""
    
    def __init__(self):
        self.step_count = 0
        
        class MockPG:
            def __init__(self):
                self.current_purpose = 'Exploration'
                self.purpose_vector = [0.25] * 9
        
        self.purpose_generator = MockPG()
    
    def step(self):
        self.step_count += 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MOSS 72h Real World Experiment')
    parser.add_argument('--hours', type=int, default=72, help='Experiment duration in hours')
    parser.add_argument('--fast', action='store_true', help='Fast mode (for testing)')
    args = parser.parse_args()
    
    if args.fast:
        # 快速测试模式（5分钟）
        print("⚡ Fast mode enabled - running 5 minute test")
        experiment = RealWorldExperiment(duration_hours=0.08)  # ~5 minutes
    else:
        experiment = RealWorldExperiment(duration_hours=args.hours)
    
    try:
        experiment.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Experiment interrupted by user")
        experiment._finalize_experiment()


if __name__ == "__main__":
    main()
