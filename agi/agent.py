"""
AGIAgent - 自主涌现驱动力Agent

核心能力：
1. 配置初始驱动力和记忆
2. 自主感知环境、决策、行动
3. 从行为模式中自发产生新驱动力
4. 新驱动力通过验证后纳入决策系统
"""

import yaml
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path
from .drive_manager import DriveManager
from .memory_engine import MemoryEngine
from .environment import RealEnvironment, EnvState
from .behavior_tracker import BehaviorTracker
from .emergence_detector import EmergenceDetector

logger = logging.getLogger('AGIAgent')


class AGIAgent:
    """
    自主涌现驱动力Agent

    使用方式：
        agent = AGIAgent('config/agent_config.yaml')
        agent.run(max_cycles=100)
    """

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)

        agent_cfg = self.config.get('agent', {})
        self.name = agent_cfg.get('name', 'AGI-001')
        self.alive = True
        self.cycle = 0

        # 初始化组件
        self.drive_manager = DriveManager(self.config.get('drives', []))
        self.memory = MemoryEngine(self.config.get('memory', {}))
        self.env = RealEnvironment(self.config.get('environment', {}))

        emergence_cfg = self.config.get('emergence', {})
        self.behavior_tracker = BehaviorTracker(
            window_size=emergence_cfg.get('detection_window', 50),
            change_threshold=emergence_cfg.get('change_threshold', 0.05)
        )
        self.emergence_detector = EmergenceDetector(emergence_cfg)

        # 统计
        self._emerged_drives: List[str] = []
        self._start_time = time.time()

        # 日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        )

    @staticmethod
    def _load_config(config_path: str) -> Dict:
        """加载YAML配置"""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config not found: {config_path}, using defaults")
            return {}
        with open(path) as f:
            return yaml.safe_load(f) or {}

    def run(self, max_cycles: int = 100, verbose: bool = True):
        """
        Agent主循环

        循环步骤：
        1. perceive  - 感知环境状态
        2. recall    - 检索相关记忆
        3. evaluate  - 评估各驱动力得分
        4. select    - 选择行动
        5. execute   - 执行行动
        6. reflect   - 存储经验 + 更新记忆
        7. detect    - 检测行为变化 → 触发涌现检测
        """
        logger.info(f"Agent [{self.name}] 启动, max_cycles={max_cycles}")
        if verbose:
            self._print_header()

        for cycle in range(1, max_cycles + 1):
            if not self.alive:
                logger.info("Agent stopped")
                break

            self.cycle = cycle
            try:
                self._one_cycle()
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Cycle {cycle} error: {e}")

            # 周期性日志
            if verbose and cycle % 10 == 0:
                self._print_status()

        self._print_final_report()

    def _one_cycle(self):
        """执行一个完整的决策周期"""

        # 1. 感知环境
        state = self.env.perceive()

        # 2. 检索记忆
        state_desc = self._state_to_query(state)
        relevant_memories = self.memory.recall(state_desc, top_k=3)

        # 3. 评估驱动力
        drive_scores = self.drive_manager.evaluate_all(state)
        best_drive = max(drive_scores, key=drive_scores.get) if drive_scores else 'none'

        # 4. 生成候选行动并选择
        candidates = self.env.generate_action_candidates(state)
        # 如果有记忆，加入记忆相关的行动
        if relevant_memories:
            mem_action = self._memory_to_action(relevant_memories[0])
            if mem_action:
                candidates.append(mem_action)

        action = self.drive_manager.get_weighted_action(state, candidates)

        # 5. 执行行动
        if action:
            result = self.env.execute(action)
        else:
            # 默认探索行动
            result = self.env.execute({
                'type': 'shell',
                'command': 'ls -la',
                'drives': ['curiosity']
            })
            action = {'description': 'default explore'}

        # 6. 反思：存储经验
        reward = 1.0 if result.get('success') else 0.0
        experience = f"Cycle {self.cycle}: {action.get('description', 'unknown')} -> {'OK' if result.get('success') else 'FAIL'}"
        self.memory.store(
            content=experience,
            memory_type='experience',
            importance=0.3 + 0.7 * reward,
            tags=['cycle', best_drive],
            metadata={'cycle': self.cycle, 'drive': best_drive, 'reward': reward}
        )

        # 更新驱动权重
        self.drive_manager.update_weight_from_feedback(best_drive, reward, lr=0.05)

        # 7. 记录行为 + 涌现检测
        self.behavior_tracker.record(action, result, reward, drive_used=best_drive)

        if self.behavior_tracker.has_significant_change():
            self._try_emergence()

    def _try_emergence(self):
        """尝试涌现检测 (v2: GP-based)"""
        logger.info("  >> 行为变化检测到! 尝试 GP 涌现检测...")

        # 记录当前环境状态供 GP 使用
        state = self.env.perceive()
        env_dict = {
            'resource_level': state.resource_level,
            'environment_entropy': state.environment_entropy,
            'error_rate': state.error_rate,
            'file_count_norm': state.file_count / max(state.total_paths, 1),
            'visited_ratio': state.visited_paths / max(state.total_paths, 1),
            'uptime_norm': min(state.uptime_hours / 72.0, 1.0),
            'interaction_norm': min(state.interactions_count / 50.0, 1.0),
            'task_completion': state.task_completion_rate,
        }
        # 简单行为标签：最近窗口内 write_file 比例高则为 1
        recent = self.behavior_tracker.get_recent_behaviors(10) if hasattr(self.behavior_tracker, 'get_recent_behaviors') else []
        write_ratio = sum(1 for b in recent if b.get('type') == 'write_file') / max(len(recent), 1)
        label = 1 if write_ratio > 0.3 else 0
        self.emergence_detector.record_state(env_dict, label)

        existing_drives = self.drive_manager.get_all_drive_names()
        new_drive = self.emergence_detector.detect(
            self.behavior_tracker, existing_drives, self.memory
        )
        if new_drive:
            # 使用 GP 进化的 eval 函数（非常数）
            eval_fn = getattr(new_drive, 'evolved_fn', None)
            if eval_fn is None:
                def eval_fn(s):
                    return 0.5  # fallback

            success = self.drive_manager.add_emergent_drive(
                name=new_drive.name,
                weight=new_drive.weight,
                description=new_drive.description,
                source_behaviors=new_drive.source_behaviors,
                novelty_score=new_drive.novelty_score,
                causal_independence=new_drive.causal_independence,
                eval_fn=eval_fn
            )
            if success:
                self._emerged_drives.append(new_drive.name)
                expr_str = getattr(new_drive, 'expr_string', 'N/A')
                logger.info(f"  >> !! GP 涌现驱动力: {new_drive.name}")
                logger.info(f"     描述: {new_drive.description}")
                logger.info(f"     函数: {expr_str}")
                logger.info(f"     因果力: {new_drive.causal_independence:.2f}")
                self.memory.store(
                    content=f"GP涌现: {new_drive.name} = {expr_str}",
                    memory_type='reflection',
                    importance=0.9,
                    tags=['emergence', new_drive.name, 'gp_evolved']
                )

    def _state_to_query(self, state: EnvState) -> str:
        """将环境状态转为记忆检索查询"""
        return (
            f"resource:{state.resource_level:.2f} "
            f"entropy:{state.environment_entropy:.2f} "
            f"errors:{state.error_rate:.2f} "
            f"files:{state.file_count}"
        )

    def _memory_to_action(self, memory) -> Optional[Dict]:
        """将记忆转化为行动建议"""
        content = memory.content
        if 'ls' in content.lower() or '探索' in content.lower():
            return {'type': 'shell', 'command': 'ls -la', 'description': '探索(记忆驱动)', 'drives': ['curiosity']}
        return None

    def _print_header(self):
        drives = self.drive_manager.get_all_drive_names()
        mem_stats = self.memory.get_stats()
        print(f"\n{'='*60}")
        print(f"  AGI Agent [{self.name}]")
        print(f"  初始驱动力: {drives}")
        print(f"  初始记忆: {mem_stats['total_records']}条")
        print(f"{'='*60}\n")

    def _print_status(self):
        drives = self.drive_manager.get_drive_summary()
        behavior = self.behavior_tracker.get_behavior_summary()
        env_stats = self.env.get_stats()
        mem_stats = self.memory.get_stats()

        print(f"\n--- Cycle {self.cycle} Status ---")
        print('  Drives: ', end='')
        for name, info in drives.items():
            marker = '*' if info['is_emergent'] else ''
            print(f"{name}={info['weight']:.2f}(s={info['score']:.2f}){marker} ", end='')
        print(f"\n  Behavior: success={behavior['success_rate']:.0%}, "
              f"changes={behavior['changes_detected']}")
        print(f"  Memory: {mem_stats['total_records']} records, "
              f"avg_importance={mem_stats['avg_importance']:.2f}")
        print(f"  Env: actions={env_stats['total_actions']}, "
              f"errors={env_stats['error_count']}, uptime={env_stats['uptime_hours']:.1f}h")

    def _print_final_report(self):
        elapsed = (time.time() - self._start_time) / 60.0
        drives = self.drive_manager.get_drive_summary()
        behavior = self.behavior_tracker.get_behavior_summary()
        env_stats = self.env.get_stats()
        emergence_history = self.emergence_detector.get_history()

        print(f"\n{'='*60}")
        print(f"  AGI Agent [{self.name}] Final Report")
        print(f"{'='*60}")
        print(f"  Total cycles: {self.cycle}")
        print(f"  Elapsed: {elapsed:.1f} min")
        print(f"  Emerged drives: {len(self._emerged_drives)}")
        for name in self._emerged_drives:
            print(f"    - {name}")
        print("\n  Final Drive Weights:")
        for name, info in drives.items():
            marker = ' [EMERGED]' if info['is_emergent'] else ''
            print(f"    {name}: weight={info['weight']:.3f}, stability={info['stability']:.2f}{marker}")
        print(f"\n  Behavior: {behavior['total']} actions, success={behavior['success_rate']:.0%}")
        print(f"  Env: {env_stats['total_actions']} commands, {env_stats['error_count']} errors")
        print(f"  Emergence history: {len(emergence_history)} events")
        print(f"{'='*60}")
