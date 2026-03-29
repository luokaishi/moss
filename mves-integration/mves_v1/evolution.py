import random
import copy

class Evolution:
    def should_mutate(self):
        return random.random() < 0.2
    
    def mutate(self, genome):
        new_genome = copy.deepcopy(genome)
        mutations = [
            self.change_strategy,
            self.change_prompt,
            self.change_memory
        ]
        return random.choice(mutations)(new_genome)
    
    def change_strategy(self, genome):
        genome["strategy"] = random.choice(
            ["random", "conserve", "explore"]
        )
        return genome
    
    def change_prompt(self, genome):
        prompts = [
            "maximize efficiency",
            "explore aggressively",
            "preserve energy"
        ]
        genome["prompt"] = random.choice(prompts)
        return genome
    
    def change_memory(self, genome):
        genome["memory_size"] = random.randint(5, 20)
        return genome
    
    def evaluate(self, genome, env):
        # 简化评估：随机模拟
        return random.random() * 100
