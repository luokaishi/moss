# MOSS 真实API集成准备指南

**目标**: 配置Google Search, Notion, GitHub, Wikipedia API  
**预算**: <$200  
**状态**: 准备阶段（等待API Key）

---

## 📋 API清单与费用

| API | 费用 | 额度 | 必要性 | 申请难度 |
|-----|------|------|--------|----------|
| **Google Custom Search** | $5/1000次 | 免费100次/天 | ⭐⭐⭐⭐⭐ | 中 |
| **Notion Integration** | 免费 | 无限制 | ⭐⭐⭐⭐ | 低 |
| **GitHub API** | 免费 | 5000次/小时 | ⭐⭐⭐⭐ | 低 |
| **Wikipedia API** | 免费 | 无限制 | ⭐⭐⭐ | 已可用 |

**预计月度费用**: $0-50（主要取决于Google Search使用量）

---

## 🔑 API申请步骤

### 1. Google Custom Search API

**用途**: 网页搜索，获取实时信息

**申请步骤**:
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Custom Search API**
4. 创建 **API Key** (Credentials → Create Credentials → API Key)
5. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)
6. 创建新的搜索引擎
7. 获取 **Search Engine ID (cx)**

**配置值**:
```json
{
  "google_api_key": "AIza...",
  "google_cx": "0123456789abcdef:xyz"
}
```

**费用控制**:
- 设置每日配额限制（建议100次/天 = 免费额度）
- 超出后$5/1000次，月上限$200

---

### 2. Notion Integration

**用途**: 知识存储，结构化笔记

**申请步骤**:
1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 点击 "New integration"
3. 填写名称: "MOSS Knowledge Base"
4. 选择关联的工作区
5. 复制 **Integration Token**

**数据库设置**:
1. 在Notion中创建数据库
2. 添加Integration到数据库（Share → 添加Integration）
3. 复制 **Database ID** (从URL获取)

**配置值**:
```json
{
  "notion_token": "secret_...",
  "notion_database_id": "abcdef1234567890"
}
```

**费用**: 完全免费

---

### 3. GitHub Personal Access Token

**用途**: 代码搜索，开源项目探索

**申请步骤**:
1. 访问 GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token
4. 选择权限:
   - `repo` (读取仓库)
   - `read:org` (读取组织)
   - `read:user` (读取用户信息)
5. 生成并复制Token

**配置值**:
```json
{
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}
```

**费用**: 完全免费（公共仓库）

---

### 4. Wikipedia API

**状态**: ✅ 已可用，无需申请

**说明**: Wikipedia提供完全免费的REST API，无需认证

**使用限制**: 
- 建议速率: 1次/秒
- 请遵守 [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Terms_of_Use)

---

## 🛠️ 配置部署

### 步骤1: 创建配置文件

```bash
cd /workspace/projects/moss
cp integration/api_config.json.template integration/api_config.json
```

### 步骤2: 编辑配置文件

```json
{
  "google_api_key": "YOUR_GOOGLE_API_KEY_HERE",
  "google_cx": "YOUR_CX_HERE",
  "notion_token": "YOUR_NOTION_TOKEN_HERE", 
  "notion_database_id": "YOUR_DB_ID_HERE",
  "github_token": "YOUR_GITHUB_TOKEN_HERE"
}
```

### 步骤3: 测试连接

```bash
python integration/real_world_api_integration.py
```

---

## 💰 预算管理

### 预算追踪器功能

```python
from integration.real_world_api_integration import RealWorldAPIIntegration

integration = RealWorldAPIIntegration()

# 查看预算状态
status = integration.budget_tracker.get_status()
print(f"Used: ${status['used_budget']:.2f} / ${status['total_budget']:.2f}")
```

### 自动限制
- 80%预算: 警告日志
- 95%预算: 自动禁用付费API
- 100%预算: 仅保留Wikipedia（免费）

### 成本优化建议
1. **优先使用Wikipedia**: 免费且覆盖大部分知识需求
2. **缓存搜索结果**: 避免重复查询
3. **限制Google Search**: 仅在必要时使用
4. **批量处理**: 合并多个小请求

---

## 🔒 安全考虑

### 敏感信息保护

**永远不要**:
- ❌ 提交API Key到GitHub
- ❌ 在代码中硬编码Token
- ❌ 在日志中打印完整Token

**正确做法**:
- ✅ 使用环境变量
- ✅ 配置文件加入.gitignore
- ✅ Token部分掩码显示

### 已配置的保护
```bash
# .gitignore 已包含
integration/api_config.json
*.key
*.token
```

### 权限最小化
- Google API: 仅搜索权限，无删除/修改
- Notion: 仅特定数据库访问
- GitHub: 仅读取权限，无写入

---

## 📊 预期实验设计

### 真实互联网子集实验

**场景1: 知识发现**
```
MOSS自主搜索 "最新AI进展" 
→ Google Search获取网页
→ Wikipedia获取背景知识  
→ Notion存储整理后的信息
```

**场景2: 代码探索**
```
MOSS发现需要实现功能X
→ GitHub搜索相关开源项目
→ 学习现有实现
→ 整合到自身知识库
```

**场景3: 持续学习**
```
每日自动执行:
→ 搜索5个新主题
→ 存储到Notion知识库
→ 更新MOSS知识图谱
```

---

## ⏱️ 时间安排

| 任务 | 预估时间 | 状态 |
|------|---------|------|
| Google API申请 | 30分钟 | ⏳ 待执行 |
| Notion Integration | 15分钟 | ⏳ 待执行 |
| GitHub Token | 10分钟 | ⏳ 待执行 |
| 配置测试 | 15分钟 | ⏳ 待执行 |
| **总计** | **~70分钟** | **准备中** |

---

## ✅ 准备清单

- [ ] Google Cloud项目创建
- [ ] Custom Search API启用
- [ ] Search Engine创建
- [ ] Notion Integration创建
- [ ] Notion数据库设置
- [ ] GitHub Token生成
- [ ] 配置文件编辑
- [ ] 连接测试通过
- [ ] 预算验证
- [ ] 安全审查

---

## 🚀 快速开始（配置完成后）

```python
from integration.real_world_api_integration import RealWorldAPIIntegration

# 初始化（自动加载配置）
integration = RealWorldAPIIntegration()

# 执行真实动作
result = integration.execute_moss_action(
    'search_knowledge',
    {'query': 'machine learning latest trends'}
)

# 存储知识
integration.execute_moss_action(
    'store_knowledge',
    {
        'title': 'ML Trends 2026',
        'content': json.dumps(result, indent=2)
    }
)
```

---

**准备状态**: 框架就绪，等待API Key配置  
**预计完成**: 配置后1小时内可运行真实实验  
**文档更新**: 2026-03-10 20:45
