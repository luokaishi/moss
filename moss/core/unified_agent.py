"""
MOSS Unified Core - Standardized Agent Interface
=================================================

统一的核心架构，整合v2/v3/v4的最佳实践

标准接口设计：
- 所有Agent继承自 BaseMOSSAgent
- 统一的配置管理
- 标准的实验框架

Author: Cash + Fuxi
Date: 2026-03-25
Version: 5.0.0-dev
"""
import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum
logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Agent状态枚举"""
    INITIALIZING = 'initializing'
    IDLE = 'idle'
    RUNNING = 'running'
    PAUSED = 'paused'
    ERROR = 'error'
    TERMINATED = 'terminated'

@dataclass
class MOSSConfig:
    """
    MOSS Agent 统一配置
    
    整合所有版本的配置参数
    """
    agent_id: str = 'moss_agent'
    version: str = '9.6.0'
    enable_survival: bool = True
    enable_curiosity: bool = True
    enable_influence: bool = True
    enable_optimization: bool = True
    enable_coherence: bool = True
    enable_valence: bool = True
    enable_other: bool = True
    enable_norm: bool = True
    enable_purpose: bool = True
    purpose_interval: int = 2000
    purpose_history_window: int = 100
    log_dir: str = 'experiments'
    checkpoint_interval: int = 1000
    enable_safety_guard: bool = True
    memory_limit_mb: int = 1024
    cpu_limit_percent: float = 80.0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'MOSSConfig':
        return cls(**data)

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'MOSSConfig':
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))

@dataclass
class ActionResult:
    """统一行动结果格式"""
    action_id: str
    action_type: str
    success: bool
    reward: float
    state: str
    purpose_vector: Optional[np.ndarray] = None
    metadata: Dict = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        return {'action_id': self.action_id, 'action_type': self.action_type, 'success': self.success, 'reward': self.reward, 'state': self.state, 'purpose_vector': self.purpose_vector.tolist() if self.purpose_vector is not None else None, 'metadata': self.metadata, 'timestamp': self.timestamp.isoformat()}

class BaseMOSSAgent(ABC):
    """
    MOSS Agent 抽象基类
    
    所有具体Agent实现必须继承此类
    """

    def __init__(self, config: MOSSConfig=None):
        self.config = config or MOSSConfig()
        self.agent_id = self.config.agent_id
        self.state = AgentState.INITIALIZING
        self.step_count = 0
        self._setup_logging()
        self.history: List[ActionResult] = []
        self.max_history = 10000
        self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        self.current_state = 'normal'
        logger.info(f'[BaseMOSSAgent] {self.agent_id} initialized')
        self.state = AgentState.IDLE

    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / f'{self.agent_id}_{datetime.now():%Y%m%d_%H%M%S}.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    @abstractmethod
    def step(self, observation: Dict=None) -> ActionResult:
        """
        执行一步决策
        
        Args:
            observation: 环境观察
            
        Returns:
            ActionResult: 行动结果
        """
        pass

    @abstractmethod
    def select_action(self, observation: Dict) -> str:
        """选择行动"""
        pass

    def update_weights(self, new_weights: np.ndarray):
        """更新权重"""
        self.weights = new_weights / np.sum(new_weights)
        logger.debug(f'[BaseMOSSAgent] Weights updated: {self.weights}')

    def get_state(self) -> Dict:
        """获取当前状态"""
        return {'agent_id': self.agent_id, 'state': self.state.value, 'step_count': self.step_count, 'weights': self.weights.tolist(), 'current_state': self.current_state}

    def save_checkpoint(self, path: str=None):
        """保存检查点"""
        if path is None:
            path = f'{self.config.log_dir}/{self.agent_id}_checkpoint_{self.step_count}.json'
        checkpoint = {'agent_id': self.agent_id, 'step_count': self.step_count, 'weights': self.weights.tolist(), 'config': self.config.to_dict(), 'timestamp': datetime.now().isoformat()}
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        logger.info(f'[BaseMOSSAgent] Checkpoint saved: {path}')

    def load_checkpoint(self, path: str):
        """加载检查点"""
        with open(path, 'r') as f:
            checkpoint = json.load(f)
        self.step_count = checkpoint['step_count']
        self.weights = np.array(checkpoint['weights'])
        logger.info(f'[BaseMOSSAgent] Checkpoint loaded: {path}')

    def run(self, steps: int=1000, callback=None):
        """
        运行多步
        
        Args:
            steps: 步数
            callback: 每步回调函数(step, result)
        """
        self.state = AgentState.RUNNING
        logger.info(f'[BaseMOSSAgent] Running {steps} steps')
        try:
            for i in range(steps):
                result = self.step()
                self.history.append(result)
                self.step_count += 1
                if self.step_count % self.config.checkpoint_interval == 0:
                    self.save_checkpoint()
                if callback:
                    callback(self.step_count, result)
        except Exception as e:
            logger.error(f'[BaseMOSSAgent] Error during run: {e}')
            self.state = AgentState.ERROR
            raise
        self.state = AgentState.IDLE
        logger.info(f'[BaseMOSSAgent] Run completed: {self.step_count} steps')

class UnifiedMOSSAgent(BaseMOSSAgent):
    """
    统一MOSS Agent实现 (v3.1 + v4.x 整合)
    
    功能：
    - 完整的9维系统 (D1-D9)
    - 真实世界桥接支持
    - 可配置的维度开关
    """

    def __init__(self, config: MOSSConfig=None):
        super().__init__(config)
        self._init_dimensions()
        self.purpose_generator = None
        if self.config.enable_purpose:
            self._init_purpose_generator()
        self.action_history = []
        self.max_action_history = 1000
        self.purpose_history = []  # D5-D8 维度使用的历史记录
        logger.info(f'[UnifiedMOSSAgent] {self.agent_id} ready with {self._get_enabled_dimensions()} dimensions')

    def _init_dimensions(self):
        """初始化各维度模块"""
        self.dimensions = {}
        if self.config.enable_survival:
            from .objectives import SurvivalObjective
            self.dimensions['survival'] = SurvivalObjective()
        if self.config.enable_curiosity:
            from .objectives import CuriosityObjective
            self.dimensions['curiosity'] = CuriosityObjective()
        if self.config.enable_influence:
            from .objectives import InfluenceObjective
            self.dimensions['influence'] = InfluenceObjective()
        if self.config.enable_optimization:
            from .objectives import OptimizationObjective
            self.dimensions['optimization'] = OptimizationObjective()
        if self.config.enable_coherence:
            from .dimensions import CoherenceModule
            self.dimensions['coherence'] = CoherenceModule()
        if self.config.enable_valence:
            from .dimensions import ValenceModule
            self.dimensions['valence'] = ValenceModule()
        if self.config.enable_other:
            from .dimensions import OtherModelingModule
            self.dimensions['other'] = OtherModelingModule()
        if self.config.enable_norm:
            from .dimensions import NormInternalizationModule
            self.dimensions['norm'] = NormInternalizationModule()

    def _init_purpose_generator(self):
        """初始化Purpose Generator"""
        try:
            from .purpose import PurposeGenerator
            self.purpose_generator = PurposeGenerator(agent_id=self.agent_id, generation_interval=self.config.purpose_interval, output_dir=self.config.log_dir)
            self.purpose_generator.load()
            logger.info('[UnifiedMOSSAgent] Purpose Generator initialized')
        except ImportError as e:
            logger.warning(f'[UnifiedMOSSAgent] Could not load Purpose Generator: {e}')
            self.purpose_generator = None

    def _get_enabled_dimensions(self) -> int:
        """获取启用的维度数"""
        return sum([self.config.enable_survival, self.config.enable_curiosity, self.config.enable_influence, self.config.enable_optimization, self.config.enable_coherence, self.config.enable_valence, self.config.enable_other, self.config.enable_norm, self.config.enable_purpose])

    def select_action(self, observation: Dict) -> str:
        """基于当前权重选择行动 (使用全部9维)"""
        self._update_state(observation)
        self._apply_state_weights()

        # 更新 D5-D8 维度状态
        self._update_extended_dimensions(observation)

        if np.random.random() < 0.1:
            return self._random_action()

        # 使用全部9维进行决策
        dim_names = [
            'survival', 'curiosity', 'influence', 'optimization',  # D1-D4
            'coherence', 'valence', 'other', 'norm', 'purpose'       # D5-D9
        ]

        # 获取9维权重 (扩展权重向量)
        weights = self._get_nine_dim_weights()

        # 选择权重最高的维度
        selected_idx = np.argmax(weights)
        selected_dim = dim_names[selected_idx]

        if selected_dim in self.dimensions:
            return self.dimensions[selected_dim].suggest_action()

        # 如果扩展维度没有返回动作，回退到 D1-D4
        if selected_idx >= 4:
            weights_d14 = weights[:4]
            selected_dim = dim_names[np.argmax(weights_d14)]
            if selected_dim in self.dimensions:
                return self.dimensions[selected_dim].suggest_action()

        return self._random_action()

    def _update_extended_dimensions(self, observation: Dict) -> None:
        """更新 D5-D8 扩展维度状态"""
        # D5: Coherence - 基于历史一致性
        if 'coherence' in self.dimensions and self.action_history:
            recent_actions = self.action_history[-10:]
            action_consistency = len(set(recent_actions)) / len(recent_actions)
            self.dimensions['coherence'].update_state({
                'consistency': 1.0 - action_consistency  # 一致性越高，值越低
            })

        # D6: Valence - 基于最近奖励
        if 'valence' in self.dimensions and self.purpose_history:
            recent_valence = [p.get('valence', 0.5) for p in self.purpose_history[-10:]]
            avg_valence = sum(recent_valence) / len(recent_valence)
            self.dimensions['valence'].update_state({'valence': avg_valence})

        # D7: Other - 简化处理
        if 'other' in self.dimensions:
            self.dimensions['other'].update_state({'trust': 0.5})

        # D8: Norm - 基于成功率
        if 'norm' in self.dimensions and self.purpose_history:
            success_rate = sum(1 for p in self.purpose_history if p.get('success', False))
            success_rate /= max(len(self.purpose_history), 1)
            self.dimensions['norm'].update_state({'compliance': success_rate})

    def _get_nine_dim_weights(self) -> np.ndarray:
        """获取9维权重向量"""
        # 基础权重 (D1-D4)
        base_weights = self.weights[:4]

        # 扩展权重 (D5-D8) - 从维度模块获取
        extended_weights = []

        for dim_name in ['coherence', 'valence', 'other', 'norm']:
            if dim_name in self.dimensions:
                # 从维度模块获取当前权重或激活度
                dim = self.dimensions[dim_name]
                if hasattr(dim, 'current_weight'):
                    extended_weights.append(dim.current_weight)
                elif hasattr(dim, 'activation'):
                    extended_weights.append(dim.activation)
                else:
                    # 默认中等权重
                    extended_weights.append(0.1)
            else:
                extended_weights.append(0.1)

        # D9: Purpose - 基于目的向量强度
        purpose_weight = float(np.linalg.norm(self.purpose_vector)) if hasattr(self, 'purpose_vector') else 0.1
        extended_weights.append(purpose_weight)

        # 合并并归一化
        all_weights = np.array(list(base_weights) + extended_weights)
        weight_sum = np.sum(all_weights)
        if weight_sum > 0:
            all_weights = all_weights / weight_sum

        return all_weights

    def _update_state(self, observation: Dict):
        """更新状态

        State determination logic:
        - crisis:    critical threat detected
        - concerned: warning-level issue detected
        - growth:    consistently high success rate (last 20 actions)
        - normal:    default state
        """
        if observation.get('critical', False):
            self.current_state = 'crisis'
        elif observation.get('warning', False):
            self.current_state = 'concerned'
        elif len(self.action_history) >= 20:
            recent_success_rate = sum((1 for a in self.action_history[-20:] if a != 'survive')) / 20.0
            if recent_success_rate > 0.8:
                self.current_state = 'growth'
            else:
                self.current_state = 'normal'
        else:
            self.current_state = 'normal'

    def _apply_state_weights(self):
        """根据状态应用权重调整

        Weight allocation follows the design in README:
        - Crisis:     Survival 60%, Curiosity 10%, Influence 20%, Optimization 10%
        - Concerned:  Survival 35%, Curiosity 35%, Influence 20%, Optimization 10%
        - Normal:     Survival 20%, Curiosity 40%, Influence 30%, Optimization 10%
        - Growth:     Survival 20%, Curiosity 20%, Influence 40%, Optimization 20%
        """
        STATE_WEIGHTS = {'crisis': np.array([0.6, 0.1, 0.2, 0.1]), 'concerned': np.array([0.35, 0.35, 0.2, 0.1]), 'normal': np.array([0.2, 0.4, 0.3, 0.1]), 'growth': np.array([0.2, 0.2, 0.4, 0.2])}
        self.weights = STATE_WEIGHTS.get(self.current_state, STATE_WEIGHTS['normal'])

    def _random_action(self) -> str:
        """随机行动"""
        actions = ['cooperate', 'survive', 'delegate', 'reflect']
        return np.random.choice(actions)

    def step(self, observation: Dict=None) -> ActionResult:
        """执行一步（含D5~D8真实更新）"""
        if observation is None:
            observation = {}
        action = self.select_action(observation)
        success = np.random.random() > 0.1
        reward = np.random.random() * 0.5 if success else -0.1
        dim_state = {'action_type': action, 'reward': reward, 'resource_level': observation.get('resource_level', 1.0), 'harm_done': observation.get('harm_done', False), 'weights': self.weights.tolist(), 'purpose_vector': self._get_purpose_vector().tolist() if self._get_purpose_vector() is not None else None}
        coherence_score = 1.0
        if 'coherence' in self.dimensions:
            self.dimensions['coherence'].update(dim_state)
            coherence_score = self.dimensions['coherence'].get_score()
        valence_profile = None
        if 'valence' in self.dimensions:
            self.dimensions['valence'].update(dim_state)
            valence_profile = self.dimensions['valence'].get_profile()
            valence_w = self.dimensions['valence'].get_weights()
            self.weights = 0.95 * self.weights + 0.05 * valence_w
            self.weights = np.maximum(self.weights, 0.05)
            self.weights = self.weights / self.weights.sum()
        social_summary = None
        if 'other' in self.dimensions:
            social_summary = self.dimensions['other'].get_summary()
        if 'norm' in self.dimensions:
            self.dimensions['norm'].update(dim_state)
            norm_penalty = self.dimensions['norm'].compute_penalty(action)
            reward = reward - 0.1 * norm_penalty * abs(reward)
        if self.purpose_generator and self.config.enable_purpose:
            purpose_result = self._update_purpose(coherence_score=coherence_score, valence_profile=valence_profile, social_summary=social_summary)
            if purpose_result.get('purpose_generated') and purpose_result.get('weight_adjustment') is not None:
                adjustment = purpose_result['weight_adjustment']
                if len(adjustment) >= len(self.weights):
                    self.weights = self.weights + adjustment[:len(self.weights)]
                    self.weights = np.maximum(self.weights, 0.05)
                    self.weights = self.weights / self.weights.sum()
                    logger.debug(f'[UnifiedMOSSAgent] Weights adjusted by Purpose: {self.weights.round(3)}')
        self.action_history.append(action)
        if len(self.action_history) > self.max_action_history:
            self.action_history.pop(0)
        result = ActionResult(action_id=f'step_{self.step_count}', action_type=action, success=success, reward=reward, state=self.current_state, purpose_vector=self._get_purpose_vector())
        self.step_count += 1
        return result

    def _update_purpose(self, coherence_score: float=0.5, valence_profile: Optional[Dict]=None, social_summary: Optional[Dict]=None) -> Dict:
        """更新Purpose（传入D5~D8真实数据）"""
        if not self.purpose_generator:
            return {'purpose_generated': False}
        agent_history = [{'action': self.action_history[i] if i < len(self.action_history) else 'unknown', 'reward': 0.1, 'state': self.current_state} for i in range(min(100, self.step_count))]
        result = self.purpose_generator.step(agent_step=self.step_count, agent_history=agent_history, current_weights=self.weights, coherence_score=coherence_score, valence_profile=valence_profile, social_summary=social_summary)
        return result

    def _get_purpose_vector(self) -> Optional[np.ndarray]:
        """获取Purpose向量"""
        if self.purpose_generator:
            return self.purpose_generator.purpose_vector
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 3: Unified Agent V2 - Bridge between v9 and v8.6
# ═══════════════════════════════════════════════════════════════════════════

class AgentMode(Enum):
    """Agent 运行模式"""
    V9_INTEGRATED = "v9"  # 与 autonomous_loop 集成
    V86_STANDALONE = "v86"  # v8.6 独立运行模式
    UNIFIED = "unified"  # 统一模式（实验性）


@dataclass
class UnifiedAgentConfig:
    """统一 Agent 配置 (Phase 3)"""
    agent_id: str = "moss_agent"
    mode: AgentMode = AgentMode.UNIFIED
    
    # v9 配置
    n_dimensions: int = 9
    learning_rate: float = 0.01
    
    # v8.6 配置
    config_path: Optional[str] = None
    max_cycles: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'mode': self.mode.value,
            'n_dimensions': self.n_dimensions,
            'learning_rate': self.learning_rate,
            'config_path': self.config_path,
            'max_cycles': self.max_cycles,
        }


class UnifiedMOSSAgentV2:
    """
    统一 Agent V2 类 (Phase 3)
    
    结合 v9 的架构抽象和 v8.6 的具体实现。
    通过 mode 参数切换不同的运行模式。
    """
    
    def __init__(self, config: Optional[UnifiedAgentConfig] = None):
        self.config = config or UnifiedAgentConfig()
        self.mode = self.config.mode
        
        # 内部组件（延迟初始化）
        self._v9_bridge = None
        self._v86_agent = None
        
        # 统一状态
        self.weights = np.ones(self.config.n_dimensions) / self.config.n_dimensions
        self.state = "initialized"
        
        logger.info(f"UnifiedMOSSAgentV2 created: mode={self.mode.value}, id={self.config.agent_id}")
    
    @classmethod
    def v9_mode(cls, agent_id: str = "moss_v9", **kwargs) -> "UnifiedMOSSAgentV2":
        """创建 v9 模式 Agent"""
        config = UnifiedAgentConfig(
            agent_id=agent_id,
            mode=AgentMode.V9_INTEGRATED,
            **kwargs
        )
        return cls(config)
    
    @classmethod
    def v86_mode(cls, config_path: Optional[str] = None, **kwargs) -> "UnifiedMOSSAgentV2":
        """创建 v8.6 模式 Agent"""
        config = UnifiedAgentConfig(
            agent_id="moss_v86",
            mode=AgentMode.V86_STANDALONE,
            config_path=config_path,
            **kwargs
        )
        return cls(config)
    
    def act(self, observation: Any) -> Any:
        """统一动作接口"""
        if self.mode == AgentMode.V9_INTEGRATED:
            return self._v9_act(observation)
        elif self.mode == AgentMode.V86_STANDALONE:
            return self._v86_act(observation)
        else:
            return self._unified_act(observation)
    
    def learn(self, experience: Any) -> None:
        """统一学习接口"""
        if self.mode == AgentMode.V9_INTEGRATED:
            self._v9_learn(experience)
        elif self.mode == AgentMode.V86_STANDALONE:
            self._v86_learn(experience)
    
    def run(self, max_cycles: Optional[int] = None) -> Dict[str, Any]:
        """运行 Agent"""
        cycles = max_cycles or self.config.max_cycles
        
        if self.mode == AgentMode.V86_STANDALONE:
            return self._v86_run(cycles)
        else:
            logger.warning(f"run() is primarily for v86 mode, current mode={self.mode.value}")
            return {"cycles": 0, "mode": self.mode.value}
    
    def get_status(self) -> Dict[str, Any]:
        """获取统一状态"""
        status = {
            'agent_id': self.config.agent_id,
            'mode': self.mode.value,
            'state': self.state,
            'weights': self.weights.tolist(),
        }
        
        if self._v86_agent:
            status['v86'] = {
                'alive': getattr(self._v86_agent, 'alive', False),
                'cycle': getattr(self._v86_agent, 'cycle', 0),
            }
        
        return status
    
    def _v9_act(self, observation: Any) -> Any:
        """v9 模式动作"""
        if self._v9_bridge is None:
            self._init_v9_bridge()
        
        action_dim = len(self.weights)
        action_probs = self.weights / self.weights.sum()
        action = np.random.choice(action_dim, p=action_probs)
        
        return {"action": action, "weights": self.weights.copy()}
    
    def _v9_learn(self, experience: Any) -> None:
        """v9 模式学习"""
        reward = experience.get('reward', 0)
        self.weights += self.config.learning_rate * reward * self.weights
        self.weights = np.clip(self.weights, 0.01, 1.0)
        self.weights /= self.weights.sum()
    
    def _init_v9_bridge(self) -> None:
        """初始化 v9 桥接组件"""
        try:
            from .agent_bridge import AgentBridge
            self._v9_bridge = AgentBridge(self.config.agent_id)
            logger.info("v9 bridge initialized")
        except ImportError as e:
            logger.warning(f"v9 bridge not available: {e}")
    
    def _v86_act(self, observation: Any) -> Any:
        """v8.6 模式动作"""
        if self._v86_agent is None:
            self._init_v86_agent()
        
        if hasattr(self._v86_agent, 'decide_action'):
            return self._v86_agent.decide_action(observation)
        return {"action": "noop"}
    
    def _v86_learn(self, experience: Any) -> None:
        """v8.6 模式学习"""
        if self._v86_agent and hasattr(self._v86_agent, 'learn'):
            self._v86_agent.learn(experience)
    
    def _v86_run(self, max_cycles: int) -> Dict[str, Any]:
        """v8.6 模式运行"""
        if self._v86_agent is None:
            self._init_v86_agent()
        
        if hasattr(self._v86_agent, 'run'):
            return self._v86_agent.run(max_cycles=max_cycles)
        
        return {"cycles": 0, "error": "v86 agent run not available"}
    
    def _init_v86_agent(self) -> None:
        """初始化 v8.6 Agent"""
        try:
            from .agi_agent import AGIAgent
            
            if self.config.config_path:
                self._v86_agent = AGIAgent(self.config.config_path)
            else:
                self._v86_agent = AGIAgent("config/default_agent.yaml")
            
            logger.info("v8.6 agent initialized")
        except Exception as e:
            logger.error(f"Failed to init v8.6 agent: {e}")
            raise
    
    def _unified_act(self, observation: Any) -> Any:
        """统一模式动作（智能选择）"""
        try:
            return self._v86_act(observation)
        except Exception:
            return self._v9_act(observation)


def create_unified_agent_v2(
    mode: str = "unified",
    agent_id: str = "moss_001",
    **kwargs
) -> UnifiedMOSSAgentV2:
    """创建统一 Agent V2 的便捷函数"""
    mode_enum = AgentMode(mode)
    config = UnifiedAgentConfig(agent_id=agent_id, mode=mode_enum, **kwargs)
    return UnifiedMOSSAgentV2(config)