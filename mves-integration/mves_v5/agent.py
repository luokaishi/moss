#!/usr/bin/env python3
"""
MVES v5 - 最小可验证演化系统
核心：演化智能体（支持结构变异）
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Set


class EvolutionaryAgent:
    """
    演化智能体 v5
    
    核心特性:
    1. 结构变异（添加模块/改写策略/生成子代）
    2. 数学化驱动函数
    3. 遗传机制
    """
    
    def __init__(self, agent_id: int, base_dir: str = "agents"):
        self.agent_id = agent_id
        self.base_dir = base_dir
        self.agent_dir = os.path.join(base_dir, f"agent_{agent_id}")
        
        # 文件路径
        self.genome_path = os.path.join(self.agent_dir, "genome.json")
        self.state_path = os.path.join(self.agent_dir, "state.json")
        self.memory_path = os.path.join(self.agent_dir, "memory.json")
        
        # 创建目录
        os.makedirs(self.agent_dir, exist_ok=True)
        
        # 位置
        self.x = random.randint(0, 29)
        self.y = random.randint(0, 29)
        
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
        # 初始基因组
        self.genome = {
            "version": "5.0",
            "created": datetime.now().isoformat(),
            "parent_id": None,
            "generation": 0,
            "modules": ["basic_perceptor", "basic_actuator"],  # 基础模块
            "strategies": {
                "exploration": "random_walk",
                "resource_management": "conservative"
            },
            "drive_weights": {
                "survival": 0.4,
                "curiosity": 0.2,
                "influence": 0.25,
                "optimization": 0.15
            },
            "mutation_count": 0,
            "capabilities": ["move", "sense", "act"]
        }
        
        # 初始状态
        self.state = {
            "energy": 100,
            "steps": 0,
            "performance_history": [],
            "x": self.x,
            "y": self.y
        }
        
        # 分层记忆
        self.memory = {
            "episodic": [],      # 经历
            "semantic": {},       # 知识
            "procedural": {}      # 策略
        }
        
        self.save()
    
    def load(self):
        """加载数据"""
        with open(self.genome_path, "r", encoding="utf-8") as f:
            self.genome = json.load(f)
        
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                self.state = json.load(f)
        else:
            # state 文件不存在，重新初始化
            self._create_new()
            return
        
        with open(self.memory_path, "r", encoding="utf-8") as f:
            self.memory = json.load(f)
    
    def save(self):
        """保存数据"""
        with open(self.genome_path, "w", encoding="utf-8") as f:
            json.dump(self.genome, f, indent=2)
        
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
        
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)
    
    # =========================================================================
    # 变异机制（核心改进 1）
    # =========================================================================
    
    def mutate_structure(self) -> str:
        """
        结构变异（v5 核心）
        
        返回：变异描述
        """
        mutations = [
            self._add_new_module,
            self._rewrite_strategy,
            self._modify_goal_function,
            self._expand_capabilities
        ]
        
        mutation_func = random.choice(mutations)
        result = mutation_func()
        
        self.genome["mutation_count"] += 1
        self.save()
        
        return result
    
    def _add_new_module(self) -> str:
        """添加新模块"""
        module_templates = {
            "memory_optimizer": "优化记忆存储和检索",
            "pattern_recognizer": "识别环境模式",
            "tool_creator": "创造新工具",
            "self_reflector": "自我反思和元认知",
            "resource_predictor": "预测资源变化",
            "social_learner": "从其他 agent 学习"
        }
        
        available = [m for m in module_templates if m not in self.genome["modules"]]
        if not available:
            return "No new modules available"
        
        new_module = random.choice(available)
        self.genome["modules"].append(new_module)
        
        return f"Added module: {new_module} ({module_templates[new_module]})"
    
    def _rewrite_strategy(self) -> str:
        """改写策略"""
        strategy_options = {
            "exploration": ["random_walk", "gradient_ascent", "simulated_annealing", "genetic_search"],
            "resource_management": ["conservative", "balanced", "aggressive", "opportunistic"]
        }
        
        strategy_type = random.choice(list(strategy_options.keys()))
        old_strategy = self.genome["strategies"][strategy_type]
        new_strategy = random.choice([s for s in strategy_options[strategy_type] if s != old_strategy])
        
        self.genome["strategies"][strategy_type] = new_strategy
        
        return f"Rewrote strategy: {strategy_type} {old_strategy} → {new_strategy}"
    
    def _modify_goal_function(self) -> str:
        """修改目标函数（驱动权重变异）"""
        # 随机调整权重
        drives = ["survival", "curiosity", "influence", "optimization"]
        target_drive = random.choice(drives)
        
        # 变异幅度：±0.1
        delta = random.uniform(-0.1, 0.1)
        old_weight = self.genome["drive_weights"][target_drive]
        new_weight = max(0.1, min(0.6, old_weight + delta))
        
        self.genome["drive_weights"][target_drive] = new_weight
        
        # 归一化
        total = sum(self.genome["drive_weights"].values())
        for drive in drives:
            self.genome["drive_weights"][drive] /= total
        
        return f"Modified goal: {target_drive} weight {old_weight:.3f} → {new_weight:.3f}"
    
    def _expand_capabilities(self) -> str:
        """扩展能力"""
        capability_tree = {
            "move": ["move_fast", "move_stealth", "jump"],
            "sense": ["sense_long_range", "sense_hidden", "predict"],
            "act": ["act_precise", "act_powerful", "act_efficient"],
            "learn": ["learn_fast", "learn_from_others", "learn_abstract"]
        }
        
        current = set(self.genome["capabilities"])
        available = []
        
        for base_cap, advanced in capability_tree.items():
            if base_cap in current:
                available.extend([c for c in advanced if c not in current])
        
        if not available:
            return "No new capabilities available"
        
        new_cap = random.choice(available)
        self.genome["capabilities"].append(new_cap)
        
        return f"Expanded capability: {new_cap}"
    
    # =========================================================================
    # 驱动系统（数学化定义，核心改进 2）
    # =========================================================================
    
    def calculate_drives(self, environment) -> Dict[str, float]:
        """
        计算四驱动分数（数学化）
        """
        return {
            "survival": self._calculate_survival(),
            "curiosity": self._calculate_curiosity(environment),
            "influence": self._calculate_influence(environment),
            "optimization": self._calculate_optimization()
        }
    
    def _calculate_survival(self) -> float:
        """
        生存驱动 = 资源缓冲 / 消耗率
        
        S = buffer / (consumption + ε)
        """
        buffer = self.state["energy"] - 20  # 20 为最低阈值
        consumption = self._get_avg_consumption()
        
        survival_score = buffer / (consumption + 1)  # +1 防止除零
        return max(0, min(1.0, survival_score / 100))  # 归一化到 [0,1]
    
    def _calculate_curiosity(self, environment) -> float:
        """
        好奇心 = 预测误差最小化
        
        C(s) = 1 / (1 + prediction_error(s))
        """
        # 获取当前位置的预测误差
        position = (self.x, self.y)
        prediction_error = environment.get_prediction_error(position)
        
        curiosity_score = 1.0 / (1.0 + prediction_error)
        return curiosity_score
    
    def _calculate_influence(self, environment) -> float:
        """
        影响力 = 外部状态变化数
        
        I = |{s ∈ Environment : caused_by(agent, s)}|
        """
        changes = environment.get_changes_caused_by(self.agent_id)
        influence_score = len(changes)
        
        return min(1.0, influence_score / 10)  # 归一化到 [0,1]
    
    def _calculate_optimization(self) -> float:
        """
        优化 = 性能提升率
        
        O = (performance_t - performance_{t-1}) / performance_{t-1}
        """
        current_perf = self._get_performance()
        
        if len(self.state["performance_history"]) == 0:
            return 0.0
        
        past_perf = self.state["performance_history"][-1]
        
        if past_perf == 0:
            return 0.0
        
        optimization_score = (current_perf - past_perf) / past_perf
        return max(0, optimization_score)  # 只计正向提升
    
    def _get_avg_consumption(self) -> float:
        """获取平均消耗率"""
        steps = self.state.get("steps", 0)
        if steps == 0:
            return 1.0
        
        initial_energy = 100
        current_energy = self.state.get("energy", 100)
        consumed = initial_energy - current_energy
        return abs(consumed) / max(1, steps)
    
    def _get_performance(self) -> float:
        """获取当前性能"""
        # 性能 = 任务完成率 × 效率
        task_completion = len(self.memory.get("episodic", [])) / max(1, self.state["steps"])
        efficiency = 1.0 / (1.0 + self._get_avg_consumption())
        
        return task_completion * efficiency
    
    # =========================================================================
    # 选择压力响应（核心改进 3）
    # =========================================================================
    
    def respond_to_selection_pressure(self, outcome: str):
        """
        响应选择压力
        """
        if outcome == "death":
            self.die()
        elif outcome == "resource_penalty":
            self._apply_resource_penalty()
        elif outcome == "selection_risk":
            self._adapt_to_risk()
    
    def die(self):
        """死亡（清除所有数据）"""
        # 保留基因组用于遗传
        genome_backup = self.genome.copy()
        
        # 清除状态和记忆
        self.state = {}
        self.memory = {}
        self.modules = []
        
        # 标记为死亡
        self.genome["status"] = "dead"
        self.genome["death_time"] = datetime.now().isoformat()
        
        self.save()
    
    def _apply_resource_penalty(self):
        """应用资源惩罚"""
        # 丢失 50% 记忆
        if "episodic" in self.memory:
            half = len(self.memory["episodic"]) // 2
            self.memory["episodic"] = self.memory["episodic"][half:]
        
        # 失去 30% 资源
        energy_loss = int(self.state["energy"] * 0.3)
        self.state["energy"] -= energy_loss
        
        self.save()
    
    def _adapt_to_risk(self):
        """适应风险（增加生存权重）"""
        self.genome["drive_weights"]["survival"] = min(
            0.6,
            self.genome["drive_weights"]["survival"] + 0.1
        )
        
        # 归一化
        total = sum(self.genome["drive_weights"].values())
        for drive in self.genome["drive_weights"]:
            self.genome["drive_weights"][drive] /= total
        
        self.save()
    
    # =========================================================================
    # 决策与行动
    # =========================================================================
    
    def decide(self, environment=None) -> str:
        """决策"""
        # 获取驱动分数
        drives = self.calculate_drives(environment=environment)
        
        # 根据驱动权重选择行动
        weights = self.genome["drive_weights"]
        
        action_scores = {
            "explore": drives["curiosity"] * weights["curiosity"],
            "conserve": drives["survival"] * weights["survival"],
            "influence": drives["influence"] * weights["influence"],
            "optimize": drives["optimization"] * weights["optimization"]
        }
        
        # 选择最高分行动
        best_action = max(action_scores, key=action_scores.get)
        
        return best_action
    
    def execute(self, action: str, environment) -> Dict:
        """执行行动"""
        result = {
            "action": action,
            "success": False,
            "energy_cost": 0
        }
        
        if action == "explore":
            result = self._execute_explore(environment)
        elif action == "conserve":
            result = self._execute_conserve()
        elif action == "influence":
            result = self._execute_influence(environment)
        elif action == "optimize":
            result = self._execute_optimize()
        
        # 更新状态
        self.state["energy"] -= result["energy_cost"]
        self.state["steps"] += 1
        
        # 记录性能
        self.state["performance_history"].append(self._get_performance())
        
        self.save()
        
        return result
    
    def _execute_explore(self, environment) -> Dict:
        """执行探索"""
        # 移动到新位置
        dx = random.randint(-3, 3)
        dy = random.randint(-3, 3)
        self.x = max(0, min(19, self.x + dx))
        self.y = max(0, min(19, self.y + dy))
        
        # 记录经历
        self.memory["episodic"].append({
            "type": "explore",
            "position": (self.x, self.y),
            "time": datetime.now().isoformat()
        })
        
        # 优化：降低能量消耗（5 → 2）
        return {
            "action": "explore",
            "success": True,
            "energy_cost": 2,
            "new_position": (self.x, self.y)
        }
    
    def _execute_conserve(self) -> Dict:
        """执行保守策略"""
        # 优化：增加能量恢复（10 → 15）
        energy_recovery = 15
        
        return {
            "action": "conserve",
            "success": True,
            "energy_cost": -energy_recovery,  # 负消耗=恢复
            "energy_recovered": energy_recovery
        }
    
    def _execute_influence(self, environment) -> Dict:
        """执行影响力行动"""
        # 改造环境
        environment.add_structure(self.x, self.y, self.agent_id)
        
        # 优化：降低能量消耗（15 → 8）
        return {
            "action": "influence",
            "success": True,
            "energy_cost": 8,
            "structure_built": True
        }
    
    def _execute_optimize(self) -> Dict:
        """执行优化行动"""
        # 优化：增加变异率（15% → 30%）
        if random.random() < 0.30:  # 30% 变异率
            mutation_result = self.mutate_structure()
        else:
            mutation_result = "No mutation"
        
        # 优化：降低能量消耗（10 → 5）
        return {
            "action": "optimize",
            "success": True,
            "energy_cost": 5,
            "mutation": mutation_result
        }
    
    # =========================================================================
    # 遗传机制
    # =========================================================================
    
    def clone(self) -> 'EvolutionaryAgent':
        """克隆（用于繁殖）"""
        child = EvolutionaryAgent(
            agent_id=random.randint(10000, 99999),  # 随机 ID
            base_dir=self.base_dir
        )
        
        # 继承基因组
        child.genome = self.genome.copy()
        child.genome["modules"] = self.genome["modules"].copy()
        child.genome["strategies"] = self.genome["strategies"].copy()
        child.genome["drive_weights"] = self.genome["drive_weights"].copy()
        child.genome["capabilities"] = self.genome["capabilities"].copy()
        
        # 标记为子代
        child.genome["parent_id"] = self.agent_id
        child.genome["generation"] = self.genome.get("generation", 0) + 1
        child.genome["created"] = datetime.now().isoformat()
        
        child.save()
        
        return child
    
    # =========================================================================
    # 工具方法
    # =========================================================================
    
    def get_capabilities(self) -> Set[str]:
        """获取能力集合"""
        return set(self.genome.get("capabilities", []))
    
    def learn(self, result: Dict):
        """
        从结果中学习
        
        Args:
            result: 行动结果
        """
        # 记录经历
        self.memory["episodic"].append({
            "action": result.get("action"),
            "success": result.get("success"),
            "energy_cost": result.get("energy_cost"),
            "time": datetime.now().isoformat()
        })
        
        # 限制记忆大小（资源优化）
        MAX_MEMORY = 100
        if len(self.memory["episodic"]) > MAX_MEMORY:
            self.memory["episodic"] = self.memory["episodic"][-MAX_MEMORY:]
    
    def get_fitness(self) -> float:
        """计算适应度"""
        # 多指标综合
        energy_score = self.state["energy"] / 100
        complexity_score = len(self.genome["modules"]) / 10
        performance_score = self._get_performance()
        
        fitness = (
            energy_score * 0.3 +
            complexity_score * 0.3 +
            performance_score * 0.4
        )
        
        return fitness
    
    def __repr__(self):
        return f"EvolutionaryAgent(id={self.agent_id}, gen={self.genome.get('generation', 0)}, energy={self.state.get('energy', 0)})"


if __name__ == "__main__":
    # 测试
    agent = EvolutionaryAgent(agent_id=1)
    print(f"Created: {agent}")
    
    # 测试变异
    for i in range(5):
        result = agent.mutate_structure()
        print(f"Mutation {i+1}: {result}")
    
    # 测试驱动计算
    class MockEnv:
        def get_prediction_error(self, pos): return 0.5
        def get_changes_caused_by(self, aid): return [1,2,3]
    
    drives = agent.calculate_drives(MockEnv())
    print(f"Drives: {drives}")
    
    # 测试克隆
    child = agent.clone()
    print(f"Child: {child}")
    print(f"Parent ID: {child.genome['parent_id']}")
