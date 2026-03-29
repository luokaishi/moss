"""
MVES v4 - 开放环境 + 工具创造 + 目标涌现
科学评估框架：可证伪的实验设计
"""

import time
import json
import os
import shutil
from datetime import datetime

from agent import Agent
from environment import OpenEnvironment
from tool_registry import ToolRegistry
from drives import Drives

def log_event(message, level="INFO"):
    """记录事件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    os.makedirs("logs", exist_ok=True)
    with open("logs/evolution_v4.log", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def save_checkpoint(agents, env, generation, metrics, reason=""):
    """保存检查点"""
    checkpoint = {
        "generation": generation,
        "timestamp": datetime.now().isoformat(),
        "population": [a.get_info() for a in agents],
        "environment": env.get_state_summary(),
        "metrics": metrics,
        "reason": reason
    }
    
    os.makedirs("checkpoints", exist_ok=True)
    filename = f"checkpoints/checkpoint_gen{generation:04d}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    return filename

def init_population(size=10):
    """初始化群体"""
    agents = []
    for i in range(size):
        agent = Agent(i)
        agents.append(agent)
    return agents

def calculate_metrics(agents, env, total_births, total_deaths):
    """
    计算科学评估指标
    """
    if not agents:
        return {"error": "Population extinct"}
    
    # 1. 结构复杂度（代码/工具）
    avg_tools = sum(len(a.tools) for a in agents) / len(agents)
    avg_structures = sum(a.state.get("structures_built", 0) for a in agents) / len(agents)
    complexity_score = avg_tools + avg_structures * 2
    
    # 2. 行为熵（行为分布）
    all_actions = []
    for a in agents:
        if a.memory.get("episodic"):
            actions = [m["action"] for m in a.memory["episodic"][-10:]]
            all_actions.extend(actions)
    
    if all_actions:
        action_counts = {}
        for a in all_actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        # 熵计算
        import math
        entropy = -sum((c/len(all_actions)) * math.log(c/len(all_actions)) for c in action_counts.values())
    else:
        entropy = 0
    
    # 3. 代际稳定性
    avg_generation = sum(a.state["generation"] for a in agents) / len(agents)
    
    # 4. 环境改变幅度
    env_change = len(env.structures) + len(env.history)
    
    # 5. 驱动分布
    from drives import Drives
    dominant_drives = {}
    for a in agents:
        scores = Drives.calculate_scores(a)
        dominant = scores["dominant"]
        dominant_drives[dominant] = dominant_drives.get(dominant, 0) + 1
    
    return {
        "population_size": len(agents),
        "avg_energy": sum(a.state["energy"] for a in agents) / len(agents),
        "avg_fitness": sum(a.get_fitness() for a in agents) / len(agents),
        "complexity_score": complexity_score,
        "behavior_entropy": entropy,
        "avg_generation": avg_generation,
        "environment_change": env_change,
        "dominant_drives": dominant_drives,
        "total_births": total_births,
        "total_deaths": total_deaths
    }

def main():
    log_event("=" * 70)
    log_event("MVES v4 - 开放环境 + 工具创造 + 目标涌现")
    log_event("科学评估框架：可证伪的实验设计")
    log_event("=" * 70)
    
    # 清理旧数据
    if os.path.exists("agents"):
        shutil.rmtree("agents")
    os.makedirs("agents", exist_ok=True)
    
    # 初始化
    env = OpenEnvironment(width=20, height=20)
    tool_registry = ToolRegistry()
    agents = init_population(size=10)
    
    log_event(f"初始群体：{len(agents)} 个 agent")
    log_event(f"环境大小：{env.width}x{env.height}, 初始资源：{sum(sum(row) for row in env.resources):.0f}")
    
    generation = 0
    max_generations = 100
    total_births = 0
    total_deaths = 0
    
    # 初始指标
    metrics = calculate_metrics(agents, env, 0, 0)
    log_event(f"初始平均能量：{metrics['avg_energy']:.1f}, 复杂度：{metrics['complexity_score']:.1f}")
    
    while generation < max_generations:
        generation += 1
        
        # 环境再生
        env.regenerate_resources()
        
        # 每个 agent 行动
        new_agents = []
        for agent in agents:
            # 行动（使用工具、改变环境）
            result = agent.act(env, tool_registry)
            
            # 繁殖
            if agent.should_reproduce():
                child = agent.reproduce() if hasattr(agent, 'reproduce') else None
                if child:
                    new_agents.append(child)
                    total_births += 1
                    log_event(f"👶 Agent {agent.agent_id} 繁殖子代", "SUCCESS")
            
            # 死亡
            if agent.is_dead():
                total_deaths += 1
                log_event(f"💀 Agent {agent.agent_id} 死亡", "WARN")
        
        # 更新群体
        agents = [a for a in agents if not a.is_dead()] + new_agents
        
        # 群体灭绝检查
        if not agents:
            log_event("⚠️ 群体灭绝！实验结束", "CRITICAL")
            break
        
        # 计算指标
        metrics = calculate_metrics(agents, env, total_births, total_deaths)
        
        # 日志
        log_entry = (
            f"Gen {generation:3d} | "
            f"Pop: {metrics['population_size']:2d} | "
            f"Energy: {metrics['avg_energy']:5.1f} | "
            f"Complexity: {metrics['complexity_score']:.1f} | "
            f"Entropy: {metrics['behavior_entropy']:.2f} | "
            f"Env Change: {metrics['environment_change']:2d} | "
            f"Drives: {metrics['dominant_drives']}"
        )
        log_event(log_entry)
        
        # 定期保存
        if generation % 10 == 0:
            checkpoint_file = save_checkpoint(agents, env, generation, metrics, "periodic")
            env.save_snapshot(generation)
            log_event(f"💾 检查点已保存：{checkpoint_file}")
        
        time.sleep(0.3)
    
    # 最终报告
    log_event("=" * 70)
    log_event(f"实验完成 - 总代数：{generation}")
    log_event(f"总出生：{total_births}, 总死亡：{total_deaths}")
    log_event("=" * 70)
    
    # 最终指标
    final_metrics = calculate_metrics(agents, env, total_births, total_deaths)
    
    print("\n📊 MVES v4 最终状态报告:")
    print(f"  最终群体：{final_metrics.get('population_size', 0)}")
    print(f"  平均能量：{final_metrics.get('avg_energy', 0):.1f}")
    print(f"  平均适应度：{final_metrics.get('avg_fitness', 0):.1f}")
    print(f"  复杂度得分：{final_metrics.get('complexity_score', 0):.1f}")
    print(f"  行为熵：{final_metrics.get('behavior_entropy', 0):.2f}")
    print(f"  环境改变：{final_metrics.get('environment_change', 0)}")
    print(f"  驱动分布：{final_metrics.get('dominant_drives', {})}")
    
    # 科学评估
    print("\n🔬 科学评估:")
    
    # 评估标准
    success_criteria = {
        "结构复杂度增长": final_metrics.get('complexity_score', 0) > 2,
        "行为多样性": final_metrics.get('behavior_entropy', 0) > 1.0,
        "环境改造": final_metrics.get('environment_change', 0) > 5,
        "群体存活": final_metrics.get('population_size', 0) > 3,
        "驱动分化": len(final_metrics.get('dominant_drives', {})) > 1
    }
    
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {criterion}")
    
    # 保存最终检查点
    save_checkpoint(agents, env, generation, final_metrics, "final")
    log_event(f"💾 最终检查点已保存")

if __name__ == "__main__":
    main()
