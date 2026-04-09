# MOSS 远程服务器部署指南

## 快速开始（手动部署）

### 1. 配置服务器信息

```bash
# 设置环境变量
export SERVER_HOST=root@your-server-ip
```

### 2. 部署命令（逐行执行）

```bash
# SSH登录
ssh $SERVER_HOST

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

### 3. 多服务器部署

如需在多台服务器上并行运行不同实验：

```bash
# 服务器1 - Run 4.3
export SERVER1_HOST=root@server1-ip
ssh $SERVER1_HOST
# ... 执行上述部署步骤 ...
nohup python3 experiments/run_4_3_optimized.py > experiments/run_4_3.out 2>&1 &

# 服务器2 - Run 4.4
export SERVER2_HOST=root@server2-ip
ssh $SERVER2_HOST
# ... 执行上述部署步骤 ...
nohup python3 experiments/run_4_4_optimized.py > experiments/run_4_4.out 2>&1 &
```

### 4. 自动化脚本部署

```bash
# 赋予执行权限
chmod +x scripts/deploy_remote.sh

# 设置服务器信息
export SERVER_HOST=root@your-server-ip

# 执行部署
./scripts/deploy_remote.sh deploy

# 检查状态
./scripts/deploy_remote.sh status
```

---

## 注意事项

1. **Swap配置**: 必须配置至少2G Swap，防止OOM
2. **后台运行**: 使用nohup确保SSH断开后进程继续
3. **日志监控**: 使用tail -f实时监控实验进度
4. **数据备份**: 定期备份experiments/目录

---

*本文档提供通用部署指南，请根据实际环境调整配置。*
