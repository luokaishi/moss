"""
MOSS Real-World API Integration - Quick Test
快速测试API集成框架
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from integration.real_world_api_integration import RealWorldAPIIntegration, APIBudgetTracker
import json

print("="*70)
print("MOSS REAL-WORLD API INTEGRATION - QUICK TEST")
print("="*70)
print()

# 创建集成实例
integration = RealWorldAPIIntegration()

# 显示API状态
print("API Status:")
print("-"*70)
for api, enabled in integration.get_available_apis().items():
    status = "✅ Enabled" if enabled else "❌ Not Configured"
    print(f"  {api:<20} {status}")
print()

# 预算状态
print("Budget Status:")
print("-"*70)
budget = integration.budget_tracker.get_status()
print(f"  Total: ${budget['total_budget']:.2f}")
print(f"  Used:  ${budget['used_budget']:.2f}")
print(f"  Remaining: ${budget['remaining']:.2f}")
print(f"  Can Continue: {budget['can_continue']}")
print()

# 生成配置模板
print("Generating config template...")
integration.save_config_template()
print("✅ Template saved to api_config.json.template")
print()

# 测试Wikipedia（免费，始终可用）
print("Testing Wikipedia API (Free):")
print("-"*70)
try:
    result = integration.wikipedia.search("artificial intelligence", limit=3)
    if result:
        print(f"  Found {len(result)} results:")
        for item in result[:3]:
            print(f"    - {item['title']}")
    else:
        print("  No results (normal if no network)")
except Exception as e:
    print(f"  Test skipped: {e}")
print()

# 完整报告
print("="*70)
print("INTEGRATION STATUS REPORT")
print("="*70)
report = integration.get_status_report()
print(json.dumps(report, indent=2))
print()

print("="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Get API keys (see docs/REAL_API_INTEGRATION_GUIDE.md)")
print("2. Edit integration/api_config.json")
print("3. Run full integration test")
print("4. Execute real-world MOSS experiment")
