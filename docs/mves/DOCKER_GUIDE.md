# Docker使用指南

**版本**: 1.0  
**日期**: 2026-04-15

---

## 快速开始

### 1. 构建镜像

```bash
docker build -t moss:7layer .
```

### 2. 运行主实验

```bash
docker run -v $(pwd)/experiments/output:/app/experiments/output moss:7layer
```

### 3. 使用docker-compose

```bash
# 运行5000周期实验
docker-compose up moss

# 运行多种子验证
docker-compose up moss-multi-seed

# 运行特征对比
docker-compose up moss-feature-compare
```

---

## 实验复现

### 复现5000周期实验

```bash
# 方法1: 直接运行
docker run --rm \
  -v $(pwd)/experiments/reproducibility:/app/experiments/reproducibility \
  -e MOSS_RANDOM_SEED=42 \
  moss:7layer \
  python experiment_7layer_v2_5000.py

# 方法2: 使用复现脚本
docker run --rm \
  -v $(pwd)/experiments/reproducibility/exp_7layer_5000:/app/output \
  moss:7layer \
  bash /app/experiments/reproducibility/exp_7layer_5000/reproduce.sh
```

### 复现多种子验证

```bash
docker run --rm \
  -v $(pwd)/experiments/multi_seed_validation:/app/experiments/multi_seed_validation \
  moss:7layer \
  python experiment_multi_seed_validation.py
```

---

## 开发环境

### 进入容器

```bash
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  moss:7layer \
  /bin/bash
```

### 运行测试

```bash
docker run --rm moss:7layer python -m pytest tests/ -v
```

### 代码检查

```bash
docker run --rm moss:7layer flake8 agi/ --max-line-length=100
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MOSS_RANDOM_SEED` | 随机种子 | 42 |
| `PYTHONPATH` | Python路径 | /app |
| `MOSS_LOG_LEVEL` | 日志级别 | INFO |

---

## 数据卷

| 容器路径 | 说明 |
|----------|------|
| `/app/experiments/output` | 实验输出 |
| `/app/experiments/reproducibility` | 复现数据 |

---

## 镜像信息

- **基础镜像**: python:3.11-slim
- **大小**: ~200MB
- **Python版本**: 3.11
- **依赖**: numpy, pyyaml, pytest, flake8, scikit-learn

---

## 故障排除

### 权限问题

```bash
# Linux/Mac
sudo chown -R $(id -u):$(id -g) experiments/output

# 或使用用户权限运行
docker run --user $(id -u):$(id -g) ...
```

### 内存不足

```bash
# 增加内存限制
docker run --memory=4g moss:7layer
```

### 网络问题

```bash
# 使用国内镜像
docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple .
```

---

## 高级用法

### 多容器并行

```bash
# 同时运行多个实验
for seed in 42 43 44 45 46; do
  docker run -d \
    --name moss_seed_$seed \
    -v $(pwd)/experiments/output/seed_$seed:/app/output \
    -e MOSS_RANDOM_SEED=$seed \
    moss:7layer \
    python experiment_7layer_v2_5000.py &
done

# 等待完成
wait
```

### 自定义实验

```bash
# 挂载自定义实验脚本
docker run --rm \
  -v $(pwd)/my_experiment.py:/app/my_experiment.py \
  -v $(pwd)/output:/app/output \
  moss:7layer \
  python my_experiment.py
```

---

## 更新镜像

```bash
# 重新构建
docker build --no-cache -t moss:7layer .

# 推送到仓库
docker tag moss:7layer luokaishi/moss:7layer
docker push luokaishi/moss:7layer
```

---

## 参考

- [Docker文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [项目README](../../README.md)
