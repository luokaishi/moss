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
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class MOSSConfig:
    """
    MOSS Agent 统一配置
    
    整合所有版本的配置参数
    """
    # 基础配置
    agent_id: str = "moss_agent"
    version: str = "5.0.0"
    
    # 维度配置 (D1-D9)
    enable_survival: bool = True
    enable_curiosity: bool = True
    enable_influence: bool = True
    enable_optimization: bool = True
    enable_coherence: bool = True      # D5
    enable_valence: bool = True        # D6
    enable_other: bool = True          # D7
    enable_norm: bool = True           # D8
    enable_purpose: bool = True        # D9
    
    # Purpose配置
    purpose_interval: int = 2000       # Purpose重新生成间隔
    purpose_history_window: int = 100
    
    # 实验配置
    log_dir: str = "experiments"
    checkpoint_interval: int = 1000    # 检查点保存间隔
    
    # 安全配置
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
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'success': self.success,
            'reward': self.reward,
            'state': self.state,
            'purpose_vector': self.purpose_vector.tolist() if self.purpose_vector is not None else None,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class BaseMOSSAgent(ABC):
    """
    MOSS Agent 抽象基类
    
    所有具体Agent实现必须继承此类
    """
    
    def __init__(self, config: MOSSConfig = None):
        self.config = config or MOSSConfig()
        self.agent_id = self.config.agent_id
        self.state = AgentState.INITIALIZING
        self.step_count = 0
        
        # 初始化日志
        self._setup_logging()
        
        # 历史记录
        self.history: List[ActionResult] = []
        self.max_history = 10000
        
        # 权重向量 (D1-D4)
        self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        
        # 状态
        self.current_state = "normal"
        
        logger.info(f"[BaseMOSSAgent] {self.agent_id} initialized")
        self.state = AgentState.IDLE
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(
            log_dir / f"{self.agent_id}_{datetime.now():%Y%m%d_%H%M%S}.log"
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    
    @abstractmethod
    def step(self, observation: Dict = None) -> ActionResult:
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
        logger.debug(f"[BaseMOSSAgent] Weights updated: {self.weights}")
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        return {
            'agent_id': self.agent_id,
            'state': self.state.value,
            'step_count': self.step_count,
            'weights': self.weights.tolist(),
            'current_state': self.current_state
        }
    
    def save_checkpoint(self, path: str = None):
        """保存检查点"""
        if path is None:
            path = f"{self.config.log_dir}/{self.agent_id}_checkpoint_{self.step_count}.json"
        
        checkpoint = {
            'agent_id': self.agent_id,
            'step_count': self.step_count,
            'weights': self.weights.tolist(),
            'config': self.config.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.info(f"[BaseMOSSAgent] Checkpoint saved: {path}")
    
    def load_checkpoint(self, path: str):
        """加载检查点"""
        with open(path, 'r') as f:
            checkpoint = json.load(f)
        
        self.step_count = checkpoint['step_count']
        self.weights = np.array(checkpoint['weights'])
        logger.info(f"[BaseMOSSAgent] Checkpoint loaded: {path}")
    
    def run(self, steps: int = 1000, callback=None):
        """
        运行多步
        
        Args:
            steps: 步数
            callback: 每步回调函数(step, result)
        """
        self.state = AgentState.RUNNING
        logger.info(f"[BaseMOSSAgent] Running {steps} steps")
        
        try:
            for i in range(steps):
                result = self.step()
                self.history.append(result)
                self.step_count += 1
                
                # 保存检查点
                if self.step_count % self.config.checkpoint_interval == 0:
                    self.save_checkpoint()
                
                # 回调
                if callback:
                    callback(self.step_count, result)
                    
        except Exception as e:
            logger.error(f"[BaseMOSSAgent] Error during run: {e}")
            self.state = AgentState.ERROR
            raise
        
        self.state = AgentState.IDLE
        logger.info(f"[BaseMOSSAgent] Run completed: {self.step_count} steps")


class UnifiedMOSSAgent(BaseMOSSAgent):
    """
    统一MOSS Agent实现 (v3.1 + v4.x 整合)
    
    功能：
    - 完整的9维系统 (D1-D9)
    - 真实世界桥接支持
    - 可配置的维度开关
    """
    
    def __init__(self, config: MOSSConfig = None):
        super().__init__(config)
        
        # 初始化维度模块
        self._init_dimensions()
        
        # Purpose Generator (如果启用D9)
        self.purpose_generator = None
        if self.config.enable_purpose:
            self._init_purpose_generator()
        
        # 行动历史（用于Purpose反思）
        self.action_history = []
        self.max_action_history = 1000
        
        logger.info(f"[UnifiedMOSSAgent] {self.agent_id} ready with {self._get_enabled_dimensions()} dimensions")
    
    def _init_dimensions(self):
        """初始化各维度模块"""
        self.dimensions = {}
        
        # D1-D4: 基础维度
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
        
        # D5-D8: 扩展维度
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
            self.purpose_generator = PurposeGenerator(
                agent_id=self.agent_id,
                generation_interval=self.config.purpose_interval,
                output_dir=self.config.log_dir
            )
            # 尝试加载之前的Purpose历史
            self.purpose_generator.load()
            logger.info("[UnifiedMOSSAgent] Purpose Generator initialized")
        except ImportError as e:
            logger.warning(f"[UnifiedMOSSAgent] Could not load Purpose Generator: {e}")
            self.purpose_generator = None
    
    def _get_enabled_dimensions(self) -> int:
        """获取启用的维度数"""
        return sum([
            self.config.enable_survival,
            self.config.enable_curiosity,
            self.config.enable_influence,
            self.config.enable_optimization,
            self.config.enable_coherence,
            self.config.enable_valence,
            self.config.enable_other,
            self.config.enable_norm,
            self.config.enable_purpose
        ])
    
    def select_action(self, observation: Dict) -> str:
        """基于当前权重选择行动"""
        # 状态检测
        self._update_state(observation)
        
        # 根据状态调整权重
        self._apply_state_weights()
        
        # 选择行动 (epsilon-greedy)
        if np.random.random() < 0.1:  # 10%探索
            return self._random_action()
        
        # 利用：选择权重的行动
        dim_names = ['survival', 'curiosity', 'influence', 'optimization']
        weights = self.weights[:4]
        selected_dim = dim_names[np.argmax(weights)]
        
        if selected_dim in self.dimensions:
            return self.dimensions[selected_dim].suggest_action()
        
        return self._random_action()
    
    def _update_state(self, observation: Dict):
        """更新状态"""
        # 简化的状态检测逻辑
        if observation.get('critical', False):
            self.current_state = "crisis"
        elif observation.get('warning', False):
            self.current_state = "concerned"
        else:
            self.current_state = "normal"
    
    def _apply_state_weights(self):
        """根据状态应用权重调整"""
        if self.current_state == "crisis":
            self.weights = np.array([0.60, 0.10, 0.20, 0.10])
        elif self.current_state == "concerned":
            self.weights = np.array([0.35, 0.35, 0.20, 0.10])
        # normal: 保持当前权重
    
    def _random_action(self) -> str:
        """随机行动"""
        actions = [
            'explore', 'survive', 'influence', 'optimize',
            'cooperate', 'maintain', 'learn', 'share'
        ]
        return np.random.choice(actions)
    
    def step(self, observation: Dict = None) -> ActionResult:
        """执行一步"""
        if observation is None:
            observation = {}
        
        # 选择行动
        action = self.select_action(observation)
        
        # 执行行动 (简化版)
        success = np.random.random() > 0.1  # 90%成功率
        reward = np.random.random() * 0.5 if success else -0.1
        
        # 更新Purpose (如果启用)
        if self.purpose_generator and self.config.enable_purpose:
            purpose_result = self._update_purpose()
            # 应用Purpose到权重
            if purpose_result.get('purpose_generated') and purpose_result.get('weight_adjustment') is not None:
                adjustment = purpose_result['weight_adjustment']
                if len(adjustment) >= len(self.weights):
                    self.weights = self.weights + adjustment[:len(self.weights)]
                    self.weights = np.maximum(self.weights, 0.05)
                    self.weights = self.weights / self.weights.sum()
                    logger.debug(f"[UnifiedMOSSAgent] Weights adjusted by Purpose: {self.weights.round(3)}")
        
        # 记录行动历史
        self.action_history.append(action)
        if len(self.action_history) > self.max_action_history:
            self.action_history.pop(0)
        
        result = ActionResult(
            action_id=f"step_{self.step_count}",
            action_type=action,
            success=success,
            reward=reward,
            state=self.current_state,
            purpose_vector=self._get_purpose_vector()
        )
        
        self.step_count += 1
        return result
    
    def _update_purpose(self) -> Dict:
        """更新Purpose"""
        if not self.purpose_generator:
            return {'purpose_generated': False}
        
        # 构建历史数据（简化版，实际应从历史记录中提取）
        agent_history = [
            {'action': self.action_history[i] if i < len(self.action_history) else 'unknown',
             'reward': 0.1,
             'state': self.current_state}
            for i in range(min(100, self.step_count))
        ]
        
        result = self.purpose_generator.step(
            agent_step=self.step_count,
            agent_history=agent_history,
            current_weights=self.weights,
            coherence_score=0.5,  # 简化值
            valence_profile=None,
            social_summary=None
        )
        
        return result
    
    def _get_purpose_vector(self) -> Optional[np.ndarray]:
        """获取Purpose向量"""
        if self.purpose_generator:
            return self.purpose_generator.purpose_vector
        return None
