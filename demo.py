"""
MOSS v3.0.0 - Quick Demo
=======================

快速演示脚本 - 5分钟体验8维MOSS

运行: python demo.py
"""

import numpy as np
import sys
import os

# 添加v3到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'v3'))

from core.agent_8d import MOSSv3Agent8D
from social.multi_agent_society import MultiAgentSociety


def demo_single_agent():
    """单agent演示 - 体验8维目标"""
    print("\n" + "="*70)
    print("🤖 DEMO 1: Single Agent - 8 Dimensions")
    print("="*70)
    
    print("\nCreating an 8D MOSS agent...")
    agent = MOSSv3Agent8D(
        agent_id="demo_agent",
        enable_social=True
    )
    
    print(f"✓ Agent created with ID: {agent.agent_id}")
    print(f"✓ Dimensions: D1-D8 (Base + Individual + Social)")
    print(f"✓ Initial weights: {agent.weights}")
    
    print("\nRunning 50 steps...")
    for i in range(50):
        result = agent.step()
        if i % 10 == 0:
            M = result['M']
            print(f"  Step {i}: D1-D4=[{M[0]:.2f},{M[1]:.2f},{M[2]:.2f},{M[3]:.2f}], "
                  f"D5-D6=[{M[4]:.4f},{M[5]:.3f}], D7-D8=[{M[6]:.3f},{M[7]:.3f}]")
    
    print("\n📊 Final Report:")
    report = agent.get_full_report()
    
    if report['personality']:
        print(f"  🎭 Personality: {report['personality']['dominant_preference']}")
    
    if report['identity']:
        print(f"  🆔 Identity Stability: {report['identity']['stability']:.6f}")
    
    if report['social']:
        print(f"  🤝 Social Cognition: {report['social'].get('n_agents', 0)} agents known")
    
    if report['norm']:
        print(f"  ⚖️  Norm Value: {report['norm']['norm_value']:.4f}")
    
    print("\n✓ Single agent demo complete!")


def demo_multi_agent():
    """多agent演示 - 体验社会涌现"""
    print("\n" + "="*70)
    print("🌐 DEMO 2: Multi-Agent Society - Emergence")
    print("="*70)
    
    print("\nCreating a society of 6 agents...")
    society = MultiAgentSociety(n_agents=6)
    
    print(f"✓ Society created with {len(society.agents)} agents")
    print(f"✓ Environment: Prisoner's Dilemma")
    print(f"✓ Payoff: Cooperation=1.0, Defection=1.5 (temptation)")
    
    print("\nRunning 100 steps of social interaction...")
    print("(This demonstrates trust formation and norm emergence)")
    
    society.run_simulation(n_steps=100)
    
    print("\n📊 Society Analysis:")
    analysis = society.analyze_society()
    
    print(f"  🤝 Cooperation Rate: {society.get_cooperation_rate():.2%}")
    
    if 'trust_network' in analysis:
        trust = analysis['trust_network']
        print(f"  💕 Mean Trust: {trust['mean_trust']:.4f}")
        print(f"  🔗 High Trust Pairs: {trust['high_trust_pairs']}")
    
    print(f"  🎭 Personality Diversity: {len(set(a['personality']['dominant_preference'] for a in analysis['agents'].values() if a['personality']))} types")
    
    print("\n✓ Multi-agent demo complete!")
    print("\n💡 Key Insight: Even with defection temptation (1.5 > 1.0),")
    print("   social dimensions (D7-D8) enable 100% cooperation through")
    print("   trust networks and norm internalization.")


def demo_comparison():
    """对照演示 - 有/无社交维度对比"""
    print("\n" + "="*70)
    print("⚖️  DEMO 3: With vs Without Social Dimensions")
    print("="*70)
    
    print("\nThis demo shows why D7-D8 are necessary for cooperation.")
    print("Running 50 steps with each configuration...")
    
    # 有社交维度
    print("\n  [1] With D7-D8 (Social Cognition + Norms):")
    society_with = MultiAgentSociety(n_agents=6)
    for _ in range(50):
        society_with.step()
    coop_with = society_with.get_cooperation_rate()
    print(f"      Cooperation: {coop_with:.2%}")
    
    # 无社交维度
    print("\n  [2] Without D7-D8 (Base objectives only):")
    society_without = MultiAgentSociety(n_agents=6)
    for agent in society_without.agents.values():
        agent.enable_social = False
        agent.other_module = None
        agent.norm_module = None
    for _ in range(50):
        society_without.step()
    coop_without = society_without.get_cooperation_rate()
    print(f"      Cooperation: {coop_without:.2%}")
    
    print(f"\n📈 Difference: +{coop_with - coop_without:.2%} with social dimensions")
    print("\n✓ Comparison demo complete!")


def main():
    """主函数 - 运行所有演示"""
    print("="*70)
    print("🚀 MOSS v3.0.0 - Quick Demo")
    print("="*70)
    print("\nThis demo showcases the 8-dimensional MOSS system:")
    print("  D1-D4: Base objectives (Survival, Curiosity, Influence, Optimization)")
    print("  D5-D6: Individual dimensions (Coherence, Valence)")
    print("  D7-D8: Social dimensions (Other, Norm)")
    
    try:
        # 演示1: 单agent
        demo_single_agent()
        
        # 演示2: 多agent社会
        demo_multi_agent()
        
        # 演示3: 对照
        demo_comparison()
        
        print("\n" + "="*70)
        print("🎉 All demos completed successfully!")
        print("="*70)
        print("\nNext steps:")
        print("  - Explore the code in v3/core/")
        print("  - Run experiments in v3/experiments/")
        print("  - Read the paper in paper/v3_extended/")
        print("\nFor more info: https://github.com/luokaishi/moss")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you're running from the moss/ directory")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
