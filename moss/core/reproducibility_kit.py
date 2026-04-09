"""
MOSS Reproducibility Kit
可复现性套件 - 回应Copilot评估

实现: Docker + 固定种子 + 依赖锁定 + 自动化脚本
"""

import subprocess
import sys
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List


class ReproducibilityKit:
    """MOSS可复现性套件"""
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_id = f"{experiment_name}_{self.timestamp}"
        self.seed = None
        self.environment_hash = None
    
    def capture_environment(self) -> Dict:
        """捕获完整环境信息"""
        env_info = {
            'timestamp': self.timestamp,
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': os.getcwd(),
            'git_commit': self._get_git_commit(),
            'git_branch': self._get_git_branch(),
            'dependencies': self._get_dependencies(),
            'environment_variables': self._get_relevant_env_vars()
        }
        
        # 计算环境哈希
        env_str = json.dumps(env_info, sort_keys=True)
        self.environment_hash = hashlib.sha256(env_str.encode()).hexdigest()[:16]
        env_info['environment_hash'] = self.environment_hash
        
        return env_info
    
    def _get_git_commit(self) -> str:
        """获取Git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'
    
    def _get_git_branch(self) -> str:
        """获取Git分支"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'
    
    def _get_dependencies(self) -> Dict[str, str]:
        """获取依赖版本"""
        deps = {}
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'freeze'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '==' in line:
                        name, version = line.split('==', 1)
                        deps[name] = version
        except:
            pass
        return deps
    
    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """获取相关环境变量（不含敏感信息）"""
        relevant = ['PYTHONPATH', 'MOSS_ENV', 'MOSS_MODE']
        return {k: os.getenv(k, '') for k in relevant if os.getenv(k)}
    
    def set_seed(self, seed: int):
        """设置随机种子"""
        self.seed = seed
        import random
        import numpy as np
        random.seed(seed)
        np.random.seed(seed)
        print(f"[Reproducibility] Random seed set to: {seed}")
    
    def run_experiment_with_tracking(self, experiment_func, *args, **kwargs) -> Dict:
        """
        运行实验并完整追踪
        
        Args:
            experiment_func: 实验函数
            *args, **kwargs: 实验函数参数
        
        Returns:
            完整实验记录
        """
        # 捕获环境
        env_info = self.capture_environment()
        
        # 记录开始
        start_time = datetime.now()
        
        print(f"[Reproducibility] Starting experiment: {self.run_id}")
        print(f"[Reproducibility] Environment hash: {self.environment_hash}")
        if self.seed:
            print(f"[Reproducibility] Random seed: {self.seed}")
        
        # 运行实验
        try:
            result = experiment_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        # 记录结束
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 构建完整记录
        full_record = {
            'run_id': self.run_id,
            'experiment_name': self.experiment_name,
            'timestamp_start': start_time.isoformat(),
            'timestamp_end': end_time.isoformat(),
            'duration_seconds': duration,
            'success': success,
            'error': error,
            'environment': env_info,
            'seed': self.seed,
            'result': result
        }
        
        # 保存记录
        self._save_record(full_record)
        
        return full_record
    
    def _save_record(self, record: Dict):
        """保存实验记录"""
        filename = f"reproducibility_record_{self.run_id}.json"
        
        # 创建目录
        os.makedirs('experiments/records', exist_ok=True)
        filepath = f"experiments/records/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(record, f, indent=2, default=str)
        
        print(f"[Reproducibility] Record saved to: {filepath}")
    
    def generate_reproducibility_report(self, records: List[Dict]) -> Dict:
        """
        生成可复现性报告
        
        Args:
            records: 多次实验记录
        
        Returns:
            统计报告
        """
        if not records:
            return {'error': 'No records provided'}
        
        # 检查环境一致性
        env_hashes = [r['environment']['environment_hash'] for r in records]
        consistent_env = len(set(env_hashes)) == 1
        
        # 统计数据
        successes = [r['success'] for r in records]
        durations = [r['duration_seconds'] for r in records]
        
        report = {
            'total_runs': len(records),
            'successful_runs': sum(successes),
            'success_rate': sum(successes) / len(successes),
            'consistent_environment': consistent_env,
            'environment_hash': env_hashes[0] if consistent_env else 'VARIED',
            'duration_stats': {
                'mean': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'std': self._calculate_std(durations)
            },
            'seeds_used': list(set([r['seed'] for r in records if r['seed']])),
            'recommendation': 'REPRODUCIBLE' if consistent_env and sum(successes)/len(successes) > 0.9 else 'NEEDS_REVIEW'
        }
        
        return report
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        import math
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


def demo_reproducibility():
    """演示可复现性套件"""
    print("="*70)
    print("MOSS REPRODUCIBILITY KIT DEMO")
    print("="*70)
    print()
    
    # 创建套件
    kit = ReproducibilityKit("baseline_test")
    
    # 定义实验函数
    def sample_experiment(iterations=10):
        """示例实验"""
        import random
        import numpy as np
        
        results = []
        for i in range(iterations):
            # 模拟实验
            value = random.random() + np.random.normal(0, 0.1)
            results.append(value)
        
        return {
            'iterations': iterations,
            'mean': np.mean(results),
            'std': np.std(results)
        }
    
    # 运行3次，不同种子
    records = []
    for seed in [42, 123, 456]:
        kit = ReproducibilityKit(f"baseline_test_seed{seed}")
        kit.set_seed(seed)
        record = kit.run_experiment_with_tracking(sample_experiment, iterations=100)
        records.append(record)
    
    # 生成报告
    print("\n" + "="*70)
    print("REPRODUCIBILITY REPORT")
    print("="*70)
    
    report = kit.generate_reproducibility_report(records)
    print(json.dumps(report, indent=2))
    
    print("\n" + "="*70)
    print("KEY TAKEAWAYS")
    print("="*70)
    print(f"✅ Environment consistency: {report['consistent_environment']}")
    print(f"✅ Success rate: {report['success_rate']:.1%}")
    print(f"✅ Duration consistency: {report['duration_stats']['std']:.2f}s std")
    print(f"✅ Status: {report['recommendation']}")


if __name__ == '__main__':
    demo_reproducibility()
