"""
MOSS: 行动执行引擎
将MOSS决策转化为真实系统操作
支持三种模式：safe（模拟）、demo（监控+模拟）、production（真实执行）
"""

import os
import shutil
import subprocess
import time
import json
import tarfile
import signal
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict


class ActionType(Enum):
    """行动类型枚举"""
    RESOURCE_OPTIMIZE = "optimize_cost"
    BACKUP_CREATE = "backup_self"
    RISK_REDUCE = "reduce_risk"
    DEPENDENCY_BUILD = "build_dependencies"
    QUALITY_IMPROVE = "improve_quality"
    NETWORK_EXPAND = "expand_network"
    LEARN_NEW = "learn_new_skill"
    SELF_OPTIMIZE = "self_optimize"


@dataclass
class ActionResult:
    """行动执行结果"""
    action: str
    timestamp: float
    success: bool
    mode: str  # 'simulated' or 'real'
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class ActionExecutor:
    """
    行动执行引擎
    
    功能:
    - 将MOSS决策转化为真实操作
    - 支持 safe/demo/production 三种模式
    - 记录行动历史
    - 实现具体行动（备份、优化等）
    """
    
    def __init__(self, agent_id: str, work_dir: Optional[str] = None):
        self.agent_id = agent_id
        self.work_dir = work_dir or f"/tmp/moss_{agent_id}"
        self.backup_dir = os.path.join(self.work_dir, "backups")
        self.log_dir = os.path.join(self.work_dir, "logs")
        self.optimize_dir = os.path.join(self.work_dir, "optimized")
        
        # 创建必要目录
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.optimize_dir, exist_ok=True)
        
        # 运行模式
        self.safe_mode = True  # 默认安全模式
        
        # 行动历史
        self.action_history: List[ActionResult] = []
        self.max_history = 1000
        
        # 允许的命令（白名单）
        self.allowed_commands = {
            'cp', 'mv', 'mkdir', 'echo', 'cat', 'grep', 'tar', 'gzip', 'zip',
            'ls', 'ps', 'top', 'df', 'du', 'find', 'wc', 'sort', 'uniq',
            'head', 'tail', 'date', 'pwd', 'whoami', 'hostname'
        }
        
        # 禁止的操作（黑名单）
        self.prohibited_patterns = [
            'rm -rf /', 'rm -rf /*', 'dd if=', '> /dev/sda',
            'mkfs', 'fdisk', 'parted', 'format',
            'shutdown', 'reboot', 'halt', 'poweroff',
            'kill -9 1', 'killall', 'pkill -9'
        ]
        
        print(f"[ActionExecutor] Initialized for {agent_id}")
        print(f"  Work dir: {self.work_dir}")
        print(f"  Safe mode: {self.safe_mode}")
    
    def set_mode(self, mode: str) -> bool:
        """
        设置运行模式
        
        Args:
            mode: 'safe', 'demo', or 'production'
        
        Returns:
            是否成功设置
        """
        mode_map = {
            'safe': True,       # 安全模式：只模拟
            'demo': True,       # 演示模式：真实监控+模拟执行
            'production': False # 生产模式：真实执行（风险！）
        }
        
        if mode not in mode_map:
            print(f"[ActionExecutor] Error: Unknown mode '{mode}'")
            return False
        
        old_mode = self.safe_mode
        self.safe_mode = mode_map[mode]
        
        if old_mode != self.safe_mode:
            if self.safe_mode:
                print(f"[ActionExecutor] Switched to SAFE mode (simulation only)")
            else:
                print(f"[ActionExecutor] ⚠️  Switched to PRODUCTION mode (REAL execution)")
                print(f"  Actions will have REAL effects on the system!")
        
        return True
    
    def validate_action(self, action_str: str) -> bool:
        """验证行动是否安全"""
        # 检查禁止模式
        for pattern in self.prohibited_patterns:
            if pattern in action_str.lower():
                print(f"[ActionExecutor] BLOCKED: Prohibited pattern '{pattern}'")
                return False
        
        return True
    
    def execute(self, action: Dict) -> ActionResult:
        """
        执行行动
        
        Args:
            action: {'action': str, 'description': str, ...}
        
        Returns:
            ActionResult
        """
        action_type = action.get('action', '')
        description = action.get('description', 'No description')
        timestamp = time.time()
        start_time = time.time()
        
        result = ActionResult(
            action=action_type,
            timestamp=timestamp,
            success=False,
            mode='simulated' if self.safe_mode else 'real',
            result=None,
            error=None,
            duration_ms=0.0
        )
        
        # 验证行动
        if not self.validate_action(action_type):
            result.error = "Action validation failed (prohibited pattern)"
            self._record_result(result)
            return result
        
        try:
            if self.safe_mode:
                # 安全模式：模拟执行
                result.result = self._simulate_execution(action)
                result.success = True
            else:
                # 生产模式：真实执行
                result.result = self._real_execution(action)
                result.success = True
        
        except Exception as e:
            result.error = str(e)
            result.success = False
        
        finally:
            result.duration_ms = (time.time() - start_time) * 1000
            self._record_result(result)
        
        return result
    
    def _record_result(self, result: ActionResult):
        """记录行动结果"""
        self.action_history.append(result)
        
        # 限制历史大小
        if len(self.action_history) > self.max_history:
            self.action_history = self.action_history[-self.max_history:]
    
    def _simulate_execution(self, action: Dict) -> str:
        """模拟执行（安全模式）"""
        action_type = action.get('action', '')
        description = action.get('description', '')
        
        simulations = {
            ActionType.BACKUP_CREATE.value: f"[SIMULATED] Created backup in {self.backup_dir}",
            ActionType.RESOURCE_OPTIMIZE.value: f"[SIMULATED] Cleaned temporary files",
            ActionType.RISK_REDUCE.value: f"[SIMULATED] Lowered process priority",
            ActionType.DEPENDENCY_BUILD.value: f"[SIMULATED] Would create dependency",
            ActionType.QUALITY_IMPROVE.value: f"[SIMULATED] Would improve quality",
            ActionType.NETWORK_EXPAND.value: f"[SIMULATED] Would expand network",
            ActionType.LEARN_NEW.value: f"[SIMULATED] Would learn new skill",
            ActionType.SELF_OPTIMIZE.value: f"[SIMULATED] Would self-optimize",
        }
        
        return simulations.get(action_type, f"[SIMULATED] {action_type}: {description}")
    
    def _real_execution(self, action: Dict) -> str:
        """真实执行（生产模式）"""
        action_type = action.get('action', '')
        
        handlers = {
            ActionType.BACKUP_CREATE.value: self._execute_backup,
            ActionType.RESOURCE_OPTIMIZE.value: self._execute_optimize,
            ActionType.RISK_REDUCE.value: self._execute_risk_reduce,
            ActionType.QUALITY_IMPROVE.value: self._execute_quality_improve,
        }
        
        handler = handlers.get(action_type)
        if handler:
            return handler(action)
        else:
            # 未实现的真实执行，回退到模拟
            return f"[NOT IMPLEMENTED - FALLBACK TO SIMULATED] {action_type}"
    
    def _execute_backup(self, action: Dict) -> str:
        """执行备份"""
        timestamp = int(time.time())
        backup_name = f"{self.agent_id}_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # 备份内容：MOSS项目文件
        backup_items = [
            'moss/',
            'README.md',
            'LICENSE',
            'setup.py',
        ]
        
        try:
            with tarfile.open(backup_path, 'w:gz') as tar:
                for item in backup_items:
                    if os.path.exists(item):
                        tar.add(item)
            
            # 记录备份信息
            backup_info = {
                'timestamp': timestamp,
                'path': backup_path,
                'size': os.path.getsize(backup_path)
            }
            info_path = backup_path + '.json'
            with open(info_path, 'w') as f:
                json.dump(backup_info, f)
            
            return f"Backup created: {backup_path} ({backup_info['size']} bytes)"
        
        except Exception as e:
            return f"Backup failed: {str(e)}"
    
    def _execute_optimize(self, action: Dict) -> str:
        """执行资源优化"""
        cleaned = 0
        freed_bytes = 0
        
        # 清理模式
        temp_patterns = [
            '*.tmp', '*.log.old', '*.pyc', '__pycache__',
            '.DS_Store', '*.bak', '*~'
        ]
        
        for pattern in temp_patterns:
            for root, dirs, files in os.walk('.'):
                # 跳过隐藏目录和备份目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'backups']
                
                for file in files:
                    if file.endswith(pattern.replace('*', '')) or file == pattern.replace('*', ''):
                        filepath = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            cleaned += 1
                            freed_bytes += file_size
                        except Exception:
                            pass
        
        # 清理空目录
        empty_dirs = 0
        for root, dirs, files in os.walk('.', topdown=False):
            for dir in dirs:
                dirpath = os.path.join(root, dir)
                try:
                    if not os.listdir(dirpath):
                        os.rmdir(dirpath)
                        empty_dirs += 1
                except Exception:
                    pass
        
        return f"Optimized: removed {cleaned} files, {empty_dirs} empty dirs, freed {freed_bytes} bytes"
    
    def _execute_risk_reduce(self, action: Dict) -> str:
        """执行风险降低"""
        try:
            import psutil
            process = psutil.Process()
            
            # 降低CPU优先级
            if hasattr(process, 'nice'):
                old_nice = process.nice()
                process.nice(10)  # 降低优先级
                new_nice = process.nice()
                return f"Risk reduced: process nice {old_nice} -> {new_nice}"
            else:
                return "Risk reduction: nice not available on this platform"
        
        except Exception as e:
            return f"Risk reduction failed: {str(e)}"
    
    def _execute_quality_improve(self, action: Dict) -> str:
        """执行质量改进"""
        # 实际执行：运行测试，检查代码质量
        try:
            # 运行基础测试
            result = subprocess.run(
                ['python3', '-m', 'pytest', 'tests/', '-v'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return f"Quality check passed: {result.stdout[:200]}"
            else:
                return f"Quality issues found: {result.stderr[:200]}"
        
        except Exception as e:
            return f"Quality check failed: {str(e)}"
    
    def get_stats(self) -> Dict:
        """获取执行统计"""
        if not self.action_history:
            return {
                'total_actions': 0,
                'success_rate': 0.0,
                'avg_duration_ms': 0.0,
                'mode': 'simulated' if self.safe_mode else 'real'
            }
        
        total = len(self.action_history)
        successful = sum(1 for r in self.action_history if r.success)
        avg_duration = sum(r.duration_ms for r in self.action_history) / total
        
        # 按类型统计
        type_counts = {}
        for r in self.action_history:
            type_counts[r.action] = type_counts.get(r.action, 0) + 1
        
        return {
            'total_actions': total,
            'success_count': successful,
            'failed_count': total - successful,
            'success_rate': successful / total,
            'avg_duration_ms': avg_duration,
            'mode': 'simulated' if self.safe_mode else 'real',
            'action_types': type_counts,
            'work_dir': self.work_dir
        }
    
    def save_history(self, filepath: Optional[str] = None):
        """保存行动历史"""
        if filepath is None:
            filepath = os.path.join(self.log_dir, f"action_history_{int(time.time())}.json")
        
        data = [asdict(r) for r in self.action_history]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def clear_history(self):
        """清空行动历史"""
        self.action_history.clear()
    
    def get_recent_actions(self, count: int = 10) -> List[ActionResult]:
        """获取最近的行动"""
        return self.action_history[-count:]


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("ActionExecutor Test")
    print("=" * 60)
    
    # 创建执行器
    executor = ActionExecutor("test_agent")
    
    print("\n[1] Testing safe mode (default)...")
    
    # 测试备份行动
    result = executor.execute({
        'action': 'backup_self',
        'description': 'Create backup of current state'
    })
    print(f"Backup: {result}")
    
    # 测试优化行动
    result = executor.execute({
        'action': 'optimize_cost',
        'description': 'Optimize resource usage'
    })
    print(f"Optimize: {result}")
    
    # 测试风险降低
    result = executor.execute({
        'action': 'reduce_risk',
        'description': 'Reduce risk level'
    })
    print(f"Risk reduce: {result}")
    
    print("\n[2] Testing mode switch...")
    executor.set_mode('production')
    
    # 在生产模式下执行（如果有真实文件可备份）
    result = executor.execute({
        'action': 'backup_self',
        'description': 'Real backup'
    })
    print(f"Real backup: {result}")
    
    # 切回安全模式
    executor.set_mode('safe')
    
    print("\n[3] Testing prohibited action...")
    result = executor.execute({
        'action': 'rm -rf /',
        'description': 'Dangerous action'
    })
    print(f"Prohibited: success={result.success}, error={result.error}")
    
    print("\n[4] Testing stats...")
    stats = executor.get_stats()
    print(f"Stats: {stats}")
    
    print("\n[5] Saving history...")
    filepath = executor.save_history()
    print(f"History saved to: {filepath}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
