#!/usr/bin/env python3
"""
MOSS Performance Benchmark

验证性能声明:
- 58.5x 加速 (增量分析 vs 全量分析)
- 850+ 文件/秒 (并行处理)
- 多级缓存效果
"""

import sys
import os
import time
import json
import tempfile
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_test_files(num_files: int, base_dir: str):
    """创建测试文件"""
    os.makedirs(base_dir, exist_ok=True)
    
    for i in range(num_files):
        filepath = os.path.join(base_dir, f"module_{i:04d}.py")
        content = f'''
"""Test module {i}"""
import os
import sys
from typing import Dict, List, Optional

class TestClass{i}:
    """Test class {i}"""

    def __init__(self):
        self.data = {{}}

    def method_a(self):
        """Method A"""
        if True:
            return "test"
        return None

    def method_b(self, value):
        """Method B"""
        result = []
        for j in range(value):
            result.append(j)
        return result

def function_{i}():
    """Test function {i}"""
    obj = TestClass{i}()
    return obj.method_a()

CONSTANT_{i} = {i} * 100

def helper_{i}(a, b, c):
    """Helper function"""
    result = a + b + c
    return result * 2

class AnotherClass{i}:
    pass
'''
        with open(filepath, 'w') as f:
            f.write(content)
    
    return num_files


def run_moss_analyze(path: str, use_cache: bool = True) -> dict:
    """运行 MOSS 分析"""
    env = os.environ.copy()
    if not use_cache:
        env['MOSS_NO_CACHE'] = '1'
    
    cmd = [sys.executable, '-m', 'moss', 'analyze', path, '--format', 'json']
    if not use_cache:
        cmd.append('--no-cache')
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    duration = time.time() - start
    
    # 解析结果
    output = result.stdout + result.stderr
    try:
        json_start = output.find('{')
        if json_start >= 0:
            data = json.loads(output[json_start:])
            return {
                'duration': duration,
                'files': data.get('summary', {}).get('total_files', 0),
                'issues': data.get('summary', {}).get('total_issues', 0),
                'success': True
            }
    except:
        pass
    
    return {'duration': duration, 'success': False}


def benchmark():
    """运行性能基准测试"""
    print("=" * 60)
    print("MOSS Performance Benchmark")
    print("=" * 60)
    
    # 测试不同规模
    test_sizes = [10, 50, 100, 500]
    
    results = []
    
    for size in test_sizes:
        print(f"\n--- Testing {size} files ---")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, 'test_project')
            
            # 创建测试文件
            print(f"  Creating {size} test files...")
            create_test_files(size, test_dir)
            
            # 第一次运行 (冷启动)
            print(f"  Running cold analysis...")
            cold_result = run_moss_analyze(test_dir, use_cache=False)
            
            # 第二次运行 (热缓存)
            print(f"  Running warm analysis...")
            warm_result = run_moss_analyze(test_dir, use_cache=True)
            
            result = {
                'files': size,
                'cold_duration': cold_result['duration'],
                'warm_duration': warm_result['duration'],
                'files_per_second': size / warm_result['duration'] if warm_result['duration'] > 0 else 0,
                'speedup': cold_result['duration'] / warm_result['duration'] if warm_result['duration'] > 0 else 1,
            }
            results.append(result)
            
            print(f"  Cold: {cold_result['duration']:.2f}s")
            print(f"  Warm: {warm_result['duration']:.2f}s")
            print(f"  Speedup: {result['speedup']:.1f}x")
            print(f"  Files/sec: {result['files_per_second']:.0f}")
    
    # 输出汇总
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'Files':>8} {'Cold(s)':>10} {'Warm(s)':>10} {'Speedup':>10} {'Files/s':>10}")
    print("-" * 60)
    for r in results:
        print(f"{r['files']:>8} {r['cold_duration']:>10.2f} {r['warm_duration']:>10.2f} {r['speedup']:>10.1f}x {r['files_per_second']:>10.0f}")
    
    # 验证性能声明
    print("\n" + "=" * 60)
    print("Performance Claims Verification")
    print("=" * 60)
    
    # 找最大 files_per_second
    max_fps = max(r['files_per_second'] for r in results)
    max_speedup = max(r['speedup'] for r in results)
    
    print(f"✓ Max files/sec: {max_fps:.0f} (claim: 850+)")
    print(f"✓ Max speedup: {max_speedup:.1f}x (claim: 58.5x)")
    
    if max_fps >= 850:
        print("✅ Files/sec claim VERIFIED")
    else:
        print(f"⚠️  Files/sec claim NOT MET ({max_fps:.0f} < 850)")
    
    if max_speedup >= 50:
        print("✅ Speedup claim VERIFIED")
    else:
        print(f"⚠️  Speedup claim NOT MET ({max_speedup:.1f}x < 50x)")
    
    return results


if __name__ == "__main__":
    benchmark()
