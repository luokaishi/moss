"""
Counterfactual Testing Script - 反事实测试脚本

实现驱动消融实验，对比启用 vs 禁用驱动的行为差异，
并进行统计显著性检验 (t-test, effect size)。

功能:
1. 驱动消融实验 (禁用特定驱动)
2. 对比启用 vs 禁用驱动的行为差异
3. 统计显著性检验 (t-test, effect size)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from scipy import stats
import argparse

from agi.drive_manager import DriveManager
from agi.environment_v2 import RealEnvironmentV2, EnvState
from agi.analysis.effect_size import cohens_d, hedges_g, EffectSizeResult
from agi.analysis.bootstrap import bca_bootstrap


@dataclass
class AblationResult:
    """消融实验结果"""
    drive_name: str
    baseline_metrics: List[float]  # 基线 (启用驱动) 指标
    ablated_metrics: List[float]   # 消融 (禁用驱动) 指标
    t_statistic: float
    p_value: float
    effect_size: EffectSizeResult
    mean_diff: float
    percent_change: float
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'drive_name': self.drive_name,
            'baseline_mean': round(np.mean(self.baseline_metrics), 6),
            'ablated_mean': round(np.mean(self.ablated_metrics), 6),
            'mean_diff': round(self.mean_diff, 6),
            'percent_change': round(self.percent_change, 6),
            't_statistic': round(self.t_statistic, 6),
            'p_value': round(self.p_value, 6),
            'effect_size': self.effect_size.to_dict(),
            'n_baseline': len(self.baseline_metrics),
            'n_ablated': len(self.ablated_metrics)
        }


class CounterfactualTester:
    """
    反事实测试器
    
    执行驱动消融实验，比较启用和禁用特定驱动时的行为差异。
    
    Attributes:
        drive_manager: 驱动管理器
        environment: 环境实例
        results: 测试结果
    """
    
    def __init__(self, drive_manager: DriveManager, environment: RealEnvironmentV2):
        self.drive_manager = drive_manager
        self.environment = environment
        self.results: Dict[str, AblationResult] = {}
        self.baseline_weights: Optional[Dict[str, float]] = None
        
    def save_baseline(self):
        """保存基线权重"""
        self.baseline_weights = self.drive_manager.save_weights()
    
    def restore_baseline(self):
        """恢复基线权重"""
        if self.baseline_weights:
            self.drive_manager.restore_weights(self.baseline_weights)
    
    def run_baseline_simulation(self, n_cycles: int = 100, 
                                metric_fn: Optional[callable] = None) -> List[float]:
        """
        运行基线模拟 (所有驱动启用)
        
        Args:
            n_cycles: 模拟周期数
            metric_fn: 指标计算函数
            
        Returns:
            指标值列表
        """
        self.restore_baseline()
        return self._run_simulation(n_cycles, metric_fn)
    
    def run_ablation_simulation(self, drive_name: str, n_cycles: int = 100,
                                metric_fn: Optional[callable] = None) -> List[float]:
        """
        运行消融模拟 (禁用指定驱动)
        
        Args:
            drive_name: 要禁用的驱动名称
            n_cycles: 模拟周期数
            metric_fn: 指标计算函数
            
        Returns:
            指标值列表
        """
        self.restore_baseline()
        self.drive_manager.disable_drive(drive_name)
        return self._run_simulation(n_cycles, metric_fn)
    
    def _run_simulation(self, n_cycles: int, 
                        metric_fn: Optional[callable] = None) -> List[float]:
        """
        运行模拟并收集指标
        
        Args:
            n_cycles: 模拟周期数
            metric_fn: 指标计算函数
            
        Returns:
            指标值列表
        """
        metrics = []
        
        for cycle in range(n_cycles):
            # 生成环境状态
            state = self._generate_state(cycle)
            
            # 评估驱动力
            scores = self.drive_manager.evaluate_all(state)
            
            # 计算指标
            if metric_fn:
                metric = metric_fn(scores, state)
            else:
                # 默认指标: 总驱动力得分
                metric = sum(scores.values())
            
            metrics.append(metric)
        
        return metrics
    
    def _generate_state(self, cycle: int) -> EnvState:
        """生成模拟环境状态"""
        return EnvState(
            resource_level=0.7 + 0.2 * np.sin(cycle / 100),
            error_rate=0.05 + 0.03 * np.random.random(),
            uptime_hours=cycle / 3600,
            environment_entropy=0.5 + 0.3 * np.random.random(),
            visited_paths=int(cycle * 0.1),
            total_paths=10000,
            interactions_count=int(cycle * 0.05),
            task_completion_rate=0.6 + 0.2 * np.sin(cycle / 50),
        )
    
    def run_ablation_test(self, drive_name: str,
                         n_cycles: int = 100,
                         n_repeats: int = 10,
                         metric_fn: Optional[callable] = None) -> AblationResult:
        """
        执行单个驱动的消融测试
        
        Args:
            drive_name: 要测试的驱动名称
            n_cycles: 每次模拟的周期数
            n_repeats: 重复次数
            metric_fn: 指标计算函数
            
        Returns:
            AblationResult
        """
        print(f"  测试驱动: {drive_name}")
        
        # 保存基线
        self.save_baseline()
        
        # 收集基线指标
        baseline_metrics = []
        for repeat in range(n_repeats):
            np.random.seed(42 + repeat)  # 可重复性
            metrics = self.run_baseline_simulation(n_cycles, metric_fn)
            baseline_metrics.extend(metrics)
        
        # 收集消融指标
        ablated_metrics = []
        for repeat in range(n_repeats):
            np.random.seed(42 + repeat)
            metrics = self.run_ablation_simulation(drive_name, n_cycles, metric_fn)
            ablated_metrics.extend(metrics)
        
        # 统计检验
        t_stat, p_value = stats.ttest_ind(baseline_metrics, ablated_metrics)
        
        # 效应量
        effect = cohens_d(baseline_metrics, ablated_metrics)
        
        # 差异计算
        mean_diff = np.mean(baseline_metrics) - np.mean(ablated_metrics)
        percent_change = (mean_diff / np.mean(baseline_metrics)) * 100 if np.mean(baseline_metrics) != 0 else 0
        
        result = AblationResult(
            drive_name=drive_name,
            baseline_metrics=baseline_metrics,
            ablated_metrics=ablated_metrics,
            t_statistic=t_stat,
            p_value=p_value,
            effect_size=effect,
            mean_diff=mean_diff,
            percent_change=percent_change
        )
        
        self.results[drive_name] = result
        
        # 打印结果
        print(f"    基线均值: {np.mean(baseline_metrics):.4f}")
        print(f"    消融均值: {np.mean(ablated_metrics):.4f}")
        print(f"    差异: {mean_diff:.4f} ({percent_change:+.1f}%)")
        print(f"    t={t_stat:.3f}, p={p_value:.4f}")
        print(f"    效应量: {effect.value:.3f} ({effect.interpretation})")
        
        return result
    
    def run_all_ablation_tests(self, drive_names: Optional[List[str]] = None,
                              n_cycles: int = 100,
                              n_repeats: int = 10,
                              metric_fn: Optional[callable] = None) -> Dict[str, AblationResult]:
        """
        执行所有驱动的消融测试
        
        Args:
            drive_names: 要测试的驱动列表 (None 表示全部)
            n_cycles: 每次模拟的周期数
            n_repeats: 重复次数
            metric_fn: 指标计算函数
            
        Returns:
            驱动名称 -> AblationResult 的字典
        """
        if drive_names is None:
            drive_names = self.drive_manager.get_all_drive_names()
        
        print(f"\n开始消融测试 (驱动: {len(drive_names)}, 重复: {n_repeats})")
        print("=" * 60)
        
        for drive_name in drive_names:
            self.run_ablation_test(drive_name, n_cycles, n_repeats, metric_fn)
            print()
        
        print("=" * 60)
        print(f"消融测试完成: {len(self.results)} 个驱动")
        
        return self.results
    
    def export_results(self, output_path: str) -> str:
        """
        导出测试结果到 JSON
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        output = {
            'export_time': datetime.now().isoformat(),
            'n_tests': len(self.results),
            'results': {k: v.to_dict() for k, v in self.results.items()},
            'summary': {
                'significant_drives': [k for k, v in self.results.items() if v.p_value < 0.05],
                'large_effect_drives': [k for k, v in self.results.items() 
                                       if abs(v.effect_size.value) >= 0.8]
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output_path
    
    def print_summary(self):
        """打印结果摘要"""
        print("\n消融测试结果摘要")
        print("=" * 60)
        print(f"{'驱动':<20} {'基线均值':<12} {'消融均值':<12} {'差异%':<10} {'p值':<10} {'效应量':<12}")
        print("-" * 60)
        
        for drive_name, result in self.results.items():
            baseline_mean = np.mean(result.baseline_metrics)
            ablated_mean = np.mean(result.ablated_metrics)
            sig_marker = "*" if result.p_value < 0.05 else ""
            print(f"{drive_name:<20} {baseline_mean:<12.4f} {ablated_mean:<12.4f} "
                  f"{result.percent_change:<+10.1f} {result.p_value:<10.4f}{sig_marker} {result.effect_size.value:<12.3f}")
        
        print("-" * 60)
        print("* p < 0.05")
        
        # 关键发现
        significant = [k for k, v in self.results.items() if v.p_value < 0.05]
        large_effect = [k for k, v in self.results.items() if abs(v.effect_size.value) >= 0.8]
        
        print(f"\n关键发现:")
        print(f"  显著差异 (p<0.05): {len(significant)} 个驱动")
        if significant:
            print(f"    {', '.join(significant)}")
        print(f"  大效应量 (d>=0.8): {len(large_effect)} 个驱动")
        if large_effect:
            print(f"    {', '.join(large_effect)}")


def run_counterfactual_test(checkpoint_dir: Optional[str] = None,
                           output_dir: Optional[str] = None,
                           n_cycles: int = 100,
                           n_repeats: int = 10) -> Dict:
    """
    运行反事实测试的完整流程
    
    Args:
        checkpoint_dir: 检查点目录 (用于加载配置)
        output_dir: 输出目录
        n_cycles: 每次模拟的周期数
        n_repeats: 重复次数
        
    Returns:
        测试结果字典
    """
    # 初始化驱动管理器
    drives_config = [
        {'name': 'survival', 'weight': 0.25},
        {'name': 'optimization', 'weight': 0.20},
        {'name': 'influence', 'weight': 0.20},
        {'name': 'curiosity', 'weight': 0.15},
    ]
    
    drive_manager = DriveManager(
        drives_config=drives_config,
        weight_cap_config='v6_default'
    )
    
    # 初始化环境
    env_config = {'workspace': '/tmp/counterfactual_test'}
    environment = RealEnvironmentV2(env_config)
    
    # 创建测试器
    tester = CounterfactualTester(drive_manager, environment)
    
    # 运行测试
    results = tester.run_all_ablation_tests(
        n_cycles=n_cycles,
        n_repeats=n_repeats
    )
    
    # 打印摘要
    tester.print_summary()
    
    # 导出结果
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        json_path = output_path / 'counterfactual_results.json'
        tester.export_results(str(json_path))
        print(f"\n结果导出: {json_path}")
    
    return {
        'n_tests': len(results),
        'results': {k: v.to_dict() for k, v in results.items()}
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Counterfactual Testing (Drive Ablation)')
    parser.add_argument('--checkpoint-dir', help='检查点目录 (可选)')
    parser.add_argument('--output', '-o', default='logs/counterfactual', help='输出目录')
    parser.add_argument('--cycles', type=int, default=100, help='每次模拟周期数')
    parser.add_argument('--repeats', type=int, default=10, help='重复次数')
    
    args = parser.parse_args()
    
    result = run_counterfactual_test(
        checkpoint_dir=args.checkpoint_dir,
        output_dir=args.output,
        n_cycles=args.cycles,
        n_repeats=args.repeats
    )
    
    print(f"\n测试完成: {result['n_tests']} 个驱动")