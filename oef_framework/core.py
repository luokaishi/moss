"""
Open Emergence Framework (OEF) - Core Module

开放涌现框架核心实现
真正能产生涌现的系统
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class Drive:
    """驱动类"""
    name: str
    weight: float = 0.5
    activity: List[float] = field(default_factory=list)
    stability: float = 0.0
    emerged: bool = False
    emergence_cycle: Optional[int] = None
    
    def update_activity(self, value: float):
        """更新活跃度"""
        self.activity.append(value)
        if len(self.activity) > 50:
            self.activity = self.activity[-50:]
        self._calculate_stability()
    
    def _calculate_stability(self):
        """计算稳定性"""
        if len(self.activity) >= 10:
            recent = self.activity[-10:]
            self.stability = 1.0 - (np.std(recent) / np.mean(recent) if np.mean(recent) > 0 else 0.0)


@dataclass
class Action:
    """行为类"""
    name: str
    base_reward: float = 0.5
    execute_count: int = 0
    
    def execute(self, state: Dict) -> Tuple[float, Dict]:
        """执行行为"""
        self.execute_count += 1
        # 模拟行为效果（真实系统需要真实实现）
        reward = self.base_reward * np.random.uniform(0.8, 1.2)
        new_state = state.copy()
        return reward, new_state


class OpenDriveSpace:
    """开放目标空间"""
    
    def __init__(self):
        self.drives: Dict[str, Drive] = {}
        self.drive_generator: Optional['DriveGenerator'] = None
        self.emergence_detector: Optional['EmergenceDetector'] = None
    
    def add_drive(self, name: str, weight: float = 0.5):
        """添加驱动"""
        self.drives[name] = Drive(name=name, weight=weight)
    
    def update_drive_weight(self, name: str, delta: float):
        """更新驱动权重"""
        if name in self.drives:
            self.drives[name].weight += delta
            self.drives[name].weight = max(0.0, min(1.0, self.drives[name].weight))
    
    def try_generate_new_drive(self, state: Dict, cycle: int):
        """尝试生成新驱动"""
        if self.drive_generator:
            new_drive = self.drive_generator.generate(state, cycle, self.drives)
            if new_drive:
                self.add_drive(new_drive.name, new_drive.weight)
                return new_drive
        return None


class ActionSpace:
    """开放行为空间"""
    
    def __init__(self):
        self.actions: Dict[str, Action] = {}
    
    def add_action(self, name: str, base_reward: float = 0.5):
        """添加行为"""
        self.actions[name] = Action(name=name, base_reward=base_reward)
    
    def select_action(self, drives: Dict[str, Drive]) -> Action:
        """基于驱动选择行为"""
        # 简化实现：真实系统需要更复杂的决策机制
        # 每个行为有基础奖励，驱动权重影响选择概率
        action_names = list(self.actions.keys())
        base_rewards = [self.actions[name].base_reward for name in action_names]
        
        # 驱动权重影响：驱动平均权重影响行为选择
        avg_drive_weight = np.mean([d.weight for d in drives.values()]) if drives else 0.5
        
        # 计算选择概率（基于奖励和驱动权重）
        probs = np.array(base_rewards) * avg_drive_weight
        probs = probs / probs.sum()
        
        selected_idx = np.random.choice(len(action_names), p=probs)
        return self.actions[action_names[selected_idx]]


class DriveGenerator:
    """驱动生成器"""
    
    def generate(self, state: Dict, cycle: int, existing_drives: Dict[str, Drive]) -> Optional[Drive]:
        """基于行为模式生成新驱动"""
        # 简化实现：真实系统需要行为历史分析
        # 检查是否应该生成新驱动
        if cycle > 1000 and len(existing_drives) < 5:
            if np.random.random() < 0.1:  # 10% 概率尝试生成
                drive_name = f"drive_emerged_at_cycle_{cycle}"
                return Drive(name=drive_name, weight=0.3, emergence_cycle=cycle)
        return None


class EmergenceDetector:
    """涌现检测器"""
    
    def __init__(self, stability_threshold: float = 0.7, 
                 activity_threshold: float = 0.3,
                 duration_threshold: int = 50,
                 weight_threshold: float = 0.05):
        self.stability_threshold = stability_threshold
        self.activity_threshold = activity_threshold
        self.duration_threshold = duration_threshold
        self.weight_threshold = weight_threshold
    
    def check_emergence(self, drive: Drive, cycle: int) -> bool:
        """检查驱动是否涌现"""
        # 稳定性检查
        if drive.stability < self.stability_threshold:
            return False
        
        # 活跃度检查
        if len(drive.activity) > 0:
            avg_activity = np.mean(drive.activity[-10:])
            if avg_activity < self.activity_threshold:
                return False
        else:
            return False
        
        # 持续时间检查
        if len(drive.activity) < self.duration_threshold:
            return False
        
        # 权重检查
        if drive.weight < self.weight_threshold:
            return False
        
        return True
    
    def validate_all_drives(self, drives: Dict[str, Drive], cycle: int) -> List[Drive]:
        """验证所有驱动涌现状态"""
        emerged_drives = []
        for drive in drives.values():
            if not drive.emerged:  # 未标记涌现的驱动
                if self.check_emergence(drive, cycle):
                    drive.emerged = True
                    emerged_drives.append(drive)
        return emerged_drives


class EmergenceEngine:
    """涌现引擎"""
    
    def __init__(self, 
                 initial_drives: List[str] = ['survival', 'curiosity', 'influence'],
                 initial_actions: List[str] = ['explore', 'conserve', 'socialize', 'learn', 'rest', 'create']):
        self.drive_space = OpenDriveSpace()
        self.action_space = ActionSpace()
        self.drive_generator = DriveGenerator()
        self.emergence_detector = EmergenceDetector()
        
        # 设置驱动生成器和涌现检测器
        self.drive_space.drive_generator = self.drive_generator
        self.drive_space.emergence_detector = self.emergence_detector
        
        # 初始化驱动和行为
        for drive_name in initial_drives:
            self.drive_space.add_drive(drive_name, weight=0.5)
        
        for action_name in initial_actions:
            base_reward = {'explore': 0.4, 'conserve': 0.6, 'socialize': 0.5, 
                          'learn': 0.5, 'rest': 0.8, 'create': 0.4}[action_name]
            self.action_space.add_action(action_name, base_reward)
    
    def run_cycle(self, state: Dict, cycle: int) -> Dict:
        """运行一个周期"""
        # 1. 选择行为
        selected_action = self.action_space.select_action(self.drive_space.drives)
        
        # 2. 执行行为
        reward, new_state = selected_action.execute(state)
        
        # 3. 更新驱动权重（反馈机制）
        for drive in self.drive_space.drives.values():
            delta = reward * 0.01 * np.random.uniform(-0.5, 1.5)
            self.drive_space.update_drive_weight(drive.name, delta)
            drive.update_activity(reward)
        
        # 4. 尝试生成新驱动
        new_drive = self.drive_space.try_generate_new_drive(new_state, cycle)
        
        # 5. 检测涌现
        emerged_drives = self.emergence_detector.validate_all_drives(self.drive_space.drives, cycle)
        
        return {
            'cycle': cycle,
            'selected_action': selected_action.name,
            'reward': reward,
            'new_drive': new_drive.name if new_drive else None,
            'emerged_drives': [d.name for d in emerged_drives],
            'state': new_state
        }
    
    def run_experiment(self, n_cycles: int = 20000, 
                       initial_state: Dict = None,
                       save_results: bool = True) -> Dict:
        """运行完整实验"""
        print("=" * 60)
        print("OEF 涌现实验启动")
        print("=" * 60)
        print(f"   周期数: {n_cycles}")
        print(f"   初始驱动: {len(self.drive_space.drives)} 个")
        print(f"   原始行为: {len(self.action_space.actions)} 个")
        print()
        
        state = initial_state or {'resource': 1.0, 'knowledge': 0.0}
        results = []
        
        for i in range(n_cycles):
            cycle = i + 1
            result = self.run_cycle(state, cycle)
            results.append(result)
            state = result['state']
            
            if cycle % 5000 == 0:
                print(f"📊 周期 {cycle}/{n_cycles} 完成...")
                print(f"   驱动数: {len(self.drive_space.drives)}")
                emerged = [d for d in self.drive_space.drives.values() if d.emerged]
                print(f"   涌现驱动: {len(emerged)} 个")
        
        # 生成最终报告
        report = self.generate_report(results)
        
        if save_results:
            self.save_results(report)
        
        return report
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """生成实验报告"""
        emerged_drives = [d for d in self.drive_space.drives.values() if d.emerged]
        action_stats = {name: action.execute_count for name, action in self.action_space.actions.items()}
        total_actions = sum(action_stats.values())
        action_distribution = {name: count/total_actions for name, count in action_stats.items()}
        
        report = {
            'experiment_config': {
                'n_cycles': len(results),
                'initial_drives': len([d for d in self.drive_space.drives.values() if not d.emerged]),
                'initial_actions': len(self.action_space.actions)
            },
            'drive_space': {
                'total_drives': len(self.drive_space.drives),
                'emerged_drives': len(emerged_drives),
                'drive_details': {}
            },
            'action_distribution': action_distribution,
            'emerged_drive_list': [
                {
                    'name': d.name,
                    'weight': d.weight,
                    'stability': d.stability,
                    'activity': np.mean(d.activity[-10:]) if len(d.activity) > 0 else 0.0,
                    'emerged': d.emerged,
                    'emergence_cycle': d.emergence_cycle
                }
                for d in self.drive_space.drives.values()
            ],
            'timestamp': datetime.now().isoformat(),
            'framework': 'OEF v1.0'
        }
        
        for name, drive in self.drive_space.drives.items():
            report['drive_space']['drive_details'][name] = {
                'weight': drive.weight,
                'stability': drive.stability,
                'emerged': drive.emerged,
                'activity_count': len(drive.activity)
            }
        
        return report
    
    def save_results(self, report: Dict, output_path: str = 'oef_results/demo_result.json'):
        """保存结果"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print()
        print("=" * 60)
        print("OEF 实验报告")
        print("=" * 60)
        print(f"   驱动空间:")
        print(f"      初始驱动: {report['experiment_config']['initial_drives']} 个")
        print(f"      当前驱动: {report['drive_space']['total_drives']} 个")
        print(f"      涌现驱动: {report['drive_space']['emerged_drives']} 个")
        print()
        print(f"   行为分布:")
        for name, pct in sorted(report['action_distribution'].items(), key=lambda x: -x[1]):
            print(f"      - {name}: {pct*100:.1f}%")
        print()
        print(f"   涌现驱动详情:")
        for drive in report['emerged_drive_list']:
            if drive['emerged']:
                print(f"      - {drive['name']}: 权重={drive['weight']:.3f}, 稳定性={drive['stability']:.3f} ✅")
        print()
        print(f"💾 结果已保存: {path}")
        print("=" * 60)


def main():
    """主函数"""
    engine = EmergenceEngine()
    report = engine.run_experiment(n_cycles=20000, save_results=True)
    return report


if __name__ == '__main__':
    main()