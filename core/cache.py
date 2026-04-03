#!/usr/bin/env python3
"""
MOSS v5.5 - Multi-Level Cache System
多级缓存系统

核心功能:
- LRU 缓存
- 记忆检索加速
- 批量缓存
- 自动过期

Author: MOSS Project
Date: 2026-04-03
Version: 5.5.0-dev
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[timedelta] = None  # Time to live
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return datetime.now() > self.created_at + self.ttl
    
    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class LRUCache:
    """
    LRU (Least Recently Used) 缓存
    
    自动淘汰最少使用的条目
    """
    
    def __init__(self, max_size: int = 1000, 
                 default_ttl: Optional[timedelta] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        # 检查过期
        if entry.is_expired():
            self.delete(key)
            self.stats['misses'] += 1
            return None
        
        # 更新访问记录
        entry.touch()
        self.cache.move_to_end(key)
        
        self.stats['hits'] += 1
        return entry.value
    
    def set(self, key: str, value: Any, 
            ttl: Optional[timedelta] = None) -> bool:
        """设置缓存"""
        # 如果已存在，更新
        if key in self.cache:
            entry = self.cache[key]
            entry.value = value
            entry.ttl = ttl or self.default_ttl
            entry.touch()
            self.cache.move_to_end(key)
            return True
        
        # 如果满了，淘汰 LRU
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # 添加新条目
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl or self.default_ttl
        )
        self.cache[key] = entry
        
        self.stats['size'] = len(self.cache)
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            self.stats['size'] = len(self.cache)
            return True
        return False
    
    def _evict_lru(self):
        """淘汰最少使用的条目"""
        if self.cache:
            # OrderedDict 第一个是最旧的
            oldest_key = next(iter(self.cache))
            self.delete(oldest_key)
            self.stats['evictions'] += 1
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.stats['size'] = 0
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / max(total, 1)
        
        return {
            'stats': self.stats,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'max_size': self.max_size
        }


class MultiLevelCache:
    """
    多级缓存系统
    
    L1: 内存缓存 (快速，小容量)
    L2: 磁盘缓存 (较慢，大容量)
    """
    
    def __init__(self, l1_size: int = 100, l2_size: int = 10000,
                 storage_dir: str = "./cache_storage"):
        # L1 缓存
        self.l1 = LRUCache(max_size=l1_size)
        
        # L2 缓存 (简化为更大的内存缓存)
        self.l2 = LRUCache(max_size=l2_size)
        
        self.storage_dir = storage_dir
        
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存 (L1 → L2)"""
        self.stats['total_requests'] += 1
        
        # 先查 L1
        value = self.l1.get(key)
        if value is not None:
            self.stats['l1_hits'] += 1
            return value
        
        # 再查 L2
        value = self.l2.get(key)
        if value is not None:
            self.stats['l2_hits'] += 1
            # 提升到 L1
            self.l1.set(key, value)
            return value
        
        # 未命中
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, 
            level: int = 1, ttl: Optional[timedelta] = None) -> bool:
        """设置缓存"""
        if level == 1:
            return self.l1.set(key, value, ttl)
        elif level == 2:
            return self.l2.set(key, value, ttl)
        return False
    
    def get_or_compute(self, key: str, compute_func,
                       ttl: Optional[timedelta] = None) -> Any:
        """
        获取或计算缓存
        
        如果缓存不存在，调用 compute_func 计算并缓存
        """
        # 尝试获取
        value = self.get(key)
        if value is not None:
            return value
        
        # 计算并缓存
        value = compute_func()
        self.set(key, value, ttl=ttl)
        
        return value
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.stats['total_requests']
        l1_hit_rate = self.stats['l1_hits'] / max(total, 1)
        l2_hit_rate = self.stats['l2_hits'] / max(total, 1)
        overall_hit_rate = (
            (self.stats['l1_hits'] + self.stats['l2_hits']) / 
            max(total, 1)
        )
        
        return {
            'stats': self.stats,
            'l1_hit_rate': l1_hit_rate,
            'l2_hit_rate': l2_hit_rate,
            'overall_hit_rate': overall_hit_rate,
            'l1': self.l1.get_stats(),
            'l2': self.l2.get_stats()
        }


class CacheManager:
    """
    缓存管理器
    
    统一管理所有缓存
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        # 默认配置
        self.l1_size = config.get('l1_size', 100)
        self.l2_size = config.get('l2_size', 10000)
        self.default_ttl = timedelta(
            minutes=config.get('default_ttl_minutes', 60)
        )
        
        # 创建缓存
        self.cache = MultiLevelCache(
            l1_size=self.l1_size,
            l2_size=self.l2_size
        )
        
        # 缓存命名空间
        self.namespaces: Dict[str, MultiLevelCache] = {}
        
        self.stats = {
            'total_operations': 0,
            'cache_creations': 0
        }
    
    def get_cache(self, namespace: str = "default") -> MultiLevelCache:
        """获取命名空间缓存"""
        if namespace not in self.namespaces:
            self.namespaces[namespace] = MultiLevelCache(
                l1_size=self.l1_size,
                l2_size=self.l2_size
            )
            self.stats['cache_creations'] += 1
        
        self.stats['total_operations'] += 1
        return self.namespaces[namespace]
    
    def cache_result(self, namespace: str, key: str, 
                    compute_func, ttl: Optional[timedelta] = None):
        """缓存结果"""
        cache = self.get_cache(namespace)
        return cache.get_or_compute(key, compute_func, ttl)
    
    def invalidate(self, namespace: str, key: Optional[str] = None):
        """使缓存失效"""
        if namespace in self.namespaces:
            if key:
                self.namespaces[namespace].delete(key)
            else:
                self.namespaces[namespace].clear()
    
    def get_status(self) -> Dict:
        """获取缓存管理器状态"""
        namespace_stats = {}
        for ns, cache in self.namespaces.items():
            namespace_stats[ns] = cache.get_stats()
        
        return {
            'stats': self.stats,
            'namespaces': namespace_stats,
            'default_cache': self.cache.get_stats()
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.5 - Multi-Level Cache Test")
    print("=" * 60)
    
    # 创建缓存管理器
    manager = CacheManager({
        'l1_size': 5,
        'l2_size': 50,
        'default_ttl_minutes': 60
    })
    
    # 测试基本缓存
    print("\n1. 测试基本缓存...")
    cache = manager.get_cache("test")
    
    # 设置缓存
    cache.set("key1", "value1")
    cache.set("key2", {"data": "test"}, level=2)
    
    # 获取缓存
    val1 = cache.get("key1")
    val2 = cache.get("key2")
    print(f"   key1: {val1}")
    print(f"   key2: {val2}")
    
    # 测试 get_or_compute
    print("\n2. 测试 get_or_compute...")
    def expensive_compute():
        time.sleep(0.1)  # 模拟耗时计算
        return "computed_value"
    
    start = time.time()
    result1 = cache.get_or_compute("computed_key", expensive_compute)
    time1 = time.time() - start
    
    start = time.time()
    result2 = cache.get_or_compute("computed_key", expensive_compute)
    time2 = time.time() - start
    
    print(f"   首次计算：{result1} ({time1*1000:.1f}ms)")
    print(f"   缓存命中：{result2} ({time2*1000:.1f}ms)")
    print(f"   加速比：{time1/time2:.1f}x")
    
    # 测试命中率
    print("\n3. 测试缓存命中率...")
    for i in range(20):
        cache.set(f"key_{i}", f"value_{i}")
        cache.get(f"key_{i}")
    
    status = cache.get_stats()
    print(f"   L1 命中率：{status['l1_hit_rate']:.1%}")
    print(f"   L2 命中率：{status['l2_hit_rate']:.1%}")
    print(f"   总体命中率：{status['overall_hit_rate']:.1%}")
    
    # 获取状态
    print("\n4. 缓存管理器状态:")
    manager_status = manager.get_status()
    print(f"   命名空间数：{len(manager_status['namespaces'])}")
    print(f"   缓存创建数：{manager_status['stats']['cache_creations']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
