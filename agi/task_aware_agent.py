"""
TaskAwareAgent - 任务感知 Agent

集成任务奖励系统，支持具体任务学习
"""

import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.agent import AGIAgent
from agi.environment import EnvState
from typing import Dict, List, Optional, Callable
import logging
import random

logger = logging.getLogger('TaskAwareAgent')


class TaskRewardSystem:
    """任务奖励系统"""
    
    def __init__(self, task_type='file_organization'):
        self.task_type = task_type
        self.initial_state = None
        self.target_state = None
        self.task_progress = 0.0
        
    def set_task(self, task_config: Dict):
        """设置当前任务"""
        self.task_type = task_config.get('type', 'file_organization')
        self.initial_state = task_config.get('initial_state')
        self.target_state = task_config.get('target_state')
        self.task_progress = 0.0
        logger.info(f"Task set: {self.task_type}")
        
    def compute_reward(self, action_result: Dict, env_state: EnvState) -> Dict:
        """
        计算任务级奖励
        
        Returns:
            {
                'total': float,      # 总奖励
                'action': float,     # 动作成功奖励
                'progress': float,   # 任务进展奖励
                'completion': float, # 完成奖励
            }
        """
        # 基础动作奖励
        action_reward = 1.0 if action_result.get('success') else 0.0
        
        # 任务进展奖励
        progress_reward = self._compute_progress(env_state)
        
        # 完成奖励
        completion_reward = self._check_completion(env_state)
        
        # 加权组合
        total_reward = (
            0.2 * action_reward +
            0.3 * progress_reward +
            0.5 * completion_reward
        )
        
        return {
            'total': total_reward,
            'action': action_reward,
            'progress': progress_reward,
            'completion': completion_reward,
        }
    
    def _compute_progress(self, env_state: EnvState) -> float:
        """计算任务进展"""
        if self.task_type == 'file_organization':
            return self._file_org_progress(env_state)
        return 0.0
    
    def _file_org_progress(self, state: EnvState) -> float:
        """文件整理任务进展"""
        # 从环境状态中提取文件信息
        # 这里简化处理，实际应该检查文件位置
        # 返回 0-1 之间的进展值
        return getattr(state, 'task_progress', 0.0)
    
    def _check_completion(self, env_state: EnvState) -> float:
        """检查任务是否完成"""
        if self.task_type == 'file_organization':
            progress = self._file_org_progress(env_state)
            return 1.0 if progress >= 0.95 else 0.0
        return 0.0
    
    def update_progress(self, progress: float):
        """外部更新任务进展"""
        self.task_progress = progress


class TaskAwareAgent(AGIAgent):
    """
    任务感知 Agent
    
    扩展 AGIAgent，添加任务奖励支持
    """
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.task_reward_system: Optional[TaskRewardSystem] = None
        self.current_task: Optional[Dict] = None
        self.task_history: List[Dict] = []
        
    def set_task(self, task_config: Dict):
        """设置当前任务"""
        self.task_reward_system = TaskRewardSystem(task_config.get('type'))
        self.task_reward_system.set_task(task_config)
        self.current_task = task_config
        self.task_history = []
        logger.info(f"Task set: {task_config.get('type')}")
        
    def _one_cycle(self):
        """执行任务周期（带任务奖励）"""
        # 1. 感知环境
        state = self.env.perceive()
        
        # 2. 检索记忆
        state_desc = self._state_to_query(state)
        relevant_memories = self.memory.recall(state_desc, top_k=3)
        
        # 3. 评估驱动力
        drive_scores = self.drive_manager.evaluate_all(state)
        best_drive = max(drive_scores, key=drive_scores.get) if drive_scores else 'none'
        
        # 4. 生成候选行动并选择
        # Phase 3: 任务感知动作生成
        task_context = self.current_task if self.current_task else None
        candidates = self.env.generate_action_candidates(state, task_context)
        
        # 如果有记忆，加入记忆相关的行动
        if relevant_memories:
            mem_action = self._memory_to_action(relevant_memories[0])
            if mem_action:
                candidates.append(mem_action)
        
        # 任务感知：优先选择与任务相关的行动
        if self.current_task and self.task_reward_system:
            candidates = self._prioritize_task_actions(candidates, self.current_task)
            # 强制选择任务相关动作 (80% 概率)
            task_candidates = [c for c in candidates if c.get('task_relevant')]
            if task_candidates and random.random() < 0.8:
                action = random.choice(task_candidates)
            else:
                action = self.drive_manager.get_weighted_action(state, candidates)
        else:
            action = self.drive_manager.get_weighted_action(state, candidates)
        
        # 5. 执行行动
        if action:
            result = self.env.execute(action)
        else:
            result = self.env.execute({
                'type': 'shell',
                'command': 'ls -la',
                'drives': ['curiosity']
            })
            action = {'description': 'default explore'}
        
        # 6. 任务感知奖励计算
        if self.task_reward_system:
            task_reward = self.task_reward_system.compute_reward(result, state)
            reward = task_reward['total']
            
            # 存储任务经验
            self._store_task_experience(action, result, task_reward, best_drive)
        else:
            reward = 1.0 if result.get('success') else 0.0
            
        # 7. 更新驱动权重（使用任务奖励）
        self.drive_manager.update_weight_from_feedback(best_drive, reward, lr=0.05)
        
        # 8. 记录行为
        self.behavior_tracker.record(action, result, reward, drive_used=best_drive)
        
        # 9. 记录状态到 GP 缓冲区
        self._record_emergence_state()
        
        # 10. 尝试涌现检测
        self._try_emergence()
    
    def _prioritize_task_actions(self, candidates: List[Dict], task: Dict) -> List[Dict]:
        """优先选择与任务相关的行动"""
        task_type = task.get('type', '')
        
        if task_type == 'file_organization':
            # 优先 mv 命令
            task_actions = []
            other_actions = []
            
            for action in candidates:
                cmd = action.get('command', '')
                if 'mv ' in cmd or 'move' in cmd.lower():
                    action['task_priority'] = 2.0  # 高优先级
                    task_actions.append(action)
                elif 'ls' in cmd or 'find' in cmd:
                    action['task_priority'] = 1.5  # 中优先级（观察）
                    task_actions.append(action)
                else:
                    action['task_priority'] = 1.0
                    other_actions.append(action)
            
            # 排序：task_actions 在前
            return sorted(task_actions + other_actions, 
                         key=lambda x: x.get('task_priority', 1.0), reverse=True)
        
        return candidates
    
    def _store_task_experience(self, action: Dict, result: Dict, task_reward: Dict, drive: str):
        """存储任务经验"""
        experience = (
            f"Task cycle {self.cycle}: {action.get('description', 'unknown')} -> "
            f"reward={task_reward['total']:.2f} "
            f"(action={task_reward['action']:.1f}, progress={task_reward['progress']:.2f}, completion={task_reward['completion']:.1f})"
        )
        
        self.memory.store(
            content=experience,
            memory_type='task_experience',
            importance=0.4 + 0.6 * task_reward['total'],
            tags=['task', drive, self.current_task.get('type', 'unknown')],
            metadata={
                'cycle': self.cycle,
                'drive': drive,
                'reward': task_reward['total'],
                'progress': task_reward['progress'],
                'completion': task_reward['completion'],
            }
        )
        
        # 记录任务历史
        self.task_history.append({
            'cycle': self.cycle,
            'action': action,
            'reward': task_reward,
            'drive': drive,
        })
    
    def get_task_summary(self) -> Dict:
        """获取任务执行摘要"""
