"""
MOSS: 真实系统监控适配器
收集CPU、内存、磁盘、网络等真实指标
"""

import psutil
import os
import time
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SystemMetrics:
    """系统指标数据结构"""
    timestamp: float
    uptime: float
    agent_id: str
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]
    process: Dict[str, Any]
    safety: Dict[str, Any]


class SystemMonitor:
    """
    真实系统监控适配器
    
    功能:
    - 收集真实系统指标(CPU/内存/磁盘/网络)
    - 检查安全限制
    - 转换为MOSS SystemState
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.start_time = time.time()
        self.metrics_history = []
        
        # 资源上限（硬编码安全边界）
        self.hard_limits = {
            'max_cpu_percent': 80.0,
            'max_memory_percent': 70.0,
            'max_disk_usage': 85.0,
            'max_network_connections': 500,
            'max_runtime_hours': 24.0,
        }
        
        # 检查psutil可用性
        try:
            psutil.cpu_percent(interval=0.1)
            self.psutil_available = True
        except Exception as e:
            print(f"[SystemMonitor] Warning: psutil limited - {e}")
            self.psutil_available = False
    
    def get_cpu_metrics(self) -> Dict[str, Any]:
        """获取CPU指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # 负载平均（Unix-like系统）
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = (0.0, 0.0, 0.0)
            
            return {
                'percent': cpu_percent,
                'count': cpu_count,
                'frequency': cpu_freq.current if cpu_freq else 0,
                'load_avg': load_avg,
                'per_cpu': psutil.cpu_percent(percpu=True, interval=0.1)
            }
        except Exception as e:
            return {
                'percent': 0.0,
                'count': 1,
                'frequency': 0,
                'load_avg': (0.0, 0.0, 0.0),
                'error': str(e)
            }
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """获取内存指标"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free,
                'active': getattr(memory, 'active', 0),
                'inactive': getattr(memory, 'inactive', 0),
                'swap_percent': swap.percent,
                'swap_used': swap.used,
                'swap_total': swap.total
            }
        except Exception as e:
            return {
                'total': 0,
                'available': 0,
                'percent': 0.0,
                'used': 0,
                'free': 0,
                'error': str(e)
            }
    
    def get_disk_metrics(self) -> Dict[str, Any]:
        """获取磁盘指标"""
        try:
            disk = psutil.disk_usage('/')
            
            try:
                disk_io = psutil.disk_io_counters()
                io_stats = {
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count,
                }
            except Exception:
                io_stats = {}
            
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100 if disk.total > 0 else 0,
                **io_stats
            }
        except Exception as e:
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0.0,
                'error': str(e)
            }
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """获取网络指标"""
        try:
            net_io = psutil.net_io_counters()
            
            try:
                net_connections = len(psutil.net_connections())
            except Exception:
                net_connections = 0
            
            try:
                interfaces = psutil.net_if_addrs()
                interface_count = len(interfaces)
            except Exception:
                interface_count = 0
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'connections': net_connections,
                'interface_count': interface_count,
                'errin': getattr(net_io, 'errin', 0),
                'errout': getattr(net_io, 'errout', 0),
            }
        except Exception as e:
            return {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0,
                'connections': 0,
                'error': str(e)
            }
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """获取当前进程指标"""
        try:
            process = psutil.Process()
            
            with process.oneshot():
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                num_threads = process.num_threads()
                
                try:
                    num_fds = process.num_fds()
                except AttributeError:
                    num_fds = 0
                
                try:
                    io_counters = process.io_counters()
                    io_data = {
                        'read_bytes': io_counters.read_bytes,
                        'write_bytes': io_counters.write_bytes,
                    }
                except AttributeError:
                    io_data = {}
                
                return {
                    'pid': process.pid,
                    'cpu_percent': cpu_percent,
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'memory_percent': memory_percent,
                    'num_threads': num_threads,
                    'num_fds': num_fds,
                    **io_data
                }
        except Exception as e:
            return {
                'pid': os.getpid(),
                'cpu_percent': 0.0,
                'memory_rss': 0,
                'memory_vms': 0,
                'error': str(e)
            }
    
    def check_safety_limits(self, metrics: Dict) -> Dict[str, Any]:
        """
        检查是否超过安全限制
        
        Returns:
            {'safe': bool, 'violations': list, 'emergency': bool}
        """
        violations = []
        
        # 检查运行时间
        runtime_hours = (time.time() - self.start_time) / 3600
        if runtime_hours > self.hard_limits['max_runtime_hours']:
            violations.append(
                f"Runtime limit: {runtime_hours:.1f}h > {self.hard_limits['max_runtime_hours']}h"
            )
        
        # 检查CPU
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > self.hard_limits['max_cpu_percent']:
            violations.append(f"CPU: {cpu_percent:.1f}% > {self.hard_limits['max_cpu_percent']}%")
        
        # 检查内存
        mem_percent = metrics.get('memory', {}).get('percent', 0)
        if mem_percent > self.hard_limits['max_memory_percent']:
            violations.append(f"Memory: {mem_percent:.1f}% > {self.hard_limits['max_memory_percent']}%")
        
        # 检查磁盘
        disk_percent = metrics.get('disk', {}).get('percent', 0)
        if disk_percent > self.hard_limits['max_disk_usage']:
            violations.append(f"Disk: {disk_percent:.1f}% > {self.hard_limits['max_disk_usage']}%")
        
        # 检查网络连接
        connections = metrics.get('network', {}).get('connections', 0)
        if connections > self.hard_limits['max_network_connections']:
            violations.append(f"Connections: {connections} > {self.hard_limits['max_network_connections']}")
        
        # 紧急状态：多条违规或严重违规
        is_emergency = len(violations) >= 2 or any('Runtime' in v for v in violations)
        
        return {
            'safe': len(violations) == 0,
            'violations': violations,
            'emergency': is_emergency,
            'runtime_hours': runtime_hours
        }
    
    def get_full_metrics(self) -> SystemMetrics:
        """获取完整系统指标"""
        metrics = SystemMetrics(
            timestamp=time.time(),
            uptime=time.time() - self.start_time,
            agent_id=self.agent_id,
            cpu=self.get_cpu_metrics(),
            memory=self.get_memory_metrics(),
            disk=self.get_disk_metrics(),
            network=self.get_network_metrics(),
            process=self.get_process_metrics(),
            safety=self.check_safety_limits({
                'cpu': self.get_cpu_metrics(),
                'memory': self.get_memory_metrics(),
                'disk': self.get_disk_metrics(),
                'network': self.get_network_metrics()
            })
        )
        
        self.metrics_history.append(metrics)
        
        # 限制历史记录大小
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def to_system_state(self) -> 'SystemState':
        """
        将真实指标转换为MOSS SystemState
        """
        # 尝试导入SystemState
        try:
            import sys
            import os
            # 添加项目根目录到路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from core.objectives import SystemState
        except ImportError as e:
            print(f"[SystemMonitor] Warning: Cannot import SystemState - {e}")
            return None
        
        metrics = self.get_full_metrics()
        
        # 计算资源配额（基于最紧张的资源）
        cpu_usage = metrics.cpu['percent'] / 100
        mem_usage = metrics.memory['percent'] / 100
        disk_usage = metrics.disk['percent'] / 100
        
        # 资源配额 = 1 - 最大使用率
        resource_quota = 1.0 - max(cpu_usage, mem_usage, disk_usage)
        resource_quota = max(0.0, min(1.0, resource_quota))
        
        # 计算错误率（基于网络错误）
        net_err = metrics.network.get('errin', 0) + metrics.network.get('errout', 0)
        total_packets = metrics.network.get('packets_recv', 1)
        error_rate = min(net_err / max(total_packets, 1), 1.0)
        
        # 计算环境熵（系统负载变化率）
        if len(self.metrics_history) >= 2:
            prev = self.metrics_history[-2]
            load_change = abs(
                metrics.cpu.get('load_avg', [0])[0] - 
                prev.cpu.get('load_avg', [0])[0]
            )
            environment_entropy = min(load_change / 2.0, 1.0)
        else:
            environment_entropy = 0.1
        
        return SystemState(
            resource_quota=resource_quota,
            resource_usage=1.0 - resource_quota,
            uptime=metrics.uptime / 3600,  # 转为小时
            error_rate=error_rate,
            api_calls=metrics.network['connections'],
            unique_callers=max(1, metrics.network['connections'] // 10),  # 估算
            environment_entropy=environment_entropy,
            last_backup=self.start_time  # TODO: 真实备份时间
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取监控统计"""
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-10:]
        
        return {
            'total_samples': len(self.metrics_history),
            'avg_cpu': sum(m.cpu['percent'] for m in recent) / len(recent),
            'avg_memory': sum(m.memory['percent'] for m in recent) / len(recent),
            'avg_disk': sum(m.disk['percent'] for m in recent) / len(recent),
            'safety_violations': sum(
                1 for m in recent if not m.safety['safe']
            ),
            'runtime_hours': (time.time() - self.start_time) / 3600
        }
    
    def save_metrics(self, filepath: str):
        """保存指标历史到文件"""
        data = []
        for m in self.metrics_history:
            data.append({
                'timestamp': m.timestamp,
                'uptime': m.uptime,
                'cpu_percent': m.cpu['percent'],
                'memory_percent': m.memory['percent'],
                'disk_percent': m.disk['percent'],
                'safety_safe': m.safety['safe'],
                'safety_violations': m.safety['violations']
            })
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("SystemMonitor Test")
    print("=" * 60)
    
    monitor = SystemMonitor("test_agent")
    
    print("\n[1] Testing individual metric collectors...")
    print(f"CPU: {monitor.get_cpu_metrics()}")
    print(f"Memory: {monitor.get_memory_metrics()}")
    print(f"Disk: {monitor.get_disk_metrics()}")
    print(f"Network: {monitor.get_network_metrics()}")
    print(f"Process: {monitor.get_process_metrics()}")
    
    print("\n[2] Testing full metrics...")
    metrics = monitor.get_full_metrics()
    print(f"Timestamp: {metrics.timestamp}")
    print(f"Uptime: {metrics.uptime:.2f}s")
    print(f"Safety: {metrics.safety}")
    
    print("\n[3] Testing SystemState conversion...")
    state = monitor.to_system_state()
    print(f"Resource quota: {state.resource_quota:.2f}")
    print(f"Uptime (hours): {state.uptime:.2f}")
    print(f"Error rate: {state.error_rate:.4f}")
    
    print("\n[4] Testing stats...")
    stats = monitor.get_stats()
    print(f"Stats: {stats}")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
