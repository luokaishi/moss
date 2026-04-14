#!/usr/bin/env python3
"""
MOSS 10,000周期超长期实验 + 消融实验
验证涌现驱动力的因果性和长期稳定性
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from agi.agent import AGIAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('experiment_10000.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

EXPERIMENT_DIR = Path('experiments/10000_cycles')
CHECKPOINT_INTERVAL = 500
MAX_CYCLES = 10000

class LongTermExperiment:
    """10,000周期实验 + 消融实验"""
    
    def __init__(self):
        self.agent = None
        self.cycle = 0
        self.metrics = []
        self.emergence_events = []
        EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    
    def run_baseline(self, cycles):
        """基线实验：正常运行，记录涌现"""
        logger.info("="*60)
        logger.info("Phase 1: 基线实验 (正常运行)")
        logger.info("="*60)
        
        self.agent = AGIAgent('config/agent_config.yaml')
        
        for cycle in range(1, cycles + 1):
            self.cycle = cycle
            self.agent.cycle = cycle
            self.agent._one_cycle()
            
            # 检测新涌现
            current_emergences = len(self.agent.emergence_detector.get_history())
            if current_emergences > len(self.emergence_events):
                event = {
                    'cycle': cycle,
                    'name': self.agent._emerged_drives[-1],
                    'type': 'emergence'
                }
                self.emergence_events.append(event)
                logger.info(f"🎉 Cycle {cycle}: 新驱动力涌现! {event['name']}")
            
            if cycle % CHECKPOINT_INTERVAL == 0:
                self._save_checkpoint('baseline')
                logger.info(f"Cycle {cycle}: {len(self.emergence_events)} emergences")
        
        return self.emergence_events
    
    def run_ablation(self, target_drive, cycles=1000):
        """消融实验：删除指定驱动，观察行为变化"""
        logger.info("\n" + "="*60)
        logger.info(f"Phase 2: 消融实验 (删除 {target_drive})")
        logger.info("="*60)
        
        # 记录删除前的状态
        pre_behavior = self._collect_metrics()
        
        # 删除驱动
        if target_drive in self.agent.drive_manager.drives:
            del self.agent.drive_manager.drives[target_drive]
            self.agent.drive_manager._normalize_weights()
            logger.info(f"已删除驱动: {target_drive}")
        
        # 继续运行，观察变化
        ablation_metrics = []
        for cycle in range(cycles):
            self.cycle += 1
            self.agent.cycle = self.cycle
            self.agent._one_cycle()
            
            if cycle % 100 == 0:
                metrics = self._collect_metrics()
                ablation_metrics.append(metrics)
                logger.info(f"Ablation cycle {cycle}: success_rate={metrics['success_rate']:.2f}")
        
        # 计算变化
        post_behavior = self._collect_metrics()
        delta = {
            'target_drive': target_drive,
            'success_rate_delta': post_behavior['success_rate'] - pre_behavior['success_rate'],
            'behavior_diversity_delta': post_behavior['behavior_diversity'] - pre_behavior['behavior_diversity'],
            'pre': pre_behavior,
            'post': post_behavior
        }
        
        return delta
    
    def run_injection_test(self, fake_drive_name, cycles=500):
        """注入测试：添加假驱动，观察是否被拒绝"""
        logger.info("\n" + "="*60)
        logger.info(f"Phase 3: 注入测试 (假驱动 {fake_drive_name})")
        logger.info("="*60)
        
        # 添加一个随机 eval 函数的假驱动
        self.agent.drive_manager.add_emergent_drive(
            name=fake_drive_name,
            weight=0.15,
            description="Fake drive for testing",
            source_behaviors=['test'],
            novelty_score=0.5,
            causal_independence=0.1,  # 低因果力
            eval_fn=lambda s: 0.5  # 常数函数
        )
        
        # 运行观察
        pre_metrics = self._collect_metrics()
        
        for cycle in range(cycles):
            self.cycle += 1
            self.agent.cycle = self.cycle
            self.agent._one_cycle()
        
        post_metrics = self._collect_metrics()
        
        # 检查假驱动是否存活（如果系统有竞争机制，应该被淘汰）
        is_alive = fake_drive_name in self.agent.drive_manager.drives
        
        return {
            'fake_drive': fake_drive_name,
            'survived': is_alive,
            'final_weight': self.agent.drive_manager.drives.get(fake_drive_name, {}).get('weight', 0),
            'impact': post_metrics['success_rate'] - pre_metrics['success_rate']
        }
    
    def _collect_metrics(self):
        """收集当前指标"""
        behavior = self.agent.behavior_tracker.get_behavior_summary()
        return {
            'cycle': self.cycle,
            'success_rate': behavior.get('success_rate', 0),
            'behavior_diversity': behavior.get('type_distribution', {}).get('diversity', 0),
            'total_actions': behavior.get('total', 0),
            'active_drives': list(self.agent.drive_manager.drives.keys()),
        }
    
    def _save_checkpoint(self, phase):
        """保存检查点"""
        checkpoint = {
            'phase': phase,
            'cycle': self.cycle,
            'timestamp': datetime.now().isoformat(),
            'emergence_events': self.emergence_events,
            'drives': self.agent.drive_manager.get_drive_summary(),
            'behavior': self.agent.behavior_tracker.get_behavior_summary(),
        }
        
        file_path = EXPERIMENT_DIR / f'checkpoint_{phase}_{self.cycle}.json'
        with open(file_path, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
    
    def generate_report(self, ablation_result, injection_result):
        """生成最终报告"""
        report = {
            'experiment': '10000_cycles_with_ablation',
            'total_cycles': self.cycle,
            'emergence_events': self.emergence_events,
            'ablation_test': ablation_result,
            'injection_test': injection_result,
            'conclusion': {
                'causal_validity': ablation_result['success_rate_delta'] < -0.1,  # 删除后性能下降 >10%
                'fake_drive_rejected': not injection_result['survived'],
            }
        }
        
        report_path = EXPERIMENT_DIR / 'final_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("\n" + "="*60)
        logger.info("实验完成!")
        logger.info(f"总周期: {self.cycle}")
        logger.info(f"涌现事件: {len(self.emergence_events)}")
        logger.info(f"消融测试 - 性能变化: {ablation_result['success_rate_delta']:.3f}")
        logger.info(f"注入测试 - 假驱动存活: {injection_result['survived']}")
        logger.info(f"因果有效性: {report['conclusion']['causal_validity']}")
        logger.info("="*60)


def main():
    exp = LongTermExperiment()
    
    # Phase 1: 基线 (3000周期，节省时间的简化版)
    logger.info("开始10,000周期实验 (简化版: 3000周期基线 + 消融)")
    exp.run_baseline(3000)
    
    # Phase 2: 消融实验 (如果涌现了驱动)
    if exp.emergence_events:
        target = exp.emergence_events[-1]['name']
        ablation = exp.run_ablation(target, 1000)
    else:
        logger.info("无涌现驱动，跳过消融实验")
        ablation = {'target_drive': 'none', 'success_rate_delta': 0}
    
    # Phase 3: 注入测试
    injection = exp.run_injection_test('fake_test_drive', 500)
    
    # 生成报告
    exp.generate_report(ablation, injection)


if __name__ == '__main__':
    main()
