# MonitoringDashboard 设计文档

**版本**: v8.6.0  
**日期**: 2026-04-25  
**作者**: MOSS Team

---

## 1. 概述

### 1.1 设计目标

MonitoringDashboard 模块提供企业级监控能力，实时收集、存储、展示Agent和系统指标，支持告警管理和可视化仪表盘。

### 1.2 核心特性

- **实时指标收集**: 支持多种指标类型的实时收集
- **告警规则管理**: 灵活的告警规则配置
- **数据可视化**: 支持图表展示和仪表盘
- **历史数据查询**: 支持时间范围查询和聚合
- **多Agent支持**: 支持多个Agent的集中监控

---

## 2. 架构设计

### 2.1 组件关系

```
┌─────────────────────────────────────────────────────────────┐
│                  MonitoringDashboard                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Metrics    │  │    Alert     │  │  Dashboard   │   │
│  │   Buffer     │  │    Rules     │  │     UI       │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                  │                  │            │
│         ↓                  ↓                  ↓            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Metric Store │  │ Alert Engine │  │  Web Server  │   │
│  │  (Memory/    │  │  (Evaluator/ │  │  (REST API)  │   │
│  │   File/DB)   │  │   Notifier)  │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
Agent → collect_metric() → Metrics Buffer → Metric Store
                                    ↓
                              Alert Engine → Notifications
                                    ↓
                              Dashboard UI
```

---

## 3. 核心类设计

### 3.1 Metric 数据模型

```python
@dataclass
class Metric:
    """监控指标数据模型"""
    timestamp: float      # Unix时间戳
    agent_id: str        # Agent标识
    metric_type: str     # 指标类型
    value: float         # 指标值
    labels: Dict         # 标签（维度信息）

# 示例
Metric(
    timestamp=1776916458.354,
    agent_id='agent_1',
    metric_type='cpu',
    value=75.5,
    labels={'host': 'server1', 'unit': 'percent'}
)
```

### 3.2 AlertRule 数据模型

```python
@dataclass
class AlertRule:
    """告警规则"""
    name: str                    # 规则名称
    condition: Callable        # 触发条件函数
    severity: str              # 严重程度
    message: str               # 告警消息模板
    cooldown: int              # 冷却时间(秒)
    last_triggered: float       # 上次触发时间
```

### 3.3 MonitoringDashboard 类

```python
class MonitoringDashboard:
    """监控仪表盘"""
    
    def __init__(self, config: Dict = None):
        self.metrics_buffer: List[Metric] = []
        self.alert_rules: List[AlertRule] = []
        self.alert_history: List[Dict] = []
        self.max_buffer_size = config.get('max_buffer_size', 10000)
        self.data_dir = Path(config.get('data_dir', '/tmp/moss_dashboard'))
        
        # 初始化默认告警规则
        self._init_default_alerts()
    
    def collect_metric(self, agent_id: str, metric_type: str, 
                      value: float, labels: Dict = None):
        """收集指标"""
        pass
    
    def get_metrics(self, **filters) -> List[Metric]:
        """查询指标"""
        pass
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """获取Agent状态"""
        pass
```

---

## 4. 指标类型定义

### 4.1 标准指标

| 指标类型 | 说明 | 单位 | 示例值 |
|----------|------|------|--------|
| `cpu` | CPU使用率 | percent | 75.5 |
| `memory` | 内存使用率 | percent | 82.0 |
| `disk` | 磁盘使用率 | percent | 60.0 |
| `network_in` | 网络流入 | bytes/s | 1024000 |
| `network_out` | 网络流出 | bytes/s | 512000 |
| `task_count` | 任务数 | count | 150 |
| `task_success_rate` | 任务成功率 | percent | 98.5 |
| `agent_status` | Agent状态 | binary | 1 (online) |
| `generation` | 当前代数 | count | 100 |
| `emerged_drives` | 涌现驱动数 | count | 5 |

### 4.2 自定义指标

```python
# 业务指标
dashboard.collect_metric(
    agent_id='agent_1',
    metric_type='custom_business_metric',
    value=123.45,
    labels={
        'category': 'user_engagement',
        'feature': 'new_dashboard'
    }
)
```

---

## 5. 告警规则设计

### 5.1 默认告警规则

```python
DEFAULT_ALERT_RULES = [
    {
        'name': 'high_cpu_usage',
        'condition': lambda m: m.metric_type == 'cpu' and m.value > 80,
        'severity': 'warning',
        'message': 'CPU usage is above 80%: {value}%',
        'cooldown': 300  # 5分钟
    },
    {
        'name': 'low_memory',
        'condition': lambda m: m.metric_type == 'memory' and m.value < 20,
        'severity': 'critical',
        'message': 'Memory is below 20%: {value}%',
        'cooldown': 60
    },
    {
        'name': 'agent_down',
        'condition': lambda m: m.metric_type == 'agent_status' and m.value == 0,
        'severity': 'critical',
        'message': 'Agent {agent_id} is not responding',
        'cooldown': 60
    },
    {
        'name': 'task_failure_rate',
        'condition': lambda m: m.metric_type == 'task_success_rate' and m.value < 70,
        'severity': 'warning',
        'message': 'Task success rate is below 70%: {value}%',
        'cooldown': 600
    }
]
```

### 5.2 自定义告警规则

```python
# 添加自定义告警规则
dashboard.add_alert_rule(
    name='custom_alert',
    condition=lambda m: m.metric_type == 'custom_metric' and m.value > 100,
    severity='warning',
    message='Custom metric exceeded threshold: {value}',
    cooldown=300
)
```

---

## 6. 数据存储策略

### 6.1 内存存储

```python
class InMemoryStore:
    """内存存储"""
    
    def __init__(self, max_size: int = 10000):
        self.metrics = []
        self.max_size = max_size
        
    def append(self, metric: Metric):
        self.metrics.append(metric)
        if len(self.metrics) > self.max_size:
            self.metrics = self.metrics[-self.max_size:]
            
    def query(self, **filters) -> List[Metric]:
        result = self.metrics
        
        if 'agent_id' in filters:
            result = [m for m in result if m.agent_id == filters['agent_id']]
        
        if 'metric_type' in filters:
            result = [m for m in result if m.metric_type == filters['metric_type']]
        
        if 'start_time' in filters:
            result = [m for m in result if m.timestamp >= filters['start_time']]
        
        if 'end_time' in filters:
            result = [m for m in result if m.timestamp <= filters['end_time']]
        
        return result
```

### 6.2 文件存储

```python
class FileStore:
    """文件存储"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def save_metrics(self, metrics: List[Metric], filename: str = None):
        if filename is None:
            filename = f"metrics_{int(time.time())}.json"
        
        filepath = self.data_dir / filename
        
        data = [asdict(m) for m in metrics]
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        return str(filepath)
    
    def load_metrics(self, filename: str) -> List[Metric]:
        filepath = self.data_dir / filename
        
        with open(filepath) as f:
            data = json.load(f)
        
        return [Metric(**d) for d in data]
```

---

## 7. API接口定义

### 7.1 核心API

```python
class MonitoringDashboard:
    def __init__(self, config: Dict = None):
        """
        初始化监控仪表盘
        
        Args:
            config: 配置字典
                - max_buffer_size: 最大缓冲区大小 (默认10000)
                - data_dir: 数据目录 (默认/tmp/moss_dashboard)
        """
        pass
    
    def collect_metric(self, agent_id: str, metric_type: str,
                      value: float, labels: Dict = None):
        """
        收集指标
        
        Args:
            agent_id: Agent标识
            metric_type: 指标类型
            value: 指标值
            labels: 标签字典
        """
        pass
    
    def get_metrics(self, agent_id: str = None,
                   metric_type: str = None,
                   start_time: float = None,
                   end_time: float = None) -> List[Metric]:
        """
        查询指标
        
        Args:
            agent_id: Agent标识过滤
            metric_type: 指标类型过滤
            start_time: 开始时间戳
            end_time: 结束时间戳
            
        Returns:
            符合条件的指标列表
        """
        pass
    
    def get_latest_metrics(self, agent_id: str = None) -> Dict[str, Metric]:
        """
        获取最新指标
        
        Args:
            agent_id: Agent标识 (可选)
            
        Returns:
            最新指标字典 {key: Metric}
        """
        pass
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """
        获取Agent状态
        
        Args:
            agent_id: Agent标识
            
        Returns:
            Agent状态字典
                - agent_id: Agent标识
                - timestamp: 时间戳
                - metrics: 指标字典
                - is_healthy: 是否健康
        """
        pass
    
    def get_dashboard_data(self) -> Dict:
        """
        获取仪表盘数据
        
        Returns:
            仪表盘数据字典
                - timestamp: 时间戳
                - agents: Agent数据
                - total_agents: Agent数量
                - recent_alerts: 最近告警
                - metrics_count: 指标总数
        """
        pass
    
    def add_alert_rule(self, name: str, condition: Callable,
                      severity: str, message: str, cooldown: int = 300):
        """
        添加告警规则
        
        Args:
            name: 规则名称
            condition: 触发条件函数
            severity: 严重程度 (critical/warning/info)
            message: 告警消息模板
            cooldown: 冷却时间(秒)
        """
        pass
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计字典
                - total_metrics: 总指标数
                - metric_types: 指标类型数
                - type_statistics: 各类型统计
                - total_alerts: 总告警数
        """
        pass
```

### 7.2 使用示例

```python
from agi.monitoring_dashboard import MonitoringDashboard

# 创建仪表盘
dashboard = MonitoringDashboard({
    'max_buffer_size': 10000,
    'data_dir': '/tmp/dashboard'
})

# 收集指标
dashboard.collect_metric('agent_1', 'cpu', 75.5)
dashboard.collect_metric('agent_1', 'memory', 82.0, {'unit': 'percent'})

# 获取Agent状态
status = dashboard.get_agent_status('agent_1')
print(f"健康状态: {status['is_healthy']}")

# 查询指标
metrics = dashboard.get_metrics(
    agent_id='agent_1',
    metric_type='cpu',
    start_time=time.time() - 3600  # 最近1小时
)

# 获取仪表盘数据
data = dashboard.get_dashboard_data()
print(f"Agent数量: {data['total_agents']}")
print(f"最近告警: {len(data['recent_alerts'])}")

# 添加自定义告警规则
dashboard.add_alert_rule(
    name='high_disk_usage',
    condition=lambda m: m.metric_type == 'disk' and m.value > 90,
    severity='critical',
    message='Disk usage is above 90%: {value}%',
    cooldown=600
)
```

---

## 8. 可视化设计

### 8.1 REST API

```python
from flask import Flask, jsonify

app = Flask(__name__)
dashboard = MonitoringDashboard()

@app.route('/api/metrics', methods=['GET'])
def get_metrics_api():
    """获取指标API"""
    agent_id = request.args.get('agent_id')
    metric_type = request.args.get('metric_type')
    
    metrics = dashboard.get_metrics(
        agent_id=agent_id,
        metric_type=metric_type
    )
    
    return jsonify({
        'metrics': [asdict(m) for m in metrics]
    })

@app.route('/api/agents/<agent_id>/status', methods=['GET'])
def get_agent_status_api(agent_id):
    """获取Agent状态API"""
    status = dashboard.get_agent_status(agent_id)
    return jsonify(status)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_api():
    """获取仪表盘数据API"""
    data = dashboard.get_dashboard_data()
    return jsonify(data)

@app.route('/api/alerts', methods=['GET'])
def get_alerts_api():
    """获取告警API"""
    return jsonify({
        'alerts': dashboard.alert_history[-50:]  # 最近50条
    })
```

### 8.2 WebSocket实时推送

```python
from flask_socketio import SocketIO

socketio = SocketIO(app)

@socketio.on('subscribe')
def handle_subscribe(data):
    """处理订阅请求"""
    agent_id = data.get('agent_id')
    # 启动实时推送
    
def broadcast_metrics():
    """广播指标更新"""
    while True:
        data = dashboard.get_dashboard_data()
        socketio.emit('metrics_update', data)
        time.sleep(10)  # 每10秒推送一次
```

---

## 9. 性能优化

### 9.1 指标采样

```python
class SamplingDashboard(MonitoringDashboard):
    """采样监控仪表盘"""
    
    def __init__(self, config):
        super().__init__(config)
        self.sample_rate = config.get('sample_rate', 1.0)
        
    def collect_metric(self, agent_id, metric_type, value, labels=None):
        """采样收集指标"""
        if random.random() > self.sample_rate:
            return  # 跳过采样
        
        super().collect_metric(agent_id, metric_type, value, labels)
```

### 9.2 数据聚合

```python
class AggregatingDashboard(MonitoringDashboard):
    """聚合监控仪表盘"""
    
    def __init__(self, config):
        super().__init__(config)
        self.aggregation_window = config.get('aggregation_window', 60)
        self.aggregation_buffer = {}
        
    def collect_metric(self, agent_id, metric_type, value, labels=None):
        """聚合收集指标"""
        key = f"{agent_id}:{metric_type}"
        
        if key not in self.aggregation_buffer:
            self.aggregation_buffer[key] = []
        
        self.aggregation_buffer[key].append(value)
        
        # 达到窗口大小时聚合
        if len(self.aggregation_buffer[key]) >= self.aggregation_window:
            aggregated_value = sum(self.aggregation_buffer[key]) / len(self.aggregation_buffer[key])
            super().collect_metric(agent_id, metric_type, aggregated_value, labels)
            self.aggregation_buffer[key] = []
```

---

## 10. 测试策略

### 10.1 单元测试

```python
import unittest

class TestMonitoringDashboard(unittest.TestCase):
    def setUp(self):
        self.dashboard = MonitoringDashboard()
        
    def test_collect_metric(self):
        """测试指标收集"""
        self.dashboard.collect_metric('agent_1', 'cpu', 75.5)
        
        metrics = self.dashboard.get_metrics(agent_id='agent_1')
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].value, 75.5)
        
    def test_alert_trigger(self):
        """测试告警触发"""
        # 添加告警规则
        self.dashboard.add_alert_rule(
            name='test_alert',
            condition=lambda m: m.value > 80,
            severity='warning',
            message='Test alert',
            cooldown=0
        )
        
        # 触发告警
        self.dashboard.collect_metric('agent_1', 'cpu', 85.0)
        
        # 验证告警
        self.assertEqual(len(self.dashboard.alert_history), 1)
        self.assertEqual(self.dashboard.alert_history[0]['severity'], 'warning')
        
    def test_agent_status(self):
        """测试Agent状态"""
        self.dashboard.collect_metric('agent_1', 'cpu', 75.5)
        self.dashboard.collect_metric('agent_1', 'memory', 82.0)
        
        status = self.dashboard.get_agent_status('agent_1')
        
        self.assertEqual(status['agent_id'], 'agent_1')
        self.assertIn('cpu', status['metrics'])
        self.assertIn('memory', status['metrics'])
```

---

## 11. 参考

- [API_REFERENCE.md](API_REFERENCE.md) - API参考文档
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - 集成指南
- [agi/monitoring_dashboard.py](agi/monitoring_dashboard.py) - 源代码

---

*最后更新: 2026-04-25*
