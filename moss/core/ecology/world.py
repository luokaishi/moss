"""
World - Multi-Agent Environment

Core Constraints:
1. Resource Scarcity - energy depletes, agents die without action
2. Costly Action - exploration is not free
3. Information Incompleteness (POMDP) - agents don't see full state
4. Multi-Agent Competition - limited resources, agents compete
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Agent:
    """Agent in ecology"""
    id: int
    position: Tuple[int, int] = (0, 0)
    energy: float = 100.0
    alive: bool = True
    
    # Drive genome (transmissible)
    drive_genome: Dict = field(default_factory=dict)
    
    # Behavior history
    behavior_history: List[str] = field(default_factory=list)
    
    # Fitness
    fitness: float = 0.0
    
    def consume_energy(self, amount: float):
        """Consume energy"""
        self.energy -= amount
        if self.energy <= 0:
            self.alive = False
            self.energy = 0
    
    def gain_energy(self, amount: float):
        """Gain energy"""
        self.energy = min(200.0, self.energy + amount)
    
    def update_fitness(self):
        """Update fitness"""
        diversity = len(set(self.behavior_history[-50:])) if self.behavior_history else 0
        self.fitness = self.energy + diversity * 10


class World:
    """Multi-agent world for drive transmission and competition"""
    
    def __init__(self, size: int = 10, n_agents: int = 3):
        self.size = size
        self.n_agents = n_agents
        
        # Resource map
        self.resources = np.random.rand(size, size) * 50
        self.resource_regen_rate = 0.1
        
        # Statistics (must be initialized before spawning agents)
        self.cycle = 0
        self.death_count = 0
        self.birth_count = 0
        self.drive_transmission_log: List[Dict] = []
        
        # Agents
        self.agents: Dict[int, Agent] = {}
        self.next_agent_id = 0
        
        # Initialize agents
        for _ in range(n_agents):
            self._spawn_agent()
    
    def _spawn_agent(self, parent: Optional[Agent] = None) -> Agent:
        """Spawn new agent"""
        agent_id = self.next_agent_id
        self.next_agent_id += 1
        
        # Random position
        x = np.random.randint(0, self.size)
        y = np.random.randint(0, self.size)
        
        # Inherit drive genome from parent
        if parent:
            drive_genome = self._mutate_genome(parent.drive_genome)
            energy = 50.0
        else:
            drive_genome = self._create_random_genome()
            energy = 100.0
        
        agent = Agent(
            id=agent_id,
            position=(x, y),
            energy=energy,
            drive_genome=drive_genome
        )
        
        self.agents[agent_id] = agent
        self.birth_count += 1
        
        return agent
    
    def _create_random_genome(self) -> Dict:
        """Create random drive genome"""
        return {
            'exploration_bias': np.random.rand(),
            'resource_focus': np.random.rand(),
            'social_bias': np.random.rand(),
            'risk_tolerance': np.random.rand()
        }
    
    def _mutate_genome(self, parent_genome: Dict) -> Dict:
        """Mutate genome"""
        child_genome = {}
        for key, value in parent_genome.items():
            mutation = np.random.randn() * 0.1
            child_genome[key] = np.clip(value + mutation, 0, 1)
        return child_genome
    
    def step(self) -> Dict:
        """World main loop step"""
        self.cycle += 1
        
        # 1. Regenerate resources
        self._regenerate_resources()
        
        # 2. Agents act
        for agent in list(self.agents.values()):
            if not agent.alive:
                continue
            self._agent_act(agent)
        
        # 3. Baseline metabolism
        for agent in list(self.agents.values()):
            if agent.alive:
                agent.consume_energy(0.5)
        
        # 4. Remove dead agents
        dead_agents = [aid for aid, a in self.agents.items() if not a.alive]
        for aid in dead_agents:
            del self.agents[aid]
            self.death_count += 1
        
        # 5. Reproduce high-fitness agents
        self._reproduce_agents()
        
        # 6. Maintain minimum agent count
        while len(self.agents) < self.n_agents:
            self._spawn_agent()
        
        return self.get_stats()
    
    def _regenerate_resources(self):
        """Regenerate resources"""
        self.resources += self.resource_regen_rate
        self.resources = np.clip(self.resources, 0, 100)
    
    def _agent_act(self, agent: Agent):
        """Agent acts"""
        x, y = agent.position
        genome = agent.drive_genome
        
        # Exploration vs exploitation
        if np.random.rand() < genome.get('exploration_bias', 0.5):
            dx = np.random.randint(-1, 2)
            dy = np.random.randint(-1, 2)
        else:
            best_dx, best_dy = self._find_best_direction(x, y)
            dx, dy = best_dx, best_dy
        
        # Move
        new_x = int(np.clip(x + dx, 0, self.size - 1))
        new_y = int(np.clip(y + dy, 0, self.size - 1))
        agent.position = (new_x, new_y)
        
        # Cost
        agent.consume_energy(1.0)
        
        # Collect resources
        resource_here = self.resources[new_x, new_y]
        if resource_here > 10:
            collected = min(resource_here * 0.5, 20)
            agent.gain_energy(collected)
            self.resources[new_x, new_y] -= collected
        
        # Record behavior
        agent.behavior_history.append(f"move_{dx}_{dy}")
        if len(agent.behavior_history) > 100:
            agent.behavior_history = agent.behavior_history[-100:]
        
        # Update fitness
        agent.update_fitness()
    
    def _find_best_direction(self, x: int, y: int) -> Tuple[int, int]:
        """Find direction with most resources"""
        best_dx, best_dy = 0, 0
        best_resource = self.resources[x, y]
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if self.resources[nx, ny] > best_resource:
                        best_resource = self.resources[nx, ny]
                        best_dx, best_dy = dx, dy
        
        return best_dx, best_dy
    
    def _reproduce_agents(self):
        """High-fitness agents reproduce"""
        if len(self.agents) < 2:
            return
        
        # Sort by fitness
        sorted_agents = sorted(self.agents.values(), key=lambda a: a.fitness, reverse=True)
        
        # Top 20% can reproduce
        top_agents = sorted_agents[:max(1, len(sorted_agents) // 5)]
        
        for parent in top_agents:
            if parent.energy > 150:
                parent.consume_energy(50)
                self._spawn_agent(parent)
    
    def get_neighbors(self, agent: Agent, radius: int = 1) -> List[Agent]:
        """Get neighboring agents"""
        x, y = agent.position
        neighbors = []
        
        for other in self.agents.values():
            if other.id == agent.id:
                continue
            ox, oy = other.position
            if abs(ox - x) <= radius and abs(oy - y) <= radius:
                neighbors.append(other)
        
        return neighbors
    
    def transmit_drive(self, from_agent: Agent, to_agent: Agent, 
                       drive_key: str) -> bool:
        """Transmit drive between agents"""
        if drive_key not in from_agent.drive_genome:
            return False
        
        # Copy drive
        to_agent.drive_genome[drive_key] = from_agent.drive_genome[drive_key]
        
        # Log
        self.drive_transmission_log.append({
            'cycle': self.cycle,
            'from': from_agent.id,
            'to': to_agent.id,
            'drive': drive_key
        })
        
        return True
    
    def get_stats(self) -> Dict:
        """Get world statistics"""
        if not self.agents:
            return {
                'cycle': self.cycle,
                'alive_agents': 0,
                'avg_energy': 0,
                'avg_fitness': 0,
                'resource_total': float(np.sum(self.resources))
            }
        
        energies = [a.energy for a in self.agents.values()]
        fitnesses = [a.fitness for a in self.agents.values()]
        
        # Calculate drive diversity
        all_drives = defaultdict(list)
        for a in self.agents.values():
            for key, value in a.drive_genome.items():
                all_drives[key].append(value)
        
        drive_diversity = {}
        for key, values in all_drives.items():
            drive_diversity[key] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values))
            }
        
        return {
            'cycle': self.cycle,
            'alive_agents': len(self.agents),
            'birth_count': self.birth_count,
            'death_count': self.death_count,
            'avg_energy': float(np.mean(energies)),
            'avg_fitness': float(np.mean(fitnesses)),
            'resource_total': float(np.sum(self.resources)),
            'drive_diversity': drive_diversity,
            'transmissions': len(self.drive_transmission_log)
        }