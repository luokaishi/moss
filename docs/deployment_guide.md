# MOSS v6.2 部署指南

本文档介绍如何将 MOSS v6.2 部署到生产环境。

## 目录

- [系统要求](#系统要求)
- [Docker 部署](#docker-部署)
- [API 使用](#api-使用)
- [监控配置](#监控配置)
- [故障排除](#故障排除)

## 系统要求

### 最低配置

- CPU: 2 核心
- 内存: 4 GB RAM
- 存储: 10 GB 可用空间
- 网络: 可访问互联网（用于下载依赖）

### 推荐配置

- CPU: 4 核心及以上
- 内存: 8 GB RAM 及以上
- 存储: 50 GB SSD
- GPU: NVIDIA GPU（可选，用于加速训练）

### 软件依赖

- Docker 20.10+
- Docker Compose 2.0+（可选）
- Python 3.8+（非 Docker 部署）

## Docker 部署

### 1. 构建镜像

```bash
# 克隆代码仓库
git clone <repository-url>
cd moss

# 构建 Docker 镜像
docker build -t moss:v6.2 .
```

### 2. 运行容器

```bash
# 基本运行
docker run -d \
  --name moss-api \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  moss:v6.2

# 带环境变量的运行
docker run -d \
  --name moss-api \
  -p 8000:8000 \
  -e MOSS_ENV=production \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  moss:v6.2
```

### 3. 使用 Docker Compose（推荐）

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  moss-api:
    build: .
    container_name: moss-api
    ports:
      - "8000:8000"
    environment:
      - MOSS_ENV=production
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  moss-dashboard:
    build: .
    container_name: moss-dashboard
    command: python monitoring/dashboard.py
    ports:
      - "8080:8080"
    environment:
      - MOSS_ENV=production
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

启动服务:

```bash
docker-compose up -d
```

### 4. 验证部署

```bash
# 检查容器状态
docker ps

# 查看日志
docker logs moss-api

# 健康检查
curl http://localhost:8000/health
```

## API 使用

### 基础信息

- 基础 URL: `http://localhost:8000`
- 内容类型: `application/json`

### 端点列表

#### 1. 健康检查

```bash
GET /health
```

**响应:**
```json
{
  "status": "ok"
}
```

#### 2. 初始化 Agent

```bash
POST /initialize
Content-Type: application/json

{
  "exploration_rate": 0.3,
  "task_focus": 0.7,
  "learning_rate": 0.01,
  "drive_weights": {
    "curiosity": 0.6,
    "efficiency": 0.5
  }
}
```

**响应:**
```json
{
  "status": "initialized"
}
```

#### 3. 执行步骤

```bash
POST /step
Content-Type: application/json

{
  "observation": {
    "state": [1.0, 0.5, 0.2],
    "reward": 1.0,
    "done": false
  }
}
```

**响应:**
```json
{
  "action": 2,
  "drive_states": {
    "exploration": 0.3,
    "task_focus": 0.7,
    "survival": 0.5
  }
}
```

#### 4. 获取驱动状态

```bash
GET /drives
```

**响应:**
```json
{
  "exploration": 0.3,
  "task_focus": 0.7,
  "survival": 0.5,
  "curiosity": 0.6,
  "efficiency": 0.45
}
```

### Python 客户端示例

```python
import requests

class MOSSClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
    
    def health_check(self):
        """健康检查"""
        response = requests.get(f'{self.base_url}/health')
        return response.json()
    
    def initialize(self, config):
        """初始化 Agent"""
        response = requests.post(
            f'{self.base_url}/initialize',
            json=config
        )
        return response.json()
    
    def step(self, observation):
        """执行一步"""
        response = requests.post(
            f'{self.base_url}/step',
            json={'observation': observation}
        )
        return response.json()
    
    def get_drives(self):
        """获取驱动状态"""
        response = requests.get(f'{self.base_url}/drives')
        return response.json()

# 使用示例
client = MOSSClient()

# 初始化
client.initialize({
    'exploration_rate': 0.3,
    'task_focus': 0.7
})

# 运行步骤
result = client.step({
    'state': [1.0, 0.5, 0.2],
    'reward': 1.0
})
print(f"Action: {result['action']}")
```

## 监控配置

### 1. 启动监控仪表板

```bash
# 独立启动
python monitoring/dashboard.py

# 或使用 Docker
docker run -d \
  --name moss-dashboard \
  -p 8080:8080 \
  moss:v6.2 \
  python monitoring/dashboard.py
```

访问 `http://localhost:8080` 查看仪表板。

### 2. 仪表板功能

- **Performance Metrics**: 显示总步数、平均奖励、成功率
- **Drive Weights**: 实时显示各驱动权重
- **Emergence Events**: 显示涌现事件和自适应调整

### 3. 程序化更新监控数据

```python
from monitoring.dashboard import DashboardServer

# 创建仪表板服务器
dashboard = DashboardServer(host='0.0.0.0', port=8080)
dashboard.start()

# 更新指标
dashboard.update_metrics({
    'total_steps': 10000,
    'avg_reward': 0.75,
    'success_rate': 0.82
})

# 更新驱动权重
dashboard.update_drive_weights({
    'exploration': 0.3,
    'task_focus': 0.7,
    'survival': 0.5
})

# 添加涌现事件
dashboard.add_emergence_event(
    name='Pattern Recognition',
    event_type='emergence',
    description='New behavioral pattern detected'
)
```

### 4. 集成 Prometheus（可选）

如需更强大的监控，可添加 Prometheus 导出器:

```python
from prometheus_client import Counter, Histogram, start_http_server

# 定义指标
steps_total = Counter('moss_steps_total', 'Total steps executed')
reward_histogram = Histogram('moss_reward', 'Reward distribution')

# 启动 Prometheus 服务器
start_http_server(9090)
```

## 故障排除

### 常见问题

#### 1. 容器无法启动

**症状:** `docker run` 后立即退出

**排查:**
```bash
# 查看日志
docker logs moss-api

# 检查端口占用
lsof -i :8000
```

**解决:**
- 检查 `requirements.txt` 是否完整
- 确认端口未被占用
- 检查环境变量配置

#### 2. API 无响应

**症状:** 请求超时或返回 500

**排查:**
```bash
# 检查容器状态
docker ps

# 测试健康检查端点
curl -v http://localhost:8000/health
```

**解决:**
- 确认 Agent 已初始化 (`POST /initialize`)
- 检查日志中的错误信息
- 重启容器: `docker restart moss-api`

#### 3. 内存不足

**症状:** 容器 OOM Killed

**排查:**
```bash
docker stats moss-api
```

**解决:**
- 增加容器内存限制: `--memory=4g`
- 优化批处理大小
- 启用梯度检查点

#### 4. 性能问题

**症状:** API 响应慢

**排查:**
```bash
# 检查 CPU 使用
top

# 检查磁盘 I/O
iostat -x 1
```

**解决:**
- 启用 GPU 加速
- 使用 Redis 缓存
- 水平扩展多个实例

### 日志查看

```bash
# 实时日志
docker logs -f moss-api

# 最近 100 行
docker logs --tail 100 moss-api

# 带时间戳
docker logs -t moss-api
```

### 调试模式

```bash
# 启用调试日志
docker run -e LOG_LEVEL=DEBUG -e FLASK_DEBUG=1 moss:v6.2
```

## 生产环境建议

### 1. 安全性

- 使用 HTTPS（配合 Nginx 或 Traefik）
- 启用 API 认证（JWT 或 API Key）
- 限制容器资源使用
- 定期更新基础镜像

### 2. 高可用

- 使用负载均衡器
- 部署多个实例
- 配置健康检查和自动重启
- 设置监控告警

### 3. 备份

- 定期备份数据卷
- 保存模型检查点
- 记录配置变更

---

**版本:** MOSS v6.2  
**最后更新:** 2026-04-18
