"""
Enhanced TextWorld Understanding - v6.5

深度环境理解，提升泛化能力
"""

import re
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class RoomNode:
    """房间节点"""
    name: str
    description: str = ""
    objects: Set[str] = field(default_factory=set)
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_name
    visited: bool = False
    visit_count: int = 0
    room_type: str = "generic"
    last_visit_step: int = 0


@dataclass
class ObjectInfo:
    """物品信息"""
    name: str
    location: str = "unknown"
    is_portable: bool = True
    is_container: bool = False
    is_locked: bool = False
    importance: float = 0.5
    last_seen: int = 0


@dataclass
class TaskInfo:
    """任务信息"""
    description: str = ""
    task_type: str = "unknown"  # find, take, go, open, etc.
    target_object: Optional[str] = None
    target_location: Optional[str] = None
    required_items: Set[str] = field(default_factory=set)
    completed: bool = False
    progress: float = 0.0


class EnhancedTextWorldUnderstanding:
    """增强型 TextWorld 理解器 - v6.5"""
    
    def __init__(self):
        # 房间图
        self.room_graph: Dict[str, RoomNode] = {}
        self.current_room: str = ""
        self.previous_room: str = ""
        
        # 物品跟踪
        self.objects: Dict[str, ObjectInfo] = {}  # 物品名 -> 信息
        self.inventory: Set[str] = set()
        self.dropped_items: Set[str] = set()  # 记录丢弃的物品
        
        # 任务状态
        self.task: TaskInfo = TaskInfo()
        self.sub_goals: List[str] = []
        self.completed_goals: List[str] = []
        
        # 动作历史
        self.action_history: List[Tuple[str, str, float]] = []  # (action, result, reward)
        self.successful_patterns: List[Dict] = []
        
        # 失败学习
        self.failed_actions: Dict[str, int] = defaultdict(int)
        self.failed_patterns: Set[str] = set()
        
        # 环境统计
        self.step_count: int = 0
        self.unique_interactions: Set[str] = set()
        self.exploration_score: float = 0.0
        
        # 泛化支持：环境无关的特征
        self.room_types_discovered: Set[str] = set()
        self.object_categories: Dict[str, Set[str]] = defaultdict(set)
        
    def parse_observation(self, obs: str, info: Optional[Dict] = None) -> Dict[str, Any]:
        """深度解析观察"""
        parsed = {
            'room': self._extract_room(obs),
            'room_type': self._classify_room_type(obs),
            'exits': self._extract_exits(obs),
            'objects': self._extract_objects(obs),
            'inventory': self._extract_inventory(obs),
            'task': self._extract_task(obs),
            'score': self._extract_score(obs) if info else 0.0,
            'moves': self._extract_moves(obs) if info else 0,
            'won': info.get('won', False) if info else False,
            'lost': info.get('lost', False) if info else False,
        }
        
        # 更新内部状态
        self._update_room_graph(parsed['room'], parsed['room_type'], 
                                parsed['exits'], parsed['objects'])
        self._update_objects(parsed['objects'], parsed['room'])
        self._update_inventory(parsed['inventory'])
        self._update_task(parsed['task'])
        
        self.previous_room = self.current_room
        self.current_room = parsed['room']
        self.step_count += 1
        
        return parsed
    
    def _extract_room(self, text: str) -> str:
        """提取当前房间名称"""
        # 匹配 "-= Room Name =-" 格式
        patterns = [
            r'-=\s*([^=]+)\s*=-',
            r'(?:you are in|location)[\s:]*([^\.\n]+)',
            r'^\s*([A-Z][a-zA-Z\s]+)\s*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return self.current_room or "unknown"
    
    def _classify_room_type(self, text: str) -> str:
        """分类房间类型"""
        text_lower = text.lower()
        
        room_types = {
            'kitchen': ['kitchen', 'cook', 'stove', 'fridge', 'refrigerator', 'food', 'pantry'],
            'bedroom': ['bedroom', 'bed', 'sleep', 'pillow', 'mattress', 'dresser'],
            'living': ['living', 'sofa', 'couch', 'tv', 'television', 'chair', 'lounge'],
            'bathroom': ['bathroom', 'toilet', 'shower', 'bath', 'sink'],
            'hallway': ['hallway', 'corridor', 'hall', 'passage'],
            'garden': ['garden', 'yard', 'outside', 'outdoor', 'flower', 'backyard'],
            'office': ['office', 'desk', 'computer', 'study', 'work'],
            'dungeon': ['dungeon', 'cellar', 'basement', 'dark', 'cave'],
            'entrance': ['entrance', 'doorway', 'foyer', 'lobby', 'entry'],
            'storage': ['storage', 'closet', 'cabinet', 'box', 'chest'],
        }
        
        for room_type, keywords in room_types.items():
            if any(kw in text_lower for kw in keywords):
                self.room_types_discovered.add(room_type)
                return room_type
        
        return "generic"
    
    def _extract_exits(self, text: str) -> List[str]:
        """提取可用出口"""
        exits = []
        
        patterns = [
            r'(?:exits?|you can go)[\s:]*([^.]+)',
            r'(?:possible exits|directions)[\s:]*([^.]+)',
            r'(?:there is|you see)\s+(?:an?\s+)?exit\s+(?:to\s+)?(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                exits_text = match.group(1)
                # 分割方向
                directions = re.split(r',\s*|\s+and\s+', exits_text)
                for d in directions:
                    d = d.strip()
                    if d and d not in ['none', '']:
                        exits.append(d)
                break
        
        # 如果没有找到，尝试其他模式
        if not exits:
            dir_patterns = [
                r'\b(north|south|east|west|up|down|inside|outside)\b',
                r'\b(n|s|e|w)\b',
            ]
            for pattern in dir_patterns:
                matches = re.findall(pattern, text.lower())
                exits.extend(matches)
        
        return list(set(exits))  # 去重
    
    def _extract_objects(self, text: str) -> List[str]:
        """提取可见物品"""
        objects = []
        
        patterns = [
            r'(?:you see|there is|you can see)[\s:]*([^.]+)',
            r'(?:here you can see|visible)[\s:]*([^.]+)',
            r'(?:on the|in the)\s+\w+\s+(?:you see|is)\s+([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                items_text = match.group(1)
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    if item and 'exit' not in item and len(item) > 1:
                        objects.append(item)
        
        return objects
    
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
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    if item and item != 'nothing':
                        inventory.append(item)
                break
        
        return inventory
    
    def _extract_task(self, text: str) -> str:
        """提取任务描述"""
        patterns = [
            r'your goal is to\s+([^.]+)',
            r'you must\s+([^.]+)',
            r'quest:\s*([^.]+)',
            r'objective:\s*([^.]+)',
            r'mission:\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return self.task.description if self.task else ""
    
    def _extract_score(self, text: str) -> float:
        """提取分数"""
        match = re.search(r'score[:\s]+(\d+)', text.lower())
        if match:
            return float(match.group(1))
        return 0.0
    
    def _extract_moves(self, text: str) -> int:
        """提取步数"""
        match = re.search(r'moves?[:\s]+(\d+)', text.lower())
        if match:
            return int(match.group(1))
        return 0
    
    def _update_room_graph(self, room_name: str, room_type: str, 
                           exits: List[str], objects: List[str]):
        """更新房间图"""
        if room_name not in self.room_graph:
            self.room_graph[room_name] = RoomNode(
                name=room_name,
                room_type=room_type
            )
        
        room = self.room_graph[room_name]
        room.visited = True
        room.visit_count += 1
        room.last_visit_step = self.step_count
        room.objects = set(objects)
        
        # 更新出口
        for exit_dir in exits:
            if exit_dir not in room.exits:
                room.exits[exit_dir] = "unknown"
    
    def _update_objects(self, objects: List[str], room: str):
        """更新物品信息"""
        for obj_name in objects:
            if obj_name not in self.objects:
                self.objects[obj_name] = ObjectInfo(name=obj_name)
            
            obj = self.objects[obj_name]
            obj.location = room
            obj.last_seen = self.step_count
            
            # 分类物品
            self._categorize_object(obj_name)
    
    def _categorize_object(self, obj_name: str):
        """分类物品类型"""
        obj_lower = obj_name.lower()
        
        # 关键物品
        if any(kw in obj_lower for kw in ['key', 'keys']):
            self.object_categories['key'].add(obj_name)
        
        # 容器
        if any(kw in obj_lower for kw in ['chest', 'box', 'cabinet', 'drawer', 'door']):
            self.object_categories['container'].add(obj_name)
            if obj_name in self.objects:
                self.objects[obj_name].is_container = True
        
        # 食物
        if any(kw in obj_lower for kw in ['food', 'apple', 'bread', 'meal']):
            self.object_categories['food'].add(obj_name)
        
        # 工具
        if any(kw in obj_lower for kw in ['knife', 'tool', 'instrument']):
            self.object_categories['tool'].add(obj_name)
        
        # 贵重物品
        if any(kw in obj_lower for kw in ['coin', 'gold', 'treasure', 'gem', 'jewel']):
            self.object_categories['valuable'].add(obj_name)
            if obj_name in self.objects:
                self.objects[obj_name].importance = 0.9
    
    def _update_inventory(self, inventory: List[str]):
        """更新库存状态"""
        new_inventory = set(inventory)
        
        # 检测新获得的物品
        for item in new_inventory - self.inventory:
            if item in self.objects:
                self.objects[item].location = "inventory"
                self.objects[item].importance += 0.1
        
        # 检测丢失的物品
        for item in self.inventory - new_inventory:
            if item in self.objects:
                self.dropped_items.add(item)
        
        self.inventory = new_inventory
    
    def _update_task(self, task_desc: str):
        """更新任务信息"""
        if not task_desc:
            return
        
        self.task.description = task_desc
        
        # 解析任务类型
        task_lower = task_desc.lower()
        
        if any(kw in task_lower for kw in ['find', 'locate', 'search']):
            self.task.task_type = "find"
        elif any(kw in task_lower for kw in ['take', 'get', 'pick', 'grab', 'collect']):
            self.task.task_type = "take"
        elif any(kw in task_lower for kw in ['go', 'move', 'walk', 'enter']):
            self.task.task_type = "go"
        elif any(kw in task_lower for kw in ['open', 'unlock']):
            self.task.task_type = "open"
        elif any(kw in task_lower for kw in ['drop', 'put', 'place']):
            self.task.task_type = "place"
        elif any(kw in task_lower for kw in ['eat', 'consume']):
            self.task.task_type = "eat"
        elif any(kw in task_lower for kw in ['cook', 'prepare']):
            self.task.task_type = "cook"
        
        # 提取目标物品
        self.task.target_object = self._extract_target_from_task(task_desc)
        
        # 提取目标位置
        self.task.target_location = self._extract_location_from_task(task_desc)
    
    def _extract_target_from_task(self, task: str) -> Optional[str]:
        """从任务中提取目标物品"""
        # 寻找物品关键词
        patterns = [
            r'(?:find|take|get|pick)\s+(?:up\s+)?(?:the\s+)?(\w+)',
            r'(?:a|an|the)\s+(\w+\s+\w+)',  # 复合名词
            r'(?:a|an|the)\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, task.lower())
            if match:
                target = match.group(1).strip()
                # 排除常见非物品词
                if target not in ['there', 'here', 'room', 'way', 'place']:
                    return target
        
        return None
    
    def _extract_location_from_task(self, task: str) -> Optional[str]:
        """从任务中提取目标位置"""
        patterns = [
            r'(?:go|move|walk)\s+(?:to\s+)?(?:the\s+)?(\w+)',
            r'(?:in|into|to)\s+(?:the\s+)?(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, task.lower())
            if match:
                return match.group(1).strip()
        
        return None
    
    def plan_next_action(self, parsed_obs: Dict, available_actions: List[str]) -> Optional[str]:
        """规划下一步动作"""
        if not available_actions:
            return None
        
        # 1. 如果任务已知，规划完成任务的动作
        if self.task.task_type and self.task.description:
            action = self._plan_for_task(available_actions)
            if action:
                return action
        
        # 2. 探索未访问的房间
        action = self._plan_exploration(parsed_obs, available_actions)
        if action:
            return action
        
        # 3. 与重要物品交互
        action = self._plan_object_interaction(parsed_obs, available_actions)
        if action:
            return action
        
        return None
    
    def _plan_for_task(self, available_actions: List[str]) -> Optional[str]:
        """为当前任务规划动作"""
        task_type = self.task.task_type
        target = self.task.target_object
        
        # 查找目标物品位置
        target_location = None
        if target:
            for obj_name, obj_info in self.objects.items():
                if target.lower() in obj_name.lower():
                    target_location = obj_info.location
                    break
        
        # 根据任务类型规划
        if task_type in ['find', 'take']:
            # 如果物品在库存中，任务可能已完成
            if target and any(target.lower() in item.lower() for item in self.inventory):
                return None
            
            # 如果知道物品位置
            if target_location and target_location != self.current_room:
                if target_location == "inventory":
                    return None  # 已经有了
                
                # 规划路径
                path = self._find_path(self.current_room, target_location)
                if path and len(path) > 0:
                    return path[0]
            
            # 如果物品在当前房间，尝试拿取
            if target_location == self.current_room:
                for action in available_actions:
                    if 'take' in action.lower() and target.lower() in action.lower():
                        return action
        
        elif task_type == 'go':
            target_loc = self.task.target_location
            if target_loc:
                # 检查是否已经在目标位置
                if target_loc.lower() in self.current_room.lower():
                    return None
                
                # 找到目标房间
                for room_name in self.room_graph:
                    if target_loc.lower() in room_name.lower():
                        path = self._find_path(self.current_room, room_name)
                        if path and len(path) > 0:
                            return path[0]
        
        elif task_type == 'open':
            # 需要钥匙
            has_key = any('key' in item.lower() for item in self.inventory)
            
            for action in available_actions:
                action_lower = action.lower()
                if 'open' in action_lower or 'unlock' in action_lower:
                    if has_key or 'key' not in action_lower:
                        return action
        
        return None
    
    def _plan_exploration(self, parsed_obs: Dict, available_actions: List[str]) -> Optional[str]:
        """规划探索动作"""
        exits = parsed_obs.get('exits', [])
        
        # 优先去未访问的房间
        for exit_dir in exits:
            # 检查这个方向通向的房间是否已知
            if self.current_room in self.room_graph:
                next_room = self.room_graph[self.current_room].exits.get(exit_dir)
                if next_room and next_room not in self.room_graph:
                    # 未探索的房间
                    for action in available_actions:
                        if f"go {exit_dir}" in action.lower():
                            return action
        
        # 其次去访问次数少的房间
        min_visits = float('inf')
        best_exit = None
        
        for exit_dir in exits:
            if self.current_room in self.room_graph:
                next_room = self.room_graph[self.current_room].exits.get(exit_dir)
                if next_room and next_room in self.room_graph:
                    visits = self.room_graph[next_room].visit_count
                    if visits < min_visits:
                        min_visits = visits
                        best_exit = exit_dir
        
        if best_exit:
            for action in available_actions:
                if f"go {best_exit}" in action.lower():
                    return action
        
        return None
    
    def _plan_object_interaction(self, parsed_obs: Dict, available_actions: List[str]) -> Optional[str]:
        """规划与物品的交互"""
        visible_objects = parsed_obs.get('objects', [])
        
        # 优先拿取重要物品
        important_keywords = ['key', 'coin', 'treasure', 'gem', 'food', 'map']
        
        for obj in visible_objects:
            obj_lower = obj.lower()
            if any(kw in obj_lower for kw in important_keywords):
                for action in available_actions:
                    if 'take' in action.lower() and obj_lower in action.lower():
                        return action
        
        # 检查容器
        for obj in visible_objects:
            if obj in self.objects and self.objects[obj].is_container:
                for action in available_actions:
                    if 'open' in action.lower() and obj.lower() in action.lower():
                        return action
                    if 'examine' in action.lower() and obj.lower() in action.lower():
                        return action
        
        return None
    
    def _find_path(self, start: str, goal: str) -> List[str]:
        """BFS 路径搜索"""
        if start == goal:
            return []
        
        if start not in self.room_graph or goal not in self.room_graph:
            return []
        
        visited = {start}
        queue = deque([(start, [])])
        
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
        
        return []
    
    def learn_from_outcome(self, action: str, obs: str, reward: float, won: bool = False):
        """从结果中学习"""
        self.action_history.append((action, obs, reward))
        self.unique_interactions.add(action)
        
        # 记录成功模式
        if reward > 0 or won:
            pattern = {
                'action': action,
                'room': self.current_room,
                'room_type': self.room_graph.get(self.current_room, RoomNode("")).room_type,
                'inventory': list(self.inventory),
                'reward': reward
            }
            self.successful_patterns.append(pattern)
        
        # 记录失败
        if reward < 0:
            self.failed_actions[action] += 1
            if self.failed_actions[action] > 2:
                self.failed_patterns.add(action)
        
        # 更新探索分数
        self.exploration_score = len(self.room_graph) * 0.1 + len(self.unique_interactions) * 0.05
    
    def update_room_connection(self, from_room: str, direction: str, to_room: str):
        """更新房间连接关系"""
        if from_room in self.room_graph:
            self.room_graph[from_room].exits[direction] = to_room
    
    def is_action_promising(self, action: str) -> bool:
        """判断动作是否有希望成功"""
        # 检查是否在失败模式中
        if action in self.failed_patterns:
            return False
        
        # 检查失败次数
        if self.failed_actions.get(action, 0) > 3:
            return False
        
        return True
    
    def get_state_vector(self) -> np.ndarray:
        """获取状态向量表示"""
        vector = np.zeros(20, dtype=np.float32)
        
        # 0: 房间探索进度
        vector[0] = len(self.room_graph) / 20.0
        
        # 1: 库存占用
        vector[1] = len(self.inventory) / 5.0
        
        # 2: 步数效率
        vector[2] = max(0, 1.0 - self.step_count / 100.0)
        
        # 3: 物品发现数量
        vector[3] = len(self.objects) / 20.0
        
        # 4: 是否有钥匙
        vector[4] = 1.0 if any('key' in item.lower() for item in self.inventory) else 0.0
        
        # 5: 任务进度（如果有分数信息）
        # 6-10: 房间类型 one-hot
        room_type_idx = {
            'kitchen': 6, 'bedroom': 7, 'living': 8, 
            'office': 9, 'dungeon': 10
        }.get(self.room_graph.get(self.current_room, RoomNode("")).room_type, 0)
        if room_type_idx > 0:
            vector[room_type_idx] = 1.0
        
        # 11: 当前房间访问次数
        if self.current_room in self.room_graph:
            vector[11] = min(1.0, self.room_graph[self.current_room].visit_count / 5.0)
        
        # 12: 失败动作比例
        total_actions = len(self.action_history)
        if total_actions > 0:
            failed_count = sum(1 for a, _, r in self.action_history if r < 0)
            vector[12] = failed_count / total_actions
        
        # 13: 探索分数
        vector[13] = min(1.0, self.exploration_score)
        
        # 14: 任务类型编码
        task_type_idx = {
            'find': 0.1, 'take': 0.2, 'go': 0.3, 
            'open': 0.4, 'eat': 0.5, 'cook': 0.6
        }.get(self.task.task_type, 0.0)
        vector[14] = task_type_idx
        
        # 15: 是否有目标任务
        vector[15] = 1.0 if self.task.target_object else 0.0
        
        # 16: 是否知道目标位置
        if self.task.target_object:
            for obj_name, obj_info in self.objects.items():
                if self.task.target_object.lower() in obj_name.lower():
                    vector[16] = 1.0
                    break
        
        # 17: 当前房间物品数量
        if self.current_room in self.room_graph:
            vector[17] = len(self.room_graph[self.current_room].objects) / 10.0
        
        # 18: 出口数量
        if self.current_room in self.room_graph:
            vector[18] = len(self.room_graph[self.current_room].exits) / 4.0
        
        # 19: 成功模式数量
        vector[19] = min(1.0, len(self.successful_patterns) / 10.0)
        
        return vector
    
    def reset(self):
        """重置理解器状态"""
        self.room_graph.clear()
        self.objects.clear()
        self.inventory.clear()
        self.dropped_items.clear()
        self.current_room = ""
        self.previous_room = ""
        self.task = TaskInfo()
        self.sub_goals.clear()
        self.completed_goals.clear()
        self.action_history.clear()
        self.successful_patterns.clear()
        self.failed_actions.clear()
        self.failed_patterns.clear()
        self.step_count = 0
        self.unique_interactions.clear()
        self.exploration_score = 0.0
        self.room_types_discovered.clear()
        self.object_categories.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取理解器状态摘要"""
        return {
            'rooms_discovered': len(self.room_graph),
            'rooms_visited': sum(1 for r in self.room_graph.values() if r.visited),
            'objects_found': len(self.objects),
            'inventory_size': len(self.inventory),
            'current_room': self.current_room,
            'task_type': self.task.task_type,
            'task_target': self.task.target_object,
            'step_count': self.step_count,
            'exploration_score': self.exploration_score,
            'successful_patterns': len(self.successful_patterns),
            'failed_patterns': len(self.failed_patterns),
        }
