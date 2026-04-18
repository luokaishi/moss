"""
Tests for TextWorld Adapter - TextWorld 适配器测试

测试模块:
- moss/benchmarks/textworld_adapter.py
- moss/benchmarks/reward_mapping.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import numpy as np
from pathlib import Path

# 尝试导入 TextWorld 组件
try:
    from moss.benchmarks.textworld_adapter import TextWorldAdapter, TextWorldState
    from moss.benchmarks.reward_mapping import TextWorldRewardMapper, DriveReward, RewardContext
    TEXTWORLD_AVAILABLE = True
except ImportError:
    TEXTWORLD_AVAILABLE = False


@unittest.skipUnless(TEXTWORLD_AVAILABLE, "TextWorld not available")
class TestTextWorldAdapter(unittest.TestCase):
    """测试 TextWorldAdapter 类"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = TextWorldAdapter(game_file_or_name='simple', mode='gym')
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.adapter)
        self.assertEqual(self.adapter.game_type, 'simple')
        self.assertEqual(self.adapter.difficulty, 'easy')
    
    def test_state_dimension(self):
        """测试状态向量维度"""
        state = self.adapter.get_state_vector()
        self.assertEqual(len(state), 12)
        self.assertIsInstance(state, np.ndarray)
    
    def test_state_normalization(self):
        """测试状态向量归一化"""
        state = self.adapter.get_state_vector()
        # 检查值范围
        self.assertTrue(np.all(state >= 0))
        self.assertTrue(np.all(state <= 1))
    
    def test_available_actions(self):
        """测试可用动作"""
        actions = self.adapter.get_available_actions()
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
    
    def test_action_parsing(self):
        """测试动作解析"""
        # 测试导航动作
        parsed = self.adapter._parse_action('go north')
        self.assertIsInstance(parsed, str)
        
        # 测试查看动作
        parsed = self.adapter._parse_action('look')
        self.assertIsInstance(parsed, str)
    
    def test_reset(self):
        """测试环境重置"""
        obs = self.adapter.reset()
        self.assertIsInstance(obs, str)
        self.assertGreater(len(obs), 0)
    
    def test_step_structure(self):
        """测试 step 返回值结构"""
        self.adapter.reset()
        
        obs, reward, done, info = self.adapter.step('look')
        
        self.assertIsInstance(obs, str)
        self.assertIsInstance(reward, (int, float))
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)


@unittest.skipUnless(TEXTWORLD_AVAILABLE, "TextWorld not available")
class TestTextWorldRewardMapper(unittest.TestCase):
    """测试 TextWorldRewardMapper 类"""
    
    def setUp(self):
        """设置测试环境"""
        self.mapper = TextWorldRewardMapper()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.mapper)
        self.assertIn('survival', self.mapper.drive_weights)
        self.assertIn('optimization', self.mapper.drive_weights)
    
    def test_reward_mapping(self):
        """测试奖励映射"""
        drive_rewards = self.mapper.map_reward(
            tw_reward=1.0,
            info={'score': 10, 'won': False}
        )
        
        self.assertIsInstance(drive_rewards, list)
        self.assertGreater(len(drive_rewards), 0)
        
        for reward in drive_rewards:
            self.assertIsInstance(reward, DriveReward)
            self.assertIn(reward.drive_name, ['survival', 'optimization', 'curiosity', 'influence'])
    
    def test_context_update(self):
        """测试上下文更新"""
        self.mapper.update_context(
            current_score=10.0,
            steps_taken=5,
            rooms_visited=2
        )
        
        self.assertEqual(self.mapper.context.current_score, 10.0)
        self.assertEqual(self.mapper.context.steps_taken, 5)
    
    def test_custom_weights(self):
        """测试自定义权重"""
        custom_weights = {
            'survival': 0.4,
            'optimization': 0.3,
            'curiosity': 0.2,
            'influence': 0.1,
        }
        mapper = TextWorldRewardMapper(drive_weights=custom_weights)
        
        self.assertEqual(mapper.drive_weights['survival'], 0.4)
        self.assertEqual(mapper.drive_weights['optimization'], 0.3)


class TestTextWorldState(unittest.TestCase):
    """测试 TextWorldState 数据结构"""
    
    def test_initialization(self):
        """测试初始化"""
        state = TextWorldState()
        
        self.assertEqual(state.observation, "")
        self.assertEqual(state.score, 0.0)
        self.assertEqual(state.moves, 0)
        self.assertFalse(state.done)
    
    def test_to_dict(self):
        """测试转换为字典"""
        state = TextWorldState(
            observation="You are in a room.",
            score=10.0,
            moves=5
        )
        
        data = state.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['observation'], "You are in a room.")
        self.assertEqual(data['score'], 10.0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @unittest.skipUnless(TEXTWORLD_AVAILABLE, "TextWorld not available")
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 创建适配器
        adapter = TextWorldAdapter(game_type='simple', difficulty='easy')
        
        # 创建奖励映射器
        mapper = TextWorldRewardMapper()
        
        # 重置环境
        obs = adapter.reset()
        self.assertIsNotNone(obs)
        
        # 执行几个动作
        for action in ['look', 'inventory']:
            if action in adapter.get_available_actions():
                obs, reward, done, info = adapter.step(action)
                
                # 映射奖励
                drive_rewards = mapper.map_reward(reward, info)
                self.assertIsInstance(drive_rewards, list)
                
                if done:
                    break
        
        # 获取最终状态
        state = adapter.get_state_vector()
        self.assertEqual(len(state), 12)


if __name__ == '__main__':
    unittest.main()
