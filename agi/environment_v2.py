"""
RealEnvironment V2 - 增强版环境接口
支持更多 action 类型，提升行为多样性

新增 action 类型:
- edit_file: 文件编辑 (追加、修改)
- exec_python: Python 代码执行
- analyze_data: 数据分析
- generate_report: 报告生成
"""

import subprocess
import time
import shutil
import random
import json
import ast
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class EnvState:
    """环境状态快照 (V2)"""
    resource_level: float = 0.5
    error_rate: float = 0.0
    uptime_hours: float = 0.0
    environment_entropy: float = 0.5
    visited_paths: int = 0
    total_paths: int = 100
    interactions_count: int = 0
    task_completion_rate: float = 0.0
    file_count: int = 0
    disk_usage: float = 0.0
    workspace_changes: int = 0
    
    # V2 新增: 行为多样性统计
    action_type_distribution: Dict[str, int] = field(default_factory=dict)
    unique_commands: int = 0
    analysis_runs: int = 0
    reports_generated: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)
    raw: Dict[str, Any] = field(default_factory=dict)


class RealEnvironmentV2:
    """
    增强版真实环境接口
    
    新增 action 类型:
    - edit_file: 安全文件编辑
    - exec_python: 受限 Python 执行
    - analyze_data: 数据分析
    - generate_report: 报告生成
    """

    DEFAULT_FORBIDDEN = [
        r'rm\s+-rf\s+/', r'sudo\s+', r'chmod\s+777',
        r':\(\)\{.*\};:', r'mkfs', r'dd\s+if=',
        r'>/dev/sd', r'curl.*\|\s*bash', r'wget.*\|\s*sh',
        r'__import__\s*\(\s*[\'"]os[\'"]\s*\)\.system',  # 防止 Python 代码注入
        r'open\s*\(\s*[\'"]/',  # 防止访问根目录
        r'subprocess\.call', r'subprocess\.run', r'subprocess\.Popen',
        r'os\.system', r'os\.popen',
    ]

    # Python 执行黑名单 (危险函数)
    PYTHON_FORBIDDEN_NAMES = {
        'os.system', 'os.popen', 'subprocess.call', 'subprocess.run',
        'subprocess.Popen', 'eval', 'exec', 'compile', '__import__',
        'open', 'file', 'input', 'raw_input'
    }

    def __init__(self, config: Dict):
        self.workspace = Path(config.get('workspace', '/workspace'))
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.workspace_limit = Path(config.get('workspace_limit', '/workspace'))

        self.allowed_commands = config.get('allowed_commands', [
            'ls', 'cat', 'python3', 'echo', 'find', 'wc', 'head', 'tail',
            'grep', 'sort', 'uniq', 'date', 'whoami', 'pwd', 'df', 'ps'
        ])
        self.forbidden_patterns = config.get('forbidden_patterns', self.DEFAULT_FORBIDDEN)

        self.start_time = time.time()
        self._action_history: List[Dict] = []
        self._visited_paths = set()
        self._error_count = 0
        self._total_actions = 0
        self._prev_snapshot = None
        self._interaction_count = 0
        
        # V2: action 类型统计
        self._action_type_counts: Dict[str, int] = {
            'shell': 0, 'write_file': 0, 'read_file': 0,
            'edit_file': 0, 'exec_python': 0, 'analyze_data': 0, 'generate_report': 0
        }
        self._unique_commands: set = set()
        self._analysis_count = 0
        self._report_count = 0

    def perceive(self) -> EnvState:
        """感知当前环境状态 (V2)"""
        uptime = (time.time() - self.start_time) / 3600.0

        disk = shutil.disk_usage(str(self.workspace))
        disk_free_ratio = disk.free / (disk.total + 1e-8)
        resource_level = self._np_clip(disk_free_ratio * 0.6 + 0.4, 0, 1)

        error_rate = self._error_count / max(self._total_actions, 1)
        entropy = self._calculate_entropy()

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
            action_type_distribution=dict(self._action_type_counts),
            unique_commands=len(self._unique_commands),
            analysis_runs=self._analysis_count,
            reports_generated=self._report_count,
        )
        self._prev_snapshot = state
        return state

    def execute(self, action: Dict) -> Dict:
        """执行行动 (V2 - 支持更多类型)"""
        self._total_actions += 1
        action_type = action.get('type', 'shell')
        
        # 更新统计
        self._action_type_counts[action_type] = self._action_type_counts.get(action_type, 0) + 1
        if 'command' in action:
            self._unique_commands.add(action['command'])

        try:
            if action_type == 'shell':
                result = self._run_shell(action.get('command', ''), timeout=action.get('timeout', 30))
            elif action_type == 'write_file':
                result = self._write_file(action['path'], action['content'])
            elif action_type == 'read_file':
                result = self._read_file(action['path'])
            elif action_type == 'edit_file':
                result = self._edit_file(action['path'], action.get('operation', 'append'), 
                                        action.get('content', ''))
            elif action_type == 'exec_python':
                result = self._exec_python(action['code'], action.get('timeout', 10))
            elif action_type == 'analyze_data':
                result = self._analyze_data(action.get('target', 'workspace'))
            elif action_type == 'generate_report':
                result = self._generate_report(action.get('report_type', 'summary'))
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
        """执行 shell 命令"""
        if not self._is_safe_command(cmd):
            return {'success': False, 'error': 'Command blocked by safety filter'}
        
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
        target = self._safe_path(path)
        if not target:
            return {'success': False, 'error': 'Invalid path'}
        
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return {'success': True, 'path': str(target), 'size': len(content)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _read_file(self, path: str) -> Dict:
        """读取文件"""
        target = self._safe_path(path)
        if not target:
            return {'success': False, 'error': 'Invalid path'}
        
        try:
            content = target.read_text()
            return {'success': True, 'content': content[:5000], 'size': len(content)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _edit_file(self, path: str, operation: str, content: str) -> Dict:
        """编辑文件 (追加或替换)"""
        target = self._safe_path(path)
        if not target:
            return {'success': False, 'error': 'Invalid path'}
        
        try:
            if operation == 'append':
                with open(target, 'a') as f:
                    f.write(content)
                return {'success': True, 'operation': 'append', 'path': str(target)}
            elif operation == 'prepend':
                existing = target.read_text() if target.exists() else ''
                target.write_text(content + existing)
                return {'success': True, 'operation': 'prepend', 'path': str(target)}
            elif operation == 'replace':
                target.write_text(content)
                return {'success': True, 'operation': 'replace', 'path': str(target)}
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _exec_python(self, code: str, timeout: int = 10) -> Dict:
        """安全执行 Python 代码"""
        # 语法检查
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {'success': False, 'error': f'Syntax error: {e}'}
        
        # 安全检查 - 遍历 AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # 检查函数调用
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        return {'success': False, 'error': f'Forbidden function: {node.func.id}'}
                elif isinstance(node.func, ast.Attribute):
                    # 检查属性调用 (如 os.system)
                    attr_chain = self._get_attr_chain(node.func)
                    if attr_chain in self.PYTHON_FORBIDDEN_NAMES:
                        return {'success': False, 'error': f'Forbidden: {attr_chain}'}
        
        # 执行代码 (受限环境)
        safe_globals = {
            '__builtins__': {
                'len': len, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'sum': sum, 'min': min, 'max': max, 'abs': abs,
                'str': str, 'int': int, 'float': float, 'list': list,
                'dict': dict, 'set': set, 'tuple': tuple,
                'print': lambda *args: ' '.join(str(a) for a in args),
                'True': True, 'False': False, 'None': None,
            }
        }
        safe_locals = {}
        
        try:
            result = eval(compile(tree, '<string>', 'eval'), safe_globals, safe_locals)
            return {
                'success': True,
                'result': str(result)[:1000],
                'result_type': type(result).__name__
            }
        except:
            try:
                exec(compile(tree, '<string>', 'exec'), safe_globals, safe_locals)
                return {'success': True, 'result': 'Executed', 'locals': {k: str(v)[:100] for k, v in safe_locals.items()}}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    def _get_attr_chain(self, node) -> str:
        """获取属性链 (如 os.system)"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attr_chain(node.value) + '.' + node.attr
        return ''

    def _analyze_data(self, target: str) -> Dict:
        """分析工作区数据"""
        self._analysis_count += 1
        
        try:
            if target == 'workspace':
                # 分析工作区文件
                file_types = {}
                total_size = 0
                
                for f in self.workspace.rglob('*'):
                    if f.is_file():
                        ext = f.suffix or 'no_ext'
                        file_types[ext] = file_types.get(ext, 0) + 1
                        try:
                            total_size += f.stat().st_size
                        except:
                            pass
                
                analysis = {
                    'file_types': file_types,
                    'total_files': sum(file_types.values()),
                    'total_size_mb': round(total_size / (1024*1024), 2),
                    'top_types': sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
                }
                
                return {'success': True, 'analysis_type': 'workspace', 'data': analysis}
            
            elif target == 'actions':
                # 分析行动历史
                if not self._action_history:
                    return {'success': False, 'error': 'No action history'}
                
                success_count = sum(1 for a in self._action_history if a['result'].get('success'))
                type_dist = {}
                for a in self._action_history:
                    t = a['action'].get('type', 'unknown')
                    type_dist[t] = type_dist.get(t, 0) + 1
                
                analysis = {
                    'total_actions': len(self._action_history),
                    'success_rate': round(success_count / len(self._action_history), 2),
                    'type_distribution': type_dist,
                    'error_rate': round(self._error_count / max(self._total_actions, 1), 2)
                }
                
                return {'success': True, 'analysis_type': 'actions', 'data': analysis}
            
            else:
                return {'success': False, 'error': f'Unknown analysis target: {target}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_report(self, report_type: str) -> Dict:
        """生成报告"""
        self._report_count += 1
        
        try:
            if report_type == 'summary':
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'uptime_hours': round((time.time() - self.start_time) / 3600, 2),
                    'total_actions': self._total_actions,
                    'error_rate': round(self._error_count / max(self._total_actions, 1), 3),
                    'action_distribution': dict(self._action_type_counts),
                    'unique_commands': len(self._unique_commands),
                    'file_count': self._count_files()
                }
                
                # 保存报告
                report_path = self.workspace / f'report_summary_{self._report_count:03d}.json'
                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2)
                
                return {'success': True, 'report_type': 'summary', 'path': str(report_path), 'data': report}
            
            elif report_type == 'diversity':
                # 行为多样性报告
                total = sum(self._action_type_counts.values())
                if total == 0:
                    return {'success': False, 'error': 'No actions recorded'}
                
                distribution = {k: round(v/total, 3) for k, v in self._action_type_counts.items() if v > 0}
                
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'total_actions': total,
                    'type_distribution': distribution,
                    'diversity_score': round(len([v for v in distribution.values() if v > 0.05]) / len(distribution), 2),
                    'shell_ratio': round(self._action_type_counts.get('shell', 0) / total, 2),
                }
                
                report_path = self.workspace / f'report_diversity_{self._report_count:03d}.json'
                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2)
                
                return {'success': True, 'report_type': 'diversity', 'path': str(report_path), 'data': report}
            
            else:
                return {'success': False, 'error': f'Unknown report type: {report_type}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _safe_path(self, path: str) -> Optional[Path]:
        """获取安全路径"""
        try:
            target = (self.workspace / path).resolve()
            if not str(target).startswith(str(self.workspace_limit)):
                return None
            return target
        except:
            return None

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
        if len(self._action_history) < 2:
            return 0.5
        recent = self._action_history[-10:]
        success_rate = sum(1 for a in recent if a['result'].get('success')) / len(recent)
        return self._np_clip(abs(success_rate - 0.7) * 2, 0.1, 1.0)

    def _np_clip(self, val, lo, hi):
        """简易 clip"""
        return max(lo, min(val, hi))

    def generate_action_candidates(self, state: EnvState) -> List[Dict]:
        """生成候选行动 (V2 - 更多样化)"""
        candidates = []
        
        # 基础 shell 命令 (减少占比)
        if state.resource_level < 0.7:
            candidates.append({
                'type': 'shell', 'command': 'df -h .',
                'description': '检查磁盘空间', 'drives': ['survival']
            })
        
        # 探索类 (多样化)
        explore_shells = [
            ('ls -la', '列出目录详情'),
            ('find . -maxdepth 2 -type f | wc -l', '统计文件数'),
            ('find . -name "*.py" | head -3', '查找Python文件'),
            ('find . -name "*.json" | head -3', '查找JSON文件'),
        ]
        cmd, desc = random.choice(explore_shells)
        candidates.append({
            'type': 'shell', 'command': cmd,
            'description': desc, 'drives': ['curiosity']
        })
        
        # 文件操作 (edit_file)
        if random.random() < 0.25:
            candidates.append({
                'type': 'edit_file',
                'path': f'log_{random.randint(0,99):02d}.txt',
                'operation': 'append',
                'content': f'[{datetime.now().isoformat()}] Cycle log entry\n',
                'description': '追加日志文件', 'drives': ['influence', 'optimization']
            })
        
        # Python 执行 (exec_python) - 新增
        if random.random() < 0.20:
            python_snippets = [
                ('[x**2 for x in range(10)]', '计算平方数'),
                ('sum(range(100))', '计算1-100和'),
                ('len([1,2,3,4,5])', '列表长度'),
                ('max([3,1,4,1,5,9])', '找最大值'),
                ('"hello".upper()', '字符串操作'),
            ]
            code, desc = random.choice(python_snippets)
            candidates.append({
                'type': 'exec_python', 'code': code,
                'description': desc, 'drives': ['curiosity', 'optimization']
            })
        
        # 数据分析 (analyze_data) - 新增
        if random.random() < 0.15:
            candidates.append({
                'type': 'analyze_data', 'target': 'workspace',
                'description': '分析工作区文件', 'drives': ['curiosity']
            })
            candidates.append({
                'type': 'analyze_data', 'target': 'actions',
                'description': '分析行动历史', 'drives': ['optimization']
            })
        
        # 生成报告 (generate_report) - 新增
        if random.random() < 0.10:
            candidates.append({
                'type': 'generate_report', 'report_type': 'summary',
                'description': '生成摘要报告', 'drives': ['influence']
            })
            candidates.append({
                'type': 'generate_report', 'report_type': 'diversity',
                'description': '生成多样性报告', 'drives': ['optimization']
            })
        
        return candidates

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = sum(self._action_type_counts.values())
        return {
            'total_actions': self._total_actions,
            'error_count': self._error_count,
            'error_rate': self._error_count / max(self._total_actions, 1),
            'uptime_hours': (time.time() - self.start_time) / 3600.0,
            'visited_paths': len(self._visited_paths),
            'action_type_distribution': dict(self._action_type_counts),
            'shell_ratio': round(self._action_type_counts.get('shell', 0) / max(total, 1), 2),
            'unique_commands': len(self._unique_commands),
            'analysis_count': self._analysis_count,
            'report_count': self._report_count,
        }