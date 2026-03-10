#!/usr/bin/env python3
"""
预测72小时实验的token消耗
"""

import json
from datetime import datetime

# 当前数据（从日志中提取）
current_data = {
    'elapsed_minutes': 2,  # 约2分钟
    'tokens_used': 11090,
    'actions': 100
}

# 实验配置
total_hours = 72
total_minutes = total_hours * 60
token_budget = 100000

# 计算速率
tokens_per_minute = current_data['tokens_used'] / current_data['elapsed_minutes']
tokens_per_hour = tokens_per_minute * 60
tokens_per_action = current_data['tokens_used'] / current_data['actions']

# 预测总消耗
projected_total = tokens_per_minute * total_minutes
projected_with_variance_low = projected_total * 0.7  # 30% lower
projected_with_variance_high = projected_total * 1.3  # 30% higher

# 预测完成时间（如果保持当前速率）
if projected_total > token_budget:
    time_to_exhaustion = token_budget / tokens_per_minute
    exhaustion_hours = time_to_exhaustion / 60
else:
    exhaustion_hours = None

print("="*60)
print("MOSS 72-Hour Experiment - Token Consumption Projection")
print("="*60)
print()

print("CURRENT STATUS:")
print(f"  Elapsed time: {current_data['elapsed_minutes']} minutes")
print(f"  Tokens used: {current_data['tokens_used']:,}")
print(f"  Actions taken: {current_data['actions']}")
print()

print("CONSUMPTION RATE:")
print(f"  Tokens per minute: {tokens_per_minute:.1f}")
print(f"  Tokens per hour: {tokens_per_hour:,.0f}")
print(f"  Tokens per action: {tokens_per_action:.1f}")
print()

print("PROJECTION (72 hours):")
print(f"  Projected total (current rate): {projected_total:,.0f} tokens")
print(f"  With -30% variance: {projected_with_variance_low:,.0f} tokens")
print(f"  With +30% variance: {projected_with_variance_high:,.0f} tokens")
print(f"  Budget: {token_budget:,} tokens")
print()

print("ANALYSIS:")
budget_ratio = projected_total / token_budget
if budget_ratio > 1.5:
    status = "🔴 CRITICAL"
    message = f"Will exhaust budget in ~{exhaustion_hours:.1f} hours"
elif budget_ratio > 1.0:
    status = "🟡 WARNING" 
    message = f"Will exhaust budget in ~{exhaustion_hours:.1f} hours"
elif budget_ratio > 0.8:
    status = "🟡 CAUTION"
    message = "Budget sufficient but tight"
else:
    status = "🟢 OK"
    message = "Budget sufficient"

print(f"  Status: {status}")
print(f"  Budget usage ratio: {budget_ratio:.1%}")
print(f"  Message: {message}")
print()

print("RECOMMENDATIONS:")
if budget_ratio > 1.0:
    print("  1. ⚠️  Reduce action frequency (increase sleep time)")
    print("  2. ⚠️  Lower token cost per action")
    print("  3. ⚠️  Increase budget or reduce duration")
else:
    print("  1. ✅ Current rate is sustainable")
    print("  2. 💡 Consider adding more complex actions")
    print("  3. 💡 Can increase knowledge acquisition rate")

print()
print("="*60)
