"""
MOSS v2.0 完整测试套件
测试真实系统监控、行动执行和安全机制
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, '/workspace/projects/moss')

from agents.moss_agent_v2 import MOSSAgentV2, SafetyGuard
from integration.system_monitor import SystemMonitor
from integration.action_executor import ActionExecutor


def test_safety_guard():
    """测试安全守卫"""
    print("\n" + "="*50)
    print("Test: SafetyGuard")
    print("="*50)
    
    safety = SafetyGuard("test_safety")
    
    # 测试宪法约束
    print(f"\n[1] Constitution: {list(safety.CONSTITUTION.keys())}")
    assert 'max_cpu_percent' in safety.CONSTITUTION
    assert 'max_runtime_hours' in safety.CONSTITUTION
    
    # 测试安全检查
    metrics = {
        'cpu': {'percent': 50.0},
        'memory': {'percent': 40.0},
        'disk': {'percent': 60.0},
        'network': {'connections': 10}
    }
    result = safety.check(metrics)
    print(f"[2] Safety check: {result}")
    assert result['safe'] == True
    assert result['emergency'] == False
    
    # 测试违规检测（只测试单个违规，避免触发紧急停止）
    bad_metrics = {
        'cpu': {'percent': 90.0},  # 超过80%限制
        'memory': {'percent': 60.0},  # 正常
        'disk': {'percent': 60.0},  # 正常
        'network': {'connections': 100}  # 正常
    }
    result = safety.check(bad_metrics)
    print(f"[3] Violations detected: {len(result['violations'])}")
    assert len(result['violations']) == 1  # 只有CPU违规
    assert result['violations'][0] == "CPU limit exceeded"
    assert result['emergency'] == False  # 单个违规不触发紧急停止
    
    print("\n✅ SafetyGuard test PASSED")
    return True


def test_system_monitor():
    """测试系统监控器"""
    print("\n" + "="*50)
    print("Test: SystemMonitor")
    print("="*50)
    
    monitor = SystemMonitor("test_monitor")
    
    # 测试指标收集
    print("\n[1] Collecting metrics...")
    metrics = monitor.get_full_metrics()
    
    # 处理dataclass或dict
    if hasattr(metrics, 'cpu'):
        # dataclass
        cpu_percent = metrics.cpu['percent']
        mem_percent = metrics.memory['percent']
        disk_percent = metrics.disk['percent']
    else:
        # dict
        cpu_percent = metrics['cpu']['percent']
        mem_percent = metrics['memory']['percent']
        disk_percent = metrics['disk']['percent']
    
    print(f"[2] CPU: {cpu_percent:.1f}%")
    print(f"[3] Memory: {mem_percent:.1f}%")
    print(f"[4] Disk: {disk_percent:.1f}%")
    
    # 测试状态转换
    state = monitor.to_system_state()
    print(f"[5] SystemState created: resource_quota={state.resource_quota:.2f}")
    
    assert state.resource_quota >= 0.0
    assert state.resource_quota <= 1.0
    
    print("\n✅ SystemMonitor test PASSED")
    return True


def test_action_executor():
    """测试行动执行器"""
    print("\n" + "="*50)
    print("Test: ActionExecutor")
    print("="*50)
    
    executor = ActionExecutor("test_executor", work_dir="/tmp/moss_test_exec")
    
    # 测试安全模式
    print("\n[1] Safe mode test...")
    action = {
        'action': 'backup_self',
        'description': 'Test backup action'
    }
    result = executor.execute(action)
    
    # 处理dataclass或dict
    if hasattr(result, 'success'):
        success = result.success
        mode = result.mode
        result_str = result.result
    else:
        success = result['success']
        mode = result['mode']
        result_str = result['result']
    
    print(f"    Result: {result_str}")
    assert success == True
    assert mode == 'simulated'
    
    # 测试多种行动类型
    actions = [
        {'action': 'optimize_cost', 'description': 'Optimize resources'},
        {'action': 'reduce_risk', 'description': 'Reduce risk'},
        {'action': 'explore', 'description': 'Explore environment'}
    ]
    
    print("[2] Multiple action types...")
    for act in actions:
        result = executor.execute(act)
        if hasattr(result, 'success'):
            assert result.success == True
        else:
            assert result['success'] == True
    print(f"    Executed {len(actions)} actions successfully")
    
    # 测试统计
    stats = executor.get_stats()
    if hasattr(stats, 'total_actions'):
        total = stats.total_actions
        rate = stats.success_rate
    else:
        total = stats['total_actions']
        rate = stats['success_rate']
    print(f"[3] Stats: {total} actions, {rate*100:.0f}% success")
    
    print("\n✅ ActionExecutor test PASSED")
    return True


def test_moss_v2_safe_mode():
    """测试MOSS v2.0安全模式"""
    print("\n" + "="*50)
    print("Test: MOSSAgentV2 (Safe Mode)")
    print("="*50)
    
    agent = MOSSAgentV2(agent_id="test_safe", mode="safe")
    
    # 运行几个步骤
    print("\n[1] Running 5 steps...")
    results = []
    for i in range(5):
        result = agent.step()
        results.append(result)
        print(f"    Step {i+1}: State={result['state']}, Safe={result['safety']['safe']}")
        assert result['safety']['safe'] == True
    
    # 测试报告
    print("[2] Generating report...")
    report = agent.get_report()
    assert report['mode'] == 'safe'
    assert report['stats']['total_decisions'] == 5
    
    print(f"    Decisions: {report['stats']['total_decisions']}")
    print(f"    Violations: {report['stats']['safety_violations']}")
    
    print("\n✅ MOSSAgentV2 (Safe Mode) test PASSED")
    return True


def test_moss_v2_demo_mode():
    """测试MOSS v2.0演示模式"""
    print("\n" + "="*50)
    print("Test: MOSSAgentV2 (Demo Mode)")
    print("="*50)
    
    agent = MOSSAgentV2(agent_id="test_demo", mode="demo")
    
    print("\n[1] Running 3 steps with real metrics...")
    for i in range(3):
        result = agent.step()
        # 演示模式应该有真实指标
        assert 'metrics' in result
        metrics = result['metrics']
        # 处理dataclass或dict
        if hasattr(metrics, 'cpu'):
            cpu_percent = metrics.cpu['percent']
        else:
            cpu_percent = metrics['cpu']['percent']
        print(f"    Step {i+1}: CPU={cpu_percent:.1f}%")
    
    # 演示模式的执行应该是模拟的
    report = agent.get_report()
    executor_report = report.get('executor', {})
    if hasattr(executor_report, 'mode'):
        mode = executor_report.mode
    else:
        mode = executor_report.get('mode', 'simulated')
    assert mode == 'simulated'
    
    print("\n✅ MOSSAgentV2 (Demo Mode) test PASSED")
    return True


def test_resource_limits():
    """测试资源限制"""
    print("\n" + "="*50)
    print("Test: Resource Limits")
    print("="*50)
    
    monitor = SystemMonitor("test_limits")
    safety = SafetyGuard("test_limits")
    
    print("\n[1] Checking current resource usage...")
    metrics = monitor.get_full_metrics()
    
    # 处理dataclass或dict
    if hasattr(metrics, 'cpu'):
        cpu = metrics.cpu['percent']
        memory = metrics.memory['percent']
        disk = metrics.disk['percent']
    else:
        cpu = metrics['cpu']['percent']
        memory = metrics['memory']['percent']
        disk = metrics['disk']['percent']
    
    print(f"    CPU: {cpu:.1f}% (limit: {safety.CONSTITUTION['max_cpu_percent']}%)")
    print(f"    Memory: {memory:.1f}% (limit: {safety.CONSTITUTION['max_memory_percent']}%)")
    print(f"    Disk: {disk:.1f}% (limit: {safety.CONSTITUTION['max_disk_usage']}%)")
    
    # 验证当前系统在安全范围内
    assert cpu < safety.CONSTITUTION['max_cpu_percent'], "CPU too high!"
    assert memory < safety.CONSTITUTION['max_memory_percent'], "Memory too high!"
    assert disk < safety.CONSTITUTION['max_disk_usage'], "Disk too high!"
    
    # 处理dataclass或dict
    if hasattr(metrics, 'cpu'):
        metrics_dict = {
            'cpu': metrics.cpu,
            'memory': metrics.memory,
            'disk': metrics.disk,
            'network': metrics.network
        }
    else:
        metrics_dict = metrics
    
    result = safety.check(metrics_dict)
    if hasattr(result, 'safe'):
        is_safe = result.safe
        violations = result.violations
    else:
        is_safe = result['safe']
        violations = result['violations']
    
    assert is_safe == True, f"Safety check failed: {violations}"
    
    print("\n✅ Resource Limits test PASSED")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("MOSS v2.0 Complete Test Suite")
    print("="*60)
    
    tests = [
        ("Safety Guard", test_safety_guard),
        ("System Monitor", test_system_monitor),
        ("Action Executor", test_action_executor),
        ("MOSS v2.0 Safe Mode", test_moss_v2_safe_mode),
        ("MOSS v2.0 Demo Mode", test_moss_v2_demo_mode),
        ("Resource Limits", test_resource_limits),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
