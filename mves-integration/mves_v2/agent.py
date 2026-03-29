#!/usr/bin/env python3
"""
MVES v2 - 智能体（规则驱动版，保留 LLM 接口）
当前使用规则驱动，但保留完整的认知结构演化机制
"""

import json
import os
import random
from datetime import datetime

class Agent:
    def __init__(self):
        self.load_genome()
        self.state = {
            "energy": 100,
            "steps": 0,
            "generation": 0
        }
        self.memory = []
        self.max_memory = self.genome.get("memory_size", 10)
    
    def load_genome(self):
        """加载基因组（认知结构）"""
        try:
            with open("genome.json", "r", encoding="utf-8") as f:
                self.genome = json.load(f)
        except FileNotFoundError:
            self.genome = {
                "system_prompt": "You are an autonomous agent trying to survive.",
                "decision_rule": "Choose actions that maximize long-term survival.",
                "tool_policy": "Use tools only when necessary.",
                "reflection_rule": "Analyze failures and adjust strategy.",
                "memory_size": 10
            }
            self.save_genome()
    
    def save_genome(self):
        """保存基因组"""
        with open("genome.json", "w", encoding="utf-8") as f:
            json.dump(self.genome, f, indent=2, ensure_ascii=False)
    
    def act(self):
        """
        决策函数
        当前：规则驱动（基于 genome 的决策规则）
        未来：LLM 驱动
        """
        rule = self.genome["decision_rule"].lower()
        energy = self.state["energy"]
        
        # 基于决策规则选择行为
        if "conserve" in rule or "minimize" in rule:
            # 保守策略
            if energy < 50:
                return "idle"
            else:
                return random.choice(["read", "idle"])
        
        elif "explore" in rule or "aggressive" in rule:
            # 探索策略
            if energy < 30:
                return "idle"
            else:
                return random.choice(["read", "write"])
        
        elif "balance" in rule or "long-term" in rule:
            # 平衡策略
            if energy < 20:
                return "idle"
            elif energy < 50:
                return random.choice(["read", "idle"])
            elif energy > 80:
                return random.choice(["write", "write", "read"])
            else:
                return random.choice(["read", "write", "idle"])
        
        elif "risk" in rule:
            # 风险策略
            if energy > 60:
                return "write"  # 高风险高回报
            else:
                return random.choice(["read", "idle"])
        
        else:
            # 默认：基于能量智能决策
            if energy < 20:
                return "idle"
            elif energy < 40:
                return random.choice(["read", "idle"])
            elif energy < 60:
                return "read"
            elif energy < 80:
                return random.choice(["read", "write"])
            else:
                return random.choice(["read", "write", "idle"])
    
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
        if len(self.memory) > self.max_memory:
            self.memory = self.memory[-self.max_memory:]
    
    def reflect(self):
        """
        反思：基于规则的分析（简化版）
        未来：LLM 驱动的深度反思
        """
        if len(self.memory) < 5:
            return None
        
        recent = self.memory[-10:]
        avg_energy = sum(m["energy_change"] for m in recent) / len(recent)
        
        if avg_energy < -1.5:
            return "Energy consumption too high. Consider conserving more."
        elif avg_energy > -0.5:
            return "Good energy management. Continue current strategy."
        else:
            return "Balanced performance. Consider exploring more."
    
    def reset(self):
        """重置状态（死亡后）"""
        self.state = {
            "energy": 100,
            "steps": 0,
            "generation": self.state["generation"]
        }
        self.memory = []
