"""
MVES v4 - 开放环境（可被 agent 修改）
核心：环境本身成为可塑对象
"""

import random
import json
import os

class OpenEnvironment:
    def __init__(self, width=20, height=20):
        self.width = width
        self.height = height
        
        # 资源网格
        self.resources = [[random.uniform(0, 10) for _ in range(width)] for _ in range(height)]
        
        # 结构（agent 创造）
        self.structures = []
        
        # 规则（可被修改）
        self.rules = {
            "resource_regeneration": 0.1,  # 每代再生率
            "action_cost": {
                "read": -1.0,
                "write": -2.0,
                "idle": -0.5,
                "gather": -0.5,
                "build": -3.0
            },
            "competition_factor": 0.5
        }
        
        # 环境历史（用于追踪变化）
        self.history = []
    
    def get_resource(self, x, y):
        """获取位置资源"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.resources[y][x]
        return 0
    
    def add_resource(self, x, y, value):
        """添加资源（agent 可调用）"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.resources[y][x] += value
            return True
        return False
    
    def gather_resource(self, x, y, amount):
        """采集资源"""
        if 0 <= x < self.width and 0 <= y < self.height:
            available = self.resources[y][x]
            gathered = min(amount, available)
            self.resources[y][x] -= gathered
            return gathered
        return 0
    
    def create_structure(self, agent, x, y, structure_type):
        """
        创建结构（agent 改变环境）
        """
        structure = {
            "id": len(self.structures) + 1,
            "type": structure_type,
            "x": x,
            "y": y,
            "creator": agent.agent_id,
            "generation": agent.state["generation"]
        }
        self.structures.append(structure)
        
        # 更新 agent 状态
        agent.state["structures_built"] = agent.state.get("structures_built", 0) + 1
        
        return structure
    
    def get_structures_nearby(self, x, y, radius=3):
        """获取附近结构"""
        nearby = []
        for s in self.structures:
            if abs(s["x"] - x) <= radius and abs(s["y"] - y) <= radius:
                nearby.append(s)
        return nearby
    
    def regenerate_resources(self):
        """资源再生"""
        for y in range(self.height):
            for x in range(self.width):
                self.resources[y][x] += self.rules["resource_regeneration"]
                self.resources[y][x] = min(self.resources[y][x], 20)  # 上限
    
    def change_rule(self, rule_id, new_value, agent=None):
        """
        修改环境规则（高阶能力）
        需要 agent 有足够影响力
        """
        if rule_id in self.rules:
            # 检查 agent 是否有足够影响力
            if agent and agent.get_influence() < 5:
                return False, "Insufficient influence"
            
            old_value = self.rules[rule_id]
            self.rules[rule_id] = new_value
            
            self.history.append({
                "type": "rule_change",
                "rule": rule_id,
                "old": old_value,
                "new": new_value,
                "agent": agent.agent_id if agent else None
            })
            
            return True, "Rule changed"
        return False, "Unknown rule"
    
    def get_state_summary(self):
        """获取环境状态摘要"""
        total_resources = sum(sum(row) for row in self.resources)
        avg_resource = total_resources / (self.width * self.height)
        
        return {
            "total_resources": total_resources,
            "avg_resource": avg_resource,
            "structures_count": len(self.structures),
            "rules": self.rules.copy()
        }
    
    def save_snapshot(self, generation):
        """保存环境快照"""
        snapshot = {
            "generation": generation,
            "resources": self.resources,
            "structures": self.structures,
            "rules": self.rules,
            "history": self.history[-100:]  # 最近 100 条历史
        }
        
        os.makedirs("environment_snapshots", exist_ok=True)
        filename = f"environment_snapshots/env_gen{generation:04d}.json"
        with open(filename, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        return filename
