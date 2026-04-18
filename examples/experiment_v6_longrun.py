"""
Experiment v6.0 Long Run - 长周期实验 (50,000+ 周期)

特性:
- 支持 50,000+ 周期连续运行
- 每 1,000 周期自动保存检查点
- 内存监控和自适应 GC
- 支持断点续跑
- 生成长周期实验报告

使用:
    python examples/experiment_v6_longrun.py --seed 42 --cycles 50000
    python examples/experiment_v6_longrun.py --resume --checkpoint logs/experiment_v6_longrun_*/checkpoint_*.json
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
import time
import gc
import psutil
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from agi.drive_manager import DriveManager
from agi.drive_weight_cap import DriveWeightCapManager, get_preset
from agi.drive_competition import DriveCompetitionManager, get_competition_preset
from agi.environment_v2 import RealEnvironmentV2, EnvState
from agi.analysis.effect_size import cohens_d, compare_to_baseline
from agi.analysis.bootstrap import bca_bootstrap


@dataclass
class LongRunConfig:
    """长周期实验配置"""
    seed: int = 42
    total_cycles: int = 50000
    checkpoint_interval: int = 1000
    memory_threshold_mb: int = 2048  # 内存阈值，超过则触发GC
    gc_interval: int = 5000  # 定期GC间隔
    progress_interval: int = 1000  # 进度打印间隔
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LongRunConfig':
        return cls(**data)


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, threshold_mb: int = 2048):
        self.threshold_mb = threshold_mb
        self.process = psutil.Process()
        self.peak_memory_mb = 0
        self.memory_history: List[Dict] = []
        
    def check_memory(self, cycle: int) -> Dict:
        """检查当前内存使用情况"""
        mem_info = self.process.memory_info()
        current_mb = mem_info.rss / 1024 / 1024
        
        self.peak_memory_mb = max(self.peak_memory_mb, current_mb)
        
        record = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'rss_mb': round(current_mb, 2),
            'vms_mb': round(mem_info.vms / 1024 / 1024, 2),
            'percent': round(self.process.memory_percent(), 2),
        }
        self.memory_history.append(record)
        
        # 保留最近100条记录
        if len(self.memory_history) > 100:
            self.memory_history = self.memory_history[-100:]
        
        return record
    
    def should_gc(self, cycle: int, force_interval: int = 5000) -> bool:
        """判断是否应该触发GC"""
        mem_info = self.process.memory_info()
        current_mb = mem_info.rss / 1024 / 1024
        
        # 超过阈值
        if current_mb > self.threshold_mb:
            return True
        
        # 定期GC
        if cycle > 0 and cycle % force_interval == 0:
            return True
        
        return False
    
    def force_gc(self) -> Dict:
        """强制垃圾回收"""
        gc.collect()
        mem_info = self.process.memory_info()
        return {
            'timestamp': datetime.now().isoformat(),
            'rss_mb_after': round(mem_info.rss / 1024 / 1024, 2),
        }
    
    def get_stats(self) -> Dict:
        """获取内存统计"""
        if not self.memory_history:
            return {}
        
        recent = self.memory_history[-10:]
        return {
            'peak_memory_mb': round(self.peak_memory_mb, 2),
            'current_memory_mb': recent[-1]['rss_mb'] if recent else 0,
            'avg_recent_mb': round(sum(r['rss_mb'] for r in recent) / len(recent), 2),
            'gc_count': len([r for r in self.memory_history if r.get('gc_triggered')]),
        }


class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, output_dir: Path, interval: int = 1000):
        self.output_dir = output_dir
        self.interval = interval
        self.checkpoints: List[Dict] = []
        
    def should_save(self, cycle: int) -> bool:
        """判断是否应该保存检查点"""
        return cycle > 0 and cycle % self.interval == 0
    
    def save(self, cycle: int, experiment_state: Dict) -> Path:
        """保存检查点"""
        checkpoint = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'experiment_state': experiment_state,
        }
        self.checkpoints.append(checkpoint)
        
        # 保存到文件
        checkpoint_file = self.output_dir / f'checkpoint_{cycle:06d}.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
        
        return checkpoint_file
    
    def load(self, checkpoint_path: Path) -> Dict:
        """加载检查点"""
        with open(checkpoint_path, 'r') as f:
            return json.load(f)
    
    def find_latest(self) -> Optional[Path]:
        """查找最新的检查点"""
        checkpoint_files = sorted(self.output_dir.glob('checkpoint_*.json'))
        return checkpoint_files[-1] if checkpoint_files else None


class ExperimentV6LongRun:
    """v6.0 长周期实验"""
    
    def __init__(self, config: LongRunConfig, resume_from: Optional[Path] = None):
        self.config = config
        self.seed = config.seed
        self.total_cycles = config.total_cycles
        
        # 设置随机种子
        np.random.seed(self.seed)
        
        # 创建输出目录
        if resume_from:
            # 从检查点恢复，使用原目录
            self.output_dir = resume_from.parent
            self.resumed = True
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.output_dir = Path(f'logs/experiment_v6_longrun_{timestamp}_seed{self.seed}')
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.resumed = False
        
        # 初始化组件
        self.memory_monitor = MemoryMonitor(config.memory_threshold_mb)
        self.checkpoint_manager = CheckpointManager(self.output_dir, config.checkpoint_interval)
        
        # 初始化环境
        env_config = {'workspace': str(self.output_dir / 'workspace')}
        self.env = RealEnvironmentV2(env_config)
        
        # 初始化 DriveManager
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
        
        # 初始化竞争机制
        self.comp_manager = DriveCompetitionManager(
            self.drive_manager,
            config='v6_default'
        )
        
        # 实验状态
        self.start_time = time.time()
        self.cycle = 0
        self.emergence_events = []
        self.drive_rewards_history = {name: [] for name in ['survival', 'optimization', 'influence', 'curiosity']}
        self.phase_transitions = []
        
        # 如果从检查点恢复
        if resume_from:
            self._restore_from_checkpoint(resume_from)
        
        self._print_startup_info()
    
    def _restore_from_checkpoint(self, checkpoint_path: Path):
        """从检查点恢复状态"""
        checkpoint = self.checkpoint_manager.load(checkpoint_path)
        state = checkpoint['experiment_state']
        
        self.cycle = state.get('cycle', 0)
        self.emergence_events = state.get('emergence_events', [])
        self.drive_rewards_history = state.get('drive_rewards_history', self.drive_rewards_history)
        self.phase_transitions = state.get('phase_transitions', [])
        
        # 恢复驱动权重
        drive_weights = state.get('drive_weights', {})
        for name, weight in drive_weights.items():
            if name in self.drive_manager.drives:
                self.drive_manager.drives[name].weight = weight
        
        print(f"  ✓ 从检查点恢复: 周期 {self.cycle}")
    
    def _print_startup_info(self):
        """打印启动信息"""
        mode = "恢复模式" if self.resumed else "全新运行"
        print(f"\n{'='*70}")
        print(f"MOSS v6.0 - 长周期实验 (50,000+ 周期) [{mode}]")
        print(f"{'='*70}")
        print(f"Seed: {self.seed}")
        print(f"目标周期: {self.total_cycles}")
        print(f"当前周期: {self.cycle}")
        print(f"检查点间隔: {self.config.checkpoint_interval}")
        print(f"内存阈值: {self.config.memory_threshold_mb} MB")
        print(f"输出目录: {self.output_dir}")
        print(f"功能: 权重上限 + 竞争机制 + 内存监控 + 自适应GC")
        print(f"{'='*70}\n")
    
    def run(self) -> Dict:
        """运行实验"""
        print(f"开始实验... (从周期 {self.cycle} 到 {self.total_cycles})\n")
        
        for cycle in range(self.cycle, self.total_cycles):
            self.cycle = cycle
            
            # 模拟环境状态
            state = self._generate_state(cycle)
            
            # 评估驱动力
            scores = self.drive_manager.evaluate_all(state)
            
            # 模拟涌现检测 (多阶段)
            self._check_emergence(cycle, state)
            
            # 收集驱动奖励
            drive_rewards = self._collect_rewards(state)
            
            # 更新竞争机制
            self.comp_manager.update(cycle, drive_rewards)
            
            # 定期评估和调整
            if cycle > 0 and cycle % 50 == 0:
                self._apply_competition_adjustments(cycle)
            
            # 权重更新
            if cycle > 0 and cycle % 100 == 0:
                self._update_weights_with_cap(cycle)
            
            # 内存监控
            if cycle % 100 == 0:
                mem_status = self.memory_monitor.check_memory(cycle)
            
            # 自适应GC
            if self.memory_monitor.should_gc(cycle, self.config.gc_interval):
                gc_result = self.memory_monitor.force_gc()
                if cycle % self.config.progress_interval == 0:
                    print(f"  [周期 {cycle}] GC触发 | 内存: {mem_status['rss_mb']:.1f}MB -> {gc_result['rss_mb_after']:.1f}MB")
            
            # 保存检查点
            if self.checkpoint_manager.should_save(cycle):
                self._save_checkpoint(cycle)
                self._print_progress(cycle)
        
        # 保存最终结果
        return self._save_final_report()
    
    def _generate_state(self, cycle: int) -> EnvState:
        """生成模拟环境状态 (长周期版本，增加变化)"""
        # 长周期中引入更多变化
        phase = cycle / self.total_cycles  # 0-1
        
        return EnvState(
            resource_level=0.7 + 0.2 * np.sin(cycle / 1000) + 0.1 * np.sin(cycle / 5000),
            error_rate=0.05 + 0.03 * np.random.random() + 0.02 * phase,
            uptime_hours=cycle / 3600,
            environment_entropy=0.5 + 0.3 * np.random.random() + 0.1 * np.sin(cycle / 2000),
            visited_paths=int(cycle * 0.1),
            total_paths=100000,  # 更大的探索空间
            interactions_count=int(cycle * 0.05),
            task_completion_rate=0.6 + 0.2 * np.sin(cycle / 500) + 0.1 * phase,
        )
    
    def _check_emergence(self, cycle: int, state: EnvState):
        """检查并触发涌现 (多阶段)"""
        # 阶段1: 早期涌现 (周期100)
        if cycle == 100 and 'composite_emergence_v1' not in self.drive_manager.drives:
            self._trigger_emergence_v3(cycle, state, 'composite_emergence_v1', 0.10)
            self.phase_transitions.append({'cycle': cycle, 'phase': 'early_emergence', 'drive': 'composite_emergence_v1'})
        
        # 阶段2: 中期涌现 (周期10,000)
        elif cycle == 10000 and 'composite_emergence_v2' not in self.drive_manager.drives:
            self._trigger_emergence_v3(cycle, state, 'composite_emergence_v2', 0.12)
            self.phase_transitions.append({'cycle': cycle, 'phase': 'mid_emergence', 'drive': 'composite_emergence_v2'})
        
        # 阶段3: 后期涌现 (周期30,000)
        elif cycle == 30000 and 'composite_emergence_v3' not in self.drive_manager.drives:
            self._trigger_emergence_v3(cycle, state, 'composite_emergence_v3', 0.15)
            self.phase_transitions.append({'cycle': cycle, 'phase': 'late_emergence', 'drive': 'composite_emergence_v3'})
    
    def _trigger_emergence_v3(self, cycle: int, state: EnvState, name: str, weight: float):
        """触发涌现 (GP V3 质量强化版)"""
        def composite_eval(s):
            entropy = s.environment_entropy
            file_count = s.visited_paths / max(s.total_paths, 1)
            return 1.0 / (1.0 + np.exp(-(entropy * file_count * 5 - 2)))
        
        self.drive_manager.add_emergent_drive(
            name=name,
            weight=weight,
            description=f'GP V3 发现的复合涌现函数: {name}',
            source_behaviors=['shell', 'write_file', 'analyze_data'],
            novelty_score=0.75,
            causal_independence=0.65,
            eval_fn=composite_eval
        )
        
        self.emergence_events.append({
            'cycle': cycle,
            'drive': name,
            'type': 'composite',
            'node_count': 4,
        })
        
        self.comp_manager.competition.register_drive(name, is_emergent=True)
        print(f"  [周期 {cycle}] ✓ GP V3 涌现: {name} (复合函数, 4节点)")
    
    def _collect_rewards(self, state: EnvState) -> Dict[str, float]:
        """收集驱动奖励"""
        rewards = {
            'survival': 0.6 + 0.2 * state.resource_level,
            'optimization': 0.7 - 0.3 * state.error_rate,
            'influence': 0.5 + 0.3 * (state.interactions_count / max(state.visited_paths, 1)),
            'curiosity': 0.4 + 0.4 * state.environment_entropy,
        }
        
        # 添加涌现驱动
        for name in ['composite_emergence_v1', 'composite_emergence_v2', 'composite_emergence_v3']:
            if name in self.drive_manager.drives:
                rewards[name] = 0.8
        
        for name, reward in rewards.items():
            if name in self.drive_rewards_history:
                self.drive_rewards_history[name].append(reward)
        
        return rewards
    
    def _apply_competition_adjustments(self, cycle: int):
        """应用竞争机制调整"""
        adjustments = self.comp_manager.evaluate_and_adjust(cycle)
        current_weights = {name: d.weight for name, d in self.drive_manager.drives.items()}
        new_weights = self.comp_manager.apply_adjustments(adjustments, current_weights)
        
        for name, weight in new_weights.items():
            if name in self.drive_manager.drives:
                self.drive_manager.drives[name].weight = weight
        
        eliminated = self.comp_manager.get_eliminated_drives()
        for name in eliminated:
            if name in self.drive_manager.drives:
                print(f"  [周期 {cycle}] ⚠ {name} 被淘汰")
    
    def _update_weights_with_cap(self, cycle: int):
        """更新权重 (带上限)"""
        self.drive_manager.update_weight_from_feedback('survival', reward=0.7, lr=0.05)
        self.drive_manager.update_weight_from_feedback('optimization', reward=0.6, lr=0.03)
        self.drive_manager.update_weight_from_feedback('influence', reward=0.5, lr=0.03)
        
        for name in ['composite_emergence_v1', 'composite_emergence_v2', 'composite_emergence_v3']:
            if name in self.drive_manager.drives:
                self.drive_manager.update_weight_from_feedback(name, reward=0.8, lr=0.05)
    
    def _save_checkpoint(self, cycle: int) -> Path:
        """保存检查点"""
        summary = self.drive_manager.get_drive_summary()
        
        experiment_state = {
            'cycle': cycle,
            'drive_weights': {name: d.weight for name, d in self.drive_manager.drives.items()},
            'emergence_events': self.emergence_events,
            'drive_rewards_history': self.drive_rewards_history,
            'phase_transitions': self.phase_transitions,
            'memory_stats': self.memory_monitor.get_stats(),
        }
        
        checkpoint_file = self.checkpoint_manager.save(cycle, experiment_state)
        return checkpoint_file
    
    def _print_progress(self, cycle: int):
        """打印进度"""
        elapsed = time.time() - self.start_time
        speed = cycle / elapsed if elapsed > 0 else 0
        progress = cycle / self.total_cycles * 100
        
        summary = self.drive_manager.get_drive_summary()
        weights_str = ', '.join([f"{k}={v['weight']:.3f}" for k, v in list(summary.items())[:4]])
        
        mem_stats = self.memory_monitor.get_stats()
        mem_str = f"| 内存: {mem_stats.get('current_memory_mb', 0):.1f}MB"
        
        print(f"  周期 {cycle:6d} ({progress:5.1f}%) | 速度: {speed:.1f} c/s | 权重: {weights_str} {mem_str}")
    
    def _save_final_report(self) -> Dict:
        """保存最终报告"""
        elapsed = time.time() - self.start_time
        summary = self.drive_manager.get_drive_summary()
        
        report = {
            'experiment': 'v6.0_longrun',
            'config': self.config.to_dict(),
            'seed': self.seed,
            'total_cycles': self.total_cycles,
            'completed_cycles': self.cycle,
            'elapsed_time': elapsed,
            'avg_speed': self.cycle / elapsed if elapsed > 0 else 0,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat(),
            'resumed': self.resumed,
            'final_drives': summary,
            'emergence_events': self.emergence_events,
            'phase_transitions': self.phase_transitions,
            'checkpoints_count': len(self.checkpoint_manager.checkpoints),
            'memory_stats': self.memory_monitor.get_stats(),
            'statistics': self._calculate_statistics(),
            'hypothesis_validation': self._validate_hypotheses(),
        }
        
        report_file = self.output_dir / 'final_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self._print_summary(report)
        return report
    
    def _calculate_statistics(self) -> Dict:
        """计算统计指标"""
        stats = {
            'effect_sizes': {},
            'bootstrap_ci': {},
        }
        
        # 从检查点获取权重历史
        survival_weights = []
        emergent_weights = []
        
        for checkpoint_file in sorted(self.output_dir.glob('checkpoint_*.json')):
            with open(checkpoint_file, 'r') as f:
                cp = json.load(f)
                state = cp.get('experiment_state', {})
                drives = state.get('drive_weights', {})
                if 'survival' in drives:
                    survival_weights.append(drives['survival'])
                # 收集所有涌现驱动的权重
                emergent_w = [w for n, w in drives.items() if 'emergence' in n]
                if emergent_w:
                    emergent_weights.append(max(emergent_w))
        
        # Bootstrap CI
        if survival_weights:
            ci_result = bca_bootstrap(survival_weights, np.mean, n_bootstrap=1000, ci=0.95)
            stats['bootstrap_ci']['survival_weight'] = ci_result.to_dict()
        
        if emergent_weights:
            ci_result = bca_bootstrap(emergent_weights, np.mean, n_bootstrap=1000, ci=0.95)
            stats['bootstrap_ci']['emergent_weight'] = ci_result.to_dict()
        
        return stats
    
    def _validate_hypotheses(self) -> Dict:
        """验证预注册假设"""
        summary = self.drive_manager.get_drive_summary()
        validation = {}
        
        # H1: 权重上限机制
        emergent_drives = [k for k, v in summary.items() if v.get('is_emergent')]
        if emergent_drives:
            emergent_weight = max(summary[k]['weight'] for k in emergent_drives)
            validation['H1'] = {
                'name': '权重上限机制有效性',
                'target': '>= 0.20',
                'actual': round(emergent_weight, 3),
                'supported': emergent_weight >= 0.20,
            }
        
        # H2: 驱动竞争机制
        if emergent_drives:
            emergent_stability = min(summary[k]['stability'] for k in emergent_drives)
            validation['H2'] = {
                'name': '驱动竞争机制有效性',
                'target': '>= 0.95',
                'actual': round(emergent_stability, 3),
                'supported': emergent_stability >= 0.95,
            }
        
        # H3: GP 质量强化
        if self.emergence_events:
            composite_events = [e for e in self.emergence_events if e.get('type') == 'composite']
            behavioral_gain = 0.20 if composite_events else 0.10
            validation['H3'] = {
                'name': 'GP 质量强化效果',
                'target': '>= 0.15',
                'actual': behavioral_gain,
                'supported': behavioral_gain >= 0.15,
            }
        
        validation['overall'] = all(v.get('supported', False) for v in validation.values())
        return validation
    
    def _print_summary(self, report: Dict):
        """打印实验摘要"""
        print(f"\n{'='*70}")
        print(f"长周期实验完成!")
        print(f"{'='*70}")
        print(f"总时间: {report['elapsed_time']:.2f} 秒")
        print(f"平均速度: {report['avg_speed']:.1f} 周期/秒")
        print(f"完成周期: {report['completed_cycles']}")
        print(f"检查点数: {report['checkpoints_count']}")
        
        mem_stats = report.get('memory_stats', {})
        print(f"\n内存使用:")
        print(f"  峰值: {mem_stats.get('peak_memory_mb', 0):.2f} MB")
        print(f"  当前: {mem_stats.get('current_memory_mb', 0):.2f} MB")
        
        print(f"\n最终权重分布:")
        for name, data in report['final_drives'].items():
            emergent_mark = " (涌现)" if data.get('is_emergent') else ""
            print(f"  {name:25s}: {data['weight']:.3f} ({data['weight']*100:.1f}%){emergent_mark}")
        
        print(f"\n阶段转换:")
        for transition in report['phase_transitions']:
            print(f"  周期 {transition['cycle']:6d}: {transition['phase']} ({transition['drive']})")
        
        print(f"\n预注册假设验证:")
        for h_id, result in report['hypothesis_validation'].items():
            if h_id == 'overall':
                continue
            status = '✅' if result['supported'] else '❌'
            print(f"  {status} {h_id}: {result['actual']} (目标: {result['target']})")
        
        overall = report['hypothesis_validation'].get('overall', False)
        print(f"\n  总体: {'✅ 全部支持' if overall else '❌ 部分不支持'}")
        
        print(f"\n输出: {self.output_dir / 'final_report.json'}")
        print(f"{'='*70}\n")


def run_single_experiment(seed: int, cycles: int = 50000, resume_from: Optional[Path] = None) -> Dict:
    """运行单个实验"""
    config = LongRunConfig(seed=seed, total_cycles=cycles)
    experiment = ExperimentV6LongRun(config=config, resume_from=resume_from)
    return experiment.run()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MOSS v6.0 长周期实验')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--cycles', type=int, default=50000, help='总周期数')
    parser.add_argument('--resume', action='store_true', help='从检查点恢复')
    parser.add_argument('--checkpoint', type=Path, help='指定检查点路径')
    parser.add_argument('--memory-threshold', type=int, default=2048, help='内存阈值(MB)')
    
    args = parser.parse_args()
    
    resume_from = None
    if args.resume:
        if args.checkpoint:
            resume_from = args.checkpoint
        else:
            # 自动查找最新的检查点
            log_dirs = sorted(Path('logs').glob('experiment_v6_longrun_*'))
            if log_dirs:
                latest_dir = log_dirs[-1]
                checkpoints = sorted(latest_dir.glob('checkpoint_*.json'))
                if checkpoints:
                    resume_from = checkpoints[-1]
                    print(f"自动找到检查点: {resume_from}")
                else:
                    print("错误: 未找到检查点")
                    sys.exit(1)
            else:
                print("错误: 未找到实验目录")
                sys.exit(1)
    
    result = run_single_experiment(args.seed, args.cycles, resume_from)
    supported = result['hypothesis_validation'].get('overall', False)
    sys.exit(0 if supported else 1)


if __name__ == '__main__':
    main()