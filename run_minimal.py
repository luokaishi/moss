"""
MOSS v5.2.0 - Minimal Runnable Example
=======================================

Quick verification that the full 9-dimension agent system runs correctly.

Usage:
    python run_minimal.py
"""

import sys
import os
import time
import json
import numpy as np

# --- Path setup ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from moss.core.unified_agent import UnifiedMOSSAgent, MOSSConfig, AgentState
from moss.core.objectives import (
    SurvivalObjective, CuriosityObjective,
    InfluenceObjective, OptimizationObjective
)


# =========================================================
# Helper
# =========================================================

def bar(width, value, max_val=1.0, char='=', bg='-'):
    filled = int(width * min(value, max_val) / max_val)
    return '[' + char * filled + bg * (width - filled) + ']'


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# =========================================================
# Demo 1: Objective modules
# =========================================================

def demo_objectives():
    print_section("Demo 1: 4-Dimension Objective Modules")

    modules = {
        'D1-Survival':     SurvivalObjective(),
        'D2-Curiosity':    CuriosityObjective(),
        'D3-Influence':    InfluenceObjective(),
        'D4-Optimization': OptimizationObjective(),
    }

    test_state = {
        'system_health': 0.85,
        'resources_available': 0.70,
        'backup_age_hours': 2,
        'new_patterns_discovered': 3,
        'information_gain': 0.4,
        'pattern_id': 'p_001',
        'changes_accepted': 2,
        'collaboration_score': 0.6,
        'performance_improvement': 0.15,
        'error_rate': 0.05,
    }

    rewards = {}
    print(f"\n  {'Module':<20} {'Reward':>8}   {'Suggested Action'}")
    print(f"  {'-'*56}")
    for name, mod in modules.items():
        r = mod.calculate_reward(test_state, 'explore')
        a = mod.suggest_action()
        rewards[name] = r
        reward_bar = bar(12, r)
        print(f"  {name:<20} {r:>6.4f}  {reward_bar}  {a}")

    return rewards


# =========================================================
# Demo 2: UnifiedMOSSAgent (9-dimension) live steps
# =========================================================

def demo_agent_run(steps=10):
    print_section(f"Demo 2: UnifiedMOSSAgent - {steps} Steps Simulation")

    config = MOSSConfig(
        agent_id="moss_demo_001",
        version="5.2.0",
        log_dir="experiments/minimal_demo",
        checkpoint_interval=9999,   # disable auto-checkpoint
    )

    print(f"\n  Creating UnifiedMOSSAgent: {config.agent_id}  (v{config.version})")
    agent = UnifiedMOSSAgent(config=config)
    n_dims = agent._get_enabled_dimensions()
    print(f"  Enabled dimensions: {n_dims}D")
    print(f"  Initial state: {agent.state.value}")
    print(f"  Initial weights (D1~D4): {np.round(agent.weights, 3)}")

    print(f"\n  Running {steps} steps...\n")
    print(f"  {'Step':>4}  {'Action':<30}  {'Success':>7}  {'Reward':>8}  {'State':<10}")
    print(f"  {'-'*64}")

    results = []
    for i in range(steps):
        # Vary observation to trigger different states
        obs = {}
        if i == 3:
            obs = {'warning': True}
        elif i == 6:
            obs = {'critical': True}

        result = agent.step(observation=obs)
        agent.step_count += 1
        agent.history.append(result)

        success_str = "SUCCESS" if result.success else "FAIL"
        print(f"  {i+1:>4}  {result.action_type:<30}  {success_str:>7}  {result.reward:>8.4f}  {result.state:<10}")
        results.append(result)

    # Summary
    print(f"\n  --- Summary ---")
    print(f"  Total steps : {len(results)}")
    successes = sum(1 for r in results if r.success)
    total_reward = sum(r.reward for r in results)
    print(f"  Success rate: {successes}/{len(results)} ({100*successes/len(results):.0f}%)")
    print(f"  Total reward: {total_reward:.4f}")
    print(f"  Avg reward  : {total_reward/len(results):.4f}")
    print(f"  Final weights (D1~D4): {np.round(agent.weights, 3)}")
    print(f"  Current state: {agent.current_state}")

    return agent, results


# =========================================================
# Demo 3: Weight dynamics under different states
# =========================================================

def demo_weight_dynamics():
    print_section("Demo 3: Weight Dynamics under State Changes")

    config = MOSSConfig(
        agent_id="moss_weight_demo",
        log_dir="experiments/minimal_demo",
        checkpoint_interval=9999,
    )
    agent = UnifiedMOSSAgent(config=config)

    scenarios = [
        ("Normal",   {}),
        ("Warning",  {'warning': True}),
        ("Crisis",   {'critical': True}),
        ("Recovery", {}),
    ]

    print(f"\n  {'Scenario':<12}  {'D1-Surv':>8}  {'D2-Cur':>8}  {'D3-Inf':>8}  {'D4-Opt':>8}  State")
    print(f"  {'-'*62}")

    for scenario_name, obs in scenarios:
        # Step once to apply state
        agent.step(observation=obs)
        w = agent.weights
        print(f"  {scenario_name:<12}  {w[0]:>8.3f}  {w[1]:>8.3f}  {w[2]:>8.3f}  {w[3]:>8.3f}  {agent.current_state}")


# =========================================================
# Main
# =========================================================

def main():
    start = time.time()

    print("\n" + "*" * 60)
    print("*  MOSS v5.2.0 - Minimal Example                       *")
    print("*  Multi-Objective Self-Driven System                  *")
    print("*  Python: " + str(sys.version.split()[0]) + "                                    *")
    print("*" * 60)

    # Demo 1
    rewards = demo_objectives()

    # Demo 2
    agent, results = demo_agent_run(steps=10)

    # Demo 3
    demo_weight_dynamics()

    elapsed = time.time() - start
    print_section("Run Complete")
    print(f"\n  Elapsed time : {elapsed:.2f}s")
    print(f"  Project root : {project_root}")
    print(f"  Log dir      : experiments/minimal_demo/")
    print(f"\n  MOSS v5.2.0 is running correctly.")
    print()


if __name__ == "__main__":
    main()
