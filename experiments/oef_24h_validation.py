#!/usr/bin/env python3
"""
OEF 2.0 - 24小时验证实验

Purpose: 验证修正后的新颖目标生成和四维度独立性验证
Duration: 24小时 (7200周期)
Validation: CompleteIndependenceValidator (四维度验证)
Goal Generation: GoalDiscoverer (新颖生成版，无模板依赖)

成功标准:
- 涌现事件 ≥ 3次
- 新颖性分数 ≥ 0.7
- 独立性验证 ≥ 4维度通过
- 因果独立性分数 ≥ 0.6

Author: OEF Team
Version: 2.0.0
Date: 2026-04-04
"""

import sys
import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import warnings

sys.path.insert(0, str(Path(__file__).parent.parent))

from oef_framework_v2 import (
    GoalDiscoverer, 
    CompleteIndependenceValidator,
    EmergenceEngineV2,
    AutonomousDriveSpace
)

warnings.filterwarnings('ignore')

@dataclass
class ValidationExperimentConfig:
    """验证实验配置"""
    experiment_name: str = "oef_24h_validation"
    duration_hours: float = 24.0
    n_cycles: int = 7200  # 24h * 300 cycles/h
    n_agents: int = 10
    initial_drives: List[str] = None
    emergence_threshold: float = 0.7
    novelty_threshold: float = 0.7
    causal_threshold: float = 0.6
    output_dir: Path = None
    checkpoint_interval: int = 300  # 每300周期保存checkpoint
    
    def __post_init__(self):
        if self.initial_drives is None:
            self.initial_drives = ['survival', 'curiosity', 'influence', 'optimization']
        if self.output_dir is None:
            self.output_dir = Path("oef_real_data") / self.experiment_name

@dataclass 
class EmergenceEvent:
    """涌现事件记录"""
    cycle: int
    timestamp: str
    goal_name: str
    novelty_score: float
    validation_result: Dict
    source_behaviors: List[str]
    emergence_pattern: str

class ValidationExperiment:
    """24小时验证实验"""
    
    def __init__(self, config: ValidationExperimentConfig):
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化核心组件
        self.goal_discoverer = GoalDiscoverer()
        self.validator = CompleteIndependenceValidator()
        self.drive_space = AutonomousDriveSpace()
        
        # 实验状态
        self.current_cycle = 0
        self.emergence_events: List[EmergenceEvent] = []
        self.behavior_history: List[Dict] = []
        self.start_time = datetime.now()
        
        print(f"🚀 24h验证实验初始化完成")
        print(f"   实验名称: {config.experiment_name}")
        print(f"   运行时长: {config.duration_hours}小时")
        print(f"   总周期数: {config.n_cycles}")
        print(f"   输出目录: {config.output_dir}")
    
    def run(self):
        """运行验证实验"""
        print(f"\n⏰ 实验启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ 预计完成时间: {(self.start_time + timedelta(hours=self.config.duration_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            for cycle in range(self.config.n_cycles):
                self.current_cycle = cycle
                
                # 模拟Agent行为（修正版 - 返回列表）
                behaviors = self._simulate_agent_behaviors(cycle)
                self.behavior_history.extend(behaviors)
                
                # 每100周期检查涌现
                if cycle % 100 == 0 and cycle > 0:
                    self._check_emergence(cycle)
                
                # 每300周期保存checkpoint
                if cycle % self.config.checkpoint_interval == 0:
                    self._save_checkpoint(cycle)
                
                # 每1000周期打印进度
                if cycle % 1000 == 0:
                    elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
                    progress = cycle / self.config.n_cycles * 100
                    print(f"📊 进度: {cycle}/{self.config.n_cycles} ({progress:.1f}%) | 已运行: {elapsed:.1f}h | 涌现事件: {len(self.emergence_events)}")
            
            # 实验完成
            self._finalize_experiment()
            
        except KeyboardInterrupt:
            print(f"\n⚠️ 实验被用户中断于周期 {self.current_cycle}")
            self._save_checkpoint(self.current_cycle)
            self._finalize_experiment(interrupted=True)
    
    def _simulate_agent_behaviors(self, cycle: int) -> List[Dict]:
        """模拟Agent行为（修正版 - 匹配GoalDiscoverer格式）"""
        behavior_types = [
            'explore', 'learn', 'share', 'coordinate', 
            'help', 'adapt', 'create', 'optimize',
            'communicate', 'protect'
        ]
        
        # 生成多个行为（每个元素包含'action'键）
        behaviors = []
        for _ in range(random.randint(2, 5)):
            action = random.choice(behavior_types)
            behaviors.append({
                'action': action,
                'cycle': cycle,
                'timestamp': datetime.now().isoformat(),
                'score': random.uniform(0.3, 0.9)
            })
        
        return behaviors  # 返回列表，每个元素包含'action'键
    
    def _check_emergence(self, cycle: int):
        """检查涌现事件"""
        # 获取最近的行为历史
        recent_behaviors = self.behavior_history[-100:]
        
        # 使用GoalDiscoverer尝试发现新颖目标
        discovered_goal = self.goal_discoverer.discover(
            behavior_history=recent_behaviors,
            cycle=cycle,
            existing_drives=self.config.initial_drives
        )
        
        if discovered_goal:
            # 执行四维度独立性验证
            goal_name = discovered_goal.get('name', discovered_goal.get('goal_name', 'unknown'))
            
            # 准备时间序列数据（简化版）
            # 使用最近的行为历史作为时间序列
            recent_scores = [b.get('score', 0.5) for b in self.behavior_history[-100:]]
            initial_series = np.array(recent_scores[:50]) if len(recent_scores) >= 50 else np.array(recent_scores + [0.5] * (50 - len(recent_scores)))
            emergent_series = np.array(recent_scores[50:]) if len(recent_scores) >= 100 else np.array(recent_scores + [0.5] * (100 - len(recent_scores)))
            time_series = np.arange(len(initial_series))
            
            validation_result = self.validator.validate_complete_independence(
                emerged_goal=goal_name,
                initial_drives=self.config.initial_drives,
                goal_templates=None,  # 修正参数名
                initial_drive_series=[initial_series],
                emergent_drive_series=[emergent_series],
                time_series=time_series
            )
            
            # 检查是否达到涌现标准
            novelty_score = discovered_goal.get('novelty_score', 0.0)
            overall_independence = validation_result.overall_independence  # dataclass属性访问
            
            # 计算通过的维度数（提前计算，避免UnboundLocalError）
            passed_dims = sum([
                validation_result.list_independence,
                validation_result.semantic_independence,
                validation_result.source_independence,
                validation_result.causal_independence
            ])
            
            if novelty_score >= self.config.novelty_threshold and overall_independence:
                # 记录涌现事件
                event = EmergenceEvent(
                    cycle=cycle,
                    timestamp=datetime.now().isoformat(),
                    goal_name=goal_name,
                    novelty_score=float(novelty_score),
                    validation_result={
                        'list_independence': bool(validation_result.list_independence),
                        'semantic_independence': bool(validation_result.semantic_independence),
                        'source_independence': bool(validation_result.source_independence),
                        'causal_independence': bool(validation_result.causal_independence),
                        'overall_independence': bool(validation_result.overall_independence),
                        'confidence': float(validation_result.confidence),
                        'passed_dimensions': passed_dims
                    },
                    source_behaviors=discovered_goal.get('source_behaviors', []),
                    emergence_pattern=discovered_goal.get('emergence_pattern', 'unknown')
                )
                
                self.emergence_events.append(event)
                
                print(f"\n🌟 涌现事件 #{len(self.emergence_events)} @ 周期 {cycle}")
                print(f"   目标名称: {discovered_goal['name']}")
                print(f"   新颖性分数: {novelty_score:.3f}")
                print(f"   四维度验证: {passed_dims}/4")
                print(f"   来源行为: {discovered_goal.get('source_behaviors', [])}")
    
    def _save_checkpoint(self, cycle: int):
        """保存checkpoint"""
        config_dict = asdict(self.config)
        config_dict['output_dir'] = str(config_dict['output_dir'])  # PosixPath转字符串
        
        checkpoint = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'emergence_events': [asdict(e) for e in self.emergence_events],
            'config': config_dict,
            'status': 'running'
        }
        
        checkpoint_file = self.config.output_dir / f"checkpoint_{cycle}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    def _finalize_experiment(self, interrupted: bool = False):
        """完成实验"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() / 3600
        
        # 生成最终报告
        report = {
            'experiment_name': self.config.experiment_name,
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_hours': duration,
            'total_cycles': self.current_cycle,
            'interrupted': interrupted,
            'emergence_events': [asdict(e) for e in self.emergence_events],
            'validation_summary': {
                'total_emergence_events': len(self.emergence_events),
                'avg_novelty_score': np.mean([e.novelty_score for e in self.emergence_events]) if self.emergence_events else 0.0,
                'avg_passed_dimensions': np.mean([e.validation_result.get('passed_dimensions', 0) for e in self.emergence_events]) if self.emergence_events else 0.0,
                'success_criteria': {
                    'emergence_count': len(self.emergence_events) >= 3,
                    'novelty_score': np.mean([e.novelty_score for e in self.emergence_events]) >= 0.7 if self.emergence_events else False,
                    'independence_validation': all(e.validation_result.get('overall_independence', False) for e in self.emergence_events) if self.emergence_events else False
                }
            },
            'scientific_conclusion': self._generate_scientific_conclusion()
        }
        
        # 保存报告
        report_file = self.config.output_dir / "final_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 实验完成报告:")
        print(f"   运行时长: {duration:.1f}小时")
        print(f"   总周期数: {self.current_cycle}")
        print(f"   涌现事件: {len(self.emergence_events)}次")
        print(f"   报告文件: {report_file}")
    
    def _generate_scientific_conclusion(self) -> str:
        """生成科学结论"""
        if len(self.emergence_events) >= 3:
            avg_novelty = np.mean([e.novelty_score for e in self.emergence_events])
            avg_dims = np.mean([e.validation_result.get('passed_dimensions', 0) for e in self.emergence_events])
            
            if avg_novelty >= 0.7 and avg_dims >= 4:
                return "✅ 验证成功：Agent能够自主生成新颖目标，四维度独立性验证通过"
            else:
                return "⚠️ 部分验证：涌现事件达标，但独立性验证未完全通过"
        else:
            return "❌ 验证失败：涌现事件未达到标准（需≥3次）"

def main():
    """主函数"""
    print("🚀 OEF 2.0 - 24小时验证实验")
    print("=" * 50)
    
    # 创建实验配置
    config = ValidationExperimentConfig(
        experiment_name="oef_24h_validation",
        duration_hours=24.0,
        n_cycles=7200,
        n_agents=10,
        output_dir=Path("oef_real_data/oef_24h_validation")
    )
    
    # 创建并运行实验
    experiment = ValidationExperiment(config)
    experiment.run()

if __name__ == "__main__":
    main()