#!/usr/bin/env python3
"""
测试MOSSInteractionAdapter参数转换器

验证功能：
1. v3.1 8D Agent参数格式转换
2. v9d Agent参数格式转换（继承v3.1）
3. v4.1 Agent参数格式转换（单参数格式）
4. 参数验证和错误处理
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any
import numpy as np

sys.path.insert(0, '.')
from moss_interaction_adapter import MOSSInteractionAdapter, DateTimeEncoder


class MockAgent:
    """模拟Agent类，用于测试适配器"""
    
    def __init__(self, version="v3.1"):
        self.version = version
        self.call_history = []
    
    def step(self, **kwargs):
        """模拟step方法调用"""
        self.call_history.append({
            'timestamp': datetime.now(),
            'args': kwargs,
            'version': self.version
        })
        
        # 返回模拟结果
        if self.version == "v4.1":
            return {
                'action': 'test_action',
                'success': True,
                'reward': 0.5,
                'purpose': 'Survival',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'step': len(self.call_history),
                'agent_id': 'mock_agent',
                'M': np.array([0.5, 0.5, 0.5, 0.5]),
                'weights': np.array([0.25, 0.25, 0.25, 0.25]),
                'state': 'normal'
            }


def test_v31_adapter():
    """测试v3.1 8D Agent适配器"""
    print("🧪 测试 v3.1 8D Agent 适配器")
    print("-" * 40)
    
    adapter = MOSSInteractionAdapter(agent_version="v3.1")
    mock_agent = MockAgent(version="v3.1")
    
    # 测试用例1: 完整观察数据
    observation1 = {
        "agent_id": "test_agent_001",
        "behavior": "explore",
        "result": "found_resource",
        "reward": 10.5,
        "context": {"environment": "forest", "temperature": "warm"},
        "timestamp": datetime.now()
    }
    
    adapted_params = adapter.adapt_observation_for_step(observation1)
    print(f"观察数据字段数: {len(observation1)}")
    print(f"适配参数类型: {type(adapted_params)}")
    print(f"包含observed_behaviors: {'observed_behaviors' in adapted_params}")
    print(f"包含interaction: {'interaction' in adapted_params}")
    
    # 验证必需的interaction字段
    interaction = adapted_params['interaction']
    required_fields = ["agent_id", "outcome", "payoff"]
    missing_fields = [field for field in required_fields if field not in interaction]
    
    if missing_fields:
        print(f"❌ 缺少必需字段: {missing_fields}")
        return False
    else:
        print(f"✅ 必需字段完整: {required_fields}")
    
    # 测试调用
    result = adapter.call_agent_step(mock_agent, observation1)
    print(f"调用结果类型: {type(result)}")
    print(f"MockAgent调用历史长度: {len(mock_agent.call_history)}")
    
    print("✅ v3.1适配器测试通过")
    return True


def test_v9d_adapter():
    """测试v9d Agent适配器"""
    print("\n🧪 测试 v9d Agent 适配器")
    print("-" * 40)
    
    adapter = MOSSInteractionAdapter(agent_version="v9d")
    mock_agent = MockAgent(version="v9d")
    
    # 测试用例
    observation = {
        "agent_id": "test_agent_002",
        "behavior": "cooperate",
        "result": "success",
        "reward": 8.2,
        "context": {"social_situation": "group_task"},
        "timestamp": datetime.now()
    }
    
    adapted_params = adapter.adapt_observation_for_step(observation)
    
    # 验证必需字段
    interaction = adapted_params['interaction']
    required_fields = ["agent_id", "outcome", "payoff"]
    missing_fields = [field for field in required_fields if field not in interaction]
    
    if missing_fields:
        print(f"❌ 缺少必需字段: {missing_fields}")
        return False
    else:
        print(f"✅ 必需字段完整: {required_fields}")
    
    # 测试调用
    result = adapter.call_agent_step(mock_agent, observation)
    print(f"调用成功: {result is not None}")
    
    print("✅ v9d适配器测试通过")
    return True


def test_v41_adapter():
    """测试v4.1 Agent适配器"""
    print("\n🧪 测试 v4.1 Agent 适配器")
    print("-" * 40)
    
    adapter = MOSSInteractionAdapter(agent_version="v4.1")
    mock_agent = MockAgent(version="v4.1")
    
    # 测试用例
    observation = {
        "agent_id": "test_agent_003",
        "resource": 0.75,
        "threat": 0.15,
        "novelty": 0.6,
        "progress": 0.4,
        "context": {"task_complexity": "high"},
        "timestamp": datetime.now()
    }
    
    adapted_params = adapter.adapt_observation_for_step(observation)
    print(f"适配参数类型: {type(adapted_params)}")
    print(f"包含observation字段: {'observation' in adapted_params}")
    
    # 验证v4.1特定的字段
    adapted_obs = adapted_params['observation']
    v41_fields = ["resource_level", "threat_level", "novelty", "goal_progress"]
    
    missing_fields = [field for field in v41_fields if field not in adapted_obs]
    
    if missing_fields:
        print(f"❌ 缺少v4.1必需字段: {missing_fields}")
        return False
    else:
        print(f"✅ v4.1必需字段完整: {v41_fields}")
    
    # 测试调用
    result = adapter.call_agent_step(mock_agent, observation)
    print(f"调用成功: {result is not None}")
    
    print("✅ v4.1适配器测试通过")
    return True


def test_validation():
    """测试参数验证功能"""
    print("\n🧪 测试参数验证功能")
    print("-" * 40)
    
    # 测试v3.1参数验证
    adapter = MOSSInteractionAdapter(agent_version="v3.1")
    
    # 完整参数
    good_interaction = {
        "agent_id": "test_id",
        "outcome": "success",
        "payoff": 10.5
    }
    
    # 缺失必需字段的参数
    bad_interaction = {
        "agent_id": "test_id",
        "outcome": "success"
        # 缺少payoff字段
    }
    
    good_valid = adapter.validate_interaction(good_interaction)
    bad_valid = adapter.validate_interaction(bad_interaction)
    
    print(f"完整参数验证: {'✅ 通过' if good_valid else '❌ 失败'}")
    print(f"缺失参数验证: {'✅ 通过' if bad_valid else '❌ 失败'}")
    
    if good_valid and not bad_valid:
        print("✅ 参数验证功能正常")
        return True
    else:
        print("❌ 参数验证功能异常")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n🧪 测试错误处理功能")
    print("-" * 40)
    
    try:
        # 使用未知版本
        adapter = MOSSInteractionAdapter(agent_version="unknown_version")
        
        observation = {"test": "data"}
        adapted_params = adapter.adapt_observation_for_step(observation)
        
        # 应该回退到v3.1格式
        if 'interaction' in adapted_params:
            print("✅ 未知版本正确处理，回退到v3.1格式")
            return True
        else:
            print("❌ 未知版本处理异常")
            return False
            
    except Exception as e:
        print(f"❌ 错误处理异常: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 70)
    print("🔬 MOSSInteractionAdapter 综合测试套件")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 5
    
    # 运行所有测试
    test_functions = [
        test_v31_adapter,
        test_v9d_adapter,
        test_v41_adapter,
        test_validation,
        test_error_handling
    ]
    
    for test_func in test_functions:
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 70)
    print(f"测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！适配器功能正常。")
        return True
    else:
        print("⚠️  部分测试失败，需要检查适配器实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)