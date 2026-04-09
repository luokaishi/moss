# GitHub 推送指南

## 当前状态

- ✅ 本地提交已完成 (`git commit`)
- ✅ 22个文件已更新
- ⏳ 等待推送到远程仓库

---

## 为什么推送失败

当前环境缺少 GitHub 身份验证：
- 无 SSH 密钥配置
- 无 Git 凭据缓存
- 需要你的 GitHub Token 或 SSH 密钥

---

## 推送方法（选择一种）

### 方法 1：使用 GitHub Token（推荐）

#### 步骤 1：创建 Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选权限：
   - ✅ `repo` (完整仓库访问)
4. 点击 "Generate token"
5. **复制 Token**（只显示一次）

#### 步骤 2：推送代码

```bash
cd /workspace/projects/moss

# 使用 token 推送
git remote set-url origin https://<TOKEN>@github.com/luokaishi/moss.git
git push origin main

# 示例（将 ghp_xxxx 替换为你的真实 token）
# git remote set-url origin https://ghp_xxxxxxxxxxxx@github.com/luokaishi/moss.git
```

---

### 方法 2：使用 SSH 密钥

#### 步骤 1：生成 SSH 密钥（如果没有）

```bash
# 生成新密钥
ssh-keygen -t ed25519 -C "cash.researcher@example.com"

# 按回车使用默认路径
# 可设置密码（可选）
```

#### 步骤 2：添加公钥到 GitHub

```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub
```

1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. Title: `moss-workspace`
4. Key: 粘贴上面的公钥内容
5. 点击 "Add SSH key"

#### 步骤 3：推送代码

```bash
cd /workspace/projects/moss

# 切换到 SSH 地址
git remote set-url origin git@github.com:luokaishi/moss.git

# 测试连接
ssh -T git@github.com

# 推送
git push origin main
```

---

## 验证推送成功

```bash
# 检查远程状态
git log --oneline --graph --all

# 查看最新提交
git log -1

# 检查远程分支
git branch -r
```

---

## 推送内容摘要

本次推送包含以下更新：

### 📝 文档更新
- `README.md` - 添加1,000代Ultra实验里程碑
- `DEPLOY.md` - 更新为本地部署指南
- `docs/paper_simple.md` - Markdown版论文（含Ultra实验结果）

### 📦 新增内容
- `docs/iclr_submission/` - ICLR 2027 Workshop投稿完整包
- `docs/longterm_results.md` - 长期实验结果分析
- `start_ultra_experiment.sh` - Ultra实验启动脚本
- `sandbox/generate_charts.py` - 数据可视化脚本

### 🔧 实验相关
- 实验4/5设计文档
- 长期实验监控脚本
- 结果检查工具

---

## 推送后验证

访问仓库确认更新：
https://github.com/luokaishi/moss

应看到：
- ✅ 最新提交时间（2026-03-06）
- ✅ README 显示1,000代实验结果
- ✅ 新增 `docs/iclr_submission/` 目录

---

## 常见问题

### Q: Token 推送失败 (403)
```
fatal: unable to access: The requested URL returned error: 403
```
**解决**: Token 权限不足，确保勾选了 `repo` 权限

### Q: SSH 推送失败 (Permission denied)
```
Permission denied (publickey)
```
**解决**: 
```bash
# 启动 SSH 代理
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### Q: 冲突 (rejected)
```
! [rejected]        main -> main (fetch first)
```
**解决**:
```bash
git pull origin main --rebase
git push origin main
```

---

## 安全提醒

⚠️ **Token 安全**
- 不要将 Token 提交到代码中
- 定期更换 Token（GitHub 建议）
- 如果泄露，立即在 GitHub 删除并重新生成

⚠️ **SSH 密钥安全**
- 私钥 (`id_ed25519`) 永远不要分享
- 只分享公钥 (`id_ed25519.pub`)

---

*生成时间: 2026-03-06*
*推送提交: ef6e395 - docs: Update GitHub with Ultra experiment results*
