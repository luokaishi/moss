"""
Test GitHub API with configured token
"""
import sys
sys.path.insert(0, '/workspace/projects/moss')

from integration.real_world_api_integration import RealWorldAPIIntegration
import json

print("Testing GitHub API...")
print("="*70)

integration = RealWorldAPIIntegration()

# 检查API状态
status = integration.get_available_apis()
print(f"GitHub API enabled: {status['github']}")
print()

if status['github']:
    print("Searching for 'machine learning' repositories...")
    result = integration.github.search_repositories("machine learning", language="python")
    
    if result:
        print(f"✅ Success! Found {len(result)} repositories:")
        for repo in result[:5]:
            print(f"  - {repo['name']} ({repo['stars']} stars)")
    else:
        print("❌ Search failed or no results")
        print("Note: This could be due to:")
        print("  - Token doesn't have required permissions")
        print("  - Rate limit exceeded")
        print("  - Network connectivity issues")
else:
    print("❌ GitHub API not configured")
    print("Please check integration/api_config.json")
