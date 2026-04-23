"""
MOSS v7.1 - Meta-SME Integration with mves Drive System
Meta-SME 与 mves 驱动系统集成模块

核心功能:
- 驱动权重自动调整
- 元驱动与 Meta-SME 协同
- 性能监控与反馈循环
- 37+ 环境支持

Author: MOSS Project
Date: 2026-04-19
Version: 7.1.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
import json

from .meta_sme import MetaSME, ModificationType, ModificationProposal
from .meta_drive.meta_controller import MetaController
from .meta_drive.self_model import SelfModel
from .drive_manager import DriveManager


@dataclass
class DrivePerformanceMetrics:
    """驱动性能指标"""
    drive_name: str
    avg_reward: float
    activation_frequency: float
    success_rate: float
    weight: float
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'drive_name': self.drive_name,
            'avg_reward': self.avg_reward,
            'activation_frequency': self.activation_frequency,
            'success_rate': self.success_rate,
            'weight': self.weight,
            'timestamp': self.timestamp.isoformat()
        }


class MetaSMEDriveIntegration:
    """
    Meta-SME 驱动集成器
    
    将 Meta-SME 的自我修改能力与 mves 的驱动系统深度集成
    """
    
    def __init__(self, 
                 meta_sme: MetaSME,
                 drive_manager: DriveManager,
                 meta_controller: Optional[MetaController] = None):
        """
        Args:
            meta_sme: Meta-SME 实例
            drive_manager: 驱动管理器
            meta_controller: 元控制器（可选）
        """
        self.meta_sme = meta_sme
        self.drive_manager = drive_manager
        self.meta_controller = meta_controller
        
        # 驱动性能历史
        self.drive_performance_history: Dict[str, List[DrivePerformanceMetrics]] = {}
        
        # 集成统计
        self.stats = {
            'weight_adjustments_proposed': 0,
            'weight_adjustments_applied': 0,
            'drive_additions_proposed': 0,
            'drive_removals_proposed': 0,
            'meta_drive_collaborations': 0
        }
        
        # 配置
        self.config = {
            'weight_adjustment_threshold': 0.05,  # 5% 调整阈值
            'min_history_length': 10,  # 最小历史长度
            'performance_window': 50,  # 性能窗口
            'auto_adjust_weights': False,  # 自动调整权重
            'collaborate_with_meta_drive': True  # 与元驱动协作
        }
    
    def record_drive_performance(self, drive_name: str,
                                  avg_reward: float,
                                  activation_frequency: float,
                                  success_rate: float):
        """
        记录驱动性能
        
        Args:
            drive_name: 驱动名称
            avg_reward: 平均奖励
            activation_frequency: 激活频率
            success_rate: 成功率
        """
        # 获取当前权重
        weight = 0.25  # 默认值
        if hasattr(self.drive_manager, 'drives') and drive_name in self.drive_manager.drives:
            weight = self.drive_manager.drives[drive_name].weight
        
        metrics = DrivePerformanceMetrics(
            drive_name=drive_name,
            avg_reward=avg_reward,
            activation_frequency=activation_frequency,
            success_rate=success_rate,
            weight=weight,
            timestamp=datetime.now()
        )
        
        if drive_name not in self.drive_performance_history:
            self.drive_performance_history[drive_name] = []
        
        self.drive_performance_history[drive_name].append(metrics)
        
        # 限制历史长度
        max_history = self.config['performance_window'] * 2
        if len(self.drive_performance_history[drive_name]) > max_history:
            self.drive_performance_history[drive_name] = \
                self.drive_performance_history[drive_name][-max_history:]
        
        # 更新 Meta-SME 性能
        overall_performance = self._calculate_overall_performance()
        self.meta_sme.record_performance(overall_performance)
    
    def _calculate_overall_performance(self) -> float:
        """计算整体性能"""
        if not self.drive_performance_history:
            return 0.5
        
        total_score = 0.0
        count = 0
        
        for drive_name, history in self.drive_performance_history.items():
            if history:
                recent = history[-10:] if len(history) >= 10 else history
                avg_reward = np.mean([m.avg_reward for m in recent])
                avg_success = np.mean([m.success_rate for m in recent])
                score = (avg_reward + avg_success) / 2
                total_score += score
                count += 1
        
        return total_score / count if count > 0 else 0.5
    
    def analyze_drive_efficiency(self, drive_name: str) -> Dict:
        """
        分析驱动效率
        
        Args:
            drive_name: 驱动名称
            
        Returns:
            效率分析结果
        """
        if drive_name not in self.drive_performance_history:
            return {'error': 'No history for this drive'}
        
        history = self.drive_performance_history[drive_name]
        
        if len(history) < self.config['min_history_length']:
            return {'error': 'Insufficient history'}
        
        recent = history[-self.config['performance_window']:]
        older = history[-self.config['performance_window']*2:-self.config['performance_window']]
        
        if not older:
            older = history[:len(history)//2]
        
        analysis = {
            'drive_name': drive_name,
            'recent_performance': {
                'avg_reward': np.mean([m.avg_reward for m in recent]),
                'avg_success_rate': np.mean([m.success_rate for m in recent]),
                'avg_activation': np.mean([m.activation_frequency for m in recent]),
                'current_weight': recent[-1].weight if recent else 0.25
            },
            'trend': {
                'reward_trend': np.mean([m.avg_reward for m in recent]) - \
                               np.mean([m.avg_reward for m in older]) if older else 0,
                'success_trend': np.mean([m.success_rate for m in recent]) - \
                                np.mean([m.success_rate for m in older]) if older else 0
            },
            'efficiency_score': 0.0,
            'recommendation': 'maintain'
        }
        
        # 计算效率分数
        analysis['efficiency_score'] = (
            analysis['recent_performance']['avg_reward'] * 0.4 +
            analysis['recent_performance']['avg_success_rate'] * 0.4 +
            analysis['recent_performance']['avg_activation'] * 0.2
        )
        
        # 生成建议
        if analysis['trend']['reward_trend'] < -0.1:
            analysis['recommendation'] = 'decrease_weight'
        elif analysis['trend']['reward_trend'] > 0.1:
            analysis['recommendation'] = 'increase_weight'
        elif analysis['efficiency_score'] < 0.3:
            analysis['recommendation'] = 'consider_removal'
        
        return analysis
    
    def propose_weight_adjustments(self) -> List[ModificationProposal]:
        """
        提议权重调整
        
        Returns:
            修改提案列表
        """
        proposals = []
        
        for drive_name in self.drive_performance_history.keys():
            analysis = self.analyze_drive_efficiency(drive_name)
            
            if 'error' in analysis:
                continue
            
            current_weight = analysis['recent_performance']['current_weight']
            recommendation = analysis['recommendation']
            
            if recommendation == 'increase_weight':
                new_weight = min(0.9, current_weight * 1.1)
            elif recommendation == 'decrease_weight':
                new_weight = max(0.05, current_weight * 0.9)
            else:
                continue
            
            # 检查调整幅度
            if abs(new_weight - current_weight) < self.config['weight_adjustment_threshold']:
                continue
            
            # 生成提案
            proposal = self.meta_sme.generate_proposal(
                target_module=f"agi.drive_manager",
                mod_type=ModificationType.WEIGHT_ADJUSTMENT,
                description=f"Adjust {drive_name} weight: {current_weight:.3f} -> {new_weight:.3f}",
                ast_patch={
                    'target_function': 'update_drive_weight',
                    'drive_name': drive_name,
                    'current_weight': current_weight,
                    'new_weight': new_weight,
                    'new_code': f'# Weight adjustment for {drive_name}'
                },
                expected_impact={
                    'min_performance_improvement': 0.01,
                    'max_regression': 0.05,
                    'auto_rollback_on_failure': True
                }
            )
            
            if proposal:
                proposals.append(proposal)
                self.stats['weight_adjustments_proposed'] += 1
        
        return proposals
    
    def apply_weight_adjustment(self, proposal: ModificationProposal) -> bool:
        """
        应用权重调整
        
        Args:
            proposal: 修改提案
            
        Returns:
            是否成功
        """
        ast_patch = proposal.ast_patch
        drive_name = ast_patch.get('drive_name')
        new_weight = ast_patch.get('new_weight')
        
        if not drive_name or new_weight is None:
            return False
        
        # 应用到驱动管理器
        if hasattr(self.drive_manager, 'drives') and drive_name in self.drive_manager.drives:
            self.drive_manager.drives[drive_name].weight = new_weight
            self.stats['weight_adjustments_applied'] += 1
            return True
        
        return False
    
    def collaborate_with_meta_controller(self, state: np.ndarray, 
                                         performance: float) -> Dict:
        """
        与元控制器协作
        
        Args:
            state: 当前状态
            performance: 当前性能
            
        Returns:
            协作结果
        """
        if not self.meta_controller:
            return {'error': 'Meta controller not available'}
        
        if not self.config['collaborate_with_meta_drive']:
            return {'error': 'Collaboration disabled'}
        
        # 更新元控制器
        self.meta_controller.step(state, performance)
        
        # 获取元驱动影响
        meta_influence = self.meta_controller.get_meta_drive_influence()
        
        # 如果元驱动影响高，生成协同提案
        if meta_influence > 0.6:
            # 元驱动建议修改，Meta-SME 生成具体提案
            proposal = self.meta_sme.generate_proposal(
                target_module="agi.meta_drive.meta_controller",
                mod_type=ModificationType.PARAMETER_UPDATE,
                description="Collaborative adjustment based on meta-drive influence",
                ast_patch={
                    'target_function': 'collaborative_update',
                    'meta_influence': meta_influence,
                    'new_code': f'# Collaborative update, meta_influence={meta_influence:.3f}'
                },
                expected_impact={
                    'min_performance_improvement': 0.005,
                    'max_regression': 0.03
                }
            )
            
            self.stats['meta_drive_collaborations'] += 1
            
            return {
                'meta_influence': meta_influence,
                'proposal_generated': proposal is not None,
                'proposal_id': proposal.proposal_id if proposal else None
            }
        
        return {
            'meta_influence': meta_influence,
            'proposal_generated': False
        }
    
    def step(self, state: np.ndarray, performance: float) -> Dict:
        """
        集成步骤
        
        Args:
            state: 当前状态
            performance: 当前性能
            
        Returns:
            步骤结果
        """
        results = {
            'proposals_generated': 0,
            'proposals_applied': 0,
            'collaboration_result': None
        }
        
        # 记录性能
        self.meta_sme.record_performance(performance)
        
        # 与元控制器协作
        if self.meta_controller:
            collab_result = self.collaborate_with_meta_controller(state, performance)
            results['collaboration_result'] = collab_result
            if collab_result.get('proposal_generated'):
                results['proposals_generated'] += 1
        
        # 提议权重调整
        if self.meta_sme.should_generate_proposal():
            proposals = self.propose_weight_adjustments()
            results['proposals_generated'] += len(proposals)
            
            # 如果启用自动调整，应用提案
            if self.config['auto_adjust_weights']:
                for proposal in proposals:
                    if proposal.safety_level.name == 'SAFE':
                        # 自动应用安全级别的调整
                        if self.apply_weight_adjustment(proposal):
                            results['proposals_applied'] += 1
        
        return results
    
    def get_status(self) -> Dict:
        """获取集成状态"""
        return {
            'stats': self.stats,
            'config': self.config,
            'drive_performance_history': {
                name: len(history) 
                for name, history in self.drive_performance_history.items()
            },
            'meta_sme_status': self.meta_sme.get_status(),
            'num_drives_monitored': len(self.drive_performance_history)
        }
    
    def export_drive_analysis(self, drive_name: Optional[str] = None) -> Dict:
        """
        导出驱动分析
        
        Args:
            drive_name: 驱动名称，如果为None则导出所有
            
        Returns:
            分析结果
        """
        if drive_name:
            return {
                drive_name: self.analyze_drive_efficiency(drive_name)
            }
        
        return {
            name: self.analyze_drive_efficiency(name)
            for name in self.drive_performance_history.keys()
        }


# 环境适配器 - 支持 37+ 环境
class EnvironmentAwareMetaSME:
    """
    环境感知 Meta-SME
    
    为不同环境提供特定的 Meta-SME 配置
    """
    
    ENVIRONMENT_CONFIGS = {
        # TextWorld 环境
        'textworld': {
            'weight_adjustment_threshold': 0.03,
            'performance_window': 30,
            'auto_adjust_weights': False
        },
        # Atari 环境
        'atari': {
            'weight_adjustment_threshold': 0.05,
            'performance_window': 100,
            'auto_adjust_weights': False
        },
        # Procgen 环境
        'procgen': {
            'weight_adjustment_threshold': 0.04,
            'performance_window': 50,
            'auto_adjust_weights': False
        },
        # 默认配置
        'default': {
            'weight_adjustment_threshold': 0.05,
            'performance_window': 50,
            'auto_adjust_weights': False
        }
    }
    
    def __init__(self, integration: MetaSMEDriveIntegration):
        self.integration = integration
        self.current_environment = 'default'
    
    def set_environment(self, env_type: str):
        """
        设置当前环境类型
        
        Args:
            env_type: 环境类型 (textworld, atari, procgen, etc.)
        """
        self.current_environment = env_type
        config = self.ENVIRONMENT_CONFIGS.get(env_type, self.ENVIRONMENT_CONFIGS['default'])
        self.integration.config.update(config)
    
    def get_environment_config(self) -> Dict:
        """获取当前环境配置"""
        return {
            'environment': self.current_environment,
            'config': self.integration.config
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.1 - Meta-SME Integration Test")
    print("=" * 60)
    
    # 创建 Mock 驱动管理器
    class MockDrive:
        def __init__(self, name, weight=0.25):
            self.name = name
            self.weight = weight
    
    class MockDriveManager:
        def __init__(self):
            self.drives = {
                'survival': MockDrive('survival', 0.2),
                'curiosity': MockDrive('curiosity', 0.4),
                'influence': MockDrive('influence', 0.3),
                'optimization': MockDrive('optimization', 0.1)
            }
    
    # 创建组件
    from .meta_sme import MetaSME
    
    meta_sme = MetaSME(enable_auto_modify=False, require_human_approval=True)
    drive_manager = MockDriveManager()
    
    integration = MetaSMEDriveIntegration(meta_sme, drive_manager)
    
    # 模拟性能记录
    print("\n1. Recording drive performance...")
    for i in range(30):
        integration.record_drive_performance(
            'survival',
            avg_reward=0.5 + np.random.randn() * 0.1,
            activation_frequency=0.3 + np.random.randn() * 0.05,
            success_rate=0.7 + np.random.randn() * 0.1
        )
        integration.record_drive_performance(
            'curiosity',
            avg_reward=0.6 + np.random.randn() * 0.1,
            activation_frequency=0.5 + np.random.randn() * 0.05,
            success_rate=0.8 + np.random.randn() * 0.1
        )
    print(f"   Recorded {len(integration.drive_performance_history)} drives")
    
    # 分析驱动效率
    print("\n2. Analyzing drive efficiency...")
    analysis = integration.analyze_drive_efficiency('survival')
    print(f"   Survival drive efficiency: {analysis.get('efficiency_score', 0):.3f}")
    print(f"   Recommendation: {analysis.get('recommendation', 'N/A')}")
    
    # 提议权重调整
    print("\n3. Proposing weight adjustments...")
    proposals = integration.propose_weight_adjustments()
    print(f"   Generated {len(proposals)} proposals")
    for prop in proposals:
        print(f"   - {prop.description}")
    
    # 设置环境
    print("\n4. Setting environment to 'textworld'...")
    env_aware = EnvironmentAwareMetaSME(integration)
    env_aware.set_environment('textworld')
    config = env_aware.get_environment_config()
    print(f"   Environment: {config['environment']}")
    print(f"   Threshold: {config['config']['weight_adjustment_threshold']}")
    
    # 获取状态
    print("\n5. Integration Status:")
    status = integration.get_status()
    print(f"   Proposals proposed: {status['stats']['weight_adjustments_proposed']}")
    print(f"   Drives monitored: {status['num_drives_monitored']}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)