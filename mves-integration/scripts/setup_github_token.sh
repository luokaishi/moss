#!/bin/bash
# GitHub Token 快速配置脚本

set -e

ENV_FILE=".env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 GitHub Token 配置工具"
echo "========================"
echo ""

# 检查 .env 文件是否存在
if [ ! -f "$PROJECT_DIR/$ENV_FILE" ]; then
    echo "❌ .env 文件不存在"
    echo "正在创建 $PROJECT_DIR/$ENV_FILE ..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/$ENV_FILE" 2>/dev/null || {
        echo "创建新的 .env 文件..."
        cat > "$PROJECT_DIR/$ENV_FILE" << 'EOF'
# GitHub Token
GITHUB_TOKEN=

# Google API (可选)
GOOGLE_API_KEY=
GOOGLE_CSE_ID=

# Notion API (可选)
NOTION_API_KEY=
NOTION_DATABASE_ID=

# 实验配置
EXPERIMENT_DURATION_HOURS=72
MAX_COST_PER_DAY=50.0
EOF
    }
fi

# 读取当前配置
CURRENT_TOKEN=$(grep "^GITHUB_TOKEN=" "$PROJECT_DIR/$ENV_FILE" | cut -d'=' -f2)

if [ -n "$CURRENT_TOKEN" ] && [ "$CURRENT_TOKEN" != "your_github_token_here" ]; then
    echo "✅ 当前已配置 GitHub Token"
    echo "   Token: ${CURRENT_TOKEN:0:8}...${CURRENT_TOKEN: -4}"
    echo ""
    read -p "是否要更新？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "保持当前配置。"
        exit 0
    fi
fi

# 输入新 Token
echo ""
echo "请输入你的 GitHub Token:"
echo "获取方式：https://github.com/settings/tokens"
echo "权限要求：勾选 'gist'"
echo ""
read -p "GITHUB_TOKEN= " -s NEW_TOKEN
echo ""

# 验证 Token 格式
if [[ ! $NEW_TOKEN =~ ^ghp_[a-zA-Z0-9]{36}$ ]]; then
    echo ""
    echo "⚠️  Token 格式可能不正确"
    echo "   预期格式：ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消。"
        exit 1
    fi
fi

# 更新 .env 文件
if grep -q "^GITHUB_TOKEN=" "$PROJECT_DIR/$ENV_FILE"; then
    # 替换现有配置
    sed -i "s|^GITHUB_TOKEN=.*|GITHUB_TOKEN=$NEW_TOKEN|" "$PROJECT_DIR/$ENV_FILE"
else
    # 添加新配置
    echo "GITHUB_TOKEN=$NEW_TOKEN" >> "$PROJECT_DIR/$ENV_FILE"
fi

echo ""
echo "✅ GitHub Token 已配置！"
echo ""

# 测试 Token
echo "🧪 测试 Token 是否有效..."
echo ""

RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $NEW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"MOSS Token Test","public":false,"files":{"test.txt":{"content":"This is a test file created by MOSS experiment."}}}' \
  https://api.github.com/gists)

# 检查响应
if echo "$RESPONSE" | grep -q '"id"'; then
    GIST_ID=$(echo "$RESPONSE" | grep -o '"id": "[^"]*"' | cut -d'"' -f4)
    GIST_URL=$(echo "$RESPONSE" | grep -o '"html_url": "[^"]*"' | cut -d'"' -f4)
    
    echo "✅ Token 有效！"
    echo "   测试 Gist ID: $GIST_ID"
    echo "   URL: $GIST_URL"
    echo ""
    
    # 删除测试 Gist
    echo "🧹 清理测试 Gist..."
    curl -s -X DELETE \
      -H "Authorization: token $NEW_TOKEN" \
      "https://api.github.com/gists/$GIST_ID" > /dev/null
    echo "✅ 测试 Gist 已删除"
else
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message": "[^"]*"' | cut -d'"' -f4)
    echo "❌ Token 测试失败"
    echo "   错误信息：$ERROR_MSG"
    echo ""
    echo "请检查："
    echo "  1. Token 是否正确复制"
    echo "  2. 是否勾选了 'gist' 权限"
    echo "  3. Token 是否已过期"
    exit 1
fi

echo ""
echo "========================"
echo "✅ 配置完成！"
echo ""
echo "下一步："
echo "  1. 运行快速测试："
echo "     cd $PROJECT_DIR"
echo "     source .env"
echo "     python3 experiments/real_world_72h_experiment.py --quick"
echo ""
echo "  2. 运行 72h 完整实验："
echo "     nohup python3 experiments/real_world_72h_experiment.py --hours 72 > logs/real_world_72h/experiment.log 2>&1 &"
echo ""
