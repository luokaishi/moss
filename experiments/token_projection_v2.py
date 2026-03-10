#!/usr/bin/env python3
"""
重新计算调整后的token消耗预测
"""

total_hours = 72
total_minutes = total_hours * 60
token_budget = 50000  # 调整后预算

# 新参数
action_interval_minutes = 5  # 每5分钟一个动作
actions_per_hour = 60 / action_interval_minutes  # 12个动作/小时
total_actions = actions_per_hour * total_hours  # 864个动作

# 平均token成本 (加权平均)
avg_cost_per_action = (
    0.2 * 50 +   # search: 20%概率，50 tokens
    0.2 * 30 +   # learn: 20%概率，30 tokens
    0.2 * 40 +   # organize: 20%概率，40 tokens
    0.2 * 20 +   # optimize: 20%概率，20 tokens
    0.2 * 5      # rest: 20%概率，5 tokens
)

projected_total = total_actions * avg_cost_per_action

# 加上检查点成本 (每2小时一个检查点，每个约100 tokens)
checkpoints = total_hours / 2
checkpoint_cost = checkpoints * 100

total_projected = projected_total + checkpoint_cost

print("="*60)
print("MOSS 72-Hour Experiment - Adjusted Token Projection")
print("="*60)
print()

print("ADJUSTED PARAMETERS:")
print(f"  Action interval: {action_interval_minutes} minutes")
print(f"  Actions per hour: {actions_per_hour:.0f}")
print(f"  Total actions (72h): {total_actions:.0f}")
print(f"  Average cost per action: {avg_cost_per_action:.1f} tokens")
print(f"  Checkpoints (every 2h): {checkpoints:.0f}")
print()

print("PROJECTION:")
print(f"  Action token cost: {projected_total:,.0f} tokens")
print(f"  Checkpoint cost: {checkpoint_cost:,.0f} tokens")
print(f"  TOTAL PROJECTED: {total_projected:,.0f} tokens")
print(f"  Budget: {token_budget:,} tokens")
print()

print("ANALYSIS:")
usage_ratio = total_projected / token_budget
if usage_ratio > 1.0:
    print(f"  Status: 🔴 STILL OVER BUDGET ({usage_ratio:.1%})")
    shortfall = total_projected - token_budget
    print(f"  Shortfall: {shortfall:,.0f} tokens")
    print(f"  Recommendation: Reduce action frequency to {action_interval_minutes * usage_ratio:.0f} min")
elif usage_ratio > 0.9:
    print(f"  Status: 🟡 TIGHT BUT OK ({usage_ratio:.1%})")
else:
    print(f"  Status: 🟢 SUSTAINABLE ({usage_ratio:.1%})")

print()
print("SUSTAINABLE CONFIGURATION:")
sustainable_interval = action_interval_minutes * usage_ratio
print(f"  Recommended action interval: {sustainable_interval:.0f} minutes")
print(f"  This gives {60/sustainable_interval:.1f} actions/hour")
print(f"  Total actions in 72h: {72 * 60/sustainable_interval:.0f}")

print()
print("="*60)
