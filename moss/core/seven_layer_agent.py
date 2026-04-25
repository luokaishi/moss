"""
SevenLayerAgent - 7层架构AGI Agent

完整的7层系统架构：

Environment (环境)
    ↓
State (状态)
    ↓
Concept System (概念系统)  ← 第7层：认知层
    ↓
Goal System (目标系统)     ← 第6层：目标层
    ↓
Drive System (驱动系统)    ← 第5层：动力层
    ↓
Meta-Drive (元驱动)        ← 第4层：元驱动层
    ↓
Evolution/Ecology (进化/生态) ← 第2-3层：进化层/生态层
    ↓
Policy (策略)
    ↓
Action (行动)

核心创新：
1. 概念涌现：状态→概念的压缩编码
2. 目标涌现：从轨迹中提取稳定行为模式
3. 元驱动：驱动系统的自我修改能力
4. 自我模型：对自身的预测能力
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# 现有组件
from .drive_manager import DriveManager
from .memory_engine import MemoryEngine
from .environment import RealEnvironment, EnvState
from .behavior_tracker import BehaviorTracker
from .emergence_detector import EmergenceDetector

# 7层架构新组件
from .concept import ConceptSystem
from .goal import GoalSystem
from .meta_drive import MetaController, SelfModel

logger = logging.getLogger('SevenLayerAgent')


class SevenLayerAgent:
    """
    7层架构AGI Agent
    
    整合概念系统、目标系统、元驱动和自我模型
    """
    
    def __init__(self, config_path: str = 'config/agent_config.yaml'):
        """
        初始化7层Agent
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        self.name = self.config.get('agent', {}).get('name', 'SevenLayer-001')
        self.cycle = 0
        self.alive = True
        
        # ========== 基础层 ==========
        # 环境
        self.env = RealEnvironment(self.config.get('environment', {}))
        
        # 记忆
        self.memory = MemoryEngine(self.config.get('memory', {}))
        
        # 驱动管理（保留原有功能）
        self.drive_manager = DriveManager(self.config.get('drives', []))
        
        # 行为追踪
        emergence_cfg = self.config.get('emergence', {})
        self.behavior_tracker = BehaviorTracker(
            window_size=emergence_cfg.get('detection_window', 50),
            change_threshold=emergence_cfg.get('change_threshold', 0.05)
        )
        
        # 涌现检测
        self.emergence_detector = EmergenceDetector(emergence_cfg)
        
        # ========== 7层架构新组件 ==========
        state_dim = 16  # 状态维度
        
        # 第7层：概念系统
        self.concept_system = ConceptSystem(
            state_dim=state_dim,
            initial_concepts=4
        )
        
        # 第6层：目标系统
        self.goal_system = GoalSystem(state_dim=state_dim)
        
        # 第4层：元驱动
        # 先创建自我模型
        self.self_model = SelfModel(
            state_dim=state_dim,
            action_dim=10,  # 动作空间维度
            drive_dim=4
        )
        
        # 元控制器
        self.meta_controller = MetaController(
            self_model=self.self_model,
            drive_manager=self.drive_manager
        )
        
        # 统计
        self.stats = {
            'concepts_learned': 0,
            'goals_formed': 0,
            'meta_modifications': 0,
            'self_awareness_history': []
        }
        
        # 当前轨迹（用于目标系统）
        self.current_trajectory = {
            'states': [],
            'actions': [],
            'rewards': []
        }
        
        logger.info(f"SevenLayerAgent [{self.name}] 初始化完成")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        import yaml
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config not found: {config_path}, using defaults")
            return {}
        with open(path) as f:
            return yaml.safe_load(f) or {}
    
    def run(self, max_cycles: int = 100, verbose: bool = True):
        """
        Agent主循环
        
        7层架构的完整循环：
        1. Perceive (感知)
        2. Conceptualize (概念化) - 第7层
        3. Goal-orient (目标导向) - 第6层
        4. Drive-evaluate (驱动评估) - 第5层
        5. Meta-control (元控制) - 第4层
        6. Self-model (自我建模)
        7. Select & Execute (选择与执行)
        8. Reflect & Learn (反思与学习)
        """
        logger.info(f"SevenLayerAgent 启动，max_cycles={max_cycles}")
        
        for cycle in range(1, max_cycles + 1):
            if not self.alive:
                break
            
            self.cycle = cycle
            
            # ===== 1. Perceive (感知) =====
            state = self._get_state_vector()
            
            # ===== 2. Conceptualize (概念化) - 第7层 =====
            if cycle > 1 and len(self.current_trajectory['states']) > 0:
                prev_state = self.current_trajectory['states'][-1]
                concept, error, concept_info = self.concept_system.step(
                    prev_state, state, 
                    action=self.current_trajectory['actions'][-1] if self.current_trajectory['actions'] else None
                )
                self.stats['concepts_learned'] = self.concept_system.step_count
            else:
                concept = None
                concept_info = {}
            
            # 获取概念泛化建议
            generalization_suggestion = None
            if concept is not None:
                generalization_suggestion = self.concept_system.get_generalization_suggestion(state)
            
            # ===== 3. Goal-orient (目标导向) - 第6层 =====
            goal_influence = self.goal_system.get_goal_influence(state)
            
            # ===== 4. Drive-evaluate (驱动评估) - 第5层 =====
            env_state = self.env.perceive()
            drive_scores = self.drive_manager.evaluate_all(env_state)
            
            # 结合目标影响调整驱动得分
            if goal_influence > 0.3:
                # 目标对驱动有约束作用
                for name in drive_scores:
                    drive_scores[name] *= (0.7 + 0.3 * goal_influence)
            
            # ===== 5. Meta-control (元控制) - 第4层 =====
            # 计算当前性能（用于元驱动）
            current_performance = self._compute_performance()
            self.meta_controller.step(state, current_performance)
            
            # ===== 6. Self-model (自我建模) =====
            # 预测行动
            predicted_action_dist = self.self_model.predict_action(state)
            
            # ===== 7. Select & Execute (选择与执行) =====
            # 选择行动（结合驱动得分和泛化建议）
            action = self._select_action(
                drive_scores, 
                generalization_suggestion,
                concept_info.get('concept_id') if concept_info else None
            )
            
            # 执行
            result = self._execute_action(action)
            
            # ===== 8. Reflect & Learn (反思与学习) =====
            # 更新自我模型
            action_onehot = self._action_to_onehot(action)
            self.self_model.update(state, action_onehot)
            
            # 积累轨迹
            reward = result.get('success', 0) * 0.5 + drive_scores.get('survival', 0) * 0.5
            self.current_trajectory['states'].append(state)
            self.current_trajectory['actions'].append(action)
            self.current_trajectory['rewards'].append(reward)
            
            # 更新目标系统
            self.goal_system.step(state, action, reward, cycle)
            
            # 行为追踪
            action_dict = {'type': 'shell', 'command': action}
            self.behavior_tracker.record(action_dict, result)
            
            # 涌现检测（原有功能）
            if cycle % 10 == 0:
                self._check_emergence()
            
            # 记录自我意识分数
            self.stats['self_awareness_history'].append(
                self.self_model.get_self_awareness_score()
            )
            
            # 输出进度
            if verbose and cycle % 50 == 0:
                self._print_progress(concept_info, goal_influence)
        
        logger.info(f"SevenLayerAgent 完成 {self.cycle} 周期")
        return self.get_summary()
    
    def _get_state_vector(self) -> np.ndarray:
        """获取状态向量"""
        env_state = self.env.perceive()
        
        # 构建16维状态向量
        state = np.array([
            env_state.resource_level if hasattr(env_state, 'resource_level') else 0.5,
            env_state.entropy if hasattr(env_state, 'entropy') else 0.5,
            env_state.error_rate if hasattr(env_state, 'error_rate') else 0.0,
            env_state.task_completion_rate if hasattr(env_state, 'task_completion_rate') else 0.0,
            len(self.memory.memories) / 1000.0 if hasattr(self.memory, 'memories') else 0.0,
            self.cycle / 1000.0,
            np.random.rand() * 0.1,  # 噪声
            0.5,  # 占位
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5
        ])
        return state
    
    def _compute_performance(self) -> float:
        """计算当前性能指标"""
        if len(self.current_trajectory['rewards']) < 10:
            return 0.5
        
        recent_rewards = self.current_trajectory['rewards'][-10:]
        return float(np.mean(recent_rewards))
    
    def _select_action(self, drive_scores: Dict[str, float],
                      generalization_suggestion: Optional[str],
                      concept_id: Optional[int]) -> str:
        """选择行动"""
        # 如果有泛化建议且置信度高，使用它
        if generalization_suggestion:
            return generalization_suggestion
        
        # 否则基于驱动得分选择
        if not drive_scores:
            return 'explore'
        
        # 选择得分最高的驱动对应的行动
        best_drive = max(drive_scores.items(), key=lambda x: x[1])[0]
        
        # 驱动到行动的映射
        drive_action_map = {
            'survival': 'maintain',
            'curiosity': 'explore',
            'influence': 'interact',
            'optimization': 'optimize'
        }
        
        return drive_action_map.get(best_drive, 'explore')
    
    def _execute_action(self, action: str) -> Dict:
        """执行行动"""
        # 简化的行动执行
        try:
            if action == 'explore':
                result = self.env.execute('ls -la')
            elif action == 'maintain':
                result = self.env.execute('pwd')
            elif action == 'optimize':
                result = self.env.execute('echo "optimizing"')
            else:
                result = self.env.execute('echo "default"')
            
            return {'success': 1.0, 'result': result}
        except Exception as e:
            return {'success': 0.0, 'error': str(e)}
    
    def _action_to_onehot(self, action: str) -> np.ndarray:
        """将行动转换为one-hot向量"""
        actions = ['explore', 'maintain', 'interact', 'optimize', 'default']
        vec = np.zeros(10)
        if action in actions:
            idx = actions.index(action)
            vec[idx] = 1.0
        return vec
    
    def _check_emergence(self):
        """检查涌现"""
        # 使用原有涌现检测逻辑
        pass
    
    def _print_progress(self, concept_info: Dict, goal_influence: float):
        """打印进度"""
        self_awareness = self.self_model.get_self_awareness_score()
        meta_influence = self.meta_controller.get_meta_drive_influence()
        
        print(f"[Cycle {self.cycle}] "
              f"Concepts: {concept_info.get('concept_dim', 0)} "
              f"Goals: {len(self.goal_system.active_goals)} "
              f"Self-Awareness: {self_awareness:.3f} "
              f"Meta-Influence: {meta_influence:.3f} "
              f"Goal-Influence: {goal_influence:.3f}")
    
    def get_summary(self) -> Dict:
        """获取运行摘要"""
        return {
            'cycles': self.cycle,
            'concept_system': self.concept_system.get_stats(),
            'goal_system': self.goal_system.get_stats(),
            'meta_controller': self.meta_controller.get_stats(),
            'self_model': self.self_model.get_stats(),
            'stats': self.stats
        }
