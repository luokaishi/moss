import random

class Environment:
    def execute(self, action):
        if action == "read":
            return {"energy": -1}
        elif action == "write":
            return {"energy": -2}
        elif action == "idle":
            return {"energy": -0.5}
        return {"energy": -1}
    
    def evaluate(self, agent):
        return agent.state["energy"] + agent.state["steps"]
    
    def is_dead(self, fitness):
        return fitness < 0
