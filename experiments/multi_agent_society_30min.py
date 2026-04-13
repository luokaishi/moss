#!/usr/bin/env python3
"""
MOSS v5.2 多Agent社会实验 - 30分钟完整测试 (Windows兼容版)

目标：验证多Agent系统在长时间运行中的稳定性
- 5个MOSS Agent并行运行
- 30分钟连续执行
- 观察Purpose分化、社会分工和协作行为
- 完整的性能指标收集和分析

运行: python experiments/multi_agent_society_30min.py
作者: MOSS项目团队
日期: 2026-04-10
"""

import sys
import os
import time
import json
import argparse
import logging
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import threading
import queue
import concurrent.futures
from dataclasses import dataclass, asdict
import statistics

# 自定义JSON编码器处理datetime对象
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        return super().default(obj)

# ============================================
# 1. 路径配置 - Windows兼容
# ============================================
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '_archive_v3', 'core'))
sys.path.insert(0, os.path.join(project_root, 'moss', 'core'))

# Windows路径兼容性
def win_path(path_str):
    """确保路径适合Windows"""
    return str(path_str).replace('/', '\\')


# ============================================
# 2. 数据类定义
# ============================================
@dataclass
class AgentConfig:
    """Agent配置"""
    agent_id: str
    enable_purpose: bool = True
    purpose_interval: int = 2000
    initial_weights: Optional[List[float]] = None
    behavior_profile: str = "balanced"  # balanced/explorer/optimizer/social
    
    def __post_init__(self):
        if self.initial_weights is None:
            # 基于行为配置文件设置初始权重
            if self.behavior_profile == "explorer":
                self.initial_weights = [0.1, 0.4, 0.2, 0.3]  # 高好奇心
            elif self.behavior_profile == "optimizer":
                self.initial_weights = [0.2, 0.2, 0.2, 0.4]  # 高优化
            elif self.behavior_profile == "social":
                self.initial_weights = [0.25, 0.2, 0.35, 0.2]  # 高影响力
            else:  # balanced
                self.initial_weights = [0.25, 0.25, 0.25, 0.25]


@dataclass
class ExperimentResult:
    """实验结果"""
    experiment_id: str
    start_time: datetime
    end_time: datetime
    total_steps: int
    agents_count: int
    success_rate: float
    average_reward: float
    purpose_evolution: Dict[str, List[float]]
    social_interactions: int
    resource_utilization: float
    performance_metrics: Dict[str, float]


@dataclass
class StepRecord:
    """单步记录"""
    timestamp: str
    agent_id: str
    step_number: int
    action: str
    success: bool
    reward: float
    purpose_vector: List[float]
    weights: List[float]
    coherence_score: float
    resource_level: float
    social_interaction: bool = False


# ============================================
# 3. 日志和监控配置
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(win_path('experiments/society_30min.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.metrics = {
            'step_latency': [],
            'memory_usage': [],
            'cpu_usage': [],
            'agent_responsiveness': [],
            'purpose_update_frequency': []
        }
        self.start_time = time.time()
    
    def record_metric(self, metric_name: str, value: float):
        """记录性能指标"""
        if metric_name in self.metrics:
            self.metrics[metric_name].append(value)
    
    def get_summary(self) -> Dict[str, float]:
        """获取性能摘要"""
        summary = {}
        for metric_name, values in self.metrics.items():
            if values:
                summary[f'{metric_name}_avg'] = statistics.mean(values)
                summary[f'{metric_name}_max'] = max(values)
                summary[f'{metric_name}_min'] = min(values)
                summary[f'{metric_name}_std'] = statistics.stdev(values) if len(values) > 1 else 0.0
        
        summary['total_duration'] = time.time() - self.start_time
        return summary


# ============================================
# 4. 实验主类
# ============================================
class MultiAgentSocietyExperiment:
    """多Agent社会实验"""
    
    def __init__(self, 
                 agents_count: int = 5,
                 duration_minutes: int = 30,
                 output_dir: str = "experiments/society_results_30min"):
        
        self.agents_count = agents_count
        self.duration_minutes = duration_minutes
        self.output_dir = Path(win_path(output_dir))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 实验配置
        self.experiment_id = f"society_30min_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        # Agent和资源
        self.agents = []
        self.agent_configs = []
        self.bridge = None
        self.monitor = PerformanceMonitor(self.experiment_id)
        
        # 数据收集
        self.step_records = []
        self.purpose_history = {}
        self.social_interactions = 0
        self.total_steps = 0
        self.successful_steps = 0
        self.total_reward = 0.0
        
        # 线程和同步
        self.step_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.lock = threading.Lock()
        
        logger.info(f"实验初始化: ID={self.experiment_id}, Agents={agents_count}, 时长={duration_minutes}分钟")
    
    def initialize_agents(self):
        """初始化Agent"""
        logger.info("初始化Agent...")
        
        # 导入Agent模块
        try:
            from _archive_v3.core.agent_9d import MOSSv3Agent9D
            from moss.core.real_world_bridge import RealWorldBridge
        except ImportError as e:
            logger.error(f"导入模块失败: {e}")
            raise
        
        # 初始化RealWorldBridge
        try:
            self.bridge = RealWorldBridge()
            logger.info("✅ RealWorldBridge初始化成功")
        except Exception as e:
            logger.warning(f"RealWorldBridge初始化失败，使用模拟模式: {e}")
            self.bridge = None
        
        # 创建不同配置的Agent
        behavior_profiles = ["balanced", "explorer", "optimizer", "social", "balanced"]
        
        for i in range(self.agents_count):
            profile = behavior_profiles[i % len(behavior_profiles)]
            config = AgentConfig(
                agent_id=f"agent_{i+1:02d}",
                behavior_profile=profile,
                enable_purpose=True,
                purpose_interval=1500 + i*100  # 错开purpose更新间隔
            )
            
            try:
                agent = MOSSv3Agent9D(
                    agent_id=config.agent_id,
                    enable_purpose=config.enable_purpose,
                    purpose_interval=config.purpose_interval
                )
                
                # 设置初始权重
                if hasattr(agent, 'weights'):
                    agent.weights = np.array(config.initial_weights)
                
                self.agents.append(agent)
                self.agent_configs.append(config)
                
                logger.info(f"✅ Agent {config.agent_id} 初始化成功 (profile: {profile})")
                
                # 初始化purpose历史记录
                self.purpose_history[config.agent_id] = []
                
            except Exception as e:
                logger.error(f"❌ Agent {config.agent_id} 初始化失败: {e}")
                raise
        
        logger.info(f"✅ 成功初始化 {len(self.agents)} 个Agent")
    
    def generate_observation(self, agent_id: str, step: int) -> Dict:
        """生成环境观察"""
        # 模拟环境状态
        time_factor = (step % 100) / 100.0  # 时间循环因子
        
        observation = {
            'step': step,
            'time': time.time(),
            'resource_level': 0.7 + 0.3 * np.sin(time_factor * 2 * np.pi),  # 周期性资源
            'threat_level': 0.1 if step % 50 == 0 else 0.0,  # 偶尔的威胁
            'novelty': 0.3 + 0.2 * np.random.random(),  # 新颖性
            'social_feedback': 0.2 if step % 20 == 0 else 0.0,  # 社交反馈
            
            # Agent特定信息
            'agent_id': agent_id,
            'agent_index': int(agent_id.split('_')[1]) - 1,
            
            # 环境复杂度
            'environment_complexity': 0.5 + 0.3 * (step / 1000.0)  # 随时间增加复杂度
        }
        
        # 添加社交交互机会
        if step % 30 == 0:
            observation['social_opportunity'] = True
            observation['other_agent_status'] = [
                {'id': f'agent_{j+1:02d}', 'trust': 0.8} 
                for j in range(self.agents_count) if j != (int(agent_id.split('_')[1]) - 1)
            ][:2]  # 最多2个其他Agent
        
        return observation
    
    def run_agent_step(self, agent, agent_id: str, step: int):
        """运行单个Agent的单步"""
        try:
            # 生成观察
            observation = self.generate_observation(agent_id, step)
            
            # 将观察拆分为MOSSv3Agent9D.step()所需的格式
            observed_behaviors = {}
            interaction = {}
            
            # 从observation字典中提取相关信息
            # observed_behaviors: 其他Agent的行为观察
            if 'other_agent_status' in observation:
                observed_behaviors = {
                    'other_agents': observation['other_agent_status'],
                    'social_opportunity': observation.get('social_opportunity', False)
                }
            
            # interaction: 与环境的相关信息
            interaction = {
                'step': observation['step'],
                'time': observation['time'],
                'resource_level': observation['resource_level'],
                'threat_level': observation['threat_level'],
                'novelty': observation['novelty'],
                'social_feedback': observation['social_feedback'],
                'environment_complexity': observation['environment_complexity']
            }
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行Agent step - 使用正确的参数格式
            result = agent.step(observed_behaviors, interaction)
            
            # 记录延迟
            latency = time.time() - start_time
            self.monitor.record_metric('step_latency', latency)
            
            # 记录Agent响应性
            self.monitor.record_metric('agent_responsiveness', 1.0 / (latency + 0.001))
            
            # 获取purpose向量
            purpose_vector = None
            if hasattr(agent, 'purpose_generator') and agent.purpose_generator is not None:
                purpose_vector = agent.purpose_generator.purpose_vector.tolist()
                self.monitor.record_metric('purpose_update_frequency', 1.0)
            
            # 创建记录
            record = StepRecord(
                timestamp=datetime.now().isoformat(),
                agent_id=agent_id,
                step_number=step,
                action=result.get('action', 'unknown'),
                success=result.get('success', False),
                reward=result.get('reward', 0.0),
                purpose_vector=purpose_vector or [0.0] * 9,
                weights=agent.weights.tolist() if hasattr(agent, 'weights') else [0.25] * 4,
                coherence_score=result.get('state', {}).get('coherence', 0.5) if isinstance(result.get('state'), dict) else 0.5,
                resource_level=observation['resource_level'],
                social_interaction='social_opportunity' in observation
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Agent {agent_id} step {step} 失败: {e}")
            # 返回一个错误记录
            return StepRecord(
                timestamp=datetime.now().isoformat(),
                agent_id=agent_id,
                step_number=step,
                action='error',
                success=False,
                reward=0.0,
                purpose_vector=[0.0] * 9,
                weights=[0.25] * 4,
                coherence_score=0.0,
                resource_level=0.0
            )
    
    def run_experiment(self):
        """运行实验"""
        logger.info(f"开始实验: {self.experiment_id}")
        logger.info(f"预计结束时间: {self.end_time}")
        
        # 初始化Agent
        self.initialize_agents()
        
        # 运行实验
        step_counter = 0
        batch_size = self.agents_count  # 每批次处理所有Agent
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.agents_count) as executor:
            while datetime.now() < self.end_time:
                batch_start_time = time.time()
                step_counter += 1
                
                logger.info(f"Step {step_counter:06d} - 剩余时间: {self.end_time - datetime.now()}")
                
                # 提交当前批次任务
                futures = []
                for i, (agent, config) in enumerate(zip(self.agents, self.agent_configs)):
                    future = executor.submit(self.run_agent_step, agent, config.agent_id, step_counter)
                    futures.append(future)
                
                # 收集结果
                batch_records = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        record = future.result(timeout=5.0)
                        batch_records.append(record)
                        
                        # 更新统计
                        with self.lock:
                            self.total_steps += 1
                            if record.success:
                                self.successful_steps += 1
                            self.total_reward += record.reward
                            
                            # 记录purpose历史
                            if record.purpose_vector:
                                self.purpose_history[record.agent_id].append(record.purpose_vector)
                            
                            # 记录社交交互
                            if record.social_interaction:
                                self.social_interactions += 1
                                
                    except concurrent.futures.TimeoutError:
                        logger.warning("Agent step 执行超时")
                    except Exception as e:
                        logger.error(f"收集结果失败: {e}")
                
                # 保存批次记录
                if batch_records:
                    self.step_records.extend(batch_records)
                    
                    # 每100步保存一次
                    if step_counter % 100 == 0:
                        self.save_checkpoint(step_counter)
                
                # 批次性能监控
                batch_duration = time.time() - batch_start_time
                self.monitor.record_metric('batch_processing_time', batch_duration)
                
                # 控制执行速度，避免过载
                target_batch_time = 1.0  # 目标每批次1秒
                if batch_duration < target_batch_time:
                    time.sleep(target_batch_time - batch_duration)
                
                # 每1000步打印进度
                if step_counter % 1000 == 0:
                    self.print_progress(step_counter)
        
        # 实验结束
        logger.info(f"实验完成! 总步数: {self.total_steps}")
        self.save_results()
    
    def print_progress(self, step_counter: int):
        """打印进度"""
        success_rate = (self.successful_steps / self.total_steps * 100) if self.total_steps > 0 else 0
        avg_reward = self.total_reward / self.total_steps if self.total_steps > 0 else 0
        
        logger.info(f"进度报告 [Step {step_counter:06d}]:")
        logger.info(f"  成功率: {success_rate:.1f}%")
        logger.info(f"  平均奖励: {avg_reward:.3f}")
        logger.info(f"  社交交互: {self.social_interactions}")
        logger.info(f"  剩余时间: {self.end_time - datetime.now()}")
        
        # 显示每个Agent的purpose向量
        if self.purpose_history:
            logger.info("  Purpose向量摘要:")
            for agent_id, history in list(self.purpose_history.items())[:3]:  # 只显示前3个
                if history:
                    latest = history[-1]
                    # 只显示前4个维度（D1-D4）
                    logger.info(f"    {agent_id}: [{latest[0]:.3f}, {latest[1]:.3f}, {latest[2]:.3f}, {latest[3]:.3f}]")
    
    def save_checkpoint(self, step_counter: int):
        """保存检查点"""
        checkpoint_file = self.output_dir / f"checkpoint_step_{step_counter:06d}.json"
        
        checkpoint_data = {
            'experiment_id': self.experiment_id,
            'step': step_counter,
            'timestamp': datetime.now().isoformat(),
            'total_steps': self.total_steps,
            'successful_steps': self.successful_steps,
            'total_reward': self.total_reward,
            'social_interactions': self.social_interactions,
            'agents': [
                {
                    'agent_id': config.agent_id,
                    'profile': config.behavior_profile,
                    'purpose_history_length': len(self.purpose_history.get(config.agent_id, [])),
                    'latest_purpose': self.purpose_history.get(config.agent_id, [])[-1] if self.purpose_history.get(config.agent_id) else None
                }
                for config in self.agent_configs
            ]
        }
        
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            
            logger.debug(f"检查点保存: {checkpoint_file}")
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")
    
    def save_results(self):
        """保存完整结果"""
        logger.info("保存实验结果...")
        
        # 计算最终统计
        success_rate = (self.successful_steps / self.total_steps) if self.total_steps > 0 else 0
        avg_reward = self.total_reward / self.total_steps if self.total_steps > 0 else 0
        
        # 资源利用率（基于资源水平）
        resource_levels = [r.resource_level for r in self.step_records if hasattr(r, 'resource_level')]
        resource_utilization = statistics.mean(resource_levels) if resource_levels else 0
        
        # 性能指标
        performance_metrics = self.monitor.get_summary()
        
        # 创建最终结果
        result = ExperimentResult(
            experiment_id=self.experiment_id,
            start_time=self.start_time,
            end_time=datetime.now(),
            total_steps=self.total_steps,
            agents_count=self.agents_count,
            success_rate=success_rate,
            average_reward=avg_reward,
            purpose_evolution=self.purpose_history,
            social_interactions=self.social_interactions,
            resource_utilization=resource_utilization,
            performance_metrics=performance_metrics
        )
        
        # 保存结果文件
        result_file = self.output_dir / f"{self.experiment_id}_final.json"
        records_file = self.output_dir / f"{self.experiment_id}_records.jsonl"
        
        try:
            # 保存摘要结果
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            
            # 保存详细记录
            with open(records_file, 'w', encoding='utf-8') as f:
                for record in self.step_records:
                    f.write(json.dumps(asdict(record), ensure_ascii=False, cls=DateTimeEncoder) + '\n')
            
            logger.info(f"✅ 结果保存完成:")
            logger.info(f"   摘要: {result_file}")
            logger.info(f"   详细记录: {records_file}")
            
            # 打印总结
            self.print_summary(result)
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            raise
    
    def print_summary(self, result: ExperimentResult):
        """打印实验总结"""
        print("\n" + "="*60)
        print("多Agent社会实验 - 30分钟完整测试总结")
        print("="*60)
        print(f"实验ID: {result.experiment_id}")
        print(f"时间: {result.start_time} 到 {result.end_time}")
        print(f"持续时间: {result.end_time - result.start_time}")
        print(f"Agent数量: {result.agents_count}")
        print(f"总步数: {result.total_steps:,}")
        print(f"成功率: {result.success_rate*100:.1f}%")
        print(f"平均奖励: {result.average_reward:.3f}")
        print(f"社交交互次数: {result.social_interactions}")
        print(f"资源利用率: {result.resource_utilization*100:.1f}%")
        print()
        print("性能指标:")
        for key, value in result.performance_metrics.items():
            if 'duration' in key or 'time' in key:
                print(f"  {key}: {value:.3f}s")
            else:
                print(f"  {key}: {value:.3f}")
        print()
        print("Purpose演化摘要:")
        for agent_id, history in result.purpose_evolution.items():
            if history:
                latest = history[-1]
                print(f"  {agent_id}: D1={latest[0]:.3f}, D2={latest[1]:.3f}, D3={latest[2]:.3f}, D4={latest[3]:.3f}")
        print("="*60)


# ============================================
# 5. 主程序
# ============================================
def main():
    parser = argparse.ArgumentParser(description='运行多Agent社会实验 (30分钟)')
    parser.add_argument('--agents', type=int, default=5,
                       help='Agent数量 (默认: 5)')
    parser.add_argument('--duration', type=int, default=30,
                       help='实验时长(分钟) (默认: 30)')
    parser.add_argument('--output', type=str, default='experiments/society_results_30min',
                       help='输出目录 (默认: experiments/society_results_30min)')
    parser.add_argument('--quick', action='store_true',
                       help='快速测试模式 (5分钟)')
    
    args = parser.parse_args()
    
    # 快速测试模式
    if args.quick:
        args.duration = 5
        print("⚠️  快速测试模式: 5分钟运行")
    
    # 创建并运行实验
    try:
        experiment = MultiAgentSocietyExperiment(
            agents_count=args.agents,
            duration_minutes=args.duration,
            output_dir=args.output
        )
        
        experiment.run_experiment()
        
        print("\n🎉 实验完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️  实验被用户中断")
        print("正在保存已收集的数据...")
    except Exception as e:
        print(f"\n❌ 实验失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())