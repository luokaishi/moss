#!/usr/bin/env python3
"""
v4.1 Agent 功能测试脚本

测试修复后的v4.1 Agent功能，包括：
1. 模块导入
2. Agent创建
3. step方法调用
4. 参数转换器集成

运行: python scripts/test_v4_agent.py
"""

import sys
import os
from pathlib import Path

def setup_paths():
    """设置项目路径"""
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / '_archive_v4'))
    sys.path.insert(0, str(project_root / '_archive_v4' / 'core'))
    sys.path.insert(0, str(project_root / '_archive_v4' / 'integration'))
    sys.path.insert(0, str(project_root / '_archive_v3' / 'core'))
    
    return project_root

def test_module_imports():
    """测试模块导入"""
    print("\n1. 测试模块导入...")
    
    try:
        # 测试v4.0模块导入
        from world_model import WorldModel
        print("   ✅ world_model 导入成功")
    except ImportError as e:
        print(f"   ❌ world_model 导入失败: {e}")
        return False
    
    try:
        from llm_reasoning import LLMReasoningLayer
        print("   ✅ llm_reasoning 导入成功")
    except ImportError as e:
        print(f"   ❌ llm_reasoning 导入失败: {e}")
        return False
    
    try:
        from open_goal_space import GoalManager
        print("   ✅ open_goal_space 导入成功")
    except ImportError as e:
        print(f"   ❌ open_goal_space 导入失败: {e}")
        return False
    
    return True

def test_v41_agent_creation():
    """测试v4.1 Agent创建"""
    print("\n2. 测试v4.1 Agent创建...")
    
    try:
        # 尝试导入修复版本的v4.1 Agent
        from agent_v4_1_fixed import PurposeEnhancedAgent
        
        # 创建Agent实例
        agent = PurposeEnhancedAgent(agent_id="test_v41")
        print(f"   ✅ v4.1 Agent创建成功: {agent.agent_id}")
        
        # 检查Agent属性
        required_attrs = ['agent_id', 'step_count', 'purpose_state', 'world_model', 'goal_manager']
        for attr in required_attrs:
            if hasattr(agent, attr):
                print(f"   ✅ 属性 {attr}: 存在")
            else:
                print(f"   ⚠️  属性 {attr}: 不存在")
        
        return agent
        
    except ImportError as e:
        print(f"   ❌ v4.1 Agent导入失败: {e}")
        return None
    except Exception as e:
        print(f"   ❌ v4.1 Agent创建失败: {e}")
        return None

def test_agent_step_method(agent):
    """测试Agent的step方法"""
    print("\n3. 测试Agent step方法...")
    
    if agent is None:
        print("   ❌ 无法测试，Agent未创建")
        return False
    
    try:
        # 测试无参数调用
        result1 = agent.step()
        print(f"   ✅ 无参数step调用成功: step={result1.get('step_count', 'unknown')}")
    except Exception as e:
        print(f"   ❌ 无参数step调用失败: {e}")
        return False
    
    try:
        # 测试带observation参数调用
        observation = {
            'resource_level': 0.8,
            'threat_level': 0.2,
            'social_opportunity': True
        }
        result2 = agent.step(observation)
        print(f"   ✅ observation参数step调用成功: step={result2.get('step_count', 'unknown')}")
    except Exception as e:
        print(f"   ❌ observation参数step调用失败: {e}")
        return False
    
    return True

def test_parameter_adapter_integration():
    """测试参数转换器集成"""
    print("\n4. 测试参数转换器集成...")
    
    try:
        # 导入参数转换器
        sys.path.insert(0, str(Path(__file__).parent.parent / 'moss' / 'api'))
        from interaction_adapter import MOSSInteractionAdapter
        
        adapter = MOSSInteractionAdapter()
        print("   ✅ 参数转换器创建成功")
        
        # 测试参数转换
        observation = {
            'other_agents': {
                'agent_B': {'action': 'cooperate', 'reward': 0.8, 'weights': [0.3, 0.2, 0.3, 0.2]}
            },
            'interaction': {'agent_id': 'agent_B', 'outcome': 'cooperate', 'payoff': 0.7}
        }
        
        observed_behaviors, interaction = adapter.convert_to_v31_format(observation)
        if observed_behaviors:
            print(f"   ✅ observation->v3.1参数转换成功: {len(observed_behaviors)}个行为")
        else:
            print("   ❌ observation->v3.1参数转换失败")
            return False
        
        # 测试反向转换
        observation_back = adapter.convert_to_v4x_format(observed_behaviors, interaction)
        if 'other_agents' in observation_back:
            print(f"   ✅ v3.1参数->observation转换成功")
        else:
            print("   ❌ v3.1参数->observation转换失败")
            return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ 参数转换器导入失败: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 参数转换器测试失败: {e}")
        return False

def test_api_adapter_compatibility():
    """测试API适配器兼容性"""
    print("\n5. 测试API适配器兼容性...")
    
    try:
        # 导入API适配器
        from moss.api.adapter import MOSSApiAdapter, create_unified_agent
        
        # 创建模拟Agent
        class MockAgent:
            def __init__(self):
                self.agent_id = "test_api_agent"
                self.step_count = 0
                
            def step(self, observation=None):
                self.step_count += 1
                return {'step': self.step_count, 'result': 'success'}
        
        mock_agent = MockAgent()
        adapter = create_unified_agent(mock_agent)
        
        print(f"   ✅ API适配器创建成功: 类型={adapter.agent_type}")
        
        # 测试适配器的step方法
        result = adapter.step(observation={'test': 'data'})
        print(f"   ✅ 适配器step调用成功: {result}")
        
        # 获取Agent信息
        info = adapter.get_agent_info()
        print(f"   ✅ Agent信息获取成功: {info.get('agent_id')}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ API适配器导入失败: {e}")
        return False
    except Exception as e:
        print(f"   ❌ API适配器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 70)
    print("MOSS v4.1 Agent 功能测试")
    print("=" * 70)
    
    # 设置路径
    project_root = setup_paths()
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("模块导入测试", test_module_imports()))
    
    agent = test_v41_agent_creation()
    test_results.append(("Agent创建测试", agent is not None))
    
    if agent:
        test_results.append(("Step方法测试", test_agent_step_method(agent)))
    
    test_results.append(("参数转换器集成测试", test_parameter_adapter_integration()))
    test_results.append(("API适配器兼容性测试", test_api_adapter_compatibility()))
    
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
        print("🎉 所有测试通过！v4.1 Agent功能正常。")
        print("🎯 参数转换器集成成功，可以处理不同版本Agent的参数格式。")
    else:
        print("⚠️  部分测试失败，请检查依赖和代码。")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)