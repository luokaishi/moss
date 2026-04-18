"""
Tests for DriveWeightCap - 权重上限机制单元测试

验证：
1. 硬上限正确应用
2. 软上限缓慢增长
3. 超额权重重新分配
4. 涌现驱动保护
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from agi.drive_weight_cap import (
    WeightCapConfig, DriveWeightCap, DriveWeightCapManager, get_preset, MockDrive
)


class MockDriveManager:
    """模拟 DriveManager 用于测试"""
    def __init__(self, drives):
        self.drives = drives





class TestWeightCapConfig(unittest.TestCase):
    """测试权重上限配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = WeightCapConfig()
        self.assertEqual(config.survival, 0.30)
        self.assertEqual(config.optimization, 0.25)
        self.assertEqual(config.influence, 0.20)
        self.assertEqual(config.curiosity, 0.15)
        self.assertEqual(config.emergent, 0.35)
    
    def test_get_cap_builtin(self):
        """测试获取内置驱动上限"""
        config = WeightCapConfig()
        self.assertEqual(config.get_cap('survival'), 0.30)
        self.assertEqual(config.get_cap('optimization'), 0.25)
        self.assertEqual(config.get_cap('influence'), 0.20)
        self.assertEqual(config.get_cap('curiosity'), 0.15)
    
    def test_get_cap_emergent(self):
        """测试获取涌现驱动上限"""
        config = WeightCapConfig()
        self.assertEqual(config.get_cap('any_name', is_emergent=True), 0.35)
    
    def test_get_cap_unknown(self):
        """测试未知驱动返回默认值"""
        config = WeightCapConfig()
        self.assertEqual(config.get_cap('unknown_drive'), 0.25)


class TestDriveWeightCap(unittest.TestCase):
    """测试权重上限核心逻辑"""
    
    def setUp(self):
        self.config = WeightCapConfig(survival=0.30)
        self.cap = DriveWeightCap(self.config)
    
    def test_hard_cap(self):
        """测试硬上限：权重不超过配置值"""
        # 当前 0.25，提议 +0.10，新值 0.35 > 软上限 0.33，应该限制在 0.33
        result = self.cap.apply_cap('survival', 0.25, False, 0.10)
        self.assertAlmostEqual(result, 0.33, places=5)  # 软上限
    
    def test_soft_cap_growth(self):
        """测试软上限：允许轻微溢出但增长放缓"""
        # 当前 0.28，提议 +0.05，硬上限 0.30，软上限 0.33
        # 新值 0.33 正好在软上限，应该应用但可能放缓
        result = self.cap.apply_cap('survival', 0.28, False, 0.05)
        # 允许在软上限范围内
        self.assertLessEqual(result, 0.33)
        self.assertGreater(result, 0.28)
    
    def test_strict_cap(self):
        """测试严格上限：超过软上限被严格限制"""
        # 当前 0.30，提议 +0.10，硬上限 0.30，软上限 0.33
        # 新值 0.40 超过软上限，应该被限制在 0.33
        result = self.cap.apply_cap('survival', 0.30, False, 0.10)
        self.assertEqual(result, 0.33)  # 软上限值
    
    def test_normal_growth(self):
        """测试正常增长：在硬上限内不受限制"""
        # 当前 0.20，提议 +0.05，上限 0.30
        # 新值 0.25 在硬上限内，应该正常增长
        result = self.cap.apply_cap('survival', 0.20, False, 0.05)
        self.assertEqual(result, 0.25)
    
    def test_overflow_tracking(self):
        """测试溢出次数记录"""
        # 多次触发严格上限
        for _ in range(3):
            self.cap.apply_cap('survival', 0.30, False, 0.10)
        
        self.assertEqual(self.cap.get_overflow_count('survival'), 3)
        self.assertEqual(self.cap.get_overflow_count('other'), 0)
    
    def test_warn_threshold(self):
        """测试警告阈值"""
        # 4 次溢出，不应警告
        for _ in range(4):
            self.cap.apply_cap('survival', 0.30, False, 0.10)
        self.assertFalse(self.cap.should_warn('survival'))
        
        # 第 5 次，应该警告
        self.cap.apply_cap('survival', 0.30, False, 0.10)
        self.assertTrue(self.cap.should_warn('survival'))


class TestDriveWeightCapManager(unittest.TestCase):
    """测试权重上限管理器集成"""
    
    def setUp(self):
        self.config = WeightCapConfig(
            survival=0.30,
            optimization=0.25,
            influence=0.20,
            curiosity=0.15,
            emergent=0.35
        )
    
    def test_apply_weight_update_within_cap(self):
        """测试在限制内更新权重"""
        drives = {
            'survival': MockDrive(0.20),
            'optimization': MockDrive(0.20),
        }
        mock_manager = MockDriveManager(drives)
        cap_manager = DriveWeightCapManager(mock_manager, self.config)
        
        # 提议 +0.05，新值 0.25 在上限 0.30 内
        delta = cap_manager.apply_weight_update('survival', 0.05)
        self.assertAlmostEqual(delta, 0.05, places=5)
    
    def test_apply_weight_update_exceeds_cap(self):
        """测试超出上限的权重更新"""
        drives = {
            'survival': MockDrive(0.28),
        }
        mock_manager = MockDriveManager(drives)
        cap_manager = DriveWeightCapManager(mock_manager, self.config)
        
        # 提议 +0.05，新值 0.33 正好是软上限
        delta = cap_manager.apply_weight_update('survival', 0.05)
        # 新权重应该不超过软上限 0.33
        new_weight = drives['survival'].weight + delta
        self.assertLessEqual(new_weight, 0.33 + 1e-9)
        self.assertGreater(new_weight, 0.28)
    
    def test_normalize_with_caps(self):
        """测试带上限的归一化"""
        # 使用外部权重字典进行测试
        weights = {
            'survival': 0.40,      # 超过上限 0.30
            'optimization': 0.30,  # 超过上限 0.25
            'curiosity': 0.10,     # 未超过上限 0.15
        }
        drives = {
            'survival': MockDrive(0.40),
            'optimization': MockDrive(0.30),
            'curiosity': MockDrive(0.10),
        }
        mock_manager = MockDriveManager(drives)
        cap_manager = DriveWeightCapManager(mock_manager, self.config)
        
        result = cap_manager.normalize_with_caps(weights)
        
        # 验证总和为 1
        self.assertAlmostEqual(sum(result.values()), 1.0, places=5)
        
        # 归一化后: survival=0.50, optimization=0.375, curiosity=0.125
        # 应用上限后，超额权重重新分配
        # 验证 curiosity 获得了额外权重
        self.assertGreater(result['curiosity'], 0.125)
    
    def test_stats_tracking(self):
        """测试统计信息"""
        drives = {'survival': MockDrive(0.28)}
        mock_manager = MockDriveManager(drives)
        cap_manager = DriveWeightCapManager(mock_manager, self.config)
        
        # 正常更新 (0.28 -> 0.29)
        cap_manager.apply_weight_update('survival', 0.01)
        # 触发上限 (0.29 -> 0.33 软上限)
        cap_manager.apply_weight_update('survival', 0.10)
        
        stats = cap_manager.get_stats()
        self.assertEqual(stats['total_updates'], 2)
        # 第二次更新被限制（0.29 + 0.10 = 0.39 > 软上限 0.33）
        self.assertGreaterEqual(stats['caps_applied'], 1)
        self.assertEqual(stats['cap_rate'], 0.5)


class TestPresets(unittest.TestCase):
    """测试预设配置"""
    
    def test_v6_default_preset(self):
        """测试 v6 默认预设"""
        config = get_preset('v6_default')
        self.assertEqual(config.survival, 0.30)
        self.assertEqual(config.emergent, 0.35)
    
    def test_v6_strict_preset(self):
        """测试 v6 严格预设"""
        config = get_preset('v6_strict')
        self.assertEqual(config.survival, 0.25)
        self.assertEqual(config.optimization, 0.22)
    
    def test_v6_loose_preset(self):
        """测试 v6 宽松预设"""
        config = get_preset('v6_loose')
        self.assertEqual(config.survival, 0.35)
        self.assertEqual(config.emergent, 0.40)
    
    def test_unknown_preset_returns_default(self):
        """测试未知预设返回默认值"""
        config = get_preset('unknown')
        self.assertEqual(config.survival, 0.30)  # v6_default 的值


class TestEmergentDriveProtection(unittest.TestCase):
    """测试涌现驱动保护机制"""
    
    def test_emergent_higher_cap(self):
        """测试涌现驱动有更高上限"""
        config = WeightCapConfig(survival=0.30, emergent=0.35)
        cap = DriveWeightCap(config)
        
        # 涌现驱动: 当前 0.30，提议 +0.10，新值 0.40 > 软上限 0.385，应该限制在 0.385
        result = cap.apply_cap('new_emergent', 0.30, True, 0.10)
        self.assertAlmostEqual(result, 0.385, places=5)  # 软上限 0.35 * 1.1
        
        # 普通驱动: 当前 0.30，提议 +0.10，新值 0.40 > 软上限 0.33，应该限制在 0.33
        result = cap.apply_cap('survival', 0.30, False, 0.10)
        self.assertAlmostEqual(result, 0.33, places=5)  # 软上限 0.30 * 1.1


if __name__ == '__main__':
    unittest.main()