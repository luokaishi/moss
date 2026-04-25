"""
TextWorld Understanding - 环境理解模块

解析游戏状态，理解任务目标，进行路径规划
"""

import re
import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import deque


@dataclass
class Room:
    """房间数据结构"""
    name: str
    description: str = ""
    objects: List[str] = field(default_factory=list)
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_name
    visited: bool = False
    visit_count: int = 0
    room_type: str = "generic"


@dataclass
class TaskGoal:
    """任务目标"""
    description: str
    target_object: Optional[str] = None
    target_location: Optional[str] = None
    action_type: str = ""  # take, go, open, etc.
    completed: bool = False
    priority: int = 1


@dataclass
class GameState:
    """游戏状态"""
    current_room: str = ""
    inventory: List[str] = field(default_factory=list)
    score: float = 0.0
    moves: int = 0
    max_score: float = 10.0
    won: bool = False
    lost: bool = False
    task_goals: List[TaskGoal] = field(default_factory=list)


class TextWorldUnderstanding:
    """
    TextWorld 环境理解器
    
    功能：
    1. 解析观察文本
    2. 构建房间图
    3. 识别任务目标
    4. 路径规划
    5. 动作推荐
    """
    
    def __init__(self):
        self.room_graph: Dict[str, Room] = {}
        self.object_locations: Dict[str, str] = {}  # object -> room
        self.inventory: Set[str] = set()
        self.current_room: str = ""
        self.game_state = GameState()
        
        # 任务跟踪
        self.task_goals: List[TaskGoal] = []
        self.completed_tasks: List[TaskGoal] = []
        
        # 历史记录
        self.action_history: List[Tuple[str, str]] = []  # (action, result)
        self.observation_history: List[str] = []
        
        # 学习到的模式
        self.object_importance: Dict[str, float] = {}
        self.action_effectiveness: Dict[str, float] = {}
        
    def parse_observation(self, obs: str, info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        解析观察文本为结构化信息
        
        Args:
            obs: 观察文本
            info: 额外信息
            
        Returns:
            结构化状态字典
        """
        parsed = {
            'current_room': self._extract_room(obs),
            'room_description': self._extract_room_description(obs),
            'inventory': self._extract_inventory(obs),
            'visible_objects': self._extract_visible_objects(obs),
            'exits': self._extract_exits(obs),
            'task_hints': self._extract_task_hints(obs),
        }
        
        # 更新内部状态
        self._update_room_graph(parsed)
        self._update_inventory(parsed['inventory'])
        self._update_object_locations(parsed['current_room'], parsed['visible_objects'])
        
        # 更新游戏状态
        if info:
            self.game_state.score = info.get('score', self.game_state.score)
            self.game_state.moves = info.get('moves', self.game_state.moves)
            self.game_state.max_score = info.get('max_score', self.game_state.max_score)
            self.game_state.won = info.get('won', False)
            self.game_state.lost = info.get('lost', False)
        
        self.current_room = parsed['current_room']
        self.observation_history.append(obs)
        
        return parsed
    
    def _extract_room(self, text: str) -> str:
        """提取当前房间名称"""
        # 匹配 "-= Room Name =-" 格式
        patterns = [
            r'-=\s*([^=]+)\s*=-',
            r'(?:you are in|location)[\s:]*([^.\n]+)',
            r'^\s*([A-Z][a-zA-Z\s]+)\s*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return self.current_room or "unknown"
    
    def _extract_room_description(self, text: str) -> str:
        """提取房间描述"""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-=') and not line.startswith('You'):
                return line
        return ""
    
    def _extract_inventory(self, text: str) -> List[str]:
        """提取库存物品"""
        inventory = []
        
        patterns = [
            r'(?:you are carrying|your inventory|inventory)[\s:]*([^.]+)',
            r'(?:you have|carrying)[\s:]*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                items_text = match.group(1)
                # 分割物品列表
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    if item and item != 'nothing':
                        inventory.append(item)
                break
        
        return inventory
    
    def _extract_visible_objects(self, text: str) -> List[str]:
        """提取可见物品"""
        objects = []
        
        patterns = [
            r'(?:you see|there is|you can see)[\s:]*([^.]+)',
            r'(?:here you can see|visible)[\s:]*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                items_text = match.group(1)
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    if item and 'exit' not in item:
                        objects.append(item)
                break
        
        return objects
    
    def _extract_exits(self, text: str) -> List[str]:
        """提取可用出口"""
        exits = []
        
        patterns = [
            r'(?:exits?|you can go)[\s:]*([^.]+)',
            r'(?:possible exits|directions)[\s:]*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                exits_text = match.group(1)
                directions = re.split(r',\s*|\s+and\s+', exits_text)
                for d in directions:
                    d = d.strip()
                    if d and d not in ['none', '']:
                        exits.append(d)
                break
        
        return exits
    
    def _extract_task_hints(self, text: str) -> List[str]:
        """提取任务提示"""
        hints = []
        
        # 寻找任务相关的关键词
        task_keywords = [
            r'your goal is to\s+([^.]+)',
            r'you must\s+([^.]+)',
            r'quest:\s*([^.]+)',
            r'objective:\s*([^.]+)',
        ]
        
        for pattern in task_keywords:
            match = re.search(pattern, text.lower())
            if match:
                hints.append(match.group(1).strip())
        
        return hints
    
    def _update_room_graph(self, parsed: Dict[str, Any]):
        """更新房间图"""
        room_name = parsed['current_room']
        
        if room_name not in self.room_graph:
            self.room_graph[room_name] = Room(
                name=room_name,
                description=parsed['room_description'],
                room_type=self._classify_room_type(parsed['room_description'])
            )
        
        room = self.room_graph[room_name]
        room.visited = True
        room.visit_count += 1
        room.objects = parsed['visible_objects']
        
        # 更新出口映射
        for exit_dir in parsed['exits']:
            if exit_dir not in room.exits:
                room.exits[exit_dir] = "unknown"  # 将在移动后更新
    
    def _update_inventory(self, inventory: List[str]):
        """更新库存"""
        self.inventory = set(inventory)
        self.game_state.inventory = inventory
    
    def _update_object_locations(self, room: str, objects: List[str]):
        """更新物品位置"""
        for obj in objects:
            self.object_locations[obj] = room
    
    def _classify_room_type(self, description: str) -> str:
        """分类房间类型"""
        text_lower = description.lower()
        
        room_types = {
            'kitchen': ['kitchen', 'cook', 'stove', 'fridge', 'refrigerator', 'food'],
            'bedroom': ['bedroom', 'bed', 'sleep', 'pillow', 'mattress'],
            'living': ['living', 'sofa', 'couch', 'tv', 'television', 'chair'],
            'bathroom': ['bathroom', 'toilet', 'shower', 'bath', 'sink'],
            'hallway': ['hallway', 'corridor', 'hall', 'passage'],
            'garden': ['garden', 'yard', 'outside', 'outdoor', 'flower'],
            'office': ['office', 'desk', 'computer', 'study'],
            'dungeon': ['dungeon', 'cellar', 'basement', 'dark', 'cave'],
            'entrance': ['entrance', 'doorway', 'foyer', 'lobby'],
        }
        
        for room_type, keywords in room_types.items():
            if any(kw in text_lower for kw in keywords):
                return room_type
        
        return "generic"
    
    def update_room_connection(self, from_room: str, direction: str, to_room: str):
        """更新房间连接关系"""
        if from_room in self.room_graph:
            self.room_graph[from_room].exits[direction] = to_room
    
    def plan_path(self, start: str, goal: str) -> List[str]:
        """
        使用 BFS 规划路径
        
        Args:
            start: 起始房间
            goal: 目标房间
            
        Returns:
            动作列表
        """
        if start == goal:
            return []
        
        if start not in self.room_graph or goal not in self.room_graph:
            return []
        
        # BFS
        queue = deque([(start, [])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == goal:
                return path
            
            if current in self.room_graph:
                room = self.room_graph[current]
                for direction, next_room in room.exits.items():
                    if next_room not in visited and next_room != "unknown":
                        visited.add(next_room)
                        queue.append((next_room, path + [f"go {direction}"]))
        
        return []  # 未找到路径
    
    def find_object(self, obj_name: str) -> Optional[str]:
        """查找物品所在房间"""
        # 检查库存
        if obj_name in self.inventory:
            return "inventory"
        
        # 检查已知位置
        return self.object_locations.get(obj_name)
    
    def identify_next_action(self, available_commands: List[str]) -> Tuple[str, float]:
        """
        识别下一步最佳动作
        
        Args:
            available_commands: 可用命令列表
            
        Returns:
            (最佳命令, 置信度)
        """
        if not available_commands:
            return "look", 0.5
        
        # 优先级排序
        scored_commands = []
        
        for cmd in available_commands:
            score = self._score_command(cmd)
            scored_commands.append((cmd, score))
        
        # 排序并返回最佳
        scored_commands.sort(key=lambda x: x[1], reverse=True)
        return scored_commands[0]
    
    def _score_command(self, command: str) -> float:
        """评分命令"""
        cmd_lower = command.lower()
        score = 0.5
        
        # 根据命令类型评分
        if 'take' in cmd_lower:
            # 获取物品通常是有益的
            score += 0.3
            # 重要物品加分
            if any(kw in cmd_lower for kw in ['key', 'coin', 'treasure', 'gem']):
                score += 0.3
        
        elif 'go' in cmd_lower:
            # 移动命令
            score += 0.2
            # 如果当前房间已充分探索，鼓励移动
            if self.current_room in self.room_graph:
                room = self.room_graph[self.current_room]
                if room.visit_count > 2:
                    score += 0.2
        
        elif 'open' in cmd_lower or 'unlock' in cmd_lower:
            # 开启/解锁通常与任务相关
            score += 0.4
            if 'key' in self.inventory:
                score += 0.2
        
        elif 'examine' in cmd_lower or 'look' in cmd_lower:
            # 查看命令 - 在未探索区域更有价值
            score += 0.1
            if self.current_room in self.room_graph:
                room = self.room_graph[self.current_room]
                if room.visit_count <= 1:
                    score += 0.2
        
        elif 'inventory' in cmd_lower:
            # 查看库存
            score += 0.1
            if len(self.inventory) > 0:
                score += 0.1
        
        # 避免重复动作
        recent_actions = [a[0] for a in self.action_history[-3:]]
        if command in recent_actions:
            score -= 0.3
        
        return max(0.1, min(1.0, score))
    
    def get_suggested_actions(self, available_commands: List[str], top_k: int = 3) -> List[Tuple[str, float]]:
        """获取建议的动作列表"""
        scored = [(cmd, self._score_command(cmd)) for cmd in available_commands]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    def learn_from_outcome(self, action: str, observation: str, reward: float):
        """从结果中学习"""
        self.action_history.append((action, observation))
        
        # 更新动作有效性
        if action not in self.action_effectiveness:
            self.action_effectiveness[action] = 0.5
        
        # 指数移动平均
        self.action_effectiveness[action] = 0.9 * self.action_effectiveness[action] + 0.1 * reward
        
        # 提取物品重要性
        if reward > 0:
            for obj in self.object_locations:
                if obj in action.lower():
                    if obj not in self.object_importance:
                        self.object_importance[obj] = 0.0
                    self.object_importance[obj] += reward
    
    def get_state_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            'current_room': self.current_room,
            'rooms_discovered': len(self.room_graph),
            'rooms_visited': sum(1 for r in self.room_graph.values() if r.visited),
            'inventory': list(self.inventory),
            'objects_found': len(self.object_locations),
            'score': self.game_state.score,
            'moves': self.game_state.moves,
            'task_progress': self.game_state.score / max(self.game_state.max_score, 1),
        }
    
    def reset(self):
        """重置理解器状态"""
        self.room_graph.clear()
        self.object_locations.clear()
        self.inventory.clear()
        self.current_room = ""
        self.game_state = GameState()
        self.task_goals.clear()
        self.completed_tasks.clear()
        self.action_history.clear()
        self.observation_history.clear()
        self.object_importance.clear()
        self.action_effectiveness.clear()