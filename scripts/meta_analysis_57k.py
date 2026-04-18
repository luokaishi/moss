#!/usr/bin/env python3
"""
MOSS v6.0 - 57K 数据 Meta-Analysis 脚本

对 experiment_v5_20260416_223622_longrun_opt/ 实验数据进行全面分析：
1. 加载所有检查点数据
2. 计算跨时间窗口的效应量 (Cohen's d)
3. 生成权重时序图数据 (CSV格式)
4. 分析涌现检测的稳定性
5. 生成内存使用趋势分析
6. 输出 JSON 格式的 meta-analysis 报告

Usage:
    python scripts/meta_analysis_57k.py --checkpoint-dir logs/experiment_v5_20260416_223622_longrun_opt/ --output logs/meta_analysis_57k/
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import numpy as np
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
from scipy import stats

from agi.analysis.effect_size import cohens_d, hedges_g, EffectSizeResult
from agi.analysis.bootstrap import bca_bootstrap, percentile_bootstrap


class MetaAnalyzer57K:
    """57K 实验数据的 Meta-Analysis 分析器"""
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoints: List[Dict] = []
        self.drive_names: List[str] = []
        self.weights_matrix: Optional[np.ndarray] = None
        self.cycles: List[int] = []
        self.timestamps: List[str] = []
        self.memory_trend: List[float] = []
        
        # 分析结果
        self.results: Dict[str, Any] = {}
        
    def load_all_checkpoints(self) -> int:
        """加载所有检查点文件"""
        checkpoint_files = sorted(
            self.checkpoint_dir.glob('checkpoint_*.json'),
            key=lambda p: int(p.stem.split('_')[1])
        )
        
        print(f"发现 {len(checkpoint_files)} 个检查点文件")
        
        for cp_file in checkpoint_files:
            try:
                with open(cp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.checkpoints.append(data)
                    self.cycles.append(data.get('cycle', 0))
                    self.timestamps.append(data.get('timestamp', ''))
                    self.memory_trend.append(data.get('memory_mb', 0))
            except Exception as e:
                print(f"警告: 无法加载 {cp_file}: {e}")
        
        if not self.checkpoints:
            raise ValueError("未找到有效的检查点文件")
        
        # 提取驱动名称
        if 'drives' in self.checkpoints[0]:
            self.drive_names = list(self.checkpoints[0]['drives'].keys())
        
        print(f"成功加载 {len(self.checkpoints)} 个检查点")
        print(f"驱动列表: {self.drive_names}")
        print(f"周期范围: {min(self.cycles)} - {max(self.cycles)}")
        
        return len(self.checkpoints)
    
    def build_weights_matrix(self):
        """构建权重时序矩阵"""
        n_checkpoints = len(self.checkpoints)
        n_drives = len(self.drive_names)
        
        self.weights_matrix = np.zeros((n_checkpoints, n_drives))
        
        for i, cp in enumerate(self.checkpoints):
            drives = cp.get('drives', {})
            for j, drive_name in enumerate(self.drive_names):
                weight = drives.get(drive_name, {}).get('weight', 0)
                self.weights_matrix[i, j] = weight
        
        print(f"权重矩阵形状: {self.weights_matrix.shape}")
    
    def analyze_data_overview(self) -> Dict:
        """数据概览分析"""
        total_cycles = max(self.cycles) - min(self.cycles)
        n_checkpoints = len(self.checkpoints)
        
        # 计算时间跨度
        if self.timestamps:
            try:
                start_time = datetime.fromisoformat(self.timestamps[0])
                end_time = datetime.fromisoformat(self.timestamps[-1])
                time_span_hours = (end_time - start_time).total_seconds() / 3600
            except:
                time_span_hours = None
        else:
            time_span_hours = None
        
        overview = {
            'total_cycles': total_cycles,
            'checkpoint_count': n_checkpoints,
            'time_span_hours': round(time_span_hours, 2) if time_span_hours else None,
            'drive_count': len(self.drive_names),
            'drive_names': self.drive_names,
            'cycle_range': [min(self.cycles), max(self.cycles)],
            'cycles_per_checkpoint': total_cycles / n_checkpoints if n_checkpoints > 0 else 0,
        }
        
        self.results['data_overview'] = overview
        return overview
    
    def analyze_weight_evolution(self) -> Dict:
        """权重演化分析"""
        if self.weights_matrix is None:
            self.build_weights_matrix()
        
        weight_analysis = {}
        
        for i, drive_name in enumerate(self.drive_names):
            weights = self.weights_matrix[:, i]
            
            initial = float(weights[0])
            final = float(weights[-1])
            change = final - initial
            change_pct = (change / initial * 100) if initial != 0 else 0
            
            # 统计量
            mean_w = float(np.mean(weights))
            std_w = float(np.std(weights))
            min_w = float(np.min(weights))
            max_w = float(np.max(weights))
            
            # 趋势方向
            trend = "increasing" if change > 0.01 else ("decreasing" if change < -0.01 else "stable")
            
            # 变异系数
            cv = std_w / mean_w if mean_w != 0 else 0
            
            weight_analysis[drive_name] = {
                'initial': round(initial, 6),
                'final': round(final, 6),
                'change': round(change, 6),
                'change_percent': round(change_pct, 2),
                'trend': trend,
                'mean': round(mean_w, 6),
                'std': round(std_w, 6),
                'min': round(min_w, 6),
                'max': round(max_w, 6),
                'coefficient_of_variation': round(cv, 4),
            }
        
        self.results['weight_evolution'] = weight_analysis
        return weight_analysis
    
    def calculate_effect_sizes(self) -> Dict:
        """计算跨时间窗口的效应量"""
        if self.weights_matrix is None:
            self.build_weights_matrix()
        
        effect_sizes = {}
        n_checkpoints = len(self.checkpoints)
        
        # 将数据分为早期、中期、晚期三个阶段
        third = n_checkpoints // 3
        early_indices = list(range(0, third))
        mid_indices = list(range(third, 2 * third))
        late_indices = list(range(2 * third, n_checkpoints))
        
        comparisons = [
            ('early_vs_late', early_indices, late_indices),
            ('early_vs_mid', early_indices, mid_indices),
            ('mid_vs_late', mid_indices, late_indices),
        ]
        
        for comp_name, idx1, idx2 in comparisons:
            effect_sizes[comp_name] = {}
            
            for i, drive_name in enumerate(self.drive_names):
                group1 = self.weights_matrix[idx1, i].tolist()
                group2 = self.weights_matrix[idx2, i].tolist()
                
                # Cohen's d
                d_result = cohens_d(group1, group2)
                
                # Hedge's g (小样本校正)
                g_result = hedges_g(group1, group2)
                
                effect_sizes[comp_name][drive_name] = {
                    'cohens_d': d_result.to_dict(),
                    'hedges_g': g_result.to_dict(),
                    'group1_mean': round(np.mean(group1), 6),
                    'group2_mean': round(np.mean(group2), 6),
                    'group1_n': len(group1),
                    'group2_n': len(group2),
                }
        
        self.results['effect_sizes'] = effect_sizes
        return effect_sizes
    
    def analyze_emergence_stability(self) -> Dict:
        """分析涌现检测的稳定性"""
        emergence_events = []
        drive_emergence = defaultdict(lambda: {'count': 0, 'first_seen': None, 'last_seen': None})
        
        for cp in self.checkpoints:
            cycle = cp.get('cycle', 0)
            emerged = cp.get('emerged_drives', [])
            
            for drive in emerged:
                drive_emergence[drive]['count'] += 1
                if drive_emergence[drive]['first_seen'] is None:
                    drive_emergence[drive]['first_seen'] = cycle
                drive_emergence[drive]['last_seen'] = cycle
            
            # 记录涌现事件
            if cp.get('emergence_event'):
                event = cp['emergence_event']
                emergence_events.append({
                    'cycle': cycle,
                    'drive': event.get('drive_name', 'unknown'),
                    'timestamp': cp.get('timestamp', ''),
                })
        
        # 计算每个涌现驱动的稳定性指标
        total_checkpoints = len(self.checkpoints)
        stability_analysis = {}
        
        for drive, info in drive_emergence.items():
            persistence_rate = info['count'] / total_checkpoints if total_checkpoints > 0 else 0
            duration = info['last_seen'] - info['first_seen'] if info['last_seen'] and info['first_seen'] else 0
            
            stability_analysis[drive] = {
                'detection_count': info['count'],
                'first_seen_cycle': info['first_seen'],
                'last_seen_cycle': info['last_seen'],
                'duration_cycles': duration,
                'persistence_rate': round(persistence_rate, 4),
                'is_stable': persistence_rate > 0.8,  # 80%以上出现认为稳定
            }
        
        emergence_summary = {
            'total_emergence_events': len(emergence_events),
            'emerged_drives_count': len(drive_emergence),
            'emerged_drives': list(drive_emergence.keys()),
            'events': emergence_events,
            'stability_analysis': stability_analysis,
        }
        
        self.results['emergence_stability'] = emergence_summary
        return emergence_summary
    
    def analyze_memory_trend(self) -> Dict:
        """内存使用趋势分析"""
        if not self.memory_trend:
            return {}
        
        memory_data = np.array(self.memory_trend)
        cycles = np.array(self.cycles)
        
        # 基本统计
        mean_mem = float(np.mean(memory_data))
        std_mem = float(np.std(memory_data))
        min_mem = float(np.min(memory_data))
        max_mem = float(np.max(memory_data))
        
        # 线性回归分析趋势
        if len(cycles) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(cycles, memory_data)
        else:
            slope = intercept = r_value = p_value = std_err = 0
        
        # 增长率 (MB per 1000 cycles)
        growth_rate = slope * 1000
        
        # 检测内存泄漏 (基于斜率)
        leak_detected = slope > 0.001  # 每周期超过0.001MB认为有泄漏
        
        memory_analysis = {
            'mean_mb': round(mean_mem, 2),
            'std_mb': round(std_mem, 2),
            'min_mb': round(min_mem, 2),
            'max_mb': round(max_mem, 2),
            'final_mb': round(float(memory_data[-1]), 2),
            'slope_mb_per_cycle': round(slope, 6),
            'growth_rate_mb_per_1k': round(growth_rate, 4),
            'r_squared': round(r_value ** 2, 4),
            'p_value': round(p_value, 6),
            'leak_detected': leak_detected,
            'trend': 'increasing' if slope > 0.01 else ('decreasing' if slope < -0.01 else 'stable'),
        }
        
        self.results['memory_trend'] = memory_analysis
        return memory_analysis
    
    def calculate_bootstrap_cis(self) -> Dict:
        """计算关键指标的 Bootstrap 置信区间"""
        bootstrap_results = {}
        
        if self.weights_matrix is not None:
            for i, drive_name in enumerate(self.drive_names):
                weights = self.weights_matrix[:, i].tolist()
                
                # 均值的 Bootstrap CI
                mean_result = bca_bootstrap(weights, np.mean, n_bootstrap=5000, ci=0.95)
                bootstrap_results[f'{drive_name}_weight_mean'] = mean_result.to_dict()
        
        # 内存使用 CI
        if self.memory_trend:
            mem_result = bca_bootstrap(self.memory_trend, np.mean, n_bootstrap=5000, ci=0.95)
            bootstrap_results['memory_mean'] = mem_result.to_dict()
        
        self.results['bootstrap_cis'] = bootstrap_results
        return bootstrap_results
    
    def generate_weight_timeseries_csv(self, output_dir: Path) -> Path:
        """生成权重时序图数据 (CSV格式)"""
        if self.weights_matrix is None:
            self.build_weights_matrix()
        
        csv_path = output_dir / 'weight_timeseries.csv'
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            # 表头
            header = ['cycle', 'timestamp'] + self.drive_names + ['memory_mb']
            f.write(','.join(header) + '\n')
            
            # 数据行
            for i, cp in enumerate(self.checkpoints):
                cycle = self.cycles[i]
                timestamp = self.timestamps[i]
                memory = self.memory_trend[i] if i < len(self.memory_trend) else 0
                
                weights = self.weights_matrix[i, :].tolist()
                row = [str(cycle), timestamp] + [f'{w:.6f}' for w in weights] + [f'{memory:.2f}']
                f.write(','.join(row) + '\n')
        
        print(f"权重时序数据已保存: {csv_path}")
        return csv_path
    
    def generate_summary_statistics(self) -> Dict:
        """生成统计摘要"""
        summary = {
            'generated_at': datetime.now().isoformat(),
            'data_source': str(self.checkpoint_dir),
        }
        
        # 权重统计摘要
        if self.weights_matrix is not None:
            all_weights = self.weights_matrix.flatten()
            summary['weights_overall'] = {
                'mean': round(float(np.mean(all_weights)), 6),
                'std': round(float(np.std(all_weights)), 6),
                'min': round(float(np.min(all_weights)), 6),
                'max': round(float(np.max(all_weights)), 6),
            }
        
        # 涌现统计
        if 'emergence_stability' in self.results:
            es = self.results['emergence_stability']
            summary['emergence'] = {
                'total_events': es.get('total_emergence_events', 0),
                'unique_drives': es.get('emerged_drives_count', 0),
                'stable_emergences': sum(1 for d in es.get('stability_analysis', {}).values() if d.get('is_stable', False)),
            }
        
        self.results['summary_statistics'] = summary
        return summary
    
    def run_full_analysis(self) -> Dict:
        """运行完整的 Meta-Analysis"""
        print("=" * 60)
        print("MOSS v6.0 - 57K 数据 Meta-Analysis")
        print("=" * 60)
        
        # 1. 加载数据
        print("\n[1/7] 加载检查点数据...")
        self.load_all_checkpoints()
        
        # 2. 数据概览
        print("\n[2/7] 数据概览分析...")
        overview = self.analyze_data_overview()
        print(f"  总周期数: {overview['total_cycles']}")
        print(f"  检查点数量: {overview['checkpoint_count']}")
        print(f"  时间跨度: {overview['time_span_hours']} 小时")
        
        # 3. 权重演化
        print("\n[3/7] 权重演化分析...")
        weight_evolution = self.analyze_weight_evolution()
        for drive, stats in weight_evolution.items():
            print(f"  {drive}: {stats['initial']:.4f} → {stats['final']:.4f} ({stats['change']:+.4f}, {stats['change_percent']:+.1f}%) [{stats['trend']}]")
        
        # 4. 效应量计算
        print("\n[4/7] 计算效应量 (Cohen's d)...")
        effect_sizes = self.calculate_effect_sizes()
        for comp, drives in effect_sizes.items():
            print(f"  {comp}:")
            for drive, es in drives.items():
                d_val = es['cohens_d']['value']
                interp = es['cohens_d']['interpretation']
                print(f"    {drive}: d={d_val:.4f} ({interp})")
        
        # 5. 涌现稳定性
        print("\n[5/7] 分析涌现检测稳定性...")
        emergence = self.analyze_emergence_stability()
        print(f"  总涌现事件: {emergence['total_emergence_events']}")
        print(f"  涌现驱动数: {emergence['emerged_drives_count']}")
        for drive, stability in emergence['stability_analysis'].items():
            print(f"    {drive}: 持久率={stability['persistence_rate']:.2%}, 稳定={stability['is_stable']}")
        
        # 6. 内存趋势
        print("\n[6/7] 内存使用趋势分析...")
        memory = self.analyze_memory_trend()
        print(f"  平均内存: {memory['mean_mb']:.2f} MB")
        print(f"  最终内存: {memory['final_mb']:.2f} MB")
        print(f"  增长率: {memory['growth_rate_mb_per_1k']:.4f} MB/1k cycles")
        print(f"  趋势: {memory['trend']}, 泄漏检测: {memory['leak_detected']}")
        
        # 7. Bootstrap CI
        print("\n[7/7] 计算 Bootstrap 置信区间...")
        bootstrap_cis = self.calculate_bootstrap_cis()
        print(f"  计算了 {len(bootstrap_cis)} 个指标的 CI")
        
        # 生成摘要
        print("\n[8/7] 生成统计摘要...")
        summary = self.generate_summary_statistics()
        
        print("\n" + "=" * 60)
        print("Meta-Analysis 完成!")
        print("=" * 60)
        
        return self.results
    
    def save_results(self, output_dir: Path):
        """保存分析结果"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 JSON 报告 (处理 numpy 类型)
        json_path = output_dir / 'meta_analysis_report.json'
        
        def convert_to_serializable(obj):
            """递归转换 numpy 类型为 Python 原生类型"""
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.bool_,)):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj
        
        serializable_results = convert_to_serializable(self.results)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        print(f"JSON 报告已保存: {json_path}")
        
        # 生成 CSV 时序数据
        csv_path = self.generate_weight_timeseries_csv(output_dir)
        
        return json_path, csv_path


def main():
    parser = argparse.ArgumentParser(description='MOSS v6.0 - 57K 数据 Meta-Analysis')
    parser.add_argument('--checkpoint-dir', type=str, 
                        default='logs/experiment_v5_20260416_223622_longrun_opt/',
                        help='检查点目录路径')
    parser.add_argument('--output', '-o', type=str, default='logs/meta_analysis_57k/',
                        help='输出目录')
    
    args = parser.parse_args()
    
    checkpoint_dir = Path(args.checkpoint_dir)
    output_dir = Path(args.output)
    
    if not checkpoint_dir.exists():
        print(f"错误: 检查点目录不存在: {checkpoint_dir}")
        return 1
    
    # 运行分析
    analyzer = MetaAnalyzer57K(checkpoint_dir)
    analyzer.run_full_analysis()
    analyzer.save_results(output_dir)
    
    print(f"\n所有结果已保存到: {output_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())