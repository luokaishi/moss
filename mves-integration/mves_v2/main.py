#!/usr/bin/env python3
"""
MVES v2 - LLM 驱动的自演化系统
Proto-AGI 阶段：系统能思考，能修改自己的认知结构
"""

import time
import json
import os
from datetime import datetime

from agent import Agent
from environment import Environment
from evolution import Evolution

def log_event(message, level="INFO"):
    """记录事件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    os.makedirs("logs", exist_ok=True)
    with open("logs/evolution_v2.log", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def save_checkpoint(agent, generation, reason=""):
    """保存检查点"""
    checkpoint = {
        "generation": generation,
        "timestamp": datetime.now().isoformat(),
        "genome": agent.genome,
        "state": agent.state,
        "memory": agent.memory[-10:],  # 最近 10 条记忆
        "reason": reason
    }
    
    os.makedirs("checkpoints", exist_ok=True)
    filename = f"checkpoints/checkpoint_gen{generation:04d}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    return filename

def main():
    log_event("=" * 60)
    log_event("MVES v2 - LLM 驱动的自演化系统启动")
    log_event("=" * 60)
    log_event("核心跃迁：行为由 LLM 生成，基因组控制认知结构")
    
    agent = Agent()
    env = Environment()
    evo = Evolution()
    
    generation = 0
    max_generations = 50  # v2 运行成本高，减少代数
    deaths = 0
    genome_updates = 0
    
    # 初始基因组保存
    log_event(f"初始认知结构：{agent.genome['decision_rule'][:50]}...")
    
    while generation < max_generations:
        generation += 1
        agent.state["generation"] = generation
        
        # LLM 驱动决策
        action = agent.act()
        result = env.execute(action)
        agent.update(result, action)
        
        fitness = env.evaluate(agent)
        is_dead = env.is_dead(agent)
        
        # 日志
        log_entry = (
            f"Gen {generation:3d} | "
            f"Energy: {agent.state['energy']:6.1f} | "
            f"Steps: {agent.state['steps']:3d} | "
            f"Fitness: {fitness:5.1f} | "
            f"Action: {action:6s} | "
            f"Result: {result['message'][:30]}"
        )
        
        if is_dead:
            log_event(log_entry + " *** DEAD ***", "WARN")
            deaths += 1
            
            # 保存死亡前快照
            save_checkpoint(agent, generation, "death")
            
            # 重置
            log_event(f"⚠️ 系统死亡 - 第 {deaths} 次重置", "WARN")
            agent.reset()
            continue
        else:
            log_event(log_entry)
        
        # 变异（认知结构演化）
        if evo.should_mutate():
            old_rule = agent.genome["decision_rule"][:40]
            new_genome = evo.mutate(agent.genome)
            new_fitness = evo.evaluate(new_genome, env, agent)
            
            if new_fitness > fitness:
                agent.genome = new_genome
                agent.save_genome()
                genome_updates += 1
                log_event(f"🧬 基因组更新 #{genome_updates}: {old_rule}... → {agent.genome['decision_rule'][:40]}...", "SUCCESS")
        
        # 反思（meta-evolution：关键跃迁）
        if evo.should_reflect() and len(agent.memory) >= 5:
            reflection = agent.reflect()
            if reflection:
                log_event(f"💭 反思：{reflection[:60]}...", "INFO")
                
                # 将反思应用到基因组
                old_rule = agent.genome["decision_rule"][:40]
                agent.genome = evo.apply_reflection(agent.genome, reflection)
                agent.save_genome()
                
                if agent.genome["decision_rule"][:40] != old_rule:
                    log_event(f"🧬 反思驱动的认知更新：{old_rule}... → {agent.genome['decision_rule'][:40]}...", "SUCCESS")
        
        # 定期保存检查点
        if generation % 10 == 0:
            checkpoint_file = save_checkpoint(agent, generation, "periodic")
            log_event(f"💾 检查点已保存：{checkpoint_file}")
        
        time.sleep(1)  # 控制节奏
    
    # 最终报告
    log_event("=" * 60)
    log_event(f"实验完成 - 总代数：{generation}, 死亡次数：{deaths}, 基因组更新：{genome_updates}")
    log_event("=" * 60)
    
    print("\n📊 MVES v2 最终状态报告:")
    print(f"  总代数：{generation}")
    print(f"  死亡次数：{deaths}")
    print(f"  基因组更新：{genome_updates}")
    print(f"  最终能量：{agent.state['energy']:.1f}")
    print(f"  最终步数：{agent.state['steps']}")
    print(f"  最终适应度：{fitness:.1f}")
    print(f"\n  最终认知结构:")
    print(f"    System: {agent.genome['system_prompt'][:60]}...")
    print(f"    Decision: {agent.genome['decision_rule']}")
    print(f"    Tool Policy: {agent.genome['tool_policy']}")
    print(f"    Memory Size: {agent.genome.get('memory_size', 10)}")
    
    # 保存最终状态
    save_checkpoint(agent, generation, "final")

if __name__ == "__main__":
    main()
