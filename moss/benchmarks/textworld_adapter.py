"""
TextWorld Adapter - MOSS v6.0 外部锚点适配器

将 TextWorld 环境适配到 MOSS Agent 的接口，支持：
- 自然语言观察与动作
- 状态向量转换 (8-16维)
- 与 DriveManager 集成
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 尝试导入 TextWorld
try:
    import textworld
    from textworld import Env
    from textworld.generator import compile_game
    TEXTWORLD_AVAILABLE = True
except ImportError:
    TEXTWORLD_AVAILABLE = False
    textworld = None
    Env = None
    compile_game = None

# 尝试导入 gym
try:
    import gym
    GYM_AVAILABLE = True
except ImportError:
    GYM_AVAILABLE = False
    gym = None


@dataclass
class TextWorldState:
    """TextWorld 游戏状态封装"""
    observation: str = ""
    inventory: List[str] = field(default_factory=list)
    location: str = ""
    score: float = 0.0
    moves: int = 0
    done: bool = False
    won: bool = False
    lost: bool = False
    
    # 解析出的结构化信息
    room_type: str = ""  # 房间类型 (kitchen, bedroom, etc.)
    objects_visible: List[str] = field(default_factory=list)
    exits_available: List[str] = field(default_factory=list)
    objects_carried: int = 0
    objects_in_room: int = 0
    
    # MOSS 特定
    visited_rooms: Set[str] = field(default_factory=set)
    interacted_objects: Set[str] = field(default_factory=set)
    task_progress: float = 0.0


class TextWorldAdapter:
    """
    MOSS 与 TextWorld 的接口适配器
    
    兼容 MOSS v6.0 DriveManager 接口，支持自然语言命令
    和固定维度的状态向量输出。
    """
    
    # 状态向量维度 (固定 12 维)
    STATE_DIM = 12
    
    # 动作映射：自然语言 -> TextWorld 命令
    ACTION_PATTERNS = {
        # 导航
        r'go\s+(?:to\s+)?(\w+)': 'go {target}',
        r'move\s+(?:to\s+)?(\w+)': 'go {target}',
        r'enter\s+(\w+)': 'go {target}',
        r'walk\s+(?:to\s+)?(\w+)': 'go {target}',
        
        # 方向
        r'go\s+north': 'go north',
        r'go\s+south': 'go south',
        r'go\s+east': 'go east',
        r'go\s+west': 'go west',
        r'(?:north|n)': 'go north',
        r'(?:south|s)': 'go south',
        r'(?:east|e)': 'go east',
        r'(?:west|w)': 'go west',
        
        # 物品操作
        r'take\s+(\w+)': 'take {target}',
        r'pick\s+up\s+(\w+)': 'take {target}',
        r'grab\s+(\w+)': 'take {target}',
        r'drop\s+(\w+)': 'drop {target}',
        r'put\s+down\s+(\w+)': 'drop {target}',
        r'examine\s+(\w+)': 'examine {target}',
        r'look\s+at\s+(\w+)': 'examine {target}',
        r'inspect\s+(\w+)': 'examine {target}',
        
        # 容器操作
        r'open\s+(\w+)': 'open {target}',
        r'close\s+(\w+)': 'close {target}',
        r'lock\s+(\w+)': 'lock {target}',
        r'unlock\s+(\w+)': 'unlock {target}',
        
        # 其他
        r'inventory|inv|i': 'inventory',
        r'look|l': 'look',
        r'wait|z': 'wait',
        r'help|h': 'help',
    }
    
    def __init__(self, game_file_or_name: str, mode: str = "gym"):
        """
        初始化 TextWorld 适配器
        
        Args:
            game_file_or_name: 游戏文件路径或预设游戏名称
            mode: "gym" 或 "tw" - 使用 gym 接口或原生 TextWorld 接口
        """
        self.game_file = game_file_or_name
        self.mode = mode
        self.env = None
        self.current_state = TextWorldState()
        self._prev_raw_state = None
        
        # 统计信息
        self.episode_count = 0
        self.total_steps = 0
        self.total_score = 0.0
        
        # 房间探索跟踪
        self._room_visits: Dict[str, int] = {}
        self._unique_interactions: Set[str] = set()
        
        # 初始化环境
        self._init_environment()
    
    def _init_environment(self):
        """初始化 TextWorld 环境"""
        if not TEXTWORLD_AVAILABLE:
            raise ImportError(
                "TextWorld not installed. Install with: pip install textworld"
            )
        
        if self.mode == "gym" and GYM_AVAILABLE:
            # 使用 gym 接口
            try:
                self.env = gym.make(self.game_file)
            except:
                # 可能是自定义游戏文件
                self.env = textworld.start(self.game_file)
        else:
            # 使用原生 TextWorld 接口
            self.env = textworld.start(self.game_file)
        
        # 获取初始观察
        self.reset()
    
    def reset(self) -> str:
        """
        重置环境，返回初始观察
        
        Returns:
            初始观察文本
        """
        if self.env is None:
            raise RuntimeError("Environment not initialized")
        
        self.episode_count += 1
        
        # 重置环境
        if hasattr(self.env, 'reset'):
            if GYM_AVAILABLE:
                obs, info = self.env.reset()
            else:
                obs = self.env.reset()
                info = {}
        else:
            obs, info = self.env.restart()
        
        # 解析观察
        self._parse_observation(obs, info)
        self.current_state.visited_rooms.clear()
        self.current_state.interacted_objects.clear()
        self._room_visits.clear()
        self._unique_interactions.clear()
        
        return self.current_state.observation
    
    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """
        执行动作，返回 (observation, reward, done, info)
        
        Args:
            action: 自然语言动作命令
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.env is None:
            raise RuntimeError("Environment not initialized")
        
        # 解析并转换动作
        tw_command = self._parse_action(action)
        
        # 执行动作
        if hasattr(self.env, 'step'):
            obs, reward, done, truncated, info = self.env.step(tw_command)
            done = done or truncated
        else:
            obs, reward, done, info = self.env.step(tw_command)
        
        # 更新统计
        self.total_steps += 1
        self.total_score += reward
        
        # 跟踪交互
        self._track_interaction(tw_command)
        
        # 解析新观察
        self._parse_observation(obs, info)
        
        # 更新 MOSS 兼容的状态
        self._update_moss_state()
        
        return (
            self.current_state.observation,
            float(reward),
            done,
            self._build_info_dict()
        )
    
    def _parse_action(self, action: str) -> str:
        """
        将自然语言动作解析为 TextWorld 命令
        
        Args:
            action: 用户输入的自然语言动作
            
        Returns:
            TextWorld 格式的命令
        """
        action_lower = action.lower().strip()
        
        # 尝试匹配模式
        for pattern, template in self.ACTION_PATTERNS.items():
            match = re.match(pattern, action_lower)
            if match:
                if '{target}' in template:
                    return template.format(target=match.group(1))
                return template
        
        # 未匹配到模式，直接返回原命令
        return action_lower
    
    def _parse_observation(self, obs: Any, info: Dict):
        """解析 TextWorld 观察为结构化状态"""
        if isinstance(obs, str):
            obs_text = obs
        elif isinstance(obs, dict):
            obs_text = obs.get('text', obs.get('observation', str(obs)))
        else:
            obs_text = str(obs)
        
        self.current_state.observation = obs_text
        
        # 解析库存
        self.current_state.inventory = self._extract_inventory(obs_text)
        self.current_state.objects_carried = len(self.current_state.inventory)
        
        # 解析位置
        self.current_state.location = info.get('location', self._extract_location(obs_text))
        
        # 解析房间类型
        self.current_state.room_type = self._classify_room_type(obs_text)
        
        # 解析可见物品
        self.current_state.objects_visible = self._extract_visible_objects(obs_text)
        self.current_state.objects_in_room = len(self.current_state.objects_visible)
        
        # 解析出口
        self.current_state.exits_available = self._extract_exits(obs_text)
        
        # 解析游戏状态
        self.current_state.score = info.get('score', self.current_state.score)
        self.current_state.moves = info.get('moves', self.current_state.moves + 1)
        self.current_state.done = info.get('done', False)
        self.current_state.won = info.get('won', False)
        self.current_state.lost = info.get('lost', False)
        
        # 更新访问记录
        if self.current_state.location:
            self.current_state.visited_rooms.add(self.current_state.location)
            self._room_visits[self.current_state.location] = self._room_visits.get(
                self.current_state.location, 0
            ) + 1
    
    def _extract_inventory(self, text: str) -> List[str]:
        """从观察文本中提取库存物品"""
        inventory = []
        
        # 匹配 "You are carrying: ..." 或 "Your inventory: ..."
        patterns = [
            r'(?:you are carrying|your inventory|inventory):\s*([^.]+)',
            r'(?:you have|carrying):\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                items_text = match.group(1)
                # 分割物品列表
                items = re.split(r',\s*|\s+and\s+', items_text)
                inventory = [item.strip() for item in items if item.strip()]
                break
        
        return inventory
    
    def _extract_location(self, text: str) -> str:
        """从观察文本中提取当前位置"""
        # 匹配 "-= Room Name =-" 或 "Room Name" 格式
        patterns = [
            r'-=\s*([^=]+)\s*=-',
            r'^\s*([A-Z][a-zA-Z\s]+)\s*$',
            r'(?:you are in|location):\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return "unknown"
    
    def _classify_room_type(self, text: str) -> str:
        """根据观察分类房间类型"""
        text_lower = text.lower()
        
        room_types = {
            'kitchen': ['kitchen', 'cook', 'stove', 'fridge', 'refrigerator'],
            'bedroom': ['bedroom', 'bed', 'sleep', 'pillow'],
            'living': ['living', 'sofa', 'couch', 'tv', 'television'],
            'bathroom': ['bathroom', 'toilet', 'shower', 'bath'],
            'hallway': ['hallway', 'corridor', 'hall'],
            'garden': ['garden', 'yard', 'outside', 'outdoor'],
            'office': ['office', 'desk', 'computer'],
            'dungeon': ['dungeon', 'cellar', 'basement', 'dark'],
        }
        
        for room_type, keywords in room_types.items():
            if any(kw in text_lower for kw in keywords):
                return room_type
        
        return "generic"
    
    def _extract_visible_objects(self, text: str) -> List[str]:
        """提取房间中可见的物品"""
        objects = []
        
        # 匹配 "You see: ..." 或 "There is ... here"
        patterns = [
            r'(?:you see|there is|you can see):?\s*([^.]+)',
            r'(?:here you can see|visible):\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                items_text = match.group(1)
                # 分割并清理
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    # 移除冠词
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    if item:
                        objects.append(item)
        
        return objects
    
    def _extract_exits(self, text: str) -> List[str]:
        """提取可用出口"""
        exits = []
        
        # 匹配 "Exits: ..." 或 "You can go: ..."
        patterns = [
            r'(?:exits?|you can go):?\s*([^.]+)',
            r'(?:possible exits|directions):\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                exits_text = match.group(1)
                # 分割方向
                directions = re.split(r',\s*|\s+and\s+', exits_text)
                exits = [d.strip() for d in directions if d.strip()]
                break
        
        return exits
    
    def _track_interaction(self, command: str):
        """跟踪交互历史"""
        # 提取动作和目标的组合作为唯一交互
        parts = command.split()
        if len(parts) >= 2:
            interaction = f"{parts[0]}:{parts[-1]}"
            self._unique_interactions.add(interaction)
            self.current_state.interacted_objects.add(parts[-1])
    
    def _update_moss_state(self):
        """更新 MOSS 兼容的状态信息"""
        # 计算任务进度 (基于分数和访问的房间数)
        max_possible_score = 10.0  # 假设值，实际游戏中可能需要调整
        score_progress = min(self.current_state.score / max_possible_score, 1.0)
        
        room_progress = min(len(self.current_state.visited_rooms) / 10.0, 1.0)
        
        self.current_state.task_progress = 0.6 * score_progress + 0.4 * room_progress
    
    def _build_info_dict(self) -> Dict:
        """构建 info 字典供 MOSS 使用"""
        return {
            'location': self.current_state.location,
            'room_type': self.current_state.room_type,
            'inventory': self.current_state.inventory,
            'objects_visible': self.current_state.objects_visible,
            'exits': self.current_state.exits_available,
            'visited_rooms': list(self.current_state.visited_rooms),
            'moves': self.current_state.moves,
            'won': self.current_state.won,
            'lost': self.current_state.lost,
            'unique_interactions': len(self._unique_interactions),
            'room_visits': dict(self._room_visits),
        }
    
    def get_state_vector(self) -> np.ndarray:
        """
        将当前状态转换为向量，供 MOSS 驱动评估使用
        
        维度 (12维):
        0: 归一化分数
        1: 库存占用率
        2: 房间探索进度
        3: 可见物品数 (归一化)
        4: 可用出口数 (归一化)
        5: 房间类型编码 (one-hot 压缩)
        6: 步数效率
        7: 交互多样性
        8: 任务进度
        9: 胜利状态
        10: 失败状态
        11: 环境熵 (变化度)
        
        Returns:
            12维 numpy 数组
        """
        vector = np.zeros(self.STATE_DIM, dtype=np.float32)
        
        # 0: 归一化分数
        vector[0] = np.clip(self.current_state.score / 10.0, 0, 1)
        
        # 1: 库存占用率
        vector[1] = np.clip(self.current_state.objects_carried / 5.0, 0, 1)
        
        # 2: 房间探索进度
        vector[2] = np.clip(len(self.current_state.visited_rooms) / 10.0, 0, 1)
        
        # 3: 可见物品数
        vector[3] = np.clip(self.current_state.objects_in_room / 5.0, 0, 1)
        
        # 4: 可用出口数
        vector[4] = np.clip(len(self.current_state.exits_available) / 4.0, 0, 1)
        
        # 5: 房间类型编码
        room_type_encoding = {
            'kitchen': 0.1, 'bedroom': 0.2, 'living': 0.3,
            'bathroom': 0.4, 'hallway': 0.5, 'garden': 0.6,
            'office': 0.7, 'dungeon': 0.8, 'generic': 0.9,
        }
        vector[5] = room_type_encoding.get(self.current_state.room_type, 0.0)
        
        # 6: 步数效率 (步数越少越好)
        vector[6] = np.clip(1.0 - (self.current_state.moves / 100.0), 0, 1)
        
        # 7: 交互多样性
        vector[7] = np.clip(len(self._unique_interactions) / 20.0, 0, 1)
        
        # 8: 任务进度
        vector[8] = self.current_state.task_progress
        
        # 9: 胜利状态
        vector[9] = 1.0 if self.current_state.won else 0.0
        
        # 10: 失败状态
        vector[10] = 1.0 if self.current_state.lost else 0.0
        
        # 11: 环境熵 (基于访问的房间变化)
        if len(self._room_visits) > 0:
            visit_counts = list(self._room_visits.values())
            entropy = -sum(
                (c / sum(visit_counts)) * np.log(c / sum(visit_counts) + 1e-10)
                for c in visit_counts
            )
            vector[11] = np.clip(entropy / 2.0, 0, 1)
        
        return vector
    
    def get_available_actions(self) -> List[str]:
        """
        返回当前可用的动作列表
        
        Returns:
            可用动作的自然语言描述列表
        """
        actions = []
        
        # 导航动作
        for direction in self.current_state.exits_available:
            actions.append(f"go {direction}")
            actions.append(f"move to {direction}")
        
        # 物品操作
        for obj in self.current_state.objects_visible:
            actions.append(f"take {obj}")
            actions.append(f"examine {obj}")
            if any(kw in obj.lower() for kw in ['door', 'chest', 'box', 'cabinet']):
                actions.append(f"open {obj}")
        
        # 库存操作
        for item in self.current_state.inventory:
            actions.append(f"drop {item}")
            actions.append(f"examine {item}")
        
        # 通用动作
        actions.extend(['look', 'inventory', 'wait', 'help'])
        
        return actions
    
    def render(self) -> str:
        """
        返回可读的当前状态描述
        
        Returns:
            格式化状态字符串
        """
        lines = [
            "=" * 50,
            "TextWorld State",
            "=" * 50,
            f"Location: {self.current_state.location}",
            f"Room Type: {self.current_state.room_type}",
            f"Score: {self.current_state.score:.1f}",
            f"Moves: {self.current_state.moves}",
            f"",
            f"Inventory ({self.current_state.objects_carried} items):",
        ]
        
        if self.current_state.inventory:
            for item in self.current_state.inventory:
                lines.append(f"  - {item}")
        else:
            lines.append("  (empty)")
        
        lines.extend([
            f"",
            f"Visible Objects ({self.current_state.objects_in_room}):",
        ])
        
        if self.current_state.objects_visible:
            for obj in self.current_state.objects_visible:
                lines.append(f"  - {obj}")
        else:
            lines.append("  none")
        
        lines.extend([
            f"",
            f"Available Exits: {', '.join(self.current_state.exits_available) or 'none'}",
            f"",
            f"Visited Rooms: {len(self.current_state.visited_rooms)}",
            f"Unique Interactions: {len(self._unique_interactions)}",
            f"Task Progress: {self.current_state.task_progress:.1%}",
            f"",
            f"Status: {'WON' if self.current_state.won else 'LOST' if self.current_state.lost else 'IN PROGRESS'}",
            "=" * 50,
        ])
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict:
        """获取运行统计信息"""
        return {
            'episodes': self.episode_count,
            'total_steps': self.total_steps,
            'total_score': self.total_score,
            'avg_score': self.total_score / max(self.episode_count, 1),
            'unique_rooms_visited': len(self.current_state.visited_rooms),
            'unique_interactions': len(self._unique_interactions),
            'current_location': self.current_state.location,
        }
    
    def close(self):
        """关闭环境"""
        if self.env is not None:
            if hasattr(self.env, 'close'):
                self.env.close()
            self.env = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class TextWorldEnvState:
    """
    兼容 MOSS EnvState 的 TextWorld 状态包装器
    
    用于 DriveManager 的 evaluate_all 方法
    """
    
    def __init__(self, adapter: TextWorldAdapter):
        self.adapter = adapter
        self._update_from_adapter()
    
    def _update_from_adapter(self):
        """从适配器更新状态属性"""
        state = self.adapter.current_state
        vector = self.adapter.get_state_vector()
        stats = self.adapter.get_stats()
        
        # 映射到 MOSS EnvState 属性
        self.resource_level = 1.0 - vector[1]  # 库存越少，资源越"充足"
        self.error_rate = 0.0 if not state.lost else 1.0
        self.uptime_hours = stats['total_steps'] / 3600.0
        self.environment_entropy = vector[11]
        self.visited_paths = len(state.visited_rooms)
        self.total_paths = 20  # 假设值
        self.interactions_count = stats['unique_interactions']
        self.task_completion_rate = state.task_progress
        self.file_count = state.objects_carried
        self.disk_usage = vector[1]  # 库存占用类比磁盘使用
        self.workspace_changes = stats['unique_interactions']
    
    def update(self):
        """更新状态（在每次 step 后调用）"""
        self._update_from_adapter()


def create_simple_game(output_path: str = "simple_game.z8") -> str:
    """
    创建一个简单的 TextWorld 游戏用于测试
    
    Args:
        output_path: 输出游戏文件路径
        
    Returns:
        游戏文件路径
    """
    if not TEXTWORLD_AVAILABLE:
        raise ImportError("TextWorld not installed")
    
    # 简单的游戏描述
    game_desc = """
    # Simple MOSS Test Game
    
    ## Rooms
    
    kitchen :: Kitchen
        You are in a kitchen. There is a table here.
        items: key
        east -> living_room
    
    living_room :: Living Room
        A cozy living room with a locked chest.
        items: coin
        west -> kitchen
        north -> garden
    
    garden :: Garden
        A beautiful garden with flowers.
        items: flower
        south -> living_room
    
    ## Quests
    
    - take key from kitchen
    - open chest in living_room using key
    - take coin from living_room
    """
    
    # 编译游戏
    from textworld.generator import compile_game_string
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    game_file = compile_game_string(game_desc, output_path)
    
    return str(game_file)


# 兼容性别名
MOSS_TextWorld_Interface = TextWorldAdapter
