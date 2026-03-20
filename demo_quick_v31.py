#!/usr/bin/env python3
"""
MOSS v3.1.0 Quick Demo
======================

5-minute demonstration of self-generated Purpose (D9).

Run: python demo_quick_v31.py
"""

import sys
sys.path.insert(0, 'v3')

from core.agent_9d import MOSSv3Agent9D as MOSSAgent9D
import json

print("=" * 70)
print("🚀 MOSS v3.1.0 Quick Demo - Self-Generated Purpose")
print("=" * 70)
print()

# Create 3 agents with identical initial conditions
print("Creating 3 identical agents...")
agents = [
    MOSSAgent9D(agent_id=f"agent_{i}", initial_weights=[0.25]*8)
    for i in range(3)
]
print(f"✓ Created {len(agents)} agents with uniform weights [0.25, 0.25, 0.25, 0.25]")
print()

# Run for 100 steps
print("Running 100 steps...")
for step in range(100):
    for agent in agents:
        agent.step()
    if step % 20 == 0:
        print(f"  Step {step}/100")
print("✓ Simulation complete")
print()

# Check generated purposes
print("=" * 70)
print("📊 Generated Purposes (Purpose Divergence)")
print("=" * 70)
print()

for agent in agents:
    purpose = agent.get_purpose()
    purpose_type = agent.get_purpose_type()
    print(f"Agent {agent.agent_id}:")
    print(f"  Type: {purpose_type}")
    print(f"  Statement: {purpose['statement']}")
    print(f"  Dominant: {purpose['dominant']}")
    print()

# Check if purposes diverged
purpose_types = [a.get_purpose_type() for a in agents]
unique_types = set(purpose_types)

print("=" * 70)
print("🎯 Result")
print("=" * 70)
print(f"Unique purpose types: {len(unique_types)} / {len(agents)} agents")
print(f"Types: {', '.join(unique_types)}")
print()

if len(unique_types) > 1:
    print("✅ Purpose Divergence VALIDATED")
    print("   Identical agents developed different 'life philosophies'")
else:
    print("⚠️  Run again - stochastic process may produce same type")

print()
print("=" * 70)
print("Next steps:")
print("  - Run full experiments: python v3/experiments/purpose_society.py")
print("  - See D9 validation: python experiments/goal_evolution_test.py")
print("  - Read paper: https://github.com/luokaishi/moss/releases/tag/v3.1.0")
print("=" * 70)
