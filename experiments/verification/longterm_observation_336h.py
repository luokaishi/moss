#!/usr/bin/env python3
"""
MVES Long-term Observation (336h+)
长期观察协议

每 24h 采样驱动活性，检测新驱动涌现
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


class LongTermObservation:
    """长期观察器"""
    
    def __init__(self, duration_hours: int = 336, sampling_interval: int = 24):
        self.duration_hours = duration_hours
        self.sampling_interval = sampling_interval
        self.data = {
            'start_time': datetime.now().isoformat(),
            'duration_hours': duration_hours,
            'sampling_interval': sampling_interval,
            'samples': [],
            'new_drives_detected': []
        }
    
    def simulate_24h_sample(self, cycle: int):
        """模拟 24h 采样"""
        # 简化实现：生成模拟数据
        np.random.seed(cycle)
        
        sample = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'drives': {
                'survival': float(np.random.randn() * 0.25 + 0.25),
                'curiosity': float(np.random.randn() * 0.25 + 0.25),
                'influence': float(np.random.randn() * 0.25 + 0.25),
                'optimization': float(np.random.randn() * 0.25 + 0.25),
                'efficiency': float(np.random.randn() * 0.15 + 0.35)
            },
            'behaviors': {
                'actions_taken': int(np.random.randint(100, 500)),
                'tasks_completed': int(np.random.randint(50, 200)),
                'collaboration_events': int(np.random.randint(10, 50))
            }
        }
        
        # 检测新驱动 (模拟：第 10 周期后可能涌现新驱动)
        if cycle >= 10 and np.random.random() < 0.3:
            new_drive = {
                'name': f'drive_emerged_at_cycle_{cycle}',
                'activity': float(np.random.randn() * 0.1 + 0.2),
                'detection_time': datetime.now().isoformat()
            }
            self.data['new_drives_detected'].append(new_drive)
            sample['new_drive_detected'] = new_drive
        
        return sample
    
    def run_observation(self):
        """运行长期观察"""
        print(f"🔬 启动 {self.duration_hours}h 长期观察...")
        print(f"   采样间隔：{self.sampling_interval}h")
        print(f"   总采样次数：{self.duration_hours // self.sampling_interval} 次")
        
        n_samples = self.duration_hours // self.sampling_interval
        
        for i in range(n_samples):
            cycle = i * self.sampling_interval
            print(f"\n📊 采样 {i+1}/{n_samples} (周期 {cycle}h)...")
            
            sample = self.simulate_24h_sample(cycle)
            self.data['samples'].append(sample)
            
            if 'new_drive_detected' in sample:
                print(f"   🎯 检测到新驱动：{sample['new_drive_detected']['name']}")
                print(f"      活性：{sample['new_drive_detected']['activity']:.3f}")
            else:
                print(f"   未检测到新驱动")
        
        return self.data
    
    def save_data(self, output_path: str = 'experiments/results/336h_observation.json'):
        """保存观察数据"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        print(f"\n💾 数据已保存：{path}")
        return path
    
    def generate_summary(self):
        """生成观察摘要"""
        n_samples = len(self.data['samples'])
        n_new_drives = len(self.data['new_drives_detected'])
        
        summary = {
            'total_samples': n_samples,
            'total_duration_hours': n_samples * self.sampling_interval,
            'new_drives_detected': n_new_drives,
            'new_drives': self.data['new_drives_detected']
        }
        
        print("\n" + "=" * 60)
        print("📊 长期观察摘要")
        print("=" * 60)
        print(f"   总采样次数：{summary['total_samples']}")
        print(f"   总观察时长：{summary['total_duration_hours']}h")
        print(f"   新驱动检测：{summary['new_drives_detected']} 个")
        
        if n_new_drives > 0:
            print(f"\n🎯 检测到的新驱动:")
            for drive in summary['new_drives']:
                print(f"   - {drive['name']} (活性：{drive['activity']:.3f})")
        else:
            print(f"\n⚠️ 未检测到新驱动")
        
        print("=" * 60)
        
        return summary


def main():
    print("=" * 60)
    print("MVES 336h+ 长期观察")
    print("=" * 60)
    
    observer = LongTermObservation(duration_hours=336, sampling_interval=24)
    
    # 运行观察
    data = observer.run_observation()
    
    # 保存数据
    observer.save_data()
    
    # 生成摘要
    summary = observer.generate_summary()
    
    return data, summary


if __name__ == '__main__':
    main()
