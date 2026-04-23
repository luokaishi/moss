"""
MOSS v7.3 - Optimized Meta-SME v2
性能优化版 Meta-SME

集成优化组件:
- PerformanceBuffer (批量处理)
- SmartTrigger (智能触发)
- CachedCalculator (缓存计算)

Author: MOSS Project
Date: 2026-04-19
Version: 7.3.0-dev
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from meta_sme import MetaSME, ModificationType, ModificationProposal, ModificationResult
from meta_sme_optimizer import PerformanceBuffer, SmartTrigger, CachedCalculator
from typing import Dict, List, Optional
import numpy as np


class OptimizedMetaSME(MetaSME):
    """
    优化的 Meta-SME v2
    
    继承原有 Meta-SME 功能，添加性能优化
    """
    
    def __init__(self, 
                 enable_auto_modify: bool = False,
                 require_human_approval: bool = True,
                 sandbox_dir: str = ".sandbox",
                 backup_dir: str = ".backups/meta_sme",
                 batch_size: int = 100,
                 cooldown_period: int = 100,
                 use_optimization: bool = True):
        """
        Args:
            enable_auto_modify: 是否启用自动修改
            require_human_approval: 是否需要人工审核
            sandbox_dir: 沙箱目录
            backup_dir: 备份目录
            batch_size: 批处理大小
            cooldown_period: 冷却期
            use_optimization: 是否使用优化
        """
        # 调用父类初始化
        super().__init__(
            enable_auto_modify=enable_auto_modify,
            require_human_approval=require_human_approval,
            sandbox_dir=sandbox_dir,
            backup_dir=backup_dir
        )
        
        self.use_optimization = use_optimization
        
        if use_optimization:
            # 优化组件
            self._perf_buffer = PerformanceBuffer(batch_size=batch_size)
            self._smart_trigger = SmartTrigger(cooldown_period=cooldown_period)
            self._calculator = CachedCalculator()
            
            # 覆盖原有性能历史
            self.performance_history = self._perf_buffer
        
        # 优化统计
        self.optimization_stats = {
            'records_optimized': 0,
            'triggers_optimized': 0,
            'cache_hits': 0,
            'use_optimization': use_optimization
        }
    
    def record_performance(self, performance: float):
        """记录性能 (优化版)"""
        if self.use_optimization:
            # 使用优化的缓冲区
            self._perf_buffer.add(performance)
            self._smart_trigger.record(performance)
            self.optimization_stats['records_optimized'] += 1
        else:
            # 使用父类方法
            super().record_performance(performance)
    
    def should_generate_proposal(self) -> bool:
        """是否应该生成提案 (优化版)"""
        if self.use_optimization:
            result = self._smart_trigger.should_trigger()
            if result:
                self.optimization_stats['triggers_optimized'] += 1
            return result
        else:
            return super().should_generate_proposal()
    
    def get_optimization_stats(self) -> Dict:
        """获取优化统计"""
        if not self.use_optimization:
            return {'use_optimization': False}
        
        return {
            **self.optimization_stats,
            'buffer_stats': self._perf_buffer.get_stats(),
            'trigger_stats': self._smart_trigger.get_stats()
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.3 - Optimized Meta-SME v2 Test")
    print("=" * 60)
    
    import time
    
    # 测试优化版
    print("\n1. Testing Optimized Meta-SME...")
    opt_sme = OptimizedMetaSME(
        enable_auto_modify=True,
        cooldown_period=50,
        use_optimization=True
    )
    
    start = time.time()
    triggers = 0
    
    for i in range(10000):
        perf = 0.5 + np.sin(i / 100) * 0.2 + np.random.randn() * 0.05
        opt_sme.record_performance(perf)
        if opt_sme.should_generate_proposal():
            triggers += 1
    
    elapsed = time.time() - start
    
    print(f"   Records: 10,000")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Throughput: {10000/elapsed:.0f} records/s")
    print(f"   Triggers: {triggers}")
    
    # 优化统计
    opt_stats = opt_sme.get_optimization_stats()
    print(f"\n2. Optimization Stats:")
    print(f"   Records optimized: {opt_stats['records_optimized']}")
    print(f"   Triggers optimized: {opt_stats['triggers_optimized']}")
    print(f"   Adaptive threshold: {opt_stats['trigger_stats']['adaptive_threshold']:.4f}")
    
    # 对比测试
    print("\n3. Comparing with original Meta-SME...")
    orig_sme = OptimizedMetaSME(
        enable_auto_modify=True,
        use_optimization=False  # 禁用优化
    )
    
    start = time.time()
    orig_triggers = 0
    
    for i in range(10000):
        perf = 0.5 + np.sin(i / 100) * 0.2 + np.random.randn() * 0.05
        orig_sme.record_performance(perf)
        if orig_sme.should_generate_proposal():
            orig_triggers += 1
    
    orig_elapsed = time.time() - start
    
    print(f"   Original Time: {orig_elapsed:.3f}s")
    print(f"   Original Triggers: {orig_triggers}")
    
    # 对比
    print(f"\n4. Comparison:")
    if orig_elapsed > 0:
        print(f"   Speedup: {orig_elapsed/elapsed:.2f}x")
    else:
        print(f"   Speedup: N/A")
    if orig_triggers > 0:
        print(f"   Trigger reduction: {(1 - triggers/orig_triggers)*100:.1f}%")
    else:
        print(f"   Trigger reduction: N/A (original had 0 triggers)")
    print(f"   Optimized triggers: {triggers} ({triggers/10000*100:.2f}%)")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)