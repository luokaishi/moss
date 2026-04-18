"""
TextWorld 任务解析器

解析观察文本，提取任务状态和目标
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TaskState:
    """任务状态"""
    current_room: str
    inventory: List[str]
    visible_objects: List[str]
    available_exits: List[str]
    task_goal: Optional[str]
    progress: float  # 0.0 - 1.0


class TextWorldTaskParser:
    """TextWorld 观察文本解析器"""
    
    def __init__(self):
        # 房间匹配模式
        self.room_patterns = [
            r'(?i)-=\s*([^=]+)\s*=-',  # -= Room Name =-
            r'(?i)(?:you are in|this is)\s+(?:the\s+)?([\w\s]+?)(?:\.|\n|$)',
            r'(?i)(?:room|location):\s*([\w\s]+?)(?:\.|\n|$)',
            r'(?i)^\s*([A-Z][a-zA-Z\s]+)\s*$',  # 单独一行的房间名
        ]
        
        # 物品匹配模式
        self.object_patterns = [
            r'(?i)(?:you see|there is|you can see):?\s*([^.]+)',
            r'(?i)(?:here you can see|visible):\s*([^.]+)',
            r'(?i)(?:on the|in the)\s+(\w+)\s+(?:is|are)\s+([^.]+)',
        ]
        
        # 出口匹配模式
        self.exit_patterns = [
            r'(?i)(?:exits?|you can go):?\s*([^.]+)',
            r'(?i)(?:possible exits|directions):\s*([^.]+)',
            r'(?i)(?:there is\s+(?:a\s+)?(?:exit|door|way)\s+(?:to\s+)?(\w+))',
        ]
        
        # 库存匹配模式
        self.inventory_patterns = [
            r'(?i)(?:you are carrying|your inventory|inventory):\s*([^.]+)',
            r'(?i)(?:you have|carrying):\s*([^.]+)',
        ]
        
        # 任务目标匹配模式
        self.goal_patterns = [
            r'(?i)(?:your goal|task|objective|quest|mission):\s*([^.]+(?:\.[^.]+)*)',
            r'(?i)(?:you need to|you must|goal is to)\s+([^.]+(?:\.[^.]+)*)',
        ]
        
        # 进度指示模式
        self.progress_patterns = [
            r'(?i)(\d+)/\d+\s+(?:points?|score|steps?|moves?)',
            r'(?i)(\d+)%\s+(?:complete|done|finished)',
            r'(?i)(?:score|points?):\s*(\d+(?:\.\d+)?)',
        ]
    
    def parse(self, observation: str) -> TaskState:
        """解析观察文本"""
        return TaskState(
            current_room=self._extract_room(observation),
            inventory=self._extract_inventory(observation),
            visible_objects=self._extract_objects(observation),
            available_exits=self._extract_exits(observation),
            task_goal=self._extract_goal(observation),
            progress=self._estimate_progress(observation)
        )
    
    def _extract_room(self, text: str) -> str:
        """提取当前房间"""
        for pattern in self.room_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                room = match.group(1).strip()
                # 清理房间名
                room = re.sub(r'\s+', ' ', room)
                if len(room) > 1 and not room.lower() in ['here', 'there']:
                    return room
        return "unknown"
    
    def _extract_inventory(self, text: str) -> List[str]:
        """提取库存物品"""
        inventory = []
        
        for pattern in self.inventory_patterns:
            match = re.search(pattern, text.lower())
            if match:
                items_text = match.group(1)
                # 分割物品列表
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    # 移除冠词和数量
                    item = re.sub(r'^(a|an|the|some|\d+)\s+', '', item)
                    # 移除状态描述
                    item = re.sub(r'\s*\([^)]*\)', '', item)
                    if item and item not in ['nothing', 'empty', 'none']:
                        inventory.append(item)
                break
        
        return inventory
    
    def _extract_objects(self, text: str) -> List[str]:
        """提取可见物品"""
        objects = []
        
        for pattern in self.object_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                if len(match.groups()) >= 2:
                    items_text = match.group(2) if match.group(2) else match.group(1)
                else:
                    items_text = match.group(1)
                
                # 分割物品列表
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    # 移除冠词
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    # 移除状态描述
                    item = re.sub(r'\s*\([^)]*\)', '', item)
                    # 提取核心名词（移除形容词）
                    item = self._extract_noun(item)
                    if item and len(item) > 1:
                        objects.append(item)
        
        # 去重并保持顺序
        seen = set()
        unique_objects = []
        for obj in objects:
            if obj not in seen:
                seen.add(obj)
                unique_objects.append(obj)
        
        return unique_objects
    
    def _extract_exits(self, text: str) -> List[str]:
        """提取可用出口"""
        exits = []
        
        for pattern in self.exit_patterns:
            match = re.search(pattern, text.lower())
            if match:
                exits_text = match.group(1)
                # 分割方向
                directions = re.split(r',\s*|\s+and\s+', exits_text)
                for direction in directions:
                    direction = direction.strip()
                    # 清理方向描述
                    direction = re.sub(r'^(?:to\s+|the\s+)?', '', direction)
                    direction = re.sub(r'\s+(?:exit|door|way)$', '', direction)
                    if direction and direction not in ['none', 'nowhere']:
                        exits.append(direction)
                break
        
        return exits
    
    def _extract_goal(self, text: str) -> Optional[str]:
        """提取任务目标"""
        for pattern in self.goal_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                goal = match.group(1).strip()
                # 清理目标描述
                goal = re.sub(r'\s+', ' ', goal)
                if len(goal) > 5:
                    return goal
        
        # 如果没有明确的目标描述，尝试从上下文推断
        if 'key' in text.lower() and 'door' in text.lower():
            return "Find the key and unlock the door"
        if 'take' in text.lower() or 'collect' in text.lower():
            return "Collect required items"
        
        return None
    
    def _estimate_progress(self, text: str) -> float:
        """估计任务进度"""
        progress = 0.0
        
        # 尝试从分数计算进度
        for pattern in self.progress_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    value = float(match.group(1))
                    # 如果是分数格式 (x/y)
                    if '/' in text[match.start():match.end()]:
                        # 尝试找到总分
                        full_match = re.search(r'(\d+)/(\d+)', text[match.start():match.end()])
                        if full_match:
                            current = float(full_match.group(1))
                            total = float(full_match.group(2))
                            if total > 0:
                                return current / total
                    else:
                        # 假设满分是 10 或 100
                        if value <= 1.0:
                            return value
                        elif value <= 10.0:
                            return value / 10.0
                        else:
                            return min(value / 100.0, 1.0)
                except (ValueError, IndexError):
                    continue
        
        # 基于关键词推断进度
        text_lower = text.lower()
        progress_keywords = {
            'won': 1.0,
            'victory': 1.0,
            'completed': 1.0,
            'success': 1.0,
            'finished': 1.0,
            'lost': 0.0,
            'failed': 0.0,
            'died': 0.0,
            'game over': 0.0,
        }
        
        for keyword, prog in progress_keywords.items():
            if keyword in text_lower:
                return prog
        
        # 基于库存物品数量粗略估计
        inventory = self._extract_inventory(text)
        if inventory:
            # 假设有物品表示有一定进度
            progress = min(len(inventory) * 0.1, 0.5)
        
        return progress
    
    def _extract_noun(self, phrase: str) -> str:
        """从短语中提取核心名词"""
        # 移除常见形容词和冠词
        words_to_remove = [
            'a', 'an', 'the', 'some', 'small', 'large', 'big', 'tiny',
            'old', 'new', 'red', 'blue', 'green', 'yellow', 'metal', 'wooden',
            'heavy', 'light', 'shiny', 'rusty', 'closed', 'open', 'locked',
            'unlocked', 'empty', 'full'
        ]
        
        words = phrase.lower().split()
        filtered = [w for w in words if w not in words_to_remove]
        
        if filtered:
            return ' '.join(filtered)
        return phrase
    
    def parse_action_suggestion(self, observation: str, task_state: TaskState) -> List[str]:
        """
        基于任务状态生成建议动作
        
        Returns:
            建议动作列表（按优先级排序）
        """
        suggestions = []
        
        # 如果有目标，尝试解析目标类型
        if task_state.task_goal:
            goal_lower = task_state.task_goal.lower()
            
            # 钥匙和门类型目标
            if 'key' in goal_lower and 'door' in goal_lower:
                # 检查是否有钥匙
                has_key = any('key' in item.lower() for item in task_state.inventory)
                
                if not has_key:
                    # 建议寻找钥匙
                    for obj in task_state.visible_objects:
                        if 'key' in obj.lower():
                            suggestions.append(f"take {obj}")
                            suggestions.append(f"examine {obj}")
                else:
                    # 建议去门那里
                    for obj in task_state.visible_objects:
                        if 'door' in obj.lower():
                            suggestions.append(f"open {obj}")
                            suggestions.append(f"unlock {obj}")
                    # 建议移动
                    for exit_dir in task_state.available_exits:
                        suggestions.append(f"go {exit_dir}")
            
            # 收集物品类型目标
            elif 'collect' in goal_lower or 'take' in goal_lower or 'find' in goal_lower:
                for obj in task_state.visible_objects:
                    suggestions.append(f"take {obj}")
                    suggestions.append(f"examine {obj}")
        
        # 通用建议
        if not suggestions:
            # 探索建议
            for exit_dir in task_state.available_exits:
                suggestions.append(f"go {exit_dir}")
            
            # 检查物品
            for obj in task_state.visible_objects:
                suggestions.append(f"examine {obj}")
            
            # 基础命令
            suggestions.extend(['look', 'inventory'])
        
        return suggestions
    
    def get_state_summary(self, task_state: TaskState) -> str:
        """生成任务状态摘要"""
        lines = [
            "=" * 50,
            "Task State Summary",
            "=" * 50,
            f"Current Room: {task_state.current_room}",
            f"Progress: {task_state.progress:.1%}",
        ]
        
        if task_state.task_goal:
            lines.append(f"Goal: {task_state.task_goal}")
        
        lines.extend([
            "",
            f"Inventory ({len(task_state.inventory)} items):",
        ])
        
        if task_state.inventory:
            for item in task_state.inventory:
                lines.append(f"  - {item}")
        else:
            lines.append("  (empty)")
        
        lines.extend([
            "",
            f"Visible Objects ({len(task_state.visible_objects)}):",
        ])
        
        if task_state.visible_objects:
            for obj in task_state.visible_objects:
                lines.append(f"  - {obj}")
        else:
            lines.append("  none")
        
        lines.extend([
            "",
            f"Available Exits: {', '.join(task_state.available_exits) or 'none'}",
            "=" * 50,
        ])
        
        return "\n".join(lines)