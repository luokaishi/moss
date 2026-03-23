# MOSS 远程服务器部署指南

## 快速开始（手动部署）

### 1. 配置服务器信息

```bash
# 设置环境变量
export SERVER1_HOST=root@your-server1-ip
export SERVER2_HOST=root@your-server2-ip
```

### 2. 部署命令（逐行执行）

#### 服务器1 - Run 4.3（Curiosity主导初始Purpose）

```bash
# SSH登录
ssh $SERVER1_HOST

# 安装基础依赖
apt-get update && apt-get install -y python3 python3-pip git

# 配置Swap（重要！）
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 克隆MOSS
cd /opt && git clone https://github.com/luokaishi/moss.git

# 安装Python依赖
cd /opt/moss && pip3 install numpy

# 启动实验（后台运行）
nohup python3 experiments/run_4_3_optimized.py > experiments/run_4_3.out 2>&1 &

# 检查状态
tail -f experiments/run_4_3.out
```

#### 服务器2 - Run 4.4（高探索率20%）

```bash
# SSH登录
ssh $SERVER2_HOST

# 安装基础依赖
apt-get update && apt-get install -y python3 python3-pip git

# 配置Swap
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 克隆MOSS
cd /opt && git clone https://github.com/luokaishi/moss.git

# 安装Python依赖
cd /opt/moss && pip3 install numpy

# 启动实验（后台运行）
nohup python3 experiments/run_4_4_optimized.py > experiments/run_4_4.out 2>&1 &

# 检查状态
tail -f experiments/run_4_4.out
```

### 3. 自动化脚本部署

```bash
# 赋予执行权限
chmod +x scripts/deploy_remote.sh

# 设置服务器信息
export SERVER1_HOST=root@your-server1-ip
export SERVER2_HOST=root@your-server2-ip

# 执行部署
./scripts/deploy_remote.sh deploy

# 检查状态
./scripts/deploy_remote.sh status
```

## 实验设计对比

| 实验 | 服务器 | 变体 | 目的 |
|------|--------|------|------|
| Run 4.2 | 当前 | 原始参数 | 基准对照 |
| Run 4.3 | 服务器1 | Curiosity主导初始 | 验证初始Purpose影响 |
| Run 4.4 | 服务器2 | 高探索率20% | 验证探索率影响 |

## 监控命令

```bash
# 检查进程
ps aux | grep run_4_3
ps aux | grep run_4_4

# 查看最新状态
tail -20 /opt/moss/experiments/run_4_3.out
tail -20 /opt/moss/experiments/run_4_4.out

# 查看完整状态
cat /opt/moss/experiments/run_4_3_status.json
cat /opt/moss/experiments/run_4_4_status.json
```

## 实验完成时间

- **持续时间**: 8小时
- **目标Steps**: 2,880,000
- **预计完成**: 启动后8小时

## 数据收集

实验完成后，数据文件位于：
```
/opt/moss/experiments/
├── run_4_3_actions.jsonl      # 行动记录
├── run_4_3_status.json        # 最终状态
├── run_4_3.out                # 运行日志
└── .checkpoints_run4_3/       # 检查点
```

## 注意事项

1. **Swap必须配置**: 1GB内存不足，必须配置2GB Swap
2. **后台运行**: 使用`nohup`确保SSH断开后继续运行
3. **防火墙**: 确保服务器可以访问GitHub
4. **磁盘空间**: 确保有至少5GB可用空间

## 故障排查

```bash
# 如果进程停止，查看错误
tail -50 /opt/moss/experiments/run_4_3.out

# 内存不足检查
free -h && swapon --show

# 恢复实验（如果有checkpoint）
cd /opt/moss && python3 experiments/run_4_3_optimized.py
```
