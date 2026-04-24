# MOSS 集成指南

**版本**: v8.6.0  
**日期**: 2026-04-24

---

## 📚 目录

1. [快速集成](#快速集成)
2. [Docker部署](#docker部署)
3. [系统集成](#系统集成)
4. [监控集成](#监控集成)
5. [扩展开发](#扩展开发)

---

## 快速集成

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/luokaishi/moss.git
cd moss

# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量
export MOSS_WORKSPACE=/path/to/workspace
export MOSS_CONFIG=config/agent_config.yaml
```

### 2. 基础配置

```yaml
# config/agent_config.yaml
environment:
  type: realworld
  workspace: /tmp/moss_workspace

agent:
  population_size: 50
  generations: 100

llm:
  model: kimi-k2.5
  temperature: 0.7
  max_tokens: 2000
```

### 3. 启动Agent

```python
from agi.task_aware_agent import TaskAwareAgent

# 创建Agent
agent = TaskAwareAgent('config/agent_config.yaml')

# 设置任务
agent.set_task({
    'type': 'file_organization',
    'description': '整理下载文件夹'
})

# 运行
agent._one_cycle()
```

---

## Docker部署

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV MOSS_WORKSPACE=/data

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python3", "-m", "agi.server"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  moss-agent:
    build: .
    container_name: moss-agent
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - MOSS_CONFIG=/config/agent_config.yaml
      - MOSS_WORKSPACE=/data
    restart: unless-stopped
    
  moss-monitor:
    build: .
    container_name: moss-monitor
    command: python3 agi/monitoring_dashboard.py
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
    restart: unless-stopped
```

### 启动服务

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 系统集成

### 与现有系统集成

#### 1. 文件系统监控

```python
from agi.mves_realworld_bridge import create_bridge
import watchdog

class FileSystemIntegration:
    def __init__(self):
        self.bridge = create_bridge({
            'workspace': '/data'
        })
        
    def on_file_change(self, event):
        """文件变化回调"""
        # 触发MOSS事件
        self.bridge.handle_event({
            'type': 'file_change',
            'data': {
                'path': event.src_path,
                'type': event.event_type
            }
        })
```

#### 2. 日志系统集成

```python
import logging
from agi.task_aware_agent import TaskAwareAgent

class LogIntegration:
    def __init__(self):
        self.agent = TaskAwareAgent('config.yaml')
        
    def process_log(self, log_entry):
        """处理日志条目"""
        self.agent.set_task({
            'type': 'log_analysis',
            'description': f'分析日志: {log_entry}'
        })
```

#### 3. CI/CD集成

```yaml
# .github/workflows/moss.yml
name: MOSS Integration

on:
  push:
    branches: [main]

jobs:
  moss-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup MOSS
        run: |
          pip install -r requirements.txt
          
      - name: Run Code Review
        run: |
          python3 -c "
          from agi.task_aware_agent import TaskAwareAgent
          agent = TaskAwareAgent('config/ci_config.yaml')
          agent.set_task({
            'type': 'code_review',
            'description': 'Review PR code'
          })
          agent._one_cycle()
          "
```

---

## 监控集成

### Prometheus集成

```python
from prometheus_client import Counter, Histogram, start_http_server
from agi.monitoring_dashboard import MonitoringDashboard

class PrometheusIntegration:
    def __init__(self):
        self.dashboard = MonitoringDashboard()
        
        # 定义指标
        self.task_counter = Counter('moss_tasks_total', 'Total tasks')
        self.cycle_duration = Histogram('moss_cycle_duration_seconds', 'Cycle duration')
        
    def start(self, port=8000):
        """启动监控服务"""
        start_http_server(port)
        
    def record_task(self, task_type):
        """记录任务"""
        self.task_counter.inc()
        self.dashboard.collect_metric('agent_1', 'task', 1, {'type': task_type})
```

### Grafana仪表盘

```json
{
  "dashboard": {
    "title": "MOSS Monitoring",
    "panels": [
      {
        "title": "Task Rate",
        "targets": [
          {
            "expr": "rate(moss_tasks_total[5m])"
          }
        ]
      },
      {
        "title": "Cycle Duration",
        "targets": [
          {
            "expr": "moss_cycle_duration_seconds"
          }
        ]
      }
    ]
  }
}
```

### 告警配置

```yaml
# alertmanager.yml
groups:
  - name: moss
    rules:
      - alert: MossAgentDown
        expr: up{job="moss-agent"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "MOSS Agent is down"
          
      - alert: MossHighErrorRate
        expr: rate(moss_errors_total[5m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
```

---

## 扩展开发

### 创建自定义任务

```python
from agi.task_aware_agent import TaskAwareAgent

class CustomTaskAgent(TaskAwareAgent):
    def __init__(self, config_path):
        super().__init__(config_path)
        self.register_task_handler('custom_task', self.handle_custom)
        
    def handle_custom(self, task):
        """处理自定义任务"""
        # 实现自定义逻辑
        result = self.execute_custom_logic(task)
        return result
        
    def execute_custom_logic(self, task):
        """执行自定义逻辑"""
        # 自定义实现
        pass
```

### 创建自定义驱动

```python
from agi.drive import Drive

class CustomDrive(Drive):
    def __init__(self, name, config):
        super().__init__(name, config)
        self.custom_param = config.get('custom_param')
        
    def calculate_activation(self, state):
        """计算激活度"""
        # 自定义激活逻辑
        return self.custom_formula(state)
        
    def custom_formula(self, state):
        """自定义公式"""
        return state.get('custom_metric', 0) * self.custom_param
```

### 创建自定义监控指标

```python
from agi.monitoring_dashboard import MonitoringDashboard

class CustomMetricsDashboard(MonitoringDashboard):
    def __init__(self, config):
        super().__init__(config)
        self.custom_metrics = {}
        
    def collect_custom_metric(self, name, value, labels=None):
        """收集自定义指标"""
        self.custom_metrics[name] = {
            'value': value,
            'timestamp': time.time(),
            'labels': labels or {}
        }
        self.collect_metric('custom', name, value, labels)
```

---

## 最佳实践

### 1. 配置管理

```python
# 使用环境变量
import os

config = {
    'llm': {
        'api_key': os.getenv('LLM_API_KEY'),
        'model': os.getenv('LLM_MODEL', 'kimi-k2.5')
    },
    'workspace': os.getenv('MOSS_WORKSPACE', '/tmp/moss')
}
```

### 2. 错误处理

```python
from agi.auto_recovery import create_auto_recovery

class RobustAgent:
    def __init__(self):
        self.agent = TaskAwareAgent('config.yaml')
        self.recovery = create_auto_recovery()
        
    def run_with_recovery(self):
        """带恢复机制的运行"""
        try:
            self.agent._one_cycle()
        except Exception as e:
            failure = self.recovery.detect_failure({
                'agent_id': 'agent_1',
                'error': str(e)
            })
            if failure:
                self.recovery.recover(failure)
```

### 3. 性能优化

```python
# 使用连接池
from concurrent.futures import ThreadPoolExecutor

class OptimizedAgent:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def parallel_tasks(self, tasks):
        """并行执行任务"""
        futures = [self.executor.submit(self.process_task, t) for t in tasks]
        return [f.result() for f in futures]
```

### 4. 安全实践

```python
# 输入验证
def validate_task(task):
    """验证任务"""
    allowed_types = ['file_organization', 'log_analysis', 'code_review']
    if task['type'] not in allowed_types:
        raise ValueError(f"Invalid task type: {task['type']}")
    return task

# 沙箱执行
import subprocess

def sandbox_execute(command):
    """沙箱执行命令"""
    return subprocess.run(
        command,
        shell=False,
        timeout=30,
        capture_output=True
    )
```

---

## 故障排除

### 常见问题

#### 1. Agent启动失败

```bash
# 检查配置
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 检查依赖
pip list | grep -E "numpy|pandas|requests"

# 检查权限
ls -la $MOSS_WORKSPACE
```

#### 2. LLM调用失败

```python
# 测试LLM连接
from agi.llm import LLMClient

client = LLMClient()
response = client.generate("test")
print(response)
```

#### 3. 内存泄漏

```python
# 监控内存使用
import psutil
import tracemalloc

tracemalloc.start()
# ... 运行代码 ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
print(top_stats[:10])
```

---

## 示例项目

### 示例1: 自动化文件整理

```python
#!/usr/bin/env python3
"""自动化文件整理服务"""

from agi.task_aware_agent import TaskAwareAgent
from agi.mves_realworld_bridge import create_bridge
import time

class FileOrganizationService:
    def __init__(self):
        self.agent = TaskAwareAgent('config/file_org.yaml')
        self.bridge = create_bridge({'workspace': '/data/downloads'})
        
    def run(self):
        """运行服务"""
        while True:
            # 检查文件变化
            changes = self.bridge.get_recent_changes(60)
            
            if changes:
                # 触发文件整理任务
                self.agent.set_task({
                    'type': 'file_organization',
                    'description': f'整理 {len(changes)} 个新文件'
                })
                self.agent._one_cycle()
                
            time.sleep(60)

if __name__ == '__main__':
    service = FileOrganizationService()
    service.run()
```

### 示例2: 系统监控Agent

```python
#!/usr/bin/env python3
"""系统监控Agent"""

from agi.task_aware_agent import TaskAwareAgent
from agi.monitoring_dashboard import MonitoringDashboard
import psutil
import time

class SystemMonitorAgent:
    def __init__(self):
        self.agent = TaskAwareAgent('config/monitor.yaml')
        self.dashboard = MonitoringDashboard()
        
    def monitor(self):
        """监控系统"""
        while True:
            # 收集系统指标
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            # 记录指标
            self.dashboard.collect_metric('system', 'cpu', cpu)
            self.dashboard.collect_metric('system', 'memory', memory)
            self.dashboard.collect_metric('system', 'disk', disk)
            
            # 检查告警
            if cpu > 80 or memory > 80:
                self.agent.set_task({
                    'type': 'system_monitor',
                    'description': f'高资源使用: CPU={cpu}%, MEM={memory}%'
                })
                self.agent._one_cycle()
                
            time.sleep(60)

if __name__ == '__main__':
    agent = SystemMonitorAgent()
    agent.monitor()
```

### 示例3: 多Agent协作系统

```python
#!/usr/bin/env python3
"""多Agent协作系统"""

from agi.multi_agent_coordinator import MultiAgentCoordinator
from agi.task_aware_agent import TaskAwareAgent

class CollaborativeSystem:
    def __init__(self):
        self.coordinator = MultiAgentCoordinator()
        self.setup_agents()
        
    def setup_agents(self):
        """设置Agents"""
        # 文件整理Agent
        file_agent = TaskAwareAgent('config/file.yaml')
        self.coordinator.register_agent('file_agent', 
                                       ['file_organization', 'backup_cleanup'])
        
        # 监控Agent
        monitor_agent = TaskAwareAgent('config/monitor.yaml')
        self.coordinator.register_agent('monitor_agent',
                                       ['system_monitor', 'log_analysis'])
        
        # 安全Agent
        security_agent = TaskAwareAgent('config/security.yaml')
        self.coordinator.register_agent('security_agent',
                                       ['security_scan', 'code_review'])
        
    def submit_workflow(self, workflow):
        """提交工作流"""
        for task in workflow:
            self.coordinator.submit_task(task['type'], 
                                        priority=task.get('priority', 'medium'))
            
if __name__ == '__main__':
    system = CollaborativeSystem()
    
    # 定义工作流
    workflow = [
        {'type': 'security_scan', 'priority': 'high'},
        {'type': 'code_review', 'priority': 'medium'},
        {'type': 'file_organization', 'priority': 'low'}
    ]
    
    system.submit_workflow(workflow)
```

---

## 资源

- **文档索引**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- **API参考**: [API_REFERENCE.md](API_REFERENCE.md)
- **GitHub**: https://github.com/luokaishi/moss
- **Issues**: https://github.com/luokaishi/moss/issues

---

*最后更新: 2026-04-24*
