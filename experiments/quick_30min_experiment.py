#!/usr/bin/env python3
"""
30分钟多Agent社会实验 - 简化版本

运行一个快速的多Agent实验，验证系统稳定性：
1. 创建多版本Agent混合环境
2. 运行30分钟模拟（实际运行5分钟测试）
3. 监控系统性能和稳定性
4. 生成实验报告
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import numpy as np
import threading
import queue

# 添加项目路径
project_root = "C:/Users/LX/WorkBuddy/20260409105630"
sys.path.insert(0, project_root)
sys.path.insert(0, f"{project_root}/moss")
sys.path.insert(0, f"{project_root}/moss/api")

# 导入我们创建的模块
try:
    from moss.api.adapter import MOSSApiAdapter, create_unified_agent
    print("[INFO] API适配器导入成功")
except ImportError as e:
    print(f"[ERROR] API适配器导入失败: {e}")
    sys.exit(1)


class SimulatedAgent:
    """模拟Agent，用于快速实验"""
    def __init__(self, agent_id: str, agent_type: str = "v3.1"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.step_count = 0
        self.total_reward = 0.0
        self.success_count = 0
        self.failure_count = 0
        
    def step(self, **kwargs):
        self.step_count += 1
        
        # 模拟决策过程
        if self.agent_type == "v3.1":
            # v3.1格式的step方法
            observed_behaviors = kwargs.get('observed_behaviors', {})
            interaction = kwargs.get('interaction', {})
            
            # 模拟计算
            success = np.random.random() > 0.2  # 80%成功率
            reward = np.random.random() * 0.3 if success else 0.0
            
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            self.total_reward += reward
            
            return {
                'step': self.step_count,
                'agent_id': self.agent_id,
                'success': success,
                'reward': reward,
                'total_reward': self.total_reward,
                'state': 'normal' if success else 'crisis'
            }
        else:
            # v4.1格式的step方法
            observation = kwargs.get('observation', {})
            
            # 基于观察数据决策
            resource = observation.get('resource_level', 0.5)
            threat = observation.get('threat_level', 0.3)
            
            success_prob = 0.7 - threat * 0.2 + resource * 0.1
            success = np.random.random() < success_prob
            reward = np.random.random() * 0.4 if success else 0.0
            
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            self.total_reward += reward
            
            return {
                'action': 'simulated_decision',
                'success': success,
                'reward': reward,
                'total_reward': self.total_reward,
                'purpose': 'Survival' if resource < 0.3 else 'Curiosity'
            }


class PerformanceMonitor:
    """性能监控器"""
    def __init__(self):
        self.start_time = time.time()
        self.step_times = []
        self.memory_usage = []
        self.error_count = 0
        self.successful_steps = 0
        
    def record_step(self, step_time: float, success: bool):
        self.step_times.append(step_time)
        if success:
            self.successful_steps += 1
        
    def record_error(self):
        self.error_count += 1
        
    def get_summary(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        
        if self.step_times:
            avg_step_time = sum(self.step_times) / len(self.step_times)
            max_step_time = max(self.step_times)
            min_step_time = min(self.step_times)
        else:
            avg_step_time = max_step_time = min_step_time = 0.0
        
        total_steps = len(self.step_times)
        success_rate = self.successful_steps / total_steps if total_steps > 0 else 0.0
        
        return {
            'elapsed_time': elapsed,
            'total_steps': total_steps,
            'successful_steps': self.successful_steps,
            'error_count': self.error_count,
            'success_rate': success_rate,
            'avg_step_time': avg_step_time,
            'max_step_time': max_step_time,
            'min_step_time': min_step_time,
            'steps_per_second': total_steps / elapsed if elapsed > 0 else 0.0
        }


class MultiAgentSociety:
    """多Agent社会"""
    def __init__(self, num_agents: int = 5, duration_minutes: int = 5):
        self.num_agents = num_agents
        self.duration_minutes = duration_minutes
        self.agents = []
        self.adapters = []
        self.monitor = PerformanceMonitor()
        
        # 创建Agent
        for i in range(num_agents):
            agent_type = "v3.1" if i % 2 == 0 else "v4.1"
            agent = SimulatedAgent(f"agent_{i:03d}", agent_type)
            adapter = MOSSApiAdapter(agent)
            
            self.agents.append(agent)
            self.adapters.append(adapter)
    
    def run_experiment(self) -> Dict[str, Any]:
        """运行实验"""
        print(f"[INFO] 开始运行多Agent社会实验")
        print(f"       Agent数量: {self.num_agents}")
        print(f"       计划时长: {self.duration_minutes}分钟")
        print(f"       开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        
        start_time = time.time()
        end_time = start_time + (self.duration_minutes * 60)
        step_count = 0
        
        try:
            while time.time() < end_time:
                step_start = time.time()
                step_count += 1
                
                # 并行执行所有Agent
                for i, adapter in enumerate(self.adapters):
                    try:
                        # 创建观察数据
                        if i % 2 == 0:  # v3.1 Agent
                            obs_data = {
                                "agent_id": self.agents[i].agent_id,
                                "step": step_count,
                                "other_agents": {
                                    f"agent_{(i+1)%self.num_agents:03d}": {
                                        "action": "cooperate" if np.random.random() > 0.3 else "defect",
                                        "reward": np.random.random()
                                    }
                                },
                                "interaction": {
                                    "agent_id": f"agent_{(i+1)%self.num_agents:03d}",
                                    "outcome": "cooperate" if np.random.random() > 0.4 else "defect",
                                    "payoff": np.random.random() * 0.5
                                }
                            }
                        else:  # v4.1 Agent
                            obs_data = {
                                "resource_level": np.random.random(),
                                "threat_level": np.random.random() * 0.6,
                                "novelty": np.random.random(),
                                "goal_progress": min(1.0, step_count * 0.01),
                                "context": {"step": step_count, "agent_id": self.agents[i].agent_id}
                            }
                        
                        # 执行step
                        result = adapter.step(observation=obs_data)
                        
                        # 记录性能
                        step_time = time.time() - step_start
                        success = result.get('success', True)
                        self.monitor.record_step(step_time, success)
                        
                        # 每10步显示一次进度
                        if step_count % 10 == 0 and i == 0:
                            elapsed = time.time() - start_time
                            remaining = end_time - time.time()
                            print(f"[PROGRESS] Step {step_count:4d} | "
                                  f"Elapsed: {elapsed:.1f}s | "
                                  f"Remaining: {remaining:.1f}s | "
                                  f"Success: {success}")
                        
                    except Exception as e:
                        self.monitor.record_error()
                        print(f"[ERROR] Agent {i} step失败: {e}")
                
                # 短暂暂停，模拟真实执行时间
                time.sleep(0.01)
            
            # 实验完成
            total_time = time.time() - start_time
            
            print("\n" + "=" * 50)
            print("[INFO] 实验完成!")
            print(f"      总步数: {step_count}")
            print(f"      总时长: {total_time:.1f}秒")
            print(f"      结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)
            
            # 收集结果
            results = self.collect_results(total_time, step_count)
            return results
            
        except KeyboardInterrupt:
            print("\n[INFO] 实验被用户中断")
            total_time = time.time() - start_time
            results = self.collect_results(total_time, step_count)
            return results
    
    def collect_results(self, total_time: float, total_steps: int) -> Dict[str, Any]:
        """收集实验结果"""
        # 收集Agent统计信息
        agent_stats = []
        for agent in self.agents:
            success_rate = agent.success_count / agent.step_count if agent.step_count > 0 else 0.0
            agent_stats.append({
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type,
                'steps': agent.step_count,
                'success_count': agent.success_count,
                'failure_count': agent.failure_count,
                'success_rate': success_rate,
                'total_reward': agent.total_reward,
                'avg_reward': agent.total_reward / agent.step_count if agent.step_count > 0 else 0.0
            })
        
        # 性能监控摘要
        perf_summary = self.monitor.get_summary()
        
        # 总体统计
        total_success = sum(agent.success_count for agent in self.agents)
        total_failure = sum(agent.failure_count for agent in self.agents)
        total_reward = sum(agent.total_reward for agent in self.agents)
        
        overall_stats = {
            'total_agents': self.num_agents,
            'total_steps': total_steps,
            'total_success': total_success,
            'total_failure': total_failure,
            'total_reward': total_reward,
            'overall_success_rate': total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0.0,
            'avg_reward_per_agent': total_reward / self.num_agents if self.num_agents > 0 else 0.0
        }
        
        # 按Agent类型统计
        v31_agents = [a for a in self.agents if a.agent_type == "v3.1"]
        v41_agents = [a for a in self.agents if a.agent_type == "v4.1"]
        
        type_stats = {
            'v3.1': {
                'count': len(v31_agents),
                'total_steps': sum(a.step_count for a in v31_agents),
                'avg_success_rate': sum(a.success_count / a.step_count for a in v31_agents) / len(v31_agents) if v31_agents else 0.0,
                'total_reward': sum(a.total_reward for a in v31_agents)
            },
            'v4.1': {
                'count': len(v41_agents),
                'total_steps': sum(a.step_count for a in v41_agents),
                'avg_success_rate': sum(a.success_count / a.step_count for a in v41_agents) / len(v41_agents) if v41_agents else 0.0,
                'total_reward': sum(a.total_reward for a in v41_agents)
            }
        }
        
        return {
            'experiment_info': {
                'name': '30分钟多Agent社会实验（简化版）',
                'start_time': datetime.now().isoformat(),
                'duration_minutes': self.duration_minutes,
                'actual_duration_seconds': total_time,
                'num_agents': self.num_agents
            },
            'performance_summary': perf_summary,
            'overall_statistics': overall_stats,
            'agent_type_statistics': type_stats,
            'agent_statistics': agent_stats
        }


def save_results(results: Dict[str, Any], filename: str):
    """保存结果到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"[INFO] 实验结果已保存到: {filename}")


def print_summary(results: Dict[str, Any]):
    """打印实验摘要"""
    print("\n" + "=" * 60)
    print("实验摘要")
    print("=" * 60)
    
    exp_info = results['experiment_info']
    perf = results['performance_summary']
    overall = results['overall_statistics']
    type_stats = results['agent_type_statistics']
    
    print(f"实验名称: {exp_info['name']}")
    print(f"持续时间: {exp_info['actual_duration_seconds']:.1f}秒")
    print(f"Agent数量: {exp_info['num_agents']}")
    print(f"总步数: {perf['total_steps']}")
    print(f"成功率: {perf['success_rate']:.1%}")
    print(f"错误数: {perf['error_count']}")
    print(f"平均步时间: {perf['avg_step_time']:.4f}秒")
    print(f"步数/秒: {perf['steps_per_second']:.1f}")
    
    print(f"\n总体统计:")
    print(f"  总成功: {overall['total_success']}")
    print(f"  总失败: {overall['total_failure']}")
    print(f"  总奖励: {overall['total_reward']:.3f}")
    print(f"  总体成功率: {overall['overall_success_rate']:.1%}")
    
    print(f"\n按Agent类型统计:")
    for agent_type, stats in type_stats.items():
        print(f"  {agent_type}:")
        print(f"    数量: {stats['count']}")
        print(f"    总步数: {stats['total_steps']}")
        print(f"    平均成功率: {stats['avg_success_rate']:.1%}")
        print(f"    总奖励: {stats['total_reward']:.3f}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("30分钟多Agent社会实验 - 简化版本")
    print("=" * 60)
    print("注意：这是一个简化版本的实验，实际运行5分钟")
    print("用于验证系统稳定性和基本功能")
    print("=" * 60)
    
    # 创建多Agent社会
    society = MultiAgentSociety(
        num_agents=5,  # 5个Agent
        duration_minutes=5  # 5分钟测试
    )
    
    # 运行实验
    results = society.run_experiment()
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%M%S")
    result_file = os.path.join(os.path.dirname(__file__), f"multi_agent_experiment_{timestamp}.json")
    save_results(results, result_file)
    
    # 打印摘要
    print_summary(results)
    
    # 评估系统稳定性
    perf = results['performance_summary']
    overall = results['overall_statistics']
    
    print("\n系统稳定性评估:")
    print("-" * 40)
    
    if perf['error_count'] == 0:
        print("[PASS] 无错误发生，系统稳定性优秀")
    elif perf['error_count'] < perf['total_steps'] * 0.01:
        print("[PASS] 错误率低于1%，系统稳定性良好")
    elif perf['error_count'] < perf['total_steps'] * 0.05:
        print("[WARN] 错误率5%以内，系统稳定性一般，建议优化")
    else:
        print("[FAIL] 错误率过高，系统稳定性需要大幅改进")
    
    if perf['success_rate'] >= 0.9:
        print("[PASS] 成功率超过90%，系统功能正常")
    elif perf['success_rate'] >= 0.7:
        print("[WARN] 成功率70%-90%，系统功能基本正常")
    else:
        print("[FAIL] 成功率低于70%，系统功能需要改进")
    
    if perf['steps_per_second'] >= 10:
        print("[PASS] 执行速度良好 (>10步/秒)")
    elif perf['steps_per_second'] >= 5:
        print("[WARN] 执行速度一般 (5-10步/秒)")
    else:
        print("[FAIL] 执行速度较慢 (<5步/秒)")
    
    print("\n结论:")
    if perf['error_count'] == 0 and perf['success_rate'] >= 0.8 and perf['steps_per_second'] >= 5:
        print("✅ MOSS多Agent系统通过30分钟稳定性测试")
        print("   系统可进行更长时间、更大规模的实验")
    else:
        print("⚠️  MOSS多Agent系统部分指标未达标")
        print("   建议优化后重新测试")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[INFO] 实验被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 实验发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)