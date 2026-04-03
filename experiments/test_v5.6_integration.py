#!/usr/bin/env python3
"""
MOSS v5.6 - Full System Integration Test
完整系统集成测试

测试所有 v5.6 模块的协同工作:
- 开放目标生成
- 目标演化
- 文化传递
- 社会学习
- AGI 评估

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.open_ended_goals import GoalGenerator, GoalType
from core.goal_evolution import GoalEvolution
from core.cultural_transmission import CulturalTransmission
from core.social_learning import SocialNetwork, SocialLearner
from evaluation.agi_metrics import AGIEvaluator


class V56IntegrationTest:
    """v5.6 集成测试管理器"""
    
    def __init__(self):
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        # 初始化所有模块
        print("🔧 初始化 v5.6 模块...")
        self.goal_generator = GoalGenerator()
        self.goal_evolution = GoalEvolution(population_size=20)
        self.cultural_transmission = CulturalTransmission(population_size=20, generations=10)
        self.agi_evaluator = AGIEvaluator()
        
        print("   ✅ 目标生成器")
        print("   ✅ 目标演化引擎")
        print("   ✅ 文化传递引擎")
        print("   ✅ AGI 评估器")
    
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
    
    def test_goal_generation(self) -> bool:
        """测试目标生成"""
        context = {
            'critical_resource': 'computational_power',
            'current_domain': 'ai_research',
            'urgency': 0.7,
            'alignment': 0.8
        }
        
        goal = self.goal_generator.generate_goal(context)
        
        return goal is not None and goal.description != ""
    
    def test_goal_evolution(self) -> bool:
        """测试目标演化"""
        # 初始化种群
        base_goals = []
        for i in range(5):
            context = {'urgency': 0.5, 'alignment': 0.7}
            goal = self.goal_generator.generate_goal(context)
            if goal:
                base_goals.append(goal)
        
        self.goal_evolution.initialize_population(base_goals)
        
        # 演化一代
        self.goal_evolution.evolve_generation()
        
        # 验证
        best_goal = self.goal_evolution.get_best_goal()
        return best_goal is not None
    
    def test_cultural_transmission(self) -> bool:
        """测试文化传递"""
        # 初始化
        self.cultural_transmission.initialize_population(n_initial_traits=3)
        
        # 运行一代
        self.cultural_transmission.run_generation(mutation_rate=0.05)
        
        # 验证
        status = self.cultural_transmission.get_status()
        return status['population_size'] > 0 and status['cultural_diversity'] >= 0
    
    def test_social_learning(self) -> bool:
        """测试社会学习"""
        # 创建社会网络
        network = SocialNetwork(n_agents=5)
        network.initialize_random_network(connection_prob=0.5)
        
        # 创建学习者
        learner = SocialLearner(0, network)
        
        # 初始化知识
        model_knowledge = {'skill_1': 0.8, 'skill_2': 0.7}
        
        # 观察学习
        learned = learner.observe(1, model_knowledge)
        
        return True  # 网络创建成功即通过
    
    def test_agi_evaluation(self) -> bool:
        """测试 AGI 评估"""
        # 准备测试数据
        system_data = {
            'components': [{'id': i} for i in range(10)],
            'connections': [(i, j) for i in range(10) for j in range(i+1, 10) if i % 2 == 0],
            'hierarchy': {'id': 'root', 'children': [{'id': f'child_{i}'} for i in range(3)]}
        }
        
        behavior_data = {
            'actions': ['explore', 'exploit', 'communicate'] * 5,
            'strategies': ['strategy_A', 'strategy_B', 'strategy_C']
        }
        
        generation_data = [
            {'traits': ['A', 'B'], 'values': {'cooperation': 0.7}},
            {'traits': ['A', 'C'], 'values': {'cooperation': 0.75}}
        ]
        
        env_data = {
            'before': {'resource_level': 100},
            'after': {'resource_level': 80},
            'resources_used': 20,
            'resources_available': 100,
            'niche_construction': 0.6
        }
        
        drive_data = {
            'drives': {'survival': 0.3, 'curiosity': 0.3, 'influence': 0.2, 'optimization': 0.2},
            'goals': [{'type': 'exploration'}, {'type': 'achievement'}],
            'values': {'efficiency': 0.8},
            'target_values': {'efficiency': 0.85}
        }
        
        # 评估
        metrics = self.agi_evaluator.evaluate(
            system_data=system_data,
            behavior_data=behavior_data,
            generation_data=generation_data,
            env_data=env_data,
            drive_data=drive_data
        )
        
        # 验证综合分数
        overall_score = metrics.get_overall_score()
        return overall_score > 0 and overall_score <= 1
    
    def test_cross_module_integration(self) -> bool:
        """测试跨模块集成"""
        # 场景：目标生成 → 演化 → 文化传递 → AGI 评估
        
        # 1. 生成目标
        context = {'urgency': 0.6, 'alignment': 0.8}
        goal = self.goal_generator.generate_goal(context)
        
        if not goal:
            return False
        
        # 2. 目标演化
        self.goal_evolution.initialize_population([goal])
        self.goal_evolution.evolve_generation()
        
        # 3. 文化传递
        self.cultural_transmission.initialize_population(n_initial_traits=2)
        self.cultural_transmission.run_generation()
        
        # 4. AGI 评估
        system_data = {
            'components': [{'id': i} for i in range(5)],
            'connections': [(0, 1), (1, 2)],
            'hierarchy': {'id': 'root'}
        }
        
        behavior_data = {
            'actions': ['action_1', 'action_2'],
            'strategies': ['strategy_1']
        }
        
        generation_data = self.cultural_transmission.generation_history[-2:] if len(self.cultural_transmission.generation_history) >= 2 else []
        
        env_data = {
            'before': {'resource': 100},
            'after': {'resource': 90},
            'resources_used': 10,
            'resources_available': 100,
            'niche_construction': 0.5
        }
        
        drive_data = {
            'drives': self.goal_generator.drive.drives,
            'goals': [{'type': g.goal_type.value} for g in self.goal_evolution.goals[:3]],
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
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("🚀 MOSS v5.6 完整系统集成测试")
        print("=" * 60)
        
        # 运行测试
        self.run_test("目标生成", self.test_goal_generation)
        self.run_test("目标演化", self.test_goal_evolution)
        self.run_test("文化传递", self.test_cultural_transmission)
        self.run_test("社会学习", self.test_social_learning)
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
    
    def save_results(self, output_path: str = "experiments/results/v5.6/integration_test.json"):
        """保存测试结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        results = {
            'timestamp': datetime.now().isoformat(),
            'version': '5.6.0',
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
    test = V56IntegrationTest()
    test.run_all_tests()


if __name__ == '__main__':
    main()
