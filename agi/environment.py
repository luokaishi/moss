"""
RealEnvironment - 真实计算机系统环境接口
感知：系统资源、文件系统、运行状态
行动：shell命令（带安全过滤）、文件读写
"""

import os
import subprocess
import time
import shutil
import platform
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class EnvState:
    """环境状态快照"""
    resource_level: float = 0.5        # 资源充足度 (0-1)
    error_rate: float = 0.0            # 近期错误率
    uptime_hours: float = 0.0          # 运行时间(小时)
    environment_entropy: float = 0.5   # 环境变化度
    visited_paths: int = 0             # 已访问路径数
    total_paths: int = 100             # 总可探索路径数
    interactions_count: int = 0        # 外部交互次数
    task_completion_rate: float = 0.0  # 任务完成率
    file_count: int = 0                # 文件数量
    disk_usage: float = 0.0            # 磁盘使用率
    workspace_changes: int = 0         # 工作区变化数
    timestamp: datetime = field(default_factory=datetime.now)
    raw: Dict[str, Any] = field(default_factory=dict)


class RealEnvironment:
    """
    真实计算机系统环境

    安全机制：
    1. 工作区限制（workspace_limit）
    2. 危险命令黑名单
    3. 允许命令白名单
    4. 超时控制
    """

    # 默认危险模式
    DEFAULT_FORBIDDEN = [
        r'rm\s+-rf\s+/', r'sudo\s+', r'chmod\s+777',
        r':\(\)\{.*\};:', r'mkfs', r'dd\s+if=',
        r'>/dev/sd', r'curl.*\|\s*bash', r'wget.*\|\s*sh'
    ]

    def __init__(self, config: Dict):
        self.workspace = Path(config.get('workspace', '/workspace'))
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.workspace_limit = Path(config.get('workspace_limit', '/workspace'))

        self.allowed_commands = config.get('allowed_commands', ['ls', 'cat', 'python3', 'echo', 'find'])
        self.forbidden_patterns = config.get('forbidden_patterns', self.DEFAULT_FORBIDDEN)

        self.start_time = time.time()
        self._action_history: List[Dict] = []
        self._visited_paths = set()
        self._error_count = 0
        self._total_actions = 0
        self._prev_snapshot = None  # 上一次文件快照
        self._interaction_count = 0

    def perceive(self) -> EnvState:
        """感知当前环境状态"""
        uptime = (time.time() - self.start_time) / 3600.0

        # 资源水平（磁盘空间 + 内存）
        disk = shutil.disk_usage(str(self.workspace))
        disk_free_ratio = disk.free / (disk.total + 1e-8)
        resource_level = np_clip(disk_free_ratio * 0.6 + 0.4, 0, 1)  # 基础40%保底

        # 错误率
        error_rate = self._error_count / max(self._total_actions, 1)

        # 环境熵（文件变化频率）
        entropy = self._calculate_entropy()

        # 扫描文件
        file_count = self._count_files()
        self._visited_paths.update(self._list_recent_paths())

        state = EnvState(
            resource_level=resource_level,
            error_rate=error_rate,
            uptime_hours=uptime,
            environment_entropy=entropy,
            visited_paths=len(self._visited_paths),
            total_paths=max(file_count * 2, 100),
            interactions_count=self._interaction_count,
            task_completion_rate=min(self._total_actions / 100.0, 1.0),
            file_count=file_count,
            disk_usage=1.0 - disk_free_ratio,
        )
        self._prev_snapshot = state
        return state

    def execute(self, action: Dict) -> Dict:
        """执行行动"""
        self._total_actions += 1
        cmd = action.get('command', '')
        action_type = action.get('type', 'shell')

        # 安全检查
        if not self._is_safe_command(cmd):
            self._error_count += 1
            return {'success': False, 'error': 'Command blocked by safety filter', 'output': ''}

        try:
            if action_type == 'shell':
                result = self._run_shell(cmd, timeout=action.get('timeout', 30))
            elif action_type == 'write_file':
                result = self._write_file(
                    action['path'], action['content']
                )
            elif action_type == 'read_file':
                result = self._read_file(action['path'])
            else:
                result = {'success': False, 'error': f'Unknown action type: {action_type}'}

            if not result.get('success'):
                self._error_count += 1

            self._action_history.append({
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            return result

        except Exception as e:
            self._error_count += 1
            return {'success': False, 'error': str(e)}

    def _is_safe_command(self, cmd: str) -> bool:
        """安全检查"""
        import re
        for pattern in self.forbidden_patterns:
            if re.search(pattern, cmd):
                return False
        return True

    def _run_shell(self, cmd: str, timeout: int = 30) -> Dict:
        """执行shell命令"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=str(self.workspace)
            )
            self._interaction_count += 1
            return {
                'success': result.returncode == 0,
                'output': result.stdout[:2000],
                'error': result.stderr[:500] if result.stderr else '',
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'Command timed out after {timeout}s'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _write_file(self, path: str, content: str) -> Dict:
        """写入文件"""
        target = (self.workspace / path).resolve()
        if not str(target).startswith(str(self.workspace_limit)):
            return {'success': False, 'error': 'Path outside workspace limit'}
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return {'success': True, 'path': str(target)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _read_file(self, path: str) -> Dict:
        """读取文件"""
        target = (self.workspace / path).resolve()
        if not str(target).startswith(str(self.workspace_limit)):
            return {'success': False, 'error': 'Path outside workspace limit'}
        try:
            content = target.read_text()
            return {'success': True, 'content': content[:5000], 'size': len(content)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _count_files(self) -> int:
        """计数工作区文件数"""
        count = 0
        try:
            for _ in self.workspace.rglob('*'):
                if _.is_file():
                    count += 1
                    if count > 10000:
                        break
        except PermissionError:
            pass
        return count

    def _list_recent_paths(self) -> List[str]:
        """列出工作区路径"""
        paths = []
        try:
            for p in self.workspace.iterdir():
                paths.append(str(p.relative_to(self.workspace)))
        except PermissionError:
            pass
        return paths

    def _calculate_entropy(self) -> float:
        """计算环境熵"""
        if self._prev_snapshot is None:
            return 0.5
        # 简化：基于行动历史的变化率
        if len(self._action_history) < 2:
            return 0.5
        recent = self._action_history[-10:]
        success_rate = sum(1 for a in recent if a['result'].get('success')) / len(recent)
        # 成功率变化越大，熵越高
        return np_clip(abs(success_rate - 0.7) * 2, 0.1, 1.0)

    def generate_action_candidates(self, state: EnvState) -> List[Dict]:
        """根据当前状态生成候选行动（引入多样性）"""
        candidates = []

        # 生存相关
        if state.resource_level < 0.7:
            candidates.append({
                'type': 'shell', 'command': 'df -h',
                'description': '检查磁盘空间', 'drives': ['survival']
            })
        if state.error_rate > 0.2:
            candidates.append({
                'type': 'shell', 'command': 'ls -la',
                'description': '检查工作区状态', 'drives': ['survival']
            })

        # 好奇相关 - 增加多样性
        explore_options = [
            ('ls', '列出当前目录'),
            ('ls -la', '列出目录详情'),
            ('find . -maxdepth 1 -type f 2>/dev/null | head -10', '查找文件'),
            ('ls -R . 2>/dev/null | head -30', '递归查看目录'),
            ('find . -name "*.py" 2>/dev/null | head -5', '查找Python文件'),
            ('find . -name "*.md" 2>/dev/null | head -5', '查找Markdown文件'),
            ('find . -name "*.json" 2>/dev/null | head -5', '查找JSON文件'),
            ('cat /etc/os-release 2>/dev/null', '查看系统信息'),
            ('whoami', '查看当前用户'),
            ('date', '查看当前时间'),
            ('pwd', '查看工作目录'),
            ('ps aux 2>/dev/null | head -5', '查看进程'),
            ('python3 -c "import os; print(os.listdir())"', 'Python列出目录'),
        ]
        chosen = random.choice(explore_options)
        candidates.append({
            'type': 'shell', 'command': chosen[0],
            'description': chosen[1], 'drives': ['curiosity']
        })

        # 偶尔尝试不同类型的命令（增加行为多样性）
        if random.random() < 0.3:
            extra_options = [
                ('wc -l *.py 2>/dev/null | tail -1', '统计代码行数'),
                ('head -5 *.md 2>/dev/null | head -20', '预览文档'),
                ('echo $PATH', '查看环境变量'),
                ('python3 -c "import numpy; print(numpy.__version__)"', '检查numpy'),
                ('python3 -c "import platform; print(platform.node())"', '查看主机名'),
            ]
            chosen = random.choice(extra_options)
            candidates.append({
                'type': 'shell', 'command': chosen[0],
                'description': chosen[1], 'drives': ['curiosity', 'influence']
            })

        # 影响力相关
        influence_options = [
            ('python3 -c "print(\'hello from AGI\')"', '验证Python环境'),
            ('echo "AGI agent alive"', '输出状态'),
            ('python3 -c "import sys; print(sys.version)"', '检查Python版本'),
        ]
        chosen = random.choice(influence_options)
        candidates.append({
            'type': 'shell', 'command': chosen[0],
            'description': chosen[1], 'drives': ['influence']
        })

        # 优化相关
        if state.file_count > 20:
            candidates.append({
                'type': 'shell', 'command': 'find . -name "*.pyc" -delete 2>/dev/null; echo done',
                'description': '清理缓存文件', 'drives': ['optimization']
            })

        # 偶尔写入文件（创造行为变化）
        if random.random() < 0.15:
            path = f'_agi_log_{random.randint(0,999)}.txt'
            content = f'AGI cycle log\nTime: {time.time()}\nCycle: random\n'
            candidates.append({
                'type': 'write_file', 'path': path, 'content': content,
                'description': '写入周期日志', 'drives': ['influence', 'optimization']
            })

        return candidates

    def get_stats(self) -> Dict:
        return {
            'total_actions': self._total_actions,
            'error_count': self._error_count,
            'error_rate': self._error_count / max(self._total_actions, 1),
            'uptime_hours': (time.time() - self.start_time) / 3600.0,
            'visited_paths': len(self._visited_paths)
        }


def np_clip(val, lo, hi):
    """简易clip"""
    import numpy as np
    return float(np.clip(val, lo, hi))
