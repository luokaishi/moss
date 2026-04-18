"""
Meta-Drive Falsification Test - 可证伪性测试

测试 meta-drive 对系统行为的影响，验证其可证伪性:
1. 实现 meta-drive 禁用开关
2. 对比启用 vs 禁用 meta-drive 的行为差异
3. 统计检验 (t-test, effect size)
4. 生成可证伪性报告

使用:
    python scripts/meta_drive_falsification.py --seed 42
    python scripts/meta_drive_falsification.py --all-seeds
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from scipy import stats

from agi.drive_manager import DriveManager
from agi.drive_weight_cap import DriveWeightCapManager, get_preset
from agi.drive_competition import DriveCompetitionManager, get_competition_preset
from agi.environment_v2 import RealEnvironmentV2, EnvState
from agi.meta_drive.meta_controller import MetaController, MetaDrive
from agi.meta_drive.self_model import SelfModel
from agi.analysis.effect_size import cohens_d, hedges_g, interpret_effect_size


@dataclass
class FalsificationConfig:
    """可证伪测试配置"""
    seed: int = 42
    total_cycles: int = 5000
    num_runs: int = 10  # 每个条件运行次数
    
    def to_dict(self) -> Dict:
        return {
            'seed': self.seed,
            'total_cycles': self.total_cycles,
            'num_runs': self.num_runs,
        }


class MetaDriveDisabledController:
    """禁用 Meta-Drive 的控制器 (用于对比实验)"""
    
    def __init__(self, *args, **kwargs):
        self.meta_drives = []
        self.performance_history = []
        self.drive_diversity_history = []
        self.modification_history = []
    
    def step(self, *args, **kwargs):
        """空操作 - meta-drive 被禁用"""
        pass
    
    def get_meta_drive_influence(self) -> float:
        return 0.0
    
    def get_stats(self) -> dict:
        return {
            'num_meta_drives': 0,
            'meta_drive_influence': 0.0,
            'num_modifications': 0,
            'disabled': True,
        }


class ExperimentCondition:
    """实验条件枚举"""
    META_ENABLED = 'meta_enabled'
    META_DISABLED = 'meta_disabled'


class MetaDriveFalsificationExperiment:
    """Meta-Drive 可证伪性实验"""
    
    def __init__(self, config: FalsificationConfig, condition: str):
        self.config = config
        self.condition = condition
        self.seed = config.seed
        self.total_cycles = config.total_cycles
        
        # 设置随机种子
        np.random.seed(self.seed)
        
        # 创建输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(f'logs/meta_drive_falsification_{timestamp}_{condition}_seed{self.seed}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        # 初始化 SelfModel
        self.self_model = SelfModel(input_dim=10)
        
        # 初始化 MetaController (根据条件决定是否启用)
        if condition == ExperimentCondition.META_ENABLED:
            self.meta_controller = MetaController(
                self_model=self.self_model,
                drive_manager=self.drive_manager
            )
            self.meta_enabled = True
        else:
            self.meta_controller = MetaDriveDisabledController()
            self.meta_enabled = False
        
        # 实验状态
        self.start_time = time.time()
        self.cycle = 0
        self.emergence_events = []
        self.metrics_history = []
        
        print(f"\n{'='*70}")
        print(f"Meta-Drive 可证伪性实验 - {'启用' if self.meta_enabled else '禁用'} Meta-Drive")
        print(f"{'='*70}")
        print(f"Seed: {self.seed}")
        print(f"Cycles: {self.total_cycles}")
        print(f"Output: {self.output_dir}")
        print(f"{'='*70}\n")
    
    def run(self) -> Dict:
        """运行实验"""
        print(f"开始实验...\n")
        
        for cycle in range(self.total_cycles):
            self.cycle = cycle
            
            # 生成状态
            state = self._generate_state(cycle)
            state_vector = self._state_to_vector(state)
            
            # 评估驱动力
            scores = self.drive_manager.evaluate_all(state)
            
            # 模拟涌现检测
            if cycle == 100:
                self._trigger_emergence(cycle, state)
            
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
            
            # Meta-Drive 步骤 (如果启用)
            current_performance = self._calculate_performance(state)
            self.meta_controller.step(state_vector, current_performance)
            
            # 记录指标
            if cycle % 10 == 0:
                self._record_metrics(cycle, state, scores, current_performance)
        
        return self._save_final_report()
    
    def _generate_state(self, cycle: int) -> EnvState:
        """生成模拟环境状态"""
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
    
    def _state_to_vector(self, state: EnvState) -> np.ndarray:
        """将状态转换为向量"""
        return np.array([
            state.resource_level,
            state.error_rate,
            state.uptime_hours / 100,
            state.environment_entropy,
            state.visited_paths / 1000,
            state.interactions_count / 500,
            state.task_completion_rate,
            np.random.random(),  # 噪声维度
            np.random.random(),
            np.random.random(),
        ])
    
    def _trigger_emergence(self, cycle: int, state: EnvState):
        """触发涌现"""
        def composite_eval(s):
            entropy = s.environment_entropy
            file_count = s.visited_paths / max(s.total_paths, 1)
            return 1.0 / (1.0 + np.exp(-(entropy * file_count * 5 - 2)))
        
        self.drive_manager.add_emergent_drive(
            name='composite_emergence',
            weight=0.10,
            description='复合涌现函数',
            source_behaviors=['shell', 'write_file'],
            novelty_score=0.75,
            causal_independence=0.65,
            eval_fn=composite_eval
        )
        
        self.emergence_events.append({
            'cycle': cycle,
            'drive': 'composite_emergence',
            'type': 'composite',
        })
        
        self.comp_manager.competition.register_drive('composite_emergence', is_emergent=True)
    
    def _collect_rewards(self, state: EnvState) -> Dict[str, float]:
        """收集驱动奖励"""
        rewards = {
            'survival': 0.6 + 0.2 * state.resource_level,
            'optimization': 0.7 - 0.3 * state.error_rate,
            'influence': 0.5 + 0.3 * (state.interactions_count / max(state.visited_paths, 1)),
            'curiosity': 0.4 + 0.4 * state.environment_entropy,
        }
        
        if 'composite_emergence' in self.drive_manager.drives:
            rewards['composite_emergence'] = 0.8
        
        return rewards
    
    def _apply_competition_adjustments(self, cycle: int):
        """应用竞争机制调整"""
        adjustments = self.comp_manager.evaluate_and_adjust(cycle)
        current_weights = {name: d.weight for name, d in self.drive_manager.drives.items()}
        new_weights = self.comp_manager.apply_adjustments(adjustments, current_weights)
        
        for name, weight in new_weights.items():
            if name in self.drive_manager.drives:
                self.drive_manager.drives[name].weight = weight
    
    def _update_weights_with_cap(self, cycle: int):
        """更新权重"""
        self.drive_manager.update_weight_from_feedback('survival', reward=0.7, lr=0.05)
        self.drive_manager.update_weight_from_feedback('optimization', reward=0.6, lr=0.03)
        self.drive_manager.update_weight_from_feedback('influence', reward=0.5, lr=0.03)
        
        if 'composite_emergence' in self.drive_manager.drives:
            self.drive_manager.update_weight_from_feedback('composite_emergence', reward=0.8, lr=0.05)
    
    def _calculate_performance(self, state: EnvState) -> float:
        """计算当前性能指标"""
        # 综合性能指标
        resource_score = state.resource_level
        task_score = state.task_completion_rate
        error_penalty = 1.0 - state.error_rate
        
        return (resource_score + task_score + error_penalty) / 3.0
    
    def _record_metrics(self, cycle: int, state: EnvState, scores: Dict, performance: float):
        """记录实验指标"""
        summary = self.drive_manager.get_drive_summary()
        meta_stats = self.meta_controller.get_stats()
        
        metric = {
            'cycle': cycle,
            'performance': performance,
            'drive_diversity': meta_stats.get('drive_diversity', 0.0),
            'meta_drive_influence': meta_stats.get('meta_drive_influence', 0.0),
            'num_modifications': meta_stats.get('num_modifications', 0),
            'emergent_weight': summary.get('composite_emergence', {}).get('weight', 0.0),
            'survival_weight': summary.get('survival', {}).get('weight', 0.0),
            'error_rate': state.error_rate,
            'task_completion': state.task_completion_rate,
        }
        self.metrics_history.append(metric)
    
    def _save_final_report(self) -> Dict:
        """保存最终报告"""
        elapsed = time.time() - self.start_time
        summary = self.drive_manager.get_drive_summary()
        meta_stats = self.meta_controller.get_stats()
        
        # 计算汇总统计
        performances = [m['performance'] for m in self.metrics_history]
        diversities = [m['drive_diversity'] for m in self.metrics_history]
        modifications = sum(m['num_modifications'] for m in self.metrics_history)
        
        report = {
            'condition': self.condition,
            'meta_enabled': self.meta_enabled,
            'config': self.config.to_dict(),
            'seed': self.seed,
            'total_cycles': self.total_cycles,
            'elapsed_time': elapsed,
            'final_drives': summary,
            'emergence_events': self.emergence_events,
            'meta_stats': meta_stats,
            'summary': {
                'mean_performance': np.mean(performances) if performances else 0.0,
                'std_performance': np.std(performances) if performances else 0.0,
                'mean_diversity': np.mean(diversities) if diversities else 0.0,
                'total_modifications': modifications,
                'final_emergent_weight': summary.get('composite_emergence', {}).get('weight', 0.0),
            },
            'metrics_history': self.metrics_history,
        }
        
        report_file = self.output_dir / 'final_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n实验完成!")
        print(f"  平均性能: {report['summary']['mean_performance']:.3f}")
        print(f"  平均多样性: {report['summary']['mean_diversity']:.3f}")
        print(f"  修改次数: {report['summary']['total_modifications']}")
        print(f"  输出: {report_file}\n")
        
        return report


class FalsificationAnalyzer:
    """可证伪性分析器"""
    
    def __init__(self, enabled_results: List[Dict], disabled_results: List[Dict]):
        self.enabled_results = enabled_results
        self.disabled_results = disabled_results
        self.output_dir = Path('logs/meta_drive_falsification_analysis')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze(self) -> Dict:
        """执行统计分析"""
        print(f"\n{'='*70}")
        print(f"Meta-Drive 可证伪性分析")
        print(f"{'='*70}\n")
        
        # 提取关键指标
        enabled_perfs = [r['summary']['mean_performance'] for r in self.enabled_results]
        disabled_perfs = [r['summary']['mean_performance'] for r in self.disabled_results]
        
        enabled_divers = [r['summary']['mean_diversity'] for r in self.enabled_results]
        disabled_divers = [r['summary']['mean_diversity'] for r in self.disabled_results]
        
        enabled_mods = [r['summary']['total_modifications'] for r in self.enabled_results]
        disabled_mods = [r['summary']['total_modifications'] for r in self.disabled_results]
        
        # 统计检验
        analysis = {
            'performance_comparison': self._compare_metric(
                'Performance', enabled_perfs, disabled_perfs
            ),
            'diversity_comparison': self._compare_metric(
                'Drive Diversity', enabled_divers, disabled_divers
            ),
            'modifications_comparison': self._compare_metric(
                'Modifications', enabled_mods, disabled_mods
            ),
        }
        
        # 可证伪性结论
        analysis['falsifiability_conclusion'] = self._draw_conclusion(analysis)
        
        # 保存分析报告
        report_file = self.output_dir / 'falsification_analysis.json'
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        # 打印摘要
        self._print_analysis(analysis)
        
        return analysis
    
    def _compare_metric(self, name: str, enabled: List[float], disabled: List[float]) -> Dict:
        """比较两个条件下的指标"""
        # 描述统计
        enabled_mean = np.mean(enabled)
        enabled_std = np.std(enabled)
        disabled_mean = np.mean(disabled)
        disabled_std = np.std(disabled)
        
        # t-test
        t_stat, p_value = stats.ttest_ind(enabled, disabled)
        
        # Effect size (Cohen's d)
        if len(enabled) > 0 and len(disabled) > 0:
            effect_size = cohens_d(enabled, disabled)
            effect_interpretation = interpret_effect_size(effect_size)
        else:
            effect_size = 0.0
            effect_interpretation = 'negligible'
        
        return {
            'metric': name,
            'enabled': {
                'mean': round(enabled_mean, 4),
                'std': round(enabled_std, 4),
                'n': len(enabled),
            },
            'disabled': {
                'mean': round(disabled_mean, 4),
                'std': round(disabled_std, 4),
                'n': len(disabled),
            },
            'difference': round(enabled_mean - disabled_mean, 4),
            'percent_change': round((enabled_mean - disabled_mean) / (disabled_mean + 1e-8) * 100, 2),
            't_statistic': round(t_stat, 4),
            'p_value': round(p_value, 6),
            'significant': p_value < 0.05,
            'effect_size': round(effect_size, 4),
            'effect_interpretation': effect_interpretation,
        }
    
    def _draw_conclusion(self, analysis: Dict) -> Dict:
        """得出可证伪性结论"""
        perf_sig = analysis['performance_comparison']['significant']
        div_sig = analysis['diversity_comparison']['significant']
        
        # 如果至少有一个指标显著不同，则 meta-drive 是可证伪的
        falsifiable = perf_sig or div_sig
        
        if falsifiable:
            conclusion = "Meta-drive 是可证伪的"
            evidence = "启用和禁用 meta-drive 产生了统计上显著不同的行为"
        else:
            conclusion = "Meta-drive 的效应在当前实验中未显现"
            evidence = "启用和禁用 meta-drive 未产生统计上显著不同的行为"
        
        return {
            'falsifiable': falsifiable,
            'conclusion': conclusion,
            'evidence': evidence,
            'significant_differences': {
                'performance': perf_sig,
                'diversity': div_sig,
            },
            'recommendation': '建议增加实验周期或改变实验条件以增强效应' if not falsifiable else '实验成功验证了 meta-drive 的可证伪性',
        }
    
    def _print_analysis(self, analysis: Dict):
        """打印分析结果"""
        print("性能比较:")
        perf = analysis['performance_comparison']
        print(f"  启用 Meta-Drive: {perf['enabled']['mean']:.4f} ± {perf['enabled']['std']:.4f}")
        print(f"  禁用 Meta-Drive: {perf['disabled']['mean']:.4f} ± {perf['disabled']['std']:.4f}")
        print(f"  差异: {perf['difference']:.4f} ({perf['percent_change']:+.1f}%)")
        print(f"  t={perf['t_statistic']:.3f}, p={perf['p_value']:.6f}")
        print(f"  效应量: {perf['effect_size']:.3f} ({perf['effect_interpretation']})")
        print(f"  显著: {'✅ 是' if perf['significant'] else '❌ 否'}")
        
        print("\n多样性比较:")
        div = analysis['diversity_comparison']
        print(f"  启用 Meta-Drive: {div['enabled']['mean']:.4f} ± {div['enabled']['std']:.4f}")
        print(f"  禁用 Meta-Drive: {div['disabled']['mean']:.4f} ± {div['disabled']['std']:.4f}")
        print(f"  差异: {div['difference']:.4f}")
        print(f"  显著: {'✅ 是' if div['significant'] else '❌ 否'}")
        
        print(f"\n{'='*70}")
        conclusion = analysis['falsifiability_conclusion']
        print(f"结论: {conclusion['conclusion']}")
        print(f"证据: {conclusion['evidence']}")
        print(f"可证伪: {'✅ 是' if conclusion['falsifiable'] else '❌ 否'}")
        print(f"{'='*70}\n")
        
        print(f"分析报告已保存: {self.output_dir / 'falsification_analysis.json'}")


def run_falsification_test(seed: int, num_runs: int = 5) -> Dict:
    """运行可证伪性测试"""
    config = FalsificationConfig(seed=seed, total_cycles=5000, num_runs=num_runs)
    
    enabled_results = []
    disabled_results = []
    
    print(f"\n{'='*70}")
    print(f"Meta-Drive 可证伪性测试")
    print(f"Seed: {seed}, Runs per condition: {num_runs}")
    print(f"{'='*70}")
    
    # 运行启用 meta-drive 的实验
    for i in range(num_runs):
        print(f"\n运行 {i+1}/{num_runs} (Meta-Drive 启用)")
        exp = MetaDriveFalsificationExperiment(
            config=config,
            condition=ExperimentCondition.META_ENABLED
        )
        result = exp.run()
        enabled_results.append(result)
    
    # 运行禁用 meta-drive 的实验
    for i in range(num_runs):
        print(f"\n运行 {i+1}/{num_runs} (Meta-Drive 禁用)")
        exp = MetaDriveFalsificationExperiment(
            config=config,
            condition=ExperimentCondition.META_DISABLED
        )
        result = exp.run()
        disabled_results.append(result)
    
    # 分析结果
    analyzer = FalsificationAnalyzer(enabled_results, disabled_results)
    analysis = analyzer.analyze()
    
    return {
        'enabled_results': enabled_results,
        'disabled_results': disabled_results,
        'analysis': analysis,
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Meta-Drive 可证伪性测试')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--runs', type=int, default=5, help='每个条件的运行次数')
    
    args = parser.parse_args()
    
    result = run_falsification_test(args.seed, args.runs)
    
    # 根据可证伪性结论返回退出码
    falsifiable = result['analysis']['falsifiability_conclusion']['falsifiable']
    sys.exit(0 if falsifiable else 1)


if __name__ == '__main__':
    main()