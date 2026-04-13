"""
MOSS API 适配器 - 统一不同版本Agent的接口

版本兼容性：
- v3.1: MOSSv3Agent9D (通过 purpose_generator.purpose_vector 访问)
- v4.1: PurposeEnhancedAgent (需要计算Purpose向量)
- v5.0: UnifiedMOSSAgent (有 _get_purpose_vector() 方法)

新增功能：参数格式转换，解决v3.x与v4.x/v5.x的参数格式不兼容问题

作者：AI Assistant
日期：2026-04-13
版本：2.0.0
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union

# 导入参数转换器
try:
    from .interaction_adapter_enhanced import MOSSInteractionAdapter, create_unified_agent_adapter
except ImportError:
    try:
        from .interaction_adapter import MOSSInteractionAdapter, create_unified_agent_adapter
    except ImportError:
        # 如果无法导入，创建简化版本
        class MOSSInteractionAdapter:
            def __init__(self, agent_type='auto'):
                self.agent_type = agent_type


class MOSSApiAdapter:
    """
    MOSS API 统一适配器
    
    该适配器提供统一的接口，屏蔽不同版本Agent的API差异
    """
    
    def __init__(self, agent: Any):
        """
        初始化适配器
        
        Args:
            agent: MOSS Agent实例 (可以是v3.1, v4.1或v5.0版本)
        """
        self.agent = agent
        self.agent_type = self._detect_agent_type()
        # 初始化参数转换器
        self.interaction_adapter = MOSSInteractionAdapter(agent_type=self.agent_type)
        
    def _detect_agent_type(self) -> str:
        """
        检测Agent类型
        
        Returns:
            字符串：'v3.1', 'v4.1' 或 'v5.0'
        """
        agent_class = type(self.agent).__name__
        
        # 检测v3.1 Agent
        if agent_class == 'MOSSv3Agent9D':
            return 'v3.1'
        
        # 检测v4.1 Agent
        if agent_class == 'PurposeEnhancedAgent':
            return 'v4.1'
        
        # 检测v5.0 Agent
        if agent_class == 'UnifiedMOSSAgent':
            return 'v5.0'
        
        # 尝试通过其他特征检测
        try:
            # 如果有purpose_generator属性，可能是v3.1
            if hasattr(self.agent, 'purpose_generator'):
                return 'v3.1'
            
            # 如果有world_model和goal_manager，可能是v4.1
            if hasattr(self.agent, 'world_model') and hasattr(self.agent, 'goal_manager'):
                return 'v4.1'
                
            # 如果有_purpose_generator属性，可能是v5.0
            if hasattr(self.agent, '_purpose_generator') or hasattr(self.agent, '_get_purpose_vector'):
                return 'v5.0'
        except:
            pass
            
        # 默认返回unknown
        return 'unknown'
    
    def get_purpose_vector(self) -> Optional[np.ndarray]:
        """
        统一获取Purpose向量的方法
        
        Returns:
            9维Purpose向量 (numpy数组)，如果不可用则返回None
        """
        try:
            if self.agent_type == 'v3.1':
                # v3.1 Agent: 通过 purpose_generator.purpose_vector 访问
                if hasattr(self.agent, 'purpose_generator') and self.agent.purpose_generator is not None:
                    return self.agent.purpose_generator.purpose_vector
            
            elif self.agent_type == 'v4.1':
                # v4.1 Agent: 需要计算Purpose向量
                if hasattr(self.agent, 'purpose_state'):
                    # 从PurposeState转换为9维向量
                    purpose_state = self.agent.purpose_state
                    vector = np.array([
                        purpose_state.survival,
                        purpose_state.curiosity,
                        purpose_state.influence,
                        purpose_state.optimization,
                        self.agent.coherence_score if hasattr(self.agent, 'coherence_score') else 0.25,
                        np.mean(self.agent.valence_profile) if hasattr(self.agent, 'valence_profile') else 0.25,
                        0.25,  # D7: Other (社交认知)
                        0.25,  # D8: Norm (规范遵守)
                        0.0    # D9: Purpose强度 (暂时设为0)
                    ])
                    
                    # 确保前8维归一化到[0,1]
                    vector[:8] = np.maximum(vector[:8], 0)
                    if vector[:8].sum() > 0:
                        vector[:8] = vector[:8] / vector[:8].sum()
                    
                    return vector
            
            elif self.agent_type == 'v5.0':
                # v5.0 Agent: 可能有 _get_purpose_vector() 方法
                if hasattr(self.agent, '_get_purpose_vector'):
                    return self.agent._get_purpose_vector()
                
                # 或者通过 purpose_generator 属性访问
                if hasattr(self.agent, 'purpose_generator') and self.agent.purpose_generator is not None:
                    return self.agent.purpose_generator.purpose_vector
        
        except Exception as e:
            print(f"Error getting purpose vector for {self.agent_type} agent: {e}")
        
        return None
    
    def get_purpose_statement(self) -> str:
        """
        获取Purpose陈述
        
        Returns:
            Purpose陈述字符串
        """
        try:
            # 尝试直接获取purpose_statement
            if hasattr(self.agent, 'purpose_statement'):
                return str(self.agent.purpose_statement)
            
            # 对于v4.1 Agent，可以通过其他方式生成陈述
            if self.agent_type == 'v4.1':
                if hasattr(self.agent, 'purpose_state'):
                    # 基于PurposeState生成陈述
                    purpose_state = self.agent.purpose_state
                    values = [purpose_state.survival, purpose_state.curiosity,
                             purpose_state.influence, purpose_state.optimization]
                    purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
                    
                    max_idx = np.argmax(values)
                    dominant = purpose_names[max_idx]
                    weight = values[max_idx]
                    
                    return f"I am driven by {dominant} with strength {weight:.2f}"
        
        except Exception as e:
            print(f"Error getting purpose statement: {e}")
        
        # 默认返回
        return "Purpose not available"
    
    def get_coherence_score(self) -> float:
        """
        获取自我连续性分数 (D5维度)
        
        Returns:
            自我连续性分数 (0.0-1.0)
        """
        try:
            # v3.1 Agent: 可能需要计算
            if self.agent_type == 'v3.1':
                # 这里可以根据实际情况实现
                return 0.75
            
            # v4.1 Agent: 可能有coherence_score属性
            if self.agent_type == 'v4.1':
                if hasattr(self.agent, 'coherence_score'):
                    return float(self.agent.coherence_score)
            
            # v5.0 Agent: 可能需要通过其他方式获取
            if self.agent_type == 'v5.0':
                return 0.8
        
        except Exception as e:
            print(f"Error getting coherence score: {e}")
        
        return 0.5
    
    def step(self, observation: Optional[Dict] = None, 
             observed_behaviors: Optional[Dict] = None,
             interaction: Optional[Dict] = None) -> Dict:
        """
        统一的step方法，支持多种参数格式

        Args:
            observation: 环境观测 (v4.x/v5.x格式)
            observed_behaviors: 观察到的他者行为 (v3.x格式)
            interaction: 当前互动信息 (v3.x格式)

        Returns:
            Agent行为结果
            
        注意：
        - 对于v3.x Agent，优先使用observed_behaviors和interaction参数
        - 对于v4.x/v5.x Agent，优先使用observation参数
        - 如果参数不匹配，会自动进行格式转换
        """
        try:
            # 首先尝试使用增强版适配器
            if hasattr(self, 'interaction_adapter'):
                try:
                    # 使用适配器的统一方法
                    result = self.interaction_adapter.adapt_step_call(
                        self.agent,
                        observation=observation,
                        observed_behaviors=observed_behaviors,
                        interaction=interaction
                    )
                    return result
                except Exception as adapter_error:
                    print(f"增强版适配器调用失败，尝试回退方案: {adapter_error}")
            
            # 如果增强版适配器失败，使用原始适配器逻辑
            # 根据Agent类型选择合适的参数格式
            if self.agent_type in ['v3.1', 'unknown']:
                # v3.x Agent：需要社交参数
                if observed_behaviors is not None or interaction is not None:
                    # 直接使用提供的社交参数
                    return self.agent.step(observed_behaviors, interaction)
                elif observation is not None:
                    # 尝试从observation中提取社交参数
                    try:
                        # 使用增强版适配器的转换方法
                        if hasattr(self, 'interaction_adapter') and hasattr(self.interaction_adapter, 'convert_to_v31_format'):
                            observed_behaviors_conv, interaction_conv = self.interaction_adapter.convert_to_v31_format(observation)
                            return self.agent.step(observed_behaviors_conv, interaction_conv)
                    except Exception as conv_error:
                        print(f"参数转换失败: {conv_error}")
                    
                    # 如果转换失败，尝试直接传递observation
                    return self.agent.step(observation)
                else:
                    # 无参数调用
                    return self.agent.step()
                    
            elif self.agent_type in ['v4.1', 'v5.0']:
                # v4.x/v5.x Agent：需要环境观察
                if observation is not None:
                    # 直接使用提供的observation
                    return self.agent.step(observation)
                elif observed_behaviors is not None:
                    # 尝试从社交参数构建observation
                    try:
                        # 使用增强版适配器的转换方法
                        if hasattr(self, 'interaction_adapter') and hasattr(self.interaction_adapter, 'convert_to_v4x_format'):
                            observation_conv = self.interaction_adapter.convert_to_v4x_format(observed_behaviors, interaction)
                            return self.agent.step(observation_conv)
                    except Exception as conv_error:
                        print(f"参数转换失败: {conv_error}")
                    
                    # 如果转换失败，尝试直接传递社交参数
                    return self.agent.step(observed_behaviors, interaction)
                else:
                    # 无参数调用
                    return self.agent.step()
                    
            else:
                # 未知类型，尝试多种格式
                try:
                    if observation is not None:
                        return self.agent.step(observation)
                except Exception:
                    pass
                    
                try:
                    if observed_behaviors is not None:
                        return self.agent.step(observed_behaviors, interaction)
                except Exception:
                    pass
                    
                try:
                    return self.agent.step()
                except Exception as e:
                    raise RuntimeError(f"无法使用任何参数格式调用agent.step(): {e}")
                    
        except Exception as e:
            print(f"Agent step调用错误 (agent_type={self.agent_type}): {e}")
            raise
    
    def get_weights(self) -> Optional[np.ndarray]:
        """
        获取权重向量
        
        Returns:
            权重向量或None
        """
        try:
            if hasattr(self.agent, 'weights'):
                return np.array(self.agent.weights)
        except:
            pass
        
        return None
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        
        Returns:
            Agent信息字典
        """
        return {
            'agent_type': self.agent_type,
            'agent_class': type(self.agent).__name__,
            'agent_id': getattr(self.agent, 'agent_id', 'unknown'),
            'step_count': getattr(self.agent, 'step_count', 0),
            'has_purpose_generator': hasattr(self.agent, 'purpose_generator'),
            'has_world_model': hasattr(self.agent, 'world_model'),
            'has_goal_manager': hasattr(self.agent, 'goal_manager'),
        }


def create_unified_agent(agent: Any) -> MOSSApiAdapter:
    """
    创建统一的Agent适配器
    
    Args:
        agent: 原始Agent实例
        
    Returns:
        MOSSApiAdapter实例
    """
    return MOSSApiAdapter(agent)


# 兼容性包装器：为任何Agent添加get_purpose_vector()方法
def add_purpose_api(agent_class):
    """
    装饰器：为Agent类添加统一的Purpose API
    
    使用示例：
        @add_purpose_api
        class MyAgent:
            ...
    """
    original_init = agent_class.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        # 创建适配器实例
        self._api_adapter = MOSSApiAdapter(self)
        
        # 添加统一的方法
        self.get_purpose_vector = self._api_adapter.get_purpose_vector
        self.get_purpose_statement = self._api_adapter.get_purpose_statement
        self.get_coherence_score = self._api_adapter.get_coherence_score
    
    agent_class.__init__ = new_init
    return agent_class