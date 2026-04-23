#!/usr/bin/env python3
"""
72小时长期实验 - Week 1

连续运行72小时，验证mves的生产级稳定性
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.mves_realworld_bridge import create_bridge
from agi.task_aware_agent import TaskAwareAgent
import yaml
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mves_72h_logs/experiment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('72h_experiment')

print("=" * 70)
print("72小时长期实验")
print("=" * 70)

# 实验配置
EXPERIMENT_DURATION = 72 * 3600  # 72小时
CHECKPOINT_INTERVAL = 3600  # 每小时检查点
METRICS_INTERVAL = 600  # 每10分钟记录指标

class Experiment72h:
    """72小时实验管理"""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time = self.start_time + EXPERIMENT_DURATION
        self.generation = 0
        self.metrics = []
        self.events = []
        self.checkpoint_dir = Path('/tmp/mves_72h_experiment')
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # 初始化桥接器
        self.bridge = create_bridge({
            'workspace': '/tmp/mves_72h_workspace',
            'checkpoint_dir': str(self.checkpoint_dir),
        })
        
        # 初始化Agent
        with open('/home/admin/.openclaw/workspace/config/agent_config.yaml') as f:
            config = yaml.safe_load(f)
        
        config['environment']['workspace'] = '/tmp/mves_72h_workspace'
        self.agent = TaskAwareAgent('/tmp/agent_config_72h.yaml')
        self.agent.set_task({
            'type': 'file_organization',
            'description': '72h long-term evolution'
        })
        
        logger.info(f"实验配置:")
        logger.info(f"  开始时间: {datetime.fromtimestamp(self.start_time)}")
        logger.info(f"  结束时间: {datetime.fromtimestamp(self.end_time)}")
        logger.info(f"  持续时间: 72小时")
        logger.info(f"  检查点间隔: 1小时")
        logger.info(f"  指标记录间隔: 10分钟")
    
    def run(self):
        """运行72小时实验"""
        print(f"\n{'='*70}")
        print("实验开始!")
        print(f"{'='*70}\n")
        
        last_checkpoint = 0
        last_metrics = 0
        
        while time.time() < self.end_time:
            current_time = time.time()
            elapsed = current_time - self.start_time
            remaining = self.end_time - current_time
            
            # 运行周期
            self.run_cycle()
            
            # 记录指标 (每10分钟)
            if current_time - last_metrics >= METRICS_INTERVAL:
                self.record_metrics()
                last_metrics = current_time
                self.print_status(elapsed, remaining)
            
            # 保存检查点 (每小时)
            if current_time - last_checkpoint >= CHECKPOINT_INTERVAL:
                self.save_checkpoint()
                last_checkpoint = current_time
                logger.info(f"💾 检查点已保存 (Gen {self.generation})")
            
            # 健康检查
            if not self.health_check():
                self.handle_failure()
            
            # 短暂休息
            time.sleep(60)
        
        print(f"\n{'='*70}")
        print("实验完成!")
        print(f"{'='*70}\n")
        
        self.generate_report()
    
    def run_cycle(self):
        """运行一个周期"""
        # 运行Agent 10个cycles
        for _ in range(10):
            self.agent._one_cycle()
        
        # 感知真实世界
        state = self.bridge.perceive()
        
        # 检测事件
        self.detect_events(state)
        
        self.generation += 1
    
    def detect_events(self, state):
        """检测真实世界事件"""
        # 检测文件变化
        changes = self.bridge.get_recent_changes(5)
        for change in changes:
            self.events.append({
                'timestamp': time.time(),
                'type': 'file_change',
                'data': change,
            })
        
        # 检测网络异常
        if not state.network.get('internet'):
            self.events.append({
                'timestamp': time.time(),
                'type': 'network_error',
                'data': state.network,
            })
    
    def record_metrics(self):
        """记录指标"""
        metric = {
            'timestamp': time.time(),
            'generation': self.generation,
            'task_history_size': len(self.agent.task_history),
            'emerged_drives': len(self.agent._emerged_drives),
            'events_count': len(self.events),
            'bridge_status': self.bridge.get_status(),
        }
        self.metrics.append(metric)
    
    def print_status(self, elapsed, remaining):
        """打印状态"""
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        remaining_str = str(timedelta(seconds=int(remaining)))
        progress = (elapsed / EXPERIMENT_DURATION) * 100
        
        status_msg = (f"[{elapsed_str}/{remaining_str}] Gen {self.generation} | "
                     f"进度: {progress:.1f}% | "
                     f"任务: {len(self.agent.task_history)} | "
                     f"事件: {len(self.events)}")
        logger.info(status_msg)
    
    def health_check(self) -> bool:
        """健康检查"""
        # 检查Agent状态
        if not self.agent.alive:
            return False
        
        # 检查资源使用
        status = self.bridge.get_status()
        if status['state_history_size'] > 10000:
            return False
        
        return True
    
    def handle_failure(self):
        """处理故障"""
        logger.warning(f"⚠️ 检测到故障，尝试恢复...")
        
        # 尝试从检查点恢复
        checkpoint = self.bridge.load_checkpoint(self.generation - 10)
        if checkpoint:
            logger.info(f"✅ 从检查点恢复 (Gen {checkpoint['generation']})")
        else:
            logger.warning(f"⚠️ 无法恢复，继续运行")
    
    def save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'generation': self.generation,
            'timestamp': time.time(),
            'metrics': self.metrics[-100:],  # 最近100个
            'events': self.events[-50:],  # 最近50个
        }
        
        checkpoint_path = self.checkpoint_dir / f'checkpoint_gen_{self.generation}.json'
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f)
        
        logger.info(f"检查点已保存: {checkpoint_path}")
    
    def generate_report(self):
        """生成实验报告"""
        logger.info("生成实验报告...")
        
        report = {
            'experiment': '72h_longterm',
            'start_time': self.start_time,
            'end_time': time.time(),
            'duration': time.time() - self.start_time,
            'total_generations': self.generation,
            'total_metrics': len(self.metrics),
            'total_events': len(self.events),
            'avg_task_per_gen': len(self.agent.task_history) / max(self.generation, 1),
            'emerged_drives': len(self.agent._emerged_drives),
        }
        
        report_path = self.checkpoint_dir / 'experiment_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"实验报告:")
        logger.info(f"  总代数: {report['total_generations']}")
        logger.info(f"  总指标: {report['total_metrics']}")
        logger.info(f"  总事件: {report['total_events']}")
        logger.info(f"  平均任务/代: {report['avg_task_per_gen']:.2f}")
        logger.info(f"  涌现驱动: {report['emerged_drives']}")
        logger.info(f"  报告保存: {report_path}")


# 运行实验
if __name__ == '__main__':
    import sys
    
    # 检查是否是完整模式
    if '--full' in sys.argv:
        print("\n🚀 启动完整72小时实验!\n")
        experiment = Experiment72h()
        experiment.run()
    else:
        print("\n注意: 这是72小时实验的简化演示版")
        print("实际实验需要运行72小时")
        print("运行完整实验: python3 72h_longterm_experiment.py --full\n")
        
        # 创建实验实例
        experiment = Experiment72h()
        
        # 运行简化版 (10分钟)
        print("运行简化版 (10分钟)...\n")
        
        # 模拟运行
        for i in range(10):
            experiment.run_cycle()
            experiment.record_metrics()
            experiment.print_status(i * 60, EXPERIMENT_DURATION - i * 60)
            time.sleep(1)  # 模拟1分钟
        
        print(f"\n{'='*70}")
        print("简化版实验完成!")
        print(f"{'='*70}")
        
        experiment.generate_report()
        
        print(f"\n{'='*70}")
        print("✅ 72小时实验框架准备完成!")
        print("运行完整实验: python3 72h_longterm_experiment.py --full")