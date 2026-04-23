"""
DriveCompetition - 驱动力竞争机制

实现优胜劣汰的自然选择机制：
1. 试用期机制：新驱动从低权重开始，逐步验证
2. 表现评估：基于历史表现动态调整权重
3. 淘汰机制：长期表现不佳的驱动被移除
4. 竞争平衡：防止单一驱动垄断

基于 Copilot 评估报告建议，解决当前驱动权重固定、无竞争淘汰的问题。
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DriveStatus(Enum):
    """驱动状态"""
    PROBATION = "probation"      # 试用期
    ACTIVE = "active"            # 正式期
    AT_RISK = "at_risk"          # 风险期 (接近淘汰)
    ELIMINATED = "eliminated"    # 已淘汰


@dataclass
class DrivePerformance:
    """驱动表现记录"""
    drive_name: str
    age: int = 0                          # 驱动年龄 (周期数)
    status: DriveStatus = DriveStatus.PROBATION
    
    # 表现历史
    reward_history: List[float] = field(default_factory=list)
    score_history: List[float] = field(default_factory=list)
    
    # 统计指标
    total_rewards: float = 0.0
    avg_reward: float = 0.0
    reward_variance: float = 0.0
    
    # 关键事件
    promoted_at: Optional[int] = None     # 转正周期
    last_evaluated: int = 0               # 上次评估周期
    warnings: int = 0                     # 警告次数
    
    def update(self, cycle: int, reward: float, score: float):
        """更新表现记录"""
        self.age = cycle
        self.reward_history.append(reward)
        self.score_history.append(score)
        
        # 限制历史长度
        if len(self.reward_history) > 200:
            self.reward_history = self.reward_history[-200:]
        if len(self.score_history) > 200:
            self.score_history = self.score_history[-200:]
        
        # 更新统计
        self._update_stats()
    
    def _update_stats(self):
        """更新统计指标"""
        if self.reward_history:
            self.total_rewards = sum(self.reward_history)
            self.avg_reward = np.mean(self.reward_history)
            self.reward_variance = np.var(self.reward_history)
    
    def get_recent_performance(self, window: int = 100) -> Dict:
        """获取近期表现"""
        recent_rewards = self.reward_history[-window:] if self.reward_history else []
        recent_scores = self.score_history[-window:] if self.score_history else []
        
        return {
            'avg_reward': np.mean(recent_rewards) if recent_rewards else 0.0,
            'std_reward': np.std(recent_rewards) if recent_rewards else 0.0,
            'avg_score': np.mean(recent_scores) if recent_scores else 0.0,
            'trend': self._calculate_trend(recent_rewards),
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势 (-1 下降, 0 平稳, 1 上升)"""
        if len(values) < 20:
            return 0.0
        
        first_half = np.mean(values[:len(values)//2])
        second_half = np.mean(values[len(values)//2:])
        
        diff = second_half - first_half
        if abs(diff) < 0.05:
            return 0.0
        return 1.0 if diff > 0 else -1.0


@dataclass
class CompetitionConfig:
    """竞争机制配置"""
    # 试用期
    probation_period: int = 500           # 试用期周期数
    probation_growth_rate: float = 1.01   # 试用期权重增长率
    probation_max_weight: float = 0.10    # 试用期最大权重
    
    # 评估窗口
    evaluation_window: int = 100          # 表现评估窗口
    evaluation_interval: int = 50         # 评估间隔周期
    
    # 权重调整
    growth_rate: float = 1.05             # 表现良好时的增长率
    decay_rate: float = 0.95              # 表现不佳时的衰减率
    min_weight: float = 0.02              # 最小权重 (低于则淘汰)
    max_weight: float = 0.35              # 最大权重
    
    # 淘汰机制
    warning_threshold: int = 3            # 警告阈值
    elimination_cooldown: int = 200       # 淘汰后冷却期
    
    # 表现阈值
    good_performance_threshold: float = 0.7   # 表现良好阈值
    poor_performance_threshold: float = 0.3   # 表现不佳阈值


class DriveCompetition:
    """
    驱动力竞争管理器
    
    核心机制：
    1. 试用期：新驱动从 0.05 开始，500周期内缓慢增长至 0.10
    2. 表现评估：每 50 周期评估一次，基于 100 周期窗口的平均奖励
    3. 动态调整：表现良好则增长 (5%)，表现不佳则衰减 (5%)
    4. 淘汰机制：权重低于 0.02 或连续警告 3 次则淘汰
    """
    
    def __init__(self, config: Optional[CompetitionConfig] = None):
        self.config = config or CompetitionConfig()
        self.performances: Dict[str, DrivePerformance] = {}
        self.eliminated_drives: List[str] = []
        self.evaluation_count: int = 0
        self.promotion_count: int = 0
        self.elimination_count: int = 0
    
    def register_drive(self, drive_name: str, is_emergent: bool = False) -> DrivePerformance:
        """注册新驱动到竞争系统"""
        performance = DrivePerformance(
            drive_name=drive_name,
            status=DriveStatus.PROBATION if is_emergent else DriveStatus.ACTIVE
        )
        self.performances[drive_name] = performance
        return performance
    
    def update_performance(self, drive_name: str, cycle: int, 
                          reward: float, score: float):
        """更新驱动表现"""
        if drive_name not in self.performances:
            self.register_drive(drive_name)
        
        perf = self.performances[drive_name]
        perf.update(cycle, reward, score)
    
    def evaluate_drive(self, drive_name: str, cycle: int) -> Dict:
        """
        评估驱动表现，返回调整建议
        
        Returns:
            {
                'action': 'grow' | 'decay' | 'eliminate' | 'keep',
                'factor': float,  # 调整因子
                'reason': str,
            }
        """
        if drive_name not in self.performances:
            return {'action': 'keep', 'factor': 1.0, 'reason': '未注册'}
        
        perf = self.performances[drive_name]
        cfg = self.config
        
        # 试用期处理
        if perf.status == DriveStatus.PROBATION:
            return self._evaluate_probation(perf, cycle, cfg)
        
        # 正式期处理
        return self._evaluate_active(perf, cycle, cfg)
    
    def _evaluate_probation(self, perf: DrivePerformance, cycle: int, 
                           config: CompetitionConfig) -> Dict:
        """评估试用期驱动"""
        # 检查是否完成试用期
        if perf.age >= config.probation_period:
            # 转正评估
            recent = perf.get_recent_performance(config.evaluation_window)
            
            if recent['avg_reward'] >= config.good_performance_threshold:
                perf.status = DriveStatus.ACTIVE
                perf.promoted_at = cycle
                self.promotion_count += 1
                return {
                    'action': 'grow',
                    'factor': config.growth_rate,
                    'reason': f'试用期完成，表现良好 (avg_reward={recent["avg_reward"]:.3f})，转正'
                }
            else:
                # 延长试用期或淘汰
                if perf.warnings >= config.warning_threshold:
                    perf.status = DriveStatus.ELIMINATED
                    self.elimination_count += 1
                    return {
                        'action': 'eliminate',
                        'factor': 0.0,
                        'reason': f'试用期表现不佳且警告次数过多，淘汰'
                    }
                else:
                    perf.warnings += 1
                    return {
                        'action': 'keep',
                        'factor': 1.0,
                        'reason': f'试用期表现不佳，警告 {perf.warnings}/{config.warning_threshold}'
                    }
        
        # 试用期内：缓慢增长
        return {
            'action': 'grow',
            'factor': config.probation_growth_rate,
            'reason': '试用期正常增长'
        }
    
    def _evaluate_active(self, perf: DrivePerformance, cycle: int,
                        cfg) -> Dict:
        """评估正式期驱动"""
        recent = perf.get_recent_performance(cfg.evaluation_window)
        avg_reward = recent['avg_reward']
        trend = recent['trend']
        
        # 表现良好：增长
        if avg_reward >= cfg.good_performance_threshold:
            perf.warnings = max(0, perf.warnings - 1)  # 减少警告
            return {
                'action': 'grow',
                'factor': cfg.growth_rate,
                'reason': f'表现良好 (avg_reward={avg_reward:.3f} >= {cfg.good_performance_threshold})'
            }
        
        # 表现不佳：衰减
        if avg_reward <= cfg.poor_performance_threshold:
            perf.warnings += 1
            
            # 检查是否需要淘汰
            if perf.warnings >= cfg.warning_threshold:
                perf.status = DriveStatus.AT_RISK
                
                # 再给一个机会，如果趋势上升则保留
                if trend > 0:
                    return {
                        'action': 'decay',
                        'factor': cfg.decay_rate,
                        'reason': f'表现不佳但趋势上升，再给一个机会'
                    }
                else:
                    perf.status = DriveStatus.ELIMINATED
                    self.elimination_count += 1
                    return {
                        'action': 'eliminate',
                        'factor': 0.0,
                        'reason': f'表现持续不佳，淘汰 (warnings={perf.warnings})'
                    }
            
            return {
                'action': 'decay',
                'factor': cfg.decay_rate,
                'reason': f'表现不佳 (avg_reward={avg_reward:.3f})，警告 {perf.warnings}/{cfg.warning_threshold}'
            }
        
        # 表现中等：保持
        return {
            'action': 'keep',
            'factor': 1.0,
            'reason': f'表现中等 (avg_reward={avg_reward:.3f})'
        }
    
    def should_eliminate(self, drive_name: str) -> bool:
        """检查驱动是否应该被淘汰"""
        if drive_name not in self.performances:
            return False
        return self.performances[drive_name].status == DriveStatus.ELIMINATED
    
    def get_drive_stats(self, drive_name: str) -> Optional[Dict]:
        """获取驱动统计信息"""
        if drive_name not in self.performances:
            return None
        
        perf = self.performances[drive_name]
        recent = perf.get_recent_performance(self.config.evaluation_window)
        
        return {
            'name': drive_name,
            'age': perf.age,
            'status': perf.status.value,
            'avg_reward': perf.avg_reward,
            'recent_performance': recent,
            'warnings': perf.warnings,
            'promoted_at': perf.promoted_at,
        }
    
    def get_all_stats(self) -> Dict:
        """获取所有驱动统计"""
        return {
            name: self.get_drive_stats(name)
            for name in self.performances.keys()
        }
    
    def get_summary(self) -> Dict:
        """获取竞争系统摘要"""
        status_counts = {
            'probation': 0,
            'active': 0,
            'at_risk': 0,
            'eliminated': 0,
        }
        
        for perf in self.performances.values():
            status_counts[perf.status.value] += 1
        
        return {
            'total_drives': len(self.performances),
            'status_distribution': status_counts,
            'eliminated_drives': self.eliminated_drives.copy(),
            'promotion_count': self.promotion_count,
            'elimination_count': self.elimination_count,
            'evaluation_count': self.evaluation_count,
        }


class DriveCompetitionManager:
    """
    集成到 DriveManager 的竞争管理器
    
    使用方式：
        drive_manager = DriveManager(drives_config)
        competition = DriveCompetitionManager(drive_manager)
        
        # 在实验循环中更新
        competition.update(cycle, drive_rewards)
        
        # 获取权重调整建议
        adjustments = competition.get_weight_adjustments(cycle)
    """
    
    def __init__(self, drive_manager, config: Optional[Union[CompetitionConfig, str]] = None):
        self.drive_manager = drive_manager
        
        # 处理字符串预设
        if isinstance(config, str):
            config = get_competition_preset(config)
        
        self.competition = DriveCompetition(config)
        self._cycle = 0
        
        # 注册现有驱动
        for name in drive_manager.get_all_drive_names():
            drive = drive_manager.drives.get(name)
            is_emergent = drive.is_emergent if drive else False
            self.competition.register_drive(name, is_emergent)
    
    def update(self, cycle: int, drive_rewards: Dict[str, float],
               drive_scores: Optional[Dict[str, float]] = None):
        """
        更新竞争系统
        
        Args:
            cycle: 当前周期
            drive_rewards: {drive_name: reward} 驱动奖励
            drive_scores: {drive_name: score} 驱动得分 (可选)
        """
        self._cycle = cycle
        
        for name, reward in drive_rewards.items():
            score = drive_scores.get(name, 0.5) if drive_scores else 0.5
            self.competition.update_performance(name, cycle, reward, score)
    
    def evaluate_and_adjust(self, cycle: int) -> Dict[str, Dict]:
        """
        评估所有驱动并返回调整建议
        
        Returns:
            {drive_name: {'action': str, 'factor': float, 'reason': str}}
        """
        adjustments = {}
        
        for name in self.drive_manager.get_all_drive_names():
            result = self.competition.evaluate_drive(name, cycle)
            adjustments[name] = result
            
            # 记录评估
            self.competition.evaluation_count += 1
        
        return adjustments
    
    def apply_adjustments(self, adjustments: Dict[str, Dict], 
                         current_weights: Dict[str, float]) -> Dict[str, float]:
        """
        应用权重调整
        
        Args:
            adjustments: evaluate_and_adjust 返回的调整建议
            current_weights: 当前权重字典
            
        Returns:
            调整后的权重字典
        """
        new_weights = current_weights.copy()
        config = self.competition.config
        
        for name, adjustment in adjustments.items():
            if name not in new_weights:
                continue
            
            action = adjustment['action']
            factor = adjustment['factor']
            
            if action == 'eliminate':
                # 标记淘汰，但不立即删除 (留给调用者处理)
                new_weights[name] = 0.0
            elif action == 'grow':
                new_weights[name] = min(
                    new_weights[name] * factor,
                    config.max_weight
                )
            elif action == 'decay':
                new_weights[name] = max(
                    new_weights[name] * factor,
                    config.min_weight
                )
            # 'keep' 不改变权重
        
        return new_weights
    
    def get_eliminated_drives(self) -> List[str]:
        """获取被淘汰的驱动列表"""
        eliminated = []
        for name in self.drive_manager.get_all_drive_names():
            if self.competition.should_eliminate(name):
                eliminated.append(name)
        return eliminated
    
    def get_stats(self) -> Dict:
        """获取竞争系统统计"""
        return {
            'competition_summary': self.competition.get_summary(),
            'drive_stats': self.competition.get_all_stats(),
        }


# 便捷配置预设
COMPETITION_PRESETS = {
    'v6_default': CompetitionConfig(
        probation_period=500,
        probation_growth_rate=1.01,
        probation_max_weight=0.10,
        evaluation_window=100,
        evaluation_interval=50,
        growth_rate=1.05,
        decay_rate=0.95,
        min_weight=0.02,
        max_weight=0.35,
        warning_threshold=3,
        good_performance_threshold=0.7,
        poor_performance_threshold=0.3,
    ),
    'v6_strict': CompetitionConfig(
        probation_period=300,
        probation_growth_rate=1.005,
        evaluation_window=50,
        growth_rate=1.03,
        decay_rate=0.90,
        min_weight=0.03,
        warning_threshold=2,
        good_performance_threshold=0.75,
        poor_performance_threshold=0.35,
    ),
    'v6_loose': CompetitionConfig(
        probation_period=700,
        probation_growth_rate=1.02,
        evaluation_window=150,
        growth_rate=1.08,
        decay_rate=0.97,
        min_weight=0.01,
        warning_threshold=5,
        good_performance_threshold=0.65,
        poor_performance_threshold=0.25,
    ),
}


def get_competition_preset(name: str) -> CompetitionConfig:
    """获取竞争机制预设配置"""
    return COMPETITION_PRESETS.get(name, COMPETITION_PRESETS['v6_default'])