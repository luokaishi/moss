#!/usr/bin/env python3
"""
MVES v4 - 开放环境 + 工具创造 + 目标涌现 (修复版)

修复内容:
- 动态驱动权重 (解决 Curiosity 100% 失衡)
- 安全守护机制 (防止群体崩溃)
- 群体规模扩展 (10 → 50)

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
from dynamic_drives import DynamicDriveWeights
from safety_guard import MVESSafetyGuard, SafetyLevel


def log_event(message, level="INFO"):
    """记录事件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    os.makedirs("logs", exist_ok=True)
    with open("logs/evolution_v4_fixed.log", "a", encoding="utf-8") as f:
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
    """计算科学评估指标"""
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
        import math
        action_counts = {}
        for a in all_actions:
            action_counts[a] = action_counts.get(a, 0) + 1
        entropy = -sum((c/len(all_actions)) * math.log(c/len(all_actions)) for c in action_counts.values())
    else:
        entropy = 0
    
    # 3. 代际稳定性（存活率）
    survival_rate = len(agents) / (total_births + 1)
    
    # 4. 环境改变幅度
    env_change = env.get_state_summary().get("structures_built", 0)
    
    # 5. 驱动分化
    drive_variance = 0
    if agents and hasattr(agents[0], 'drives'):
        all_drives = [a.drives for a in agents if hasattr(a, 'drives')]
        if all_drives:
            import numpy as np
            drive_variance = np.var([d.get('curiosity', 0.25) for d in all_drives])
    
    return {
        "complexity": complexity_score,
        "entropy": entropy,
        "survival_rate": survival_rate,
        "env_change": env_change,
        "drive_variance": drive_variance,
        "total_births": total_births,
        "total_deaths": total_deaths
    }


def run_experiment(hours=24, quick=False, population_size=50):
    """
    运行修复版 v4 实验
    
    Args:
        hours: 实验时长
        quick: 快速测试模式
        population_size: 群体大小 (默认 50)
    """
    log_event("="*60, "INFO")
    log_event("MVES v4 - 修复版实验启动", "INFO")
    log_event(f"时长：{hours}小时", "INFO")
    log_event(f"群体大小：{population_size}", "INFO")
    log_event("="*60, "INFO")
    
    # 初始化
    agents = init_population(population_size)
    env = OpenEnvironment()
    tool_registry = ToolRegistry()
    
    # 初始化修复模块
    dynamic_weights = DynamicDriveWeights()
    safety_guard = MVESSafetyGuard()
    
    log_event(f"群体初始化完成：{len(agents)} agents", "INFO")
    
    # 实验循环
    start_time = time.time()
    generation = 0
    total_births = 0
    total_deaths = 0
    
    while True:
        elapsed_hours = (time.time() - start_time) / 3600
        
        # 检查实验结束
        if elapsed_hours >= hours:
            log_event(f"实验完成：运行 {elapsed_hours:.2f}小时", "INFO")
            break
        
        # 检查群体灭绝
        if not agents:
            log_event("群体灭绝！实验终止", "CRITICAL")
            break
        
        generation += 1
        
        # 1. 安全检查
        safety_level = safety_guard.check_population_health(agents)
        if safety_level != SafetyLevel.NORMAL:
            intervention = safety_guard.intervene(agents)
            log_event(f"安全干预：{safety_level.name} - {intervention['actions']}", "WARNING")
        
        # 2. 更新驱动权重
        for agent in agents:
            if hasattr(agent, 'drives') and hasattr(agent, 'get_state'):
                agent_state = agent.get_state()
                env_state = env.get_state_summary()
                new_weights = dynamic_weights.update_weights(agent_state, env_state)
                agent.drives = new_weights
        
        # 3. agent 行动
        for agent in agents:
            try:
                agent.act(env, tool_registry)
            except Exception as e:
                log_event(f"Agent {agent.id} 行动失败：{e}", "ERROR")
        
        # 4. 环境更新
        env.update()
        
        # 5. 统计
        alive_agents = [a for a in agents if not getattr(a, 'dead', False)]
        deaths_this_gen = len(agents) - len(alive_agents)
        total_deaths += deaths_this_gen
        
        # 6. 繁殖（如果存活 agent 足够）
        if len(alive_agents) >= 2:
            # 选择最优秀的 2 个 agent 繁殖
            alive_agents.sort(key=lambda a: a.get_fitness(), reverse=True)
            parent1, parent2 = alive_agents[0], alive_agents[1]
            child = parent1.reproduce(parent2)
            if child:
                agents.append(child)
                total_births += 1
        
        # 7. 清理死亡 agent
        agents = [a for a in agents if not getattr(a, 'dead', False)]
        
        # 8. 定期保存检查点
        if generation % 10 == 0:
            metrics = calculate_metrics(agents, env, total_births, total_deaths)
            save_checkpoint(agents, env, generation, metrics)
            
            # 打印进度
            log_event(
                f"Gen {generation:4d} | "
                f"Pop {len(agents):3d} | "
                f"Births {total_births:4d} | "
                f"Deaths {total_deaths:4d} | "
                f"Survival {metrics.get('survival_rate', 0):.1%}",
                "INFO"
            )
        
        # 9. 时间控制
        time.sleep(0.1)  # 避免 CPU 过载
    
    # 最终保存
    final_metrics = calculate_metrics(agents, env, total_births, total_deaths)
    save_checkpoint(agents, env, generation, final_metrics, "FINAL")
    
    # 生成报告
    log_event("="*60, "INFO")
    log_event("实验报告", "INFO")
    log_event(f"总代数：{generation}", "INFO")
    log_event(f"最终群体：{len(agents)}", "INFO")
    log_event(f"总出生：{total_births}", "INFO")
    log_event(f"总死亡：{total_deaths}", "INFO")
    log_event(f"存活率：{final_metrics.get('survival_rate', 0):.1%}", "INFO")
    log_event(f"复杂度：{final_metrics.get('complexity', 0):.2f}", "INFO")
    log_event(f"行为熵：{final_metrics.get('entropy', 0):.2f}", "INFO")
    log_event("="*60, "INFO")
    
    return final_metrics


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MVES v4 - 修复版实验")
    parser.add_argument("--hours", type=int, default=24, help="实验时长 (小时)")
    parser.add_argument("--quick", action="store_true", help="快速测试 (1 小时)")
    parser.add_argument("--population", type=int, default=50, help="群体大小")
    
    args = parser.parse_args()
    
    hours = 1 if args.quick else args.hours
    pop_size = args.population
    
    run_experiment(hours=hours, quick=args.quick, population_size=pop_size)
