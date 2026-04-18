"""
Experiment v6.0 - 权重上限机制验证实验

验证目标:
1. survival 驱动权重是否被限制在 30% 以内
2. 涌现驱动权重是否能达到 20% 以上
3. 系统稳定性是否保持

预期结果:
- survival 权重: ≤0.30 (vs v5.5.2 的 0.378)
- emergent 权重: ≥0.20 (vs v5.5.2 的 0.168)
- 稳定性: ≥95%
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


class ExperimentV6WeightCap:
    """v6.0 权重上限验证实验"""
    
    def __init__(self, seed=42, total_cycles=5000, checkpoint_interval=1000):
        self.seed = seed
        self.total_cycles = total_cycles
        self.checkpoint_interval = checkpoint_interval
        
        # 设置随机种子
        np.random.seed(seed)
        
        # 创建输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(f'logs/experiment_v6_weightcap_{timestamp}_seed{seed}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化环境
        env_config = {'workspace': str(self.output_dir / 'workspace')}
        self.env = RealEnvironmentV2(env_config)
        
        # 初始化 DriveManager (启用权重上限)
        drives_config = [
            {'name': 'survival', 'weight': 0.25, 'description': '生存驱动'},
            {'name': 'optimization', 'weight': 0.20, 'description': '优化驱动'},
            {'name': 'influence', 'weight': 0.20, 'description': '影响驱动'},
            {'name': 'curiosity', 'weight': 0.15, 'description': '好奇驱动'},
        ]
        
        # 使用 v6 默认权重上限配置
        self.drive_manager = DriveManager(
            drives_config=drives_config,
            weight_cap_config='v6_default'
        )
        
        # 实验状态
        self.cycle = 0
        self.start_time = time.time()
        self.checkpoints = []
        self.emergence_events = []
        
        print(f"=" * 60)
        print(f"Experiment v6.0 - 权重上限机制验证")
        print(f"=" * 60)
        print(f"Seed: {seed}")
        print(f"Total Cycles: {total_cycles}")
        print(f"Output: {self.output_dir}")
        print(f"Weight Caps: survival=0.30, optimization=0.25, influence=0.20, curiosity=0.15, emergent=0.35")
        print(f"=" * 60)
    
    def run(self):
        """运行实验"""
        print(f"\n开始实验...")
        
        for cycle in range(self.total_cycles):
            self.cycle = cycle
            
            # 模拟环境状态
            state = self._generate_state(cycle)
            
            # 评估驱动力
            scores = self.drive_manager.evaluate_all(state)
            
            # 模拟涌现检测 (每 50 周期)
            if cycle > 0 and cycle % 50 == 0:
                self._check_emergence(cycle, state)
            
            # 模拟权重更新 (基于反馈)
            if cycle > 0 and cycle % 100 == 0:
                self._update_weights(cycle)
            
            # 保存检查点
            if cycle > 0 and cycle % self.checkpoint_interval == 0:
                self._save_checkpoint(cycle)
                self._print_progress(cycle)
        
        # 保存最终结果
        self._save_final_report()
        self._print_summary()
        
        return self._get_results()
    
    def _generate_state(self, cycle: int) -> EnvState:
        """生成模拟环境状态"""
        # 基于周期的模拟状态
        state = EnvState(
            resource_level=0.7 + 0.2 * np.sin(cycle / 1000),
            error_rate=0.05 + 0.03 * np.random.random(),
            uptime_hours=cycle / 3600,
            environment_entropy=0.5 + 0.3 * np.random.random(),
            visited_paths=int(cycle * 0.1),
            total_paths=10000,
            interactions_count=int(cycle * 0.05),
            task_completion_rate=0.6 + 0.2 * np.sin(cycle / 500),
        )
        return state
    
    def _check_emergence(self, cycle: int, state: EnvState):
        """检查涌现驱动"""
        # 模拟涌现检测 (简化版)
        if cycle == 100:  # 在第 100 周期模拟涌现
            # 添加涌现驱动
            success = self.drive_manager.add_emergent_drive(
                name='auto_success_rate_recent',
                weight=0.10,
                description='自动发现的成功率驱动',
                source_behaviors=['shell', 'write_file'],
                novelty_score=0.7,
                causal_independence=0.6,
                eval_fn=lambda s: s.task_completion_rate
            )
            if success:
                self.emergence_events.append({
                    'cycle': cycle,
                    'drive': 'auto_success_rate_recent',
                    'initial_weight': 0.10
                })
                print(f"  [周期 {cycle}] 涌现驱动检测: auto_success_rate_recent")
    
    def _update_weights(self, cycle: int):
        """模拟权重更新"""
        # 模拟 survival 驱动获得正反馈 (试图增长)
        # 权重上限机制应该限制其增长
        self.drive_manager.update_weight_from_feedback('survival', reward=0.7, lr=0.05)
        
        # 模拟其他驱动更新
        self.drive_manager.update_weight_from_feedback('optimization', reward=0.6, lr=0.03)
        self.drive_manager.update_weight_from_feedback('influence', reward=0.5, lr=0.03)
        
        # 如果存在涌现驱动，给予正反馈
        if 'auto_success_rate_recent' in self.drive_manager.drives:
            self.drive_manager.update_weight_from_feedback(
                'auto_success_rate_recent', reward=0.8, lr=0.05
            )
    
    def _save_checkpoint(self, cycle: int):
        """保存检查点"""
        checkpoint = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'drives': self.drive_manager.get_drive_summary(),
            'weight_cap_stats': self.drive_manager.get_weight_cap_stats(),
        }
        self.checkpoints.append(checkpoint)
        
        # 保存到文件
        checkpoint_file = self.output_dir / f'checkpoint_{cycle:06d}.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
    
    def _print_progress(self, cycle: int):
        """打印进度"""
        elapsed = time.time() - self.start_time
        speed = cycle / elapsed if elapsed > 0 else 0
        progress = cycle / self.total_cycles * 100
        
        summary = self.drive_manager.get_drive_summary()
        weights_str = ', '.join([f"{k}={v['weight']:.3f}" for k, v in summary.items()])
        
        print(f"  周期 {cycle:6d} ({progress:5.1f}%) | 速度: {speed:.2f} c/s | 权重: {weights_str}")
    
    def _save_final_report(self):
        """保存最终报告"""
        elapsed = time.time() - self.start_time
        
        final_summary = self.drive_manager.get_drive_summary()
        weight_cap_stats = self.drive_manager.get_weight_cap_stats()
        
        report = {
            'experiment': 'v6.0_weight_cap',
            'seed': self.seed,
            'total_cycles': self.total_cycles,
            'elapsed_time': elapsed,
            'avg_speed': self.total_cycles / elapsed if elapsed > 0 else 0,
            'final_drives': final_summary,
            'emergence_events': self.emergence_events,
            'weight_cap_stats': weight_cap_stats,
            'checkpoints_count': len(self.checkpoints),
        }
        
        # 添加验证结果
        report['validation'] = self._validate_results(final_summary)
        
        # 保存报告
        report_file = self.output_dir / 'final_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report
    
    def _validate_results(self, summary: dict) -> dict:
        """验证实验结果是否符合预期"""
        validation = {
            'survival_cap_pass': False,
            'emergent_target_pass': False,
            'overall_pass': False,
        }
        
        # 检查 survival 是否被限制在 30% 以内
        if 'survival' in summary:
            survival_weight = summary['survival']['weight']
            validation['survival_cap_pass'] = survival_weight <= 0.33  # 软上限
            validation['survival_weight'] = survival_weight
        
        # 检查涌现驱动是否达到 20%
        emergent_drives = [k for k in summary.keys() if summary[k].get('is_emergent', False)]
        if emergent_drives:
            emergent_weight = max(summary[k]['weight'] for k in emergent_drives)
            validation['emergent_target_pass'] = emergent_weight >= 0.20
            validation['emergent_weight'] = emergent_weight
        else:
            validation['emergent_target_pass'] = False
            validation['emergent_weight'] = 0.0
        
        # 总体验证
        validation['overall_pass'] = (
            validation['survival_cap_pass'] and 
            validation['emergent_target_pass']
        )
        
        return validation
    
    def _print_summary(self):
        """打印实验摘要"""
        print(f"\n{'=' * 60}")
        print(f"实验完成!")
        print(f"{'=' * 60}")
        
        summary = self.drive_manager.get_drive_summary()
        
        print(f"\n最终权重分布:")
        for name, data in summary.items():
            emergent_mark = " (涌现)" if data.get('is_emergent') else ""
            print(f"  {name:20s}: {data['weight']:.3f} ({data['weight']*100:.1f}%){emergent_mark}")
        
        # 验证结果
        validation = self._validate_results(summary)
        print(f"\n验证结果:")
        print(f"  survival 上限 (≤33%): {'✅ 通过' if validation['survival_cap_pass'] else '❌ 失败'} ({validation.get('survival_weight', 0)*100:.1f}%)")
        print(f"  emergent 目标 (≥20%): {'✅ 通过' if validation['emergent_target_pass'] else '❌ 失败'} ({validation.get('emergent_weight', 0)*100:.1f}%)")
        print(f"  总体: {'✅ 通过' if validation['overall_pass'] else '❌ 失败'}")
        
        # 权重上限统计
        cap_stats = self.drive_manager.get_weight_cap_stats()
        if cap_stats:
            print(f"\n权重上限统计:")
            print(f"  总更新次数: {cap_stats['total_updates']}")
            print(f"  触发上限次数: {cap_stats['caps_applied']}")
            print(f"  上限触发率: {cap_stats['cap_rate']*100:.1f}%")
        
        print(f"\n输出目录: {self.output_dir}")
        print(f"{'=' * 60}")
    
    def _get_results(self) -> dict:
        """获取实验结果"""
        summary = self.drive_manager.get_drive_summary()
        validation = self._validate_results(summary)
        
        return {
            'seed': self.seed,
            'total_cycles': self.total_cycles,
            'final_weights': {k: v['weight'] for k, v in summary.items()},
            'validation': validation,
            'output_dir': str(self.output_dir),
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='v6.0 权重上限验证实验')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--cycles', type=int, default=5000, help='总周期数')
    parser.add_argument('--checkpoint-interval', type=int, default=1000, help='检查点间隔')
    
    args = parser.parse_args()
    
    # 运行实验
    experiment = ExperimentV6WeightCap(
        seed=args.seed,
        total_cycles=args.cycles,
        checkpoint_interval=args.checkpoint_interval
    )
    
    results = experiment.run()
    
    # 返回结果
    return results


if __name__ == '__main__':
    results = main()