"""
Tests for DriveCompetition - 驱动竞争机制单元测试

验证：
1. 试用期机制正确工作
2. 表现评估逻辑准确
3. 权重动态调整合理
4. 淘汰机制有效
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from agi.drive_competition import (
    DriveCompetition, DriveCompetitionManager, DrivePerformance,
    DriveStatus, CompetitionConfig, get_competition_preset
)


class MockDriveManager:
    """模拟 DriveManager 用于测试"""
    def __init__(self, drives):
        self.drives = drives
    
    def get_all_drive_names(self):
        return list(self.drives.keys())


class MockDrive:
    """模拟 Drive 用于测试"""
    def __init__(self, is_emergent=False):
        self.is_emergent = is_emergent


class TestCompetitionConfig(unittest.TestCase):
    """测试竞争配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = CompetitionConfig()
        self.assertEqual(config.probation_period, 500)
        self.assertEqual(config.min_weight, 0.02)
        self.assertEqual(config.max_weight, 0.35)
    
    def test_preset_v6_default(self):
        """测试 v6 默认预设"""
        config = get_competition_preset('v6_default')
        self.assertEqual(config.probation_period, 500)
        self.assertEqual(config.warning_threshold, 3)
    
    def test_preset_v6_strict(self):
        """测试 v6 严格预设"""
        config = get_competition_preset('v6_strict')
        self.assertEqual(config.probation_period, 300)
        self.assertEqual(config.warning_threshold, 2)
    
    def test_preset_v6_loose(self):
        """测试 v6 宽松预设"""
        config = get_competition_preset('v6_loose')
        self.assertEqual(config.probation_period, 700)
        self.assertEqual(config.warning_threshold, 5)


class TestDrivePerformance(unittest.TestCase):
    """测试驱动表现记录"""
    
    def setUp(self):
        self.perf = DrivePerformance(drive_name='test_drive')
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(self.perf.drive_name, 'test_drive')
        self.assertEqual(self.perf.age, 0)
        self.assertEqual(self.perf.status, DriveStatus.PROBATION)
    
    def test_update(self):
        """测试更新"""
        self.perf.update(cycle=100, reward=0.8, score=0.7)
        self.assertEqual(self.perf.age, 100)
        self.assertEqual(len(self.perf.reward_history), 1)
        self.assertEqual(self.perf.reward_history[0], 0.8)
    
    def test_recent_performance(self):
        """测试近期表现"""
        for i in range(10):
            self.perf.update(cycle=i*10, reward=0.5 + i*0.05, score=0.5)
        
        recent = self.perf.get_recent_performance(window=5)
        self.assertIn('avg_reward', recent)
        self.assertIn('trend', recent)


class TestDriveCompetition(unittest.TestCase):
    """测试驱动竞争核心逻辑"""
    
    def setUp(self):
        self.config = CompetitionConfig(
            probation_period=100,
            evaluation_window=20,
            good_performance_threshold=0.7,
            poor_performance_threshold=0.3,
        )
        self.competition = DriveCompetition(self.config)
    
    def test_register_drive(self):
        """测试注册驱动"""
        perf = self.competition.register_drive('survival', is_emergent=False)
        self.assertEqual(perf.drive_name, 'survival')
        self.assertEqual(perf.status, DriveStatus.ACTIVE)  # 非涌现直接激活
        
        perf2 = self.competition.register_drive('emergent', is_emergent=True)
        self.assertEqual(perf2.status, DriveStatus.PROBATION)  # 涌现进入试用期
    
    def test_probation_growth(self):
        """测试试用期增长"""
        self.competition.register_drive('test', is_emergent=True)
        
        # 添加表现数据
        for i in range(50):
            self.competition.update_performance('test', i, 0.6, 0.5)
        
        # 评估 (还在试用期内)
        result = self.competition.evaluate_drive('test', cycle=50)
        self.assertEqual(result['action'], 'grow')
        self.assertEqual(result['reason'], '试用期正常增长')
    
    def test_probation_promotion(self):
        """测试试用期转正"""
        self.competition.register_drive('test', is_emergent=True)
        
        # 添加良好表现数据 (超过试用期)
        for i in range(120):
            self.competition.update_performance('test', i, 0.8, 0.7)  # 高奖励
        
        # 评估 (完成试用期，表现良好)
        result = self.competition.evaluate_drive('test', cycle=120)
        self.assertEqual(result['action'], 'grow')
        self.assertIn('转正', result['reason'])
        self.assertEqual(self.competition.performances['test'].status, DriveStatus.ACTIVE)
    
    def test_active_growth(self):
        """测试正式期增长"""
        self.competition.register_drive('test', is_emergent=False)
        
        # 添加良好表现
        for i in range(30):
            self.competition.update_performance('test', i, 0.8, 0.7)
        
        result = self.competition.evaluate_drive('test', cycle=30)
        self.assertEqual(result['action'], 'grow')
        self.assertIn('表现良好', result['reason'])
    
    def test_active_decay(self):
        """测试正式期衰减"""
        self.competition.register_drive('test', is_emergent=False)
        
        # 添加差表现
        for i in range(30):
            self.competition.update_performance('test', i, 0.2, 0.3)
        
        result = self.competition.evaluate_drive('test', cycle=30)
        self.assertEqual(result['action'], 'decay')
        self.assertIn('表现不佳', result['reason'])
    
    def test_elimination(self):
        """测试淘汰机制"""
        config = CompetitionConfig(
            probation_period=100,
            evaluation_window=20,
            warning_threshold=2,
            poor_performance_threshold=0.3,
        )
        competition = DriveCompetition(config)
        competition.register_drive('test', is_emergent=False)
        
        # 连续差表现，触发多次警告
        for cycle in range(100):
            competition.update_performance('test', cycle, 0.1, 0.2)
            # 每 50 周期评估一次
            if cycle > 0 and cycle % 50 == 0:
                competition.evaluate_drive('test', cycle)
        
        # 最终评估应该淘汰
        result = competition.evaluate_drive('test', cycle=100)
        self.assertEqual(result['action'], 'eliminate')
        self.assertTrue(competition.should_eliminate('test'))
    
    def test_get_summary(self):
        """测试获取摘要"""
        self.competition.register_drive('d1', is_emergent=False)
        self.competition.register_drive('d2', is_emergent=True)
        
        summary = self.competition.get_summary()
        self.assertEqual(summary['total_drives'], 2)
        self.assertIn('status_distribution', summary)


class TestDriveCompetitionManager(unittest.TestCase):
    """测试竞争管理器集成"""
    
    def setUp(self):
        self.config = CompetitionConfig(
            probation_period=100,
            evaluation_window=20,
        )
        self.drives = {
            'survival': MockDrive(is_emergent=False),
            'emergent': MockDrive(is_emergent=True),
        }
        self.mock_manager = MockDriveManager(self.drives)
        self.comp_manager = DriveCompetitionManager(self.mock_manager, self.config)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.comp_manager.competition.performances), 2)
        self.assertEqual(
            self.comp_manager.competition.performances['survival'].status,
            DriveStatus.ACTIVE
        )
        self.assertEqual(
            self.comp_manager.competition.performances['emergent'].status,
            DriveStatus.PROBATION
        )
    
    def test_update(self):
        """测试更新"""
        drive_rewards = {'survival': 0.7, 'emergent': 0.6}
        self.comp_manager.update(cycle=10, drive_rewards=drive_rewards)
        
        self.assertEqual(
            self.comp_manager.competition.performances['survival'].age,
            10
        )
        self.assertEqual(
            len(self.comp_manager.competition.performances['survival'].reward_history),
            1
        )
    
    def test_evaluate_and_adjust(self):
        """测试评估和调整"""
        # 先更新一些表现数据
        for i in range(30):
            self.comp_manager.update(
                cycle=i,
                drive_rewards={'survival': 0.8, 'emergent': 0.9}
            )
        
        # 评估
        adjustments = self.comp_manager.evaluate_and_adjust(cycle=30)
        
        self.assertIn('survival', adjustments)
        self.assertIn('emergent', adjustments)
        self.assertIn('action', adjustments['survival'])
        self.assertIn('factor', adjustments['survival'])
    
    def test_apply_adjustments(self):
        """测试应用调整"""
        current_weights = {'survival': 0.25, 'emergent': 0.15}
        
        adjustments = {
            'survival': {'action': 'grow', 'factor': 1.05, 'reason': 'test'},
            'emergent': {'action': 'decay', 'factor': 0.95, 'reason': 'test'},
        }
        
        new_weights = self.comp_manager.apply_adjustments(adjustments, current_weights)
        
        self.assertGreater(new_weights['survival'], current_weights['survival'])
        self.assertLess(new_weights['emergent'], current_weights['emergent'])
    
    def test_get_eliminated_drives(self):
        """测试获取被淘汰驱动"""
        # 使用已有的 survival 驱动进行测试
        # 手动标记为淘汰
        from agi.drive_competition import DriveStatus
        self.comp_manager.competition.performances['survival'].status = DriveStatus.ELIMINATED
        
        eliminated = self.comp_manager.get_eliminated_drives()
        self.assertIn('survival', eliminated)
    
    def test_get_stats(self):
        """测试获取统计"""
        stats = self.comp_manager.get_stats()
        
        self.assertIn('competition_summary', stats)
        self.assertIn('drive_stats', stats)


if __name__ == '__main__':
    unittest.main()