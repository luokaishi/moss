"""
MVES v4 - 开放环境智能体
核心：驱动系统 + 工具使用 + 环境改造
"""

import json
import os
import random
import shutil
from datetime import datetime

class Agent:
    def __init__(self, agent_id, base_dir="agents"):
        self.agent_id = agent_id
        self.base_dir = base_dir
        self.agent_dir = os.path.join(base_dir, f"agent_{agent_id}")
        
        # 文件路径
        self.brain_path = os.path.join(self.agent_dir, "brain.py")
        self.genome_path = os.path.join(self.agent_dir, "genome.json")
        self.state_path = os.path.join(self.agent_dir, "state.json")
        self.memory_path = os.path.join(self.agent_dir, "memory.json")
        self.tools_dir = os.path.join(self.agent_dir, "tools")
        
        # 创建目录
        os.makedirs(self.agent_dir, exist_ok=True)
        os.makedirs(self.tools_dir, exist_ok=True)
        
        # 位置（用于环境交互）
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)
        
        # 初始化或加载
        self._init_or_load()
    
    def _init_or_load(self):
        """初始化或加载"""
        if os.path.exists(self.genome_path):
            self.load()
        else:
            self._create_new()
    
    def _create_new(self):
        """创建新 agent"""
        # 初始基因组（包含驱动权重）
        self.genome = {
            "version": "4.0",
            "created": datetime.now().isoformat(),
            "parent_id": None,
            "drive_weights": {
                "survival": 0.5,
                "curiosity": 0.3,
                "control": 0.2
            },
            "mutation_count": 0,
            "tools_created": 0
        }
        
        # 初始状态
        self.state = {
            "energy": 100,
            "steps": 0,
            "generation": 0,
            "offspring_count": 0,
            "structures_built": 0,
            "tools_used": 0,
            "x": self.x,
            "y": self.y
        }
        
        # 分层记忆
        self.memory = {
            "episodic": [],      # 经历
            "semantic": {},       # 知识
            "procedural": {}      # 策略
        }
        
        # 工具清单
        self.tools = ["gather"]  # 初始有一个采集工具
        
        self.save()
    
    def load(self):
        """加载数据"""
        with open(self.genome_path, "r", encoding="utf-8") as f:
            self.genome = json.load(f)
        
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        
        with open(self.memory_path, "r", encoding="utf-8") as f:
            self.memory = json.load(f)
        
        # 加载工具清单
        tools_file = os.path.join(self.agent_dir, "tools.json")
        if os.path.exists(tools_file):
            with open(tools_file, "r") as f:
                self.tools = json.load(f)
        else:
            self.tools = ["gather"]
    
    def save(self):
        """保存数据"""
        with open(self.genome_path, "w", encoding="utf-8") as f:
            json.dump(self.genome, f, indent=2, ensure_ascii=False)
        
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
        
        # 保存工具清单
        tools_file = os.path.join(self.agent_dir, "tools.json")
        with open(tools_file, "w") as f:
            json.dump(self.tools, f)
    
    def decide(self, environment, tool_registry):
        """
        决策：基于驱动系统
        返回：行动决策
        """
        from drives import Drives
        
        # 计算驱动得分
        drive_scores = Drives.calculate_scores(self)
        dominant = drive_scores["dominant"]
        
        # 基于主导驱动选择行动
        if dominant == "survival":
            if self.state["energy"] < 20:
                action = "idle"
            elif self.state["energy"] < 50:
                action = "gather"
            else:
                action = "read"
        
        elif dominant == "curiosity":
            # 探索新位置
            if random.random() < 0.5:
                self._move(environment)
            action = random.choice(["scan", "read", "write"])
        
        elif dominant == "control":
            # 建造或创造
            if self.state["energy"] > 50:
                action = "build"
            else:
                action = "gather"
        
        else:
            action = "idle"
        
        return action, drive_scores
    
    def _move(self, environment, distance=1):
        """移动到附近位置"""
        dx = random.randint(-distance, distance)
        dy = random.randint(-distance, distance)
        
        new_x = max(0, min(environment.width - 1, self.x + dx))
        new_y = max(0, min(environment.height - 1, self.y + dy))
        
        self.x = new_x
        self.y = new_y
        self.state["x"] = new_x
        self.state["y"] = new_y
    
    def act(self, environment, tool_registry):
        """
        执行行动（可使用工具）
        """
        from drives import Drives
        
        # 决策
        action, drive_scores = self.decide(environment, tool_registry)
        
        # 执行行动
        result = {"action": action, "drive_scores": drive_scores}
        
        if action == "gather":
            tool_result = tool_registry.use_tool("gather", self, environment)
            if tool_result["success"]:
                self.state["energy"] += tool_result["energy_gain"]
                self.state["tools_used"] += 1
            result["tool_result"] = tool_result
        
        elif action == "build":
            structure = environment.create_structure(self, self.x, self.y, "outpost")
            result["structure"] = structure
        
        elif action == "scan":
            tool_result = tool_registry.use_tool("scan", self, environment)
            result["tool_result"] = tool_result
        
        elif action == "idle":
            result["energy_change"] = -0.5
        
        elif action == "read":
            result["energy_change"] = -1.0
        
        elif action == "write":
            result["energy_change"] = -2.0
        
        # 应用能量变化
        if "energy_change" in result:
            self.state["energy"] += result["energy_change"]
        
        # 更新记忆（分层）
        self._update_memory(action, result)
        
        # 更新步数
        self.state["steps"] += 1
        self.state["generation"] += 1
        
        return result
    
    def _update_memory(self, action, result):
        """更新分层记忆"""
        # 情景记忆（最近 20 条）
        episodic = {
            "step": self.state["steps"],
            "action": action,
            "result": result,
            "position": (self.x, self.y)
        }
        self.memory["episodic"].append(episodic)
        if len(self.memory["episodic"]) > 20:
            self.memory["episodic"] = self.memory["episodic"][-20:]
        
        # 语义记忆（知识积累）
        if result.get("tool_result", {}).get("success"):
            key = f"tool_{action}_success"
            self.memory["semantic"][key] = self.memory["semantic"].get(key, 0) + 1
        
        # 程序记忆（策略）
        if self.state["energy"] > 80:
            self.memory["procedural"]["high_energy_strategy"] = action
        elif self.state["energy"] < 30:
            self.memory["procedural"]["low_energy_strategy"] = action
    
    def get_influence(self):
        """计算影响力"""
        tools = len(self.tools)
        structures = self.state.get("structures_built", 0)
        return tools * 2 + structures
    
    def is_dead(self):
        """死亡判断"""
        return self.state["energy"] <= 0
    
    def should_reproduce(self):
        """繁殖判断"""
        return self.state["energy"] > 120 and self.state["steps"] > 20
    
    def get_fitness(self):
        """适应度（用于选择）"""
        survival = max(0, self.state["energy"] / 10)
        influence = self.get_influence() * 5
        offspring = self.state.get("offspring_count", 0) * 10
        return survival + influence + offspring
    
    def reproduce(self):
        """繁殖子代"""
        new_id = max([int(d.replace("agent_", "")) for d in os.listdir(self.base_dir) if d.startswith("agent_")] + [-1]) + 1
        child = Agent(new_id, self.base_dir)
        
        # 继承基因组（带变异）
        child.genome = self.genome.copy()
        child.genome["parent_id"] = self.agent_id
        child.genome["created"] = datetime.now().isoformat()
        child.genome["mutation_count"] = self.genome["mutation_count"] + 1
        
        # 继承工具
        child.tools = self.tools.copy()
        
        # 继承部分记忆
        child.memory["semantic"] = self.memory.get("semantic", {}).copy()
        child.memory["procedural"] = self.memory.get("procedural", {}).copy()
        
        # 重置状态
        child.state = {
            "energy": 80,
            "steps": 0,
            "generation": 0,
            "offspring_count": 0,
            "structures_built": 0,
            "tools_used": 0,
            "x": child.x,
            "y": child.y,
            "parent_energy": self.state["energy"]
        }
        
        # 位置变异
        child.x = max(0, min(19, self.x + random.randint(-2, 2)))
        child.y = max(0, min(19, self.y + random.randint(-2, 2)))
        child.state["x"] = child.x
        child.state["y"] = child.y
        
        child.save()
        
        # 更新父代
        self.state["offspring_count"] += 1
        self.save()
        
        return child
    
    def get_info(self):
        """获取信息"""
        return {
            "id": self.agent_id,
            "energy": self.state["energy"],
            "steps": self.state["steps"],
            "generation": self.state["generation"],
            "influence": self.get_influence(),
            "offspring": self.state.get("offspring_count", 0),
            "tools": len(self.tools),
            "structures": self.state.get("structures_built", 0),
            "fitness": self.get_fitness()
        }
