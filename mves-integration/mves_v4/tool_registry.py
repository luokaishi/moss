"""
MVES v4 - 工具注册表
核心：工具 = 可执行能力模块
"""

import random

class ToolRegistry:
    """
    管理所有可用工具
    """
    
    def __init__(self):
        self.tools = {
            "gather": self.gather_tool,
            "predict": self.predict_tool,
            "optimize": self.optimize_tool,
            "store": self.store_tool,
            "scan": self.scan_tool
        }
        
        self.tool_costs = {
            "gather": -0.5,
            "predict": -1.0,
            "optimize": -1.5,
            "store": -0.5,
            "scan": -0.3
        }
    
    def gather_tool(self, state, environment):
        """
        采集工具：从环境中获取资源
        """
        x, y = state.get("x", 0), state.get("y", 0)
        gathered = environment.gather_resource(x, y, 5)
        return {
            "tool": "gather",
            "success": gathered > 0,
            "energy_gain": gathered,
            "message": f"Gathered {gathered:.1f} resources"
        }
    
    def predict_tool(self, state, environment):
        """
        预测工具：预测下一步最佳行动
        （简化版：基于当前能量）
        """
        energy = state.get("energy", 100)
        if energy < 30:
            prediction = "idle"
        elif energy < 60:
            prediction = "gather"
        else:
            prediction = "write"
        
        return {
            "tool": "predict",
            "prediction": prediction,
            "confidence": random.uniform(0.6, 0.9),
            "message": f"Predicted best action: {prediction}"
        }
    
    def optimize_tool(self, state, environment):
        """
        优化工具：提高能量效率
        """
        # 临时降低行动成本
        return {
            "tool": "optimize",
            "success": True,
            "efficiency_bonus": 0.2,  # 20% 效率提升
            "duration": 5,  # 持续 5 代
            "message": "Optimization active for 5 generations"
        }
    
    def store_tool(self, state, environment):
        """
        存储工具：储备资源
        """
        stored = state.get("energy", 0) * 0.2  # 存储 20% 能量
        return {
            "tool": "store",
            "stored": stored,
            "reserved": True,
            "message": f"Stored {stored:.1f} energy reserves"
        }
    
    def scan_tool(self, state, environment):
        """
        扫描工具：探测周围资源
        """
        x, y = state.get("x", 0), state.get("y", 0)
        nearby = environment.get_structures_nearby(x, y, radius=5)
        resource_level = environment.get_resource(x, y)
        
        return {
            "tool": "scan",
            "nearby_structures": len(nearby),
            "resource_level": resource_level,
            "message": f"Scanned area: {resource_level:.1f} resources, {len(nearby)} structures"
        }
    
    def use_tool(self, tool_name, agent, environment):
        """
        使用工具
        返回：工具执行结果
        """
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        # 检查能量成本
        cost = self.tool_costs.get(tool_name, -1.0)
        if agent.state["energy"] + cost < 0:
            return {"success": False, "error": "Insufficient energy"}
        
        # 执行工具
        agent.state["energy"] += cost
        result = self.tools[tool_name](agent.state, environment)
        result["cost"] = cost
        
        return result
    
    def get_available_tools(self, agent):
        """获取 agent 可用的工具"""
        return list(agent.tools) if hasattr(agent, 'tools') else []
