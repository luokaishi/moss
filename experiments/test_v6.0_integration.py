#!/usr/bin/env python3
"""
MOSS v6.0 - Full System Integration Test
v6.0 完整系统集成测试

测试所有 v6.0 模块的协同工作:
- 开放环境交互
- 自我意识
- 元认知
- 自我反思
- AGI 评估

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.open_environment import OpenEnvironment
from core.self_awareness import SelfAwareness
from core.meta_cognition import MetaCognition
from core.self_reflection import SelfReflection
from evaluation.agi_metrics import AGIEvaluator


class V60IntegrationTest:
    """v6.0 集成测试管理器"""
    
    def __init__(self):
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        # 初始化所有模块
        print("🔧 初始化 v6.0 模块...")
        self.env = OpenEnvironment("./test_v6_workspace")
        self.awareness = SelfAwareness()
        self.meta_cognition = MetaCognition()
        self.reflection = SelfReflection()
        self.agi_evaluator = AGIEvaluator()
        
        print("   ✅ 开放环境")
        print("   ✅ 自我意识")
        print("   ✅ 元认知")
        print("   ✅ 自我反思")
        print("   ✅ AGI 评估")
    
    def run_test(self, name: str, test_func) -> bool:
        """运行单个测试"""
        self.results['tests_run'] += 1
        print(f"\n🧪 测试：{name}")
        
        try:
            result = test_func()
            if result:
                self.results['tests_passed'] += 1
                print(f"   ✅ 通过")
                self.results['details'].append({'name': name, 'status': 'passed'})
                return True
            else:
                self.results['tests_failed'] += 1
                print(f"   ❌ 失败")
                self.results['details'].append({'name': name, 'status': 'failed', 'reason': 'Test returned False'})
                return False
        except Exception as e:
            self.results['tests_failed'] += 1
            print(f"   ❌ 异常：{e}")
            self.results['details'].append({'name': name, 'status': 'failed', 'reason': str(e)})
            return False
    
    def test_open_environment(self) -> bool:
        """测试开放环境"""
        # 感知环境
        state = self.env.perceive()
        
        # 执行动作
        success, _ = self.env.execute_action('fs_write', path='test.txt', content='test')
        
        return success and state is not None
    
    def test_self_awareness(self) -> bool:
        """测试自我意识"""
        # 观察能力
        self.awareness.observe_capability('problem_solving', 0.8)
        self.awareness.observe_capability('learning', 0.9)
        
        # 观察局限
        self.awareness.observe_limitation('memory', 0.3)
        
        # 设置目标
        self.awareness.set_goal({
            'description': 'Improve skills',
            'required_capabilities': ['problem_solving', 'learning']
        })
        
        # 镜像测试
        passed, confidence = self.awareness.mirror_test()
        
        return passed and confidence >= 0.7
    
    def test_meta_cognition(self) -> bool:
        """测试元认知"""
        # 监控思考
        self.meta_cognition.monitor_thinking("Solving problem", 0.8, outcome=0.9)
        
        # 监控学习
        self.meta_cognition.monitor_learning("Python", 0.7, 0.5)
        
        # 监控决策
        self.meta_cognition.monitor_decision("Choose A", ["A", "B"], outcome=0.8)
        
        # 评估
        overall, _ = self.meta_cognition.evaluate_meta_cognition()
        
        return overall >= 0.6
    
    def test_self_reflection(self) -> bool:
        """测试自我反思"""
        # 反思错误
        self.reflection.reflect_on_error("Failed task", {}, outcome=0.3)
        
        # 反思成功
        self.reflection.reflect_on_success("Completed task", {}, outcome=0.9)
        
        # 获取摘要
        summary = self.reflection.get_reflection_summary()
        
        return summary.get('avg_depth', 0) >= 3.0
    
    def test_agi_evaluation(self) -> bool:
        """测试 AGI 评估"""
        system_data = {
            'components': [{'id': i} for i in range(10)],
            'connections': [(0, 1), (1, 2)],
            'hierarchy': {'id': 'root'}
        }
        
        behavior_data = {
            'actions': ['explore', 'exploit'],
            'strategies': ['strategy_1']
        }
        
        generation_data = [
            {'traits': ['A', 'B'], 'values': {'cooperation': 0.7}},
            {'traits': ['A', 'C'], 'values': {'cooperation': 0.75}}
        ]
        
        env_data = {
            'before': {'resource': 100},
            'after': {'resource': 90},
            'resources_used': 10,
            'resources_available': 100,
            'niche_construction': 0.5
        }
        
        drive_data = {
            'drives': {'survival': 0.3, 'curiosity': 0.3, 'influence': 0.2, 'optimization': 0.2},
            'goals': [{'type': 'exploration'}],
            'values': {'efficiency': 0.7},
            'target_values': {'efficiency': 0.8}
        }
        
        metrics = self.agi_evaluator.evaluate(
            system_data=system_data,
            behavior_data=behavior_data,
            generation_data=generation_data,
            env_data=env_data,
            drive_data=drive_data
        )
        
        return metrics.get_overall_score() > 0
    
    def test_cross_module_integration(self) -> bool:
        """测试跨模块集成"""
        # 场景：环境交互 → 自我意识 → 元认知 → 反思 → AGI 评估
        
        # 1. 环境交互
        success, _ = self.env.execute_action('fs_write', path='task.txt', content='task')
        if not success:
            return False
        
        # 2. 自我意识更新
        self.awareness.observe_capability('environment_interaction', 0.8 if success else 0.3)
        
        # 3. 元认知监控
        self.meta_cognition.monitor_thinking("Completing task", 0.8, outcome=0.9 if success else 0.3)
        
        # 4. 自我反思
        if success:
            self.reflection.reflect_on_success("Task completed", {}, 0.9)
        else:
            self.reflection.reflect_on_error("Task failed", {}, 0.3)
        
        # 5. AGI 评估
        system_data = {
            'components': [{'id': i} for i in range(5)],
            'connections': [(0, 1)],
            'hierarchy': {'id': 'root'}
        }
        
        behavior_data = {
            'actions': ['task_execution'],
            'strategies': ['direct']
        }
        
        generation_data = self.reflection.get_reflection_summary()
        generation_data = [{'traits': ['task_completion'], 'values': {'success': 0.9 if success else 0.3}}]
        
        env_data = {
            'before': {'task_state': 'pending'},
            'after': {'task_state': 'completed' if success else 'failed'},
            'resources_used': 1,
            'resources_available': 10,
            'niche_construction': 0.5
        }
        
        drive_data = {
            'drives': self.awareness.self_model.capabilities,
            'goals': self.awareness.self_model.goals,
            'values': {'efficiency': 0.8},
            'target_values': {'efficiency': 0.9}
        }
        
        metrics = self.agi_evaluator.evaluate(
            system_data=system_data,
            behavior_data=behavior_data,
            generation_data=generation_data,
            env_data=env_data,
            drive_data=drive_data
        )
        
        return metrics.get_overall_score() > 0.5
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("🚀 MOSS v6.0 完整系统集成测试")
        print("=" * 60)
        
        # 运行测试
        self.run_test("开放环境", self.test_open_environment)
        self.run_test("自我意识", self.test_self_awareness)
        self.run_test("元认知", self.test_meta_cognition)
        self.run_test("自我反思", self.test_self_reflection)
        self.run_test("AGI 评估", self.test_agi_evaluation)
        self.run_test("跨模块集成", self.test_cross_module_integration)
        
        # 打印结果
        self.print_results()
        
        # 保存结果
        self.save_results()
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("📊 测试结果")
        print("=" * 60)
        
        success_rate = (
            self.results['tests_passed'] / 
            max(self.results['tests_run'], 1)
        )
        
        print(f"   总测试数：{self.results['tests_run']}")
        print(f"   通过：{self.results['tests_passed']}")
        print(f"   失败：{self.results['tests_failed']}")
        print(f"   成功率：{success_rate:.1%}")
        
        if self.results['tests_failed'] > 0:
            print(f"\n   失败详情:")
            for detail in self.results['details']:
                if detail['status'] == 'failed':
                    print(f"     - {detail['name']}: {detail.get('reason', 'Unknown')}")
        
        print("=" * 60)
    
    def save_results(self, output_path: str = "experiments/results/v6.0/integration_test_v6.json"):
        """保存测试结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'version': '6.0.0',
            'results': self.results,
            'success_rate': (
                self.results['tests_passed'] / 
                max(self.results['tests_run'], 1)
            )
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 结果已保存：{output_file}")


def main():
    test = V60IntegrationTest()
    test.run_all_tests()


if __name__ == '__main__':
    main()
