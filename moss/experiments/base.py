"""
MOSS Unified Experiments - Standardized Experiment Framework
=============================================================

统一的实验框架，提供标准化的实验执行、数据收集和报告生成

特性：
- 所有实验继承自 BaseExperiment
- 统一的配置管理
- 自动数据记录和检查点
- 标准化的报告格式
"""

import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC, abstractmethod
import numpy as np

from ..core.unified_agent import BaseMOSSAgent, MOSSConfig, ActionResult

logger = logging.getLogger(__name__)


class ExperimentConfig:
    """实验配置"""
    
    def __init__(self,
                 experiment_id: str = "exp_default",
                 duration_steps: int = 1000,
                 duration_hours: Optional[float] = None,
                 checkpoint_interval: int = 100,
                 log_interval: int = 10,
                 output_dir: str = "experiments/results"):
        self.experiment_id = experiment_id
        self.duration_steps = duration_steps
        self.duration_hours = duration_hours
        self.checkpoint_interval = checkpoint_interval
        self.log_interval = log_interval
        self.output_dir = output_dir
        
        # 如果指定了小时，转换为步数 (假设1秒/步)
        if duration_hours:
            self.duration_steps = int(duration_hours * 3600 * 10)  # 10 steps/sec
    
    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'duration_steps': self.duration_steps,
            'duration_hours': self.duration_hours,
            'checkpoint_interval': self.checkpoint_interval,
            'log_interval': self.log_interval,
            'output_dir': self.output_dir
        }


class BaseExperiment(ABC):
    """
    实验基类
    
    所有具体实验必须继承此类
    """
    
    def __init__(self,
                 config: ExperimentConfig,
                 agent: BaseMOSSAgent = None):
        self.config = config
        self.agent = agent
        
        # 初始化输出目录
        self.output_dir = Path(config.output_dir) / config.experiment_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 实验状态
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_step = 0
        self.is_running = False
        
        # 数据收集
        self.results: List[ActionResult] = []
        self.metrics: Dict[str, List] = {
            'rewards': [],
            'successes': [],
            'states': [],
            'actions': []
        }
        
        logger.info(f"[BaseExperiment] {config.experiment_id} initialized")
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.output_dir / f"{self.config.experiment_id}.log"
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    
    @abstractmethod
    def setup(self):
        """实验设置（子类实现）"""
        pass
    
    @abstractmethod
    def run_step(self, step: int) -> ActionResult:
        """单步执行（子类实现）"""
        pass
    
    @abstractmethod
    def teardown(self):
        """实验清理（子类实现）"""
        pass
    
    def run(self, progress_callback: Callable[[int, int, Dict], None] = None) -> Dict:
        """
        运行实验
        
        Args:
            progress_callback: 进度回调函数(step, total, metrics)
        
        Returns:
            Dict: 实验结果摘要
        """
        self.start_time = datetime.now()
        self.is_running = True
        
        logger.info("=" * 70)
        logger.info(f"🚀 Starting Experiment: {self.config.experiment_id}")
        logger.info(f"   Duration: {self.config.duration_steps} steps")
        logger.info(f"   Output: {self.output_dir}")
        logger.info("=" * 70)
        
        try:
            # 实验设置
            self.setup()
            
            # 主循环
            for step in range(self.config.duration_steps):
                self.current_step = step
                
                # 执行单步
                result = self.run_step(step)
                self.results.append(result)
                
                # 收集指标
                self._collect_metrics(result)
                
                # 保存检查点
                if step % self.config.checkpoint_interval == 0:
                    self._save_checkpoint()
                
                # 日志记录
                if step % self.config.log_interval == 0:
                    self._log_progress(step)
                
                # 进度回调
                if progress_callback:
                    progress_callback(step, self.config.duration_steps, self._get_current_metrics())
                
                # 步进延迟（控制速度）
                time.sleep(0.1)
            
            # 实验完成
            self.end_time = datetime.now()
            self.is_running = False
            
            # 生成报告
            summary = self._generate_summary()
            self._save_report(summary)
            
            logger.info("=" * 70)
            logger.info(f"✅ Experiment Complete: {self.config.experiment_id}")
            logger.info(f"   Duration: {self.end_time - self.start_time}")
            logger.info("=" * 70)
            
            return summary
            
        except Exception as e:
            logger.error(f"[BaseExperiment] Error: {e}")
            self.is_running = False
            raise
        finally:
            self.teardown()
    
    def _collect_metrics(self, result: ActionResult):
        """收集指标"""
        self.metrics['rewards'].append(result.reward)
        self.metrics['successes'].append(1 if result.success else 0)
        self.metrics['states'].append(result.state)
        self.metrics['actions'].append(result.action_type)
    
    def _get_current_metrics(self) -> Dict:
        """获取当前指标"""
        if not self.metrics['rewards']:
            return {}
        
        rewards = self.metrics['rewards']
        return {
            'avg_reward': np.mean(rewards),
            'total_reward': np.sum(rewards),
            'success_rate': np.mean(self.metrics['successes']),
            'steps': self.current_step
        }
    
    def _log_progress(self, step: int):
        """记录进度"""
        metrics = self._get_current_metrics()
        progress = (step / self.config.duration_steps) * 100
        
        logger.info(
            f"[Step {step}] Progress: {progress:.1f}% | "
            f"Avg Reward: {metrics.get('avg_reward', 0):.3f} | "
            f"Success Rate: {metrics.get('success_rate', 0):.2%}"
        )
    
    def _save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'experiment_id': self.config.experiment_id,
            'step': self.current_step,
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics,
            'agent_state': self.agent.get_state() if self.agent else None
        }
        
        checkpoint_file = self.output_dir / f"checkpoint_{self.current_step}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
    
    def _generate_summary(self) -> Dict:
        """生成实验摘要"""
        duration = self.end_time - self.start_time if self.end_time else timedelta(0)
        
        rewards = self.metrics['rewards']
        successes = self.metrics['successes']
        
        return {
            'experiment_id': self.config.experiment_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration.total_seconds(),
            'total_steps': self.current_step,
            'summary': {
                'total_reward': float(np.sum(rewards)) if rewards else 0,
                'avg_reward': float(np.mean(rewards)) if rewards else 0,
                'std_reward': float(np.std(rewards)) if rewards else 0,
                'success_rate': float(np.mean(successes)) if successes else 0,
                'total_successes': int(np.sum(successes)) if successes else 0
            },
            'config': self.config.to_dict()
        }
    
    def _save_report(self, summary: Dict):
        """保存报告"""
        report_file = self.output_dir / "report.json"
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"[BaseExperiment] Report saved: {report_file}")


class SimpleMOSSExperiment(BaseExperiment):
    """
    简单的MOSS实验
    
    使用UnifiedMOSSAgent运行标准实验
    """
    
    def __init__(self,
                 config: ExperimentConfig,
                 agent_config: MOSSConfig = None):
        from ..core.unified_agent import UnifiedMOSSAgent
        
        agent = UnifiedMOSSAgent(agent_config) if agent_config else None
        super().__init__(config, agent)
        
        self.observation = {}
    
    def setup(self):
        """实验设置"""
        logger.info(f"[SimpleMOSSExperiment] Setup complete")
    
    def run_step(self, step: int) -> ActionResult:
        """单步执行"""
        if self.agent:
            return self.agent.step(self.observation)
        
        # Mock result if no agent
        return ActionResult(
            action_id=f"step_{step}",
            action_type="mock",
            success=True,
            reward=0.0,
            state="normal"
        )
    
    def teardown(self):
        """实验清理"""
        logger.info(f"[SimpleMOSSExperiment] Teardown complete")


class ExperimentRunner:
    """
    实验运行器
    
    批量运行多个实验，统一管理
    """
    
    def __init__(self, output_dir: str = "experiments/batch"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.experiments: List[BaseExperiment] = []
    
    def add_experiment(self, experiment: BaseExperiment):
        """添加实验"""
        self.experiments.append(experiment)
    
    def run_all(self, parallel: bool = False) -> List[Dict]:
        """
        运行所有实验
        
        Args:
            parallel: 是否并行运行（暂不支持）
        
        Returns:
            List[Dict]: 所有实验的结果摘要
        """
        results = []
        
        for i, exp in enumerate(self.experiments):
            logger.info(f"[ExperimentRunner] Running experiment {i+1}/{len(self.experiments)}")
            result = exp.run()
            results.append(result)
        
        # 保存批量报告
        self._save_batch_report(results)
        
        return results
    
    def _save_batch_report(self, results: List[Dict]):
        """保存批量报告"""
        batch_report = {
            'timestamp': datetime.now().isoformat(),
            'total_experiments': len(results),
            'experiments': results
        }
        
        report_file = self.output_dir / f"batch_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_file, 'w') as f:
            json.dump(batch_report, f, indent=2)
        
        logger.info(f"[ExperimentRunner] Batch report saved: {report_file}")
