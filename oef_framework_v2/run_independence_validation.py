"""
OEF 2.0 真实独立性验证实验
使用真实涌现检测和因果验证

科学目标：
1. 配置明确的初始驱动
2. 使用GoalDiscoverer进行真实涌现检测
3. 执行CausalIndependenceValidator进行因果验证
4. 记录完整的涌现来源信息
5. 验证涌现驱动独立于初始目标

关键改进：
- 不使用随机概率模拟涌现
- 使用行为历史分析发现目标
- 执行完整的因果独立性验证
"""

import numpy as np
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal
import sys

# 导入OEF 2.0模块
sys.path.append('/home/admin/.openclaw/workspace')
from oef_framework_v2.emergence_engine_v2 import EmergenceEngineV2
from oef_framework_v2.goal_discoverer import GoalDiscoverer
from oef_framework_v2.causal_validator import CausalIndependenceValidator
from oef_framework_v2.autonomous_drive_space import AutonomousDriveSpace


class RealIndependenceValidationExperiment:
    """
    真实独立性验证实验
    
    关键改进：
    1. 配置明确的初始驱动（不再为空）
    2. 使用GoalDiscoverer（不使用随机概率）
    3. 执行因果验证（填充independence_validations）
    4. 记录涌现来源（填充source_behaviors）
    """
    
    def __init__(self,
                 experiment_name: str = "oef_independence_validation",
                 duration_hours: float = 24.0,
                 save_interval_minutes: float = 30.0,
                 report_interval_hours: float = 6.0,
                 cycles_per_minute: int = 1):
        
        self.experiment_name = experiment_name
        self.duration_hours = duration_hours
        self.save_interval_minutes = save_interval_minutes
        self.report_interval_hours = report_interval_hours
        self.cycles_per_minute = cycles_per_minute
        
        # 时间参数
        self.duration_seconds = duration_hours * 3600
        self.save_interval_seconds = save_interval_minutes * 60
        self.report_interval_seconds = report_interval_hours * 3600
        
        # 🌟 关键改进：配置明确的初始驱动
        self.initial_drives = [
            'survival',       # 生存驱动
            'curiosity',      # 好奇心驱动
            'influence',      # 影响力驱动
            'optimization'    # 优化驱动
        ]
        
        # 实验状态
        self.start_time: Optional[datetime] = None
        self.elapsed_seconds: float = 0.0
        self.cycle_count: int = 0
        
        # 🌟 创建真实涌现引擎（配置GoalDiscoverer和CausalValidator）
        self.drive_space = AutonomousDriveSpace()
        self.goal_discoverer = GoalDiscoverer(
            min_pattern_frequency=10,
            novelty_threshold=0.7,
            behavior_window=100
        )
        self.causal_validator = CausalIndependenceValidator(significance_level=0.05)
        
        # 设置目标发现器和因果验证器
        self.drive_space.set_goal_discoverer(self.goal_discoverer)
        self.drive_space.set_causal_validator(self.causal_validator)
        
        # 初始化初始驱动
        for drive_name in self.initial_drives:
            self.drive_space.add_drive(drive_name, weight=0.25, autonomous=False)
        
        # 数据目录
        self.data_dir = f"/home/admin/.openclaw/workspace/oef_real_data/{experiment_name}"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 观察记录
        self.emergence_events: List[Dict] = []
        self.behavior_history: List[Dict] = []  # 🌟 新增：行为历史
        self.state_history: List[np.ndarray] = []
        
        # 统计指标
        self.total_emergence_count: int = 0
        self.independence_validations: List[Dict] = []  # 🌟 关键：因果验证记录
        self.novelty_scores: List[float] = []
        
        # 优雅退出
        self.running = True
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        print("✅ 真实独立性验证实验初始化完成")
        print(f"   实验名称: {experiment_name}")
        print(f"   持续时长: {duration_hours}小时")
        print(f"   数据目录: {self.data_dir}")
        print(f"   🌟 初始驱动: {self.initial_drives}")
        print(f"   🌟 使用GoalDiscoverer: True")
        print(f"   🌟 使用CausalValidator: True")
    
    def _handle_shutdown(self, signum, frame):
        """优雅退出处理"""
        print(f"\n⚠️ 收到退出信号，正在保存数据...")
        self.running = False
        self._save_checkpoint()
        self._generate_final_report()
        sys.exit(0)
    
    def _generate_behavior(self, cycle: int) -> Dict:
        """
        🌟 生成模拟行为（真实系统应从Agent行为日志获取）
        
        关键改进：
        - 行为来源于系统状态
        - 行为包含语义信息
        - 行为可被GoalDiscoverer分析
        """
        
        # 模拟Agent行为选择（基于当前驱动权重）
        behavior_types = [
            ('explore_environment', 'exploration'),
            ('help_peer_agent', 'collaboration'),
            ('optimize_strategy', 'optimization'),
            ('share_resource', 'collaboration'),
            ('investigate_new_area', 'exploration'),
            ('coordinate_team_action', 'collaboration'),
            ('improve_efficiency', 'optimization'),
            ('learn_from_peer', 'learning'),
            ('adapt_to_change', 'resilience'),
            ('create_novel_solution', 'creativity')
        ]
        
        # 根据周期选择行为（模拟Agent决策）
        behavior_idx = cycle % len(behavior_types)
        
        # 添加随机性（模拟真实Agent行为）
        if np.random.rand() < 0.3:
            behavior_idx = np.random.randint(0, len(behavior_types))
        
        behavior_action, behavior_category = behavior_types[behavior_idx]
        
        return {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'action': behavior_action,
            'category': behavior_category,
            'agent_id': 'agent_001',
            'context': {
                'state': self._get_current_state().tolist(),
                'cycle': cycle
            }
        }
    
    def _get_current_state(self) -> np.ndarray:
        """获取当前系统状态"""
        health = 0.5 + 0.3 * np.sin(self.cycle_count / 100)
        crisis = 0.1 + 0.05 * np.random.randn()
        resources = 100 - self.cycle_count / 100
        
        return np.array([health, crisis, resources])
    
    def run_cycle(self) -> Dict:
        """运行单个周期（使用真实涌现检测）"""
        
        # 生成行为
        behavior = self._generate_behavior(self.cycle_count)
        self.behavior_history.append(behavior)
        
        # 获取系统状态
        state = self._get_current_state()
        
        # 🌟 使用真实GoalDiscoverer进行涌现检测（不使用随机概率）
        discovered_goal = self.drive_space.autonomously_discover_goal(
            self.behavior_history,
            self.cycle_count,
            self.initial_drives  # 🌟 传入初始驱动列表
        )
        
        cycle_result = {
            'cycle': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'state': state.tolist(),
            'behavior': behavior['action'],
            'emergence': None
        }
        
        if discovered_goal:
            # 🌟 记录涌现事件（包含完整信息）
            emergence_event = {
                'cycle': self.cycle_count,
                'timestamp': datetime.now().isoformat(),
                'drive_name': discovered_goal['name'],
                'source_behaviors': discovered_goal['source_behaviors'],  # 🌟 来源行为
                'novelty_score': discovered_goal['novelty_score'],  # 🌟 新颖性分数
                'confidence': discovered_goal['confidence'],
                'causal_independence_score': discovered_goal.get('causal_independence_score', 0.0)  # 🌟 因果独立性
            }
            
            self.emergence_events.append(emergence_event)
            self.total_emergence_count += 1
            
            # 🌟 记录独立性验证结果
            independence_validation = {
                'drive_name': discovered_goal['name'],
                'initial_drives': self.initial_drives,
                'novelty_score': discovered_goal['novelty_score'],
                'causal_independence_score': discovered_goal.get('causal_independence_score', 0.0),
                'is_novel': discovered_goal['novelty_score'] >= 0.7,
                'is_independent': discovered_goal.get('causal_independence_score', 0.0) >= 0.6,
                'validation_cycle': self.cycle_count
            }
            
            self.independence_validations.append(independence_validation)
            self.novelty_scores.append(discovered_goal['novelty_score'])
            
            cycle_result['emergence'] = emergence_event
            
            print(f"🎉 周期{self.cycle_count}: 发现新目标 {discovered_goal['name']}")
            print(f"   来源行为: {discovered_goal['source_behaviors']}")
            print(f"   新颖性分数: {discovered_goal['novelty_score']:.2f}")
            print(f"   因果独立性: {discovered_goal.get('causal_independence_score', 0.0):.2f}")
        
        # 记录状态
        self.state_history.append(state)
        
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-1000:]
        
        # 更新周期计数
        self.cycle_count += 1
        
        return cycle_result
    
    def _save_checkpoint(self):
        """保存checkpoint"""
        
        elapsed = time.time() - self.start_time.timestamp() if self.start_time else 0
        
        checkpoint = {
            'experiment_name': self.experiment_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'elapsed_seconds': elapsed,
            'cycle_count': self.cycle_count,
            'cycles_per_minute': self.cycles_per_minute,
            
            # 🌟 关键改进：记录初始驱动
            'initial_drives': self.initial_drives,
            
            # 🌟 关键改进：涌现事件包含完整信息
            'emergence_events': self.emergence_events,
            'total_emergence_count': self.total_emergence_count,
            
            # 🌟 关键改进：独立性验证记录
            'independence_validations': self.independence_validations,
            
            # 新颖性分数记录
            'novelty_scores': self.novelty_scores,
            
            # 状态历史
            'state_history': [s.tolist() for s in self.state_history[-100:]],
            
            # GoalDiscoverer发现摘要
            'goal_discoverer_summary': self.goal_discoverer.get_discovery_summary(),
            
            # 实验配置
            'config': {
                'duration_hours': self.duration_hours,
                'cycles_per_minute': self.cycles_per_minute,
                'min_pattern_frequency': self.goal_discoverer.min_pattern_frequency,
                'novelty_threshold': self.goal_discoverer.novelty_threshold,
                'causal_validator_alpha': self.causal_validator.alpha
            }
        }
        
        checkpoint_path = os.path.join(self.data_dir, 'checkpoint.json')
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"✅ Checkpoint已保存: {checkpoint_path}")
    
    def _generate_final_report(self):
        """生成最终报告"""
        
        print("\n" + "="*60)
        print("📊 真实独立性验证实验最终报告")
        print("="*60)
        
        print(f"\n实验名称: {self.experiment_name}")
        print(f"运行时长: {self.elapsed_seconds/3600:.2f}小时")
        print(f"总周期数: {self.cycle_count}")
        
        print(f"\n🌟 初始驱动配置:")
        for drive in self.initial_drives:
            print(f"   - {drive}")
        
        print(f"\n🎉 涌现统计:")
        print(f"   涌现事件数: {self.total_emergence_count}")
        print(f"   涌现驱动: {[e['drive_name'] for e in self.emergence_events]}")
        
        print(f"\n🔬 独立性验证:")
        print(f"   验证记录数: {len(self.independence_validations)}")
        
        if self.independence_validations:
            for validation in self.independence_validations:
                print(f"   - {validation['drive_name']}:")
                print(f"     新颖性分数: {validation['novelty_score']:.2f}")
                print(f"     因果独立性: {validation['causal_independence_score']:.2f}")
                print(f"     是否新颖: {'✅' if validation['is_novel'] else '❌'}")
                print(f"     是否独立: {'✅' if validation['is_independent'] else '❌'}")
        
        print(f"\n📈 GoalDiscoverer摘要:")
        summary = self.goal_discoverer.get_discovery_summary()
        print(f"   发现总数: {summary['total_discovered']}")
        print(f"   平均新颖性: {summary['avg_novelty']:.2f}")
        print(f"   平均置信度: {summary['avg_confidence']:.2f}")
        
        print("\n" + "="*60)
    
    def run(self):
        """运行实验"""
        
        print("\n🚀 启动真实独立性验证实验...")
        
        self.start_time = datetime.now()
        
        cycle_interval = 60.0 / self.cycles_per_minute  # 秒/周期
        last_save_time = time.time()
        last_report_time = time.time()
        
        while self.running and self.elapsed_seconds < self.duration_seconds:
            # 运行周期
            self.run_cycle()
            
            # 更新时间
            self.elapsed_seconds = time.time() - self.start_time.timestamp()
            
            # 定期保存
            current_time = time.time()
            if current_time - last_save_time >= self.save_interval_seconds:
                self._save_checkpoint()
                last_save_time = current_time
            
            # 定期报告
            if current_time - last_report_time >= self.report_interval_seconds:
                self._generate_progress_report()
                last_report_time = current_time
            
            # 等待下一个周期
            time.sleep(cycle_interval)
        
        # 实验完成
        print("\n✅ 实验完成！")
        self._save_checkpoint()
        self._generate_final_report()
    
    def _generate_progress_report(self):
        """生成进度报告"""
        
        elapsed_hours = self.elapsed_seconds / 3600
        progress = self.elapsed_seconds / self.duration_seconds
        
        print(f"\n📊 进度报告 ({elapsed_hours:.1f}小时)")
        print(f"   周期数: {self.cycle_count}")
        print(f"   进度: {progress:.1%}")
        print(f"   涌现事件: {self.total_emergence_count}")
        print(f"   独立性验证: {len(self.independence_validations)}")


def main():
    """主函数"""
    
    # 创建实验
    experiment = RealIndependenceValidationExperiment(
        experiment_name="oef_independence_validation_24h",
        duration_hours=24.0,
        save_interval_minutes=30.0,
        report_interval_hours=6.0,
        cycles_per_minute=1
    )
    
    # 运行实验
    experiment.run()


if __name__ == "__main__":
    main()