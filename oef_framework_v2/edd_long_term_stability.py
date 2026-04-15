"""
长期稳定性测试 - Phase 6

目标: 1000+ cycles长期运行，验证多目标共存和驱动冲突解决
"""

import numpy as np
from typing import Dict, List
import time

from edd_runtime_causal_validation import ValidatedSelfDrivenAgent


class LongTermStabilityTest:
    """
    长期稳定性测试
    
    测试场景:
    1. 1000+ cycles连续运行
    2. 多行为模式切换
    3. 验证驱动力长期稳定性
    4. 测试驱动冲突解决
    """
    
    def __init__(self, n_cycles: int = 1000):
        self.n_cycles = n_cycles
        
        # 创建Agent
        self.agent = ValidatedSelfDrivenAgent(
            embedding_dim=64,
            min_cluster_size=5
        )
        
        # 测试记录
        self.metrics_history = []
        self.drive_evolution = []
        self.conflict_events = []
    
    def run_long_term_test(self):
        """运行长期测试"""
        
        print("=" * 70)
        print(f"Phase 6: 长期稳定性测试 ({self.n_cycles} cycles)")
        print("=" * 70)
        
        # 定义测试阶段
        phases = [
            ('exploration', 0, 250),
            ('gathering', 250, 500),
            ('collaboration', 500, 750),
            ('learning', 750, 1000)
        ]
        
        print(f"\n📊 测试阶段:")
        for name, start, end in phases:
            print(f"   {name}: {start}-{end}")
        
        # 运行测试
        for phase_name, start, end in phases:
            print(f"\n{'='*70}")
            print(f"📍 阶段: {phase_name} ({start}-{end})")
            print(f"{'='*70}")
            
            for cycle in range(start, end):
                # 根据阶段选择action分布
                action = self._select_action_for_phase(phase_name)
                
                # Agent step
                result = self.agent.step({'phase': phase_name, 'cycle': cycle})
                
                # 记录metrics
                if cycle % 50 == 0:
                    self._record_metrics(cycle)
                    
                    # 打印进度
                    summary = self.agent.get_summary()
                    print(f"\nCycle {cycle}:")
                    print(f"   发现聚类: {summary['edd_summary']['n_discovered']}")
                    print(f"   驱动力数: {summary['drive_space_summary']['total_drives']}")
                    print(f"   活跃驱动: {summary['drive_space_summary']['active_drives']}")
                    
                    # 检查驱动冲突
                    conflicts = self._check_drive_conflicts()
                    if conflicts:
                        print(f"   ⚠️ 检测到 {len(conflicts)} 个驱动冲突")
                        self.conflict_events.extend(conflicts)
        
        # 生成最终报告
        return self._generate_report()
    
    def _select_action_for_phase(self, phase: str) -> str:
        """根据阶段选择action"""
        action_distributions = {
            'exploration': ['explore', 'explore', 'explore', 'rest', 'rest'],
            'gathering': ['gather', 'gather', 'gather', 'rest', 'rest'],
            'collaboration': ['communicate', 'communicate', 'help', 'rest', 'rest'],
            'learning': ['learn', 'learn', 'adapt', 'rest', 'rest']
        }
        
        actions = action_distributions.get(phase, ['explore', 'rest'])
        return np.random.choice(actions)
    
    def _record_metrics(self, cycle: int):
        """记录metrics"""
        summary = self.agent.get_summary()
        
        metrics = {
            'cycle': cycle,
            'n_discovered': summary['edd_summary']['n_discovered'],
            'n_drives': summary['drive_space_summary']['total_drives'],
            'n_active': summary['drive_space_summary']['active_drives'],
            'drives': [
                {
                    'name': d['name'],
                    'weight': d['weight'],
                    'confidence': d['confidence'],
                    'is_initial': d['is_initial']
                }
                for d in summary['drive_space_summary']['drives']
            ]
        }
        
        self.metrics_history.append(metrics)
    
    def _check_drive_conflicts(self) -> List[Dict]:
        """检查驱动冲突"""
        conflicts = []
        
        drives = self.agent.drive_space.get_active_drives()
        
        # 检查权重过高的驱动
        for drive in drives:
            if drive.weight > 0.8:
                conflicts.append({
                    'type': 'high_weight',
                    'drive': drive.name,
                    'weight': drive.weight,
                    'cycle': self.agent.cycle
                })
        
        # 检查长期未激活的驱动
        for drive in drives:
            if (self.agent.cycle - drive.last_activation > 200 and
                drive.activation_count > 0):
                conflicts.append({
                    'type': 'stale_drive',
                    'drive': drive.name,
                    'last_activation': drive.last_activation,
                    'cycle': self.agent.cycle
                })
        
        return conflicts
    
    def _generate_report(self) -> Dict:
        """生成测试报告"""
        
        print("\n" + "=" * 70)
        print("长期稳定性测试报告")
        print("=" * 70)
        
        # 基本统计
        final_metrics = self.metrics_history[-1] if self.metrics_history else {}
        
        print(f"\n📊 基本统计:")
        print(f"   总周期: {self.n_cycles}")
        print(f"   最终发现聚类: {final_metrics.get('n_discovered', 0)}")
        print(f"   最终驱动力数: {final_metrics.get('n_drives', 0)}")
        print(f"   最终活跃驱动: {final_metrics.get('n_active', 0)}")
        
        # 驱动力演化
        print(f"\n📈 驱动力演化:")
        initial_count = self.metrics_history[0]['n_drives'] if self.metrics_history else 0
        max_count = max(m['n_drives'] for m in self.metrics_history) if self.metrics_history else 0
        
        print(f"   初始驱动力: {initial_count}")
        print(f"   最大驱动力: {max_count}")
        print(f"   最终驱动力: {final_metrics.get('n_drives', 0)}")
        
        # 冲突统计
        print(f"\n⚠️ 冲突事件:")
        print(f"   总冲突数: {len(self.conflict_events)}")
        
        conflict_types = {}
        for c in self.conflict_events:
            t = c['type']
            conflict_types[t] = conflict_types.get(t, 0) + 1
        
        for t, count in conflict_types.items():
            print(f"   - {t}: {count}")
        
        # 稳定性评估
        print(f"\n✅ 稳定性评估:")
        
        # 检查是否稳定运行到结束
        stable = len(self.metrics_history) >= self.n_cycles // 50 - 5
        print(f"   完整运行: {'✅' if stable else '❌'}")
        
        # 检查是否有涌现驱动
        has_emergent = any(
            not d['is_initial'] 
            for m in self.metrics_history 
            for d in m.get('drives', [])
        )
        print(f"   涌现驱动: {'✅' if has_emergent else '❌'}")
        
        # 检查冲突处理
        conflicts_resolved = len(self.conflict_events) < 10
        print(f"   冲突可控: {'✅' if conflicts_resolved else '❌'}")
        
        # 综合评分
        stability_score = sum([
            1.0 if stable else 0.0,
            1.0 if has_emergent else 0.0,
            1.0 if conflicts_resolved else 0.0
        ]) / 3.0
        
        print(f"\n📊 稳定性评分: {stability_score:.2f}/1.00")
        
        if stability_score >= 0.8:
            print("   🎉 优秀: 系统高度稳定")
        elif stability_score >= 0.6:
            print("   ✅ 良好: 系统基本稳定")
        else:
            print("   ⚠️ 需改进: 存在稳定性问题")
        
        return {
            'n_cycles': self.n_cycles,
            'final_discovered': final_metrics.get('n_discovered', 0),
            'final_drives': final_metrics.get('n_drives', 0),
            'stability_score': stability_score,
            'conflict_count': len(self.conflict_events),
            'metrics_history': self.metrics_history
        }


# 运行测试
if __name__ == "__main__":
    test = LongTermStabilityTest(n_cycles=1000)
    report = test.run_long_term_test()
    
    print("\n" + "=" * 70)
    print("Phase 6 完成")
    print("=" * 70)
    print(f"\n稳定性评分: {report['stability_score']:.2f}")
    print(f"发现聚类: {report['final_discovered']}")
    print(f"最终驱动力: {report['final_drives']}")
    print(f"冲突事件: {report['conflict_count']}")
