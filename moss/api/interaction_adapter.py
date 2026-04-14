"""
MOSS Interaction Adapter - 统一不同版本Agent的step方法参数格式

核心问题：v3.x系列（8D/9D Agent）使用社交参数范式，而v4.x/v5.x系列使用环境观察范式
解决方案：创建统一的参数转换器，支持：
1. v3.x -> v4.x 参数转换（社交参数 -> 环境观察）
2. v4.x -> v3.x 参数转换（环境观察 -> 社交参数）
3. 向后兼容性处理

作者：AI Assistant
日期：2026-04-13
版本：1.0.0
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union


class MOSSInteractionAdapter:
    """
    MOSS Interaction Adapter - 统一不同版本Agent的step方法参数格式
    
    支持的主要Agent类型：
    - v3.x系列 (agent_8d.py, agent_9d.py): 使用社交参数范式
    - v4.x系列 (agent_v4.py, agent_v4_1.py): 使用环境观察范式
    - v5.x系列 (unified_agent.py): 使用环境观察范式
    """
    
    def __init__(self, agent_type: str = "auto"):
        """
        初始化参数转换器
        
        Args:
            agent_type: Agent类型标识符
                - "auto": 自动检测
                - "v3.1": 9维Agent (社交参数范式)
                - "v4.1": Purpose增强Agent (环境观察范式)
                - "v5.0": 统一Agent (环境观察范式)
        """
        self.agent_type = agent_type
        
    def detect_agent_from_instance(self, agent_instance: Any) -> str:
        """
        从Agent实例检测其类型
        
        Args:
            agent_instance: Agent实例
            
        Returns:
            字符串: 'v3.1', 'v4.1', 'v5.0' 或 'unknown'
        """
        agent_class = type(agent_instance).__name__
        
        # 检测v3.1 Agent (MOSSv3Agent9D)
        if agent_class == 'MOSSv3Agent9D':
            return 'v3.1'
        
        # 检测v4.1 Agent (PurposeEnhancedAgent)
        if agent_class == 'PurposeEnhancedAgent':
            return 'v4.1'
        
        # 检测v5.0 Agent (UnifiedMOSSAgent)
        if agent_class == 'UnifiedMOSSAgent':
            return 'v5.0'
        
        # 通过特征检测
        try:
            # v3.x特征：有purpose_generator属性，step方法接收社交参数
            if hasattr(agent_instance, 'purpose_generator'):
                step_signature = getattr(agent_instance.step, '__code__', None)
                if step_signature and step_signature.co_argcount >= 3:  # 包含self, observed_behaviors, interaction
                    return 'v3.1'
            
            # v4.x特征：有world_model, goal_manager属性
            if hasattr(agent_instance, 'world_model') and hasattr(agent_instance, 'goal_manager'):
                return 'v4.1'
            
            # v5.x特征：有_purpose_generator或_get_purpose_vector方法
            if hasattr(agent_instance, '_purpose_generator') or hasattr(agent_instance, '_get_purpose_vector'):
                return 'v5.0'
                
        except Exception:
            pass
            
        return 'unknown'
    
    def convert_to_v31_format(self, observation: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        将环境观察转换为v3.1 Agent所需的社交参数格式
        
        Args:
            observation: 环境观察字典
            
        Returns:
            (observed_behaviors, interaction) 元组
            observed_behaviors: 观察到的他者行为 {agent_id: behavior}
            interaction: 当前互动信息 {'agent_id': str, 'outcome': str, 'payoff': float}
            
        转换逻辑：
        1. 从observation中提取社交相关字段
        2. 构建v3.1 Agent期望的参数格式
        3. 如果没有社交信息，返回(None, None)
        """
        observed_behaviors = None
        interaction = None
        
        try:
            # 从observation中提取他者信息
            if 'other_agents' in observation:
                other_agents = observation['other_agents']
                if isinstance(other_agents, dict) and len(other_agents) > 0:
                    observed_behaviors = {}
                    for agent_id, agent_data in other_agents.items():
                        behavior = {
                            'action': agent_data.get('action', 'unknown'),
                            'reward': agent_data.get('reward', 0.0),
                            'weights': np.array(agent_data.get('weights', [0.25, 0.25, 0.25, 0.25]))
                        }
                        observed_behaviors[agent_id] = behavior
            
            # 从observation中提取互动信息
            if 'interaction' in observation:
                interaction_data = observation['interaction']
                interaction = {
                    'agent_id': str(interaction_data.get('agent_id', 'unknown')),
                    'outcome': str(interaction_data.get('outcome', 'cooperate')),
                    'payoff': float(interaction_data.get('payoff', 0.5))
                }
            elif 'social_opportunity' in observation and observation['social_opportunity']:
                # 如果有社交机会但无具体互动，创建默认互动
                interaction = {
                    'agent_id': 'agent_0',
                    'outcome': 'cooperate',
                    'payoff': 0.5
                }
                
        except Exception as e:
            print(f"Warning: Error converting to v3.1 format: {e}")
            
        return observed_behaviors, interaction
    
    def convert_to_v4x_format(self, observed_behaviors: Optional[Dict] = None, 
                              interaction: Optional[Dict] = None) -> Dict[str, Any]:
        """
        将社交参数转换为v4.x/v5.x Agent所需的环境观察格式
        
        Args:
            observed_behaviors: 观察到的他者行为 {agent_id: behavior}
            interaction: 当前互动信息 {'agent_id': str, 'outcome': str, 'payoff': float}
            
        Returns:
            环境观察字典
            
        转换逻辑：
        1. 将社交参数打包到observation字典中
        2. 保持向后兼容的字段名称
        3. 添加元数据以便后续转换
        """
        observation = {}
        
        try:
            # 打包他者行为信息
            if observed_behaviors is not None:
                observation['other_agents'] = {}
                for agent_id, behavior in observed_behaviors.items():
                    observation['other_agents'][agent_id] = {
                        'action': behavior.get('action', 'unknown'),
                        'reward': float(behavior.get('reward', 0.0)),
                        'weights': behavior.get('weights', [0.25, 0.25, 0.25, 0.25])
                    }
            
            # 打包互动信息
            if interaction is not None:
                observation['interaction'] = {
                    'agent_id': str(interaction.get('agent_id', 'unknown')),
                    'outcome': str(interaction.get('outcome', 'cooperate')),
                    'payoff': float(interaction.get('payoff', 0.5))
                }
                
        except Exception as e:
            print(f"Warning: Error converting to v4.x format: {e}")
            
        return observation
    
    def get_unified_step_params(self, agent_instance: Any, 
                               observation: Optional[Dict] = None,
                               observed_behaviors: Optional[Dict] = None,
                               interaction: Optional[Dict] = None) -> Tuple[Any, Dict]:
        """
        根据Agent类型获取统一的step方法参数
        
        Args:
            agent_instance: Agent实例
            observation: 环境观察（v4.x/v5.x格式）
            observed_behaviors: 观察到的他者行为（v3.x格式）
            interaction: 当前互动信息（v3.x格式）
            
        Returns:
            (agent, params) 元组，其中params是调用step所需的参数
        """
        # 自动检测Agent类型
        if self.agent_type == 'auto':
            detected_type = self.detect_agent_from_instance(agent_instance)
        else:
            detected_type = self.agent_type
            
        if detected_type in ['v3.1', 'unknown']:
            # v3.1 Agent：需要社交参数
            # 如果提供了observation，尝试从中提取社交参数
            if observation is not None and observed_behaviors is None and interaction is None:
                observed_behaviors, interaction = self.convert_to_v31_format(observation)
            
            # 确保参数格式正确
            params = (observed_behaviors, interaction)
            
        elif detected_type in ['v4.1', 'v5.0']:
            # v4.x/v5.x Agent：需要环境观察
            # 如果提供了社交参数，尝试转换为环境观察
            if observed_behaviors is not None and observation is None:
                observation = self.convert_to_v4x_format(observed_behaviors, interaction)
            
            # 确保参数格式正确
            params = (observation,)
            
        else:
            # 未知类型，返回原始参数
            params = (observation,)
            
        return agent_instance, params
    
    def adapt_step_call(self, agent_instance: Any, **kwargs) -> Dict:
        """
        统一的step方法调用适配器
        
        Args:
            agent_instance: Agent实例
            **kwargs: 可能的参数：
                - observation: Dict（v4.x/v5.x格式）
                - observed_behaviors: Dict（v3.x格式）
                - interaction: Dict（v3.x格式）
                
        Returns:
            Agent执行结果
            
        使用示例：
            adapter = MOSSInteractionAdapter(agent_type='auto')
            result = adapter.adapt_step_call(agent, observation={'resource_level': 0.8})
            
            或：
            result = adapter.adapt_step_call(agent, observed_behaviors={'agent_1': {...}})
        """
        # 提取参数
        observation = kwargs.get('observation')
        observed_behaviors = kwargs.get('observed_behaviors')
        interaction = kwargs.get('interaction')
        
        # 获取统一的参数
        agent, params = self.get_unified_step_params(
            agent_instance=agent_instance,
            observation=observation,
            observed_behaviors=observed_behaviors,
            interaction=interaction
        )
        
        # 调用Agent的step方法
        try:
            result = agent.step(*params)
            return result
        except Exception as e:
            # 如果失败，尝试其他参数格式
            print(f"Primary step call failed: {e}, trying alternative formats...")
            
            # 尝试不同的参数组合
            try:
                # 尝试只传递observation
                if observation is not None:
                    return agent.step(observation)
            except Exception:
                pass
                
            try:
                # 尝试只传递社交参数
                if observed_behaviors is not None:
                    return agent.step(observed_behaviors, interaction)
            except Exception:
                pass
                
            try:
                # 尝试无参数调用
                return agent.step()
            except Exception as e2:
                raise RuntimeError(f"Failed to call agent.step() with any parameter format: {e2}")
    
    def create_agent_wrapper(self, agent_instance: Any):
        """
        创建Agent包装器，提供统一的接口
        
        Args:
            agent_instance: 原始Agent实例
            
        Returns:
            包装后的Agent实例，具有统一的step方法
        """
        class UnifiedAgentWrapper:
            def __init__(self, agent, adapter):
                self._agent = agent
                self._adapter = adapter
                
                # 复制关键属性
                self.agent_id = getattr(agent, 'agent_id', 'unknown')
                self.step_count = getattr(agent, 'step_count', 0)
                
            def step(self, **kwargs) -> Dict:
                return self._adapter.adapt_step_call(self._agent, **kwargs)
            
            def __getattr__(self, name):
                # 委托其他属性到原始Agent
                return getattr(self._agent, name)
        
        return UnifiedAgentWrapper(agent_instance, self)


def create_unified_agent_adapter(agent_instance: Any, agent_type: str = 'auto') -> MOSSInteractionAdapter:
    """
    创建统一的Agent适配器工厂函数
    
    Args:
        agent_instance: Agent实例
        agent_type: Agent类型标识符
        
    Returns:
        MOSSInteractionAdapter实例
    """
    adapter = MOSSInteractionAdapter(agent_type=agent_type)
    return adapter


# 使用示例
if __name__ == "__main__":
    # 示例Agent类
    class MockV31Agent:
        def __init__(self, agent_id="test_v31"):
            self.agent_id = agent_id
            self.step_count = 0
            self.purpose_generator = type('MockPurposeGen', (), {'purpose_vector': np.array([0.25]*9)})()
            
        def step(self, observed_behaviors=None, interaction=None):
            self.step_count += 1
            return {
                'agent_id': self.agent_id,
                'step': self.step_count,
                'observed_behaviors': observed_behaviors,
                'interaction': interaction,
                'result': 'v3.1_success'
            }
    
    class MockV41Agent:
        def __init__(self, agent_id="test_v41"):
            self.agent_id = agent_id
            self.step_count = 0
            self.world_model = type('MockWorldModel', (), {})()
            self.goal_manager = type('MockGoalManager', (), {})()
            
        def step(self, observation=None):
            self.step_count += 1
            return {
                'agent_id': self.agent_id,
                'step': self.step_count,
                'observation': observation,
                'result': 'v4.1_success'
            }
    
    # 测试不同Agent类型
    print("=" * 70)
    print("MOSS Interaction Adapter 测试")
    print("=" * 70)
    
    # 测试v3.1 Agent
    v31_agent = MockV31Agent()
    adapter = create_unified_agent_adapter(v31_agent, agent_type='auto')
    
    print(f"\n1. 测试 v3.1 Agent (检测类型: {adapter.detect_agent_from_instance(v31_agent)})")
    
    # 方式1：使用observation参数
    result1 = adapter.adapt_step_call(v31_agent, observation={
        'other_agents': {
            'agent_B': {'action': 'cooperate', 'reward': 0.8, 'weights': [0.3, 0.2, 0.3, 0.2]}
        },
        'interaction': {'agent_id': 'agent_B', 'outcome': 'cooperate', 'payoff': 0.7}
    })
    print(f"   使用observation参数: {result1['result']}")
    
    # 方式2：直接使用社交参数
    result2 = adapter.adapt_step_call(v31_agent, observed_behaviors={
        'agent_C': {'action': 'explore', 'reward': 0.5, 'weights': [0.25]*4}
    }, interaction={'agent_id': 'agent_C', 'outcome': 'defect', 'payoff': 0.3})
    print(f"   使用社交参数: {result2['result']}")
    
    # 测试v4.1 Agent
    v41_agent = MockV41Agent()
    adapter2 = create_unified_agent_adapter(v41_agent, agent_type='auto')
    
    print(f"\n2. 测试 v4.1 Agent (检测类型: {adapter2.detect_agent_from_instance(v41_agent)})")
    
    # 方式1：使用observation参数
    result3 = adapter2.adapt_step_call(v41_agent, observation={
        'resource_level': 0.9,
        'threat_level': 0.1
    })
    print(f"   使用observation参数: {result3['result']}")
    
    # 方式2：使用社交参数（将自动转换）
    result4 = adapter2.adapt_step_call(v41_agent, observed_behaviors={
        'agent_D': {'action': 'cooperate', 'reward': 0.9, 'weights': [0.4, 0.1, 0.3, 0.2]}
    })
    print(f"   使用社交参数（自动转换）: {result4['result']}")
    
    print(f"\n✓ 测试完成")
    print("=" * 70)