#!/bin/bash
# MOSS GitHub发布 - 完整脚本
# 执行前需要：1) 创建GitHub仓库 2) 提供用户名

set -e

echo "=========================================="
echo "MOSS GitHub发布脚本"
echo "=========================================="

# 检查目录
if [ ! -f "README_GITHUB.md" ]; then
    echo "错误：请在 moss/ 目录下运行此脚本"
    exit 1
fi

# GitHub用户名
GITHUB_USER="luokaishi"

REPO_NAME="moss"
REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME"

echo ""
echo "GitHub用户名: $GITHUB_USER"
echo "仓库名: $REPO_NAME"
echo "完整地址: $REPO_URL"
echo ""
read -p "确认发布? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "已取消"
    exit 1
fi

# 准备README
echo ""
echo "[1/7] 准备README..."
cp README_GITHUB.md README.md
echo "✓ README.md 就绪"

# 初始化git
echo "[2/7] 初始化Git仓库..."
if [ ! -d ".git" ]; then
    git init
    git branch -M main
    echo "✓ Git初始化完成"
else
    echo "✓ Git已存在"
fi

# 配置git
echo "[3/7] 配置Git..."
git config user.email "cash.researcher@example.com" 2>/dev/null || true
git config user.name "Cash" 2>/dev/null || true
echo "✓ Git配置完成"

# 添加文件
echo "[4/7] 添加文件到Git..."
git add .
echo "✓ 文件已添加"

# 提交
echo "[5/7] 创建提交..."
git commit -m "Initial release: MOSS v0.1.0 - Multi-Objective Self-Driven System

This release includes:
- Complete MOSS framework implementation (6000+ lines)
- Four objective modules: Survival, Curiosity, Influence, Optimization
- Dynamic weight allocation mechanism
- 5 validated simulation experiments
- Full documentation and deployment guides
- ICLR 2027 workshop submission ready

Authors: Cash, Fuxi (equal contribution)
Date: March 2026

Paper: MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution" || echo "Already committed"
echo "✓ 提交完成"

# 添加远程仓库
echo "[6/7] 连接GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL.git"
echo "✓ 远程仓库已添加"

# 推送
echo "[7/7] 推送到GitHub..."
git push -u origin main || {
    echo ""
    echo "=========================================="
    echo "推送失败！可能原因："
    echo "=========================================="
    echo "1. GitHub仓库未创建"
    echo "   解决: 访问 https://github.com/new 创建仓库"
    echo ""
    echo "2. 用户名错误"
    echo "   解决: 确认你的GitHub用户名正确"
    echo ""
    echo "3. 需要认证"
    echo "   解决: 使用SSH密钥或Personal Access Token"
    echo ""
    exit 1
}

echo ""
echo "=========================================="
echo "🎉 GitHub发布成功！"
echo "=========================================="
echo ""
echo "📦 仓库地址: $REPO_URL"
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 访问仓库设置:"
echo "   $REPO_URL/settings"
echo ""
echo "2. 添加描述和标签:"
echo "   Description: MOSS: Multi-Objective Self-Driven System for AI Autonomous Evolution"
echo "   Topics: ai, artificial-intelligence, autonomous-agents, multi-objective-optimization, self-driven-ai"
echo ""
echo "3. 创建Release:"
echo "   $REPO_URL/releases/new"
echo "   Tag: v0.1.0"
echo "   Title: Initial Release - MOSS Framework"
echo ""
echo "4. 社交媒体发布:"
echo "   - Twitter/X: 分享 $REPO_URL"
echo "   - LinkedIn: 发布项目介绍"
echo "   - Reddit: r/MachineLearning"
echo ""
echo "=========================================="
echo "⏰ 时间戳已建立: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "=========================================="
