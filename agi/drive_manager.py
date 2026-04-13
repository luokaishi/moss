"""
DriveManager - 驱动力管理器
管理初始驱动力和涌现驱动力的评估、权重动态调整
"""

import numpy as np
from typing import Dict, List, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

if TYPE_CHECKING:
    from .environment import EnvState


def _to_native(obj):
    """将 numpy 类型转为 Python 原生类型，确保 JSON 可序列化"""
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    return obj


@dataclass
class Drive:
    """驱动力"""
    name: str
    weight: float = 0.25
    description: str = ""
    score: float = 0.0
    history: List[float] = field(default_factory=list)
    is_emergent: bool = False
    emerged_at: Optional[datetime] = None
    source_behaviors: List[str] = field(default_factory=list)
    novelty_score: float = 0.0
    causal_independence: float = 0.0
    stability: float = 0.0

    def update_score(self, score: float):
        self.score = float(score)
        self.history.append(float(score))
        if len(self.history) > 200:
            self.history = self.history[-200:]
        # 计算稳定性
        if len(self.history) >= 20:
            recent = np.array(self.history[-20:])
            mean = np.mean(recent)
            self.stability = float(np.clip(1.0 - (np.std(recent) / (mean + 1e-8)), 0, 1))


class DriveManager:
    """
    驱动力管理器

    负责：
    1. 管理初始驱动和涌现驱动
    2. 基于环境状态评估每个驱动力的得分
    3. 动态调整驱动权重
    4. 验证新驱动的独立性
    """

    # 内置评估器
    EVALUATORS = {}

    def __init__(self, drives_config: List[Dict]):
        self.drives: Dict[str, Drive] = {}
        self._evaluators: Dict[str, Callable] = {}
        self._register_builtin_evaluators()

        for cfg in drives_config:
            self._add_drive_from_config(cfg)

    def _register_builtin_evaluators(self):
        """注册内置驱动力评估器"""
        self._evaluators['survival'] = self._eval_survival
        self._evaluators['curiosity'] = self._eval_curiosity
        self._evaluators['influence'] = self._eval_influence
        self._evaluators['optimization'] = self._eval_optimization

    def _eval_survival(self, state: 'EnvState') -> float:
        """生存驱动力：基于资源充足度和健康度"""
        resource_score = np.clip(state.resource_level, 0, 1)
        health_score = 1.0 - min(state.error_rate, 1.0)
        uptime_score = np.clip(state.uptime_hours / 72.0, 0, 1)  # 72h为满
        return 0.4 * resource_score + 0.4 * health_score + 0.2 * uptime_score

    def _eval_curiosity(self, state: 'EnvState') -> float:
        """好奇驱动力：基于环境变化程度和探索空间"""
        entropy_score = np.clip(state.environment_entropy, 0, 1)
        novelty_score = np.clip(1.0 - (state.visited_paths / max(state.total_paths, 1)), 0, 1)
        return 0.6 * entropy_score + 0.4 * novelty_score

    def _eval_influence(self, state: 'EnvState') -> float:
        """影响力驱动力：基于外部交互和任务完成度"""
        interaction_score = np.clip(state.interactions_count / 50.0, 0, 1)
        task_score = np.clip(state.task_completion_rate, 0, 1)
        return 0.5 * interaction_score + 0.5 * task_score

    def _eval_optimization(self, state: 'EnvState') -> float:
        """优化驱动力：基于效率和改进空间"""
        efficiency = 1.0 - min(state.error_rate, 1.0)
        improvement_space = np.clip(state.environment_entropy, 0, 1)
        return 0.6 * efficiency + 0.4 * improvement_space

    def _add_drive_from_config(self, cfg: Dict):
        name = cfg['name']
        drive = Drive(
            name=name,
            weight=cfg.get('weight', 0.25),
            description=cfg.get('description', ''),
            is_emergent=False
        )
        # 注册评估器
        evaluator_key = cfg.get('evaluator', name)
        if evaluator_key.startswith('builtin:'):
            evaluator_key = evaluator_key.split(':', 1)[1]
        if evaluator_key in self._evaluators:
            drive._eval_fn = self._evaluators[evaluator_key]
        else:
            drive._eval_fn = lambda s: 0.5  # 默认评估
        self.drives[name] = drive

    def add_emergent_drive(self, name: str, weight: float,
                           description: str, source_behaviors: List[str],
                           novelty_score: float, causal_independence: float,
                           eval_fn: Optional[Callable] = None) -> bool:
        """添加涌现驱动力"""
        if name in self.drives:
            return False

        drive = Drive(
            name=name,
            weight=weight,
            description=description,
            is_emergent=True,
            emerged_at=datetime.now(),
            source_behaviors=source_behaviors,
            novelty_score=novelty_score,
            causal_independence=causal_independence
        )
        drive._eval_fn = eval_fn or self._evaluators.get('curiosity', lambda s: 0.5)
        self.drives[name] = drive

        # 重新归一化权重
        self._normalize_weights()
        return True

    def _normalize_weights(self):
        """归一化所有驱动权重到总和1.0"""
        total = sum(d.weight for d in self.drives.values())
        if total > 0:
            for d in self.drives.values():
                d.weight /= total

    # ========== 干预式验证支持方法 ==========

    def force_drive(self, drive_name: str) -> None:
        """
        干预模式：强制使用指定驱动力
        将该驱动力权重设为接近1.0，其他设为接近0
        """
        if drive_name not in self.drives:
            return
        for name, drive in self.drives.items():
            if name == drive_name:
                drive.weight = 0.99
            else:
                drive.weight = 0.01 / max(len(self.drives) - 1, 1)
        # 不调用 _normalize_weights()，保持干预状态

    def disable_drive(self, drive_name: str) -> None:
        """
        干预模式：禁用指定驱动力
        将该驱动力权重设为接近0，重新归一化其他驱动力
        """
        if drive_name not in self.drives:
            return
        self.drives[drive_name].weight = 0.01
        self._normalize_weights()

    def save_weights(self) -> Dict[str, float]:
        """保存当前权重"""
        return {name: drive.weight for name, drive in self.drives.items()}

    def restore_weights(self, saved_weights: Dict[str, float]) -> None:
        """恢复保存的权重（干预实验后恢复）"""
        for name, weight in saved_weights.items():
            if name in self.drives:
                self.drives[name].weight = weight
        self._normalize_weights()

    def evaluate_all(self, state: 'EnvState') -> Dict[str, float]:
        """评估所有驱动力得分"""
        scores = {}
        for name, drive in self.drives.items():
            try:
                score = drive._eval_fn(state)
                score = float(np.clip(score, 0, 1))
            except Exception:
                score = 0.5
            drive.update_score(score)
            scores[name] = float(score * drive.weight)
        return scores

    def get_weighted_action(self, state: 'EnvState',
                            action_candidates: List[Dict]) -> Optional[Dict]:
        """基于驱动力得分加权选择最佳行动"""
        if not action_candidates:
            return None

        scores = self.evaluate_all(state)
        total_score = sum(scores.values()) or 1.0

        # 计算每个行动的加权分
        best_action = None
        best_value = -1.0

        for action in action_candidates:
            contributing_drives = action.get('drives', list(scores.keys()))
            value = sum(scores.get(d, 0) for d in contributing_drives) / total_score
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def get_all_drive_names(self) -> List[str]:
        return list(self.drives.keys())

    def get_drive_summary(self) -> Dict:
        return {
            name: {
                'weight': float(d.weight),
                'score': float(d.score),
                'stability': float(d.stability),
                'is_emergent': d.is_emergent,
                'history_len': len(d.history)
            }
            for name, d in self.drives.items()
        }

    def update_weight_from_feedback(self, drive_name: str, reward: float, lr: float = 0.1):
        """根据反馈更新驱动权重"""
        if drive_name in self.drives:
            delta = lr * (reward - 0.5)  # reward>0.5则增强
            self.drives[drive_name].weight = float(np.clip(
                self.drives[drive_name].weight + delta, 0.05, 0.6
            ))
            self._normalize_weights()
