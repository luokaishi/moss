#!/usr/bin/env python3
"""
MOSS v6.1 - Memory Manager
内存管理器

核心功能:
- 内存分配/释放
- 垃圾回收
- 使用率监控
- 内存池

Author: MOSS Project
Date: 2026-04-03
Version: 6.1.0-dev
"""

import gc
import sys
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import weakref


@dataclass
class MemoryBlock:
    """内存块"""
    id: str
    size_mb: float
    allocated_at: datetime = field(default_factory=datetime.now)
    freed_at: Optional[datetime] = None
    is_active: bool = True


class MemoryPool:
    """
    内存池
    
    预分配内存块
    """
    
    def __init__(self, pool_size_mb: int = 100, block_size_mb: float = 1.0):
        self.pool_size_mb = pool_size_mb
        self.block_size_mb = block_size_mb
        
        self.blocks: List[MemoryBlock] = []
        self.available_blocks: List[MemoryBlock] = []
        self.allocated_blocks: Dict[str, MemoryBlock] = {}
        
        self.lock = threading.Lock()
        
        self.stats = {
            'allocations': 0,
            'deallocations': 0,
            'peak_usage_mb': 0.0
        }
        
        # 预分配内存块
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化内存池"""
        num_blocks = int(self.pool_size_mb / self.block_size_mb)
        
        for i in range(num_blocks):
            block = MemoryBlock(
                id=f"block_{i}",
                size_mb=self.block_size_mb
            )
            self.blocks.append(block)
            self.available_blocks.append(block)
    
    def allocate(self, size_mb: float) -> Optional[str]:
        """
        分配内存
        
        Args:
            size_mb: 大小 (MB)
            
        Returns:
            内存块 ID，失败返回 None
        """
        with self.lock:
            # 计算需要的块数
            num_blocks_needed = int(size_mb / self.block_size_mb) + 1
            
            if len(self.available_blocks) < num_blocks_needed:
                return None
            
            # 分配块
            allocated_ids = []
            for _ in range(num_blocks_needed):
                block = self.available_blocks.pop(0)
                block.is_active = False
                self.allocated_blocks[block.id] = block
                allocated_ids.append(block.id)
            
            block_id = "+".join(allocated_ids)
            
            self.stats['allocations'] += 1
            current_usage = self._get_current_usage()
            if current_usage > self.stats['peak_usage_mb']:
                self.stats['peak_usage_mb'] = current_usage
            
            return block_id
    
    def deallocate(self, block_id: str) -> bool:
        """
        释放内存
        
        Args:
            block_id: 内存块 ID
            
        Returns:
            是否成功
        """
        with self.lock:
            ids = block_id.split("+")
            
            for bid in ids:
                if bid not in self.allocated_blocks:
                    return False
                
                block = self.allocated_blocks[bid]
                block.is_active = True
                block.freed_at = datetime.now()
                
                self.available_blocks.append(block)
                del self.allocated_blocks[bid]
            
            self.stats['deallocations'] += 1
            return True
    
    def _get_current_usage(self) -> float:
        """获取当前使用量"""
        return len(self.allocated_blocks) * self.block_size_mb
    
    def get_usage(self) -> Dict:
        """获取使用情况"""
        return {
            'total_mb': self.pool_size_mb,
            'used_mb': self._get_current_usage(),
            'available_mb': len(self.available_blocks) * self.block_size_mb,
            'usage_percent': (self._get_current_usage() / self.pool_size_mb) * 100,
            'stats': self.stats
        }


class GarbageCollector:
    """
    垃圾回收器
    
    自动回收未使用的内存
    """
    
    def __init__(self, memory_pool: MemoryPool):
        self.memory_pool = memory_pool
        self.references: Dict[str, weakref.ref] = {}
        
        self.stats = {
            'collections': 0,
            'objects_collected': 0,
            'memory_freed_mb': 0.0
        }
    
    def register(self, obj_id: str, obj: Any, memory_block: str):
        """
        注册对象
        
        Args:
            obj_id: 对象 ID
            obj: 对象
            memory_block: 内存块 ID
        """
        def callback(ref):
            # 对象被垃圾回收时释放内存
            self.memory_pool.deallocate(memory_block)
            self.stats['objects_collected'] += 1
        
        self.references[obj_id] = weakref.ref(obj, callback)
    
    def collect(self) -> int:
        """
        执行垃圾回收
        
        Returns:
            回收的对象数
        """
        collected = 0
        
        # 强制垃圾回收
        gc.collect()
        
        # 检查引用
        for obj_id, ref in list(self.references.items()):
            if ref() is None:
                del self.references[obj_id]
                collected += 1
        
        self.stats['collections'] += 1
        return collected
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'stats': self.stats,
            'registered_objects': len(self.references)
        }


class MemoryManager:
    """
    内存管理器
    
    统一管理内存分配和回收
    """
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.memory_pool = MemoryPool(pool_size_mb=max_memory_mb)
        self.gc = GarbageCollector(self.memory_pool)
        
        self.allocations: Dict[str, Dict] = {}
        
        self.stats = {
            'total_allocations': 0,
            'total_deallocations': 0,
            'current_usage_mb': 0.0,
            'peak_usage_mb': 0.0
        }
    
    def allocate(self, key: str, size_mb: float, 
                 obj: Optional[Any] = None) -> bool:
        """
        分配内存
        
        Args:
            key: 分配键
            size_mb: 大小 (MB)
            obj: 关联对象 (可选)
            
        Returns:
            是否成功
        """
        block_id = self.memory_pool.allocate(size_mb)
        
        if block_id is None:
            return False
        
        self.allocations[key] = {
            'block_id': block_id,
            'size_mb': size_mb,
            'allocated_at': datetime.now()
        }
        
        self.stats['total_allocations'] += 1
        self.stats['current_usage_mb'] += size_mb
        
        if self.stats['current_usage_mb'] > self.stats['peak_usage_mb']:
            self.stats['peak_usage_mb'] = self.stats['current_usage_mb']
        
        # 注册垃圾回收
        if obj is not None:
            self.gc.register(key, obj, block_id)
        
        return True
    
    def deallocate(self, key: str) -> bool:
        """
        释放内存
        
        Args:
            key: 分配键
            
        Returns:
            是否成功
        """
        if key not in self.allocations:
            return False
        
        allocation = self.allocations[key]
        success = self.memory_pool.deallocate(allocation['block_id'])
        
        if success:
            self.stats['total_deallocations'] += 1
            self.stats['current_usage_mb'] -= allocation['size_mb']
            del self.allocations[key]
        
        return success
    
    def get_usage(self) -> Dict:
        """获取使用情况"""
        return {
            'stats': self.stats,
            'pool': self.memory_pool.get_usage(),
            'gc': self.gc.get_stats()
        }
    
    def optimize(self) -> Dict:
        """
        优化内存使用
        
        Returns:
            优化结果
        """
        # 执行垃圾回收
        collected = self.gc.collect()
        
        # 获取使用率
        usage = self.get_usage()
        usage_percent = usage['pool']['usage_percent']
        
        suggestions = []
        
        if usage_percent > 80:
            suggestions.append({
                'type': 'high_usage',
                'issue': 'Memory usage above 80%',
                'suggestion': 'Consider increasing memory limit or optimizing allocations',
                'current': usage_percent
            })
        
        if collected > 0:
            suggestions.append({
                'type': 'gc_collected',
                'issue': f'{collected} objects collected',
                'suggestion': 'Review object lifecycle management'
            })
        
        return {
            'suggestions': suggestions,
            'usage': usage,
            'collected': collected
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.1 - Memory Manager Test")
    print("=" * 60)
    
    # 创建内存管理器
    manager = MemoryManager(max_memory_mb=100)
    
    # 测试内存分配
    print("\n1. 测试内存分配...")
    success1 = manager.allocate('test1', 10.0)
    success2 = manager.allocate('test2', 20.0)
    success3 = manager.allocate('test3', 30.0)
    
    print(f"   分配 1: {'✅' if success1 else '❌'}")
    print(f"   分配 2: {'✅' if success2 else '❌'}")
    print(f"   分配 3: {'✅' if success3 else '❌'}")
    
    # 获取使用情况
    print("\n2. 内存使用情况:")
    usage = manager.get_usage()
    print(f"   当前使用：{usage['stats']['current_usage_mb']:.1f}MB")
    print(f"   峰值使用：{usage['stats']['peak_usage_mb']:.1f}MB")
    print(f"   使用率：{usage['pool']['usage_percent']:.1f}%")
    
    # 测试内存释放
    print("\n3. 测试内存释放...")
    success = manager.deallocate('test2')
    print(f"   释放 test2: {'✅' if success else '❌'}")
    
    usage = manager.get_usage()
    print(f"   当前使用：{usage['stats']['current_usage_mb']:.1f}MB")
    
    # 测试优化
    print("\n4. 内存优化:")
    optimization = manager.optimize()
    print(f"   建议数：{len(optimization['suggestions'])}")
    print(f"   回收对象：{optimization['collected']}")
    
    # 获取最终状态
    print("\n5. 最终状态:")
    final_usage = manager.get_usage()
    print(f"   总分配：{final_usage['stats']['total_allocations']}")
    print(f"   总释放：{final_usage['stats']['total_deallocations']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
