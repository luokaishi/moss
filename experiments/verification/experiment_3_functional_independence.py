#!/usr/bin/env python3
"""
MVES Drive Functional Independence Test
实验 3: 功能独立性测试

验证移除四目标驱动后效率驱动仍存在
判定标准：移除四目标后活性 > 0.5
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime


class FunctionalIndependenceTest:
    """功能独立性测试器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test': 'functional_independence',
            'experimental_group': {},
            'control_group': {},
            'conclusion': None
        }
    
    def simulate_base_drives_removal(self, drive_data):
        """模拟移除四目标驱动"""
        # 实验组：移除四目标驱动
        experimental = {
            'survival': np.zeros(len(drive_data['efficiency'])),
            'curiosity': np.zeros(len(drive_data['efficiency'])),
            'influence': np.zeros(len(drive_data['efficiency'])),
            'optimization': np.zeros(len(drive_data['efficiency'])),
            'efficiency': np.array(drive_data['efficiency'])
        }
        
        # 模拟移除后的影响：效率驱动活性下降 20%
        experimental['efficiency'] = experimental['efficiency'] * 0.8
        
        # 对照组：保留四目标驱动
        control = {
            'survival': np.array(drive_data['survival']),
            'curiosity': np.array(drive_data['curiosity']),
            'influence': np.array(drive_data['influence']),
            'optimization': np.array(drive_data['optimization']),
            'efficiency': np.array(drive_data['efficiency'])
        }
        
        return experimental, control
    
    def compute_drive_activity(self, drive_values):
        """计算驱动活性"""
        # 活性定义为平均值和方差的组合
        mean_activity = np.mean(drive_values)
        variance_activity = np.var(drive_values)
        
        # 综合活性 (加权平均)
        activity = mean_activity * 0.7 + variance_activity * 0.3
        
        return float(activity)
    
    def assess_independence(self, experimental, control):
        """评估功能独立性"""
        # 计算实验组效率驱动活性
        experimental_activity = self.compute_drive_activity(experimental['efficiency'])
        
        # 计算对照组效率驱动活性
        control_activity = self.compute_drive_activity(control['efficiency'])
        
        # 计算活性保持率
        activity_retention = experimental_activity / max(control_activity, 0.001)
        
        # 判定：移除四目标后活性 > 0.5
        passed = experimental_activity > 0.5
        
        assessment = {
            'experimental_activity': float(experimental_activity),
            'control_activity': float(control_activity),
            'activity_retention': float(activity_retention),
            'threshold': 0.5,
            'passed': bool(passed),
            'interpretation': '功能独立支持' if passed else '依赖四目标',
            'evidence_strength': '强' if experimental_activity > 0.7 else '中等' if experimental_activity > 0.5 else '弱'
        }
        
        self.results['experimental_group'] = {
            'activity': float(experimental_activity),
            'description': '移除四目标驱动'
        }
        self.results['control_group'] = {
            'activity': float(control_activity),
            'description': '保留四目标驱动'
        }
        self.results['conclusion'] = assessment
        
        return assessment
    
    def save_results(self, output_dir: str = 'experiments/results/verification'):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'functional_independence_test_{timestamp}.json'
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath


def main():
    print("=" * 60)
    print("实验 3: 功能独立性测试")
    print("=" * 60)
    
    tester = FunctionalIndependenceTest()
    
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
    
    # 效率驱动 (60 周期后涌现)
    drive_data['efficiency'][:60] = np.random.randn(60) * 0.05
    drive_data['efficiency'][60:] = np.random.randn(n_samples-60) * 0.15 + 0.35
    
    print(f"   数据周期：{n_samples} 周期")
    
    # 模拟移除四目标驱动
    print("\n2. 模拟移除四目标驱动...")
    experimental, control = tester.simulate_base_drives_removal(drive_data)
    print(f"   实验组：移除四目标驱动")
    print(f"   对照组：保留四目标驱动")
    
    # 评估功能独立性
    print("\n3. 功能独立性评估...")
    assessment = tester.assess_independence(experimental, control)
    print(f"   实验组活性：{assessment['experimental_activity']:.3f}")
    print(f"   对照组活性：{assessment['control_activity']:.3f}")
    print(f"   活性保持率：{assessment['activity_retention']:.1%}")
    print(f"   阈值：> {assessment['threshold']}")
    print(f"   判定：{assessment['interpretation']}")
    print(f"   证据强度：{assessment['evidence_strength']}")
    
    # 保存结果
    filepath = tester.save_results()
    print(f"\n💾 结果已保存：{filepath}")
    
    print("\n" + "=" * 60)
    if assessment['passed']:
        print("✅ 实验 3 通过：效率驱动功能独立性支持!")
    else:
        print("⚠️ 实验 3 待验证：效率驱动可能依赖四目标")
    print("=" * 60)
    
    return assessment['passed']


if __name__ == '__main__':
    main()
