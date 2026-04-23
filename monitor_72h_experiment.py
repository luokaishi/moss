#!/usr/bin/env python3
"""
72小时实验监控脚本

定时检查实验状态，发送告警通知
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

import os
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
PID_FILE = '/tmp/mves_72h_full/experiment.pid'
LOG_FILE = '/tmp/mves_72h_logs/experiment.log'
CHECKPOINT_DIR = '/tmp/mves_72h_checkpoints/'
STATUS_FILE = '/tmp/mves_72h_full/monitor_status.json'
ALERT_THRESHOLD_CPU = 95  # CPU告警阈值
ALERT_THRESHOLD_MEM = 80  # 内存告警阈值

class ExperimentMonitor:
    """72小时实验监控器"""
    
    def __init__(self):
        self.status = {
            'last_check': time.time(),
            'check_count': 0,
            'alerts': [],
            'experiment_start': None,
            'experiment_end': None,
        }
        self.load_status()
    
    def load_status(self):
        """加载状态"""
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                self.status = json.load(f)
    
    def save_status(self):
        """保存状态"""
        with open(STATUS_FILE, 'w') as f:
            json.dump(self.status, f, indent=2)
    
    def get_pid(self) -> int:
        """获取实验PID"""
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                return int(f.read().strip())
        return None
    
    def check_process(self, pid: int) -> dict:
        """检查进程状态"""
        try:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', '%cpu,%mem,etime', '--no-headers'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                return {
                    'running': True,
                    'cpu': float(parts[0]),
                    'mem': float(parts[1]),
                    'etime': parts[2],
                }
            else:
                return {'running': False}
        except Exception as e:
            return {'running': False, 'error': str(e)}
    
    def check_log(self) -> dict:
        """检查日志"""
        if not os.path.exists(LOG_FILE):
            return {'exists': False}
        
        # 获取日志大小
        size = os.path.getsize(LOG_FILE)
        
        # 获取最后10行
        try:
            result = subprocess.run(
                ['tail', '-10', LOG_FILE],
                capture_output=True,
                text=True
            )
            last_lines = result.stdout.strip().split('\n')
        except:
            last_lines = []
        
        return {
            'exists': True,
            'size': size,
            'last_lines': last_lines,
        }
    
    def check_checkpoints(self) -> dict:
        """检查检查点"""
        if not os.path.exists(CHECKPOINT_DIR):
            return {'exists': False}
        
        checkpoints = list(Path(CHECKPOINT_DIR).glob('checkpoint_*.json'))
        
        return {
            'exists': True,
            'count': len(checkpoints),
            'latest': str(checkpoints[-1]) if checkpoints else None,
        }
    
    def send_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """发送告警"""
        alert = {
            'timestamp': time.time(),
            'type': alert_type,
            'severity': severity,
            'message': message,
        }
        
        self.status['alerts'].append(alert)
        
        # 打印告警
        emoji = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, 'ℹ️')
        print(f"{emoji} [{severity.upper()}] {message}")
    
    def check(self):
        """执行检查"""
        print(f"\n{'='*70}")
        print(f"72小时实验监控检查 #{self.status['check_count'] + 1}")
        print(f"时间: {datetime.now()}")
        print(f"{'='*70}")
        
        pid = self.get_pid()
        
        if not pid:
            self.send_alert('process_not_found', 'Experiment PID not found', 'critical')
            self.save_status()
            return
        
        # 检查进程
        process_status = self.check_process(pid)
        
        if not process_status['running']:
            self.send_alert('process_crashed', f'Experiment process {pid} crashed', 'critical')
            self.save_status()
            return
        
        print(f"✅ 进程运行中 (PID: {pid})")
        print(f"   CPU: {process_status['cpu']:.1f}%")
        print(f"   MEM: {process_status['mem']:.1f}%")
        print(f"   运行时间: {process_status['etime']}")
        
        # CPU告警
        if process_status['cpu'] > ALERT_THRESHOLD_CPU:
            self.send_alert('high_cpu', f'CPU usage {process_status["cpu"]:.1f}% > {ALERT_THRESHOLD_CPU}%', 'warning')
        
        # 内存告警
        if process_status['mem'] > ALERT_THRESHOLD_MEM:
            self.send_alert('high_memory', f'Memory usage {process_status["mem"]:.1f}% > {ALERT_THRESHOLD_MEM}%', 'warning')
        
        # 检查日志
        log_status = self.check_log()
        if log_status['exists']:
            print(f"✅ 日志正常 (大小: {log_status['size']} bytes)")
            if log_status['last_lines']:
                print(f"   最后日志: {log_status['last_lines'][-1][:80]}...")
        else:
            self.send_alert('log_not_found', 'Log file not found', 'warning')
        
        # 检查检查点
        checkpoint_status = self.check_checkpoints()
        if checkpoint_status['exists']:
            print(f"✅ 检查点: {checkpoint_status['count']} 个")
            if checkpoint_status['latest']:
                print(f"   最新: {checkpoint_status['latest']}")
        else:
            self.send_alert('checkpoint_not_found', 'Checkpoint directory not found', 'warning')
        
        # 更新状态
        self.status['check_count'] += 1
        self.status['last_check'] = time.time()
        self.save_status()
        
        print(f"\n✅ 检查完成")
        print(f"{'='*70}\n")


def main():
    """主函数"""
    monitor = ExperimentMonitor()
    
    # 立即执行一次检查
    monitor.check()
    
    print("监控已启动，将每10分钟检查一次")
    print("按 Ctrl+C 停止\n")
    
    # 定时检查 (每10分钟)
    try:
        while True:
            time.sleep(600)  # 10分钟
            monitor.check()
    except KeyboardInterrupt:
        print("\n监控已停止")


if __name__ == '__main__':
    main()
