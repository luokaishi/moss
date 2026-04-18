"""
Generate Pre-registration - 预注册文档生成器

基于 Copilot 评估报告建议，实现实验预注册模板生成。

功能:
1. 生成预注册文档模板
2. 锁定预注册参数 (实验开始后不可修改)
3. 验证预注册完整性
4. 导出预注册报告

使用:
    python scripts/generate_preregistration.py --template v6.0
    python scripts/generate_preregistration.py --lock docs/mves/pre_registration/v6_20260417.yaml
    python scripts/generate_preregistration.py --verify docs/mves/pre_registration/v6_20260417.yaml
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import yaml
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Hypothesis:
    """假设定义"""
    id: str
    name: str
    null_hypothesis: str
    alternative_hypothesis: str
    expected_effect: str
    primary_outcome: str


@dataclass
class PrimaryMetric:
    """主要指标"""
    name: str
    definition: str
    measurement_method: str
    target_value: float
    direction: str  # 'greater', 'less', 'equal'


@dataclass
class ControlCondition:
    """对照条件"""
    name: str
    description: str
    purpose: str


@dataclass
class StatisticalMethod:
    """统计方法"""
    effect_size_metric: str
    ci_method: str
    correction_method: str
    significance_level: float


@dataclass
class PreRegistration:
    """预注册文档"""
    version: str
    date: str
    status: str  # 'draft', 'locked', 'completed'
    
    # 核心内容
    hypotheses: List[Hypothesis]
    primary_metrics: List[PrimaryMetric]
    control_conditions: List[ControlCondition]
    statistical_methods: StatisticalMethod
    
    # 实验设计
    sample_size: int
    random_seeds: List[int]
    total_cycles: int
    checkpoint_interval: int
    
    # 锁定信息
    locked_at: Optional[str] = None
    lock_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'version': self.version,
            'date': self.date,
            'status': self.status,
            'hypotheses': [asdict(h) for h in self.hypotheses],
            'primary_metrics': [asdict(m) for m in self.primary_metrics],
            'control_conditions': [asdict(c) for c in self.control_conditions],
            'statistical_methods': asdict(self.statistical_methods),
            'sample_size': self.sample_size,
            'random_seeds': self.random_seeds,
            'total_cycles': self.total_cycles,
            'checkpoint_interval': self.checkpoint_interval,
            'locked_at': self.locked_at,
            'lock_hash': self.lock_hash,
        }
    
    def calculate_hash(self) -> str:
        """计算内容哈希 (用于锁定验证)"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def lock(self):
        """锁定预注册"""
        if self.status == 'locked':
            raise ValueError("Already locked")
        
        self.status = 'locked'
        self.locked_at = datetime.now().isoformat()
        self.lock_hash = self.calculate_hash()
    
    def verify_integrity(self) -> bool:
        """验证完整性"""
        if self.status != 'locked':
            return True  # 未锁定无需验证
        
        current_hash = self.calculate_hash()
        return current_hash == self.lock_hash


class PreRegistrationGenerator:
    """预注册文档生成器"""
    
    TEMPLATES = {
        'v6.0': {
            'version': 'v6.0.0',
            'hypotheses': [
                {
                    'id': 'H1',
                    'name': '权重上限机制有效性',
                    'null_hypothesis': '设置 survival 驱动权重上限 (30%) 不会显著提升涌现驱动的最终权重',
                    'alternative_hypothesis': '设置 survival 驱动权重上限 (30%) 将使涌现驱动权重从 0.168 提升至 ≥0.20',
                    'expected_effect': '涌现权重 ≥ 0.20',
                    'primary_outcome': 'emergent_drive_weight',
                },
                {
                    'id': 'H2',
                    'name': '驱动竞争机制有效性',
                    'null_hypothesis': '引入驱动竞争机制不会提升涌现驱动的稳定性',
                    'alternative_hypothesis': '驱动竞争机制将使涌现驱动在 10,000 周期内的稳定性从 100% 保持，且权重方差降低 30%',
                    'expected_effect': '稳定性 ≥ 95% 且方差降低 ≥ 20%',
                    'primary_outcome': 'emergent_drive_stability',
                },
                {
                    'id': 'H3',
                    'name': 'GP 质量强化效果',
                    'null_hypothesis': '增加种群规模、惩罚单终端函数不会提升涌现函数的行为增益',
                    'alternative_hypothesis': 'GP 质量强化将使涌现函数的行为增益从当前水平提升至 ≥0.15',
                    'expected_effect': '行为增益 ≥ 0.15',
                    'primary_outcome': 'behavioral_gain',
                },
            ],
            'primary_metrics': [
                {
                    'name': 'emergent_drive_weight',
                    'definition': '涌现驱动在总权重中的占比',
                    'measurement_method': '最终 checkpoint 权重值',
                    'target_value': 0.20,
                    'direction': 'greater',
                },
                {
                    'name': 'emergent_drive_stability',
                    'definition': '涌现驱动在实验周期内的持续存在比例',
                    'measurement_method': '存在周期数 / 总周期数',
                    'target_value': 0.95,
                    'direction': 'greater',
                },
                {
                    'name': 'behavioral_gain',
                    'definition': '涌现驱动带来的行为多样性提升',
                    'measurement_method': '(新行为数 - 基线) / 基线',
                    'target_value': 0.15,
                    'direction': 'greater',
                },
            ],
            'control_conditions': [
                {
                    'name': 'baseline',
                    'description': 'v5.5.2 默认参数',
                    'purpose': '提供比较基准',
                },
                {
                    'name': 'ablation_weight_cap',
                    'description': '移除权重上限机制',
                    'purpose': '验证权重上限的必要性',
                },
                {
                    'name': 'ablation_competition',
                    'description': '移除驱动竞争机制',
                    'purpose': '验证竞争机制的必要性',
                },
            ],
            'statistical_methods': {
                'effect_size_metric': "Cohen's d",
                'ci_method': 'BCa Bootstrap (10,000 samples)',
                'correction_method': 'Bonferroni (α=0.0167 for 3 hypotheses)',
                'significance_level': 0.05,
            },
            'sample_size': 3,  # 3 个 seed
            'random_seeds': [42, 123, 456],
            'total_cycles': 10000,
            'checkpoint_interval': 1000,
        }
    }
    
    def __init__(self, output_dir: str = 'docs/mves/pre_registration'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, template_name: str) -> PreRegistration:
        """生成预注册文档"""
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.TEMPLATES[template_name]
        
        # 构建预注册对象
        pre_reg = PreRegistration(
            version=template['version'],
            date=datetime.now().isoformat(),
            status='draft',
            hypotheses=[Hypothesis(**h) for h in template['hypotheses']],
            primary_metrics=[PrimaryMetric(**m) for m in template['primary_metrics']],
            control_conditions=[ControlCondition(**c) for c in template['control_conditions']],
            statistical_methods=StatisticalMethod(**template['statistical_methods']),
            sample_size=template['sample_size'],
            random_seeds=template['random_seeds'],
            total_cycles=template['total_cycles'],
            checkpoint_interval=template['checkpoint_interval'],
        )
        
        return pre_reg
    
    def save(self, pre_reg: PreRegistration, filename: str = None):
        """保存预注册文档"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"v6_{timestamp}.yaml"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            yaml.dump(pre_reg.to_dict(), f, default_flow_style=False, sort_keys=False)
        
        return filepath
    
    def load(self, filepath: str) -> PreRegistration:
        """加载预注册文档"""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        return PreRegistration(
            version=data['version'],
            date=data['date'],
            status=data['status'],
            hypotheses=[Hypothesis(**h) for h in data['hypotheses']],
            primary_metrics=[PrimaryMetric(**m) for m in data['primary_metrics']],
            control_conditions=[ControlCondition(**c) for c in data['control_conditions']],
            statistical_methods=StatisticalMethod(**data['statistical_methods']),
            sample_size=data['sample_size'],
            random_seeds=data['random_seeds'],
            total_cycles=data['total_cycles'],
            checkpoint_interval=data['checkpoint_interval'],
            locked_at=data.get('locked_at'),
            lock_hash=data.get('lock_hash'),
        )
    
    def lock(self, filepath: str):
        """锁定预注册文档"""
        pre_reg = self.load(filepath)
        pre_reg.lock()
        self.save(pre_reg, Path(filepath).name)
        print(f"✅ 预注册已锁定: {filepath}")
        print(f"   锁定时间: {pre_reg.locked_at}")
        print(f"   锁定哈希: {pre_reg.lock_hash}")
        return pre_reg
    
    def verify(self, filepath: str) -> bool:
        """验证预注册文档完整性"""
        pre_reg = self.load(filepath)
        
        is_valid = pre_reg.verify_integrity()
        
        print(f"\n{'='*60}")
        print(f"预注册验证: {filepath}")
        print(f"{'='*60}")
        print(f"版本: {pre_reg.version}")
        print(f"状态: {pre_reg.status}")
        print(f"创建时间: {pre_reg.date}")
        
        if pre_reg.status == 'locked':
            print(f"锁定时间: {pre_reg.locked_at}")
            print(f"锁定哈希: {pre_reg.lock_hash}")
            print(f"当前哈希: {pre_reg.calculate_hash()}")
            print(f"完整性: {'✅ 通过' if is_valid else '❌ 失败'}")
        
        print(f"\n假设 ({len(pre_reg.hypotheses)} 个):")
        for h in pre_reg.hypotheses:
            print(f"  - {h.id}: {h.name}")
        
        print(f"\n主要指标 ({len(pre_reg.primary_metrics)} 个):")
        for m in pre_reg.primary_metrics:
            print(f"  - {m.name}: target={m.target_value}")
        
        print(f"\n对照条件 ({len(pre_reg.control_conditions)} 个):")
        for c in pre_reg.control_conditions:
            print(f"  - {c.name}")
        
        print(f"{'='*60}\n")
        
        return is_valid


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MOSS 实验预注册文档生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成预注册模板
  python generate_preregistration.py --template v6.0
  
  # 锁定预注册
  python generate_preregistration.py --lock docs/mves/pre_registration/v6_20260417.yaml
  
  # 验证预注册
  python generate_preregistration.py --verify docs/mves/pre_registration/v6_20260417.yaml
        """
    )
    
    parser.add_argument('--template', type=str,
                       help='生成预注册模板 (v6.0)')
    parser.add_argument('--lock', type=str,
                       help='锁定预注册文档')
    parser.add_argument('--verify', type=str,
                       help='验证预注册文档')
    parser.add_argument('--output-dir', type=str,
                       default='docs/mves/pre_registration',
                       help='输出目录')
    
    args = parser.parse_args()
    
    generator = PreRegistrationGenerator(args.output_dir)
    
    if args.template:
        # 生成模板
        pre_reg = generator.generate(args.template)
        filepath = generator.save(pre_reg)
        print(f"✅ 预注册模板已生成: {filepath}")
        generator.verify(str(filepath))
        
    elif args.lock:
        # 锁定文档
        generator.lock(args.lock)
        
    elif args.verify:
        # 验证文档
        generator.verify(args.verify)
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()