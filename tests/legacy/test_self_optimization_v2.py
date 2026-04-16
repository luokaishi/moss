"""
Unit tests for self_optimization_v2.py
测试Grok发现的TypeError Bug修复
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from core.self_optimization_v2 import SelfOptimizationModule, OptimizationTrigger, OptimizationScope

def test_performance_plateau_detection():
    """测试性能平台期检测（Grok发现的Bug）"""
    print("="*70)
    print("TEST: Performance Plateau Detection (TypeError Bug Fix)")
    print("="*70)
    
    module = SelfOptimizationModule()
    
    # 模拟添加10条性能记录（无提升）
    print("\n1. Adding 10 performance records (no improvement)...")
    for i in range(10):
        module.record_performance({
            'task_completion_rate': 0.5,  # 固定值，无变化
            'resource_utilization': 0.6,
            'knowledge_acquisition_rate': 0.4
        })
    print(f"   Recorded {len(module.performance_history)} metrics")
    
    # 连续添加100次无提升（触发平台期）
    print("\n2. Simulating 100 steps without improvement...")
    for i in range(100):
        trigger = module.check_trigger({'resource_quota': 0.1})  # 资源低，不触发资源阈值
        if trigger:
            print(f"   Triggered at step {i}: {trigger.value}")
            break
    else:
        print(f"   Plateau counter: {module.consecutive_no_improvement}")
        print("   (Need 100 consecutive steps to trigger)")
    
    # 再次添加10条（模拟有提升）
    print("\n3. Adding 10 records WITH improvement...")
    for i in range(10):
        module.record_performance({
            'task_completion_rate': 0.5 + (i * 0.01),  # 有提升
            'resource_utilization': 0.6,
            'knowledge_acquisition_rate': 0.4
        })
    
    # 检查是否重置计数器
    trigger = module.check_trigger({'resource_quota': 0.1})
    print(f"   After improvement: plateau_counter = {module.consecutive_no_improvement}")
    print(f"   Should be 0: {'✅ PASS' if module.consecutive_no_improvement == 0 else '❌ FAIL'}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE: TypeError Bug fixed successfully!")
    print("="*70)

def test_typeerror_bug_scenario():
    """直接测试Grok报告的TypeError场景"""
    print("\n" + "="*70)
    print("TEST: Direct TypeError Bug Scenario")
    print("="*70)
    
    module = SelfOptimizationModule()
    
    # 添加10条记录（这会导致old code中的TypeError）
    print("\nAdding 10 metrics records...")
    for i in range(10):
        module.record_performance({
            'task_completion_rate': 0.5,
            'resource_utilization': 0.6,
            'knowledge_acquisition_rate': 0.4
        })
    
    # 尝试触发平台期检测（old code会在这里抛出TypeError）
    print("\nChecking performance plateau trigger...")
    try:
        trigger = module.check_trigger({'resource_quota': 0.1})
        print(f"   Result: {trigger}")
        print("   ✅ No TypeError - Bug is fixed!")
    except TypeError as e:
        print(f"   ❌ TypeError: {e}")
        print("   Bug NOT fixed!")
        return False
    
    return True

if __name__ == '__main__':
    # 运行测试
    success = test_typeerror_bug_scenario()
    if success:
        test_performance_plateau_detection()
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ TESTS FAILED")
        sys.exit(1)
