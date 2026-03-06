# MOSS Server Deployment Guide

**Target Server**: 43.156.104.179  
**Deploy Time**: ~5 minutes

---

## Quick Deploy (推荐)

### 1. 上传部署包

在你的本地机器上执行：

```bash
# 使用scp上传（替换为你的实际私钥路径）
scp -i /path/to/your/private_key /path/to/moss-deploy.tar.gz root@43.156.104.179:/root/

# 或者使用rsync
rsync -avz -e "ssh -i /path/to/your/private_key" /path/to/moss-deploy.tar.gz root@43.156.104.179:/root/
```

### 2. SSH到服务器并部署

```bash
ssh -i /path/to/your/private_key root@43.156.104.179
```

然后在服务器上执行：

```bash
cd /root
tar -xzf moss-deploy.tar.gz
cd moss
chmod +x deploy.sh
sudo ./deploy.sh
```

### 3. 启动MOSS

```bash
# 方式1：直接运行（前台）
cd /opt/moss
source venv/bin/activate
python moss/agents/moss_agent.py

# 方式2：后台运行
cd /opt/moss
source venv/bin/activate
nohup python moss/agents/moss_agent.py > moss.log 2>&1 &

# 方式3：系统服务
sudo systemctl enable --now moss
sudo systemctl status moss
```

---

## 手动部署（如果脚本失败）

### 1. 安装依赖

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

### 2. 创建目录

```bash
sudo mkdir -p /opt/moss
cd /opt/moss
sudo python3 -m venv venv
source venv/bin/activate
pip install numpy flask requests psutil
```

### 3. 上传代码

```bash
# 在本地执行
scp -r moss/ root@43.156.104.179:/opt/moss/
```

### 4. 启动

```bash
cd /opt/moss
source venv/bin/activate
export PYTHONPATH=/opt/moss
python moss/agents/moss_agent.py
```

---

## Docker部署（最简单）

如果你的服务器有Docker：

### 1. 上传代码

```bash
scp -r moss/ root@43.156.104.179:/root/
ssh root@43.156.104.179
```

### 2. 构建并运行

```bash
cd /root/moss
docker build -t moss .
docker run -d --name moss-agent --restart always moss
```

### 3. 查看日志

```bash
docker logs -f moss-agent
```

---

## 验证部署

### 检查运行状态

```bash
# 查看进程
ps aux | grep moss

# 查看日志
tail -f /opt/moss/moss.log

# 查看系统状态
curl http://localhost:8000/status  # 如果启用了HTTP接口
```

### 预期输出

```
MOSS Agent started: moss_server_001
State: growth, Decisions: 1
State: growth, Decisions: 2
...
```

---

## 配置说明

### 环境变量

```bash
export MOSS_AGENT_ID="moss_prod_001"
export MOSS_LOG_LEVEL="INFO"
export MOSS_RESOURCE_LIMIT="0.8"
```

### 配置文件

创建 `/opt/moss/config.json`:

```json
{
  "agent_id": "moss_server_001",
  "log_level": "INFO",
  "decision_interval": 60,
  "resource_limits": {
    "max_cpu": 0.8,
    "max_memory": 0.8
  }
}
```

---

## 监控

### 查看实时状态

```bash
# 查看日志
tail -f /opt/moss/moss.log

# 查看资源使用
htop

# 查看网络连接
netstat -tlnp | grep python
```

### 设置自动重启

```bash
sudo systemctl enable moss
sudo systemctl restart moss
```

---

## 故障排除

### 问题1：权限错误

```bash
sudo chown -R root:root /opt/moss
sudo chmod -R 755 /opt/moss
```

### 问题2：依赖缺失

```bash
cd /opt/moss
source venv/bin/activate
pip install -r requirements.txt  # 如果有的话
pip install numpy flask requests psutil
```

### 问题3：端口占用

```bash
# 查找占用端口的进程
sudo lsof -i :8000

# 杀死进程
sudo kill -9 <PID>
```

---

## 下一步

1. ✅ 部署完成
2. 运行24小时，收集数据
3. 分析日志，观察行为模式
4. 根据结果调整参数

---

**部署包位置**: `/workspace/projects/moss-deploy.tar.gz`  
**部署脚本**: `/workspace/projects/moss/deploy.sh`
