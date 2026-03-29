#!/usr/bin/env python3
"""
MVES v3 - 可演化智能体
核心：Code as Genome, brain.py 可被修改
"""

import json
import os
import random
import shutil
import importlib.util
from datetime import datetime

class Agent:
    def __init__(self, agent_id, base_dir="agents"):
        self.agent_id = agent_id
        self.base_dir = base_dir
        self.agent_dir = os.path.join(base_dir, f"agent_{agent_id}")
        self.brain_path = os.path.join(self.agent_dir, "brain.py")
        self.genome_path = os.path.join(self.agent_dir, "genome.json")
        self.memory_path = os.path.join(self.agent_dir, "memory.json")
        self.state_path = os.path.join(self.agent_dir, "state.json")
        
        # 创建 agent 目录
        os.makedirs(self.agent_dir, exist_ok=True)
        
        # 初始化或加载
        self._init_or_load()
    
    def _init_or_load(self):
        """初始化新 agent 或加载已有 agent"""
        if os.path.exists(self.genome_path):
            self.load()
        else:
            self._create_new()
    
    def _create_new(self):
        """创建新 agent"""
        # 复制基础 brain
        shutil.copy("brain_template.py", self.brain_path)
        
        # 初始基因组
        self.genome = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "parent_id": None,
            "strategy": "survival_basic",
            "mutation_count": 0
        }
        
        # 初始状态
        self.state = {
            "energy": 100,
            "steps": 0,
            "generation": 0,
            "offspring_count": 0
        }
        
        # 空记忆
        self.memory = []
        
        self.save()
    
    def load(self):
        """加载 agent 数据"""
        with open(self.genome_path, "r", encoding="utf-8") as f:
            self.genome = json.load(f)
        
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        
        with open(self.memory_path, "r", encoding="utf-8") as f:
            self.memory = json.load(f)
    
    def save(self):
        """保存 agent 数据"""
        with open(self.genome_path, "w", encoding="utf-8") as f:
            json.dump(self.genome, f, indent=2, ensure_ascii=False)
        
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def act(self):
        """
        使用 brain.py 决策
        核心跃迁：行为由可修改的代码决定
        """
        try:
            # 动态加载 brain.py
            spec = importlib.util.spec_from_file_location("brain", self.brain_path)
            brain = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(brain)
            
            # 调用 decide 函数
            action = brain.decide(self.state, self.memory, self.genome)
            
            # 验证动作
            if action not in ["read", "write", "idle"]:
                action = self._fallback_act()
            
            return action
        except Exception as e:
            print(f"Agent {self.agent_id} brain error: {e}")
            return self._fallback_act()
    
    def _fallback_act(self):
        """brain.py 失败时的回退策略"""
        energy = self.state.get("energy", 100)
        if energy < 20:
            return "idle"
        elif energy < 50:
            return "read"
        else:
            return random.choice(["read", "write"])
    
    def update(self, result, action):
        """更新状态和记忆"""
        self.state["energy"] += result["energy"]
        self.state["steps"] += 1
        self.state["generation"] += 1
        
        self.memory.append({
            "step": self.state["steps"],
            "action": action,
            "energy_change": result["energy"],
            "result": result.get("message", "")
        })
        
        # 限制记忆大小
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]
        
        self.save()
    
    def self_modify(self):
        """
        自修改：让 LLM 或规则修改 brain.py
        返回：是否成功修改
        """
        try:
            with open(self.brain_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            
            # 当前用规则修改（LLM 不可用时）
            new_code = self._rule_based_modify(old_code)
            
            # 安全检查
            if self._safe_check(new_code):
                with open(self.brain_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                
                self.genome["mutation_count"] += 1
                self.genome["last_modified"] = datetime.now().isoformat()
                self.save()
                return True
            else:
                print(f"Agent {self.agent_id}: Code modification blocked by safety check")
                return False
        except Exception as e:
            print(f"Agent {self.agent_id} self-modify error: {e}")
            return False
    
    def _rule_based_modify(self, code):
        """
        基于规则的代码修改（简化版 LLM）
        实际应该用 LLM 生成更智能的修改
        """
        modifications = [
            # 修改能量阈值
            (r'energy < 20', 'energy < 15'),
            (r'energy < 50', 'energy < 40'),
            (r'energy > 80', 'energy > 70'),
            # 修改行为倾向
            (r'return "idle"', 'return "read"'),
            (r'return "read"', 'return random.choice(["read", "idle"])'),
        ]
        
        # 随机选择一个修改
        if random.random() < 0.5 and modifications:
            old, new = random.choice(modifications)
            code = code.replace(old, new, 1)
        
        # 添加变异标记
        code = code.replace(
            'return "survival_basic_v1"',
            f'return "survival_mutated_v{self.genome["mutation_count"] + 1}"'
        )
        
        return code
    
    def _safe_check(self, code):
        """
        安全检查：禁止危险操作
        """
        forbidden = [
            "import os",
            "import sys",
            "import subprocess",
            "delete",
            "remove",
            "socket",
            "urllib",
            "requests",
            "__class__",
            "__bases__",
            "eval(",
            "exec("
        ]
        return not any(f in code for f in forbidden)
    
    def reproduce(self):
        """
        繁殖：创建子代 agent
        返回：子代 agent
        """
        # 创建新 agent ID
        new_id = self._get_next_agent_id()
        
        # 复制当前 agent
        child = Agent(new_id, self.base_dir)
        
        # 复制 brain.py
        shutil.copy(self.brain_path, child.brain_path)
        
        # 复制并修改基因组
        child.genome = self.genome.copy()
        child.genome["parent_id"] = self.agent_id
        child.genome["created"] = datetime.now().isoformat()
        child.genome["version"] = f"{self.genome['version']}.{self.state['offspring_count'] + 1}"
        
        # 重置状态
        child.state = {
            "energy": 80,  # 子代初始能量略低
            "steps": 0,
            "generation": 0,
            "offspring_count": 0,
            "parent_energy": self.state["energy"]
        }
        
        child.memory = []
        child.save()
        
        # 更新父代计数
        self.state["offspring_count"] += 1
        self.save()
        
        return child
    
    def _get_next_agent_id(self):
        """获取下一个可用的 agent ID"""
        existing = []
        if os.path.exists(self.base_dir):
            for name in os.listdir(self.base_dir):
                if name.startswith("agent_"):
                    try:
                        existing.append(int(name.replace("agent_", "")))
                    except:
                        pass
        return max(existing, default=0) + 1
    
    def is_dead(self):
        """判断是否死亡"""
        return self.state["energy"] <= 0
    
    def should_reproduce(self):
        """判断是否应该繁殖"""
        return self.state["energy"] > 150
    
    def get_fitness(self):
        """计算适应度（用于选择）"""
        survival_bonus = min(self.state["steps"] / 10, 30)
        energy_bonus = max(0, self.state["energy"] / 5)
        offspring_bonus = self.state["offspring_count"] * 10
        
        return survival_bonus + energy_bonus + offspring_bonus
    
    def get_info(self):
        """获取 agent 信息"""
        return {
            "id": self.agent_id,
            "energy": self.state["energy"],
            "steps": self.state["steps"],
            "generation": self.state["generation"],
            "offspring": self.state["offspring_count"],
            "mutations": self.genome["mutation_count"],
            "fitness": self.get_fitness()
        }
