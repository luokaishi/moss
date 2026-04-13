# GitHub API Token 配置指南

本文档介绍如何为MOSS项目配置GitHub API token，以进行真实环境测试。

## 为什么需要GitHub API Token

GitHub API token允许MOSS Agent：
1. 搜索开源仓库和代码
2. 读取issue和pull request
3. 获取项目统计信息
4. 在真实互联网环境中进行学习

## 获取GitHub Personal Access Token (PAT)

### 步骤1：登录GitHub
访问 [GitHub](https://github.com) 并登录您的账户。

### 步骤2：创建新的Token
1. 点击右上角头像 → **Settings**
2. 左侧菜单选择 **Developer settings**
3. 选择 **Personal access tokens** → **Tokens (classic)**
4. 点击 **Generate new token** → **Generate new token (classic)**

### 步骤3：配置Token权限
为MOSS项目配置以下最小权限：

```
✓ repo (Full control of private repositories)
✓ repo:status (Access commit status)
✓ repo_deployment (Access deployment status)
✓ public_repo (Access public repositories)
✓ read:org (Read org and team membership, read org projects)
✓ read:user (Read all user profile data)
✓ user:email (Access user email addresses)
```

**注意**：对于测试目的，可以只勾选 `public_repo`。

### 步骤4：生成Token
1. 输入Token名称：`moss-experiment-2026`
2. 选择过期时间：建议90天或自定义
3. 点击 **Generate token**
4. **立即复制Token**（只会显示一次）

## 配置MOSS项目

### 方法1：使用配置文件
1. 复制配置文件模板：
   ```bash
   cp integration/api_config.json.template integration/api_config.json
   ```

2. 编辑配置文件：
   ```json
   {
     "google_api_key": "YOUR_GOOGLE_API_KEY",
     "google_cx": "YOUR_CUSTOM_SEARCH_ENGINE_ID",
     "notion_token": "YOUR_NOTION_INTEGRATION_TOKEN",
     "notion_database_id": "YOUR_DATABASE_ID",
     "github_token": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE"
   }
   ```

3. 将 `YOUR_GITHUB_PERSONAL_ACCESS_TOKEN_HERE` 替换为您的真实token。

### 方法2：使用环境变量
```bash
# Windows PowerShell
$env:GITHUB_TOKEN = "your_token_here"

# Windows CMD
set GITHUB_TOKEN=your_token_here

# Linux/macOS
export GITHUB_TOKEN=your_token_here
```

### 方法3：程序内设置
在实验脚本中直接设置：
```python
import os
os.environ['GITHUB_TOKEN'] = 'your_token_here'
```

## 安全注意事项

⚠️ **重要安全警告** ⚠️

1. **绝不提交Token到版本控制**
   - 确保 `integration/api_config.json` 在 `.gitignore` 中
   - 使用 `.gitignore` 规则：`integration/api_config.json`

2. **使用最小权限原则**
   - 只授予项目所需的最小权限
   - 定期轮换Token

3. **监控Token使用**
   - 定期检查GitHub安全日志
   - 设置使用量提醒

4. **本地开发最佳实践**
   ```bash
   # 使用本地环境变量文件（不提交）
   echo "GITHUB_TOKEN=your_token_here" > .env.local
   # 在.gitignore中添加 .env.local
   ```

## 模拟模式（无Token情况）

如果无法获取GitHub token，MOSS项目支持模拟模式：

### 模拟模式特点
1. **无真实API调用**：所有GitHub操作返回模拟数据
2. **完整功能测试**：可以测试Agent的逻辑和决策流程
3. **离线可用**：不需要互联网连接
4. **无成本**：不消耗API配额

### 启用模拟模式
```python
# 在实验脚本中设置test_mode=True
experiment = GitHubMOSSExperiment(test_mode=True)
```

## 测试Token配置

### 测试脚本
运行以下脚本验证Token配置：

```bash
python integration/test_github_api.py
```

### 预期输出
- **成功配置**：显示GitHub API连接成功
- **模拟模式**：显示"Running in simulation mode"
- **配置错误**：显示具体错误信息

## 故障排除

### 常见问题

#### 1. Token无效或过期
```
错误：401 Unauthorized
解决：重新生成Token并更新配置
```

#### 2. 权限不足
```
错误：403 Forbidden
解决：检查Token权限设置，确保有public_repo权限
```

#### 3. 速率限制
```
错误：429 Too Many Requests
解决：实现速率限制逻辑，或使用模拟模式
```

#### 4. 网络连接问题
```
错误：网络超时
解决：检查网络连接，或使用模拟模式
```

### 调试步骤
1. 验证Token有效性：
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

2. 检查配置文件路径：
   ```python
   import os
   print("配置文件路径:", os.path.join('integration', 'api_config.json'))
   print("文件存在:", os.path.exists('integration/api_config.json'))
   ```

3. 查看环境变量：
   ```python
   import os
   print("GITHUB_TOKEN环境变量:", os.getenv('GITHUB_TOKEN'))
   ```

## 高级配置

### 使用多个Token
对于大规模实验，可以使用Token池：
```python
tokens = ["token1", "token2", "token3"]
current_token_index = 0

def get_next_token():
    global current_token_index
    token = tokens[current_token_index]
    current_token_index = (current_token_index + 1) % len(tokens)
    return token
```

### 实现自动Token轮换
```python
class TokenManager:
    def __init__(self):
        self.tokens = self.load_tokens()
        self.current_index = 0
    
    def get_token(self):
        token = self.tokens[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.tokens)
        return token
```

## 相关文件

- `integration/api_config.json.template` - 配置文件模板
- `integration/real_world_api_integration.py` - API集成框架
- `experiments/real_github_moss_experiment_fixed.py` - GitHub实验脚本
- `tests/test_github_api.py` - API测试脚本

## 支持与反馈

如果遇到配置问题：
1. 查看项目文档
2. 检查GitHub API文档
3. 创建issue报告问题

---
**最后更新**: 2026-04-10  
**维护者**: MOSS项目团队