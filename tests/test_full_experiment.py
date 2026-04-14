#!/usr/bin/env python3
"""
MOSS完整实验系统测试

测试整个MOSS多Agent系统，包括：
1. 参数转换器集成
2. 多版本Agent兼容性
3. 实验框架功能
4. 错误恢复机制
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# 添加项目路径
project_root = "C:/Users/LX/WorkBuddy/20260409105630"
sys.path.insert(0, project_root)
sys.path.insert(0, f"{project_root}/moss")
sys.path.insert(0, f"{project_root}/moss/api")

# 导入我们创建的模块
try:
    from moss.api.adapter import MOSSApiAdapter, create_unified_agent
    print("✅ API适配器导入成功")
except ImportError as e:
    print(f"❌ API适配器导入失败: {e}")
    sys.exit(1)

try:
    from moss.api.interaction_adapter_enhanced import MOSSInteractionAdapter, create_unified_agent_adapter
    print("✅ 增强版参数转换器导入成功")
except ImportError as e:
    print(f"⚠️  增强版参数转换器导入失败: {e}")
    try:
        from moss.api.interaction_adapter import MOSSInteractionAdapter, create_unified_agent_adapter
        print("✅ 普通版参数转换器导入成功")
    except ImportError as e2:
        print(f"❌ 参数转换器导入失败: {e2}")
        sys.exit(1)


class MockV31Agent:
    """模拟v3.1 8D Agent"""
    def __init__(self, agent_id: str = "mock_v31_agent"):
        self.agent_id = agent_id
        self.step_count = 0
        self.enable_social = True
        self.purpose_generator = type('obj', (object,), {
            'purpose_vector': [0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.5, 0.5, 0.1]
        })()
        
    def step(self, observed_behaviors: Optional[Dict] = None, interaction: Optional[Dict] = None) -> Dict:
        self.step_count += 1
        
        # 模拟8维Agent的step方法
        M_base = np.array([0.5, 0.5, 0.5, 0.5])
        coherence = np.random.random()
        valence = np.random.random()
        
        # 如果有社交参数，处理社交维度
        other_val = 0.0
        norm_val = 0.0
        if self.enable_social and interaction:
            if interaction.get('outcome') == 'cooperate':
                other_val = 0.7
                norm_val = 0.8
            else:
                other_val = 0.3
                norm_val = 0.2
        
        # 构建8维向量
        M_vector = np.concatenate([M_base, [coherence, valence, other_val, norm_val]])
        
        return {
            'step': self.step_count,
            'agent_id': self.agent_id,
            'M': M_vector.tolist(),
            'weights': [0.25, 0.25, 0.25, 0.25],
            'state': 'normal'
        }


class MockV41Agent:
    """模拟v4.1 Agent"""
    def __init__(self, agent_id: str = "mock_v41_agent"):
        self.agent_id = agent_id
        self.step_count = 0
        self.world_model = type('obj', (object,), {})()
        self.goal_manager = type('obj', (object,), {})()
        self.coherence_score = 0.5
        self.valence_profile = [0.25, 0.25, 0.25, 0.25]
        self.purpose_state = type('obj', (object,), {
            'survival': 0.3,
            'curiosity': 0.3,
            'influence': 0.2,
            'optimization': 0.2,
            'purpose_statement': "I am a mock v4.1 agent"
        })()
        
    def step(self, observation: Optional[Dict] = None) -> Dict:
        self.step_count += 1
        
        # 模拟v4.1 Agent的step方法
        if observation and 'resource_level' in observation:
            # 根据观察数据模拟决策
            resource = observation.get('resource_level', 0.5)
            threat = observation.get('threat_level', 0.3)
            
            # 模拟成功概率
            success_prob = 0.8 - threat * 0.3 + resource * 0.2
            success = np.random.random() < success_prob
            
            reward = np.random.random() * 0.5 if success else 0.0
            
            return {
                'action': 'simulated_action',
                'success': success,
                'reward': reward,
                'purpose': 'Simulation',
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'action': 'wait',
            'success': True,
            'reward': 0.0,
            'purpose': 'Default',
            'timestamp': datetime.now().isoformat()
        }


def test_parameter_conversion():
    """测试参数格式转换"""
    print("\n🔧 参数格式转换测试")
    print("-" * 50)
    
    # 创建适配器
    adapter_v31 = MOSSInteractionAdapter(agent_type="v3.1")
    adapter_v41 = MOSSInteractionAdapter(agent_type="v4.1")
    
    # 测试数据
    test_observation = {
        "agent_id": "test_agent_001",
        "behavior": "explore",
        "result": "found_resource",
        "reward": 10.5,
        "resource": 0.8,
        "threat": 0.2,
        "novelty": 0.4,
        "progress": 0.3,
        "context": {"environment": "forest", "time_of_day": "day"},
        "timestamp": datetime.now().isoformat()
    }
    
    print("1. v3.1格式转换:")
    observed_behaviors, interaction = adapter_v31.convert_to_v31_format(test_observation)
    
    # 验证v3.1必需字段
    required_fields = ["agent_id", "outcome", "payoff"]
    missing = [field for field in required_fields if field not in interaction]
    
    if missing:
        print(f"   ❌ 缺少必需字段: {missing}")
        return False
    else:
        print(f"   ✅ 必需字段完整")
        print(f"     agent_id: {interaction['agent_id']}")
        print(f"     outcome: {interaction['outcome']}")
        print(f"     payoff: {interaction['payoff']}")
    
    print("\n2. v4.1格式转换:")
    v41_observation = adapter_v41.prepare_v41_observation(test_observation)
    
    # 检查v4.1特定字段
    v41_fields = ["resource_level", "threat_level", "novelty", "goal_progress"]
    missing_fields = [field for field in v41_fields if field not in v41_observation]
    
    if missing_fields:
        print(f"   ❌ 缺少v4.1字段: {missing_fields}")
        return False
    else:
        print(f"   ✅ v4.1必需字段完整")
        for field in v41_fields:
            print(f"     {field}: {v41_observation[field]}")
    
    return True


def test_agent_compatibility():
    """测试多版本Agent兼容性"""
    print("\n🤝 多版本Agent兼容性测试")
    print("-" * 50)
    
    # 创建模拟Agent
    mock_v31 = MockV31Agent("test_v31_agent")
    mock_v41 = MockV41Agent("test_v41_agent")
    
    # 创建API适配器
    adapter_v31 = MOSSApiAdapter(mock_v31)
    adapter_v41 = MOSSApiAdapter(mock_v41)
    
    print("1. v3.1 Agent测试:")
    try:
        # 测试step方法（使用通用observation格式）
        test_observation = {
            "agent_id": "test_v31",
            "behavior": "cooperate",
            "result": "success",
            "reward": 8.5
        }
        
        result = adapter_v31.step(observation=test_observation)
        print(f"   ✅ v3.1 Agent step成功")
        print(f"     结果: {result}")
    except Exception as e:
        print(f"   ❌ v3.1 Agent step失败: {e}")
        return False
    
    print("\n2. v4.1 Agent测试:")
    try:
        # 测试step方法（使用v4.1格式）
        test_observation = {
            "resource_level": 0.8,
            "threat_level": 0.2,
            "novelty": 0.5,
            "goal_progress": 0.3
        }
        
        result = adapter_v41.step(observation=test_observation)
        print(f"   ✅ v4.1 Agent step成功")
        print(f"     结果: {result}")
    except Exception as e:
        print(f"   ❌ v4.1 Agent step失败: {e}")
        return False
    
    return True


def test_error_recovery():
    """测试错误恢复机制"""
    print("\n🔄 错误恢复机制测试")
    print("-" * 50)
    
    # 创建带有错误处理的Agent
    class FaultyAgent:
        def __init__(self, failure_rate=0.3):
            self.step_count = 0
            self.failure_rate = failure_rate
            self.recovery_attempts = 0
            
        def step(self, **kwargs):
            self.step_count += 1
            
            # 模拟随机失败
            if np.random.random() < self.failure_rate and self.step_count % 3 == 0:
                raise RuntimeError(f"Step {self.step_count}: Simulated failure")
            
            # 如果之前有恢复尝试，模拟成功恢复
            if self.recovery_attempts > 0:
                success_rate = min(1.0, 0.7 + self.recovery_attempts * 0.1)
                success = np.random.random() < success_rate
                if success:
                    self.recovery_attempts = 0
                return {
                    'step': self.step_count,
                    'success': success,
                    'recovery_attempts': self.recovery_attempts,
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'step': self.step_count,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
    
    faulty_agent = FaultyAgent()
    adapter = MOSSApiAdapter(faulty_agent)
    
    print("1. 错误注入和恢复测试:")
    
    successful_steps = 0
    total_steps = 10
    
    for i in range(total_steps):
        try:
            test_data = {"step": i + 1}
            result = adapter.step(observation=test_data)
            
            if result.get('success', False):
                successful_steps += 1
                print(f"   Step {i+1}: ✅ 成功")
            else:
                print(f"   Step {i+1}: ⚠️  恢复中...")
                
        except Exception as e:
            print(f"   Step {i+1}: ❌ 失败 - {e}")
    
    success_rate = successful_steps / total_steps
    print(f"\n   成功率: {successful_steps}/{total_steps} ({success_rate:.1%})")
    
    if success_rate >= 0.7:
        print("   ✅ 错误恢复机制基本正常")
        return True
    else:
        print("   ⚠️  错误恢复机制需要改进")
        return False


def test_full_system():
    """测试完整系统"""
    print("\n🚀 完整系统测试")
    print("-" * 50)
    
    # 创建一个多Agent系统
    agents = [
        MockV31Agent("agent_01"),
        MockV31Agent("agent_02"),
        MockV41Agent("agent_03"),
        MockV41Agent("agent_04")
    ]
    
    adapters = [MOSSApiAdapter(agent) for agent in agents]
    
    print("1. 并行Agent执行:")
    total_steps = 5
    successful_interactions = 0
    
    for step in range(total_steps):
        print(f"\n   第 {step+1} 步:")
        
        for i, adapter in enumerate(adapters):
            try:
                # 创建不同的观察数据
                obs_data = {
                    "agent_id": agents[i].agent_id,
                    "step": step + 1,
                    "resource": np.random.random(),
                    "threat": np.random.random() * 0.5
                }
                
                result = adapter.step(observation=obs_data)
                
                if result.get('success', False):
                    successful_interactions += 1
                    print(f"     Agent {i+1} ({agents[i].__class__.__name__}): ✅")
                else:
                    print(f"     Agent {i+1} ({agents[i].__class__.__name__}): ⚠️")
                    
            except Exception as e:
                print(f"     Agent {i+1} ({agents[i].__class__.__name__}): ❌ - {e}")
    
    total_interactions = total_steps * len(agents)
    success_rate = successful_interactions / total_interactions
    
    print(f"\n   总交互: {total_interactions}")
    print(f"   成功交互: {successful_interactions}")
    print(f"   成功率: {success_rate:.1%}")
    
    if success_rate >= 0.6:
        print("   ✅ 完整系统测试通过")
        return True
    else:
        print("   ⚠️  系统需要进一步优化")
        return False


def main():
    """主测试函数"""
    print("=" * 70)
    print("🔬 MOSS 完整实验系统综合测试")
    print("=" * 70)
    
    print(f"Python版本: {sys.version}")
    print(f"项目根目录: {project_root}")
    
    tests = [
        ("参数格式转换", test_parameter_conversion),
        ("多版本Agent兼容性", test_agent_compatibility),
        ("错误恢复机制", test_error_recovery),
        ("完整系统", test_full_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 开始测试: {test_name}")
        
        start_time = time.time()
        
        try:
            success = test_func()
            elapsed = time.time() - start_time
            
            if success:
                print(f"✅ {test_name} 测试通过 ({elapsed:.2f}s)")
                results.append((test_name, True))
            else:
                print(f"❌ {test_name} 测试失败 ({elapsed:.2f}s)")
                results.append((test_name, False))
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {test_name} 测试异常 ({elapsed:.2f}s): {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 最终测试结果")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"测试总数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"成功率: {passed/total:.1%}")
    
    print("\n详细结果:")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 所有测试通过！MOSS实验系统完整可用。")
        return 0
    elif passed >= total * 0.7:
        print("\n⚠️  大部分测试通过，建议进一步优化失败的测试项。")
        return 1
    else:
        print("\n❌ 多个测试失败，需要修复系统实现。")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)