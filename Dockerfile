# MOSS 7层AGI涌现架构 - Docker容器

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir numpy pyyaml pytest flake8 scikit-learn

# 设置Python路径
ENV PYTHONPATH=/app

# 创建实验输出目录
RUN mkdir -p /app/experiments/output

# 默认命令
CMD ["python", "experiment_7layer_v2_5000.py"]
