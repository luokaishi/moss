import json
import random

class Agent:
    def __init__(self):
        self.load_genome()
        self.state = {
            "energy": 100,
            "steps": 0
        }
    
    def load_genome(self):
        try:
            with open("genome.json", "r") as f:
                self.genome = json.load(f)
        except:
            self.genome = {
                "prompt": "Explore environment efficiently",
                "strategy": "random",
                "memory_size": 10
            }
    
    def save_genome(self):
        with open("genome.json", "w") as f:
            json.dump(self.genome, f, indent=2)
    
    def get_state(self):
        return self.state
    
    def act(self, state):
        strategy = self.genome["strategy"]
        if strategy == "random":
            return random.choice(["read", "write", "idle"])
        elif strategy == "conserve":
            return "idle" if state["energy"] < 30 else "read"
        elif strategy == "explore":
            return random.choice(["read", "write"])
        return "idle"
    
    def update(self, result):
        self.state["energy"] += result["energy"]
        self.state["steps"] += 1
    
    def reset(self):
        self.state = {"energy": 100, "steps": 0}
