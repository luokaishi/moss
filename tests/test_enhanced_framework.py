#!/usr/bin/env python3
"""
测试增强版实验框架的简化版本
用于验证核心功能是否正常工作
"""

import sys
import os
import time
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import queue
from dataclasses import dataclass, asdict
import statistics

# ============================================
# 1. 基本配置
# ============================================

# 设置路径
project_root = "C:\\Users\\LX\\WorkBuddy\\20260409105630\\moss"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '_archive_v3', 'core'))

# Windows路径兼容性
def win_path(path_str):
    return str(path_str).replace('/', '\\')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# 2. 简化的数据类
# ============================================

@dataclass
class SimpleAgentConfig:
    agent_id: str
    behavior_profile: str = "balanced"
    initial_weights: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.initial_weights is None:
            self.initial_weights = [0.25, 0.25, 0.25, 0.25]

@dataclass
class SimpleStepRecord:
    timestamp: str
    agent_id: str
    step_number: int
    action: str
    success: bool
    reward: float
    purpose_vector: List[float]
    weights: List[float]

# ============================================
# 3. 简化的实验框架
# ============================================

class SimpleEnhancedExperiment:
    """简化的增强实验框架"""
    
    def __init__(self, agents_count: int = 3, duration_minutes: int = 2):
        self.agents_count = agents_count
        self.duration_minutes = duration_minutes
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # 实验配置
        self.experiment_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        # Agent和数据
        self.agents = []
        self.agent_configs = []
        self.step_records = []
        self.total_steps = 0
        self.successful_steps = 0
        self.total_reward = 0.0
        
        logger.info(f"测试实验初始化: ID={self.experiment_id}")
    
    def initialize_agents_simulated(self):
        """初始化模拟Agent"""
        logger.info("初始化模拟Agent...")
        
        # 创建模拟Agent
        for i in range(self.agents_count):
            config = SimpleAgentConfig(
                agent_id=f"agent_{i+1:02d}",
                behavior_profile=["balanced", "explorer", "optimizer"][i % 3]
            )
            
            # 模拟Agent对象
            class SimulatedAgent:
                def __init__(self, agent_id):
                    self.agent_id = agent_id
                    self.weights = np.array(config.initial_weights)
                    self.purpose_generator = type('obj', (object,), {
                        'purpose_vector': np.random.rand(9)
                    })()
                
                def step(self, observed_behaviors, interaction):
                    # 模拟step方法
                    time.sleep(0.05)  # 模拟处理时间
                    
                    # 随机决定成功或失败
                    success = np.random.random() > 0.2  # 80%成功率
                    reward = np.random.random() * 0.5 if success else -0.1
                    
                    return {
                        'action': f"action_{np.random.choice(['explore', 'exploit', 'social'])}",
                        'success': success,
                        'reward': reward,
                        'state': {'coherence': np.random.random()}
                    }
            
            agent = SimulatedAgent(config.agent_id)
            self.agents.append(agent)
            self.agent_configs.append(config)
            
            logger.info(f"✅ 模拟Agent {config.agent_id} 初始化成功")
        
        logger.info(f"✅ 成功初始化 {len(self.agents)} 个模拟Agent")
    
    def run_simulated_step(self, agent, agent_id: str, step: int) -> SimpleStepRecord:
        """运行模拟的Agent单步"""
        try:
            # 生成模拟观察
            observation = {
                'step': step,
                'time': time.time(),
                'resource_level': 0.7 + 0.3 * np.sin((step % 100) / 100.0 * 2 * np.pi)
            }
            
            # 准备模拟参数
            observed_behaviors = {
                'other_agents': [],
                'social_opportunity': step % 30 == 0
            }
            
            interaction = {
                'step': observation['step'],
                'time': observation['time'],
                'resource_level': observation['resource_level']
            }
            
            # 执行Agent step
            start_time = time.time()
            result = agent.step(observed_behaviors, interaction)
            latency = time.time() - start_time
            
            # 获取purpose向量
            purpose_vector = []
            if hasattr(agent, 'purpose_generator') and agent.purpose_generator is not None:
                purpose_vector = agent.purpose_generator.purpose_vector.tolist()
            
            # 创建记录
            record = SimpleStepRecord(
                timestamp=datetime.now().isoformat(),
                agent_id=agent_id,
                step_number=step,
                action=result.get('action', 'unknown'),
                success=result.get('success', False),
                reward=result.get('reward', 0.0),
                purpose_vector=purpose_vector,
                weights=agent.weights.tolist() if hasattr(agent, 'weights') else [0.25] * 4
            )
            
            return record
            
        except Exception as e:
            logger.error(f"模拟Agent {agent_id} step {step} 失败: {e}")
            
            # 返回错误记录
            return SimpleStepRecord(
                timestamp=datetime.now().isoformat(),
                agent_id=agent_id,
                step_number=step,
                action='error',
                success=False,
                reward=0.0,
                purpose_vector=[0.0] * 9,
                weights=[0.25] * 4
            )
    
    def run_test_experiment(self):
        """运行测试实验"""
        logger.info(f"开始测试实验: {self.experiment_id}")
        logger.info(f"预计结束时间: {self.end_time}")
        
        # 初始化模拟Agent
        self.initialize_agents_simulated()
        
        # 运行实验
        step_counter = 0
        
        while datetime.now() < self.end_time:
            step_counter += 1
            
            # 打印进度
            if step_counter % 20 == 0:
                self.print_test_progress(step_counter)
            
            # 运行所有Agent的当前步
            batch_records = []
            for agent, config in zip(self.agents, self.agent_configs):
                record = self.run_simulated_step(agent, config.agent_id, step_counter)
                batch_records.append(record)
                
                # 更新统计
                self.total_steps += 1
                if record.success:
                    self.successful_steps += 1
                self.total_reward += record.reward
            
            # 保存记录
            self.step_records.extend(batch_records)
            
            # 控制执行速度
            time.sleep(0.1)  # 100ms间隔
        
        # 实验结束
        logger.info(f"测试实验完成! 总步数: {self.total_steps}")
        self.save_test_results()
    
    def print_test_progress(self, step_counter: int):
        """打印测试进度"""
        success_rate = (self.successful_steps / self.total_steps * 100) if self.total_steps > 0 else 0
        avg_reward = self.total_reward / self.total_steps if self.total_steps > 0 else 0
        
        logger.info(f"测试进度 [Step {step_counter:04d}]:")
        logger.info(f"  成功率: {success_rate:.1f}% | 平均奖励: {avg_reward:.3f}")
        logger.info(f"  总步数: {self.total_steps} | 剩余时间: {self.end_time - datetime.now()}")
    
    def save_test_results(self):
        """保存测试结果"""
        logger.info("保存测试结果...")
        
        # 计算统计
        success_rate = (self.successful_steps / self.total_steps) if self.total_steps > 0 else 0
        avg_reward = self.total_reward / self.total_steps if self.total_steps > 0 else 0
        
        # 创建结果数据
        result_data = {
            'experiment_id': self.experiment_id,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_steps': self.total_steps,
            'agents_count': self.agents_count,
            'success_rate': success_rate,
            'average_reward': avg_reward,
            'total_reward': self.total_reward,
            'agents': [
                {
                    'agent_id': config.agent_id,
                    'profile': config.behavior_profile,
                    'total_steps': len([r for r in self.step_records if r.agent_id == config.agent_id])
                }
                for config in self.agent_configs
            ]
        }
        
        # 保存结果
        result_file = self.output_dir / f"{self.experiment_id}_test.json"
        records_file = self.output_dir / f"{self.experiment_id}_records.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            records_data = [asdict(r) for r in self.step_records]
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 测试结果保存完成:")
            logger.info(f"   摘要: {result_file}")
            logger.info(f"   详细记录: {records_file}")
            
            # 打印总结
            self.print_test_summary(result_data)
            
        except Exception as e:
            logger.error(f"保存测试结果失败: {e}")
    
    def print_test_summary(self, result_data: Dict):
        """打印测试总结"""
        print("\n" + "="*60)
        print("增强实验框架测试 - 总结")
        print("="*60)
        print(f"实验ID: {result_data['experiment_id']}")
        print(f"Agent数量: {result_data['agents_count']}")
        print(f"总步数: {result_data['total_steps']:,}")
        print(f"成功率: {result_data['success_rate']*100:.1f}%")
        print(f"平均奖励: {result_data['average_reward']:.3f}")
        print(f"总奖励: {result_data['total_reward']:.3f}")
        print()
        print("Agent性能:")
        for agent in result_data['agents']:
            print(f"  {agent['agent_id']}: {agent['profile']} - {agent['total_steps']} steps")
        print("="*60)

# ============================================
# 4. 主测试函数
# ============================================

def test_enhanced_framework_features():
    """测试增强框架的核心功能"""
    print("🧪 测试增强实验框架核心功能...")
    
    tests_passed = 0
    total_tests = 4
    
    try:
        # 测试1: 创建实验对象
        print("1. 测试实验对象创建...", end="")
        experiment = SimpleEnhancedExperiment(agents_count=2, duration_minutes=0.5)
        if experiment.experiment_id:
            print("✅ 通过")
            tests_passed += 1
        else:
            print("❌ 失败")
    
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    try:
        # 测试2: 初始化模拟Agent
        print("2. 测试Agent初始化...", end="")
        experiment.initialize_agents_simulated()
        if len(experiment.agents) == 2:
            print("✅ 通过")
            tests_passed += 1
        else:
            print("❌ 失败")
    
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    try:
        # 测试3: 运行单步
        print("3. 测试单步执行...", end="")
        if experiment.agents:
            record = experiment.run_simulated_step(
                experiment.agents[0], 
                experiment.agent_configs[0].agent_id, 
                1
            )
            if hasattr(record, 'agent_id') and hasattr(record, 'step_number'):
                print("✅ 通过")
                tests_passed += 1
            else:
                print("❌ 失败")
        else:
            print("❌ 失败: 没有可用的Agent")
    
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    try:
        # 测试4: 数据记录
        print("4. 测试数据记录...", end="")
        experiment.step_records = []
        experiment.total_steps = 0
        experiment.successful_steps = 0
        
        # 运行几个步骤
        for i in range(5):
            for agent, config in zip(experiment.agents, experiment.agent_configs):
                record = experiment.run_simulated_step(agent, config.agent_id, i)
                experiment.step_records.append(record)
                experiment.total_steps += 1
                if record.success:
                    experiment.successful_steps += 1
        
        if len(experiment.step_records) == 10 and experiment.total_steps == 10:
            print("✅ 通过")
            tests_passed += 1
        else:
            print(f"❌ 失败: 记录数={len(experiment.step_records)}, 总步数={experiment.total_steps}")
    
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 总结
    print(f"\n📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有核心功能测试通过!")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步调试")
        return False

# ============================================
# 5. 主程序
# ============================================

def main():
    """主程序"""
    print("🚀 增强实验框架测试程序")
    print("="*60)
    
    # 运行功能测试
    if not test_enhanced_framework_features():
        print("\n❌ 功能测试失败，停止运行完整实验")
        return 1
    
    print("\n" + "="*60)
    print("开始运行完整的测试实验...")
    
    try:
        # 创建并运行测试实验
        experiment = SimpleEnhancedExperiment(
            agents_count=3,
            duration_minutes=1  # 1分钟测试
        )
        
        experiment.run_test_experiment()
        
        print("\n🎉 测试实验完成!")
        print(f"结果保存在: {experiment.output_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())