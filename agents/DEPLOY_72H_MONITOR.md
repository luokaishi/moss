# MOSS 72h Experiment Monitor - Sub-Agent Deployment
## 子Agent部署说明

---

## 📋 任务概述

**Agent名称**: 72h-Experiment-Monitor  
**部署位置**: 阿里云OpenClaw  
**监控目标**: PID 11788 (72h真实世界实验)  
**监控频率**: 每30分钟  
**持续时间**: 68小时（至2026-03-27 10:12）  
**异常响应**: 立即生成警报文件

---

## 🚀 部署步骤

### 步骤1: 上传监控脚本到阿里云

在阿里云OpenClaw Web Terminal执行：

```bash
cd /home/admin/moss

# 创建agents目录
mkdir -p agents

# 创建监控脚本（复制以下内容到agents/monitor_72h_agent.sh）
```

### 步骤2: 启动监控Agent

```bash
cd /home/admin/moss
chmod +x agents/monitor_72h_agent.sh

# 后台启动（nohup确保SSH断开后继续运行）
nohup ./agents/monitor_72h_agent.sh > logs/72h_monitor.log 2>&1 &

echo $! > /tmp/moss_72h_monitor.pid
echo "监控Agent已启动，PID: $(cat /tmp/moss_72h_monitor.pid)"
```

### 步骤3: 验证启动

```bash
# 检查进程
ps aux | grep monitor_72h_agent | grep -v grep

# 检查日志
tail -5 /home/admin/moss/logs/72h_monitor.log

# 检查报告文件
cat /home/admin/moss/experiments/72h_monitor_report.json
```

---

## 📊 监控机制

### 正常状态
- 每30分钟检查一次PID 11788
- 记录CPU时间和运行状态
- 每小时保存详细状态到历史文件

### 异常检测
- **进程消失**: 立即生成 `/tmp/moss_72h_emergency_alert`
- **日志异常**: 记录到 `logs/72h_monitor.log`
- **紧急通知**: 追加到 `/tmp/moss_alerts.log`

### 状态报告文件

**主报告**: `/home/admin/moss/experiments/72h_monitor_report.json`
```json
{
  "monitor_started": "2026-03-24T16:20:00+08:00",
  "target_pid": 11788,
  "target_experiment": "72h_real_world",
  "status": "RUNNING",
  "checks": [...]
}
```

**历史记录**: `/home/admin/moss/experiments/72h_status_history.jsonl`
```jsonl
{"timestamp": "...", "check": 1, "status": "RUNNING", "cpu_time": "0:23"}
{"timestamp": "...", "check": 2, "status": "RUNNING", "cpu_time": "0:45"}
```

---

## 🔔 主会话检测机制

主会话（当前AI）每4-6小时检查以下文件：

```bash
# 检查紧急警报
if [ -f "/tmp/moss_72h_emergency_alert" ]; then
    echo "🚨 72h实验异常停止！"
    cat /tmp/moss_alerts.log
fi

# 检查监控状态
if [ -f "/home/admin/moss/experiments/72h_monitor_report.json" ]; then
    cat /home/admin/moss/experiments/72h_monitor_report.json
fi
```

---

## 🛑 停止监控

如需停止子Agent：

```bash
touch /tmp/moss_monitor_stop
kill $(cat /tmp/moss_72h_monitor.pid) 2>/dev/null
```

---

## 📅 预计完成

**实验完成时间**: 2026-03-27 10:12  
**监控结束**: 实验完成后自动退出

---

## 📞 联系机制

- **正常运行**: 无通知，静默监控
- **异常警报**: 生成 `/tmp/moss_72h_emergency_alert`
- **完成通知**: 实验正常结束后，子Agent退出，主会话可通过日志确认

---

**部署状态**: 待执行  
**创建时间**: 2026-03-24 16:20  
**版本**: v1.0
