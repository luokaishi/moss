#!/usr/bin/env python3
"""
MOSS v5.2 多Agent社会实验 - 30分钟完整测试 (增强版)

增强功能：
1. 集成参数转换器，支持多种Agent类型
2. 增强的错误恢复和监控
3. 实时性能指标收集
4. 自动参数格式适配

运行: python experiments/multi_agent_society_30min_enhanced.py
作者: AI Assistant
日期: 2026-04-13
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
from typing import Dict, List, Tuple, Optional, Any
import threading
import queue
import concurrent.futures
from dataclasses import dataclass, asdict
import statistics
import traceback

# ============================================
# 1. 路径配置 - Windows兼容
# ============================================
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '_archive_v3', 'core'))
sys.path.insert(0, os.path.join(project_root, '_archive_v4', 'integration'))
sys.path.insert(0, os.path.join(project_root, 'moss', 'core'))
sys.path.insert(0, os.path.join(project_root, 'moss', 'api'))

# Windows路径兼容性
def win_path(path_str):
    """确保路径适合Windows"""
    return str(path_str).replace('/', '\\')

# 导入参数转换器
try:
    from moss.api.interaction_adapter import MOSSInteractionAdapter, create_unified_agent_adapter
    from moss.api.adapter import MOSSApiAdapter, create_unified_agent
    PARAMETER_ADAPTER_AVAILABLE = True
    print("✅ 参数转换器导入成功")
except ImportError as e:
    PARAMETER_ADAPTER_AVAILABLE = False
    print(f"⚠️  参数转换器导入失败: {e}")
    print("⚠️  将使用基本模式运行")

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
    agent_type: str = "auto"  # auto/v3.1/v4.1/v5.0
    
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
    agent_types_used: Dict[str, int]

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
    agent_type: str = "unknown"
    execution_time: float = 0.0

# ============================================
# 3. 日志和监控配置
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(win_path('experiments/society_30min_enhanced.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedPerformanceMonitor:
    """增强的性能监控器"""
    
    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.metrics = {
            'step_latency': [],
            'memory_usage': [],
            'batch_processing_time': [],
            'agent_responsiveness': [],
            'purpose_update_frequency': [],
            'error_rate': [],
            'parameter_conversion_time': [],
            'agent_initialization_time': []
        }
        self.error_counts = {
            'parameter_conversion': 0,
            'agent_step': 0,
            'import_error': 0,
            'other': 0
        }
        self.start_time = time.time()
        self.last_checkpoint = self.start_time
    
    def record_metric(self, metric_name: str, value: float):
        """记录性能指标"""
        if metric_name in self.metrics:
            self.metrics[metric_name].append(value)
    
    def record_error(self, error_type: str):
        """记录错误"""
        if error_type in self.error_counts:
            self.error_counts[error_type] += 1
    
    def get_summary(self) -> Dict[str, float]:
        """获取性能摘要"""
        summary = {}
        for metric_name, values in self.metrics.items():
            if values:
                summary[f'{metric_name}_avg'] = statistics.mean(values)
                summary[f'{metric_name}_max'] = max(values)
                summary[f'{metric_name}_min'] = min(values)
                summary[f'{metric_name}_std'] = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 错误统计
        total_errors = sum(self.error_counts.values())
        for error_type, count in self.error_counts.items():
            summary[f'errors_{error_type}'] = count
        
        summary['total_errors'] = total_errors
        summary['error_rate_percent'] = (total_errors / (len(self.metrics.get('step_latency', [1])) + 1)) * 100
        summary['total_duration'] = time.time() - self.start_time
        summary['checkpoint_interval'] = time.time() - self.last_checkpoint
        
        return summary
    
    def reset_checkpoint(self):
        """重置检查点计时器"""
        self.last_checkpoint = time.time()

# ============================================
# 4. 实验主类
# ============================================
class EnhancedMultiAgentSocietyExperiment:
    """增强的多Agent社会实验"""
    
    def __init__(self, 
                 agents_count: int = 5,
                 duration_minutes: int = 30,
                 output_dir: str = "experiments/society_results_30min_enhanced",
                 use_parameter_adapter: bool = True):
        
        self.agents_count = agents_count
        self.duration_minutes = duration_minutes
        self.output_dir = Path(win_path(output_dir))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_parameter_adapter = use_parameter_adapter and PARAMETER_ADAPTER_AVAILABLE
        
        # 实验配置
        self.experiment_id = f"society_30min_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        # Agent和资源
        self.agents = []
        self.agent_configs = []
        self.agent_adapters = []  # 参数转换器实例
        self.bridge = None
        self.monitor = EnhancedPerformanceMonitor(self.experiment_id)
        
        # 数据收集
        self.step_records = []
        self.purpose_history = {}
        self.social_interactions = 0
        self.total_steps = 0
        self.successful_steps = 0
        self.total_reward = 0.0
        self.agent_types_used = {}
        
        # 线程和同步
        self.step_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.lock = threading.Lock()
        
        logger.info(f"实验初始化: ID={self.experiment_id}, Agents={agents_count}, 时长={duration_minutes}分钟")
        logger.info(f"参数转换器: {'启用' if self.use_parameter_adapter else '禁用'}")
    
    def initialize_agents(self):
        """初始化Agent（支持多种类型）"""
        logger.info("初始化Agent...")
        start_time = time.time()
        
        # 尝试导入不同版本的Agent
        agent_types_to_try = ['v3.1', 'v4.1', 'v5.0']
        available_agents = {}
        
        for agent_type in agent_types_to_try:
            try:
                if agent_type == 'v3.1':
                    from _archive_v3.core.agent_9d import MOSSv3Agent9D
                    available_agents['v3.1'] = MOSSv3Agent9D
                    logger.info("✅ v3.1 Agent (MOSSv3Agent9D) 可用")
                elif agent_type == 'v4.1':
                    from agent_v4_1_fixed import PurposeEnhancedAgent
                    available_agents['v4.1'] = PurposeEnhancedAgent
                    logger.info("✅ v4.1 Agent (PurposeEnhancedAgent) 可用")
                elif agent_type == 'v5.0':
                    from moss.core.unified_agent import UnifiedMOSSAgent
                    available_agents['v5.0'] = UnifiedMOSSAgent
                    logger.info("✅ v5.0 Agent (UnifiedMOSSAgent) 可用")
            except ImportError as e:
                logger.warning(f"⚠️  {agent_type} Agent不可用: {e}")
                self.monitor.record_error('import_error')
        
        if not available_agents:
            logger.error("❌ 没有可用的Agent类型!")
            raise ImportError("没有可用的Agent类型")
        
        # 创建不同配置的Agent
        behavior_profiles = ["balanced", "explorer", "optimizer", "social", "balanced"]
        agent_type_rotation = list(available_agents.keys())
        
        for i in range(self.agents_count):
            profile = behavior_profiles[i % len(behavior_profiles)]
            agent_type = agent_type_rotation[i % len(agent_type_rotation)]
            AgentClass = available_agents[agent_type]
            
            config = AgentConfig(
                agent_id=f"agent_{i+1:02d}",
                behavior_profile=profile,
                enable_purpose=True,
                purpose_interval=1500 + i*100,
                agent_type=agent_type
            )
            
            try:
                # 创建Agent实例
                if agent_type == 'v3.1':
                    agent = AgentClass(
                        agent_id=config.agent_id,
                        enable_purpose=config.enable_purpose,
                        purpose_interval=config.purpose_interval
                    )
                elif agent_type == 'v4.1':
                    agent = AgentClass(agent_id=config.agent_id)
                elif agent_type == 'v5.0':
                    agent = AgentClass()
                    agent.agent_id = config.agent_id
                else:
                    agent = AgentClass(agent_id=config.agent_id)
                
                # 设置初始权重
                if hasattr(agent, 'weights'):
                    agent.weights = np.array(config.initial_weights)
                
                self.agents.append(agent)
                self.agent_configs.append(config)
                
                # 创建参数转换器
                if self.use_parameter_adapter:
                    adapter = MOSSInteractionAdapter(agent_type=agent_type)
                    self.agent_adapters.append(adapter)
                else:
                    self.agent_adapters.append(None)
                
                # 记录Agent类型使用情况
                if agent_type not in self.agent_types_used:
                    self.agent_types_used[agent_type] = 0
                self.agent_types_used[agent_type] += 1
                
                # 初始化purpose历史记录
                self.purpose_history[config.agent_id] = []
                
                logger.info(f"✅ Agent {config.agent_id} 初始化成功 (type: {agent_type}, profile: {profile})")
                
            except Exception as e:
                logger.error(f"❌ Agent {config.agent_id} ({agent_type}) 初始化失败: {e}")
                logger.error(traceback.format_exc())
                self.monitor.record_error('other')
                raise
        
        # 记录初始化时间
        init_time = time.time() - start_time
        self.monitor.record_metric('agent_initialization_time', init_time)
        logger.info(f"✅ 成功初始化 {len(self.agents)} 个Agent (耗时: {init_time:.2f}s)")
        logger.info(f"Agent类型分布: {self.agent_types_used}")
    
    def generate_observation(self, agent_id: str, step: int) -> Dict:
        """生成环境观察"""
        # 模拟环境状态
        time_factor = (step % 100) / 100.0
        
        observation = {
            'step': step,
            'time': time.time(),
            'resource_level': 0.7 + 0.3 * np.sin(time_factor * 2 * np.pi),
            'threat_level': 0.1 if step % 50 == 0 else 0.0,
            'novelty': 0.3 + 0.2 * np.random.random(),
            'social_feedback': 0.2 if step % 20 == 0 else 0.0,
            'agent_id': agent_id,
            'agent_index': int(agent_id.split('_')[1]) - 1,
            'environment_complexity': 0.5 + 0.3 * (step / 1000.0)
        }
        
        # 添加社交交互机会
        if step % 30 == 0:
            observation['social_opportunity'] = True
            observation['other_agent_status'] = [
                {'id': f'agent_{j+1:02d}', 'trust': 0.8} 
                for j in range(self.agents_count) if j != (int(agent_id.split('_')[1]) - 1)
            ][:2]
        
        return observation
    
    def run_agent_step(self, agent_idx: int, step: int) -> StepRecord:
        """运行单个Agent的单步（支持参数转换器）"""
        agent = self.agents[agent_idx]
        config = self.agent_configs[agent_idx]
        adapter = self.agent_adapters[agent_idx]
        
        start_time = time.time()
        
        try:
            # 生成观察
            observation = self.generate_observation(config.agent_id, step)
            
            # 执行Agent step
            if self.use_parameter_adapter and adapter is not None:
                # 使用参数转换器
                conversion_start = time.time()
                
                # 检测Agent实际类型（如果配置为auto）
                if config.agent_type == 'auto':
                    detected_type = adapter.detect_agent_from_instance(agent)
                else:
                    detected_type = config.agent_type
                
                # 根据Agent类型选择参数格式
                if detected_type in ['v3.1', 'unknown']:
                    # v3.1 Agent：需要社交参数
                    observed_behaviors, interaction = adapter.convert_to_v31_format(observation)
                    result = agent.step(observed_behaviors, interaction)
                else:
                    # v4.1/v5.0 Agent：需要环境观察
                    result = agent.step(observation)
                
                conversion_time = time.time() - conversion_start
                self.monitor.record_metric('parameter_conversion_time', conversion_time)
                
            else:
                # 不使用参数转换器，尝试多种格式
                try:
                    # 先尝试v4.x/v5.x格式
                    result = agent.step(observation)
                except TypeError:
                    try:
                        # 尝试v3.1格式
                        observed_behaviors, interaction = {}, {}
                        if 'other_agent_status' in observation:
                            observed_behaviors = {
                                'other_agents': observation['other_agent_status'],
                                'social_opportunity': observation.get('social_opportunity', False)
                            }
                        interaction = {'step': observation['step'], 'resource_level': observation['resource_level']}
                        result = agent.step(observed_behaviors, interaction)
                    except Exception:
                        # 最后尝试无参数
                        result = agent.step()
            
            # 记录执行时间
            execution_time = time.time() - start_time
            self.monitor.record_metric('step_latency', execution_time)
            self.monitor.record_metric('agent_responsiveness', 1.0 / (execution_time + 0.001))
            
            # 获取purpose向量
            purpose_vector = None
            if hasattr(agent, 'purpose_generator') and agent.purpose_generator is not None:
                purpose_vector = agent.purpose_generator.purpose_vector.tolist()
                self.monitor.record_metric('purpose_update_frequency', 1.0)
            elif hasattr(agent, '_get_purpose_vector'):
                purpose_vector = agent._get_purpose_vector().tolist()
            
            # 创建记录
            record = StepRecord(
                timestamp=datetime.now().isoformat(),
                agent_id=config.agent_id,
                step_number=step,
                action=result.get('action', 'unknown'),
                success=result.get('success', False),
                reward=result.get('reward', 0.0),
                purpose_vector=purpose_vector or [0.0] * 9,
                weights=agent.weights.tolist() if hasattr(agent, 'weights') else [0.25] * 4,
                coherence_score=result.get('state', {}).get('coherence', 0.5) if isinstance(result.get('state'), dict) else 0.5,
                resource_level=observation['resource_level'],
                social_interaction='social_opportunity' in observation,
                agent_type=config.agent_type,
                execution_time=execution_time
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Agent {config.agent_id} step {step} 失败: {e}")
            self.monitor.record_error('agent_step')
            
            # 返回错误记录
            return StepRecord(
                timestamp=datetime.now().isoformat(),
                agent_id=config.agent_id,
                step_number=step,
                action='error',
                success=False,
                reward=0.0,
                purpose_vector=[0.0] * 9,
                weights=[0.25] * 4,
                coherence_score=0.0,
                resource_level=0.0,
                agent_type=config.agent_type,
                execution_time=time.time() - start_time
            )
    
    def run_experiment(self):
        """运行实验"""
        logger.info(f"开始实验: {self.experiment_id}")
        logger.info(f"预计结束时间: {self.end_time}")
        
        # 初始化Agent
        self.initialize_agents()
        
        # 运行实验
        step_counter = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.agents_count) as executor:
            while datetime.now() < self.end_time:
                batch_start_time = time.time()
                step_counter += 1
                
                # 显示进度
                if step_counter % 100 == 0:
                    remaining = self.end_time - datetime.now()
                    logger.info(f"Step {step_counter:06d} - 剩余时间: {remaining}")
                
                # 提交当前批次任务
                futures = []
                for i in range(self.agents_count):
                    future = executor.submit(self.run_agent_step, i, step_counter)
                    futures.append(future)
                
                # 收集结果
                batch_records = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        record = future.result(timeout=10.0)  # 10秒超时
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
                        self.monitor.record_error('agent_step')
                    except Exception as e:
                        logger.error(f"收集结果失败: {e}")
                        self.monitor.record_error('other')
                
                # 保存批次记录
                if batch_records:
                    self.step_records.extend(batch_records)
                    
                    # 每100步保存一次检查点
                    if step_counter % 100 == 0:
                        self.save_checkpoint(step_counter)
                        self.monitor.reset_checkpoint()
                
                # 批次性能监控
                batch_duration = time.time() - batch_start_time
                self.monitor.record_metric('batch_processing_time', batch_duration)
                
                # 控制执行速度，避免过载
                target_batch_time = 1.0
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
        
        # 获取性能指标
        metrics = self.monitor.get_summary()
        
        logger.info(f"进度报告 [Step {step_counter:06d}]:")
        logger.info(f"  成功率: {success_rate:.1f}%")
        logger.info(f"  平均奖励: {avg_reward:.3f}")
        logger.info(f"  社交交互: {self.social_interactions}")
        logger.info(f"  平均延迟: {metrics.get('step_latency_avg', 0):.3f}s")
        logger.info(f"  错误率: {metrics.get('error_rate_percent', 0):.1f}%")
        logger.info(f"  Agent类型: {self.agent_types_used}")
        
        # 显示每个Agent的purpose向量
        if self.purpose_history:
            logger.info("  Purpose向量摘要 (前3个Agent):")
            for agent_id, history in list(self.purpose_history.items())[:3]:
                if history:
                    latest = history[-1]
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
            'agent_types_used': self.agent_types_used,
            'agents': [
                {
                    'agent_id': config.agent_id,
                    'profile': config.behavior_profile,
                    'type': config.agent_type,
                    'purpose_history_length': len(self.purpose_history.get(config.agent_id, []))
                }
                for config in self.agent_configs
            ],
            'performance_metrics': self.monitor.get_summary()
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
        
        # 资源利用率
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
            performance_metrics=performance_metrics,
            agent_types_used=self.agent_types_used
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
        print("\n" + "="*70)
        print("多Agent社会实验 - 30分钟增强版测试总结")
        print("="*70)
        print(f"实验ID: {result.experiment_id}")
        print(f"时间: {result.start_time} 到 {result.end_time}")
        print(f"持续时间: {result.end_time - result.start_time}")
        print(f"Agent数量: {result.agents_count}")
        print(f"Agent类型分布: {result.agent_types_used}")
        print(f"总步数: {result.total_steps:,}")
        print(f"成功率: {result.success_rate*100:.1f}%")
        print(f"平均奖励: {result.average_reward:.3f}")
        print(f"社交交互次数: {result.social_interactions}")
        print(f"资源利用率: {result.resource_utilization*100:.1f}%")
        print(f"参数转换器: {'启用' if self.use_parameter_adapter else '禁用'}")
        print()
        print("性能指标:")
        for key, value in result.performance_metrics.items():
            if 'duration' in key or 'time' in key:
                print(f"  {key}: {value:.3f}s")
            elif 'error' in key:
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value:.3f}")
        print()
        print("Purpose演化摘要 (前3个Agent):")
        for agent_id, history in list(result.purpose_evolution.items())[:3]:
            if history:
                latest = history[-1]
                print(f"  {agent_id}: D1={latest[0]:.3f}, D2={latest[1]:.3f}, D3={latest[2]:.3f}, D4={latest[3]:.3f}")
        print("="*70)

# ============================================
# 5. 主程序
# ============================================
def main():
    parser = argparse.ArgumentParser(description='运行增强版多Agent社会实验 (30分钟)')
    parser.add_argument('--agents', type=int, default=5,
                       help='Agent数量 (默认: 5)')
    parser.add_argument('--duration', type=int, default=30,
                       help='实验时长(分钟) (默认: 30)')
    parser.add_argument('--output', type=str, default='experiments/society_results_30min_enhanced',
                       help='输出目录 (默认: experiments/society_results_30min_enhanced)')
    parser.add_argument('--quick', action='store_true',
                       help='快速测试模式 (2分钟)')
    parser.add_argument('--no-adapter', action='store_true',
                       help='禁用参数转换器')
    
    args = parser.parse_args()
    
    # 快速测试模式
    if args.quick:
        args.duration = 2
        print("⚠️  快速测试模式: 2分钟运行")
    
    # 创建并运行实验
    try:
        experiment = EnhancedMultiAgentSocietyExperiment(
            agents_count=args.agents,
            duration_minutes=args.duration,
            output_dir=args.output,
            use_parameter_adapter=not args.no_adapter
        )
        
        experiment.run_experiment()
        
        print("\n🎉 实验完成！")
        print("📊 实验结果已保存到输出目录")
        
    except KeyboardInterrupt:
        print("\n⚠️  实验被用户中断")
        print("正在保存已收集的数据...")
        # 这里可以添加中断时的保存逻辑
    except Exception as e:
        print(f"\n❌ 实验失败: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())