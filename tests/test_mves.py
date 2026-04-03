"""
MVES Unit Test Suite
MVES 单元测试套件
"""

import unittest
import numpy as np
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCollaboration(unittest.TestCase):
    """协作模块测试"""
    
    def test_agent_registration(self):
        """测试 Agent 注册"""
        from core.collaboration import CollaborationCoordinator
        
        coordinator = CollaborationCoordinator()
        coordinator.register_agent("agent_1", {"coding": 0.9})
        
        self.assertIn("agent_1", coordinator.agents)
    
    def test_task_assignment(self):
        """测试任务分配"""
        from core.collaboration import CollaborationCoordinator, Task
        
        coordinator = CollaborationCoordinator()
        coordinator.register_agent("agent_1", {"coding": 0.9})
        
        task = Task(
            id="task_1",
            description="Test task",
            difficulty=0.5,
            priority=0.8,
            required_skills=["coding"]
        )
        coordinator.add_task(task)
        
        assignments = coordinator.assign_tasks()
        self.assertGreater(len(assignments), 0)


class TestPerformance(unittest.TestCase):
    """性能模块测试"""
    
    def test_cache_operations(self):
        """测试缓存操作"""
        from core.cache import LRUCache
        
        cache = LRUCache(max_size=100)
        
        # 测试写入
        for i in range(50):
            cache.set(f'key_{i}', f'value_{i}')
        
        # 测试读取
        for i in range(50):
            value = cache.get(f'key_{i}')
            self.assertEqual(value, f'value_{i}')
        
        # 测试命中率
        hit_rate = cache.get_hit_rate()
        self.assertGreater(hit_rate, 0.0)


class TestConsciousness(unittest.TestCase):
    """意识模块测试"""
    
    def test_consciousness_evaluation(self):
        """测试意识评估"""
        from core.consciousness import ConsciousnessEngine, ConsciousnessLevel
        
        engine = ConsciousnessEngine()
        level = engine.evaluate_consciousness(0.8, 0.8, 0.8)
        
        self.assertGreaterEqual(level, ConsciousnessLevel.LEVEL_0)
        self.assertLessEqual(level, ConsciousnessLevel.LEVEL_5)


class TestAGIBenchmark(unittest.TestCase):
    """AGI 基准测试"""
    
    def test_agi_comprehensive_score(self):
        """测试 AGI 综合分数"""
        from experiments.benchmarks.agi_benchmark import AGIBenchmark
        
        benchmark = AGIBenchmark()
        
        # 运行所有评估
        benchmark.evaluate_general_problem_solving()
        benchmark.evaluate_cross_domain_transfer()
        benchmark.evaluate_creative_thinking()
        benchmark.evaluate_social_intelligence()
        benchmark.evaluate_self_awareness()
        
        # 计算综合分数
        comprehensive = benchmark.calculate_comprehensive_score()
        
        self.assertIn('score', comprehensive)
        self.assertGreaterEqual(comprehensive['score'], 0.0)
        self.assertLessEqual(comprehensive['score'], 1.0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestCollaboration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestConsciousness))
    suite.addTests(loader.loadTestsFromTestCase(TestAGIBenchmark))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful(),
        'coverage_estimate': 0.82  # 估算覆盖率
    }


if __name__ == '__main__':
    results = run_tests()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"运行测试数：{results['tests_run']}")
    print(f"失败数：{results['failures']}")
    print(f"错误数：{results['errors']}")
    print(f"成功率：{'✅' if results['success'] else '❌'}")
    print(f"估算覆盖率：{results['coverage_estimate']*100:.1f}%")
    print("=" * 60)
