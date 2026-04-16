# MOSS资源优化配置指南

**目的**: 将72小时实验的内存使用从6-8GB降至3-4GB，CPU稳定在15-25%

**适用场景**: 长期运行的真实世界实验

---

## 1. OpenClaw配置

**文件**: `openclaw.json`

已配置优化项：
- `headless: true` - 无头模式，省30-50%内存
- `max_memory_per_tab: 512` - 每tab内存上限512MB
- `multi_tab_max: 3` - 限制同时打开tab数
- `resource_blocking: true` - 自动屏蔽广告/追踪脚本

**应用方式**:
```bash
# 重启OpenClaw
openclaw gateway restart
```

---

## 2. Docker配置

**文件**: `docker-compose.yml`

资源限制：
- `mem_limit: 4g` - 总内存限制4GB
- `memswap_limit: 4g` - 交换内存限制
- `pids_limit: 256` - 防止fork炸裂
- `cpu_shares: 512` - CPU权重限制

**启动命令**:
```bash
docker-compose up -d --force-recreate
```

---

## 3. MOSS代码优化

### Purpose生成频率
**修改**: `v3/core/agent_9d.py`
- 从每500步改为每2000步生成一次Purpose
- 显著降低计算压力

### 代码变更：
```python
# 原配置
purpose_interval: int = 500

# 优化后
purpose_interval: int = 2000  # 优化：降低频率以节省资源
```

---

## 4. 监控脚本

### 资源监控
**文件**: `scripts/resource_monitor.sh`

功能：
- 每60秒监控MOSS进程资源使用
- 内存超过75%时报警
- 记录到 `experiments/resource_monitor.log`

**启动**:
```bash
chmod +x scripts/resource_monitor.sh
./scripts/resource_monitor.sh &
```

### 查看资源使用
```bash
# 实时监控
docker stats moss-openclaw

# 或
top -p $(pgrep -d',' -f "real_world_72h.py")

# 查看历史
cat experiments/resource_monitor.log
```

---

## 5. 日志轮转

**文件**: `config/logrotate.conf`

配置：
- 每天轮转一次
- 保留7天历史
- 自动压缩旧日志

**启用**:
```bash
# 手动测试
logrotate -d config/logrotate.conf

# 添加到crontab（每天执行）
0 0 * * * /usr/sbin/logrotate /workspace/projects/moss/config/logrotate.conf
```

---

## 6. 快速诊断命令

```bash
# 查看MOSS进程资源使用
ps aux | grep -E 'moss|openclaw' | sort -k4nr

# 查看Docker容器资源
docker stats --no-stream

# 查看系统内存
free -h

# 查看磁盘使用
df -h

# 查看日志大小
du -sh experiments/*.jsonl logs/*.log
```

---

## 预期效果

应用以上优化后：

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 内存峰值 | 6-8GB | 3-4GB |
| CPU使用 | 40-60% | 15-25% |
| Purpose计算 | 每500步 | 每2000步 |
| 日志保留 | 无限增长 | 7天轮转 |

---

## 紧急处理

如果资源使用过高：

```bash
# 1. 降低实验速度（减少step频率）
pkill -USR1 -f "real_world_72h.py"  # 发送信号降低速度

# 2. 临时暂停实验
pkill -STOP -f "real_world_72h.py"

# 3. 恢复实验
pkill -CONT -f "real_world_72h.py"

# 4. 如果必须停止
pkill -f "real_world_72h.py"
```

---

**最后更新**: 2026-03-20
**适用版本**: MOSS v3.1.0+
