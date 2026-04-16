#!/usr/bin/env python3
"""
MOSS 多Agent协作实验 v5.5.0
验证涌现驱动力在多Agent场景中的稳定性

特性:
- 2-Agent 协作实验
- 3-Agent 竞争实验
- 驱动力传播观察
- 涌现驱动群体收敛分析

使用:
    python experiment_v5_multiagent.py --mode 2agent --cycles 5000
    python experiment_v5_multiagent.py --mode 3agent --cycles 5000
"""

import os
import sys
import json
import time
import signal
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agi.agent import AGIAgent
from agi.ecology.world import World, Agent as EcoAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('experiment-multiagent')


class MOSSAgentWrapper:
    """包装 MOSS Agent 以适应 Ecology World"""
    
    def __init__(self, agent_id: int, config_path: str, world: World):
        self.id = agent_id
        self.moss_agent = AGIAgent(config_path)
        self.world = world
        self.eco_agent: Optional[EcoAgent] = None
        
        # 行为历史
        self.action_history: List[str] = []
        self.drive_influences: Dict[str, float] = {}
        
    def spawn(self, position: tuple):
        """在生态世界中生成"""
        # 创建生态 Agent
        self.eco_agent = EcoAgent(
            id=self.id,
            position=position,
            energy=100.0,
            drive_genome=self._extract_drive_genome()
        )
        return self.eco_agent
    
    def _extract_drive_genome(self) -> Dict:
        """从 MOSS Agent 提取驱动力基因组"""
        drives = self.moss_agent.drive_manager.get_drive_summary()
        return {
            'survival': drives.get('survival', {}).get('weight', 0.25),
            'curiosity': drives.get('curiosity', {}).get('weight', 0.25),
            'influence': drives.get('influence', {}).get('weight', 0.25),
            'optimization': drives.get('optimization', {}).get('weight', 0.25),
        }
    
    def act(self, world_state: Dict) -> str:
        """执行一个周期"""
        # 运行 MOSS Agent 一个周期
        try:
            self.moss_agent._one_cycle()
            action_desc = f"cycle_{self.moss_agent.cycle}"
            self.action_history.append(action_desc)
            
            # 更新生态 Agent 的基因组
            if self.eco_agent:
                self.eco_agent.drive_genome = self._extract_drive_genome()
                self.eco_agent.behavior_history.append(action_desc)
            
            return action_desc
        except Exception as e:
            logger.error(f"Agent {self.id} 执行错误: {e}")
            return f"error_{e}"
    
    def get_drive_weights(self) -> Dict[str, float]:
        """获取当前驱动力权重"""
        drives = self.moss_agent.drive_manager.get_drive_summary()
        return {name: data.get('weight', 0) for name, data in drives.items()}
    
    def get_emerged_drives(self) -> List[str]:
        """获取涌现的驱动力"""
        return list(self.moss_agent._emerged_drives)


class MultiAgentExperiment:
    """多Agent实验控制器"""
    
    def __init__(self, mode: str, n_cycles: int, run_dir: str, config_path: str):
        self.mode = mode
        self.n_cycles = n_cycles
        self.run_dir = run_dir
        self.config_path = config_path
        
        # 创建生态世界
        self.world_size = 10
        self.n_agents = 2 if mode == '2agent' else 3
        self.world = World(size=self.world_size, n_agents=self.n_agents)
        
        # 创建 MOSS Agent 包装器
        self.agents: List[MOSSAgentWrapper] = []
        self._init_agents()
        
        # 统计
        self.cycle = 0
        self.drive_transmission_log: List[Dict] = []
        self.emergence_convergence: Dict[str, List[int]] = {}
        
    def _init_agents(self):
        """初始化 Agents"""
        for i in range(self.n_agents):
            wrapper = MOSSAgentWrapper(i, self.config_path, self.world)
            
            # 随机位置
            import numpy as np
            pos = (np.random.randint(0, self.world_size), 
                   np.random.randint(0, self.world_size))
            
            wrapper.spawn(pos)
            self.agents.append(wrapper)
            
            logger.info(f"Agent {i} 初始化完成，位置: {pos}")
    
    def run(self) -> Dict:
        """运行实验"""
        logger.info(f"开始 {self.mode} 实验，目标 {self.n_cycles} 周期")
        
        for cycle in range(1, self.n_cycles + 1):
            self.cycle = cycle
            
            # 1. 每个 MOSS Agent 执行
            for agent in self.agents:
                agent.act(self.world.get_stats())
            
            # 2. 生态世界步进
            world_stats = self.world.step()
            
            # 3. 检查驱动力传播
            self._check_drive_transmission()
            
            # 4. 检查涌现收敛
            self._check_emergence_convergence()
            
            # 5. 定期报告
            if cycle % 500 == 0:
                self._report_progress(cycle, world_stats)
        
        return self._generate_final_report()
    
    def _check_drive_transmission(self):
        """检查驱动力传播"""
        # 如果 Agents 位置接近，可能发生驱动力传播
        for i, agent1 in enumerate(self.agents):
            for agent2 in self.agents[i+1:]:
                if self._are_neighbors(agent1, agent2):
                    # 模拟驱动力传播
                    self._transmit_drives(agent1, agent2)
    
    def _are_neighbors(self, agent1: MOSSAgentWrapper, agent2: MOSSAgentWrapper) -> bool:
        """检查是否相邻"""
        if not agent1.eco_agent or not agent2.eco_agent:
            return False
        
        x1, y1 = agent1.eco_agent.position
        x2, y2 = agent2.eco_agent.position
        return abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1
    
    def _transmit_drives(self, from_agent: MOSSAgentWrapper, to_agent: MOSSAgentWrapper):
        """传播驱动力"""
        from_drives = from_agent.get_drive_weights()
        to_drives = to_agent.get_drive_weights()
        
        # 记录差异
        for drive_name in from_drives:
            if abs(from_drives[drive_name] - to_drives.get(drive_name, 0)) > 0.1:
                self.drive_transmission_log.append({
                    'cycle': self.cycle,
                    'from_agent': from_agent.id,
                    'to_agent': to_agent.id,
                    'drive': drive_name,
                    'from_weight': from_drives[drive_name],
                    'to_weight': to_drives.get(drive_name, 0)
                })
    
    def _check_emergence_convergence(self):
        """检查涌现驱动力收敛"""
        for agent in self.agents:
            for drive in agent.get_emerged_drives():
                if drive not in self.emergence_convergence:
                    self.emergence_convergence[drive] = []
                if agent.id not in self.emergence_convergence[drive]:
                    self.emergence_convergence[drive].append(agent.id)
    
    def _report_progress(self, cycle: int, world_stats: Dict):
        """进度报告"""
        # 收集 Agents 状态
        agent_states = []
        for agent in self.agents:
            state = {
                'id': agent.id,
                'drives': agent.get_drive_weights(),
                'emerged': agent.get_emerged_drives(),
                'history_len': len(agent.action_history)
            }
            agent_states.append(state)
        
        # 检查涌现收敛
        converged_drives = [d for d, agents in self.emergence_convergence.items() 
                          if len(agents) >= len(self.agents)]
        
        logger.info(
            f"[{cycle:>5,}] "
            f"Agents: {world_stats['alive_agents']} | "
            f"AvgEnergy: {world_stats['avg_energy']:.1f} | "
            f"Transmissions: {len(self.drive_transmission_log)} | "
            f"Converged: {converged_drives}"
        )
    
    def _generate_final_report(self) -> Dict:
        """生成最终报告"""
        report = {
            'experiment': {
                'mode': self.mode,
                'n_agents': self.n_agents,
                'total_cycles': self.cycle,
                'world_size': self.world_size,
            },
            'world_final': self.world.get_stats(),
            'agents': [],
            'drive_transmissions': self.drive_transmission_log,
            'emergence_convergence': self.emergence_convergence,
            'convergence_rate': self._calculate_convergence_rate(),
        }
        
        # Agent 最终状态
        for agent in self.agents:
            agent_report = {
                'id': agent.id,
                'final_drives': agent.get_drive_weights(),
                'emerged_drives': agent.get_emerged_drives(),
                'action_count': len(agent.action_history),
            }
            report['agents'].append(agent_report)
        
        return report
    
    def _calculate_convergence_rate(self) -> float:
        """计算涌现收敛率"""
        if not self.emergence_convergence:
            return 0.0
        
        # 在所有 Agents 中都出现的涌现驱动
        fully_converged = sum(1 for agents in self.emergence_convergence.values() 
                            if len(agents) >= self.n_agents)
        
        return fully_converged / len(self.emergence_convergence)


def main():
    parser = argparse.ArgumentParser(description='MOSS 多Agent实验 v5.5.0')
    parser.add_argument('--mode', type=str, choices=['2agent', '3agent'], 
                       default='2agent', help='实验模式')
    parser.add_argument('--cycles', type=int, default=5000, help='运行周期')
    parser.add_argument('--label', type=str, default='', help='实验标签')
    args = parser.parse_args()

    moss_root = Path(__file__).resolve().parent.parent
    config_path = str(moss_root / 'config' / 'agent_config.yaml')
    
    # 创建实验目录
    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    label = f"_{args.label}" if args.label else ""
    run_dir = str(moss_root / 'logs' / f'experiment_v5_multiagent_{args.mode}_{run_id}{label}')
    os.makedirs(run_dir, exist_ok=True)
    
    # 日志
    fh = logging.FileHandler(os.path.join(run_dir, 'experiment.log'))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    logger.info("=" * 70)
    logger.info("  MOSS 多Agent实验 v5.5.0")
    logger.info("=" * 70)
    logger.info(f"模式: {args.mode}")
    logger.info(f"周期: {args.cycles:,}")
    logger.info(f"目录: {run_dir}")
    
    # 运行实验
    experiment = MultiAgentExperiment(
        mode=args.mode,
        n_cycles=args.cycles,
        run_dir=run_dir,
        config_path=config_path
    )
    
    try:
        final_report = experiment.run()
        
        # 保存报告
        report_file = os.path.join(run_dir, 'final_report.json')
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info("=" * 70)
        logger.info("实验完成!")
        logger.info(f"涌现收敛率: {final_report['convergence_rate']:.2%}")
        logger.info(f"驱动力传播次数: {len(final_report['drive_transmissions'])}")
        logger.info(f"报告: {report_file}")
        logger.info("=" * 70)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    except Exception as e:
        logger.error(f"实验异常: {e}", exc_info=True)


if __name__ == '__main__':
    main()