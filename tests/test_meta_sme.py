"""
MOSS v7.1 - Meta-SME Unit Tests
Meta-SME 单元测试
"""

import unittest
import sys
import os
import numpy as np
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.meta_sme import (
    MetaSME, ModificationType, SafetyLevel,
    ModificationProposal, ModificationResult,
    SandboxTester, PatchVerifier, RollbackManager
)
from agi.meta_sme_integration import (
    MetaSMEDriveIntegration, DrivePerformanceMetrics,
    EnvironmentAwareMetaSME
)


class TestSandboxTester(unittest.TestCase):
    """测试沙箱测试器"""
    
    def setUp(self):
        self.sandbox = SandboxTester(sandbox_dir=".test_sandbox")
    
    def tearDown(self):
        # 清理测试沙箱
        import shutil
        if Path(".test_sandbox").exists():
            shutil.rmtree(".test_sandbox")
    
    def test_create_sandbox(self):
        """测试创建沙箱"""
        source_code = "def test(): return 42"
        sandbox_path = self.sandbox.create_sandbox("test_module", source_code)
        
        self.assertTrue(sandbox_path.exists())
        self.assertTrue((sandbox_path / "test_module.py").exists())
    
    def test_syntax_check_pass(self):
        """测试语法检查通过"""
        proposal = ModificationProposal(
            proposal_id="test_1",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            safety_level=SafetyLevel.SAFE,
            target_module="test",
            target_function=None,
            description="Test",
            ast_patch={'new_code': 'def test(): return 42'},
            expected_impact={}
        )
        
        passed, results = self.sandbox.test_modification(proposal, [])
        self.assertTrue(passed)
        self.assertTrue(any(r['test'] == 'syntax_check' for r in results))
    
    def test_syntax_check_fail(self):
        """测试语法检查失败"""
        proposal = ModificationProposal(
            proposal_id="test_2",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            safety_level=SafetyLevel.SAFE,
            target_module="test",
            target_function=None,
            description="Test",
            ast_patch={'new_code': 'def test(: return 42'},  # 语法错误
            expected_impact={}
        )
        
        passed, results = self.sandbox.test_modification(proposal, [])
        self.assertFalse(passed)


class TestPatchVerifier(unittest.TestCase):
    """测试补丁验证器"""
    
    def setUp(self):
        self.verifier = PatchVerifier()
    
    def test_record_baseline(self):
        """测试记录基线"""
        metrics = {'performance': 0.5}
        self.verifier.record_baseline(metrics)
        
        self.assertEqual(self.verifier.metrics_before['performance'], 0.5)
    
    def test_verify_patch_success(self):
        """测试验证补丁成功"""
        self.verifier.record_baseline({'performance': 0.5})
        
        proposal = ModificationProposal(
            proposal_id="test_3",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            safety_level=SafetyLevel.SAFE,
            target_module="test",
            target_function=None,
            description="Test",
            ast_patch={},
            expected_impact={'min_performance_improvement': 0.01}
        )
        
        verified, delta = self.verifier.verify_patch(proposal, {'performance': 0.55})
        
        self.assertTrue(verified)
        self.assertAlmostEqual(delta, 0.1, places=2)
    
    def test_verify_patch_failure(self):
        """测试验证补丁失败"""
        self.verifier.record_baseline({'performance': 0.5})
        
        proposal = ModificationProposal(
            proposal_id="test_4",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            safety_level=SafetyLevel.SAFE,
            target_module="test",
            target_function=None,
            description="Test",
            ast_patch={},
            expected_impact={'min_performance_improvement': 0.2}
        )
        
        verified, delta = self.verifier.verify_patch(proposal, {'performance': 0.55})
        
        self.assertFalse(verified)


class TestRollbackManager(unittest.TestCase):
    """测试回滚管理器"""
    
    def setUp(self):
        self.rollback = RollbackManager(backup_dir=".test_backups")
    
    def tearDown(self):
        import shutil
        if Path(".test_backups").exists():
            shutil.rmtree(".test_backups")
    
    def test_create_backup(self):
        """测试创建备份"""
        source_code = "def test(): return 42"
        backup_id = self.rollback.create_backup("test_module", source_code)
        
        self.assertIsNotNone(backup_id)
        self.assertTrue(any(b['backup_id'] == backup_id for b in self.rollback.backup_history))
    
    def test_rollback(self):
        """测试回滚"""
        source_code = "def test(): return 42"
        backup_id = self.rollback.create_backup("test_module", source_code)
        
        rolled_back_code = self.rollback.rollback(backup_id)
        
        self.assertEqual(rolled_back_code, source_code)


class TestMetaSME(unittest.TestCase):
    """测试 Meta-SME"""
    
    def setUp(self):
        self.meta_sme = MetaSME(
            enable_auto_modify=False,
            require_human_approval=True,
            sandbox_dir=".test_sandbox_meta",
            backup_dir=".test_backups_meta"
        )
    
    def tearDown(self):
        import shutil
        for dir_name in [".test_sandbox_meta", ".test_backups_meta"]:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertFalse(self.meta_sme.enable_auto_modify)
        self.assertTrue(self.meta_sme.require_human_approval)
        self.assertEqual(self.meta_sme.stats['proposals_generated'], 0)
    
    def test_should_generate_proposal_insufficient_history(self):
        """测试历史不足时不生成提案"""
        result = self.meta_sme.should_generate_proposal()
        self.assertFalse(result)
    
    def test_should_generate_proposal_plateau(self):
        """测试平台期时生成提案"""
        # 模拟平台期
        for _ in range(20):
            self.meta_sme.record_performance(0.5 + np.random.randn() * 0.005)
        
        result = self.meta_sme.should_generate_proposal()
        self.assertTrue(result)
    
    def test_generate_proposal(self):
        """测试生成提案"""
        proposal = self.meta_sme.generate_proposal(
            target_module="agi.drive_manager",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            description="Test proposal",
            ast_patch={'new_code': 'pass'},
            expected_impact={}
        )
        
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.mod_type, ModificationType.WEIGHT_ADJUSTMENT)
        self.assertEqual(self.meta_sme.stats['proposals_generated'], 1)
    
    def test_generate_proposal_protected_module(self):
        """测试保护模块拒绝"""
        proposal = self.meta_sme.generate_proposal(
            target_module="agi.safety.critical",
            mod_type=ModificationType.SAFETY_RULE_UPDATE,
            description="Test proposal",
            ast_patch={'new_code': 'pass'},
            expected_impact={}
        )
        
        self.assertIsNone(proposal)
    
    def test_review_proposal(self):
        """测试审核提案"""
        proposal = self.meta_sme.generate_proposal(
            target_module="agi.drive_manager",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            description="Test proposal",
            ast_patch={'new_code': 'pass'},
            expected_impact={}
        )
        
        result = self.meta_sme.review_proposal(proposal.proposal_id, approved=True, reviewer="test")
        
        self.assertTrue(result)
        self.assertEqual(self.meta_sme.stats['proposals_approved'], 1)
    
    def test_get_status(self):
        """测试获取状态"""
        status = self.meta_sme.get_status()
        
        self.assertIn('stats', status)
        self.assertIn('num_proposals', status)
        self.assertIn('enable_auto_modify', status)


class TestMetaSMEDriveIntegration(unittest.TestCase):
    """测试 Meta-SME 驱动集成"""
    
    def setUp(self):
        self.meta_sme = MetaSME(
            enable_auto_modify=False,
            require_human_approval=True,
            sandbox_dir=".test_sandbox_int",
            backup_dir=".test_backups_int"
        )
        
        # Mock 驱动管理器
        class MockDrive:
            def __init__(self, name, weight=0.25):
                self.name = name
                self.weight = weight
        
        class MockDriveManager:
            def __init__(self):
                self.drives = {
                    'survival': MockDrive('survival', 0.2),
                    'curiosity': MockDrive('curiosity', 0.4)
                }
        
        self.drive_manager = MockDriveManager()
        self.integration = MetaSMEDriveIntegration(self.meta_sme, self.drive_manager)
    
    def tearDown(self):
        import shutil
        for dir_name in [".test_sandbox_int", ".test_backups_int"]:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
    
    def test_record_drive_performance(self):
        """测试记录驱动性能"""
        self.integration.record_drive_performance(
            'survival',
            avg_reward=0.5,
            activation_frequency=0.3,
            success_rate=0.7
        )
        
        self.assertIn('survival', self.integration.drive_performance_history)
        self.assertEqual(len(self.integration.drive_performance_history['survival']), 1)
    
    def test_analyze_drive_efficiency_insufficient_history(self):
        """测试历史不足时的分析"""
        analysis = self.integration.analyze_drive_efficiency('nonexistent')
        
        self.assertIn('error', analysis)
    
    def test_analyze_drive_efficiency(self):
        """测试驱动效率分析"""
        # 添加足够的历史
        for i in range(20):
            self.integration.record_drive_performance(
                'survival',
                avg_reward=0.5 + i * 0.01,
                activation_frequency=0.3,
                success_rate=0.7
            )
        
        analysis = self.integration.analyze_drive_efficiency('survival')
        
        self.assertNotIn('error', analysis)
        self.assertIn('efficiency_score', analysis)
        self.assertIn('recommendation', analysis)
    
    def test_propose_weight_adjustments(self):
        """测试提议权重调整"""
        # 添加历史数据
        for i in range(30):
            self.integration.record_drive_performance(
                'survival',
                avg_reward=0.3,  # 低性能
                activation_frequency=0.2,
                success_rate=0.4
            )
        
        proposals = self.integration.propose_weight_adjustments()
        
        # 应该生成至少一个提案（因为性能低）
        self.assertIsInstance(proposals, list)
    
    def test_get_status(self):
        """测试获取集成状态"""
        status = self.integration.get_status()
        
        self.assertIn('stats', status)
        self.assertIn('config', status)
        self.assertIn('meta_sme_status', status)


class TestEnvironmentAwareMetaSME(unittest.TestCase):
    """测试环境感知 Meta-SME"""
    
    def setUp(self):
        meta_sme = MetaSME(
            enable_auto_modify=False,
            require_human_approval=True
        )
        
        class MockDrive:
            def __init__(self, name, weight=0.25):
                self.name = name
                self.weight = weight
        
        class MockDriveManager:
            def __init__(self):
                self.drives = {'test': MockDrive('test')}
        
        drive_manager = MockDriveManager()
        integration = MetaSMEDriveIntegration(meta_sme, drive_manager)
        self.env_aware = EnvironmentAwareMetaSME(integration)
    
    def test_set_environment(self):
        """测试设置环境"""
        self.env_aware.set_environment('textworld')
        
        self.assertEqual(self.env_aware.current_environment, 'textworld')
        self.assertEqual(
            self.env_aware.integration.config['weight_adjustment_threshold'],
            0.03
        )
    
    def test_get_environment_config(self):
        """测试获取环境配置"""
        self.env_aware.set_environment('atari')
        config = self.env_aware.get_environment_config()
        
        self.assertEqual(config['environment'], 'atari')
        self.assertIn('config', config)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSandboxTester))
    suite.addTests(loader.loadTestsFromTestCase(TestPatchVerifier))
    suite.addTests(loader.loadTestsFromTestCase(TestRollbackManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMetaSME))
    suite.addTests(loader.loadTestsFromTestCase(TestMetaSMEDriveIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentAwareMetaSME))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)