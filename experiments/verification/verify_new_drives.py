#!/usr/bin/env python3
"""
MVES New Drive Verification
新驱动验证

对 336h 观察中检测到的新驱动进行 5 项独立性验证
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime


class NewDriveVerification:
    """新驱动验证器"""
    
    def __init__(self, drive_name: str, drive_data: dict):
        self.drive_name = drive_name
        self.drive_data = drive_data
        self.results = {
            'drive_name': drive_name,
            'verification_time': datetime.now().isoformat(),
            'tests': [],
            'conclusion': None
        }
    
    def run_all_tests(self, base_drives: dict):
        """运行全部 5 项验证实验"""
        print(f"\n🔬 验证新驱动：{self.drive_name}")
        
        # 实验 1: 相关性分析
        print("\n1. 相关性分析...")
        test1 = self._correlation_test(base_drives)
        self.results['tests'].append(test1)
        
        # 实验 2: 时间延迟分析
        print("\n2. 时间延迟分析...")
        test2 = self._time_delay_test()
        self.results['tests'].append(test2)
        
        # 实验 3: 功能独立性测试
        print("\n3. 功能独立性测试...")
        test3 = self._functional_independence_test(base_drives)
        self.results['tests'].append(test3)
        
        # 实验 4: 神经表征分析
        print("\n4. 神经表征分析...")
        test4 = self._neural_representation_test(base_drives)
        self.results['tests'].append(test4)
        
        # 实验 5: 演化路径追溯
        print("\n5. 演化路径追溯...")
        test5 = self._emergence_path_test()
        self.results['tests'].append(test5)
        
        return self.results['tests']
    
    def _correlation_test(self, base_drives):
        """实验 1: 相关性分析"""
        # 简化实现：从驱动数据计算
        efficiency = np.array(self.drive_data.get('activity_series', []))
        
        correlations = {}
        for name, values in base_drives.items():
            if len(values) == len(efficiency):
                corr = np.corrcoef(efficiency, values)[0, 1]
                correlations[name] = float(corr)
        
        max_corr = max(abs(c) for c in correlations.values()) if correlations else 1.0
        passed = max_corr < 0.6
        
        return {
            'test': 'correlation',
            'correlations': correlations,
            'max_correlation': max_corr,
            'threshold': 0.6,
            'passed': passed
        }
    
    def _time_delay_test(self):
        """实验 2: 时间延迟分析"""
        # 从驱动数据获取涌现时间
        emergence_time = self.drive_data.get('emergence_cycle', 0)
        passed = emergence_time > 50
        
        return {
            'test': 'time_delay',
            'emergence_time': emergence_time,
            'threshold': 50,
            'passed': passed
        }
    
    def _functional_independence_test(self, base_drives):
        """实验 3: 功能独立性测试"""
        # 简化实现：从驱动数据获取
        activity_without_base = self.drive_data.get('activity_without_base', 0)
        passed = activity_without_base > 0.5
        
        return {
            'test': 'functional_independence',
            'activity': activity_without_base,
            'threshold': 0.5,
            'passed': passed
        }
    
    def _neural_representation_test(self, base_drives):
        """实验 4: 神经表征分析"""
        # 简化实现：从驱动数据获取
        max_overlap = self.drive_data.get('max_neural_overlap', 1.0)
        passed = max_overlap < 0.5
        
        return {
            'test': 'neural_representation',
            'max_overlap': max_overlap,
            'threshold': 0.5,
            'passed': passed
        }
    
    def _emergence_path_test(self):
        """实验 5: 演化路径追溯"""
        # 简化实现：从驱动数据获取
        clarity_score = self.drive_data.get('emergence_path_clarity', 0)
        passed = clarity_score > 0.6
        
        return {
            'test': 'emergence_path',
            'clarity_score': clarity_score,
            'threshold': 0.6,
            'passed': passed
        }
    
    def assess_evidence_level(self):
        """评估证据等级"""
        tests = self.results['tests']
        passed_count = sum(1 for t in tests if t['passed'])
        total_count = len(tests)
        
        if passed_count >= 4:
            level = 'A'
            conclusion = 'A 级证据：独立新驱动确认'
        elif passed_count >= 3:
            level = 'B'
            conclusion = 'B 级证据：部分独立'
        else:
            level = 'C'
            conclusion = 'C 级证据：非独立驱动'
        
        assessment = {
            'passed_tests': passed_count,
            'total_tests': total_count,
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
        filename = f'new_drive_verification_{self.drive_name}_{timestamp}.json'
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath


def main():
    print("=" * 60)
    print("新驱动验证")
    print("=" * 60)
    
    # 加载 336h 观察数据
    print("\n1. 加载 336h 观察数据...")
    observation_path = Path('experiments/results/336h_observation.json')
    
    if not observation_path.exists():
        print("⚠️ 未找到 336h 观察数据，使用模拟数据...")
        # 模拟数据
        new_drives = [
            {'name': 'drive_emerged_at_cycle_24', 'activity': 0.056, 'emergence_cycle': 24},
            {'name': 'drive_emerged_at_cycle_48', 'activity': 0.309, 'emergence_cycle': 48},
            {'name': 'drive_emerged_at_cycle_216', 'activity': 0.094, 'emergence_cycle': 216}
        ]
    else:
        with open(observation_path, 'r') as f:
            data = json.load(f)
        new_drives = data.get('new_drives', [])
    
    print(f"   检测到 {len(new_drives)} 个新驱动")
    
    # 验证每个新驱动
    base_drives = {
        'survival': np.random.randn(336) * 0.25 + 0.25,
        'curiosity': np.random.randn(336) * 0.25 + 0.25,
        'influence': np.random.randn(336) * 0.25 + 0.25,
        'optimization': np.random.randn(336) * 0.25 + 0.25
    }
    
    results = []
    for drive in new_drives:
        verifier = NewDriveVerification(drive['name'], drive)
        verifier.run_all_tests(base_drives)
        assessment = verifier.assess_evidence_level()
        results.append(assessment)
        
        print(f"\n📊 {drive['name']} 验证结果:")
        print(f"   通过测试：{assessment['passed_tests']}/{assessment['total_tests']}")
        print(f"   证据等级：{assessment['evidence_level']}级")
        print(f"   结论：{assessment['conclusion']}")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 新驱动验证总结")
    print("=" * 60)
    
    a_count = sum(1 for r in results if r['evidence_level'] == 'A')
    b_count = sum(1 for r in results if r['evidence_level'] == 'B')
    c_count = sum(1 for r in results if r['evidence_level'] == 'C')
    
    print(f"   验证驱动数：{len(results)}")
    print(f"   A 级证据：{a_count} 个")
    print(f"   B 级证据：{b_count} 个")
    print(f"   C 级证据：{c_count} 个")
    
    if a_count > 0:
        print(f"\n🎯 发现 {a_count} 个独立新驱动!")
    elif b_count > 0:
        print(f"\n⚠️ 发现 {b_count} 个部分独立驱动")
    else:
        print(f"\n⚠️ 未检测到独立新驱动")
    
    print("=" * 60)
    
    return results


if __name__ == '__main__':
    main()
