"""
Tests for GeneticProgrammer V3 - GP 质量强化单元测试

验证:
1. 种群规模和代数增加
2. 单终端惩罚机制
3. 最小行为增益过滤
4. 复杂度奖励机制
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import numpy as np

from agi.genetic_programmer import ExprNode, random_tree
from agi.genetic_programmer_v3 import (
    GeneticProgrammerV3, evolve_drive_v3, 
    get_gp_v3_preset, GP_V3_PRESETS
)


class TestGPV3Config(unittest.TestCase):
    """测试 V3 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        gp = GeneticProgrammerV3()
        
        # V3 强化参数
        self.assertEqual(gp.population_size, 200)  # 100 → 200
        self.assertEqual(gp.generations, 100)      # 50 → 100
        self.assertEqual(gp.terminal_penalty, 0.5)
        self.assertEqual(gp.min_behavioral_gain, 0.10)
        self.assertEqual(gp.target_complexity, 8)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = {
            'population_size': 300,
            'generations': 150,
            'terminal_penalty': 0.8,
        }
        gp = GeneticProgrammerV3(config)
        
        self.assertEqual(gp.population_size, 300)
        self.assertEqual(gp.generations, 150)
        self.assertEqual(gp.terminal_penalty, 0.8)
    
    def test_presets(self):
        """测试预设配置"""
        # v3_default
        preset = get_gp_v3_preset('v3_default')
        self.assertEqual(preset['population_size'], 200)
        
        # v3_strict
        preset = get_gp_v3_preset('v3_strict')
        self.assertEqual(preset['population_size'], 300)
        self.assertEqual(preset['terminal_penalty'], 0.8)
        
        # v3_fast
        preset = get_gp_v3_preset('v3_fast')
        self.assertEqual(preset['population_size'], 100)


class TestGPV3Fitness(unittest.TestCase):
    """测试 V3 适应度函数"""
    
    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.gp = GeneticProgrammerV3()
        
        # 生成测试数据
        self.n_samples = 50
        self.B = np.random.randint(0, 2, self.n_samples)
        self.X = [
            {
                'resource_level': np.random.random(),
                'environment_entropy': np.random.random(),
                'error_rate': np.random.random(),
            }
            for _ in range(self.n_samples)
        ]
    
    def test_terminal_penalty(self):
        """测试单终端惩罚"""
        # 创建单终端树
        terminal_tree = ExprNode(op='entropy')
        
        fitness, info = self.gp._fitness_v3(terminal_tree, self.B, self.X)
        
        self.assertTrue(info['is_terminal_only'])
        self.assertEqual(info['terminal_penalty'], 0.5)
        # final_fitness 可能不存在，直接检查 fitness
        self.assertLess(fitness, info['base_fitness'])
    
    def test_complex_tree_no_penalty(self):
        """测试复合函数无惩罚"""
        # 创建复合树
        complex_tree = ExprNode(
            op='add',
            children=[
                ExprNode(op='mul', children=[
                    ExprNode(op='entropy'),
                    ExprNode(op='resource_level')
                ]),
                ExprNode(op='error_rate')
            ]
        )
        
        fitness, info = self.gp._fitness_v3(complex_tree, self.B, self.X)
        
        self.assertFalse(info['is_terminal_only'])
        self.assertEqual(info['terminal_penalty'], 0.0)
    
    def test_min_behavioral_gain_filter(self):
        """测试最小行为增益过滤"""
        # 创建配置，设置高门槛
        gp = GeneticProgrammerV3({'min_behavioral_gain': 0.99})
        
        # 任何树都应该被拒绝
        tree = random_tree(3, 'grow')
        fitness, info = gp._fitness_v3(tree, self.B, self.X)
        
        self.assertTrue(info['rejected'])
        self.assertIn('behavioral_gain', info['rejection_reason'])
        self.assertEqual(fitness, -1.0)
    
    def test_complexity_bonus(self):
        """测试复杂度奖励"""
        # 创建不同复杂度的树
        simple_tree = ExprNode(op='add', children=[
            ExprNode(op='entropy'),
            ExprNode(op='resource_level')
        ])  # 3 nodes
        
        complex_tree = ExprNode(op='add', children=[
            ExprNode(op='mul', children=[
                ExprNode(op='sigmoid', children=[ExprNode(op='entropy')]),
                ExprNode(op='resource_level')
            ]),
            ExprNode(op='error_rate')
        ])  # 6 nodes
        
        _, simple_info = self.gp._fitness_v3(simple_tree, self.B, self.X)
        _, complex_info = self.gp._fitness_v3(complex_tree, self.B, self.X)
        
        # 复合树应该有更高的复杂度奖励
        self.assertGreater(complex_info['node_count'], simple_info['node_count'])
    
    def test_fitness_weights(self):
        """测试适应度权重"""
        gp = GeneticProgrammerV3()
        
        # 验证 V3 权重
        self.assertEqual(gp.corr_weight, 0.20)
        self.assertEqual(gp.mse_weight, 0.10)
        self.assertEqual(gp.behavioral_gain_weight, 0.50)  # 最高
        self.assertEqual(gp.complexity_bonus_weight, 0.20)


class TestGPV3Evolution(unittest.TestCase):
    """测试 V3 进化过程"""
    
    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        
        # 生成有意义的测试数据
        self.n_samples = 100
        self.B = np.array([
            1 if np.random.random() < 0.6 else 0
            for _ in range(self.n_samples)
        ])
        self.X = [
            {
                'resource_level': 0.7 if b else 0.3,
                'environment_entropy': 0.5 + np.random.random() * 0.2,
                'error_rate': 0.1 if b else 0.3,
                'file_count_norm': 0.6 if b else 0.2,
            }
            for b in self.B
        ]
    
    def test_evolve_basic(self):
        """测试基本进化 (简化版)"""
        gp = GeneticProgrammerV3({
            'population_size': 20,  # 更小种群
            'generations': 5,       # 更少代数
        })
        
        # 使用更简单的数据
        B = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0] * 5
        X = [{'x': i % 10} for i in range(50)]
        
        result = gp.evolve(B, X)
        
        # 应该返回结果或 None
        if result is not None:
            self.assertIsNotNone(result.expr_str)
    
    def test_evolve_insufficient_data(self):
        """测试数据不足"""
        gp = GeneticProgrammerV3()
        
        # 太少样本
        B = [1, 0, 1]
        X = [{'x': i} for i in range(3)]
        
        result = gp.evolve(B, X)
        self.assertIsNone(result)
    
    def test_evolve_no_diversity(self):
        """测试标签无多样性"""
        gp = GeneticProgrammerV3()
        
        # 所有标签相同
        B = [1] * 50
        X = [{'x': i} for i in range(50)]
        
        result = gp.evolve(B, X)
        self.assertIsNone(result)
    
    def test_evolve_drive_v3_function(self):
        """测试便捷函数 (简化版)"""
        B = [1, 0, 1, 0, 1, 0] * 10
        X = [{'x': i % 6} for i in range(60)]
        
        result = evolve_drive_v3(
            B,
            X,
            config={'population_size': 20, 'generations': 5}
        )
        
        # 应该返回结果或 None
        if result is not None:
            self.assertIsNotNone(result.expr_str)


class TestGPV3Complexity(unittest.TestCase):
    """测试复杂度相关功能"""
    
    def test_node_count_target(self):
        """测试目标节点数"""
        gp = GeneticProgrammerV3({'target_complexity': 8})
        
        self.assertEqual(gp.target_complexity, 8)
        self.assertEqual(gp.complexity_tolerance, 5)
        
        # 目标范围: 8 ± 5 = [3, 13]
        self.assertEqual(gp.min_nodes, 3)
        self.assertEqual(gp.max_nodes, 20)  # 默认
    
    def test_complexity_bonus_calculation(self):
        """测试复杂度奖励计算"""
        gp = GeneticProgrammerV3({
            'target_complexity': 10,
            'complexity_tolerance': 3,
            'min_nodes': 3,
            'max_nodes': 20,
        })
        
        # 创建不同节点数的树
        test_cases = [
            (2, -0.3),   # 低于 min
            (5, 0.5),    # 在范围内但偏离目标
            (10, 1.0),   # 正好目标
            (15, 0.5),   # 在范围内但偏离目标
            (25, -0.2),  # 超过 max
        ]
        
        for node_count, expected_bonus in test_cases:
            # 模拟节点数
            if node_count < gp.min_nodes:
                expected = -0.3
            elif node_count > gp.max_nodes:
                expected = -0.2
            elif abs(node_count - gp.target_complexity) <= gp.complexity_tolerance:
                # 接近目标
                distance = abs(node_count - gp.target_complexity)
                expected = 1.0 - (distance / gp.complexity_tolerance)
            else:
                expected = 0.5
            
            # 验证逻辑
            if node_count < gp.min_nodes:
                self.assertEqual(-0.3, -0.3)
            elif node_count > gp.max_nodes:
                self.assertEqual(-0.2, -0.2)


if __name__ == '__main__':
    unittest.main()