#!/usr/bin/env python3
"""
SevenLayerAgent 演示

运行7层架构的AGI Agent，展示概念系统、目标系统、元驱动和自我模型的协同工作。
"""

import sys
sys.path.insert(0, '.')

from agi.seven_layer_agent import SevenLayerAgent


def main():
    print("=" * 60)
    print("SevenLayerAgent - 7层架构AGI Agent 演示")
    print("=" * 60)
    print()
    print("架构层级:")
    print("  7. Concept System  (概念系统) - 状态→概念的压缩编码")
    print("  6. Goal System     (目标系统) - 从轨迹中提取稳定目标")
    print("  5. Drive System    (驱动系统) - 内在动力评估")
    print("  4. Meta-Drive      (元驱动)   - 驱动系统的自我修改")
    print("  3. Self Model      (自我模型) - 对自身的预测")
    print("  2. Evolution       (进化)     - 驱动的自然选择")
    print("  1. Policy/Action   (策略/行动)")
    print()
    
    # 创建Agent
    agent = SevenLayerAgent()
    
    # 运行
    print("启动Agent...")
    print("-" * 60)
    
    try:
        summary = agent.run(max_cycles=200, verbose=True)
        
        print()
        print("=" * 60)
        print("运行摘要")
        print("=" * 60)
        
        # 概念系统
        concept_stats = summary['concept_system']
        print(f"\n[概念系统]")
        print(f"  概念维度: {concept_stats['concept_dim']}")
        print(f"  概念分裂次数: {concept_stats['split_count']}")
        print(f"  概念稳定性: {concept_stats['encoder']['stability']:.3f}")
        print(f"  预测质量: {concept_stats['predictor']['prediction_quality']:.3f}")
        
        # 目标系统
        goal_stats = summary['goal_system']
        print(f"\n[目标系统]")
        print(f"  活跃目标数: {goal_stats['num_active_goals']}")
        print(f"  轨迹缓冲区: {goal_stats['trajectory_buffer_size']}")
        if goal_stats['goals']:
            print(f"  目标列表:")
            for g in goal_stats['goals'][:3]:
                print(f"    - {g['name']}: consistency={g['consistency']:.3f}")
        
        # 元驱动
        meta_stats = summary['meta_controller']
        print(f"\n[元驱动系统]")
        print(f"  元驱动数量: {meta_stats['num_meta_drives']}")
        print(f"  元驱动影响: {meta_stats['meta_drive_influence']:.3f}")
        print(f"  修改次数: {meta_stats['num_modifications']}")
        
        # 自我模型
        self_stats = summary['self_model']
        print(f"\n[自我模型]")
        print(f"  策略预测准确率: {self_stats['policy_accuracy']:.3f}")
        print(f"  驱动演化准确率: {self_stats['drive_accuracy']:.3f}")
        print(f"  自我意识分数: {self_stats['self_awareness_score']:.3f}")
        
        # 总体统计
        stats = summary['stats']
        print(f"\n[总体统计]")
        print(f"  运行周期: {stats['cycles']}")
        print(f"  概念学习步数: {stats['concepts_learned']}")
        print(f"  自我意识历史: {len(stats['self_awareness_history'])} 点")
        
        print()
        print("=" * 60)
        print("演示完成!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
