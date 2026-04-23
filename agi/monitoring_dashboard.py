#!/usr/bin/env python3
"""
监控仪表盘 - Week 3

企业级监控仪表盘
实时可视化Agent状态
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import time
import json
from datetime import datetime
from pathlib import Path


@dataclass
class Metric:
    """监控指标"""
    timestamp: float
    agent_id: str
    metric_type: str
    value: float
    labels: Dict


class MonitoringDashboard:
    """
    监控仪表盘
    
    核心功能:
    1. 实时指标收集
    2. 告警规则管理
    3. 数据可视化
    4. 历史数据查询
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.metrics_buffer: List[Metric] = []
        self.alert_rules: List[Dict] = []
        self.alert_history: List[Dict] = []
        self.max_buffer_size = self.config.get('max_buffer_size', 10000)
        self.data_dir = Path(self.config.get('data_dir', '/tmp/mves_dashboard'))
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化告警规则
        self._init_default_alerts()
    
    def _init_default_alerts(self):
        """初始化默认告警规则"""
        self.alert_rules = [
            {
                'name': 'high_cpu_usage',
                'condition': lambda m: m.metric_type == 'cpu' and m.value > 80,
                'severity': 'warning',
                'message': 'CPU usage is above 80%',
            },
            {
                'name': 'low_memory',
                'condition': lambda m: m.metric_type == 'memory' and m.value < 20,
                'severity': 'critical',
                'message': 'Memory is below 20%',
            },
            {
                'name': 'agent_down',
                'condition': lambda m: m.metric_type == 'agent_status' and m.value == 0,
                'severity': 'critical',
                'message': 'Agent is not responding',
            },
            {
                'name': 'task_failure_rate',
                'condition': lambda m: m.metric_type == 'task_failure_rate' and m.value > 0.3,
                'severity': 'warning',
                'message': 'Task failure rate is above 30%',
            },
        ]
    
    def collect_metric(self, agent_id: str, metric_type: str, value: float, labels: Dict = None):
        """收集指标"""
        metric = Metric(
            timestamp=time.time(),
            agent_id=agent_id,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
        )
        
        self.metrics_buffer.append(metric)
        
        # 限制缓冲区大小
        if len(self.metrics_buffer) > self.max_buffer_size:
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer_size:]
        
        # 检查告警
        self._check_alerts(metric)
    
    def _check_alerts(self, metric: Metric):
        """检查告警"""
        for rule in self.alert_rules:
            try:
                if rule['condition'](metric):
                    alert = {
                        'timestamp': time.time(),
                        'rule_name': rule['name'],
                        'severity': rule['severity'],
                        'message': rule['message'],
                        'metric': asdict(metric),
                    }
                    self.alert_history.append(alert)
                    self._on_alert(alert)
            except Exception:
                pass
    
    def _on_alert(self, alert: Dict):
        """告警触发回调"""
        print(f"  🚨 ALERT [{alert['severity'].upper()}]: {alert['message']}")
    
    def get_metrics(self, agent_id: str = None, metric_type: str = None, 
                  start_time: float = None, end_time: float = None) -> List[Metric]:
        """查询指标"""
        result = self.metrics_buffer
        
        if agent_id:
            result = [m for m in result if m.agent_id == agent_id]
        
        if metric_type:
            result = [m for m in result if m.metric_type == metric_type]
        
        if start_time:
            result = [m for m in result if m.timestamp >= start_time]
        
        if end_time:
            result = [m for m in result if m.timestamp <= end_time]
        
        return result
    
    def get_latest_metrics(self, agent_id: str = None) -> Dict[str, Metric]:
        """获取最新指标"""
        latest = {}
        
        for metric in self.metrics_buffer:
            if agent_id and metric.agent_id != agent_id:
                continue
            
            key = f"{metric.agent_id}:{metric.metric_type}"
            if key not in latest or metric.timestamp > latest[key].timestamp:
                latest[key] = metric
        
        return latest
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """获取Agent状态"""
        metrics = self.get_latest_metrics(agent_id)
        
        status = {
            'agent_id': agent_id,
            'timestamp': time.time(),
            'metrics': {m.metric_type: m.value for m in metrics.values()},
            'is_healthy': True,
        }
        
        # 健康检查
        if 'agent_status' in status['metrics']:
            status['is_healthy'] = status['metrics']['agent_status'] == 1
        
        return status
    
    def get_dashboard_data(self) -> Dict:
        """获取仪表盘数据"""
        # 获取所有Agent的最新指标
        all_metrics = self.get_latest_metrics()
        
        # 按Agent分组
        agent_data = {}
        for key, metric in all_metrics.items():
            agent_id = metric.agent_id
            if agent_id not in agent_data:
                agent_data[agent_id] = {}
            agent_data[agent_id][metric.metric_type] = metric.value
        
        # 获取最近告警
        recent_alerts = self.alert_history[-10:] if self.alert_history else []
        
        return {
            'timestamp': time.time(),
            'agents': agent_data,
            'total_agents': len(agent_data),
            'recent_alerts': recent_alerts,
            'metrics_count': len(self.metrics_buffer),
        }
    
    def save_metrics(self, filename: str = None):
        """保存指标到文件"""
        if filename is None:
            filename = f"metrics_{int(time.time())}.json"
        
        filepath = self.data_dir / filename
        
        data = [asdict(m) for m in self.metrics_buffer]
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        return str(filepath)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.metrics_buffer:
            return {}
        
        # 按类型统计
        type_stats = {}
        for metric in self.metrics_buffer:
            if metric.metric_type not in type_stats:
                type_stats[metric.metric_type] = {
                    'count': 0,
                    'sum': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                }
            
            stats = type_stats[metric.metric_type]
            stats['count'] += 1
            stats['sum'] += metric.value
            stats['min'] = min(stats['min'], metric.value)
            stats['max'] = max(stats['max'], metric.value)
        
        # 计算平均值
        for stats in type_stats.values():
            stats['avg'] = stats['sum'] / stats['count'] if stats['count'] > 0 else 0
        
        return {
            'total_metrics': len(self.metrics_buffer),
            'metric_types': len(type_stats),
            'type_statistics': type_stats,
            'total_alerts': len(self.alert_history),
        }
    
    def get_status(self) -> Dict:
        """获取仪表盘状态"""
        return {
            'metrics_buffer_size': len(self.metrics_buffer),
            'alert_rules_count': len(self.alert_rules),
            'alert_history_size': len(self.alert_history),
            'data_dir': str(self.data_dir),
        }