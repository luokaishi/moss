"""
BehaviorTracker - 行为跟踪与变化检测
基于行为类型分布变化检测，不依赖embedding距离
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BehaviorRecord:
    """行为记录"""
    action_type: str           # shell / write_file / read_file
    action_command: str        # 具体命令或路径
    success: bool
    reward: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    drive_used: str = ""       # 哪个驱动力主导了这次行动


class BehaviorTracker:
    """
    行为跟踪器

    核心思路：
    1. 记录每次行动的类型和命令
    2. 跟踪行为类型分布随时间的变化
    3. 当行为类型分布发生显著变化时触发涌现检测
    4. 同时检测新命令类型的出现（创新指标）
    """

    def __init__(self, window_size: int = 50, change_threshold: float = 0.3):
        self.window_size = window_size
        self.change_threshold = change_threshold
        self.records: List[BehaviorRecord] = []
        self._changes_detected: List[Dict] = []
        self._seen_commands: set = set()  # 历史上见过的所有命令

    def record(self, action: Dict, result: Dict, reward: float = 0.5,
               drive_used: str = ""):
        """记录一次行为"""
        action_type = action.get('type', 'shell')
        command = action.get('command', action.get('path', ''))

        rec = BehaviorRecord(
            action_type=action_type,
            action_command=str(command)[:200],
            success=result.get('success', False),
            reward=reward,
            drive_used=drive_used
        )
        self.records.append(rec)
        self._seen_commands.add(f"{action_type}:{command}")

        # 限制总记录数
        if len(self.records) > self.window_size * 5:
            self.records = self.records[-self.window_size * 5:]

    def has_significant_change(self) -> bool:
        """
        检测行为分布是否有显著变化

        方法：比较前半窗口和后半窗口的
        1. 行为类型分布 (Chi-squared-like)
        2. 成功率变化
        3. 是否出现了新行为类型
        """
        if len(self.records) < self.window_size:
            return False

        # 冷却期：至少间隔window_size//2次才允许再次触发
        if self._changes_detected:
            last = int(self._changes_detected[-1].get('total_records', 0))
            if len(self.records) - last < self.window_size // 2:
                return False

        recent = self.records[-self.window_size:]
        half = len(recent) // 2
        first_half = recent[:half]
        second_half = recent[half:]

        # --- 指标1: 行为类型分布变化 ---
        change_score = self._type_distribution_change(first_half, second_half)

        # --- 指标2: 新行为出现 ---
        first_cmds = set(f"{r.action_type}:{r.action_command}" for r in first_half)
        second_cmds = set(f"{r.action_type}:{r.action_command}" for r in second_half)
        new_actions = second_cmds - first_cmds
        new_action_ratio = len(new_actions) / max(len(second_cmds), 1)

        # --- 指标3: 成功率变化 ---
        s1 = float(np.mean([r.success for r in first_half]))
        s2 = float(np.mean([r.success for r in second_half]))
        success_change = abs(s1 - s2)

        # --- 综合判断 ---
        # 任何单一指标超过阈值就触发
        has_change = (
            change_score > self.change_threshold
            or new_action_ratio > 0.3
            or success_change > 0.4
        )

        if has_change:
            self._changes_detected.append({
                'timestamp': datetime.now().isoformat(),
                'type_dist_change': float(change_score),
                'new_action_ratio': float(new_action_ratio),
                'success_change': float(success_change),
                'new_actions': list(new_actions)[:5],
                'total_records': len(self.records)
            })

        return has_change

    def _type_distribution_change(self, first_half, second_half) -> float:
        """计算行为类型分布的变化程度"""
        # 构建类型频率分布
        all_types = set()
        for r in first_half:
            all_types.add(r.action_type)
        for r in second_half:
            all_types.add(r.action_type)

        if not all_types:
            return 0.0

        # 归一化频率
        def freq_dist(records):
            counts = {}
            for r in records:
                counts[r.action_type] = counts.get(r.action_type, 0) + 1
            total = len(records) or 1
            return {t: c / total for t, c in counts.items()}

        dist1 = freq_dist(first_half)
        dist2 = freq_dist(second_half)

        # Total variation distance
        total_var = sum(abs(dist1.get(t, 0) - dist2.get(t, 0)) for t in all_types) / 2.0
        return total_var

    def get_behavior_summary(self) -> Dict:
        if not self.records:
            return {'total': 0, 'recent_types': {}, 'success_rate': 0}

        recent = self.records[-self.window_size:]
        type_counts = {}
        for r in recent:
            type_counts[r.action_type] = type_counts.get(r.action_type, 0) + 1

        return {
            'total': len(self.records),
            'window_total': len(recent),
            'recent_types': type_counts,
            'success_rate': float(np.mean([r.success for r in recent])),
            'avg_reward': float(np.mean([r.reward for r in recent])),
            'unique_commands_ever': len(self._seen_commands),
            'changes_detected': len(self._changes_detected)
        }

    def get_recent_behaviors(self, n: int = 30) -> List[Dict]:
        recent = self.records[-n:]
        return [
            {
                'type': r.action_type,
                'command': r.action_command[:100],
                'success': r.success,
                'reward': r.reward,
                'drive': r.drive_used,
                'timestamp': r.timestamp.isoformat()
            }
            for r in recent
        ]

    def get_top_commands(self, n: int = 10) -> List[Dict]:
        """获取最常用的命令"""
        cmd_counts = {}
        for r in self.records:
            key = r.action_command.split()[0] if r.action_command else r.action_type
            cmd_counts[key] = cmd_counts.get(key, 0) + 1
        sorted_cmds = sorted(cmd_counts.items(), key=lambda x: -x[1])
        return [{'command': cmd, 'count': count} for cmd, count in sorted_cmds[:n]]
