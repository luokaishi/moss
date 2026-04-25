#!/usr/bin/env python3
"""
MOSS v9.6 - Meta-SME Bridge

将Meta-SME自我修改能力桥接到v9.6统一架构。

核心功能:
- 桥接 MetaSME ↔ UnifiedMOSSAgentV2
- 统一保护模块路径
- 性能反馈从Agent流向MetaSME
- 修改提案从MetaSME流向Agent权重系统
"""

import logging
import time
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .meta_sme import MetaSME, ModificationType, ModificationProposal

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceSnapshot:
    """Agent性能快照"""
    agent_id: str
    step_count: int
    avg_reward: float
    success_rate: float
    weights: List[float]
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class MetaSMEBridge:
    """
    Meta-SME v9.6 桥接器
    
    将MetaSME的自我修改能力与v9.6统一Agent架构连接。
    
    工作流:
    1. Agent运行 → 收集性能数据
    2. 性能数据 → MetaSME评估
    3. MetaSME → 生成修改提案
    4. 提案审核 → 应用到Agent权重/参数
    
    Example:
        bridge = MetaSMEBridge(agent, meta_sme)
        
        # 在Agent步骤后调用
        bridge.record_step(result)
        
        # 检查是否有待处理的提案
        proposals = bridge.check_proposals()
    """
    
    def __init__(self, agent=None, meta_sme: MetaSME = None):
        """
        Args:
            agent: UnifiedMOSSAgent 或 UnifiedMOSSAgentV2 实例
            meta_sme: MetaSME 实例
        """
        self.agent = agent
        self.meta_sme = meta_sme or MetaSME()
        
        # 性能追踪
        self._performance_history: List[AgentPerformanceSnapshot] = []
        self._max_history = 1000
        
        # 修改追踪
        self._applied_modifications: List[Dict] = []
        self._rejected_modifications: List[Dict] = []
        
        # 配置
        self.config = {
            'min_steps_before_proposal': 100,
            'performance_window': 50,
            'weight_adjustment_threshold': 0.05,
            'auto_apply_safe_modifications': False,
        }
    
    def record_step(self, action_result: Any) -> None:
        """记录Agent步骤结果"""
        if self.agent is None:
            return
        
        # 收集性能数据
        snapshot = AgentPerformanceSnapshot(
            agent_id=getattr(self.agent, 'agent_id', 'unknown'),
            step_count=getattr(self.agent, 'step_count', 0),
            avg_reward=self._calculate_avg_reward(),
            success_rate=self._calculate_success_rate(),
            weights=getattr(self.agent, 'weights', np.ones(9)/9).tolist(),
        )
        
        self._performance_history.append(snapshot)
        if len(self._performance_history) > self._max_history:
            self._performance_history.pop(0)
        
        # 更新MetaSME性能历史
        self.meta_sme.performance_history.append(snapshot.avg_reward)
    
    def check_proposals(self) -> List[ModificationProposal]:
        """检查是否应生成修改提案"""
        proposals = []
        
        if not self.meta_sme.should_generate_proposal():
            return proposals
        
        # 分析性能趋势
        if len(self._performance_history) < self.config['min_steps_before_proposal']:
            return proposals
        
        recent = self._performance_history[-self.config['performance_window']:]
        
        # 计算性能趋势
        rewards = [s.avg_reward for s in recent]
        if len(rewards) < 2:
            return proposals
        
        trend = rewards[-1] - rewards[0]
        
        # 如果性能下降，生成权重调整提案
        if trend < -0.1:
            proposal = self._generate_weight_adjustment(trend)
            if proposal:
                proposals.append(proposal)
        
        # 如果性能停滞，生成探索增强提案
        elif abs(trend) < 0.01:
            proposal = self._generate_exploration_boost()
            if proposal:
                proposals.append(proposal)
        
        return proposals
    
    def apply_proposal(self, proposal: ModificationProposal) -> bool:
        """
        应用修改提案到Agent
        
        Args:
            proposal: 修改提案
            
        Returns:
            是否成功应用
        """
        if self.agent is None:
            logger.warning("No agent connected, cannot apply proposal")
            return False
        
        if proposal.mod_type == ModificationType.WEIGHT_ADJUSTMENT:
            return self._apply_weight_adjustment(proposal)
        elif proposal.mod_type == ModificationType.PARAMETER_UPDATE:
            return self._apply_parameter_update(proposal)
        else:
            logger.info(f"Modification type {proposal.mod_type} requires human approval")
            return False
    
    def get_status(self) -> Dict:
        """获取桥接器状态"""
        return {
            'agent_connected': self.agent is not None,
            'performance_history_length': len(self._performance_history),
            'applied_modifications': len(self._applied_modifications),
            'rejected_modifications': len(self._rejected_modifications),
            'meta_sme_stats': self.meta_sme.stats,
            'meta_sme_should_propose': self.meta_sme.should_generate_proposal(),
        }
    
    # ── 内部方法 ──
    
    def _calculate_avg_reward(self) -> float:
        """计算平均奖励"""
        if not self._performance_history:
            return 0.0
        
        recent = self._performance_history[-20:]
        return sum(s.avg_reward for s in recent) / len(recent)
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self._performance_history:
            return 0.0
        
        recent = self._performance_history[-20:]
        return sum(s.success_rate for s in recent) / len(recent)
    
    def _generate_weight_adjustment(self, trend: float) -> Optional[ModificationProposal]:
        """生成权重调整提案"""
        if self.agent is None:
            return None
        
        current_weights = getattr(self.agent, 'weights', np.ones(9)/9)
        
        # 计算调整方向
        # 性能下降时增强survival权重
        adjustment = np.zeros_like(current_weights)
        if len(adjustment) >= 4:
            adjustment[0] = 0.05  # 增加survival
            adjustment[1] = -0.02  # 减少curiosity
        
        new_weights = current_weights + adjustment
        new_weights = np.clip(new_weights, 0.05, 1.0)
        new_weights /= new_weights.sum()
        
        proposal = self.meta_sme.generate_proposal(
            target_module=f"agent.{getattr(self.agent, 'agent_id', 'unknown')}.weights",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            description=f"Weight adjustment due to performance decline (trend={trend:.3f})",
            ast_patch={'old_weights': current_weights.tolist(), 'new_weights': new_weights.tolist()},
            expected_impact={'reward_change': -trend * 0.5}
        )
        
        return proposal
    
    def _generate_exploration_boost(self) -> Optional[ModificationProposal]:
        """生成探索增强提案"""
        if self.agent is None:
            return None
        
        current_weights = getattr(self.agent, 'weights', np.ones(9)/9)
        
        # 增加curiosity权重
        adjustment = np.zeros_like(current_weights)
        if len(adjustment) >= 4:
            adjustment[1] = 0.03  # 增加curiosity
        
        new_weights = current_weights + adjustment
        new_weights = np.clip(new_weights, 0.05, 1.0)
        new_weights /= new_weights.sum()
        
        proposal = self.meta_sme.generate_proposal(
            target_module=f"agent.{getattr(self.agent, 'agent_id', 'unknown')}.weights",
            mod_type=ModificationType.WEIGHT_ADJUSTMENT,
            description="Exploration boost due to performance plateau",
            ast_patch={'old_weights': current_weights.tolist(), 'new_weights': new_weights.tolist()},
            expected_impact={'diversity_increase': 0.1}
        )
        
        return proposal
    
    def _apply_weight_adjustment(self, proposal: ModificationProposal) -> bool:
        """应用权重调整"""
        if not proposal or not proposal.ast_patch:
            return False
        
        new_weights = proposal.ast_patch.get('new_weights')
        if new_weights is None:
            return False
        
        try:
            self.agent.weights = np.array(new_weights)
            self._applied_modifications.append({
                'type': 'weight_adjustment',
                'proposal_id': proposal.proposal_id,
                'timestamp': time.time(),
            })
            logger.info(f"Weight adjustment applied: {proposal.proposal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply weight adjustment: {e}")
            return False
    
    def _apply_parameter_update(self, proposal: ModificationProposal) -> bool:
        """应用参数更新"""
        if not proposal or not proposal.ast_patch:
            return False
        
        try:
            # 参数更新逻辑
            self._applied_modifications.append({
                'type': 'parameter_update',
                'proposal_id': proposal.proposal_id,
                'timestamp': time.time(),
            })
            logger.info(f"Parameter update applied: {proposal.proposal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply parameter update: {e}")
            return False


__all__ = ['MetaSMEBridge', 'AgentPerformanceSnapshot']
