"""
Verify Reproduction - 复现验证脚本

自动验证 MOSS 实验的可复现性。

验证内容:
1. 涌现检测验证 - 确认涌现驱动在预期周期出现
2. 权重分布验证 - 确认权重分布符合预期
3. 内存使用验证 - 确认内存使用正常
4. 统计指标验证 - 确认统计指标合理

使用:
    python scripts/verify_reproduction.py --report logs/experiment_xxx/final_report.json
    python scripts/verify_reproduction.py --verify-all
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    name: str
    passed: bool
    expected: any
    actual: any
    message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'passed': self.passed,
            'expected': self.expected,
            'actual': self.actual,
            'message': self.message,
        }


class ReproductionVerifier:
    """复现验证器"""
    
    # 验证标准
    CRITERIA = {
        'emergence': {
            'detected': True,
            'cycle_range': (50, 150),
        },
        'weights': {
            'survival_max': 0.33,
            'emergent_min': 0.20,
            'min_weight': 0.02,
            'max_weight': 0.40,
        },
        'memory': {
            'max_mb': 1000,
            'growth_rate_max': 5.0,  # MB/千周期
        },
        'stability': {
            'min_stability': 0.90,
        },
    }
    
    def __init__(self, report_path: str):
        self.report_path = Path(report_path)
        self.report = self._load_report()
        self.results: List[ValidationResult] = []
    
    def _load_report(self) -> Dict:
        """加载报告"""
        if not self.report_path.exists():
            raise FileNotFoundError(f"报告不存在: {self.report_path}")
        
        with open(self.report_path, 'r') as f:
            return json.load(f)
    
    def verify_all(self) -> Tuple[bool, List[ValidationResult]]:
        """验证所有项目"""
        self.results = []
        
        # 1. 验证涌现
        self._verify_emergence()
        
        # 2. 验证权重分布
        self._verify_weights()
        
        # 3. 验证内存
        self._verify_memory()
        
        # 4. 验证稳定性
        self._verify_stability()
        
        # 5. 验证统计指标
        self._verify_statistics()
        
        # 计算总结果
        all_passed = all(r.passed for r in self.results)
        
        return all_passed, self.results
    
    def _verify_emergence(self):
        """验证涌现检测"""
        # 检查是否检测到涌现
        emergence_events = self.report.get('emergence_events', [])
        detected = len(emergence_events) > 0
        
        self.results.append(ValidationResult(
            name="涌现检测",
            passed=detected == self.CRITERIA['emergence']['detected'],
            expected=self.CRITERIA['emergence']['detected'],
            actual=detected,
            message="涌现驱动是否被检测到" if detected else "未检测到涌现驱动"
        ))
        
        # 检查涌现周期
        if emergence_events:
            cycle = emergence_events[0].get('cycle', 0)
            cycle_range = self.CRITERIA['emergence']['cycle_range']
            in_range = cycle_range[0] <= cycle <= cycle_range[1]
            
            self.results.append(ValidationResult(
                name="涌现周期",
                passed=in_range,
                expected=f"{cycle_range[0]}-{cycle_range[1]}",
                actual=cycle,
                message=f"涌现发生在周期 {cycle}"
            ))
    
    def _verify_weights(self):
        """验证权重分布"""
        final_drives = self.report.get('final_drives', {})
        
        if not final_drives:
            self.results.append(ValidationResult(
                name="权重分布",
                passed=False,
                expected="有数据",
                actual="无数据",
                message="报告中无驱动权重数据"
            ))
            return
        
        # 检查 survival 上限
        if 'survival' in final_drives:
            survival_weight = final_drives['survival'].get('weight', 0)
            survival_max = self.CRITERIA['weights']['survival_max']
            
            self.results.append(ValidationResult(
                name="survival 上限",
                passed=survival_weight <= survival_max,
                expected=f"<= {survival_max}",
                actual=round(survival_weight, 3),
                message=f"survival 权重: {survival_weight:.3f}"
            ))
        
        # 检查涌现驱动权重
        emergent_drives = [k for k, v in final_drives.items() 
                          if v.get('is_emergent', False)]
        if emergent_drives:
            emergent_weight = max(final_drives[k].get('weight', 0) for k in emergent_drives)
            emergent_min = self.CRITERIA['weights']['emergent_min']
            
            self.results.append(ValidationResult(
                name="涌现驱动权重",
                passed=emergent_weight >= emergent_min,
                expected=f">= {emergent_min}",
                actual=round(emergent_weight, 3),
                message=f"涌现驱动权重: {emergent_weight:.3f}"
            ))
        
        # 检查权重范围
        for name, data in final_drives.items():
            weight = data.get('weight', 0)
            min_w = self.CRITERIA['weights']['min_weight']
            max_w = self.CRITERIA['weights']['max_weight']
            
            if not (min_w <= weight <= max_w):
                self.results.append(ValidationResult(
                    name=f"{name} 权重范围",
                    passed=False,
                    expected=f"[{min_w}, {max_w}]",
                    actual=round(weight, 3),
                    message=f"{name} 权重超出范围"
                ))
    
    def _verify_memory(self):
        """验证内存使用"""
        memory_stats = self.report.get('memory_stats', {})
        
        if not memory_stats:
            # 如果没有内存统计，跳过
            return
        
        # 检查峰值内存
        peak_mb = memory_stats.get('peak_mb', 0)
        max_mb = self.CRITERIA['memory']['max_mb']
        
        self.results.append(ValidationResult(
            name="峰值内存",
            passed=peak_mb <= max_mb,
            expected=f"<= {max_mb} MB",
            actual=f"{peak_mb:.1f} MB",
            message=f"峰值内存使用: {peak_mb:.1f} MB"
        ))
        
        # 检查内存增长率
        growth_rate = memory_stats.get('growth_rate_mb_per_1k', 0)
        max_growth = self.CRITERIA['memory']['growth_rate_max']
        
        self.results.append(ValidationResult(
            name="内存增长率",
            passed=growth_rate <= max_growth,
            expected=f"<= {max_growth} MB/千周期",
            actual=f"{growth_rate:.2f} MB/千周期",
            message=f"内存增长率: {growth_rate:.2f} MB/千周期"
        ))
    
    def _verify_stability(self):
        """验证稳定性"""
        final_drives = self.report.get('final_drives', {})
        
        for name, data in final_drives.items():
            stability = data.get('stability', 0)
            min_stability = self.CRITERIA['stability']['min_stability']
            
            if stability < min_stability:
                self.results.append(ValidationResult(
                    name=f"{name} 稳定性",
                    passed=False,
                    expected=f">= {min_stability}",
                    actual=round(stability, 3),
                    message=f"{name} 稳定性过低: {stability:.3f}"
                ))
    
    def _verify_statistics(self):
        """验证统计指标"""
        # 检查是否有效应量
        effect_sizes = self.report.get('statistics', {}).get('effect_sizes', {})
        
        if effect_sizes:
            for metric, data in effect_sizes.items():
                value = data.get('value', 0)
                ci_lower = data.get('ci_95', [0, 0])[0]
                ci_upper = data.get('ci_95', [0, 0])[1]
                
                # CI 应该包含效应量 (近似)
                ci_valid = ci_lower <= value <= ci_upper or \
                          abs(ci_lower - value) < 0.01 or \
                          abs(ci_upper - value) < 0.01
                
                self.results.append(ValidationResult(
                    name=f"{metric} CI",
                    passed=ci_valid,
                    expected=f"CI 包含 {value:.3f}",
                    actual=f"[{ci_lower:.3f}, {ci_upper:.3f}]",
                    message=f"{metric}: {value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]"
                ))
    
    def print_report(self):
        """打印验证报告"""
        print(f"\n{'='*60}")
        print(f"复现验证报告")
        print(f"{'='*60}")
        print(f"报告: {self.report_path}")
        print(f"{'='*60}\n")
        
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        
        for result in self.results:
            status = '✅' if result.passed else '❌'
            print(f"{status} {result.name}")
            print(f"   预期: {result.expected}")
            print(f"   实际: {result.actual}")
            if result.message:
                print(f"   说明: {result.message}")
            print()
        
        print(f"{'='*60}")
        print(f"结果: {passed_count}/{total_count} 通过")
        print(f"{'='*60}\n")
        
        return passed_count == total_count


def verify_single_report(report_path: str) -> bool:
    """验证单个报告"""
    try:
        verifier = ReproductionVerifier(report_path)
        passed, results = verifier.verify_all()
        verifier.print_report()
        return passed
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def verify_all_seeds():
    """验证所有 seed 的实验"""
    seeds = [42, 123, 456]
    
    print(f"\n{'='*60}")
    print(f"验证所有 Seed 的复现性")
    print(f"{'='*60}\n")
    
    results = {}
    all_passed = True
    
    for seed in seeds:
        # 查找最新的实验目录
        log_dir = Path('logs')
        if not log_dir.exists():
            print(f"❌ Seed {seed}: 无实验目录")
            results[seed] = False
            all_passed = False
            continue
        
        # 查找包含该 seed 的最新报告
        report_files = list(log_dir.glob(f'*/final_report.json'))
        matching_reports = [f for f in report_files if f'seed{seed}' in str(f)]
        
        if not matching_reports:
            print(f"❌ Seed {seed}: 未找到报告")
            results[seed] = False
            all_passed = False
            continue
        
        # 使用最新的报告
        latest_report = max(matching_reports, key=lambda p: p.stat().st_mtime)
        
        print(f"\n验证 Seed {seed}:")
        print(f"  报告: {latest_report}")
        
        passed = verify_single_report(str(latest_report))
        results[seed] = passed
        all_passed = all_passed and passed
    
    # 打印汇总
    print(f"\n{'='*60}")
    print(f"验证汇总")
    print(f"{'='*60}")
    
    for seed, passed in results.items():
        status = '✅' if passed else '❌'
        print(f"  {status} Seed {seed}: {'通过' if passed else '失败'}")
    
    print(f"\n  总体: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    print(f"{'='*60}\n")
    
    return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MOSS 复现验证脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python verify_reproduction.py --report logs/experiment_xxx/final_report.json
  python verify_reproduction.py --verify-all
        """
    )
    
    parser.add_argument('--report', type=str,
                       help='实验报告路径')
    parser.add_argument('--verify-all', action='store_true',
                       help='验证所有 seed 的实验')
    
    args = parser.parse_args()
    
    if args.verify_all:
        # 验证所有 seed
        passed = verify_all_seeds()
        sys.exit(0 if passed else 1)
    elif args.report:
        # 验证单个报告
        passed = verify_single_report(args.report)
        sys.exit(0 if passed else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()