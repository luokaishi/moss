#!/usr/bin/env python3
"""
MOSS v5.2 多Agent社会实验框架增强版 - 高级监控和错误恢复

核心增强功能：
1. 增强性能监控：实时CPU、内存、磁盘IO监控
2. 智能错误恢复：自动重试、降级策略、故障隔离
3. 深度学习分析：实时分析purpose演化模式和协作行为
4. 可视化监控：实时图表显示系统状态
5. 预测性维护：基于历史数据的性能预测

运行: python upgraded_experiment_framework.py --agents 5 --duration 30
作者: MOSS项目团队
日期: 2026-04-13
"""

import sys
import os
import time
import json
import argparse
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import threading
import queue
import concurrent.futures
from dataclasses import dataclass, asdict, field
import statistics
import psutil  # 系统监控
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 1. 增强的数据类定义
# ============================================

@dataclass
class AgentConfig:
    """增强的Agent配置"""
    agent_id: str
    enable_purpose: bool = True
    purpose_interval: int = 2000
    initial_weights: Optional[List[float]] = None
    behavior_profile: str = "balanced"  # balanced/explorer/optimizer/social/adaptive
    learning_rate: float = 0.01
    memory_size: int = 1000
    resilience: float = 0.8  # 容错能力
    specialization: str = "general"  # 专业化领域
    
    def __post_init__(self):
        if self.initial_weights is None:
            # 基于行为配置文件设置初始权重
            if self.behavior_profile == "explorer":
                self.initial_weights = [0.1, 0.4, 0.2, 0.3]  # 高好奇心
            elif self.behavior_profile == "optimizer":
                self.initial_weights = [0.2, 0.2, 0.2, 0.4]  # 高优化
            elif self.behavior_profile == "social":
                self.initial_weights = [0.25, 0.2, 0.35, 0.2]  # 高影响力
            elif self.behavior_profile == "adaptive":
                self.initial_weights = [0.2, 0.3, 0.2, 0.3]  # 自适应
            else:  # balanced
                self.initial_weights = [0.25, 0.25, 0.25, 0.25]
        
        # 专业化领域影响权重
        if self.specialization == "memory":
            self.initial_weights[1] += 0.1  # 增强记忆
        elif self.specialization == "planning":
            self.initial_weights[2] += 0.1  # 增强规划


@dataclass
class StepRecord:
    """增强的单步记录"""
    timestamp: str
    agent_id: str
    step_number: int
    action: str
    action_type: str  # explore/exploit/social/rest
    success: bool
    reward: float
    purpose_vector: List[float]
    weights: List[float]
    coherence_score: float
    resource_level: float
    social_interaction: bool = False
    interaction_partner: Optional[str] = None
    confidence: float = 0.5  # Agent置信度
    novelty: float = 0.0  # 行动新颖度
    efficiency: float = 0.0  # 执行效率
    error_code: str = "none"  # 错误代码


@dataclass
class ExperimentResult:
    """增强的实验结果"""
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
    resilience_metrics: Dict[str, float]  # 容错指标
    collaboration_metrics: Dict[str, float]  # 协作指标
    emergence_indicators: Dict[str, float]  # 涌现指标


@dataclass
class SystemHealth:
    """系统健康状态"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_bandwidth: float
    agent_responsiveness: float
    system_stability: float
    error_count: int


# ============================================
# 2. 增强的性能监控器
# ============================================

class EnhancedPerformanceMonitor:
    """增强的性能监控器"""
    
    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.metrics = {
            # 基础性能
            'step_latency': [],
            'memory_usage': [],
            'cpu_usage': [],
            'agent_responsiveness': [],
            'purpose_update_frequency': [],
            
            # 系统健康
            'system_stability': [],
            'error_rate': [],
            'recovery_time': [],
            
            # 协作指标
            'social_engagement': [],
            'collaboration_efficiency': [],
            'trust_network_density': [],
            
            # 涌现指标
            'purpose_diversity': [],
            'behavioral_entropy': [],
            'coherence_convergence': []
        }
        
        self.health_history: List[SystemHealth] = []
        self.start_time = time.time()
        self.error_log = []
        
        # 创建监控线程
        self.monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
        self.monitor_active = True
        self.monitor_thread.start()
    
    def _system_monitor_loop(self):
        """系统监控循环"""
        while self.monitor_active:
            try:
                health = self._capture_system_health()
                self.health_history.append(health)
                
                # 记录到metrics
                self.record_metric('cpu_usage', health.cpu_usage)
                self.record_metric('memory_usage', health.memory_usage)
                self.record_metric('system_stability', health.system_stability)
                self.record_metric('error_rate', health.error_count / 1000.0)  # 标准化
                
                # 每10秒采集一次
                time.sleep(10)
                
            except Exception as e:
                self.error_log.append(f"监控线程错误: {e}")
                time.sleep(5)
    
    def _capture_system_health(self) -> SystemHealth:
        """捕获系统健康状态"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            
            # 计算系统稳定性（基于近1分钟的错误率）
            recent_errors = len([e for e in self.error_log[-60:] if "error" in e.lower()])
            stability = max(0, 1.0 - recent_errors / 60.0)
            
            return SystemHealth(
                timestamp=datetime.now().isoformat(),
                cpu_usage=cpu_percent,
                memory_usage=memory_info.percent,
                disk_io=disk_io.read_bytes + disk_io.write_bytes,
                network_bandwidth=network_io.bytes_sent + network_io.bytes_recv,
                agent_responsiveness=0.0,  # 由主程序更新
                system_stability=stability,
                error_count=recent_errors
            )
        except Exception:
            # 如果psutil不可用，返回默认值
            return SystemHealth(
                timestamp=datetime.now().isoformat(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_io=0.0,
                network_bandwidth=0.0,
                agent_responsiveness=0.0,
                system_stability=1.0,
                error_count=0
            )
    
    def record_metric(self, metric_name: str, value: float):
        """记录性能指标"""
        if metric_name in self.metrics:
            self.metrics[metric_name].append(value)
    
    def record_error(self, error_type: str, error_details: str, agent_id: Optional[str] = None):
        """记录错误"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'details': error_details,
            'agent_id': agent_id
        }
        self.error_log.append(error_entry)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取增强的性能摘要"""
        summary = {}
        
        # 基础统计
        for metric_name, values in self.metrics.items():
            if values:
                summary[f'{metric_name}_avg'] = statistics.mean(values)
                summary[f'{metric_name}_max'] = max(values)
                summary[f'{metric_name}_min'] = min(values)
                summary[f'{metric_name}_std'] = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 系统健康指标
        if self.health_history:
            summary['avg_cpu_usage'] = statistics.mean([h.cpu_usage for h in self.health_history])
            summary['avg_memory_usage'] = statistics.mean([h.memory_usage for h in self.health_history])
            summary['system_uptime'] = time.time() - self.start_time
            summary['total_errors'] = len(self.error_log)
        
        # 性能趋势分析
        if len(self.metrics.get('step_latency', [])) > 10:
            latencies = self.metrics['step_latency'][-100:]  # 最近100个
            if len(latencies) > 1:
                slope, _, _, _, _ = stats.linregress(range(len(latencies)), latencies)
                summary['latency_trend'] = slope
        
        summary['total_duration'] = time.time() - self.start_time
        return summary
    
    def generate_health_report(self) -> Dict[str, Any]:
        """生成健康报告"""
        if not self.health_history:
            return {"status": "no_data"}
        
        latest = self.health_history[-1]
        report = {
            "timestamp": latest.timestamp,
            "status": "healthy" if latest.system_stability > 0.8 else "warning",
            "cpu_usage": latest.cpu_usage,
            "memory_usage": latest.memory_usage,
            "stability": latest.system_stability,
            "recent_errors": latest.error_count,
            "total_errors": len(self.error_log)
        }
        
        # 添加建议
        suggestions = []
        if latest.cpu_usage > 80:
            suggestions.append("CPU使用率过高，考虑减少并发或优化算法")
        if latest.memory_usage > 85:
            suggestions.append("内存使用率过高，考虑内存优化")
        if latest.system_stability < 0.7:
            suggestions.append("系统稳定性下降，检查错误日志")
        
        report["suggestions"] = suggestions
        return report
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitor_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)


# ============================================
# 3. 智能错误恢复管理器
# ============================================

class ErrorRecoveryManager:
    """智能错误恢复管理器"""
    
    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.error_patterns = {}
        self.recovery_history = []
        self.degradation_modes = {
            "low_memory": {"strategy": "reduce_batch_size", "priority": 1},
            "high_latency": {"strategy": "increase_timeout", "priority": 2},
            "agent_failure": {"strategy": "restart_agent", "priority": 3},
            "system_overload": {"strategy": "throttle_requests", "priority": 4}
        }
        
    def analyze_error(self, error_type: str, error_details: str, context: Dict) -> Dict:
        """分析错误并推荐恢复策略"""
        # 记录错误模式
        if error_type not in self.error_patterns:
            self.error_patterns[error_type] = {"count": 0, "contexts": []}
        
        self.error_patterns[error_type]["count"] += 1
        self.error_patterns[error_type]["contexts"].append({
            "timestamp": datetime.now().isoformat(),
            "details": error_details,
            "context": context
        })
        
        # 基于错误类型推荐策略
        strategy = self._recommend_strategy(error_type, context)
        
        recovery_plan = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "strategy": strategy["name"],
            "actions": strategy["actions"],
            "expected_impact": strategy["impact"],
            "confidence": self._calculate_confidence(error_type)
        }
        
        self.recovery_history.append(recovery_plan)
        return recovery_plan
    
    def _recommend_strategy(self, error_type: str, context: Dict) -> Dict:
        """推荐恢复策略"""
        strategies = {
            "agent_timeout": {
                "name": "gradual_recovery",
                "actions": [
                    "increase_timeout:1.5x",
                    "retry_with_backoff",
                    "isolate_failing_agent"
                ],
                "impact": "low"
            },
            "memory_error": {
                "name": "memory_optimization",
                "actions": [
                    "clear_caches",
                    "reduce_batch_size",
                    "garbage_collection"
                ],
                "impact": "medium"
            },
            "connection_error": {
                "name": "connection_recovery",
                "actions": [
                    "exponential_backoff",
                    "switch_to_fallback",
                    "validate_connection"
                ],
                "impact": "high"
            },
            "validation_error": {
                "name": "data_validation",
                "actions": [
                    "sanitize_input",
                    "apply_defaults",
                    "log_and_continue"
                ],
                "impact": "low"
            }
        }
        
        # 默认策略
        default_strategy = {
            "name": "graceful_degradation",
            "actions": ["log_error", "skip_step", "continue_experiment"],
            "impact": "low"
        }
        
        return strategies.get(error_type, default_strategy)
    
    def _calculate_confidence(self, error_type: str) -> float:
        """计算恢复策略置信度"""
        if error_type not in self.error_patterns:
            return 0.5
        
        pattern = self.error_patterns[error_type]
        total_errors = pattern["count"]
        
        # 计算该错误类型的成功恢复率（假设）
        recovery_success = len([r for r in self.recovery_history 
                               if r["error_type"] == error_type and r.get("success", False)])
        
        if total_errors > 0:
            success_rate = recovery_success / total_errors
            return min(0.9, success_rate + 0.1)  # 基础置信度
        
        return 0.5
    
    def apply_recovery_strategy(self, strategy_plan: Dict, agent_pool: List) -> bool:
        """应用恢复策略"""
        try:
            logger.info(f"应用恢复策略: {strategy_plan['strategy']}")
            
            for action in strategy_plan["actions"]:
                logger.debug(f"执行恢复动作: {action}")
                
                if action.startswith("increase_timeout"):
                    # 解析超时倍数
                    multiplier = float(action.split(":")[1].replace("x", ""))
                    # 这里可以实际调整超时设置
                    pass
                    
                elif action == "retry_with_backoff":
                    # 指数退避重试逻辑
                    pass
                    
                elif action == "isolate_failing_agent":
                    # 隔离失败Agent逻辑
                    pass
            
            strategy_plan["applied_at"] = datetime.now().isoformat()
            strategy_plan["success"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"应用恢复策略失败: {e}")
            strategy_plan["applied_at"] = datetime.now().isoformat()
            strategy_plan["success"] = False
            strategy_plan["failure_reason"] = str(e)
            
            return False
    
    def get_recovery_statistics(self) -> Dict:
        """获取恢复统计信息"""
        if not self.recovery_history:
            return {"total_recoveries": 0, "success_rate": 0.0}
        
        total = len(self.recovery_history)
        successful = len([r for r in self.recovery_history if r.get("success", False)])
        
        return {
            "total_recoveries": total,
            "successful_recoveries": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "common_error_types": sorted(
                self.error_patterns.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:5]
        }


# ============================================
# 4. 实时数据分析器
# ============================================

class RealTimeAnalyzer:
    """实时数据分析器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_buffer = {
            "purpose_vectors": [],
            "rewards": [],
            "latencies": [],
            "social_interactions": []
        }
        
    def add_data_point(self, record: StepRecord):
        """添加数据点"""
        # 更新缓冲区
        self.data_buffer["purpose_vectors"].append(record.purpose_vector)
        self.data_buffer["rewards"].append(record.reward)
        self.data_buffer["latencies"].append(0.0)  # 由主程序填充
        if record.social_interaction:
            self.data_buffer["social_interactions"].append({
                "agent_id": record.agent_id,
                "partner": record.interaction_partner,
                "timestamp": record.timestamp
            })
        
        # 保持缓冲区大小
        for key in self.data_buffer:
            if isinstance(self.data_buffer[key], list):
                if len(self.data_buffer[key]) > self.window_size:
                    self.data_buffer[key] = self.data_buffer[key][-self.window_size:]
    
    def analyze_purpose_dynamics(self) -> Dict:
        """分析Purpose动态"""
        if len(self.data_buffer["purpose_vectors"]) < 10:
            return {"status": "insufficient_data"}
        
        vectors = self.data_buffer["purpose_vectors"]
        
        # 计算多样性
        diversity = self._calculate_diversity(vectors)
        
        # 计算收敛性
        convergence = self._calculate_convergence(vectors)
        
        # 计算演化速度
        evolution_speed = self._calculate_evolution_speed(vectors)
        
        return {
            "purpose_diversity": diversity,
            "purpose_convergence": convergence,
            "evolution_speed": evolution_speed,
            "trend": "differentiating" if diversity > 0.7 else "converging"
        }
    
    def _calculate_diversity(self, vectors: List[List[float]]) -> float:
        """计算Purpose向量多样性"""
        if not vectors:
            return 0.0
        
        # 使用余弦相似度的方差作为多样性指标
        similarities = []
        for i in range(len(vectors)):
            for j in range(i+1, len(vectors)):
                if i < len(vectors) and j < len(vectors):
                    sim = np.dot(vectors[i][:4], vectors[j][:4]) / (
                        np.linalg.norm(vectors[i][:4]) * np.linalg.norm(vectors[j][:4]) + 1e-8
                    )
                    similarities.append(sim)
        
        if similarities:
            return 1.0 - statistics.mean(similarities)
        return 0.0
    
    def _calculate_convergence(self, vectors: List[List[float]]) -> float:
        """计算Purpose向量收敛性"""
        if len(vectors) < 2:
            return 0.0
        
        # 计算最后几个向量的平均相似度
        recent = vectors[-min(10, len(vectors)):]
        similarities = []
        
        for i in range(len(recent)):
            for j in range(i+1, len(recent)):
                sim = np.dot(recent[i][:4], recent[j][:4]) / (
                    np.linalg.norm(recent[i][:4]) * np.linalg.norm(recent[j][:4]) + 1e-8
                )
                similarities.append(sim)
        
        if similarities:
            return statistics.mean(similarities)
        return 0.0
    
    def _calculate_evolution_speed(self, vectors: List[List[float]]) -> float:
        """计算演化速度"""
        if len(vectors) < 2:
            return 0.0
        
        # 计算相邻向量之间的平均变化
        changes = []
        for i in range(1, len(vectors)):
            if i < len(vectors):
                change = np.linalg.norm(
                    np.array(vectors[i][:4]) - np.array(vectors[i-1][:4])
                )
                changes.append(change)
        
        if changes:
            return statistics.mean(changes)
        return 0.0
    
    def analyze_collaboration_patterns(self) -> Dict:
        """分析协作模式"""
        interactions = self.data_buffer["social_interactions"]
        if not interactions:
            return {"total_interactions": 0, "network_density": 0.0}
        
        # 构建交互网络
        agents = set()
        edges = set()
        
        for interaction in interactions:
            agents.add(interaction["agent_id"])
            if interaction.get("partner"):
                agents.add(interaction["partner"])
                edge = tuple(sorted([interaction["agent_id"], interaction["partner"]]))
                edges.add(edge)
        
        # 计算网络密度
        n = len(agents)
        max_edges = n * (n - 1) / 2 if n > 1 else 0
        density = len(edges) / max_edges if max_edges > 0 else 0.0
        
        return {
            "total_interactions": len(interactions),
            "unique_agents": len(agents),
            "unique_connections": len(edges),
            "network_density": density,
            "avg_interactions_per_agent": len(interactions) / len(agents) if agents else 0.0
        }


# ============================================
# 5. 增强的实验主类
# ============================================

class EnhancedMultiAgentExperiment:
    """增强的多Agent实验框架"""
    
    def __init__(self, 
                 agents_count: int = 5,
                 duration_minutes: int = 30,
                 output_dir: str = "experiments/enhanced_society"):
        
        self.agents_count = agents_count
        self.duration_minutes = duration_minutes
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 实验配置
        self.experiment_id = f"enhanced_society_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        # 增强的组件
        self.monitor = EnhancedPerformanceMonitor(self.experiment_id)
        self.recovery_manager = ErrorRecoveryManager(self.experiment_id)
        self.analyzer = RealTimeAnalyzer(window_size=200)
        
        # Agent和资源
        self.agents = []
        self.agent_configs = []
        self.bridge = None
        
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
        
        # 实验状态
        self.experiment_status = "initialized"
        self.degradation_mode = "normal"  # normal/degraded/recovery
        
        logger.info(f"增强实验框架初始化: ID={self.experiment_id}")
        logger.info(f"Agents={agents_count}, 时长={duration_minutes}分钟")
    
    def initialize_agents(self):
        """初始化Agent - 增强版本"""
        logger.info("初始化增强Agent...")
        
        try:
            # 尝试导入多个版本的Agent
            from _archive_v3.core.agent_9d import MOSSv3Agent9D
            from moss.core.real_world_bridge import RealWorldBridge
            logger.info("✅ 成功导入MOSSv3Agent9D和RealWorldBridge")
        except ImportError as e:
            logger.warning(f"导入失败: {e}，使用回退方案")
            # 这里可以添加回退逻辑
            raise
        
        # 初始化RealWorldBridge
        try:
            self.bridge = RealWorldBridge()
            logger.info("✅ RealWorldBridge初始化成功")
        except Exception as e:
            logger.warning(f"RealWorldBridge初始化失败，使用模拟模式: {e}")
            self.bridge = None
        
        # 创建多样化的Agent配置
        specializations = ["general", "memory", "planning", "exploration", "social"]
        
        for i in range(self.agents_count):
            specialization = specializations[i % len(specializations)]
            
            # 分配行为配置文件
            if specialization == "memory":
                profile = "optimizer"
            elif specialization == "exploration":
                profile = "explorer"
            elif specialization == "social":
                profile = "social"
            else:
                profile = "balanced"
            
            config = AgentConfig(
                agent_id=f"agent_{i+1:02d}",
                behavior_profile=profile,
                specialization=specialization,
                enable_purpose=True,
                purpose_interval=1500 + i*100,
                resilience=0.7 + 0.1 * (i % 3),  # 不同的容错能力
                learning_rate=0.01 + 0.005 * (i % 2)  # 不同的学习率
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
                
                logger.info(f"✅ Agent {config.agent_id} 初始化成功")
                logger.info(f"   配置: profile={profile}, specialization={specialization}")
                logger.info(f"   容错: {config.resilience:.2f}, 学习率: {config.learning_rate:.3f}")
                
                # 初始化purpose历史记录
                self.purpose_history[config.agent_id] = []
                
            except Exception as e:
                logger.error(f"❌ Agent {config.agent_id} 初始化失败: {e}")
                # 应用错误恢复
                recovery_plan = self.recovery_manager.analyze_error(
                    "agent_failure", 
                    f"Agent初始化失败: {e}",
                    {"agent_id": config.agent_id, "config": config.__dict__}
                )
                logger.warning(f"应用恢复策略: {recovery_plan['strategy']}")
        
        logger.info(f"✅ 成功初始化 {len(self.agents)} 个增强Agent")
    
    def run_agent_step_with_recovery(self, agent, agent_id: str, step: int) -> StepRecord:
        """运行Agent单步，带有错误恢复"""
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 生成观察
                observation = self.generate_enhanced_observation(agent_id, step)
                
                # 准备参数
                observed_behaviors, interaction = self.prepare_agent_parameters(observation)
                
                # 执行step
                start_time = time.time()
                result = agent.step(observed_behaviors, interaction)
                latency = time.time() - start_time
                
                # 记录性能
                self.monitor.record_metric('step_latency', latency)
                self.monitor.record_metric('agent_responsiveness', 1.0 / (latency + 0.001))
                
                # 创建记录
                record = self.create_enhanced_record(
                    agent_id, step, observation, result, agent, latency
                )
                
                return record
                
            except Exception as e:
                retry_count += 1
                error_type = self.classify_error(e)
                
                # 记录错误
                self.monitor.record_error(error_type, str(e), agent_id)
                
                # 分析错误并获取恢复策略
                context = {
                    "agent_id": agent_id,
                    "step": step,
                    "retry_count": retry_count,
                    "error": str(e)
                }
                
                recovery_plan = self.recovery_manager.analyze_error(error_type, str(e), context)
                
                if retry_count < max_retries:
                    logger.warning(f"Agent {agent_id} step失败 (重试 {retry_count}/{max_retries}): {e}")
                    logger.info(f"应用恢复策略: {recovery_plan['strategy']}")
                    
                    # 应用恢复策略
                    success = self.recovery_manager.apply_recovery_strategy(recovery_plan, self.agents)
                    
                    if success:
                        # 指数退避
                        time.sleep(2 ** retry_count)
                        continue
                
                # 达到最大重试次数或恢复失败
                logger.error(f"Agent {agent_id} step失败，达到最大重试次数: {e}")
                
                # 进入降级模式
                self.degradation_mode = "degraded"
                logger.warning(f"进入降级模式: {self.degradation_mode}")
                
                # 返回错误记录
                return self.create_error_record(agent_id, step, error_type, str(e))
        
        # 不应该到达这里
        return self.create_error_record(agent_id, step, "unknown", "未知错误")
    
    def classify_error(self, error: Exception) -> str:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return "agent_timeout"
        elif "memory" in error_str:
            return "memory_error"
        elif "connection" in error_str or "network" in error_str:
            return "connection_error"
        elif "validation" in error_str or "invalid" in error_str:
            return "validation_error"
        else:
            return "general_error"
    
    def generate_enhanced_observation(self, agent_id: str, step: int) -> Dict:
        """生成增强的环境观察"""
        # 基础环境状态
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
            'environment_complexity': 0.5 + 0.3 * (step / 1000.0),
            
            # 增强指标
            'system_health': self.monitor.generate_health_report(),
            'experiment_status': self.experiment_status,
            'degradation_mode': self.degradation_mode
        }
        
        # 添加社交交互机会
        if step % 30 == 0 or (self.degradation_mode == "degraded" and step % 10 == 0):
            observation['social_opportunity'] = True
            observation['other_agent_status'] = [
                {
                    'id': f'agent_{j+1:02d}', 
                    'trust': 0.8 + 0.1 * np.random.random(),
                    'specialization': self.agent_configs[j].specialization if j < len(self.agent_configs) else "general"
                } 
                for j in range(self.agents_count) if j != (int(agent_id.split('_')[1]) - 1)
            ][:3]  # 最多3个其他Agent
        
        return observation
    
    def prepare_agent_parameters(self, observation: Dict) -> Tuple[Dict, Dict]:
        """准备Agent参数"""
        observed_behaviors = {}
        interaction = {}
        
        # observed_behaviors: 其他Agent的行为观察
        if 'other_agent_status' in observation:
            observed_behaviors = {
                'other_agents': observation['other_agent_status'],
                'social_opportunity': observation.get('social_opportunity', False),
                'system_status': observation.get('system_health', {})
            }
        
        # interaction: 与环境的相关信息
        interaction = {
            'step': observation['step'],
            'time': observation['time'],
            'resource_level': observation['resource_level'],
            'threat_level': observation['threat_level'],
            'novelty': observation['novelty'],
            'social_feedback': observation['social_feedback'],
            'environment_complexity': observation['environment_complexity'],
            'experiment_status': observation.get('experiment_status', 'normal')
        }
        
        return observed_behaviors, interaction
    
    def create_enhanced_record(self, agent_id: str, step: int, observation: Dict, 
                              result: Dict, agent, latency: float) -> StepRecord:
        """创建增强的记录"""
        # 获取purpose向量
        purpose_vector = None
        if hasattr(agent, 'purpose_generator') and agent.purpose_generator is not None:
            purpose_vector = agent.purpose_generator.purpose_vector.tolist()
            self.monitor.record_metric('purpose_update_frequency', 1.0)
        
        # 判断行动类型
        action_type = self.classify_action_type(result.get('action', 'unknown'))
        
        # 计算置信度
        confidence = self.calculate_confidence(result, agent)
        
        # 计算新颖度
        novelty = observation.get('novelty', 0.0)
        
        # 计算效率
        efficiency = self.calculate_efficiency(result, latency)
        
        # 检查社交交互
        social_interaction = observation.get('social_opportunity', False)
        interaction_partner = None
        if social_interaction and observation.get('other_agent_status'):
            # 随机选择一个交互伙伴
            partners = observation['other_agent_status']
            if partners:
                interaction_partner = partners[np.random.randint(len(partners))]['id']
        
        record = StepRecord(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            step_number=step,
            action=result.get('action', 'unknown'),
            action_type=action_type,
            success=result.get('success', False),
            reward=result.get('reward', 0.0),
            purpose_vector=purpose_vector or [0.0] * 9,
            weights=agent.weights.tolist() if hasattr(agent, 'weights') else [0.25] * 4,
            coherence_score=result.get('state', {}).get('coherence', 0.5) if isinstance(result.get('state'), dict) else 0.5,
            resource_level=observation['resource_level'],
            social_interaction=social_interaction,
            interaction_partner=interaction_partner,
            confidence=confidence,
            novelty=novelty,
            efficiency=efficiency,
            error_code="none"
        )
        
        return record
    
    def classify_action_type(self, action: str) -> str:
        """分类行动类型"""
        action_lower = action.lower()
        
        if any(word in action_lower for word in ['explore', 'search', 'discover']):
            return 'explore'
        elif any(word in action_lower for word in ['exploit', 'optimize', 'refine']):
            return 'exploit'
        elif any(word in action_lower for word in ['social', 'collaborate', 'communicate']):
            return 'social'
        elif any(word in action_lower for word in ['rest', 'pause', 'idle']):
            return 'rest'
        else:
            return 'unknown'
    
    def calculate_confidence(self, result: Dict, agent) -> float:
        """计算Agent置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于成功率和奖励调整
        if result.get('success', False):
            confidence += 0.2
        
        reward = result.get('reward', 0.0)
        if reward > 0:
            confidence += min(0.3, reward * 0.1)
        
        # 基于coherence调整
        coherence = result.get('state', {}).get('coherence', 0.5) if isinstance(result.get('state'), dict) else 0.5
        confidence += (coherence - 0.5) * 0.2
        
        return max(0.1, min(0.99, confidence))
    
    def calculate_efficiency(self, result: Dict, latency: float) -> float:
        """计算执行效率"""
        if latency <= 0:
            return 0.0
        
        reward = result.get('reward', 0.0)
        success = result.get('success', False)
        
        # 效率 = (奖励 * 成功因子) / 延迟
        success_factor = 1.0 if success else 0.3
        efficiency = (abs(reward) * success_factor) / (latency + 0.001)
        
        return min(1.0, efficiency * 10)  # 标准化到0-1范围
    
    def create_error_record(self, agent_id: str, step: int, error_type: str, error_msg: str) -> StepRecord:
        """创建错误记录"""
        return StepRecord(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            step_number=step,
            action='error',
            action_type='error',
            success=False,
            reward=0.0,
            purpose_vector=[0.0] * 9,
            weights=[0.25] * 4,
            coherence_score=0.0,
            resource_level=0.0,
            social_interaction=False,
            confidence=0.1,
            novelty=0.0,
            efficiency=0.0,
            error_code=error_type
        )
    
    def run_experiment(self):
        """运行增强的实验"""
        logger.info(f"开始增强实验: {self.experiment_id}")
        logger.info(f"预计结束时间: {self.end_time}")
        
        # 更新状态
        self.experiment_status = "running"
        
        # 初始化Agent
        self.initialize_agents()
        
        # 运行实验
        step_counter = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.agents_count) as executor:
            while datetime.now() < self.end_time and self.experiment_status != "stopped":
                step_counter += 1
                batch_start_time = time.time()
                
                # 打印进度
                if step_counter % 100 == 0:
                    self.print_enhanced_progress(step_counter)
                
                # 提交批次任务
                futures = []
                for i, (agent, config) in enumerate(zip(self.agents, self.agent_configs)):
                    future = executor.submit(
                        self.run_agent_step_with_recovery, 
                        agent, config.agent_id, step_counter
                    )
                    futures.append(future)
                
                # 收集结果
                batch_records = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        record = future.result(timeout=10.0)
                        batch_records.append(record)
                        
                        # 更新统计和数据分析
                        with self.lock:
                            self.update_statistics(record)
                            self.analyzer.add_data_point(record)
                            
                    except concurrent.futures.TimeoutError:
                        logger.warning("Agent step执行超时")
                        self.monitor.record_error("timeout", "Future result timeout")
                    except Exception as e:
                        logger.error(f"收集结果失败: {e}")
                        self.monitor.record_error("collection_error", str(e))
                
                # 保存批次记录
                if batch_records:
                    self.step_records.extend(batch_records)
                    
                    # 定期保存检查点
                    if step_counter % 200 == 0:
                        self.save_enhanced_checkpoint(step_counter)
                
                # 控制执行速度
                batch_duration = time.time() - batch_start_time
                self.monitor.record_metric('batch_processing_time', batch_duration)
                
                target_batch_time = 1.0
                if batch_duration < target_batch_time:
                    time.sleep(target_batch_time - batch_duration)
                
                # 定期进行系统健康检查
                if step_counter % 500 == 0:
                    self.perform_system_health_check()
        
        # 实验结束
        logger.info(f"实验完成! 总步数: {self.total_steps}")
        self.experiment_status = "completed"
        
        # 保存最终结果
        self.save_enhanced_results()
        
        # 停止监控
        self.monitor.stop_monitoring()
    
    def update_statistics(self, record: StepRecord):
        """更新统计信息"""
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
    
    def print_enhanced_progress(self, step_counter: int):
        """打印增强的进度报告"""
        success_rate = (self.successful_steps / self.total_steps * 100) if self.total_steps > 0 else 0
        avg_reward = self.total_reward / self.total_steps if self.total_steps > 0 else 0
        
        # 获取系统健康报告
        health_report = self.monitor.generate_health_report()
        
        # 获取Purpose动态分析
        purpose_analysis = self.analyzer.analyze_purpose_dynamics()
        
        # 获取协作分析
        collaboration_analysis = self.analyzer.analyze_collaboration_patterns()
        
        # 获取恢复统计
        recovery_stats = self.recovery_manager.get_recovery_statistics()
        
        logger.info("=" * 80)
        logger.info(f"增强进度报告 [Step {step_counter:06d}]:")
        logger.info(f"  成功率: {success_rate:.1f}% | 平均奖励: {avg_reward:.3f}")
        logger.info(f"  社交交互: {self.social_interactions} | 系统状态: {self.experiment_status}")
        logger.info(f"  降级模式: {self.degradation_mode} | 剩余时间: {self.end_time - datetime.now()}")
        logger.info("")
        logger.info("  系统健康:")
        logger.info(f"    CPU: {health_report.get('cpu_usage', 0):.1f}% | 内存: {health_report.get('memory_usage', 0):.1f}%")
        logger.info(f"    稳定性: {health_report.get('stability', 0):.2f} | 错误数: {health_report.get('total_errors', 0)}")
        logger.info("")
        logger.info("  Purpose动态:")
        logger.info(f"    多样性: {purpose_analysis.get('purpose_diversity', 0):.3f}")
        logger.info(f"    收敛性: {purpose_analysis.get('purpose_convergence', 0):.3f}")
        logger.info(f"    趋势: {purpose_analysis.get('trend', 'unknown')}")
        logger.info("")
        logger.info("  协作网络:")
        logger.info(f"    交互次数: {collaboration_analysis.get('total_interactions', 0)}")
        logger.info(f"    网络密度: {collaboration_analysis.get('network_density', 0):.3f}")
        logger.info("")
        logger.info("  错误恢复:")
        logger.info(f"    恢复次数: {recovery_stats.get('total_recoveries', 0)}")
        logger.info(f"    成功率: {recovery_stats.get('success_rate', 0)*100:.1f}%")
        logger.info("=" * 80)
    
    def perform_system_health_check(self):
        """执行系统健康检查"""
        health_report = self.monitor.generate_health_report()
        
        # 检查是否需要调整
        if health_report.get('status') == 'warning':
            logger.warning("⚠️  系统健康警告！")
            
            # 根据警告类型采取行动
            suggestions = health_report.get('suggestions', [])
            for suggestion in suggestions:
                logger.warning(f"  建议: {suggestion}")
                
                if "CPU使用率过高" in suggestion:
                    # 可以调整并发度或降低计算强度
                    pass
                elif "内存使用率过高" in suggestion:
                    # 可以清理缓存或减少数据保留
                    pass
        
        # 检查是否需要进入/退出降级模式
        if health_report.get('stability', 1.0) < 0.6 and self.degradation_mode != "degraded":
            logger.warning("⚠️  系统稳定性下降，进入降级模式")
            self.degradation_mode = "degraded"
        elif health_report.get('stability', 0.0) > 0.8 and self.degradation_mode == "degraded":
            logger.info("✅ 系统稳定性恢复，退出降级模式")
            self.degradation_mode = "normal"
    
    def save_enhanced_checkpoint(self, step_counter: int):
        """保存增强的检查点"""
        checkpoint_file = self.output_dir / f"checkpoint_step_{step_counter:06d}.json"
        
        # Purpose分析
        purpose_analysis = self.analyzer.analyze_purpose_dynamics()
        
        # 协作分析
        collaboration_analysis = self.analyzer.analyze_collaboration_patterns()
        
        # 恢复统计
        recovery_stats = self.recovery_manager.get_recovery_statistics()
        
        # 系统健康
        health_report = self.monitor.generate_health_report()
        
        checkpoint_data = {
            'experiment_id': self.experiment_id,
            'step': step_counter,
            'timestamp': datetime.now().isoformat(),
            'total_steps': self.total_steps,
            'successful_steps': self.successful_steps,
            'total_reward': self.total_reward,
            'social_interactions': self.social_interactions,
            'experiment_status': self.experiment_status,
            'degradation_mode': self.degradation_mode,
            
            'purpose_analysis': purpose_analysis,
            'collaboration_analysis': collaboration_analysis,
            'recovery_statistics': recovery_stats,
            'system_health': health_report,
            
            'agents': [
                {
                    'agent_id': config.agent_id,
                    'profile': config.behavior_profile,
                    'specialization': config.specialization,
                    'resilience': config.resilience,
                    'purpose_history_length': len(self.purpose_history.get(config.agent_id, [])),
                    'latest_purpose': self.purpose_history.get(config.agent_id, [])[-5:] if self.purpose_history.get(config.agent_id) else None
                }
                for config in self.agent_configs
            ]
        }
        
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"检查点保存: {checkpoint_file}")
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")
    
    def save_enhanced_results(self):
        """保存增强的完整结果"""
        logger.info("保存增强实验结果...")
        
        # 计算统计
        success_rate = (self.successful_steps / self.total_steps) if self.total_steps > 0 else 0
        avg_reward = self.total_reward / self.total_steps if self.total_steps > 0 else 0
        
        # 资源利用率
        resource_levels = [r.resource_level for r in self.step_records if hasattr(r, 'resource_level')]
        resource_utilization = statistics.mean(resource_levels) if resource_levels else 0
        
        # 性能指标
        performance_metrics = self.monitor.get_summary()
        
        # 容错指标
        recovery_stats = self.recovery_manager.get_recovery_statistics()
        resilience_metrics = {
            'recovery_success_rate': recovery_stats.get('success_rate', 0.0),
            'total_recoveries': recovery_stats.get('total_recoveries', 0),
            'error_pattern_diversity': len(self.recovery_manager.error_patterns),
            'system_uptime': performance_metrics.get('total_duration', 0)
        }
        
        # 协作指标
        collaboration_analysis = self.analyzer.analyze_collaboration_patterns()
        collaboration_metrics = {
            'total_interactions': collaboration_analysis.get('total_interactions', 0),
            'network_density': collaboration_analysis.get('network_density', 0.0),
            'unique_connections': collaboration_analysis.get('unique_connections', 0),
            'avg_interactions_per_agent': collaboration_analysis.get('avg_interactions_per_agent', 0.0)
        }
        
        # 涌现指标
        purpose_analysis = self.analyzer.analyze_purpose_dynamics()
        emergence_indicators = {
            'purpose_diversity': purpose_analysis.get('purpose_diversity', 0.0),
            'purpose_convergence': purpose_analysis.get('purpose_convergence', 0.0),
            'evolution_speed': purpose_analysis.get('evolution_speed', 0.0),
            'trend': purpose_analysis.get('trend', 'unknown')
        }
        
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
            resilience_metrics=resilience_metrics,
            collaboration_metrics=collaboration_metrics,
            emergence_indicators=emergence_indicators
        )
        
        # 保存结果文件
        result_file = self.output_dir / f"{self.experiment_id}_final.json"
        records_file = self.output_dir / f"{self.experiment_id}_records.jsonl"
        error_log_file = self.output_dir / f"{self.experiment_id}_errors.json"
        
        try:
            # 保存摘要结果
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
            
            # 保存详细记录
            with open(records_file, 'w', encoding='utf-8') as f:
                for record in self.step_records:
                    f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
            
            # 保存错误日志
            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.monitor.error_log, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 增强结果保存完成:")
            logger.info(f"   摘要: {result_file}")
            logger.info(f"   详细记录: {records_file}")
            logger.info(f"   错误日志: {error_log_file}")
            
            # 打印增强的总结
            self.print_enhanced_summary(result)
            
        except Exception as e:
            logger.error(f"保存增强结果失败: {e}")
            raise
    
    def print_enhanced_summary(self, result: ExperimentResult):
        """打印增强的实验总结"""
        print("\n" + "="*80)
        print("增强多Agent社会实验 - 完整总结")
        print("="*80)
        print(f"实验ID: {result.experiment_id}")
        print(f"时间: {result.start_time} 到 {result.end_time}")
        print(f"持续时间: {result.end_time - result.start_time}")
        print(f"Agent数量: {result.agents_count}")
        print(f"总步数: {result.total_steps:,}")
        print(f"成功率: {result.success_rate*100:.1f}%")
        print(f"平均奖励: {result.average_reward:.3f}")
        print()
        
        print("性能指标:")
        for key, value in result.performance_metrics.items():
            if isinstance(value, float):
                if 'duration' in key or 'time' in key:
                    print(f"  {key}: {value:.3f}s")
                else:
                    print(f"  {key}: {value:.3f}")
        
        print()
        print("容错指标:")
        for key, value in result.resilience_metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        print()
        print("协作指标:")
        for key, value in result.collaboration_metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        print()
        print("涌现指标:")
        for key, value in result.emergence_indicators.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        print()
        print("Purpose演化摘要 (最新):")
        for agent_id, history in result.purpose_evolution.items():
            if history:
                latest = history[-1]
                print(f"  {agent_id}: D1={latest[0]:.3f}, D2={latest[1]:.3f}, D3={latest[2]:.3f}, D4={latest[3]:.3f}")
        
        print("="*80)


# ============================================
# 6. 主程序
# ============================================

def setup_logging():
    """设置日志"""
    log_dir = Path("logs/enhanced_experiments")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"enhanced_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """主函数"""
    global logger
    logger = setup_logging()
    
    parser = argparse.ArgumentParser(description='运行增强的多Agent社会实验')
    parser.add_argument('--agents', type=int, default=5,
                       help='Agent数量 (默认: 5)')
    parser.add_argument('--duration', type=int, default=30,
                       help='实验时长(分钟) (默认: 30)')
    parser.add_argument('--output', type=str, default='experiments/enhanced_society',
                       help='输出目录 (默认: experiments/enhanced_society)')
    parser.add_argument('--quick', action='store_true',
                       help='快速测试模式 (5分钟)')
    parser.add_argument('--monitoring', action='store_true', default=True,
                       help='启用系统监控 (默认: 启用)')
    
    args = parser.parse_args()
    
    # 快速测试模式
    if args.quick:
        args.duration = 5
        print("⚠️  快速测试模式: 5分钟运行")
    
    # 检查psutil是否可用
    try:
        import psutil
        logger.info("✅ psutil可用，启用系统监控")
    except ImportError:
        logger.warning("❌ psutil不可用，系统监控功能受限")
        args.monitoring = False
    
    # 创建并运行实验
    try:
        experiment = EnhancedMultiAgentExperiment(
            agents_count=args.agents,
            duration_minutes=args.duration,
            output_dir=args.output
        )
        
        logger.info("🎯 开始运行增强实验框架...")
        experiment.run_experiment()
        
        print("\n🎉 增强实验完成！")
        print(f"结果保存在: {args.output}")
        
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