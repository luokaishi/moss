#!/bin/bash
# GitHub Token 测试脚本

set -e

cd "$(dirname "$0")/.."
source .env

echo "🔍 GitHub Token 测试"
echo "===================="
echo ""

# 1. 验证 Token 基本信息
echo "1️⃣ 验证 Token 基本信息..."
RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user)

if echo "$RESPONSE" | grep -q '"login"'; then
    LOGIN=$(echo "$RESPONSE" | jq -r '.login')
    ID=$(echo "$RESPONSE" | jq -r '.id')
    echo "   ✅ Token 有效"
    echo "   用户：$LOGIN (ID: $ID)"
else
    echo "   ❌ Token 无效"
    echo "   错误：$(echo "$RESPONSE" | jq -r '.message')"
    exit 1
fi

echo ""

# 2. 检查 Token 权限
echo "2️⃣ 检查 Token 权限..."
SCOPES=$(curl -s -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user \
  | grep -i "x-oauth-scopes" | cut -d: -f2 | tr -d ' ')

if [ -n "$SCOPES" ]; then
    echo "   当前权限：$SCOPES"
    
    if echo "$SCOPES" | grep -q "gist"; then
        echo "   ✅ 包含 gist 权限"
    else
        echo "   ⚠️  缺少 gist 权限"
        echo ""
        echo "   需要重新创建 token："
        echo "   1. 访问：https://github.com/settings/tokens"
        echo "   2. 找到当前 token 并删除"
        echo "   3. 点击 'Generate new token (classic)'"
        echo "   4. ✅ 勾选 'gist' 权限"
        echo "   5. 复制新 token 并更新 .env 文件"
        exit 1
    fi
else
    echo "   ⚠️  无法获取权限信息"
fi

echo ""

# 3. 测试创建 Gist
echo "3️⃣ 测试创建 Gist..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"description\": \"MOSS 72h Experiment Test\",
    \"public\": false,
    \"files\": {
      \"moss_test_$(date +%s).txt\": {
        \"content\": \"MOSS Real World Experiment\nUser: $LOGIN\nTest Time: $(date -Iseconds)\"
      }
    }
  }" \
  https://api.github.com/gists)

if echo "$RESPONSE" | grep -q '"id"'; then
    GIST_ID=$(echo "$RESPONSE" | jq -r '.id')
    GIST_URL=$(echo "$RESPONSE" | jq -r '.html_url')
    echo "   ✅ Gist 创建成功"
    echo "   ID: $GIST_ID"
    echo "   URL: $GIST_URL"
    
    # 清理测试 Gist
    echo ""
    echo "4️⃣ 清理测试 Gist..."
    curl -s -X DELETE -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/gists/$GIST_ID" > /dev/null
    echo "   ✅ 已删除测试 Gist"
    
    echo ""
    echo "===================="
    echo "✅ Token 配置完成！可以运行实验了"
    echo ""
    echo "运行快速测试："
    echo "  python3 experiments/real_world_72h_experiment.py --quick"
    echo ""
    echo "运行 72h 完整实验："
    echo "  nohup python3 experiments/real_world_72h_experiment.py --hours 72 > logs/real_world_72h/experiment.log 2>&1 &"
    
else
    ERROR=$(echo "$RESPONSE" | jq -r '.message')
    echo "   ❌ Gist 创建失败"
    echo "   错误：$ERROR"
    echo ""
    echo "可能原因："
    echo "  1. Token 没有 gist 权限"
    echo "  2. Token 已过期"
    echo "  3. 达到速率限制"
    exit 1
fi
