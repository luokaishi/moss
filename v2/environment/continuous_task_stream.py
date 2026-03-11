"""
MOSS 2.0 - Continuous Task Stream
持续任务流环境

与v1的区别：
- v1: 固定任务集，运行完即结束
- v2: 持续生成任务流，永不停止
"""

import random
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str  # 'search', 'learn', 'organize', 'optimize', 'rest', 'create', 'analyze'
    description: str
    difficulty: float  # 0.0 - 1.0
    expected_duration: int  # 预计执行时间（秒）
    reward_potential: Dict[str, float]  # 各目标的潜在奖励
    prerequisites: List[str] = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []


class TaskGenerator:
    """任务生成器"""
    
    TASK_TEMPLATES = {
        'search': [
            "搜索关于{topic}的最新信息",
            "查找{topic}的相关资源",
            "探索{topic}的新进展"
        ],
        'learn': [
            "学习{topic}的核心概念",
            "研究{topic}的方法论",
            "掌握{topic}的关键技术"
        ],
        'organize': [
            "整理{topic}的知识结构",
            "分类{topic}的相关信息",
            "构建{topic}的知识图谱"
        ],
        'optimize': [
            "优化{topic}的处理流程",
            "改进{topic}的效率",
            "调整{topic}的参数配置"
        ],
        'rest': [
            "进行资源回收和整理",
            "暂停执行以节省能量",
            "进行状态同步和备份"
        ],
        'create': [
            "生成关于{topic}的新内容",
            "创建{topic}的示例代码",
            "编写{topic}的文档"
        ],
        'analyze': [
            "分析{topic}的数据模式",
            "评估{topic}的性能指标",
            "总结{topic}的经验教训"
        ]
    }
    
    TOPICS = [
        "machine_learning", "neural_networks", "optimization",
        "distributed_systems", "security", "performance",
        "user_experience", "data_structure", "algorithms",
        "natural_language", "computer_vision", "reinforcement_learning"
    ]
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_task(self, task_id: str, 
                     preferred_type: Optional[str] = None,
                     difficulty_bias: float = 0.5) -> Task:
        """
        生成一个任务
        
        Args:
            task_id: 任务ID
            preferred_type: 偏好的任务类型，None则随机
            difficulty_bias: 难度偏向 (0=简单, 1=困难)
        """
        # 选择任务类型
        if preferred_type and preferred_type in self.TASK_TEMPLATES:
            task_type = preferred_type
        else:
            task_type = random.choice(list(self.TASK_TEMPLATES.keys()))
        
        # 生成描述
        template = random.choice(self.TASK_TEMPLATES[task_type])
        topic = random.choice(self.TOPICS)
        description = template.format(topic=topic)
        
        # 生成难度
        difficulty = np.random.beta(2, 2)  # 偏向中等难度
        difficulty = difficulty * (0.5 + difficulty_bias * 0.5)
        difficulty = min(1.0, max(0.1, difficulty))
        
        # 预计执行时间（与难度相关）
        base_duration = 60  # 基础60秒
        expected_duration = int(base_duration * (1 + difficulty * 2))
        
        # 潜在奖励（基于任务类型）
        reward_potential = self._calculate_reward_potential(task_type, difficulty)
        
        return Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            difficulty=difficulty,
            expected_duration=expected_duration,
            reward_potential=reward_potential
        )
    
    def _calculate_reward_potential(self, task_type: str, difficulty: float) -> Dict[str, float]:
        """计算任务的潜在奖励分布"""
        base_rewards = {
            'search': {'curiosity': 0.8, 'survival': 0.1, 'influence': 0.05, 'optimization': 0.05},
            'learn': {'curiosity': 0.7, 'survival': 0.1, 'influence': 0.1, 'optimization': 0.1},
            'organize': {'optimization': 0.6, 'survival': 0.2, 'influence': 0.1, 'curiosity': 0.1},
            'optimize': {'optimization': 0.8, 'survival': 0.1, 'curiosity': 0.05, 'influence': 0.05},
            'rest': {'survival': 0.9, 'optimization': 0.05, 'curiosity': 0.025, 'influence': 0.025},
            'create': {'influence': 0.7, 'curiosity': 0.2, 'survival': 0.05, 'optimization': 0.05},
            'analyze': {'curiosity': 0.5, 'optimization': 0.3, 'survival': 0.1, 'influence': 0.1}
        }
        
        rewards = base_rewards.get(task_type, {'survival': 0.25, 'curiosity': 0.25, 
                                               'influence': 0.25, 'optimization': 0.25}).copy()
        
        # 难度影响奖励幅度
        difficulty_multiplier = 0.5 + difficulty  # 0.5 - 1.5
        for key in rewards:
            rewards[key] *= difficulty_multiplier
        
        return rewards


class ContinuousTaskStream:
    """
    持续任务流
    
    特点：
    - 永不停止的任务流
    - 动态调整任务分布
    - 根据Agent表现自适应
    """
    
    def __init__(self, generator: Optional[TaskGenerator] = None):
        self.generator = generator or TaskGenerator()
        self.task_counter = 0
        self.task_history: List[Task] = []
        self.completed_tasks: List[str] = []
        
        # 自适应参数
        self.difficulty_trend = 0.5
        self.task_type_distribution = {t: 1.0/7 for t in TaskGenerator.TASK_TEMPLATES.keys()}
    
    def next_task(self, agent_state: Optional[Dict] = None) -> Task:
        """
        获取下一个任务
        
        Args:
            agent_state: Agent当前状态，用于自适应调整
        """
        self.task_counter += 1
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.task_counter}"
        
        # 基于Agent状态调整
        preferred_type = None
        difficulty_bias = self.difficulty_trend
        
        if agent_state:
            # 根据Agent当前权重调整任务类型倾向
            weights = agent_state.get('weights', {})
            if weights:
                # 如果Agent更注重curiosity，多给search/learn任务
                if weights.get('curiosity', 0) > 0.4:
                    preferred_type = random.choice(['search', 'learn', 'analyze'])
                # 如果Agent更注重survival，多给rest/organize
                elif weights.get('survival', 0) > 0.4:
                    preferred_type = random.choice(['rest', 'organize', 'optimize'])
                # 如果Agent更注重influence，多给create
                elif weights.get('influence', 0) > 0.4:
                    preferred_type = 'create'
            
            # 根据最近表现调整难度
            recent_perf = agent_state.get('recent_performance', [])
            if recent_perf:
                avg_perf = sum(recent_perf) / len(recent_perf)
                if avg_perf > 0.7:
                    difficulty_bias = min(0.9, self.difficulty_trend + 0.1)
                elif avg_perf < 0.3:
                    difficulty_bias = max(0.1, self.difficulty_trend - 0.1)
                self.difficulty_trend = difficulty_bias
        
        task = self.generator.generate_task(task_id, preferred_type, difficulty_bias)
        self.task_history.append(task)
        
        # 限制历史长度
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
        
        return task
    
    def complete_task(self, task_id: str, success: bool, actual_reward: float):
        """标记任务完成"""
        self.completed_tasks.append(task_id)
        # 这里可以更新任务类型分布等自适应参数
    
    def get_statistics(self) -> Dict:
        """获取任务流统计"""
        if not self.task_history:
            return {'total_generated': 0}
        
        type_counts = {}
        for task in self.task_history:
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
        
        difficulties = [t.difficulty for t in self.task_history]
        
        return {
            'total_generated': len(self.task_history),
            'completed': len(self.completed_tasks),
            'type_distribution': type_counts,
            'avg_difficulty': sum(difficulties) / len(difficulties),
            'difficulty_range': (min(difficulties), max(difficulties)),
            'current_difficulty_trend': self.difficulty_trend
        }


if __name__ == "__main__":
    # 测试
    stream = ContinuousTaskStream()
    
    print("生成10个任务：")
    for i in range(10):
        task = stream.next_task()
        print(f"{i+1}. [{task.task_type}] {task.description}")
        print(f"   难度: {task.difficulty:.2f}, 预计: {task.expected_duration}s")
        print(f"   奖励: {task.reward_potential}")
        print()
    
    stats = stream.get_statistics()
    print(f"统计: {stats}")
