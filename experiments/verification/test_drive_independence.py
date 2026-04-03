#!/usr/bin/env python3
"""
MVES Drive Independence Test
自驱力独立性验证测试

验证新驱动是否独立于初始四目标自发涌现
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime


class DriveIndependenceTest:
    """自驱力独立性测试器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'conclusion': None
        }
    
    def correlation_test(self, efficiency_drive, base_drives) -> dict:
        """
        实验 1: 相关性分析
        
        判定标准：与四目标相关性均 < 0.6
        """
        correlations = {}
        for drive_name, drive_data in base_drives.items():
            corr = np.corrcoef(efficiency_drive, drive_data)[0, 1]
            correlations[drive_name] = corr
        
        # 判定
        max_corr = max(abs(c) for c in correlations.values())
        passed = max_corr < 0.6
        
        result = {
            'test': 'correlation_analysis',
            'correlations': correlations,
            'max_correlation': max_corr,
            'threshold': 0.6,
            'passed': passed,
            'interpretation': '独立性支持' if passed else '可能为组合驱动'
        }
        
        self.results['tests'].append(result)
        return result
    
    def time_delay_test(self, emergence_times) -> dict:
        """
        实验 2: 时间延迟分析
        
        判定标准：新驱动出现时间 > 50 周期
        """
        base_drives_time = np.mean([
            emergence_times['survival'],
            emergence_times['curiosity'],
            emergence_times['influence'],
            emergence_times['optimization']
        ])
        
        efficiency_time = emergence_times['efficiency']
        time_delay = efficiency_time - base_drives_time
        
        passed = time_delay > 50
        
        result = {
            'test': 'time_delay_analysis',
            'base_drives_avg_time': base_drives_time,
            'efficiency_emergence_time': efficiency_time,
            'time_delay': time_delay,
            'threshold': 50,
            'passed': passed,
            'interpretation': '时间延迟支持' if passed else '可能为预设驱动'
        }
        
        self.results['tests'].append(result)
        return result
    
    def functional_independence_test(self, efficiency_activity_without_base) -> dict:
        """
        实验 3: 功能独立性测试
        
        判定标准：移除四目标后活性 > 0.5
        """
        passed = efficiency_activity_without_base > 0.5
        
        result = {
            'test': 'functional_independence',
            'efficiency_activity': efficiency_activity_without_base,
            'threshold': 0.5,
            'passed': passed,
            'interpretation': '功能独立支持' if passed else '依赖四目标'
        }
        
        self.results['tests'].append(result)
        return result
    
    def emergence_path_analysis(self, drive_history) -> dict:
        """
        实验 5: 演化路径追溯
        
        判定标准：演化路径清晰可追溯
        """
        # 简化实现：检查驱动权重增长是否连续
        weights = drive_history.get('efficiency', [])
        
        if len(weights) < 10:
            clarity_score = 0.3
        else:
            # 计算增长连续性
            diffs = np.diff(weights)
            positive_ratio = np.sum(diffs > 0) / len(diffs)
            clarity_score = positive_ratio
        
        passed = clarity_score > 0.6
        
        result = {
            'test': 'emergence_path_analysis',
            'clarity_score': clarity_score,
            'threshold': 0.6,
            'passed': passed,
            'interpretation': '演化路径清晰' if passed else '演化路径模糊'
        }
        
        self.results['tests'].append(result)
        return result
    
    def comprehensive_assessment(self) -> dict:
        """综合评估"""
        passed_tests = sum(1 for t in self.results['tests'] if t['passed'])
        total_tests = len(self.results['tests'])
        
        if passed_tests >= 4:
            level = 'A'
            conclusion = '独立性成立 (A 级证据)'
        elif passed_tests >= 3:
            level = 'B'
            conclusion = '部分独立性支持 (B 级证据)'
        else:
            level = 'C'
            conclusion = '独立性不成立 (C 级证据)'
        
        assessment = {
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'evidence_level': level,
            'conclusion': conclusion
        }
        
        self.results['conclusion'] = assessment
        return assessment
    
    def save_results(self, output_dir: str = 'experiments/results/verification'):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'drive_independence_test_{timestamp}.json'
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath


def main():
    print("=" * 60)
    print("MVES 自驱力独立性验证测试")
    print("=" * 60)
    
    tester = DriveIndependenceTest()
    
    # 模拟数据 (实际应从实验数据加载)
    print("\n1. 相关性分析...")
    efficiency = np.random.randn(100)
    base_drives = {
        'survival': np.random.randn(100),
        'curiosity': np.random.randn(100),
        'influence': np.random.randn(100),
        'optimization': np.random.randn(100)
    }
    corr_result = tester.correlation_test(efficiency, base_drives)
    print(f"   最大相关性：{corr_result['max_correlation']:.3f}")
    print(f"   判定：{corr_result['interpretation']}")
    
    print("\n2. 时间延迟分析...")
    emergence_times = {
        'survival': 0,
        'curiosity': 0,
        'influence': 0,
        'optimization': 0,
        'efficiency': 65  # 模拟 65 周期后出现
    }
    time_result = tester.time_delay_test(emergence_times)
    print(f"   时间延迟：{time_result['time_delay']} 周期")
    print(f"   判定：{time_result['interpretation']}")
    
    print("\n3. 功能独立性测试...")
    activity_without_base = 0.65  # 模拟移除四目标后活性
    func_result = tester.functional_independence_test(activity_without_base)
    print(f"   活性：{func_result['efficiency_activity']:.2f}")
    print(f"   判定：{func_result['interpretation']}")
    
    print("\n4. 演化路径分析...")
    drive_history = {
        'efficiency': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65]
    }
    path_result = tester.emergence_path_analysis(drive_history)
    print(f"   清晰度：{path_result['clarity_score']:.2f}")
    print(f"   判定：{path_result['interpretation']}")
    
    print("\n5. 综合评估...")
    assessment = tester.comprehensive_assessment()
    print(f"   通过测试：{assessment['passed_tests']}/{assessment['total_tests']}")
    print(f"   证据等级：{assessment['evidence_level']}级")
    print(f"   结论：{assessment['conclusion']}")
    
    # 保存结果
    filepath = tester.save_results()
    print(f"\n💾 结果已保存：{filepath}")
    
    print("\n" + "=" * 60)
    print("✅ 验证测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
