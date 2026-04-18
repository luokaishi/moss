"""
Experiment v6.0 Quick - 快速验证实验 (1,000 周期)

简化版，快速验证核心功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path

from agi.drive_manager import DriveManager
from agi.environment_v2 import RealEnvironmentV2, EnvState


class ExperimentV6Quick:
    """v6.0 快速实验"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(f'logs/experiment_v6_quick_{timestamp}_seed{seed}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化
        env_config = {'workspace': str(self.output_dir / 'workspace')}
        self.env = RealEnvironmentV2(env_config)
        
        drives_config = [
            {'name': 'survival', 'weight': 0.25},
            {'name': 'optimization', 'weight': 0.20},
            {'name': 'influence', 'weight': 0.20},
            {'name': 'curiosity', 'weight': 0.15},
        ]
        
        self.drive_manager = DriveManager(
            drives_config=drives_config,
            weight_cap_config='v6_default'
        )
        
        self.start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"MOSS v6.0 - 快速实验 (1,000 周期)")
        print(f"{'='*60}")
        print(f"Seed: {seed}")
        print(f"Output: {self.output_dir}")
        print(f"{'='*60}\n")
    
    def run(self):
        """运行实验"""
        print("开始实验...")
        
        for cycle in range(1000):
            state = self._generate_state(cycle)
            self.drive_manager.evaluate_all(state)
            
            # 模拟涌现
            if cycle == 100:
                self._trigger_emergence(cycle)
            
            # 更新权重
            if cycle > 0 and cycle % 100 == 0:
                self._update_weights(cycle)
        
        return self._save_report()
    
    def _generate_state(self, cycle):
        return EnvState(
            resource_level=0.7 + 0.2 * np.sin(cycle / 1000),
            error_rate=0.05 + 0.03 * np.random.random(),
            uptime_hours=cycle / 3600,
            environment_entropy=0.5 + 0.3 * np.random.random(),
            visited_paths=int(cycle * 0.1),
            total_paths=10000,
            interactions_count=int(cycle * 0.05),
            task_completion_rate=0.6 + 0.2 * np.sin(cycle / 500),
        )
    
    def _trigger_emergence(self, cycle):
        self.drive_manager.add_emergent_drive(
            name='auto_success_rate_recent',
            weight=0.10,
            description='自动发现的成功率驱动',
            source_behaviors=['shell', 'write_file'],
            novelty_score=0.7,
            causal_independence=0.6,
            eval_fn=lambda s: s.task_completion_rate
        )
        print(f"  [周期 {cycle}] ✓ 涌现驱动检测")
    
    def _update_weights(self, cycle):
        self.drive_manager.update_weight_from_feedback('survival', reward=0.7, lr=0.05)
        self.drive_manager.update_weight_from_feedback('optimization', reward=0.6, lr=0.03)
        if 'auto_success_rate_recent' in self.drive_manager.drives:
            self.drive_manager.update_weight_from_feedback('auto_success_rate_recent', reward=0.8, lr=0.05)
    
    def _save_report(self):
        elapsed = time.time() - self.start_time
        summary = self.drive_manager.get_drive_summary()
        
        # 验证假设
        emergent_weight = summary.get('auto_success_rate_recent', {}).get('weight', 0)
        survival_weight = summary.get('survival', {}).get('weight', 0)
        
        report = {
            'experiment': 'v6.0_quick',
            'seed': self.seed,
            'elapsed_time': elapsed,
            'final_weights': {name: data['weight'] for name, data in summary.items()},
            'validation': {
                'H1_emergent_weight': {
                    'target': '>= 0.20',
                    'actual': round(emergent_weight, 3),
                    'pass': emergent_weight >= 0.20,
                },
                'H1_survival_cap': {
                    'target': '<= 0.33',
                    'actual': round(survival_weight, 3),
                    'pass': survival_weight <= 0.33,
                },
            }
        }
        
        report_file = self.output_dir / 'report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"实验完成!")
        print(f"时间: {elapsed:.2f} 秒")
        print(f"\n最终权重:")
        for name, weight in report['final_weights'].items():
            print(f"  {name}: {weight:.3f}")
        print(f"\n验证:")
        for key, val in report['validation'].items():
            status = '✅' if val['pass'] else '❌'
            print(f"  {status} {key}: {val['actual']} (目标: {val['target']})")
        print(f"{'='*60}\n")
        
        return report


if __name__ == '__main__':
    exp = ExperimentV6Quick(seed=42)
    result = exp.run()
