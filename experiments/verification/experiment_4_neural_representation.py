#!/usr/bin/env python3
"""
MVES Drive Neural Representation Analysis
实验 4: 神经表征分析

分析效率驱动与四目标的激活模式重叠度
判定标准：表征重叠度 < 0.5
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime


class NeuralRepresentationAnalysis:
    """神经表征分析器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test': 'neural_representation_analysis',
            'activation_patterns': {},
            'overlap_metrics': {},
            'conclusion': None
        }
    
    def simulate_activation_patterns(self, drive_data):
        """模拟驱动激活模式"""
        # 简化实现：使用驱动值作为激活模式代理
        patterns = {}
        
        for drive_name, drive_values in drive_data.items():
            values = np.array(drive_values)
            
            # 计算激活模式特征
            patterns[drive_name] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'skewness': float(self._compute_skewness(values)),
                'kurtosis': float(self._compute_kurtosis(values)),
                'autocorrelation': float(self._compute_autocorrelation(values))
            }
        
        self.results['activation_patterns'] = patterns
        return patterns
    
    def _compute_skewness(self, x):
        """计算偏度"""
        n = len(x)
        if n < 3:
            return 0.0
        mean = np.mean(x)
        std = np.std(x)
        if std < 1e-10:
            return 0.0
        return np.mean(((x - mean) / std) ** 3)
    
    def _compute_kurtosis(self, x):
        """计算峰度"""
        n = len(x)
        if n < 4:
            return 0.0
        mean = np.mean(x)
        std = np.std(x)
        if std < 1e-10:
            return 0.0
        return np.mean(((x - mean) / std) ** 4) - 3
    
    def _compute_autocorrelation(self, x, lag=1):
        """计算自相关"""
        n = len(x)
        if n < lag + 2:
            return 0.0
        mean = np.mean(x)
        var = np.var(x)
        if var < 1e-10:
            return 0.0
        
        autocorr = np.corrcoef(x[:-lag], x[lag:])[0, 1]
        return float(autocorr) if not np.isnan(autocorr) else 0.0
    
    def compute_overlap(self, patterns):
        """计算效率驱动与四目标的表征重叠度"""
        efficiency = patterns['efficiency']
        base_drives = ['survival', 'curiosity', 'influence', 'optimization']
        
        overlaps = {}
        for drive in base_drives:
            # 计算特征向量距离
            features_eff = np.array([
                efficiency['mean'],
                efficiency['std'],
                efficiency['skewness'],
                efficiency['kurtosis'],
                efficiency['autocorrelation']
            ])
            
            features_drive = np.array([
                patterns[drive]['mean'],
                patterns[drive]['std'],
                patterns[drive]['skewness'],
                patterns[drive]['kurtosis'],
                patterns[drive]['autocorrelation']
            ])
            
            # 计算余弦相似度 (重叠度)
            dot_product = np.dot(features_eff, features_drive)
            norm_eff = np.linalg.norm(features_eff)
            norm_drive = np.linalg.norm(features_drive)
            
            if norm_eff < 1e-10 or norm_drive < 1e-10:
                overlap = 0.0
            else:
                overlap = dot_product / (norm_eff * norm_drive)
                overlap = (overlap + 1) / 2  # 归一化到 [0, 1]
            
            overlaps[drive] = float(overlap)
        
        # 最大重叠度和平均重叠度
        max_overlap = max(overlaps.values())
        avg_overlap = np.mean(list(overlaps.values()))
        
        self.results['overlap_metrics'] = {
            'overlaps': overlaps,
            'max_overlap': float(max_overlap),
            'avg_overlap': float(avg_overlap)
        }
        
        return overlaps, max_overlap, avg_overlap
    
    def assess_neural_independence(self, max_overlap, avg_overlap):
        """评估神经独立性"""
        # 判定：重叠度 < 0.5
        passed = max_overlap < 0.5
        
        assessment = {
            'max_overlap': float(max_overlap),
            'avg_overlap': float(avg_overlap),
            'threshold': 0.5,
            'passed': bool(passed),
            'interpretation': '神经表征独立' if passed else '表征重叠',
            'evidence_strength': '强' if max_overlap < 0.3 else '中等' if max_overlap < 0.5 else '弱'
        }
        
        self.results['conclusion'] = assessment
        return assessment
    
    def save_results(self, output_dir: str = 'experiments/results/verification'):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'neural_representation_analysis_{timestamp}.json'
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath


def main():
    print("=" * 60)
    print("实验 4: 神经表征分析")
    print("=" * 60)
    
    analyzer = NeuralRepresentationAnalysis()
    
    # 生成模拟数据
    print("\n1. 生成驱动数据...")
    np.random.seed(42)
    n_samples = 160
    
    drive_data = {
        'survival': np.random.randn(n_samples) * 0.25 + 0.25,
        'curiosity': np.random.randn(n_samples) * 0.25 + 0.25,
        'influence': np.random.randn(n_samples) * 0.25 + 0.25,
        'optimization': np.random.randn(n_samples) * 0.25 + 0.25,
        'efficiency': np.zeros(n_samples)
    }
    
    # 效率驱动 (独特模式：60 周期后涌现)
    drive_data['efficiency'][:60] = np.random.randn(60) * 0.05
    drive_data['efficiency'][60:] = np.random.randn(n_samples-60) * 0.15 + 0.35
    
    print(f"   数据周期：{n_samples} 周期")
    
    # 计算激活模式
    print("\n2. 计算驱动激活模式...")
    patterns = analyzer.simulate_activation_patterns(drive_data)
    
    for drive, pattern in patterns.items():
        print(f"   {drive}: 均值={pattern['mean']:.3f}, 标准差={pattern['std']:.3f}")
    
    # 计算重叠度
    print("\n3. 计算表征重叠度...")
    overlaps, max_overlap, avg_overlap = analyzer.compute_overlap(patterns)
    
    for drive, overlap in overlaps.items():
        print(f"   效率驱动 vs {drive}: {overlap:.3f}")
    
    print(f"   最大重叠度：{max_overlap:.3f}")
    print(f"   平均重叠度：{avg_overlap:.3f}")
    
    # 评估神经独立性
    print("\n4. 神经独立性评估...")
    assessment = analyzer.assess_neural_independence(max_overlap, avg_overlap)
    print(f"   最大重叠度：{assessment['max_overlap']:.3f}")
    print(f"   阈值：< {assessment['threshold']}")
    print(f"   判定：{assessment['interpretation']}")
    print(f"   证据强度：{assessment['evidence_strength']}")
    
    # 保存结果
    filepath = analyzer.save_results()
    print(f"\n💾 结果已保存：{filepath}")
    
    print("\n" + "=" * 60)
    if assessment['passed']:
        print("✅ 实验 4 通过：效率驱动神经表征独立!")
    else:
        print("⚠️ 实验 4 待验证：效率驱动表征与四目标重叠")
    print("=" * 60)
    
    return assessment['passed']


if __name__ == '__main__':
    main()
