#!/bin/bash
# MOSS GitHub一键发布脚本
# 在服务器上执行此脚本，自动推送到GitHub

set -e

echo "=========================================="
echo "MOSS GitHub一键发布"
echo "=========================================="

# 检查是否在正确的目录
if [ ! -f "README_GITHUB.md" ]; then
    echo "错误：请在moss/目录下运行此脚本"
    exit 1
fi

# 你的GitHub用户名（需要替换）
GITHUB_USER="YOUR_GITHUB_USERNAME"
REPO_NAME="moss"

echo ""
echo "请确认以下信息："
echo "GitHub用户名: $GITHUB_USER"
echo "仓库名: $REPO_NAME"
echo ""
read -p "是否正确? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "请编辑此脚本，修改 GITHUB_USER 变量"
    exit 1
fi

# 复制GitHub版本README
echo "[1/6] 准备README..."
cp README_GITHUB.md README.md

# 初始化git（如果还没有）
echo "[2/6] 初始化Git仓库..."
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

# 配置git（如果需要）
echo "[3/6] 配置Git..."
git config user.email "cash.research@example.com"
git config user.name "Cash"

# 添加所有文件
echo "[4/6] 添加文件..."
git add .

# 提交
echo "[5/6] 创建提交..."
git commit -m "Initial release: MOSS framework v0.1.0

- Multi-objective self-driven system implementation
- Four objective modules: Survival, Curiosity, Influence, Optimization
- Dynamic weight allocation mechanism
- 5 validated simulation experiments
- Complete documentation and examples
- ICLR 2027 workshop submission ready

Authors: Cash, Fuxi (equal contribution)" || echo "Already committed"

# 连接到GitHub并推送
echo "[6/6] 推送到GitHub..."
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || echo "Remote already exists"
git push -u origin main

echo ""
echo "=========================================="
echo "GitHub发布成功！"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "下一步:"
echo "1. 访问 https://github.com/$GITHUB_USER/$REPO_NAME"
echo "2. 点击 'Settings'"
echo "3. 添加描述和标签"
echo "4. 创建 Release v0.1.0"
echo ""
echo "=========================================="
