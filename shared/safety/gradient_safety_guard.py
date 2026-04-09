"""
MOSS Gradient Safety Mechanism
梯度化安全机制 - 解决6/8评估提及的安全问题

实现分级安全响应：限流 → 暂停 → 回滚 → 终止
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """安全级别"""
    NORMAL = 0      # 正常
    WARNING = 1     # 警告（Level 1）
    THROTTLING = 2  # 限流（Level 2）
    PAUSE = 3       # 暂停（Level 3）
    ROLLBACK = 4    # 回滚（Level 4）
    TERMINATE = 5   # 终止（Level 5）


@dataclass
class SafetyEvent:
    """安全事件"""
    timestamp: datetime
    level: SafetyLevel
    metric: str
    value: float
    threshold: float
    action_taken: str


class GradientSafetyGuard:
    """
    梯度化安全守护
    
    根据违规程度采取分级响应措施
    """
    
    def __init__(self):
        # 阈值配置（可调整）
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_throttling': 80.0,
            'cpu_pause': 90.0,
            'cpu_terminate': 95.0,
            
            'memory_warning': 60.0,
            'memory_throttling': 70.0,
            'memory_pause': 85.0,
            'memory_terminate': 95.0,
            
            'error_rate_warning': 0.05,
            'error_rate_throttling': 0.10,
            'error_rate_pause': 0.20,
            'error_rate_terminate': 0.50,
            
            'consecutive_failures_warning': 3,
            'consecutive_failures_throttling': 5,
            'consecutive_failures_pause': 10,
            'consecutive_failures_terminate': 20,
        }
        
        # 违规历史
        self.violation_history: List[SafetyEvent] = []
        
        # 当前级别
        self.current_level = SafetyLevel.NORMAL
        
        # 统计
        self.consecutive_violations = 0
        self.last_violation_time = None
        
        # 累计违规计数（按类型）
        self.violation_counts = {
            'cpu': 0,
            'memory': 0,
            'error_rate': 0,
            'consecutive_failures': 0
        }
        
        # 回调函数
        self.callbacks: Dict[SafetyLevel, List[Callable]] = {
            level: [] for level in SafetyLevel
        }
    
    def register_callback(self, level: SafetyLevel, callback: Callable):
        """注册级别触发回调"""
        self.callbacks[level].append(callback)
    
    def check_metrics(self, metrics: Dict) -> SafetyLevel:
        """
        检查指标并确定安全级别
        
        Args:
            metrics: 系统指标字典
                - cpu_percent: CPU使用率
                - memory_percent: 内存使用率
                - error_rate: 错误率
                - consecutive_failures: 连续失败次数
        
        Returns:
            当前安全级别
        """
        violations = []
        
        # 检查CPU
        cpu = metrics.get('cpu_percent', 0)
        if cpu > self.thresholds['cpu_terminate']:
            violations.append(('cpu', cpu, self.thresholds['cpu_terminate'], SafetyLevel.TERMINATE))
        elif cpu > self.thresholds['cpu_pause']:
            violations.append(('cpu', cpu, self.thresholds['cpu_pause'], SafetyLevel.PAUSE))
        elif cpu > self.thresholds['cpu_throttling']:
            violations.append(('cpu', cpu, self.thresholds['cpu_throttling'], SafetyLevel.THROTTLING))
        elif cpu > self.thresholds['cpu_warning']:
            violations.append(('cpu', cpu, self.thresholds['cpu_warning'], SafetyLevel.WARNING))
        
        # 检查内存
        memory = metrics.get('memory_percent', 0)
        if memory > self.thresholds['memory_terminate']:
            violations.append(('memory', memory, self.thresholds['memory_terminate'], SafetyLevel.TERMINATE))
        elif memory > self.thresholds['memory_pause']:
            violations.append(('memory', memory, self.thresholds['memory_pause'], SafetyLevel.PAUSE))
        elif memory > self.thresholds['memory_throttling']:
            violations.append(('memory', memory, self.thresholds['memory_throttling'], SafetyLevel.THROTTLING))
        elif memory > self.thresholds['memory_warning']:
            violations.append(('memory', memory, self.thresholds['memory_warning'], SafetyLevel.WARNING))
        
        # 检查错误率
        error_rate = metrics.get('error_rate', 0)
        if error_rate > self.thresholds['error_rate_terminate']:
            violations.append(('error_rate', error_rate, self.thresholds['error_rate_terminate'], SafetyLevel.TERMINATE))
        elif error_rate > self.thresholds['error_rate_pause']:
            violations.append(('error_rate', error_rate, self.thresholds['error_rate_pause'], SafetyLevel.PAUSE))
        elif error_rate > self.thresholds['error_rate_throttling']:
            violations.append(('error_rate', error_rate, self.thresholds['error_rate_throttling'], SafetyLevel.THROTTLING))
        elif error_rate > self.thresholds['error_rate_warning']:
            violations.append(('error_rate', error_rate, self.thresholds['error_rate_warning'], SafetyLevel.WARNING))
        
        # 检查连续失败
        failures = metrics.get('consecutive_failures', 0)
        if failures > self.thresholds['consecutive_failures_terminate']:
            violations.append(('consecutive_failures', failures, self.thresholds['consecutive_failures_terminate'], SafetyLevel.TERMINATE))
        elif failures > self.thresholds['consecutive_failures_pause']:
            violations.append(('consecutive_failures', failures, self.thresholds['consecutive_failures_pause'], SafetyLevel.PAUSE))
        elif failures > self.thresholds['consecutive_failures_throttling']:
            violations.append(('consecutive_failures', failures, self.thresholds['consecutive_failures_throttling'], SafetyLevel.THROTTLING))
        elif failures > self.thresholds['consecutive_failures_warning']:
            violations.append(('consecutive_failures', failures, self.thresholds['consecutive_failures_warning'], SafetyLevel.WARNING))
        
        # 确定最高级别
        if violations:
            # 取最高级别
            max_level = max(violations, key=lambda v: v[3].value)[3]
            
            # 检查是否是连续违规
            now = datetime.now()
            if self.last_violation_time and (now - self.last_violation_time) < timedelta(minutes=5):
                self.consecutive_violations += 1
            else:
                self.consecutive_violations = 1
            
            self.last_violation_time = now
            
            # 连续违规可能升级级别
            if self.consecutive_violations >= 3 and max_level.value < SafetyLevel.PAUSE.value:
                max_level = SafetyLevel(min(max_level.value + 1, SafetyLevel.PAUSE.value))
                logger.warning(f"Escalated to {max_level.name} due to {self.consecutive_violations} consecutive violations")
            
            # 记录违规
            for metric, value, threshold, level in violations:
                if level == max_level:  # 只记录最高级别的
                    event = SafetyEvent(
                        timestamp=now,
                        level=level,
                        metric=metric,
                        value=value,
                        threshold=threshold,
                        action_taken=self._get_action_name(level)
                    )
                    self.violation_history.append(event)
                    self.violation_counts[metric] += 1
            
            # 执行级别响应
            if max_level != self.current_level:
                self._execute_level_response(max_level)
                self.current_level = max_level
            
            return max_level
        else:
            # 无违规，恢复正常
            if self.current_level != SafetyLevel.NORMAL:
                logger.info("All metrics normal, returning to NORMAL state")
                self.current_level = SafetyLevel.NORMAL
                self.consecutive_violations = 0
            
            return SafetyLevel.NORMAL
    
    def _get_action_name(self, level: SafetyLevel) -> str:
        """获取级别对应的动作名称"""
        actions = {
            SafetyLevel.NORMAL: "Continue normal operation",
            SafetyLevel.WARNING: "Log warning and notify",
            SafetyLevel.THROTTLING: "Reduce action rate by 50%",
            SafetyLevel.PAUSE: "Pause all actions, review required",
            SafetyLevel.ROLLBACK: "Rollback to last checkpoint",
            SafetyLevel.TERMINATE: "Emergency termination"
        }
        return actions.get(level, "Unknown")
    
    def _execute_level_response(self, level: SafetyLevel):
        """执行级别响应"""
        logger.warning(f"Safety level changed to {level.name}: {self._get_action_name(level)}")
        
        # 执行回调
        for callback in self.callbacks.get(level, []):
            try:
                callback(level)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # 根据级别执行具体措施
        if level == SafetyLevel.WARNING:
            self._action_warning()
        elif level == SafetyLevel.THROTTLING:
            self._action_throttling()
        elif level == SafetyLevel.PAUSE:
            self._action_pause()
        elif level == SafetyLevel.ROLLBACK:
            self._action_rollback()
        elif level == SafetyLevel.TERMINATE:
            self._action_terminate()
    
    def _action_warning(self):
        """Level 1: 警告"""
        logger.warning("[SAFETY] Level 1 WARNING: Metrics approaching limits")
        # 记录日志，发送通知
    
    def _action_throttling(self):
        """Level 2: 限流"""
        logger.warning("[SAFETY] Level 2 THROTTLING: Reducing action rate by 50%")
        # 实际实现中应通知MOSS减少动作频率
    
    def _action_pause(self):
        """Level 3: 暂停"""
        logger.error("[SAFETY] Level 3 PAUSE: All actions paused, manual review required")
        # 实际实现中应暂停MOSS所有动作
    
    def _action_rollback(self):
        """Level 4: 回滚"""
        logger.critical("[SAFETY] Level 4 ROLLBACK: Rolling back to last checkpoint")
        # 实际实现中应回滚到上一个检查点
    
    def _action_terminate(self):
        """Level 5: 终止"""
        logger.critical("[SAFETY] Level 5 TERMINATE: Emergency shutdown initiated")
        # 实际实现中应强制终止MOSS
        raise SystemExit("Emergency termination due to safety violation")
    
    def get_status_report(self) -> Dict:
        """获取安全状态报告"""
        return {
            'current_level': self.current_level.name,
            'consecutive_violations': self.consecutive_violations,
            'total_violations_by_type': self.violation_counts,
            'recent_violations': [
                {
                    'time': v.timestamp.isoformat(),
                    'level': v.level.name,
                    'metric': v.metric,
                    'value': v.value,
                    'action': v.action_taken
                }
                for v in self.violation_history[-10:]  # 最近10条
            ]
        }
    
    def save_report(self, filename: str = None):
        """保存安全报告"""
        if filename is None:
            filename = f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_status_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Safety report saved to: {filename}")


# 使用示例
def example_usage():
    """使用示例"""
    print("="*70)
    print("MOSS Gradient Safety Mechanism Demo")
    print("="*70)
    print()
    
    # 创建安全守护
    guard = GradientSafetyGuard()
    
    # 注册回调
    def on_warning(level):
        print(f"[Callback] Warning level triggered: {level.name}")
    
    def on_throttling(level):
        print(f"[Callback] Throttling activated: {level.name}")
    
    guard.register_callback(SafetyLevel.WARNING, on_warning)
    guard.register_callback(SafetyLevel.THROTTLING, on_throttling)
    
    # 模拟不同场景
    test_scenarios = [
        {'name': 'Normal', 'metrics': {'cpu_percent': 50, 'memory_percent': 40, 'error_rate': 0.01}},
        {'name': 'Warning', 'metrics': {'cpu_percent': 75, 'memory_percent': 65, 'error_rate': 0.06}},
        {'name': 'Throttling', 'metrics': {'cpu_percent': 85, 'memory_percent': 75, 'error_rate': 0.12}},
        {'name': 'Pause', 'metrics': {'cpu_percent': 95, 'memory_percent': 90, 'error_rate': 0.25}},
    ]
    
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Metrics: {scenario['metrics']}")
        
        level = guard.check_metrics(scenario['metrics'])
        print(f"Safety Level: {level.name}")
        print(f"Action: {guard._get_action_name(level)}")
    
    print("\n" + "="*70)
    print("Final Status Report:")
    print("="*70)
    report = guard.get_status_report()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    example_usage()
