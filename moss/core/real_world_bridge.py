#!/usr/bin/env python3
"""
mves-realworld 桥接模块

将 mves 多向量演化系统接入真实世界环境

核心功能:
1. 真实世界状态感知
2. 真实动作安全执行
3. 长期实验状态管理
4. 与 mves 核心模块集成
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import time
import json
import os
from pathlib import Path


@dataclass
class RealWorldState:
    """真实世界状态快照"""
    timestamp: float
    files: Dict  # 文件系统状态
    network: Dict  # 网络状态
    system: Dict  # 系统资源状态
    processes: Dict  # 进程状态
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'files': self.files,
            'network': self.network,
            'system': self.system,
            'processes': self.processes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RealWorldState':
        return cls(
            timestamp=data['timestamp'],
            files=data['files'],
            network=data['network'],
            system=data['system'],
            processes=data['processes'],
        )


class FileSystemMonitor:
    """文件系统监控"""
    
    def __init__(self, workspace: str = '/tmp/mves_workspace'):
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)
        self._last_scan = {}
    
    def scan(self, path: str = None) -> Dict:
        """扫描文件系统"""
        target = Path(path) if path else self.workspace
        
        files = []
        dirs = []
        
        try:
            for item in target.iterdir():
                if item.is_file():
                    files.append({
                        'name': item.name,
                        'size': item.stat().st_size,
                        'mtime': item.stat().st_mtime,
                        'ext': item.suffix,
                    })
                elif item.is_dir():
                    dirs.append({
                        'name': item.name,
                        'file_count': len(list(item.iterdir())),
                    })
        except PermissionError:
            pass
        
        return {
            'path': str(target),
            'files': files,
            'dirs': dirs,
            'total_files': len(files),
            'total_dirs': len(dirs),
            'scan_time': time.time(),
        }
    
    def detect_changes(self) -> List[Dict]:
        """检测文件变化"""
        current = self.scan()
        changes = []
        
        current_files = {f['name']: f for f in current['files']}
        last_files = {f['name']: f for f in self._last_scan.get('files', [])}
        
        # 新增文件
        for name in current_files:
            if name not in last_files:
                changes.append({'type': 'created', 'file': name})
        
        # 删除文件
        for name in last_files:
            if name not in current_files:
                changes.append({'type': 'deleted', 'file': name})
        
        # 修改文件
        for name in current_files:
            if name in last_files:
                if current_files[name]['mtime'] != last_files[name]['mtime']:
                    changes.append({'type': 'modified', 'file': name})
        
        self._last_scan = current
        return changes


class NetworkMonitor:
    """网络状态监控"""
    
    def __init__(self):
        self._last_check = None
    
    def check(self) -> Dict:
        """检查网络状态"""
        import subprocess
        
        status = {
            'timestamp': time.time(),
            'internet': False,
            'dns': False,
            'latency': None,
            'interfaces': [],
        }
        
        # 检查外网连接
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                capture_output=True,
                timeout=5
            )
            status['internet'] = result.returncode == 0
        except:
            pass
        
        # 检查 DNS
        try:
            result = subprocess.run(
                ['nslookup', 'google.com'],
                capture_output=True,
                timeout=5
            )
            status['dns'] = result.returncode == 0
        except:
            pass
        
        # 获取网络接口
        try:
            result = subprocess.run(
                ['ip', 'addr'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                interfaces = []
                for line in result.stdout.split('\n'):
                    if line.startswith('    inet '):
                        interfaces.append(line.strip())
                status['interfaces'] = interfaces[:5]  # 只取前5个
        except:
            pass
        
        self._last_check = status
        return status


class SystemMonitor:
    """系统资源监控"""
    
    def check(self) -> Dict:
        """检查系统资源"""
        import subprocess
        
        status = {
            'timestamp': time.time(),
            'cpu': {},
            'memory': {},
            'disk': {},
            'uptime': None,
        }
        
        # CPU 信息
        try:
            with open('/proc/loadavg') as f:
                load = f.read().strip().split()
                status['cpu'] = {
                    'load_1m': float(load[0]),
                    'load_5m': float(load[1]),
                    'load_15m': float(load[2]),
                }
        except:
            pass
        
        # 内存信息
        try:
            with open('/proc/meminfo') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if line.startswith('MemTotal:'):
                        status['memory']['total'] = line.split()[1]
                    elif line.startswith('MemAvailable:'):
                        status['memory']['available'] = line.split()[1]
                    elif line.startswith('MemFree:'):
                        status['memory']['free'] = line.split()[1]
        except:
            pass
        
        # 磁盘信息
        try:
            result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    status['disk'] = {
                        'total': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'usage_percent': parts[4],
                    }
        except:
            pass
        
        # 运行时间
        try:
            with open('/proc/uptime') as f:
                uptime = float(f.read().split()[0])
                status['uptime'] = uptime
        except:
            pass
        
        return status


class SafeActionExecutor:
    """安全动作执行器"""
    
    def __init__(self, workspace: str = '/tmp/mves_workspace'):
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)
        self.allowed_commands = [
            'ls', 'cat', 'head', 'tail', 'wc', 'find',
            'grep', 'echo', 'mkdir', 'touch', 'pwd',
            'df', 'free', 'ps', 'uptime', 'whoami',
            'ping', 'curl', 'nslookup',
        ]
        self.forbidden_patterns = [
            'rm -rf', 'sudo', 'chmod 777', 'mkfs',
            'dd if=', '>', '|', ';', '&&',
        ]
    
    def validate_command(self, command: str) -> bool:
        """验证命令安全性"""
        # 检查禁止模式
        for pattern in self.forbidden_patterns:
            if pattern in command:
                return False
        
        # 检查是否在允许列表
        cmd = command.split()[0] if ' ' in command else command
        return cmd in self.allowed_commands
    
    def execute(self, action: Dict) -> Dict:
        """安全执行动作"""
        import subprocess
        
        command = action.get('command', '')
        
        # 验证安全性
        if not self.validate_command(command):
            return {
                'success': False,
                'error': f'Command not allowed: {command}',
                'action': action,
            }
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace)
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[:1000],  # 限制输出
                'stderr': result.stderr[:500],
                'returncode': result.returncode,
                'action': action,
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out',
                'action': action,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': action,
            }


class MVESRealWorldBridge:
    """
    mves-realworld 桥接器
    
    连接 mves 多向量演化系统与真实世界
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.workspace = self.config.get('workspace', '/tmp/mves_workspace')
        
        # 初始化监控器
        self.file_monitor = FileSystemMonitor(self.workspace)
        self.network_monitor = NetworkMonitor()
        self.system_monitor = SystemMonitor()
        self.action_executor = SafeActionExecutor(self.workspace)
        
        # 状态历史
        self.state_history: List[RealWorldState] = []
        self.max_history = self.config.get('max_history', 1000)
        
        # 实验状态
        self.experiment_running = False
        self.generation = 0
        self.checkpoint_dir = Path(self.config.get('checkpoint_dir', '/tmp/mves_checkpoints'))
        self.checkpoint_dir.mkdir(exist_ok=True)
    
    def perceive(self) -> RealWorldState:
        """感知真实世界状态"""
        state = RealWorldState(
            timestamp=time.time(),
            files=self.file_monitor.scan(),
            network=self.network_monitor.check(),
            system=self.system_monitor.check(),
            processes={},  # 简化处理
        )
        
        # 保存历史
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
        
        return state
    
    def execute_action(self, action: Dict) -> Dict:
        """执行真实世界动作"""
        return self.action_executor.execute(action)
    
    def save_checkpoint(self, generation: int, population: List, metrics: Dict):
        """保存实验检查点"""
        checkpoint = {
            'generation': generation,
            'timestamp': time.time(),
            'population': population,
            'metrics': metrics,
            'state_history': [s.to_dict() for s in self.state_history[-100:]],
        }
        
        checkpoint_path = self.checkpoint_dir / f'checkpoint_gen_{generation}.json'
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        return str(checkpoint_path)
    
    def load_checkpoint(self, generation: int) -> Optional[Dict]:
        """加载实验检查点"""
        checkpoint_path = self.checkpoint_dir / f'checkpoint_gen_{generation}.json'
        
        if not checkpoint_path.exists():
            return None
        
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        
        return checkpoint
    
    def get_recent_changes(self, n: int = 10) -> List[Dict]:
        """获取最近的变化"""
        if len(self.state_history) < 2:
            return []
        
        changes = []
        for i in range(max(0, len(self.state_history) - n), len(self.state_history) - 1):
            old_state = self.state_history[i]
            new_state = self.state_history[i + 1]
            
            # 检测文件变化
            old_files = {f['name'] for f in old_state.files.get('files', [])}
            new_files = {f['name'] for f in new_state.files.get('files', [])}
            
            if old_files != new_files:
                changes.append({
                    'timestamp': new_state.timestamp,
                    'type': 'file_change',
                    'added': list(new_files - old_files),
                    'removed': list(old_files - new_files),
                })
        
        return changes
    
    def get_status(self) -> Dict:
        """获取桥接器状态"""
        return {
            'workspace': str(self.workspace),
            'state_history_size': len(self.state_history),
            'experiment_running': self.experiment_running,
            'current_generation': self.generation,
            'checkpoints': len(list(self.checkpoint_dir.glob('checkpoint_*.json'))),
        }


# 便捷函数
def create_bridge(config: Dict = None) -> MVESRealWorldBridge:
    """创建桥接器"""
    return MVESRealWorldBridge(config)


if __name__ == '__main__':
    print("=" * 70)
    print("mves-realworld 桥接器测试")
    print("=" * 70)
    
    # 创建桥接器
    bridge = create_bridge()
    
    print("\n1. 感知真实世界状态")
    state = bridge.perceive()
    print(f"  文件数: {state.files.get('total_files', 0)}")
    print(f"  网络状态: {'✅' if state.network.get('internet') else '❌'}")
    print(f"  系统运行时间: {state.system.get('uptime', 0):.0f}s")
    
    print("\n2. 执行安全动作")
    result = bridge.execute_action({'command': 'ls -la'})
    print(f"  成功: {'✅' if result['success'] else '❌'}")
    print(f"  输出: {result.get('stdout', '')[:100]}...")
    
    print("\n3. 检查状态")
    status = bridge.get_status()
    print(f"  状态历史: {status['state_history_size']} entries")
    print(f"  检查点: {status['checkpoints']} checkpoints")
    
    print("\n" + "=" * 70)
    print("✅ mves-realworld 桥接器测试完成!")
    print("=" * 70)
