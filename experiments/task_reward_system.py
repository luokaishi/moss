#!/usr/bin/env python3
"""
任务奖励系统 - 让 Agent 能学习具体任务
为文件整理等实用任务提供明确的奖励信号
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

class TaskRewardSystem:
    """
    任务奖励系统
    
    为 Agent 提供任务级别的奖励，而不仅是动作成功/失败
    """
    
    def __init__(self, task_type='file_organization'):
        self.task_type = task_type
        self.initial_state = None
        self.target_state = None
        
    def set_task(self, task_config):
        """设置当前任务"""
        self.task_type = task_config.get('type', 'file_organization')
        self.initial_state = task_config.get('initial_state')
        self.target_state = task_config.get('target_state')
        
    def compute_reward(self, action_result, current_state):
        """
        计算任务级奖励
        
        结合:
        1. 动作成功奖励 (0/1)
        2. 任务进展奖励 (向目标状态靠近的程度)
        3. 完成奖励 (达到目标状态)
        """
        # 基础动作奖励
        action_reward = 1.0 if action_result.get('success') else 0.0
        
        # 任务进展奖励
        progress_reward = self._compute_progress(current_state)
        
        # 完成奖励
        completion_reward = self._check_completion(current_state)
        
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
    
    def _compute_progress(self, current_state):
        """计算向目标状态的进展"""
        if self.task_type == 'file_organization':
            return self._file_org_progress(current_state)
        return 0.0
    
    def _file_org_progress(self, state):
        """文件整理任务进展"""
        # 检查文件是否被移动到正确位置
        if not state or 'files' not in state:
            return 0.0
        
        files = state.get('files', [])
        total = len(files)
        if total == 0:
            return 1.0  # 全部整理完成
        
        # 统计已分类的文件
        organized = sum(1 for f in files if f.get('in_correct_folder', False))
        return organized / total
    
    def _check_completion(self, current_state):
        """检查任务是否完成"""
        if self.task_type == 'file_organization':
            progress = self._file_org_progress(current_state)
            return 1.0 if progress >= 0.95 else 0.0
        return 0.0


# 演示
if __name__ == '__main__':
    print("=" * 70)
    print("任务奖励系统演示")
    print("=" * 70)
    
    reward_system = TaskRewardSystem('file_organization')
    
    # 模拟任务状态
    initial_state = {
        'files': [
            {'name': 'photo.jpg', 'in_correct_folder': False},
            {'name': 'doc.pdf', 'in_correct_folder': False},
            {'name': 'script.py', 'in_correct_folder': False},
        ]
    }
    
    print("\n初始状态: 3 个文件待整理")
    
    # 模拟动作结果
    action_result = {'success': True, 'command': 'mv photo.jpg images/'}
    
    # 模拟移动一个文件后的状态
    current_state = {
        'files': [
            {'name': 'photo.jpg', 'in_correct_folder': True},
            {'name': 'doc.pdf', 'in_correct_folder': False},
            {'name': 'script.py', 'in_correct_folder': False},
        ]
    }
    
    reward = reward_system.compute_reward(action_result, current_state)
    
    print(f"\n动作: mv photo.jpg images/")
    print(f"奖励分解:")
    print(f"  动作奖励: {reward['action']:.2f}")
    print(f"  进展奖励: {reward['progress']:.2f} (1/3 文件已整理)")
    print(f"  完成奖励: {reward['completion']:.2f}")
    print(f"  总奖励: {reward['total']:.3f}")
    
    # 模拟完成状态
    completed_state = {
        'files': [
            {'name': 'photo.jpg', 'in_correct_folder': True},
            {'name': 'doc.pdf', 'in_correct_folder': True},
            {'name': 'script.py', 'in_correct_folder': True},
        ]
    }
    
    reward_complete = reward_system.compute_reward(action_result, completed_state)
    
    print(f"\n任务完成状态:")
    print(f"  进展奖励: {reward_complete['progress']:.2f}")
    print(f"  完成奖励: {reward_complete['completion']:.2f} ✅")
    print(f"  总奖励: {reward_complete['total']:.3f}")
    
    print("\n" + "=" * 70)
    print("任务奖励系统可集成到 Agent 中，提供明确的任务导向信号")
    print("=" * 70)
