"""
增强版MOSS交互参数适配器

基于agent_8d.py、agent_9d.py和agent_v4_1.py的深度分析：
1. v3.1 8D: step(observed_behaviors=None, interaction=None)
   - interaction必需字段: agent_id, outcome, payoff
2. v3.1 9D: 完全继承8D参数格式
3. v4.1: step(observation=None) - 单参数格式

此模块提供准确的参数转换功能，解决不同版本Agent的参数格式兼容性问题。
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，支持datetime和numpy类型"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, np.bool)):
            return bool(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


class MOSSInteractionAdapter:
    """
    增强版MOSS交互参数适配器
    
    基于实际代码分析提供准确的参数转换：
    - v3.1 (8D/9D): 双参数格式 - observed_behaviors和interaction
    - v4.1: 单参数格式 - observation
    - v5.0: 支持后续扩展
    """
    
    def __init__(self, agent_type: str = "auto"):
        """
        初始化适配器
        
        Args:
            agent_type: Agent类型，支持 'v3.1', 'v9d', 'v4.1', 'v5.0', 'auto'
        """
        self.agent_type = agent_type if agent_type != "auto" else "v3.1"
        self.interaction_history = []
        self.logger = logging.getLogger(f"MOSSAdapter.{self.agent_type}")
        
        # 版本特定的配置（基于实际代码分析）
        self.version_configs = {
            "v3.1": {  # agent_8d.py格式
                "required_fields": ["agent_id", "outcome", "payoff"],
                "optional_fields": ["timestamp", "type", "metadata", "context"],
                "default_payoff": 0.0,
                "step_method": "dual_param",  # 需要两个参数: observed_behaviors和interaction
                "agent_class": "MOSSv3Agent8D"
            },
            "v9d": {  # agent_9d.py格式 - 继承v3.1
                "required_fields": ["agent_id", "outcome", "payoff"],
                "optional_fields": ["timestamp", "type", "metadata", "context"],
                "default_payoff": 0.0,
                "step_method": "dual_param",  # 继承8D参数格式
                "agent_class": "MOSSv3Agent9D"
            },
            "v4.1": {  # agent_v4_1.py格式
                "required_fields": [],  # v4.1没有严格必需字段
                "optional_fields": ["resource_level", "threat_level", "novelty", "goal_progress", "context"],
                "default_reward": 0.0,
                "step_method": "single_param",  # 只需要一个observation参数
                "agent_class": "PurposeEnhancedAgent"
            },
            "v5.0": {
                "required_fields": ["agent_id", "action", "observation"],
                "optional_fields": ["reward", "done", "info", "timestamp"],
                "default_reward": 0.0,
                "step_method": "dual_param",
                "agent_class": "MOSSv5Agent"
            }
        }
        
        logger.info(f"初始化增强版MOSSInteractionAdapter，类型: {self.agent_type}")
    
    def detect_interaction_type(self, observation: Dict[str, Any]) -> str:
        """根据观察数据确定交互类型"""
        observation_str = str(observation).lower()
        
        # 合作相关的关键词
        cooperative_keywords = ['cooperate', 'help', 'assist', 'support', 'share', 'collaborate']
        # 竞争相关的关键词  
        competitive_keywords = ['compete', 'fight', 'attack', 'defeat', 'win', 'lose']
        
        for keyword in cooperative_keywords:
            if keyword in observation_str:
                return "cooperative"
        
        for keyword in competitive_keywords:
            if keyword in observation_str:
                return "competitive"
        
        return "neutral"
    
    def extract_agent_id(self, observation: Dict[str, Any]) -> str:
        """从观察数据中提取agent_id"""
        # 尝试从常见字段中提取agent_id
        possible_fields = ['agent_id', 'actor_id', 'agent', 'id', 'name']
        
        for field in possible_fields:
            if field in observation:
                value = observation[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, (int, float)):
                    return str(value)
        
        # 如果都没有，使用默认值
        return f"agent_{np.random.randint(1000, 9999)}"
    
    def extract_outcome(self, observation: Dict[str, Any]) -> str:
        """从观察数据中提取outcome/result"""
        # 尝试从常见字段中提取outcome
        possible_fields = ['outcome', 'result', 'status', 'action_result', 'state']
        
        for field in possible_fields:
            if field in observation:
                value = observation[field]
                if isinstance(value, str):
                    return value
        
        # 如果没有明确的结果，基于观察内容生成
        observation_str = str(observation)
        if 'success' in observation_str.lower():
            return "success"
        elif 'fail' in observation_str.lower():
            return "failure"
        else:
            return "undefined"
    
    def extract_payoff(self, observation: Dict[str, Any]) -> float:
        """从观察数据中提取payoff/reward值"""
        # 尝试从常见字段中提取payoff
        possible_fields = ['payoff', 'reward', 'score', 'value', 'utility']
        
        for field in possible_fields:
            if field in observation:
                value = observation[field]
                if isinstance(value, (int, float)):
                    return float(value)
        
        # 默认值
        config = self.version_configs.get(self.agent_type, self.version_configs["v3.1"])
        return config.get("default_payoff", 0.0)
    
    def prepare_v31_interaction(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """准备v3.1版本（agent_8d.py）的interaction参数"""
        interaction = {
            'agent_id': self.extract_agent_id(observation),
            'outcome': self.extract_outcome(observation),
            'payoff': self.extract_payoff(observation),
            'timestamp': observation.get('timestamp', datetime.now()),
            'type': self.detect_interaction_type(observation),
            'metadata': {
                'source': 'MOSSInteractionAdapterEnhanced',
                'agent_version': 'v3.1',
                'original_data': observation,
                'conversion_timestamp': datetime.now().isoformat()
            }
        }
        
        # 添加额外的上下文信息
        if 'context' in observation:
            interaction['context'] = observation['context']
        
        return interaction
    
    def prepare_v41_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备v4.1版本的observation参数
        
        基于agent_v4_1.py分析：
        - v4.1 Agent只需要单个observation参数
        - 典型observation包含: resource_level, threat_level, novelty, goal_progress, context等
        """
        v41_observation = {}
        
        # 核心字段映射
        field_mappings = {
            'resource_level': ['resource', 'energy', 'health', 'status'],
            'threat_level': ['threat', 'danger', 'risk', 'pressure'],
            'novelty': ['novelty', 'unfamiliarity', 'surprise', 'information'],
            'goal_progress': ['progress', 'achievement', 'completion', 'milestone']
        }
        
        for v41_field, possible_keys in field_mappings.items():
            # 优先使用与v4.1字段名匹配的值
            if v41_field in observation:
                v41_observation[v41_field] = observation[v41_field]
            else:
                # 尝试从可能的键中寻找值
                for key in possible_keys:
                    if key in observation:
                        v41_observation[v41_field] = observation[key]
                        break
            
            # 如果没有找到，使用默认值
            if v41_field not in v41_observation:
                if v41_field == 'resource_level':
                    v41_observation[v41_field] = 0.8
                elif v41_field == 'threat_level':
                    v41_observation[v41_field] = 0.2
                elif v41_field == 'novelty':
                    v41_observation[v41_field] = 0.4
                elif v41_field == 'goal_progress':
                    v41_observation[v41_field] = 0.0
        
        # 添加上下文信息
        if 'context' in observation:
            v41_observation['context'] = observation['context']
        
        # 添加时间戳
        v41_observation['timestamp'] = observation.get('timestamp', datetime.now())
        
        # 记录适配信息
        v41_observation['_adapter_info'] = {
            'source': 'MOSSInteractionAdapterEnhanced',
            'agent_version': 'v4.1',
            'conversion_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"准备v4.1 observation: {len(v41_observation)}个字段")
        return v41_observation
    
    def prepare_observed_behaviors(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """准备observed_behaviors参数（用于v3.1/v9d/v5.0）"""
        behaviors = {
            'agent_id': self.extract_agent_id(observation),
            'behavior_type': observation.get('behavior_type', 'default_behavior'),
            'intensity': observation.get('intensity', 1.0),
            'target': observation.get('target', 'environment'),
            'context': observation.get('context', {}),
            'timestamp': observation.get('timestamp', datetime.now())
        }
        
        return behaviors
    
    def convert_to_v31_format(self, observation: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        将通用observation转换为v3.1格式（双参数）
        
        Returns:
            (observed_behaviors, interaction) 元组
        """
        observed_behaviors = self.prepare_observed_behaviors(observation)
        interaction = self.prepare_v31_interaction(observation)
        
        # 验证必需字段
        required_fields = self.version_configs.get("v3.1", {}).get("required_fields", [])
        missing_fields = [field for field in required_fields if field not in interaction]
        
        if missing_fields:
            self.logger.warning(f"v3.1 interaction缺少必需字段: {missing_fields}")
            # 尝试填充缺失字段
            for field in missing_fields:
                if field == "agent_id":
                    interaction["agent_id"] = self.extract_agent_id(observation)
                elif field == "outcome":
                    interaction["outcome"] = self.extract_outcome(observation)
                elif field == "payoff":
                    interaction["payoff"] = self.extract_payoff(observation)
        
        return observed_behaviors, interaction
    
    def convert_to_v41_format(self, observed_behaviors: Dict[str, Any], interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        将v3.1格式参数转换为v4.1格式（单参数）
        
        Args:
            observed_behaviors: v3.1格式的observed_behaviors
            interaction: v3.1格式的interaction
            
        Returns:
            v4.1格式的observation字典
        """
        # 从v3.1参数中提取信息构建v4.1 observation
        v41_observation = {}
        
        # 从interaction中提取信息
        if interaction:
            # 根据outcome设置威胁水平
            outcome = interaction.get('outcome', '').lower()
            if outcome in ['success', 'cooperate', 'help']:
                v41_observation['resource_level'] = 0.8
                v41_observation['threat_level'] = 0.1
            elif outcome in ['failure', 'defect', 'attack']:
                v41_observation['resource_level'] = 0.4
                v41_observation['threat_level'] = 0.6
            else:
                v41_observation['resource_level'] = 0.6
                v41_observation['threat_level'] = 0.3
            
            # 根据payoff设置目标进度
            payoff = interaction.get('payoff', 0.0)
            v41_observation['goal_progress'] = min(1.0, max(0.0, payoff / 10.0))
        
        # 从observed_behaviors中提取信息
        if observed_behaviors:
            behavior_type = observed_behaviors.get('behavior_type', '').lower()
            if behavior_type in ['explore', 'discover', 'learn']:
                v41_observation['novelty'] = 0.7
            else:
                v41_observation['novelty'] = 0.3
        
        # 确保所有必需字段都存在
        v41_fields = ['resource_level', 'threat_level', 'novelty', 'goal_progress']
        for field in v41_fields:
            if field not in v41_observation:
                # 设置默认值
                if field == 'resource_level':
                    v41_observation[field] = 0.6
                elif field == 'threat_level':
                    v41_observation[field] = 0.3
                elif field == 'novelty':
                    v41_observation[field] = 0.4
                elif field == 'goal_progress':
                    v41_observation[field] = 0.0
        
        # 添加上下文信息
        if observed_behaviors and 'context' in observed_behaviors:
            v41_observation['context'] = observed_behaviors['context']
        
        # 添加时间戳
        v41_observation['timestamp'] = datetime.now()
        
        # 记录适配信息
        v41_observation['_adapter_info'] = {
            'source': 'MOSSInteractionAdapterEnhanced',
            'conversion_type': 'v31_to_v41',
            'conversion_time': datetime.now().isoformat()
        }
        
        return v41_observation
    
    def adapt_step_call(self, agent, observation: Optional[Dict] = None, 
                       observed_behaviors: Optional[Dict] = None,
                       interaction: Optional[Dict] = None) -> Dict:
        """
        统一适配step方法调用
        
        Args:
            agent: Agent实例
            observation: 环境观察 (v4.x/v5.x格式)
            observed_behaviors: 观察到的他者行为 (v3.x格式)
            interaction: 当前互动信息 (v3.x格式)
            
        Returns:
            Agent行为结果
        """
        try:
            # 检测Agent类型
            agent_type = self.detect_agent_type(agent)
            
            if agent_type in ['v3.1', 'v9d', 'unknown']:
                # v3.x格式Agent
                if observed_behaviors is not None or interaction is not None:
                    # 直接使用v3.x格式参数
                    return agent.step(observed_behaviors, interaction)
                elif observation is not None:
                    # 将observation转换为v3.x格式
                    observed_behaviors_conv, interaction_conv = self.convert_to_v31_format(observation)
                    return agent.step(observed_behaviors_conv, interaction_conv)
                else:
                    # 无参数调用
                    return agent.step()
                    
            elif agent_type in ['v4.1', 'v5.0']:
                # v4.x/v5.x格式Agent
                if observation is not None:
                    # 直接使用v4.x格式参数
                    return agent.step(observation)
                elif observed_behaviors is not None or interaction is not None:
                    # 将v3.x格式参数转换为v4.x格式
                    obs_conv = self.convert_to_v41_format(observed_behaviors or {}, interaction or {})
                    return agent.step(obs_conv)
                else:
                    # 无参数调用
                    return agent.step()
                    
            else:
                # 未知Agent类型，尝试多种格式
                try:
                    if observation is not None:
                        return agent.step(observation)
                except Exception:
                    pass
                    
                try:
                    if observed_behaviors is not None:
                        return agent.step(observed_behaviors, interaction)
                except Exception:
                    pass
                    
                try:
                    return agent.step()
                except Exception as e:
                    raise RuntimeError(f"无法使用任何参数格式调用agent.step(): {e}")
        
        except Exception as e:
            self.logger.error(f"适配step调用失败: {e}")
            raise
    
    def detect_agent_type(self, agent) -> str:
        """检测Agent类型"""
        agent_class = type(agent).__name__
        
        # 检测v3.1 Agent
        if agent_class == 'MOSSv3Agent8D' or agent_class == 'MOSSv3Agent9D':
            return 'v3.1' if agent_class == 'MOSSv3Agent8D' else 'v9d'
        
        # 检测v4.1 Agent
        if agent_class == 'PurposeEnhancedAgent':
            return 'v4.1'
        
        # 检测v5.0 Agent
        if agent_class == 'UnifiedMOSSAgent':
            return 'v5.0'
        
        # 尝试通过其他特征检测
        try:
            # 如果有purpose_generator属性，可能是v3.1
            if hasattr(agent, 'purpose_generator'):
                return 'v3.1'
            
            # 如果有world_model和goal_manager，可能是v4.1
            if hasattr(agent, 'world_model') and hasattr(agent, 'goal_manager'):
                return 'v4.1'
                
            # 如果有_purpose_generator属性，可能是v5.0
            if hasattr(agent, '_purpose_generator') or hasattr(agent, '_get_purpose_vector'):
                return 'v5.0'
        except:
            pass
            
        return 'unknown'
    
    def validate_interaction(self, interaction: Dict[str, Any]) -> bool:
        """验证interaction参数的完整性"""
        config = self.version_configs.get(self.agent_type, self.version_configs["v3.1"])
        required_fields = config.get("required_fields", [])
        
        missing_fields = []
        for field in required_fields:
            if field not in interaction:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.warning(f"interaction缺少必需字段: {missing_fields}")
            return False
        
        return True
    
    def get_interaction_summary(self) -> Dict[str, Any]:
        """获取交互历史摘要"""
        total_interactions = len(self.interaction_history)
        
        if total_interactions == 0:
            return {"total_interactions": 0, "latest_interaction": None}
        
        latest = self.interaction_history[-1]
        
        # 统计各类型的交互
        interaction_types = {}
        for record in self.interaction_history:
            interaction_type = record.get('interaction', {}).get('type', 'unknown')
            interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
        
        return {
            "total_interactions": total_interactions,
            "agent_version": self.agent_type,
            "latest_interaction": {
                "timestamp": latest.get('timestamp', datetime.now()).isoformat(),
                "type": latest.get('interaction', {}).get('type', 'unknown'),
                "agent_id": latest.get('interaction', {}).get('agent_id', 'unknown')
            },
            "interaction_type_distribution": interaction_types
        }


def create_unified_agent_adapter(agent_type: str = "auto") -> MOSSInteractionAdapter:
    """创建统一的Agent适配器"""
    return MOSSInteractionAdapter(agent_type=agent_type)


# 使用示例
def example_usage():
    """演示增强版适配器的使用方法"""
    print("=" * 70)
    print("增强版MOSSInteractionAdapter 使用示例")
    print("=" * 70)
    
    # 创建适配器
    adapter_v31 = create_unified_agent_adapter("v3.1")
    adapter_v41 = create_unified_agent_adapter("v4.1")
    
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
        "timestamp": datetime.now()
    }
    
    print("\n1. v3.1格式转换:")
    print("-" * 40)
    observed_behaviors, interaction = adapter_v31.convert_to_v31_format(test_observation)
    print(f"observed_behaviors: {len(observed_behaviors)}个字段")
    print(f"interaction: {len(interaction)}个字段")
    print(f"必需字段验证: {adapter_v31.validate_interaction(interaction)}")
    
    print("\n2. v4.1格式转换:")
    print("-" * 40)
    v41_observation = adapter_v41.prepare_v41_observation(test_observation)
    print(f"v41_observation: {len(v41_observation)}个字段")
    
    print("\n3. v3.1到v4.1格式转换:")
    print("-" * 40)
    v41_from_v31 = adapter_v41.convert_to_v41_format(observed_behaviors, interaction)
    print(f"转换后的v41_observation: {len(v41_from_v31)}个字段")
    
    print("\n✅ 示例演示完成")
    print("=" * 70)


if __name__ == "__main__":
    example_usage()