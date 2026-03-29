#!/usr/bin/env python3
"""
MVES v3 - 自修改代码 + 多体繁殖的演化系统
数字生命系统：Code as Genome, 群体选择
"""

import time
import json
import os
import shutil
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
    with open("logs/evolution_v3.log", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def save_checkpoint(agents, generation, reason=""):
    """保存群体检查点"""
    checkpoint = {
        "generation": generation,
        "timestamp": datetime.now().isoformat(),
        "population_size": len(agents),
        "agents": [a.get_info() for a in agents],
        "reason": reason
    }
    
    os.makedirs("checkpoints", exist_ok=True)
    filename = f"checkpoints/checkpoint_gen{generation:04d}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    return filename

def init_population(size=5):
    """初始化群体"""
    agents = []
    for i in range(size):
        agent = Agent(i)
        agents.append(agent)
    return agents

def main():
    log_event("=" * 60)
    log_event("MVES v3 - 自修改代码 + 多体繁殖演化系统启动")
    log_event("=" * 60)
    log_event("核心跃迁：Code as Genome, 群体选择，数字生命")
    
    # 清理旧数据
    if os.path.exists("agents"):
        shutil.rmtree("agents")
    os.makedirs("agents", exist_ok=True)
    
    # 初始化
    env = Environment()
    evo = Evolution()
    agents = init_population(size=5)
    
    log_event(f"初始群体：{len(agents)} 个 agent")
    
    generation = 0
    max_generations = 100
    total_births = 0
    total_deaths = 0
    total_mutations = 0
    
    # 初始统计
    stats = evo.get_population_stats(agents)
    log_event(f"初始平均能量：{stats['avg_energy']:.1f}, 平均适应度：{stats['avg_fitness']:.1f}")
    
    while generation < max_generations:
        generation += 1
        
        # 群体大小影响资源竞争
        population_size = len(agents)
        
        if population_size == 0:
            log_event("⚠️ 群体灭绝！实验结束", "WARN")
            break
        
        if population_size > env.carrying_capacity:
            log_event(f"⚠️ 种群过大 ({population_size}), 施加选择压力", "WARN")
            env.apply_population_pressure(agents)
        
        # 每个 agent 行动
        new_agents = []
        for agent in agents:
            # 决策
            action = agent.act()
            
            # 执行（考虑群体竞争）
            result = env.execute(action, population_size)
            agent.update(result, action)
            
            # 自修改（Code as Genome 的关键）
            if evo.should_self_modify():
                if agent.self_modify():
                    total_mutations += 1
                    log_event(f"🧬 Agent {agent.agent_id} 自修改成功 (mutation #{agent.genome['mutation_count']})", "SUCCESS")
            
            # 繁殖
            if agent.should_reproduce():
                child = agent.reproduce()
                new_agents.append(child)
                total_births += 1
                log_event(f"👶 Agent {agent.agent_id} 繁殖子代 #{child.agent_id}", "SUCCESS")
            
            # 死亡
            if env.is_dead(agent):
                total_deaths += 1
                log_event(f"💀 Agent {agent.agent_id} 死亡 (energy={agent.state['energy']:.1f}, steps={agent.state['steps']})", "WARN")
        
        # 更新群体
        agents = [a for a in agents if not env.is_dead(a)] + new_agents
        
        # 群体控制（防止爆炸）
        if len(agents) > env.carrying_capacity:
            culled = evo.cull_weakest(agents, len(agents) - env.carrying_capacity)
            if culled:
                log_event(f"🗑️ 淘汰 {len(culled)} 个最弱 agent", "WARN")
        
        # 获取群体统计
        stats = evo.get_population_stats(agents)
        
        # 日志
        log_entry = (
            f"Gen {generation:3d} | "
            f"Pop: {stats['count']:2d} | "
            f"Energy: {stats['avg_energy']:5.1f}±{stats['max_energy']-stats['min_energy']:.1f} | "
            f"Fitness: {stats['avg_fitness']:5.1f} | "
            f"Mutations: {stats['avg_mutations']:.1f} | "
            f"Births: {total_births:2d} | "
            f"Deaths: {total_deaths:2d}"
        )
        log_event(log_entry)
        
        # 定期保存检查点
        if generation % 10 == 0:
            checkpoint_file = save_checkpoint(agents, generation, "periodic")
            log_event(f"💾 检查点已保存：{checkpoint_file}")
        
        time.sleep(0.5)  # 控制节奏
    
    # 最终报告
    log_event("=" * 60)
    log_event(f"实验完成 - 总代数：{generation}")
    log_event(f"总出生：{total_births}, 总死亡：{total_deaths}, 总变异：{total_mutations}")
    log_event("=" * 60)
    
    # 最终统计
    final_stats = evo.get_population_stats(agents)
    
    print("\n📊 MVES v3 最终状态报告:")
    print(f"  最终群体大小：{final_stats['count']}")
    print(f"  平均能量：{final_stats['avg_energy']:.1f}")
    print(f"  平均适应度：{final_stats['avg_fitness']:.1f}")
    print(f"  平均变异数：{final_stats['avg_mutations']:.1f}")
    print(f"  总出生数：{total_births}")
    print(f"  总死亡数：{total_deaths}")
    print(f"  总变异数：{total_mutations}")
    
    # 输出最终 agent 信息
    if agents:
        print("\n  最终群体详情:")
        for agent in sorted(agents, key=lambda a: a.get_fitness(), reverse=True)[:5]:
            info = agent.get_info()
            print(f"    Agent {info['id']:2d}: Energy={info['energy']:5.1f}, Fitness={info['fitness']:5.1f}, Mutations={info['mutations']}, Offspring={info['offspring']}")
    
    # 保存最终检查点
    save_checkpoint(agents, generation, "final")
    log_event(f"💾 最终检查点已保存")

if __name__ == "__main__":
    main()
