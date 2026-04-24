#!/bin/bash
#
# MOSS v9.3.0 - GitHub Release Publishing Script
# Usage: ./scripts/publish_github_release.sh [GITHUB_TOKEN]
#

set -e

REPO="luokaishi/moss"
VERSION="v9.3.0"
RELEASE_TITLE="MOSS v9.3.0 - Enterprise Release"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MOSS v9.3.0 GitHub Release Publisher${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# Check for GitHub token
if [ -z "$1" ] && [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GitHub token required${NC}"
    echo "Usage: $0 <github_token>"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

TOKEN="${1:-$GITHUB_TOKEN}"

# Verify assets exist
echo -e "${YELLOW}Checking build artifacts...${NC}"
ASSETS=(
    "dist/moss_refactor-9.3.0-py3-none-any.whl"
    "dist/moss_refactor-9.3.0.tar.gz"
    "extensions/vscode-moss/moss-refactor-9.3.0.vsix"
)

for asset in "${ASSETS[@]}"; do
    if [ -f "$asset" ]; then
        size=$(ls -lh "$asset" | awk '{print $5}')
        echo -e "  ${GREEN}✓${NC} $asset ($size)"
    else
        echo -e "  ${RED}✗${NC} $asset ${RED}NOT FOUND${NC}"
        exit 1
    fi
done
echo

# Create Release
echo -e "${YELLOW}Creating GitHub Release $VERSION...${NC}"
RELEASE_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/releases" \
    -d "{
        \"tag_name\": \"$VERSION\",
        \"name\": \"$RELEASE_TITLE\",
        \"body\": \"Major enterprise release with Performance Engine (58.5x speedup), IDE Ecosystem (VSCode + PyCharm), CI/CD Integration, ML Features, and Enterprise Tools.\\n\\n## Assets\\n- Python Wheel\\n- Source Distribution\\n- VSCode Extension\\n\\nSee RELEASE_v9.3.0.md for full details.\",
        \"draft\": false,
        \"prerelease\": false
    }")

# Check for errors
if echo "$RELEASE_RESPONSE" | grep -q "message"; then
    echo -e "${RED}Error creating release:${NC}"
    echo "$RELEASE_RESPONSE" | grep -o '"message":"[^"]*"'
    exit 1
fi

# Extract upload URL
UPLOAD_URL=$(echo "$RELEASE_RESPONSE" | grep -o '"upload_url":"[^"]*' | cut -d'"' -f4)
UPLOAD_URL="${UPLOAD_URL%\{*}"
RELEASE_ID=$(echo "$RELEASE_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
RELEASE_URL=$(echo "$RELEASE_RESPONSE" | grep -o '"html_url":"[^"]*' | cut -d'"' -f4)

echo -e "${GREEN}✓ Release created:${NC} $RELEASE_URL"
echo

# Upload assets
echo -e "${YELLOW}Uploading assets...${NC}"
for asset in "${ASSETS[@]}"; do
    filename=$(basename "$asset")
    echo -n "  Uploading $filename... "
    
    curl -s -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/octet-stream" \
        --data-binary "@$asset" \
        "${UPLOAD_URL}?name=$filename" > /dev/null
    
    echo -e "${GREEN}✓${NC}"
done
echo

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Release $VERSION Published Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Release URL: $RELEASE_URL"
echo
echo "Assets uploaded:"
for asset in "${ASSETS[@]}"; do
    echo "  - $(basename "$asset")"
done
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Publish to PyPI: twine upload dist/*"
echo "  2. Publish VSCode extension to marketplace"
echo "  3. Deploy documentation: mkdocs gh-deploy"
