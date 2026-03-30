#!/usr/bin/env python3
"""
MVES v5 - 演化引擎（简化版，资源优化）

资源限制：
- 内存：<100 MB
- 磁盘：<10 MB/检查点
- CPU: <50%
"""

import json
import gzip
import os
import random
from datetime import datetime
from typing import Dict, List

from agent import EvolutionaryAgent


class EvolutionEngine:
    """
    演化引擎 v5（简化版）
    
    核心功能:
    1. 种群管理（10 个 agent）
    2. 选择压力（能量耗尽→死亡）
    3. 繁殖机制（前 3 名繁殖）
    4. 检查点保存（gzip 压缩）
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化演化引擎
        
        Args:
            config: 配置字典
                - population_size: 种群大小（默认 10）
                - mutation_rate: 变异率（默认 0.15）
                - checkpoint_interval: 检查点间隔（默认 20 代）
        """
        self.config = config or {}
        self.population_size = self.config.get('population_size', 10)
        self.mutation_rate = self.config.get('mutation_rate', 0.15)
        self.checkpoint_interval = self.config.get('checkpoint_interval', 20)
        
        self.population: List[EvolutionaryAgent] = []
        self.generation = 0
        self.history = []
        
        # 资源监控
        self.max_memory_mb = 200
        self.max_disk_mb = 50
        
        self._init_population()
    
    def _init_population(self):
        """初始化种群"""
        print(f"Initializing population with {self.population_size} agents...")
        
        self.population = []
        for i in range(self.population_size):
            agent = EvolutionaryAgent(agent_id=i, base_dir="agents")
            self.population.append(agent)
        
        print(f"Population initialized: {len(self.population)} agents")
    
    def run_generation(self, environment) -> Dict:
        """
        运行一代演化
        
        Args:
            environment: 环境对象
        
        Returns:
            演化结果字典
        """
        deaths = 0
        births = 0
        mutations = 0
        
        # 1. 每个 agent 行动
        for agent in self.population:
            if not agent.state:  # 已死亡
                continue
            
            # 决策（传入环境）
            action = agent.decide(environment=environment)
            
            # 执行
            result = agent.execute(action, environment)
            
            # 学习
            agent.learn(result)
            
            # 统计变异
            if result.get('mutation') and 'No mutation' not in result['mutation']:
                mutations += 1
        
        # 2. 应用选择压力
        survivors = []
        for agent in self.population:
            if not agent.state:  # 已死亡
                deaths += 1
                continue
            
            outcome = environment.apply_selection_pressure(agent)
            if outcome == "death":
                deaths += 1
            else:
                survivors.append(agent)
        
        # 3. 繁殖（每代固定繁殖 2-3 个，保持演化压力）
        breed_target = min(3, len(survivors))  # 最多 3 个
        for i in range(breed_target):
            if len(self.population) >= self.population_size * 1.2:  # 允许超出 20%
                break
            
            # 选择适应度最高的
            best = max(survivors, key=lambda a: a.get_fitness())
            
            child = best.clone()
            
            # 优化：增加变异触发
            mutation_result = child.mutate_structure()
            mutations += 1  # 修复：更新变异计数
            print(f"  → Born: agent {child.agent_id} from {best.agent_id}, mutation: {mutation_result[:40]}...")
            
            self.population.append(child)
            births += 1
        
        # 4. 更新代数
        self.generation += 1
        
        # 5. 记录历史
        result = {
            'generation': self.generation,
            'deaths': deaths,
            'births': births,
            'mutations': mutations,
            'population_size': len([a for a in self.population if a.state]),
            'avg_fitness': self._avg_fitness()
        }
        self.history.append(result)
        
        return result
    
    def _avg_fitness(self) -> float:
        """计算平均适应度"""
        survivors = [a for a in self.population if a.state]
        if not survivors:
            return 0.0
        return sum(a.get_fitness() for a in survivors) / len(survivors)
    
    def save_checkpoint(self, filepath: str = None):
        """
        保存检查点（gzip 压缩）
        
        Args:
            filepath: 文件路径（默认自动生成）
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"checkpoints/checkpoint_gen{self.generation}_{timestamp}.json.gz"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 只保存必要数据（节省空间）
        checkpoint = {
            'generation': self.generation,
            'population_size': len(self.population),
            'history': self.history[-100:],  # 只保留最近 100 代
            'config': self.config,
            'top_agents': []
        }
        
        # 保存前 3 名 agent 的基因组
        survivors = [a for a in self.population if a.state]
        if survivors:
            top_agents = sorted(survivors, key=lambda a: a.get_fitness())[:3]
            for agent in top_agents:
                checkpoint['top_agents'].append({
                    'agent_id': agent.agent_id,
                    'genome': agent.genome,
                    'fitness': agent.get_fitness()
                })
        
        # gzip 压缩保存
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)
        
        file_size_mb = os.path.getsize(filepath) / 1024 / 1024
        print(f"Checkpoint saved: {filepath} ({file_size_mb:.2f} MB)")
        
        return filepath
    
    def load_checkpoint(self, filepath: str):
        """
        加载检查点
        
        Args:
            filepath: 文件路径
        """
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        self.generation = checkpoint['generation']
        self.history = checkpoint['history']
        self.config = checkpoint['config']
        
        # 恢复种群
        self.population = []
        for agent_data in checkpoint['top_agents']:
            agent = EvolutionaryAgent(
                agent_id=agent_data['agent_id'],
                base_dir="agents"
            )
            agent.genome = agent_data['genome']
            agent.save()
            self.population.append(agent)
        
        print(f"Checkpoint loaded: generation {self.generation}, {len(self.population)} agents")
    
    def get_statistics(self) -> Dict:
        """获取当前统计信息"""
        survivors = [a for a in self.population if a.state]
        
        return {
            'generation': self.generation,
            'population_size': len(survivors),
            'avg_fitness': self._avg_fitness(),
            'max_fitness': max((a.get_fitness() for a in survivors), default=0),
            'avg_energy': sum(a.state.get('energy', 0) for a in survivors) / len(survivors) if survivors else 0,
            'total_deaths': sum(h['deaths'] for h in self.history),
            'total_births': sum(h['births'] for h in self.history),
            'total_mutations': sum(h['mutations'] for h in self.history)
        }
    
    def check_resources(self):
        """检查资源使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            disk_percent = psutil.disk_usage('.').percent
            
            print(f"Resources: Memory={memory_mb:.1f}MB, Disk={disk_percent:.1f}%")
            
            # 警告
            if memory_mb > self.max_memory_mb * 0.8:
                print(f"⚠️  Warning: Memory usage high ({memory_mb:.1f}MB / {self.max_memory_mb}MB)")
            if disk_percent > 80:
                print(f"⚠️  Warning: Disk usage high ({disk_percent:.1f}%)")
            
            return {'memory_mb': memory_mb, 'disk_percent': disk_percent}
        
        except Exception as e:
            print(f"Resource check failed: {e}")
            return {}
    
    def optimize_resources(self):
        """优化资源使用"""
        print("Optimizing resources...")
        
        # 1. 垃圾回收
        import gc
        gc.collect()
        
        # 2. 清理旧历史
        if len(self.history) > 100:
            self.history = self.history[-100:]
            print("Cleaned old history")
        
        # 3. 如果种群太大，减少
        if len(self.population) > self.population_size * 1.5:
            # 移除适应度最低的
            survivors = [a for a in self.population if a.state]
            survivors.sort(key=lambda a: a.get_fitness())
            self.population = survivors[:int(self.population_size * 1.2)]
            print(f"Reduced population to {len(self.population)}")
        
        self.check_resources()


class SimpleEnvironment:
    """
    简化环境（内存版，资源优化）
    
    资源限制:
    - 内存：<50 MB
    - 磁盘：0（不持久化）
    """
    
    def __init__(self, size: tuple = (20, 20), initial_resources: int = 1500):
        """
        初始化环境
        
        Args:
            size: 环境大小 (宽，高)
            initial_resources: 初始资源
        """
        self.size = size
        self.resources = initial_resources
        self.structures: Dict[int, List[tuple]] = {}
    
    def apply_selection_pressure(self, agent) -> str:
        """
        应用选择压力
        
        Args:
            agent: 智能体
        
        Returns:
            结果："death" | "resource_penalty" | "survived"
        """
        if not agent.state:
            return "death"
        
        energy = agent.state.get('energy', 0)
        
        if energy <= 0:
            # 死亡
            agent.die()
            return "death"
        
        elif energy < 30:
            # 资源惩罚
            if agent.memory and "episodic" in agent.memory:
                half = len(agent.memory["episodic"]) // 2
                agent.memory["episodic"] = agent.memory["episodic"][half:]
            
            energy_loss = int(energy * 0.3)
            agent.state["energy"] -= energy_loss
            agent.save()
            
            return "resource_penalty"
        
        else:
            return "survived"
    
    def get_prediction_error(self, position: tuple) -> float:
        """
        获取预测误差（简化版）
        
        Args:
            position: 位置 (x, y)
        
        Returns:
            预测误差 (0-1)
        """
        # 简化：随机值
        return random.uniform(0, 1)
    
    def get_changes_caused_by(self, agent_id: int) -> List:
        """
        获取 agent 造成的变化
        
        Args:
            agent_id: agent ID
        
        Returns:
            变化列表
        """
        return self.structures.get(agent_id, [])
    
    def add_structure(self, x: int, y: int, agent_id: int):
        """
        添加结构
        
        Args:
            x: x 坐标
            y: y 坐标
            agent_id: agent ID
        """
        if agent_id not in self.structures:
            self.structures[agent_id] = []
        
        self.structures[agent_id].append((x, y))
    
    def get_resource_rate(self, hour: int) -> float:
        """
        获取资源再生率（支持环境变化阶段）
        
        Args:
            hour: 当前小时
        
        Returns:
            资源再生率 (0-1)
        """
        # Phase 1 (0-48h): 稳定
        if hour < 48:
            return 1.0
        
        # Phase 2 (48-96h): 资源减少 50%
        elif hour < 96:
            return 0.5
        
        # Phase 3 (96-144h): 新工具可用
        elif hour < 144:
            return 1.0
        
        # Phase 4 (144-168h): 环境重构
        else:
            return 1.5


if __name__ == "__main__":
    # 快速测试
    print("="*60)
    print("Evolution Engine Quick Test")
    print("="*60)
    
    # 创建引擎
    config = {
        'population_size': 5,  # 小种群测试
        'mutation_rate': 0.15,
        'checkpoint_interval': 5
    }
    
    engine = EvolutionEngine(config)
    env = SimpleEnvironment()
    
    # 运行 10 代
    for i in range(10):
        result = engine.run_generation(env)
        print(f"Gen {result['generation']:3d}: "
              f"Pop={result['population_size']:2d}, "
              f"Deaths={result['deaths']}, "
              f"Births={result['births']}, "
              f"Mutations={result['mutations']}")
        
        # 保存检查点
        if engine.generation % engine.checkpoint_interval == 0:
            engine.save_checkpoint()
        
        # 资源检查
        if i % 5 == 0:
            engine.check_resources()
    
    # 最终统计
    print("\n" + "="*60)
    print("Final Statistics:")
    stats = engine.get_statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("="*60)
    print("Quick test complete!")
