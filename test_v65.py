#!/usr/bin/env python3
"""Test v6.5 modules"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing TextWorld v6.5 Modules...")
print("=" * 60)

# Test 1: Enhanced Understanding
print("\n1. Testing EnhancedTextWorldUnderstanding...")
try:
    from agi.textworld_enhanced_understanding import EnhancedTextWorldUnderstanding
    understanding = EnhancedTextWorldUnderstanding()
    
    # Test parsing
    test_obs = """
-= Kitchen =-

A kitchen with various appliances.

You see: apple, knife.

Exits: west.

You are carrying: key.

Your goal is to: Find and take the apple.
"""
    parsed = understanding.parse_observation(test_obs)
    print(f"   ✓ Parsed room: {parsed['room']}")
    print(f"   ✓ Room type: {parsed['room_type']}")
    print(f"   ✓ Exits: {parsed['exits']}")
    print(f"   ✓ Objects: {parsed['objects']}")
    print(f"   ✓ Inventory: {parsed['inventory']}")
    print(f"   ✓ Task: {parsed['task']}")
    
    # Test state vector
    state_vec = understanding.get_state_vector()
    print(f"   ✓ State vector shape: {state_vec.shape}")
    print(f"   ✓ State vector sample: {state_vec[:5]}")
    
    print("   ✓ EnhancedTextWorldUnderstanding: PASSED")
except Exception as e:
    print(f"   ✗ EnhancedTextWorldUnderstanding: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 2: RL Agent
print("\n2. Testing TextWorldRLAgentV65...")
try:
    from agi.textworld_rl_agent_v65 import TextWorldRLAgentV65
    agent = TextWorldRLAgentV65(state_dim=20, action_dim=10, hidden_dim=64)
    print(f"   ✓ Agent created")
    print(f"   ✓ Exploration rate: {agent.exploration_rate}")
    print(f"   ✓ State dim: {agent.state_dim}")
    print(f"   ✓ Action dim: {agent.action_dim}")
    print("   ✓ TextWorldRLAgentV65: PASSED")
except Exception as e:
    print(f"   ✗ TextWorldRLAgentV65: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 3: Training Script Components
print("\n3. Testing Training Script Components...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("train_module", 
        os.path.join(os.path.dirname(__file__), 'examples', 'train_textworld_v6.5.py'))
    train_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(train_module)
    TextWorldAdapter = train_module.TextWorldAdapter
    evaluate = train_module.evaluate
    env = TextWorldAdapter()
    obs, info = env.reset()
    print(f"   ✓ Environment created")
    print(f"   ✓ Initial observation length: {len(obs)}")
    print(f"   ✓ Available actions: {len(info['admissible_commands'])}")
    
    # Test step
    next_obs, reward, done, next_info = env.step("look")
    print(f"   ✓ Step executed, reward: {reward}")
    
    print("   ✓ Training Script Components: PASSED")
except Exception as e:
    print(f"   ✗ Training Script Components: FAILED - {e}")
    import traceback
    traceback.print_exc()

# Test 4: Quick Training Run
print("\n4. Running Quick Training Test...")
try:
    from agi.textworld_rl_agent_v65 import TextWorldRLAgentV65
    
    env = TextWorldAdapter()
    agent = TextWorldRLAgentV65(state_dim=20, action_dim=20, hidden_dim=64, lr=1e-3)
    
    print("   Training 10 episodes...")
    for ep in range(10):
        reward, steps, success, info = agent.train_episode(env, max_steps=50)
        if ep % 5 == 0:
            print(f"     Episode {ep}: reward={reward:.2f}, steps={steps}, success={success}")
    
    stats = agent.get_stats()
    print(f"   ✓ Training complete")
    print(f"   ✓ Episodes: {stats['episodes']}")
    print(f"   ✓ Successes: {stats['successes']}")
    print(f"   ✓ Success rate: {stats['success_rate']:.2%}")
    
    print("   ✓ Quick Training Test: PASSED")
except Exception as e:
    print(f"   ✗ Quick Training Test: FAILED - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("All Tests Complete!")
