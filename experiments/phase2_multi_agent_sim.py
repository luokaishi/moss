#!/usr/bin/env python3
"""
MOSS Phase 2 - Multi-Agent Simulation
======================================

多Agent协作模拟实验

验证：10个MOSS Agent能否在共享任务池中形成分工与信任？
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

from moss.core import UnifiedMOSSAgent, MOSSConfig
from moss.core.phase2_components import MessageHub, TaskPool, TrustNetwork, DivisionOfLaborAnalyzer, Message
import numpy as np
from datetime import datetime
from typing import Dict


class MultiAgentExperiment:
    """多Agent实验"""
    
    def __init__(self, n_agents: int = 10, n_steps: int = 1000):
        self.n_agents = n_agents
        self.n_steps = n_steps
        
        # 初始化组件
        self.hub = MessageHub()
        self.task_pool = TaskPool()
        self.trust_network = TrustNetwork()
        self.division_analyzer = DivisionOfLaborAnalyzer()
        
        # 创建Agent
        self.agents = {}
        self._create_agents()
        
        # 统计数据
        self.stats = {
            'messages_exchanged': 0,
            'tasks_completed': 0,
            'trust_updates': 0,
            'collaborations': 0
        }
    
    def _create_agents(self):
        """创建不同Purpose的Agent"""
        # 为每个Agent设置不同的初始Purpose偏向
        purpose_profiles = [
            ('survival', [0.60, 0.10, 0.20, 0.10]),
            ('survival', [0.55, 0.15, 0.20, 0.10]),
            ('optimizer', [0.20, 0.20, 0.20, 0.40]),
            ('optimizer', [0.15, 0.25, 0.20, 0.40]),
            ('curious', [0.15, 0.55, 0.15, 0.15]),
            ('curious', [0.20, 0.50, 0.15, 0.15]),
            ('social', [0.15, 0.20, 0.50, 0.15]),
            ('social', [0.20, 0.15, 0.55, 0.10]),
            ('balanced', [0.30, 0.30, 0.25, 0.15]),
            ('balanced', [0.25, 0.25, 0.25, 0.25])
        ]
        
        for i, (profile_name, weights) in enumerate(purpose_profiles[:self.n_agents]):
            agent_id = f"agent_{i:02d}_{profile_name}"
            
            config = MOSSConfig(
                agent_id=agent_id,
                enable_purpose=True,
                purpose_interval=200,
                log_dir=f"experiments/phase2_simulation"
            )
            
            agent = UnifiedMOSSAgent(config)
            agent.weights = np.array(weights)
            
            self.agents[agent_id] = {
                'agent': agent,
                'profile': profile_name,
                'tasks_completed': 0,
                'reputation': 0.5
            }
            
            # 注册到消息中心
            self.hub.register(agent_id)
        
        print(f"[MultiAgent] Created {self.n_agents} agents")
    
    def run(self):
        """运行实验"""
        print("=" * 70)
        print("🚀 Phase 2 Multi-Agent Simulation")
        print("=" * 70)
        print(f"Agents: {self.n_agents}")
        print(f"Steps: {self.n_steps}")
        print()
        
        # 初始生成一些任务
        for _ in range(20):
            self.task_pool.generate_random_task()
        
        for step in range(self.n_steps):
            # 每100步生成新任务
            if step % 100 == 0:
                for _ in range(5):
                    self.task_pool.generate_random_task()
            
            # 每个Agent行动
            for agent_id, agent_data in self.agents.items():
                self._agent_step(agent_id, agent_data, step)
            
            # 显示进度
            if step % 200 == 0:
                self._print_progress(step)
        
        # 最终分析
        self._final_analysis()
    
    def _agent_step(self, agent_id: str, agent_data: Dict, step: int):
        """单个Agent的一步"""
        agent = agent_data['agent']
        
        # 1. 接收消息
        messages = self.hub.receive(agent_id)
        
        # 2. Agent决策
        result = agent.step()
        action = result.action_type
        
        # 3. 根据Purpose选择任务
        if np.random.random() < 0.3:  # 30%概率尝试获取任务
            available = self.task_pool.get_available_tasks()
            if available:
                # 根据Agent的Purpose偏向选择任务类型
                task = self._select_task_by_purpose(agent_id, available)
                if task:
                    self.task_pool.assign_task(task['id'], agent_id)
                    
                    # 模拟任务完成
                    if np.random.random() > 0.2:  # 80%成功率
                        quality = np.random.uniform(0.6, 1.0)
                        self.task_pool.complete_task(task['id'], agent_id, quality)
                        
                        agent_data['tasks_completed'] += 1
                        self.division_analyzer.record_task_completion(agent_id, task)
                        
                        # 广播完成情况（建立声誉）
                        msg = Message(
                            sender_id=agent_id,
                            receiver_id='broadcast',
                            msg_type='task_complete',
                            content={'task_id': task['id'], 'quality': quality},
                            timestamp=datetime.now()
                        )
                        self.hub.send(msg)
        
        # 4. 处理接收到的消息，更新信任
        for msg in messages:
            if msg.msg_type == 'task_complete':
                # 观察到其他Agent完成任务，更新信任
                quality = msg.content.get('quality', 0.5)
                self.trust_network.update_trust(agent_id, msg.sender_id, quality)
                self.stats['trust_updates'] += 1
        
        # 5. 偶尔寻求帮助（协作）
        if np.random.random() < 0.05:  # 5%概率寻求帮助
            trusted = self.trust_network.get_trusted_partners(agent_id, threshold=0.3)
            if trusted:
                partner = np.random.choice(trusted)
                # 模拟协作
                self.stats['collaborations'] += 1
                # 协作成功增加双方信任
                self.trust_network.update_trust(agent_id, partner, 0.8)
                self.trust_network.update_trust(partner, agent_id, 0.8)
    
    def _select_task_by_purpose(self, agent_id: str, tasks: list) -> Dict:
        """根据Agent的Purpose选择任务"""
        agent_data = self.agents[agent_id]
        agent = agent_data['agent']
        
        # 获取当前主导Purpose
        weights = agent.weights
        dominant = np.argmax(weights)
        
        # Purpose到任务类型的映射
        purpose_to_task = {
            0: 'security',      # Survival
            1: 'documentation', # Curiosity
            2: 'community',     # Influence
            3: 'optimization'   # Optimization
        }
        
        preferred_type = purpose_to_task.get(dominant, 'other')
        
        # 优先选择匹配的任务
        matching = [t for t in tasks if t['type'] == preferred_type]
        if matching:
            return np.random.choice(matching)
        
        # 没有匹配则随机选择
        return np.random.choice(tasks) if tasks else None
    
    def _print_progress(self, step: int):
        """打印进度"""
        progress = (step / self.n_steps) * 100
        task_stats = self.task_pool.get_stats()
        
        print(f"[Step {step}] {progress:.1f}% | "
              f"Tasks: {task_stats['completed']}/{task_stats['total']} | "
              f"Trust updates: {self.stats['trust_updates']} | "
              f"Collaborations: {self.stats['collaborations']}")
    
    def _final_analysis(self):
        """最终分析"""
        print("\n" + "=" * 70)
        print("📊 Final Analysis")
        print("=" * 70)
        
        # 任务完成情况
        task_stats = self.task_pool.get_stats()
        print(f"\n📋 Task Statistics:")
        print(f"  Total created: {task_stats['total']}")
        print(f"  Completed: {task_stats['completed']}")
        print(f"  Completion rate: {task_stats['completion_rate']:.2%}")
        
        # 信任网络
        print(f"\n🤝 Trust Network:")
        print(f"  Network density: {self.trust_network.get_network_density():.2f}")
        print(f"  Total trust updates: {self.stats['trust_updates']}")
        
        # 分工分析
        print(f"\n📊 Division of Labor:")
        div_index = self.division_analyzer.get_division_index()
        print(f"  Division index: {div_index:.2f}")
        print(f"  (0=无分工, 1=完全专业化)")
        
        specializations = self.division_analyzer.detect_specialization()
        print(f"\n  Agent Specializations:")
        for agent_id, spec in specializations.items():
            tasks_completed = self.agents[agent_id]['tasks_completed']
            print(f"    {agent_id}: {spec} ({tasks_completed} tasks)")
        
        # Agent贡献
        print(f"\n🏆 Agent Contributions:")
        sorted_agents = sorted(
            self.agents.items(),
            key=lambda x: x[1]['tasks_completed'],
            reverse=True
        )
        for agent_id, data in sorted_agents[:5]:
            print(f"  {agent_id}: {data['tasks_completed']} tasks")
        
        print("\n" + "=" * 70)
        
        # 关键发现
        print("\n💡 Key Findings:")
        if div_index > 0.3:
            print("  ✅ Division of labor emerged!")
        if self.trust_network.get_network_density() > 0.2:
            print("  ✅ Trust network formed!")
        if self.stats['collaborations'] > 10:
            print("  ✅ Collaboration behavior observed!")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    # 快速模拟（1000步）
    experiment = MultiAgentExperiment(n_agents=10, n_steps=1000)
    experiment.run()
