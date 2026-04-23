#!/usr/bin/env python3
"""
任务发现模块 - 让 Agent 自主发现新任务

核心功能:
1. 从历史行为中识别重复模式
2. 评估模式的任务价值
3. 自动生成新任务场景
"""

import numpy as np
from typing import Dict, List, Optional
from collections import Counter
import re


class TaskDiscovery:
    """
    任务发现器
    
    从 Agent 的行为历史中自动发现潜在任务
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.min_pattern_frequency = self.config.get('min_pattern_frequency', 3)
        self.min_task_value = self.config.get('min_task_value', 0.5)
        self.pattern_window = self.config.get('pattern_window', 100)
        
        # 已发现的任务
        self.discovered_tasks: List[Dict] = []
        
    def discover_from_history(self, action_history: List[Dict]) -> List[Dict]:
        """
        从历史行为中发现任务
        
        Args:
            action_history: Agent 的行为历史
            
        Returns:
            发现的任务列表
        """
        if len(action_history) < self.min_pattern_frequency:
            return []
        
        # 1. 提取命令模式
        command_patterns = self._extract_command_patterns(action_history)
        
        # 2. 提取文件操作模式
        file_patterns = self._extract_file_patterns(action_history)
        
        # 3. 提取成功模式
        success_patterns = self._extract_success_patterns(action_history)
        
        # 4. 合并并评估
        all_patterns = command_patterns + file_patterns + success_patterns
        
        # 5. 评估任务价值
        tasks = []
        for pattern in all_patterns:
            task = self._evaluate_as_task(pattern, action_history)
            if task and task['value'] >= self.min_task_value:
                tasks.append(task)
        
        # 6. 去重并排序
        tasks = self._deduplicate_tasks(tasks)
        tasks.sort(key=lambda x: x['value'], reverse=True)
        
        # 7. 保存发现的任务
        self.discovered_tasks.extend(tasks[:5])  # 只保留前5个
        
        return tasks[:5]
    
    def _extract_command_patterns(self, history: List[Dict]) -> List[Dict]:
        """提取命令使用模式"""
        commands = []
        for h in history:
            action = h.get('action', {})
            cmd = action.get('command', '')
            if cmd:
                # 提取命令类型
                cmd_type = cmd.split()[0] if ' ' in cmd else cmd
                commands.append(cmd_type)
        
        # 统计频率
        cmd_counts = Counter(commands)
        patterns = []
        
        for cmd, count in cmd_counts.most_common(10):
            if count >= self.min_pattern_frequency:
                patterns.append({
                    'type': 'command',
                    'pattern': cmd,
                    'frequency': count,
                    'description': f'Frequent use of {cmd}'
                })
        
        return patterns
    
    def _extract_file_patterns(self, history: List[Dict]) -> List[Dict]:
        """提取文件操作模式"""
        file_ops = []
        file_extensions = []
        
        for h in history:
            action = h.get('action', {})
            cmd = action.get('command', '')
            
            # 检测文件操作
            if any(op in cmd for op in ['ls', 'find', 'cat', 'mv', 'cp', 'rm']):
                file_ops.append(cmd)
            
            # 检测文件扩展名
            ext_match = re.search(r'\.(\w+)', cmd)
            if ext_match:
                file_extensions.append(ext_match.group(1))
        
        patterns = []
        
        # 文件操作模式
        if len(file_ops) >= self.min_pattern_frequency:
            patterns.append({
                'type': 'file_operation',
                'pattern': 'file_management',
                'frequency': len(file_ops),
                'description': 'Frequent file operations'
            })
        
        # 文件类型模式
        ext_counts = Counter(file_extensions)
        for ext, count in ext_counts.most_common(3):
            if count >= self.min_pattern_frequency:
                patterns.append({
                    'type': 'file_type',
                    'pattern': ext,
                    'frequency': count,
                    'description': f'Frequent {ext} file operations'
                })
        
        return patterns
    
    def _extract_success_patterns(self, history: List[Dict]) -> List[Dict]:
        """提取成功行为模式"""
        successful_actions = []
        
        for h in history:
            result = h.get('result', {})
            if result.get('success'):
                action = h.get('action', {})
                cmd = action.get('command', '')
                if cmd:
                    successful_actions.append(cmd.split()[0] if ' ' in cmd else cmd)
        
        patterns = []
        
        if len(successful_actions) >= self.min_pattern_frequency:
            patterns.append({
                'type': 'success_pattern',
                'pattern': 'successful_execution',
                'frequency': len(successful_actions),
                'description': 'Consistent successful actions'
            })
        
        return patterns
    
    def _evaluate_as_task(self, pattern: Dict, history: List[Dict]) -> Optional[Dict]:
        """评估模式作为任务的价值"""
        # 计算任务价值
        frequency_score = min(pattern['frequency'] / 10, 1.0)  # 频率分
        
        # 检查是否有自动化潜力
        automation_potential = self._check_automation_potential(pattern, history)
        
        # 检查是否有明确目标
        goal_clarity = self._check_goal_clarity(pattern)
        
        # 综合价值
        value = (
            0.4 * frequency_score +
            0.4 * automation_potential +
            0.2 * goal_clarity
        )
        
        if value < self.min_task_value:
            return None
        
        # 生成任务配置
        task_config = self._generate_task_config(pattern)
        
        return {
            'name': task_config['name'],
            'type': task_config['type'],
            'description': pattern['description'],
            'value': value,
            'pattern': pattern,
            'config': task_config,
        }
    
    def _check_automation_potential(self, pattern: Dict, history: List[Dict]) -> float:
        """检查自动化潜力"""
        # 检查是否有重复性
        if pattern['frequency'] >= 5:
            return 0.8
        elif pattern['frequency'] >= 3:
            return 0.6
        else:
            return 0.4
    
    def _check_goal_clarity(self, pattern: Dict) -> float:
        """检查目标清晰度"""
        pattern_type = pattern.get('type', '')
        
        # 文件操作通常有明确目标
        if pattern_type in ['file_operation', 'file_type']:
            return 0.9
        elif pattern_type == 'command':
            return 0.7
        else:
            return 0.5
    
    def _generate_task_config(self, pattern: Dict) -> Dict:
        """生成任务配置"""
        pattern_type = pattern.get('type', '')
        pattern_value = pattern.get('pattern', '')
        
        if pattern_type == 'file_type':
            return {
                'name': f'{pattern_value}_file_management',
                'type': 'file_organization',
                'description': f'Organize {pattern_value} files',
            }
        elif pattern_type == 'command' and pattern_value in ['find', 'grep']:
            return {
                'name': f'{pattern_value}_search_task',
                'type': 'log_analysis',
                'description': f'Systematic {pattern_value} operations',
            }
        elif pattern_type == 'file_operation':
            return {
                'name': 'auto_file_organization',
                'type': 'file_organization',
                'description': 'Automatic file management',
            }
        else:
            return {
                'name': f'discovered_{pattern_value}_task',
                'type': 'system_monitor',
                'description': f'Discovered {pattern_value} task',
            }
    
    def _deduplicate_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """去重任务"""
        seen = set()
        unique_tasks = []
        
        for task in tasks:
            key = task.get('name', '')
            if key not in seen:
                seen.add(key)
                unique_tasks.append(task)
        
        return unique_tasks