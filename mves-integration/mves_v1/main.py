#!/usr/bin/env python3
"""
MVES v1.0 - Minimal Viable Evolutionary System
最小可行演化系统 - 无任务输入的自主演化原型
"""

import time
import json
import os
from datetime import datetime
from agent import Agent
from environment import Environment
from evolution import Evolution

def log_event(message):
    """记录事件到日志文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # 写入日志文件
    os.makedirs("logs", exist_ok=True)
    with open("logs/evolution.log", "a") as f:
        f.write(log_entry + "\n")

def main():
    log_event("=" * 50)
    log_event("MVES v1.0 系统启动")
    log_event("=" * 50)
    
    agent = Agent()
    env = Environment()
    evo = Evolution()
    
    generation = 0
    max_generations = 100  # 最大代数
    
    while generation < max_generations:
        generation += 1
        state = agent.get_state()
        action = agent.act(state)
        result = env.execute(action)
        agent.update(result)
        fitness = env.evaluate(agent)
        
        log_event(f"Gen {generation:3d} | Energy: {agent.state['energy']:6.1f} | Steps: {agent.state['steps']:4d} | Fitness: {fitness:6.1f} | Action: {action:6s} | Strategy: {agent.genome['strategy']}")
        
        # 选择机制 - 死亡判断
        if env.is_dead(fitness):
            log_event(f"⚠️  SYSTEM DIED -> RESET (Generation {generation})")
            agent.reset()
            continue
        
        # 变异触发
        if evo.should_mutate():
            old_strategy = agent.genome["strategy"]
            new_genome = evo.mutate(agent.genome)
            new_fitness = evo.evaluate(new_genome, env)
            
            if new_fitness > fitness:
                agent.genome = new_genome
                agent.save_genome()
                log_event(f"🧬 GENOME UPDATED: {old_strategy} -> {agent.genome['strategy']}")
        
        # 保存状态快照
        if generation % 10 == 0:
            with open("memory.json", "w") as f:
                json.dump({
                    "generation": generation,
                    "genome": agent.genome,
                    "state": agent.state,
                    "fitness": fitness
                }, f, indent=2)
        
        time.sleep(0.5)  # 控制节奏便于观察
    
    log_event("=" * 50)
    log_event(f"实验完成 - 总代数：{generation}")
    log_event("=" * 50)
    
    # 最终报告
    print("\n📊 最终状态报告:")
    print(f"  最终策略：{agent.genome['strategy']}")
    print(f"  最终能量：{agent.state['energy']:.1f}")
    print(f"  总步数：{agent.state['steps']}")
    print(f"  最终适应度：{fitness:.1f}")

if __name__ == "__main__":
    main()
