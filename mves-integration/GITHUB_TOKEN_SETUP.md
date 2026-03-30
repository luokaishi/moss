# GitHub Token 配置指南

## 🔑 第一步：获取 GitHub Token

### 1. 访问 Token 设置页面

打开：https://github.com/settings/tokens

### 2. 创建新 Token

1. 点击 **"Generate new token (classic)"**
2. 填写备注（Note）：`MOSS 72h Experiment`
3. 设置过期时间（建议 30-90 天）
4. 勾选权限：
   - ✅ **`gist`** - 创建代码片段（必需）
   - ✅ **`repo`** - 访问仓库（可选，用于更高级实验）

### 3. 复制 Token

- 点击 **"Generate token"**
- **立即复制** token（格式：`ghp_xxxxxxxxxxxxxxxxxxxx`）
- ⚠️ **重要**：token 只会显示一次！

---

## 🔧 第二步：配置环境变量

### 方法 1: 编辑 .env 文件（推荐）

```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration

# 编辑 .env 文件
nano .env

# 找到这一行并替换为你的真实 token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 方法 2: 直接设置环境变量

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 方法 3: 添加到 shell 配置文件

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx' >> ~/.bashrc
source ~/.bashrc
```

---

## ✅ 第三步：验证配置

### 检查环境变量

```bash
echo $GITHUB_TOKEN
# 应该输出：ghp_xxxxxxxxxxxxxxxxxxxx
```

### 测试 Token 是否有效

```bash
# 测试创建 Gist
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"MOSS Test","public":true,"files":{"test.txt":{"content":"Hello World"}}}' \
  https://api.github.com/gists
```

成功响应示例：
```json
{
  "id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "html_url": "https://gist.github.com/...",
  "description": "MOSS Test",
  ...
}
```

---

## 🚀 第四步：运行实验

### 快速测试（1 小时）

```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration

# 加载环境变量
source .env

# 运行快速测试
python3 experiments/real_world_72h_experiment.py --quick
```

### 完整实验（72 小时）

```bash
# 后台运行
nohup python3 experiments/real_world_72h_experiment.py --hours 72 \
  > logs/real_world_72h/experiment.log 2>&1 &

# 查看进程
ps aux | grep real_world_72h

# 查看实时日志
tail -f logs/real_world_72h/experiment.log
```

---

## 📊 预期行为

配置 GitHub token 后，实验会：

1. **Optimization 行动** - 创建真实的 GitHub Gist
   ```
   action_type: "github_gist"
   description: "Saving optimization to GitHub Gist"
   ```

2. **真实 API 调用** - 不再是模拟数据
   ```python
   # 真实创建 Gist
   self.github.create_gist(f"opt_{timestamp}.py", code, description)
   ```

3. **审计日志** - 记录每次 API 调用
   ```json
   {
     "action_type": "github_gist",
     "success": true,
     "audit_hash": "..."
   }
   ```

---

## 🔒 安全提示

### 1. 不要泄露 Token

- ✅ 使用 `.env` 文件存储
- ✅ 将 `.env` 添加到 `.gitignore`
- ❌ 不要提交到 Git
- ❌ 不要在公开场合分享

### 2. 设置合理的权限

- 仅勾选需要的权限（`gist` 即可）
- 设置过期时间（30-90 天）
- 定期轮换 token

### 3. 监控使用情况

```bash
# 查看实验创建了多少 Gist
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists | jq '. | length'
```

---

## 🛑 第五步：撤销 Token（如需要）

### 立即撤销

1. 访问：https://github.com/settings/tokens
2. 找到 `MOSS 72h Experiment`
3. 点击 **"Delete"**

### 实验结束后清理

```bash
# 删除 .env 文件中的 token
nano .env
# 删除 GITHUB_TOKEN=... 这一行
```

---

## 📝 故障排查

### 问题 1: Token 无效

**错误**: `401 Unauthorized`

**解决**:
```bash
# 检查 token 是否正确
echo $GITHUB_TOKEN

# 重新设置
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 问题 2: 权限不足

**错误**: `403 Forbidden`

**解决**:
- 确认已勾选 `gist` 权限
- 重新创建 token 并勾选正确权限

### 问题 3: 达到速率限制

**错误**: `403 rate limit exceeded`

**解决**:
- 等待 1 小时（速率限制会重置）
- 减少实验频率
- 使用经过身份验证的请求（已配置 token 则自动认证）

---

## 📚 相关资源

- GitHub Token 文档：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- Gist API 文档：https://docs.github.com/en/rest/gists
- 速率限制：https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting

---

## ✅ 配置完成清单

- [ ] 获取 GitHub Personal Access Token
- [ ] 勾选 `gist` 权限
- [ ] 复制 token 到 `.env` 文件
- [ ] 运行 `source .env` 加载配置
- [ ] 验证 `echo $GITHUB_TOKEN` 有输出
- [ ] 运行快速测试 `python3 experiments/real_world_72h_experiment.py --quick`
- [ ] 检查日志确认 Gist 创建成功

---

**下一步**: 配置完成后运行实验！🚀

```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration
source .env
python3 experiments/real_world_72h_experiment.py --quick
```
