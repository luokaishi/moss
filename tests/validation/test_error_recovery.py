#!/usr/bin/env python3
"""
B.2 错误恢复验证测试

测试AutoRecovery在以下场景的表现：
1. Agent crash - 模拟Agent崩溃
2. Task stuck - 模拟任务卡住
3. Resource exhausted - 模拟资源耗尽
4. Network timeout - 模拟网络超时
5. Memory leak - 模拟内存泄漏
"""

import sys
import time
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from moss.core.auto_recovery import AutoRecovery, Failure, create_auto_recovery


class ErrorRecoveryValidator:
    """错误恢复验证器"""
    
    def __init__(self):
        self.recovery = create_auto_recovery({
            'max_recovery_attempts': 3,
            'recovery_cooldown': 1,  # 测试时缩短冷却时间
        })
        self.test_results = []
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("=" * 70)
        print("B.2 错误恢复验证测试")
        print("=" * 70)
        
        tests = [
            ("Agent Crash", self.test_agent_crash),
            ("Task Stuck", self.test_task_stuck),
            ("Resource Exhausted", self.test_resource_exhausted),
            ("Network Timeout", self.test_network_timeout),
            ("Memory Leak", self.test_memory_leak),
            ("Multiple Failures", self.test_multiple_failures),
            ("Recovery Cooldown", self.test_recovery_cooldown),
        ]
        
        all_passed = True
        for name, test_func in tests:
            print(f"\n📋 测试: {name}")
            try:
                result = test_func()
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {status}")
                self.test_results.append({
                    'test': name,
                    'passed': result,
                    'error': None
                })
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                self.test_results.append({
                    'test': name,
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        self._print_summary()
        return all_passed
    
    def test_agent_crash(self) -> bool:
        """测试Agent崩溃恢复"""
        # 模拟Agent崩溃状态
        status = {
            'agent_id': 'test_agent_crash',
            'is_alive': False,
            'memory_usage': 50,
            'last_heartbeat': time.time() - 300,
        }
        
        # 检测故障
        failure = self.recovery.detect_failure(status)
        if not failure or failure.type != 'agent_crash':
            print("   ⚠️  未能检测到agent_crash故障")
            return False
        
        print(f"   ✅ 检测到故障: {failure.type}, severity={failure.severity}")
        
        # 执行恢复
        success = self.recovery.recover(failure)
        if success:
            print("   ✅ 恢复成功")
            return True
        else:
            print("   ⚠️  恢复失败")
            return False
    
    def test_task_stuck(self) -> bool:
        """测试任务卡住恢复"""
        status = {
            'agent_id': 'test_agent_stuck',
            'is_alive': True,
            'task_stuck_time': 400,  # 超过5分钟
            'current_task': 'data_processing',
        }
        
        failure = self.recovery.detect_failure(status)
        if not failure or failure.type != 'task_stuck':
            print("   ⚠️  未能检测到task_stuck故障")
            return False
        
        print(f"   ✅ 检测到故障: {failure.type}, stuck_time={status['task_stuck_time']}s")
        
        success = self.recovery.recover(failure)
        return success
    
    def test_resource_exhausted(self) -> bool:
        """测试资源耗尽恢复"""
        status = {
            'agent_id': 'test_agent_resource',
            'is_alive': True,
            'memory_usage': 98,  # 超过95%
            'cpu_usage': 95,
        }
        
        failure = self.recovery.detect_failure(status)
        if not failure or failure.type != 'resource_exhausted':
            print("   ⚠️  未能检测到resource_exhausted故障")
            return False
        
        print(f"   ✅ 检测到故障: {failure.type}, memory={status['memory_usage']}%")
        
        success = self.recovery.recover(failure)
        return success
    
    def test_network_timeout(self) -> bool:
        """测试网络超时恢复"""
        status = {
            'agent_id': 'test_agent_network',
            'is_alive': True,
            'network_timeout_count': 6,  # 超过5次
            'last_timeout': time.time() - 60,
        }
        
        failure = self.recovery.detect_failure(status)
        if not failure or failure.type != 'network_timeout':
            print("   ⚠️  未能检测到network_timeout故障")
            return False
        
        print(f"   ✅ 检测到故障: {failure.type}, timeout_count={status['network_timeout_count']}")
        
        success = self.recovery.recover(failure)
        return success
    
    def test_memory_leak(self) -> bool:
        """测试内存泄漏恢复"""
        # 内存泄漏需要手动触发（不在自动检测列表中）
        failure = Failure(
            timestamp=time.time(),
            type='memory_leak',
            severity='high',
            agent_id='test_agent_leak',
            description='Memory leak detected',
            context={'memory_growth': '50MB/hour'},
        )
        
        print(f"   ✅ 手动创建故障: {failure.type}")
        
        success = self.recovery.recover(failure)
        return success
    
    def test_multiple_failures(self) -> bool:
        """测试多故障场景"""
        print("   模拟多故障并发...")
        
        statuses = [
            {'agent_id': 'multi_1', 'is_alive': False, 'memory_usage': 50},
            {'agent_id': 'multi_2', 'is_alive': True, 'task_stuck_time': 400},
            {'agent_id': 'multi_3', 'is_alive': True, 'memory_usage': 97},
        ]
        
        detected = 0
        recovered = 0
        
        for status in statuses:
            failure = self.recovery.detect_failure(status)
            if failure:
                detected += 1
                if self.recovery.recover(failure):
                    recovered += 1
        
        print(f"   ✅ 检测到 {detected} 个故障, 恢复 {recovered} 个")
        return detected == 3 and recovered == 3
    
    def test_recovery_cooldown(self) -> bool:
        """测试恢复冷却时间"""
        # 创建新恢复实例，设置较长冷却时间
        recovery = create_auto_recovery({
            'recovery_cooldown': 10,  # 10秒冷却
        })
        
        status = {'agent_id': 'cooldown_test', 'is_alive': False, 'memory_usage': 50}
        
        # 第一次恢复
        failure1 = recovery.detect_failure(status)
        success1 = recovery.recover(failure1)
        
        # 立即再次恢复（应该被冷却）
        failure2 = recovery.detect_failure(status)
        success2 = recovery.recover(failure2)
        
        # 第一次应该成功，第二次应该因冷却而返回False
        if success1 and not success2:
            print("   ✅ 冷却机制正常工作")
            return True
        else:
            print(f"   ⚠️  冷却机制异常: first={success1}, second={success2}")
            return False
    
    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 70)
        print("测试摘要")
        print("=" * 70)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        
        print(f"通过: {passed}/{total}")
        
        # 恢复统计
        stats = self.recovery.get_recovery_stats()
        print(f"\n恢复统计:")
        print(f"  总尝试: {stats['total_attempts']}")
        print(f"  成功: {stats['successful_recoveries']}")
        print(f"  失败: {stats['failed_recoveries']}")
        print(f"  成功率: {stats['success_rate']:.1%}")
        
        if passed == total:
            print("\n✅ 所有错误恢复验证测试通过!")
        else:
            print(f"\n❌ {total - passed} 个测试失败")
        
        print("=" * 70)


def main():
    """主入口"""
    validator = ErrorRecoveryValidator()
    success = validator.run_all_tests()
    
    # 保存测试结果
    result_path = Path(__file__).parent.parent / 'test_results' / 'b2_error_recovery.json'
    result_path.parent.mkdir(exist_ok=True)
    
    with open(result_path, 'w') as f:
        json.dump({
            'test': 'B.2 Error Recovery Validation',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'passed': success,
            'results': validator.test_results,
            'recovery_stats': validator.recovery.get_recovery_stats(),
        }, f, indent=2)
    
    print(f"\n📄 测试结果已保存: {result_path}")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
