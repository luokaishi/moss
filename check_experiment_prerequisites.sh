#!/bin/bash
# 检查72-168小时实验的前提条件

echo "============================================"
echo "MOSS Real Internet Experiment Prerequisites"
echo "============================================"
echo ""

# 1. 检查ARK API密钥
echo "1. ARK API (火山引擎):"
if [ -z "$ARK_API_KEY" ]; then
    echo "   ❌ Not set"
else
    echo "   ✅ Set (masked)"
fi
echo ""

# 2. 检查其他必要的API密钥
echo "2. Required API Keys for Real Internet Experiment:"
echo ""

echo "   Google Search API:"
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "   ❌ Not set (required for search)"
else
    echo "   ✅ Set"
fi

echo ""
echo "   Notion API:"
if [ -z "$NOTION_API_KEY" ]; then
    echo "   ❌ Not set (required for memory)"
else
    echo "   ✅ Set"
fi

echo ""
echo "   GitHub Token (for Gist):"
if [ -z "$GITHUB_TOKEN" ]; then
    echo "   ❌ Not set (required for code storage)"
else
    echo "   ✅ Set"
fi

echo ""

# 3. 检查Firecracker
echo "3. Firecracker MicroVM:"
if command -v firecracker &> /dev/null; then
    echo "   ✅ Installed"
else
    echo "   ❌ Not installed (recommended for sandbox)"
fi
echo ""

# 4. 检查Docker
echo "4. Docker (alternative to Firecracker):"
if command -v docker &> /dev/null; then
    echo "   ✅ Installed"
    docker --version
else
    echo "   ❌ Not installed"
fi
echo ""

echo "============================================"
echo "Summary"
echo "============================================"
