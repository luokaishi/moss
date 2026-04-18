# MOSS v6.4 生产部署指南

**版本**: 6.4.0  
**日期**: 2026-04-18  
**状态**: ✅ 已完成

---

## 概述

本指南提供 MOSS v6.4 的生产环境部署说明，包括 Kubernetes 配置、Docker 部署和监控设置。

---

## 部署要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| API 服务 | 2 CPU, 4GB RAM | 4 CPU, 8GB RAM |
| 训练节点 | 8 CPU, 16GB RAM, 1 GPU | 16 CPU, 32GB RAM, 2 GPU |
| Worker 节点 | 4 CPU, 8GB RAM | 8 CPU, 16GB RAM |
| 存储 | 100GB SSD | 500GB SSD |

### 软件要求

- Kubernetes 1.24+
- Docker 20.10+
- Helm 3.0+
- NVIDIA GPU Operator (如需 GPU 支持)

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/moss-ai/moss.git
cd moss
git checkout v6.4.0
```

### 2. 构建镜像

```bash
# 构建生产镜像
docker build -t moss/moss:v6.4 -f Dockerfile .

# 推送镜像
docker push moss/moss:v6.4
```

### 3. 部署到 Kubernetes

```bash
# 创建命名空间
kubectl create namespace moss

# 应用配置
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 验证部署
kubectl get pods -n moss
```

---

## Kubernetes 配置详解

### ConfigMap (`k8s/configmap.yaml`)

ConfigMap 存储应用配置，包括：
- 环境变量
- 训练超参数
- 数据库连接信息
- 监控配置

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: moss-config
data:
  MOSS_ENV: "production"
  MOSS_LOG_LEVEL: "INFO"
  TRAINING_BATCH_SIZE: "32"
  # ...
```

### Deployment (`k8s/deployment.yaml`)

包含三个主要组件：

#### API 服务 (moss-api)
- **用途**: REST API 和 WebSocket 服务
- **副本数**: 3-10 (自动扩缩容)
- **资源**: 512Mi-2Gi 内存, 500m-2000m CPU
- **健康检查**: /health, /ready

#### 训练服务 (moss-training)
- **用途**: 模型训练主节点
- **副本数**: 1
- **资源**: 4Gi-16Gi 内存, 2-8 CPU, 1 GPU
- **存储**: 持久化卷用于模型检查点

#### Worker 服务 (moss-worker)
- **用途**: 分布式训练工作节点
- **副本数**: 5-20 (自动扩缩容)
- **资源**: 1Gi-4Gi 内存, 1-4 CPU
- **调度**: 基于队列深度自动扩缩容

### Service (`k8s/service.yaml`)

#### 内部服务
- **moss-api**: ClusterIP, 端口 8000
- **moss-training**: ClusterIP, 端口 8080
- **moss-worker**: ClusterIP, 端口 8081

#### 外部访问
- **Ingress**: api.moss.ai
- **TLS**: Let's Encrypt 自动证书
- **限流**: 100 req/s

---

## 部署模式

### 模式 1: 单节点部署

适合开发和测试环境。

```bash
# 使用 Docker Compose
docker-compose up -d
```

### 模式 2: 多节点 Kubernetes

适合生产环境。

```bash
# 部署所有组件
kubectl apply -f k8s/

# 查看状态
kubectl get all -n moss
```

### 模式 3: 混合部署

API 服务在 K8s，训练在裸金属 GPU 服务器。

```bash
# 仅部署 API
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/configmap.yaml

# 在 GPU 服务器上运行训练
python examples/train_textworld_rl.py --distributed
```

---

## 自动扩缩容

### HPA 配置

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: moss-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: moss-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

### 扩缩容策略

| 组件 | 最小副本 | 最大副本 | 触发条件 |
|------|----------|----------|----------|
| API | 3 | 10 | CPU > 70% |
| Worker | 5 | 20 | 队列深度 > 10 |

---

## 监控与日志

### Prometheus 监控

```yaml
# ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: moss-metrics
spec:
  selector:
    matchLabels:
      app: moss
  endpoints:
  - port: metrics
    interval: 30s
```

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| moss_api_requests_total | API 请求总数 | > 1000/min |
| moss_training_loss | 训练损失 | 增长 > 20% |
| moss_gpu_utilization | GPU 利用率 | < 50% |
| moss_queue_depth | 任务队列深度 | > 100 |

### 日志收集

```bash
# 查看 API 日志
kubectl logs -f deployment/moss-api -n moss

# 查看训练日志
kubectl logs -f deployment/moss-training -n moss

# 聚合日志 (使用 Fluentd/ELK)
kubectl apply -f logging/fluentd.yaml
```

---

## 安全设置

### NetworkPolicy

限制 Pod 间通信：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: moss-network-policy
spec:
  podSelector:
    matchLabels:
      app: moss
  policyTypes:
  - Ingress
  - Egress
```

### Secret 管理

```bash
# 创建数据库密码 Secret
kubectl create secret generic moss-db-secret \
  --from-literal=password=your-password \
  -n moss

# 使用 Secret
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: moss-db-secret
      key: password
```

### RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: moss-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
```

---

## 备份与恢复

### 模型检查点备份

```bash
# 创建备份 Job
kubectl apply -f k8s/backup-job.yaml

# 手动备份
kubectl exec deployment/moss-training -- \
  tar czf /backup/models-$(date +%Y%m%d).tar.gz /app/data/models
```

### 数据持久化

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: moss-data-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 500Gi
  storageClassName: fast-ssd
```

---

## 故障排除

### 常见问题

#### Pod 无法启动

```bash
# 检查事件
kubectl describe pod <pod-name> -n moss

# 检查资源限制
kubectl top pods -n moss
```

#### GPU 不可用

```bash
# 检查 GPU Operator
kubectl get pods -n gpu-operator

# 检查节点标签
kubectl get nodes -L nvidia.com/gpu.product
```

#### 服务无法访问

```bash
# 检查 Ingress
kubectl get ingress -n moss

# 检查 Service
kubectl get svc -n moss

# 检查 Endpoints
kubectl get endpoints -n moss
```

### 调试命令

```bash
# 进入容器
kubectl exec -it deployment/moss-api -n moss -- /bin/bash

# 查看环境变量
kubectl exec deployment/moss-api -n moss -- env

# 测试连接
kubectl run debug --rm -i --tty --image=curlimages/curl -- curl moss-api:8000/health
```

---

## 性能优化

### 资源优化

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### 缓存策略

```yaml
# 使用 Redis 缓存
env:
- name: CACHE_BACKEND
  value: "redis"
- name: REDIS_HOST
  value: "moss-redis"
```

### 连接池

```yaml
env:
- name: DB_POOL_SIZE
  value: "20"
- name: DB_MAX_OVERFLOW
  value: "10"
```

---

## 升级指南

### 滚动升级

```bash
# 更新镜像
kubectl set image deployment/moss-api \
  moss-api=moss/moss:v6.4.1 -n moss

# 监控升级
kubectl rollout status deployment/moss-api -n moss

# 回滚 (如需要)
kubectl rollout undo deployment/moss-api -n moss
```

### 数据库迁移

```bash
# 运行迁移 Job
kubectl apply -f k8s/migration-job.yaml

# 检查迁移状态
kubectl logs job/moss-migration -n moss
```

---

## 验收标准

- [x] Kubernetes 配置完成
- [x] Deployment 配置
- [x] Service 配置
- [x] ConfigMap 配置
- [x] HPA 自动扩缩容
- [x] NetworkPolicy 安全策略
- [x] Ingress 配置
- [x] 监控集成
- [x] 文档完整

---

## 参考文档

- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [Helm 用户指南](https://helm.sh/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html)
- [Prometheus 监控](https://prometheus.io/docs/)

---

**创建日期**: 2026-04-18  
**维护者**: MOSS Team
