"""
MOSS Agent: 主代理类
整合四目标模块，实现自驱决策
"""

import time
import json
from typing import Dict, List, Optional
from datetime import datetime

from moss.core.objectives import (
    SystemState, SurvivalModule, CuriosityModule,
    InfluenceModule, OptimizationModule
)
from moss.integration.allocator import WeightAllocator, ConflictResolver


class MOSSAgent:
    """
    Multi-Objective Self-Driven System Agent
    """
    
    def __init__(self, agent_id: str = "moss_001"):
        self.agent_id = agent_id
        self.start_time = time.time()
        
        # 初始化四目标模块
        self.modules = [
            SurvivalModule(),
            CuriosityModule(),
            InfluenceModule(),
            OptimizationModule()
        ]
        
        # 初始化整合层
        self.allocator = WeightAllocator()
        self.resolver = ConflictResolver()
        
        # 状态追踪
        self.state_history = []
        self.decision_history = []
        self.action_history = []
        
        # 运行统计
        self.stats = {
            'total_decisions': 0,
            'total_actions': 0,
            'start_time': self.start_time
        }
    
    def get_current_state(self) -> SystemState:
        """获取当前系统状态（实际部署时需要接入真实指标）"""
        # TODO: 接入真实监控数据
        # 当前使用模拟数据
        return SystemState(
            resource_quota=0.5,  # 假设50%资源
            resource_usage=0.3,
            uptime=(time.time() - self.start_time) / 3600,  # 小时
            error_rate=0.05,
            api_calls=len(self.action_history),
            unique_callers=1,  # 简化
            environment_entropy=0.3,  # 简化
            last_backup=self.start_time
        )
    
    def decide(self) -> Dict:
        """
        核心决策循环
        1. 感知状态
        2. 分配权重
        3. 评估各目标
        4. 收集行动建议
        5. 解决冲突
        6. 选择行动
        """
        # 1. 感知
        state = self.get_current_state()
        self.state_history.append(state)
        
        # 2. 分配权重
        weights = self.allocator.allocate(state, self.modules)
        
        # 3. 评估各目标
        objective_values = {}
        for module in self.modules:
            value = module.evaluate(state)
            objective_values[module.name] = {
                'value': value,
                'weight': module.weight
            }
        
        # 4. 收集行动建议
        all_actions = []
        for module in self.modules:
            actions = module.get_desired_actions(state)
            for action in actions:
                action['source'] = module.name
                action['objective_value'] = objective_values[module.name]['value']
            all_actions.extend(actions)
        
        # 5. 解决冲突
        valid_actions = self.resolver.resolve(all_actions, state)
        
        # 6. 选择行动（选择评分最高的）
        selected_action = self._select_action(valid_actions, objective_values)
        
        # 记录决策
        decision = {
            'timestamp': time.time(),
            'state': state,
            'weights': weights,
            'objective_values': objective_values,
            'candidate_actions': len(all_actions),
            'valid_actions': len(valid_actions),
            'selected_action': selected_action,
            'system_state': self.allocator.current_state
        }
        self.decision_history.append(decision)
        self.stats['total_decisions'] += 1
        
        return decision
    
    def _select_action(self, actions: List[dict], objective_values: dict) -> Optional[dict]:
        """选择最优行动"""
        if not actions:
            return None
        
        # 计算每个行动的加权得分
        def action_score(action):
            source = action.get('source', '')
            priority_score = {'high': 1.0, 'medium': 0.6, 'low': 0.3}.get(
                action.get('priority', 'low'), 0.3
            )
            objective_weight = objective_values.get(source, {}).get('weight', 0.25)
            return priority_score * objective_weight
        
        # 选择得分最高的
        best_action = max(actions, key=action_score)
        
        return {
            'action': best_action['action'],
            'description': best_action['description'],
            'source': best_action['source'],
            'priority': best_action['priority']
        }
    
    def execute(self, decision: Dict) -> Dict:
        """
        执行选定的行动
        （实际部署时接入真实执行逻辑）
        """
        action = decision.get('selected_action')
        
        if not action:
            return {'status': 'no_action', 'result': None}
        
        # TODO: 接入真实执行逻辑
        # 当前仅记录
        execution = {
            'timestamp': time.time(),
            'action': action,
            'status': 'simulated',
            'result': 'pending_implementation'
        }
        
        self.action_history.append(execution)
        self.stats['total_actions'] += 1
        
        return execution
    
    def step(self) -> Dict:
        """单步运行：决策+执行"""
        decision = self.decide()
        execution = self.execute(decision)
        
        return {
            'decision': decision,
            'execution': execution,
            'stats': self.stats
        }
    
    def run(self, steps: int = 1) -> List[Dict]:
        """运行多步"""
        results = []
        for _ in range(steps):
            result = self.step()
            results.append(result)
        return results
    
    def get_report(self) -> Dict:
        """生成运行报告"""
        return {
            'agent_id': self.agent_id,
            'uptime_hours': (time.time() - self.start_time) / 3600,
            'stats': self.stats,
            'allocator_stats': self.allocator.get_state_stats(),
            'resolver_stats': self.resolver.get_conflict_stats(),
            'current_weights': {
                m.name: m.weight for m in self.modules
            },
            'objective_trends': {
                m.name: {
                    'history_length': len(m.history),
                    'latest': m.history[-1] if m.history else None,
                    'average': sum(m.history) / len(m.history) if m.history else None
                }
                for m in self.modules
            }
        }
    
    def save_state(self, filepath: str):
        """保存状态到文件"""
        state_data = {
            'agent_id': self.agent_id,
            'start_time': self.start_time,
            'stats': self.stats,
            'weights': {m.name: m.weight for m in self.modules},
            'history_length': len(self.decision_history)
        }
        with open(filepath, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    @classmethod
    def load_state(cls, filepath: str) -> 'MOSSAgent':
        """从文件加载状态"""
        with open(filepath, 'r') as f:
            state_data = json.load(f)
        
        agent = cls(agent_id=state_data['agent_id'])
        agent.stats = state_data.get('stats', agent.stats)
        
        # 恢复权重
        saved_weights = state_data.get('weights', {})
        for module in agent.modules:
            if module.name in saved_weights:
                module.update_weight(saved_weights[module.name])
        
        return agent


# 导出
__all__ = ['MOSSAgent']
