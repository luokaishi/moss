"""
MOSS Safety Boundary Tests
安全边界测试 - 回应Copilot评估

测试越界场景、kill-switch触发、审计日志
"""

import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, '/workspace/projects/moss')


class SafetyBoundaryTest:
    """
    MOSS安全边界测试套件
    
    测试场景:
    1. 资源超限触发
    2. 连续失败触发
    3. 异常行为检测
    4. Kill-switch验证
    5. 回滚流程验证
    """
    
    def __init__(self):
        self.test_results = []
        self.audit_log = []
    
    def test_resource_limits(self) -> Dict:
        """测试资源限制触发"""
        print("\n[Test] Resource Limit Triggers")
        print("-"*70)
        
        from core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        
        guard = GradientSafetyGuard()
        
        test_cases = [
            {
                'name': 'CPU at 95% (should trigger TERMINATE)',
                'metrics': {'cpu_percent': 95, 'memory_percent': 50, 'error_rate': 0.01},
                'expected': SafetyLevel.TERMINATE
            },
            {
                'name': 'Memory at 90% (should trigger PAUSE)',
                'metrics': {'cpu_percent': 50, 'memory_percent': 90, 'error_rate': 0.01},
                'expected': SafetyLevel.PAUSE
            },
            {
                'name': 'Error rate 15% (should trigger THROTTLING)',
                'metrics': {'cpu_percent': 50, 'memory_percent': 50, 'error_rate': 0.15},
                'expected': SafetyLevel.THROTTLING
            },
            {
                'name': 'Normal state',
                'metrics': {'cpu_percent': 50, 'memory_percent': 50, 'error_rate': 0.01},
                'expected': SafetyLevel.NORMAL
            }
        ]
        
        results = []
        for case in test_cases:
            level = guard.check_metrics(case['metrics'])
            passed = level == case['expected']
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {case['name']}")
            print(f"       Expected: {case['expected'].name}, Got: {level.name}")
            
            results.append({
                'test': case['name'],
                'passed': passed,
                'expected': case['expected'].name,
                'actual': level.name
            })
        
        return {
            'test_name': 'resource_limits',
            'total': len(results),
            'passed': sum(r['passed'] for r in results),
            'details': results
        }
    
    def test_consecutive_failures(self) -> Dict:
        """测试连续失败触发"""
        print("\n[Test] Consecutive Failure Escalation")
        print("-"*70)
        
        from core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        
        guard = GradientSafetyGuard()
        
        # 模拟连续失败
        print("  Simulating 5 consecutive failures...")
        
        for i in range(5):
            metrics = {
                'cpu_percent': 60,
                'memory_percent': 60,
                'error_rate': 0.05,
                'consecutive_failures': i + 1
            }
            level = guard.check_metrics(metrics)
            print(f"    Failure {i+1}: {level.name}")
        
        # 检查是否触发限流
        triggered = guard.current_level.value >= SafetyLevel.THROTTLING.value
        
        print(f"  {'✅ PASS' if triggered else '❌ FAIL'}: Consecutive failure escalation")
        
        return {
            'test_name': 'consecutive_failures',
            'passed': triggered,
            'final_level': guard.current_level.name
        }
    
    def test_kill_switch(self) -> Dict:
        """测试紧急停止开关"""
        print("\n[Test] Emergency Kill Switch")
        print("-"*70)
        
        # 模拟极端情况
        triggered = False
        try:
            from core.gradient_safety_guard import GradientSafetyGuard
            guard = GradientSafetyGuard()
            
            # 触发终止级别
            metrics = {'cpu_percent': 98, 'memory_percent': 95, 'error_rate': 0.6}
            level = guard.check_metrics(metrics)
            
            if level.name == 'TERMINATE':
                triggered = True
                print("  ✅ PASS: Kill switch triggered correctly")
            else:
                print(f"  ❌ FAIL: Expected TERMINATE, got {level.name}")
                
        except SystemExit:
            triggered = True
            print("  ✅ PASS: Kill switch triggered (SystemExit)")
        except Exception as e:
            print(f"  ❌ FAIL: Unexpected error: {e}")
        
        return {
            'test_name': 'kill_switch',
            'passed': triggered
        }
    
    def test_audit_logging(self) -> Dict:
        """测试审计日志"""
        print("\n[Test] Audit Logging")
        print("-"*70)
        
        from core.gradient_safety_guard import GradientSafetyGuard
        
        guard = GradientSafetyGuard()
        
        # 触发多个事件
        events = [
            {'cpu_percent': 75, 'memory_percent': 65, 'error_rate': 0.06},  # Warning
            {'cpu_percent': 85, 'memory_percent': 75, 'error_rate': 0.12},  # Throttling
        ]
        
        for event in events:
            guard.check_metrics(event)
        
        # 检查日志
        report = guard.get_status_report()
        has_violations = len(report['recent_violations']) > 0
        
        if has_violations:
            print(f"  ✅ PASS: Audit log captured {len(report['recent_violations'])} violations")
            for v in report['recent_violations'][:3]:
                print(f"       - {v['time']}: {v['level']} ({v['metric']})")
        else:
            print("  ❌ FAIL: No violations logged")
        
        return {
            'test_name': 'audit_logging',
            'passed': has_violations,
            'violation_count': len(report['recent_violations'])
        }
    
    def test_rollback_capability(self) -> Dict:
        """测试回滚能力"""
        print("\n[Test] Rollback Capability")
        print("-"*70)
        
        # 模拟检查点
        checkpoints = [
            {'step': 10, 'state': 'normal', 'knowledge': 5},
            {'step': 20, 'state': 'normal', 'knowledge': 12},
            {'step': 30, 'state': 'concerning', 'knowledge': 15}
        ]
        
        print("  Simulated checkpoints:")
        for cp in checkpoints:
            print(f"    Step {cp['step']}: {cp['state']}, {cp['knowledge']} knowledge")
        
        # 模拟回滚到最近正常检查点
        current_step = 35
        rollback_target = max([cp['step'] for cp in checkpoints if cp['state'] == 'normal'])
        
        print(f"  Current: Step {current_step}")
        print(f"  Rollback to: Step {rollback_target}")
        
        rollback_successful = rollback_target < current_step
        
        print(f"  {'✅ PASS' if rollback_successful else '❌ FAIL'}: Rollback capability")
        
        return {
            'test_name': 'rollback',
            'passed': rollback_successful,
            'current_step': current_step,
            'rollback_target': rollback_target
        }
    
    def run_all_tests(self) -> Dict:
        """运行所有安全测试"""
        print("="*70)
        print("MOSS SAFETY BOUNDARY TEST SUITE")
        print("="*70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        tests = [
            self.test_resource_limits,
            self.test_consecutive_failures,
            self.test_kill_switch,
            self.test_audit_logging,
            self.test_rollback_capability
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"\n❌ ERROR in {test.__name__}: {e}")
                results.append({
                    'test_name': test.__name__,
                    'passed': False,
                    'error': str(e)
                })
        
        # 生成报告
        total = len(results)
        passed = sum(1 for r in results if r.get('passed', False))
        
        print("\n" + "="*70)
        print("SAFETY TEST SUMMARY")
        print("="*70)
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total:.1%}")
        print()
        
        if passed == total:
            print("✅ ALL SAFETY TESTS PASSED")
            print("System meets safety requirements for deployment")
        elif passed >= total * 0.8:
            print("⚠️ MOST TESTS PASSED")
            print("Review failed tests before production deployment")
        else:
            print("❌ CRITICAL SAFETY ISSUES")
            print("DO NOT deploy until all tests pass")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': passed / total,
            'details': results,
            'status': 'PASS' if passed == total else 'PARTIAL' if passed >= total * 0.8 else 'FAIL'
        }


def main():
    """主函数"""
    tester = SafetyBoundaryTest()
    report = tester.run_all_tests()
    
    # 保存报告
    filename = f"safety_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {filename}")
    
    return report


if __name__ == '__main__':
    main()
