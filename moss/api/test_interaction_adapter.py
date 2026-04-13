"""
MOSS Interaction Adapter 测试脚本

测试参数转换器的功能和兼容性

作者：AI Assistant
日期：2026-04-13
"""

import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moss.api.interaction_adapter import MOSSInteractionAdapter, create_unified_agent_adapter
from moss.api.adapter import MOSSApiAdapter, create_unified_agent


# 模拟Agent类
class MockV31Agent:
    """模拟 v3.1 Agent (社交参数范式)"""
    def __init__(self, agent_id="test_v31"):
        self.agent_id = agent_id
        self.step_count = 0
        self.purpose_generator = type('MockPurposeGen', (), {
            'purpose_vector': np.array([0.25]*9),
            'purpose_statement': "I am a v3.1 agent"
        })()
        self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        
    def step(self, observed_behaviors=None, interaction=None):
        """v3.1 Agent的step方法 (接收社交参数)"""
        self.step_count += 1
        return {
            'agent_id': self.agent_id,
            'step': self.step_count,
            'observed_behaviors': observed_behaviors,
            'interaction': interaction,
            'result': 'v3.1_success',
            'weights': self.weights.tolist()
        }
        
    def get_full_report(self):
        return {'agent_type': 'v3.1', 'agent_id': self.agent_id}


class MockV41Agent:
    """模拟 v4.1 Agent (环境观察范式)"""
    def __init__(self, agent_id="test_v41"):
        self.agent_id = agent_id
        self.step_count = 0
        self.world_model = type('MockWorldModel', (), {})()
        self.goal_manager = type('MockGoalManager', (), {})()
        self.coherence_score = 0.8
        self.valence_profile = [0.3, 0.2, 0.3, 0.2]
        self.purpose_state = type('MockPurposeState', (), {
            'survival': 0.4,
            'curiosity': 0.2,
            'influence': 0.3,
            'optimization': 0.1,
            'purpose_statement': "I am a v4.1 agent"
        })()
        
    def step(self, observation=None):
        """v4.1 Agent的step方法 (接收环境观察)"""
        self.step_count += 1
        return {
            'agent_id': self.agent_id,
            'step': self.step_count,
            'observation': observation,
            'result': 'v4.1_success'
        }


class MockV50Agent:
    """模拟 v5.0 Agent (统一Agent)"""
    def __init__(self, agent_id="test_v50"):
        self.agent_id = agent_id
        self.step_count = 0
        self._purpose_generator = type('MockPurposeGen', (), {
            'purpose_vector': np.array([0.2, 0.3, 0.2, 0.1, 0.1, 0.05, 0.02, 0.02, 0.01]),
            'purpose_statement': "I am a unified agent"
        })()
        self.weights = np.array([0.3, 0.2, 0.3, 0.2])
        
    def _get_purpose_vector(self):
        return self._purpose_generator.purpose_vector
        
    def step(self, observation=None):
        """v5.0 Agent的step方法 (接收环境观察)"""
        self.step_count += 1
        return {
            'agent_id': self.agent_id,
            'step': self.step_count,
            'observation': observation,
            'result': 'v5.0_success',
            'purpose_vector': self._get_purpose_vector().tolist()
        }


def test_parameter_conversion():
    """测试参数转换功能"""
    print("=" * 70)
    print("MOSS Interaction Adapter 参数转换测试")
    print("=" * 70)
    
    adapter = MOSSInteractionAdapter(agent_type='auto')
    
    # 测试数据
    observation_data = {
        'other_agents': {
            'agent_B': {
                'action': 'cooperate',
                'reward': 0.8,
                'weights': [0.3, 0.2, 0.3, 0.2]
            }
        },
        'interaction': {
            'agent_id': 'agent_B',
            'outcome': 'cooperate',
            'payoff': 0.7
        },
        'resource_level': 0.9,
        'threat_level': 0.1
    }
    
    observed_behaviors_data = {
        'agent_C': {
            'action': 'explore',
            'reward': 0.5,
            'weights': [0.25, 0.25, 0.25, 0.25]
        }
    }
    
    interaction_data = {
        'agent_id': 'agent_C',
        'outcome': 'defect',
        'payoff': 0.3
    }
    
    # 测试1：observation -> v3.1参数转换
    print("\n1. Observation -> v3.1参数转换测试")
    observed_behaviors_conv, interaction_conv = adapter.convert_to_v31_format(observation_data)
    print(f"   原始observation: 包含{len(observation_data.get('other_agents', {}))}个他者Agent")
    print(f"   转换后observed_behaviors: {len(observed_behaviors_conv) if observed_behaviors_conv else 0}个行为")
    print(f"   转换后interaction: {interaction_conv}")
    
    # 测试2：v3.1参数 -> observation转换
    print("\n2. v3.1参数 -> Observation转换测试")
    observation_conv = adapter.convert_to_v4x_format(observed_behaviors_data, interaction_data)
    print(f"   原始observed_behaviors: {len(observed_behaviors_data)}个行为")
    print(f"   原始interaction: {interaction_data}")
    print(f"   转换后observation: 包含other_agents={len(observation_conv.get('other_agents', {}))}个")
    
    return True


def test_agent_detection():
    """测试Agent类型检测"""
    print("\n" + "=" * 70)
    print("Agent类型检测测试")
    print("=" * 70)
    
    # 创建不同版本的Agent
    v31_agent = MockV31Agent()
    v41_agent = MockV41Agent()
    v50_agent = MockV50Agent()
    
    # 创建适配器
    adapter = MOSSInteractionAdapter(agent_type='auto')
    
    # 检测Agent类型
    v31_type = adapter.detect_agent_from_instance(v31_agent)
    v41_type = adapter.detect_agent_from_instance(v41_agent)
    v50_type = adapter.detect_agent_from_instance(v50_agent)
    
    print(f"v3.1 Agent检测结果: {v31_type} (预期: v3.1)")
    print(f"v4.1 Agent检测结果: {v41_type} (预期: v4.1)")
    print(f"v5.0 Agent检测结果: {v50_type} (预期: v5.0)")
    
    return (v31_type == 'v3.1') and (v41_type == 'v4.1') and (v50_type == 'v5.0')


def test_api_adapter_compatibility():
    """测试API适配器的兼容性"""
    print("\n" + "=" * 70)
    print("API适配器兼容性测试")
    print("=" * 70)
    
    # 创建不同版本的Agent
    v31_agent = MockV31Agent("v31_compat_test")
    v41_agent = MockV41Agent("v41_compat_test")
    v50_agent = MockV50Agent("v50_compat_test")
    
    # 创建API适配器
    adapter_v31 = MOSSApiAdapter(v31_agent)
    adapter_v41 = MOSSApiAdapter(v41_agent)
    adapter_v50 = MOSSApiAdapter(v50_agent)
    
    # 测试参数获取
    print("\n1. Purpose向量获取测试:")
    purpose_v31 = adapter_v31.get_purpose_vector()
    purpose_v41 = adapter_v41.get_purpose_vector()
    purpose_v50 = adapter_v50.get_purpose_vector()
    
    print(f"   v3.1 Purpose向量: {purpose_v31 is not None}")
    print(f"   v4.1 Purpose向量: {purpose_v41 is not None}")
    print(f"   v5.0 Purpose向量: {purpose_v50 is not None}")
    
    # 测试Agent信息获取
    print("\n2. Agent信息获取测试:")
    info_v31 = adapter_v31.get_agent_info()
    info_v41 = adapter_v41.get_agent_info()
    info_v50 = adapter_v50.get_agent_info()
    
    print(f"   v3.1 Agent类型: {info_v31['agent_type']}")
    print(f"   v4.1 Agent类型: {info_v41['agent_type']}")
    print(f"   v5.0 Agent类型: {info_v50['agent_type']}")
    
    return True


def test_unified_step_calls():
    """测试统一的step方法调用"""
    print("\n" + "=" * 70)
    print("统一step方法调用测试")
    print("=" * 70)
    
    # 创建不同版本的Agent
    v31_agent = MockV31Agent("v31_step_test")
    v41_agent = MockV41Agent("v41_step_test")
    v50_agent = MockV50Agent("v50_step_test")
    
    # 创建API适配器
    adapter_v31 = MOSSApiAdapter(v31_agent)
    adapter_v41 = MOSSApiAdapter(v41_agent)
    adapter_v50 = MOSSApiAdapter(v50_agent)
    
    # 测试数据
    observation = {'resource_level': 0.8, 'threat_level': 0.2}
    observed_behaviors = {'agent_X': {'action': 'help', 'reward': 0.9, 'weights': [0.4, 0.1, 0.3, 0.2]}}
    interaction = {'agent_id': 'agent_X', 'outcome': 'cooperate', 'payoff': 0.8}
    
    print("\n1. 使用observation参数调用:")
    try:
        result_v31 = adapter_v31.step(observation=observation)
        print(f"   v3.1 Agent: {result_v31['result']} (step {result_v31['step']})")
    except Exception as e:
        print(f"   v3.1 Agent: 失败 - {e}")
        
    try:
        result_v41 = adapter_v41.step(observation=observation)
        print(f"   v4.1 Agent: {result_v41['result']} (step {result_v41['step']})")
    except Exception as e:
        print(f"   v4.1 Agent: 失败 - {e}")
        
    try:
        result_v50 = adapter_v50.step(observation=observation)
        print(f"   v5.0 Agent: {result_v50['result']} (step {result_v50['step']})")
    except Exception as e:
        print(f"   v5.0 Agent: 失败 - {e}")
    
    print("\n2. 使用社交参数调用:")
    try:
        result_v31 = adapter_v31.step(observed_behaviors=observed_behaviors, interaction=interaction)
        print(f"   v3.1 Agent: {result_v31['result']} (step {result_v31['step']})")
    except Exception as e:
        print(f"   v3.1 Agent: 失败 - {e}")
        
    try:
        result_v41 = adapter_v41.step(observed_behaviors=observed_behaviors, interaction=interaction)
        print(f"   v4.1 Agent: {result_v41['result']} (step {result_v41['step']})")
    except Exception as e:
        print(f"   v4.1 Agent: 失败 - {e}")
        
    try:
        result_v50 = adapter_v50.step(observed_behaviors=observed_behaviors, interaction=interaction)
        print(f"   v5.0 Agent: {result_v50['result']} (step {result_v50['step']})")
    except Exception as e:
        print(f"   v5.0 Agent: 失败 - {e}")
    
    print("\n3. 无参数调用:")
    try:
        result_v31 = adapter_v31.step()
        print(f"   v3.1 Agent: {result_v31['result']} (step {result_v31['step']})")
    except Exception as e:
        print(f"   v3.1 Agent: 失败 - {e}")
        
    try:
        result_v41 = adapter_v41.step()
        print(f"   v4.1 Agent: {result_v41['result']} (step {result_v41['step']})")
    except Exception as e:
        print(f"   v4.1 Agent: 失败 - {e}")
        
    try:
        result_v50 = adapter_v50.step()
        print(f"   v5.0 Agent: {result_v50['result']} (step {result_v50['step']})")
    except Exception as e:
        print(f"   v5.0 Agent: 失败 - {e}")
    
    return True


def main():
    """主测试函数"""
    print("🚀 MOSS Interaction Adapter 完整测试套件")
    print("=" * 70)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("参数转换测试", test_parameter_conversion()))
    test_results.append(("Agent类型检测测试", test_agent_detection()))
    test_results.append(("API适配器兼容性测试", test_api_adapter_compatibility()))
    test_results.append(("统一step方法调用测试", test_unified_step_calls()))
    
    # 输出测试结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有测试通过！参数转换器功能正常。")
    else:
        print("⚠️  部分测试失败，请检查问题。")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)