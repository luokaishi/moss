"""
测试MOSS API适配器

验证不同版本Agent的API兼容性
"""

import sys
import os
import numpy as np

# 设置路径
_MOSS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _MOSS_ROOT)
sys.path.insert(0, os.path.join(_MOSS_ROOT, 'moss', 'api'))
sys.path.insert(0, os.path.join(_MOSS_ROOT, '_archive_v3', 'core'))
sys.path.insert(0, os.path.join(_MOSS_ROOT, '_archive_v4', 'integration'))

from adapter import MOSSApiAdapter, create_unified_agent


def test_v31_agent():
    """测试v3.1 Agent适配"""
    print("\n" + "="*60)
    print("测试 v3.1 Agent (MOSSv3Agent9D)")
    print("="*60)
    
    try:
        from agent_9d import MOSSv3Agent9D
        
        # 创建v3.1 Agent实例
        agent_v31 = MOSSv3Agent9D(
            agent_id="test_v31",
            enable_purpose=True,
            purpose_interval=1000
        )
        
        # 创建适配器
        adapter_v31 = MOSSApiAdapter(agent_v31)
        
        # 测试适配器功能
        print(f"检测到的Agent类型: {adapter_v31.agent_type}")
        
        info = adapter_v31.get_agent_info()
        print(f"Agent信息: {info}")
        
        # 测试Purpose向量获取
        purpose_vec = adapter_v31.get_purpose_vector()
        if purpose_vec is not None:
            print(f"Purpose向量形状: {purpose_vec.shape}")
            print(f"Purpose向量: {purpose_vec}")
        else:
            print("⚠️ 无法获取Purpose向量")
        
        # 测试Purpose陈述
        statement = adapter_v31.get_purpose_statement()
        print(f"Purpose陈述: {statement}")
        
        # 测试连续性分数
        coherence = adapter_v31.get_coherence_score()
        print(f"自我连续性分数: {coherence:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ v3.1 Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v41_agent():
    """测试v4.1 Agent适配"""
    print("\n" + "="*60)
    print("测试 v4.1 Agent (PurposeEnhancedAgent)")
    print("="*60)
    
    try:
        from agent_v4_1 import PurposeEnhancedAgent
        
        # 创建v4.1 Agent实例
        agent_v41 = PurposeEnhancedAgent(agent_id="test_v41")
        
        # 创建适配器
        adapter_v41 = MOSSApiAdapter(agent_v41)
        
        # 测试适配器功能
        print(f"检测到的Agent类型: {adapter_v41.agent_type}")
        
        info = adapter_v41.get_agent_info()
        print(f"Agent信息: {info}")
        
        # 测试Purpose向量获取
        purpose_vec = adapter_v41.get_purpose_vector()
        if purpose_vec is not None:
            print(f"Purpose向量形状: {purpose_vec.shape}")
            print(f"Purpose向量: {purpose_vec}")
        else:
            print("⚠️ 无法获取Purpose向量")
        
        # 测试Purpose陈述
        statement = adapter_v41.get_purpose_statement()
        print(f"Purpose陈述: {statement}")
        
        # 测试连续性分数
        coherence = adapter_v41.get_coherence_score()
        print(f"自我连续性分数: {coherence:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ v4.1 Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v50_agent():
    """测试v5.0 Agent适配"""
    print("\n" + "="*60)
    print("测试 v5.0 Agent (UnifiedMOSSAgent)")
    print("="*60)
    
    try:
        # 导入v5.0核心模块
        sys.path.insert(0, os.path.join(_MOSS_ROOT, 'moss', 'core'))
        
        # 尝试不同的导入方式
        try:
            from unified_agent import UnifiedMOSSAgent
        except ImportError:
            # 尝试其他可能的导入方式
            from moss.core.unified_agent import UnifiedMOSSAgent
        
        # 导入配置类
        try:
            from moss.core.config import MOSSConfig
        except ImportError:
            # 创建简化的配置类
            class MOSSConfig:
                def __init__(self):
                    self.enable_purpose = True
                    self.purpose_interval = 1000
        
        # 创建v5.0 Agent实例
        config = MOSSConfig()
        agent_v50 = UnifiedMOSSAgent(
            agent_id="test_v50",
            config=config
        )
        
        # 创建适配器
        adapter_v50 = MOSSApiAdapter(agent_v50)
        
        # 测试适配器功能
        print(f"检测到的Agent类型: {adapter_v50.agent_type}")
        
        info = adapter_v50.get_agent_info()
        print(f"Agent信息: {info}")
        
        # 测试Purpose向量获取
        purpose_vec = adapter_v50.get_purpose_vector()
        if purpose_vec is not None:
            print(f"Purpose向量形状: {purpose_vec.shape}")
            print(f"Purpose向量: {purpose_vec}")
        else:
            print("⚠️ 无法获取Purpose向量")
        
        # 测试Purpose陈述
        statement = adapter_v50.get_purpose_statement()
        print(f"Purpose陈述: {statement}")
        
        return True
        
    except Exception as e:
        print(f"❌ v5.0 Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_unified_agent():
    """测试create_unified_agent函数"""
    print("\n" + "="*60)
    print("测试 create_unified_agent 函数")
    print("="*60)
    
    try:
        # 创建一个简单的模拟Agent
        class MockAgent:
            def __init__(self):
                self.agent_id = "mock_agent"
                self.step_count = 0
            
            def step(self, observation):
                self.step_count += 1
                return {"action": "wait", "success": True, "reward": 0.1}
        
        mock_agent = MockAgent()
        
        # 使用create_unified_agent创建适配器
        unified_agent = create_unified_agent(mock_agent)
        
        print(f"创建的适配器类型: {type(unified_agent)}")
        
        # 测试适配器功能
        info = unified_agent.get_agent_info()
        print(f"Agent信息: {info}")
        
        # 测试step方法
        result = unified_agent.step({"time": 0})
        print(f"Step结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ create_unified_agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_simulation():
    """测试Agent的step方法"""
    print("\n" + "="*60)
    print("测试Agent Step模拟")
    print("="*60)
    
    try:
        # 创建一个简单的模拟Agent
        class SimpleAgent:
            def __init__(self):
                self.agent_id = "simple_agent"
                self.step_count = 0
                self.weights = np.array([0.25, 0.25, 0.25, 0.25])
                
                # 模拟purpose_generator
                class MockPurposeGenerator:
                    def __init__(self):
                        self.purpose_vector = np.array([0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.0, 0.0, 0.0])
                
                self.purpose_generator = MockPurposeGenerator()
            
            def step(self, observation):
                self.step_count += 1
                
                # 简单的行为逻辑
                action = "explore" if observation.get("time", 0) % 2 == 0 else "rest"
                success = True
                reward = 0.1 * (self.step_count % 10)
                
                return {
                    "action": action,
                    "success": success,
                    "reward": reward,
                    "weights": self.weights.tolist()
                }
        
        # 创建Agent和适配器
        agent = SimpleAgent()
        adapter = MOSSApiAdapter(agent)
        
        print(f"Agent类型: {adapter.agent_type}")
        
        # 运行多次step
        for i in range(5):
            observation = {"time": i, "resource_level": 0.8}
            result = adapter.step(observation)
            
            print(f"\nStep {i}:")
            print(f"  观察: {observation}")
            print(f"  结果: {result}")
            
            # 获取Purpose向量
            purpose_vec = adapter.get_purpose_vector()
            if purpose_vec is not None:
                print(f"  Purpose向量: {purpose_vec[:4]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Step模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("MOSS API适配器测试开始")
    print("="*60)
    
    results = {
        "v3.1": test_v31_agent(),
        "v4.1": test_v41_agent(),
        "v5.0": test_v50_agent(),
        "create_unified": test_create_unified_agent(),
        "step_simulation": test_step_simulation()
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过 ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！API适配器工作正常。")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，需要进一步调试。")


if __name__ == "__main__":
    main()